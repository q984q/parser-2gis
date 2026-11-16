from __future__ import annotations

import queue
import webbrowser
from functools import partial
from typing import TYPE_CHECKING, Any

from ..common import GUI_ENABLED
from ..logger import logger, setup_cli_logger, setup_gui_logger
from ..paths import image_data, image_path
from ..runner import GUIRunner
from ..version import version
from . import components as ui
from . import theme
from .error_popup import gui_error_popup
from .settings import gui_settings
from .urls_editor import gui_urls_editor
from .utils import (ensure_gui_enabled, generate_event_handler,
                    setup_text_widget, window_title)

if TYPE_CHECKING:
    from ..config import Configuration

if GUI_ENABLED:
    import tkinter as tk

    import PySimpleGUI as sg


# Result formats supported by the parser
RESULT_FILETYPES = {
    'csv': [('CSV Table', '*.csv')],
    'xlsx': [('Microsoft Excel Spreadsheet', '*.xlsx')],
    'json': [('JSON', '*.json')],
}

# Log line colors by level
LOG_COLORS = {
    'CRITICAL': (theme.LOG_ERROR_TEXT, theme.LOG_ERROR_BACKGROUND),
    'ERROR': (theme.LOG_ERROR_TEXT, theme.LOG_ERROR_BACKGROUND),
    'WARNING': (theme.LOG_WARNING_TEXT, theme.LOG_WARNING_BACKGROUND),
}


def plural_links(count: int) -> str:
    """Decline the word "ссылка" according to `count`.

    Args:
        count: Number of links.

    Returns:
        String like `1 ссылка`, `3 ссылки`, `5 ссылок`.
    """
    last_1d = count % 10
    last_2d = count % 100

    if 11 <= last_2d <= 19:
        word = 'ссылок'
    elif last_1d == 1:
        word = 'ссылка'
    elif 2 <= last_1d <= 4:
        word = 'ссылки'
    else:
        word = 'ссылок'

    return f'{count} {word}'


def build_layout(urls: list[str], output_path: str | None, result_format: str,
                 config: Configuration) -> list[list[Any]]:
    """Build the main window layout.

    Args:
        urls: 2GIS URLs with results to be collected.
        output_path: Path to the result file.
        result_format: `csv`, `xlsx` or `json` format.
        config: User configuration.

    Returns:
        PySimpleGUI layout.
    """
    urls_count = len(urls)
    urls_value = urls[0] if urls_count == 1 else ''
    urls_disabled = urls_count > 1

    # ------------------------------------------------------------------ #
    # Header
    # ------------------------------------------------------------------ #
    header = [
        sg.Image(data=image_data('logo_dark'), background_color=theme.BACKGROUND,
                 pad=((0, 0), (0, 0)), enable_events=True, key='-IMG_LOGO-',
                 tooltip='Открыть страницу проекта'),
        sg.Push(background_color=theme.BACKGROUND),
        sg.Button('Настройки', key='-BTN_SETTINGS-', size=(12, 1),
                  button_color=(theme.TEXT_MUTED, theme.BACKGROUND),
                  mouseover_colors=(theme.TEXT, theme.SURFACE_HOVER),
                  border_width=0, font=theme.font_of(theme.BODY),
                  tooltip=str(config.path), pad=((0, 8), (0, 0))),
        sg.Text(f'v{version}', font=theme.font_of(theme.SMALL),
                text_color=theme.TEXT_DISABLED, background_color=theme.BACKGROUND,
                pad=((0, 0), (0, 0))),
    ]

    # ------------------------------------------------------------------ #
    # Task: URL input
    # ------------------------------------------------------------------ #
    url_row = [
        ui.input_field('-IN_URL-', default_text=urls_value, disabled=urls_disabled,
                       use_readonly_for_disable=True, pad=((0, 8), (0, 0))),
        ui.button('Ссылки', key='-BTN_URLS-', size=(9, 1), tooltip='Редактор списка ссылок'),
    ]

    task_card = ui.card('Ссылка на выдачу 2ГИС', [url_row], key='-CARD_TASK-')

    # ------------------------------------------------------------------ #
    # Result: format and output path
    # ------------------------------------------------------------------ #
    result_row = [
        ui.combo_field('-FILE_FORMAT-', ['csv', 'xlsx', 'json'],
                       default_value=result_format, size=(7, 1), pad=((0, 8), (0, 0))),
        ui.input_field('-OUTPUT_PATH-', default_text=output_path or '', pad=((0, 8), (0, 0))),
        sg.FileSaveAs(key='-OUTPUT_PATH_BROWSE-', button_text='Обзор', size=(7, 1),
                      default_extension=f'.{result_format}',
                      file_types=RESULT_FILETYPES[result_format],
                      button_color=(theme.TEXT, theme.SURFACE_HOVER),
                      font=theme.font_of(theme.BODY),
                      target='-OUTPUT_PATH-', pad=(0, 0)),
    ]

    result_card = ui.card('Результат', [
        result_row,
        [ui.caption('Формат файла подставляется автоматически при выборе типа.',
                    background=theme.SURFACE, pad=((0, 0), (8, 0)))],
    ], key='-CARD_RESULT-')

    # ------------------------------------------------------------------ #
    # Log
    # ------------------------------------------------------------------ #
    log_element = ui.multiline_log('-LOG-', size=(80, 14), expand_x=True, expand_y=True,
                                   autoscroll=True, reroute_stdout=True,
                                   reroute_stderr=True, echo_stdout_stderr=True)

    log_card = ui.card('Журнал', [[log_element]], key='-CARD_LOG-', expand_y=True,
                       extra_header=[sg.Text('', key='-STATUS-', font=theme.font_of(theme.SMALL),
                                             text_color=theme.ACCENT,
                                             background_color=theme.SURFACE,
                                             pad=((0, 0), (0, 8)))])

    # ------------------------------------------------------------------ #
    # Footer
    # ------------------------------------------------------------------ #
    footer = [
        sg.Image(key='-IMG_LOADING-', visible=False, background_color=theme.BACKGROUND,
                 pad=((0, 10), (0, 0))),
        sg.Text('Готов к работе', key='-FOOTER_HINT-', font=theme.font_of(theme.SMALL),
                text_color=theme.TEXT_MUTED, background_color=theme.BACKGROUND,
                pad=((0, 0), (0, 0))),
        sg.Push(background_color=theme.BACKGROUND),
        ui.primary_button('Запуск', key='-BTN_START-', size=(12, 1), pad=((0, 8), (0, 0))),
        ui.button('Стоп', key='-BTN_STOP-', size=(10, 1), visible=False,
                  disabled=True, tooltip='Остановить парсинг', pad=((0, 8), (0, 0))),
        ui.danger_button('Выход', key='-BTN_EXIT-', size=(10, 1)),
    ]

    return [
        header,
        [ui.separator(pad=((0, 0), (14, 16)))],
        [task_card],
        [result_card],
        [log_card],
        [ui.separator(pad=((0, 0), (16, 14)))],
        footer,
    ]


def _theme_scrollbars(window: sg.Window) -> None:
    """Paint tk scrollbars (log area, spin boxes) with the theme colors.

    PySimpleGUI themes its own scrollbars, but the ones inside tk widgets
    such as Spinbox keep the system colors.

    Args:
        window: Window whose widgets are about to be themed.
    """
    for element in window.key_dict.values():
        widget = getattr(element, 'Widget', None)
        if widget is None:
            continue

        # Spinbox keeps solid stack of buttons on the right
        try:
            widget.configure(buttonbackground=theme.SURFACE_HOVER,
                             background=theme.BACKGROUND_DEEP,
                             foreground=theme.TEXT,
                             insertbackground=theme.TEXT,
                             relief='flat', borderwidth=0, highlightthickness=0)
        except tk.TclError:
            pass


@ensure_gui_enabled
def gui_app(urls: list[str], output_path: str, format: str, config: Configuration) -> None:
    """Run GUI.

    Args:
        urls: 2GIS URLs with results to be collected.
        output_path: Path to the result file.
        format: `csv`, `xlsx` or `json` format.
        config: User configuration.
    """
    # App color theme
    theme.apply_theme()

    # Set icon
    sg.set_global_icon(image_data('icon', 'png'))

    # Setup main CLI logger
    setup_cli_logger(config.log)

    # If urls wasn't passed then let it be an empty list
    if urls is None:
        urls = []

    # Result format
    default_result_format = format if format else 'csv'

    # Main window
    window = sg.Window(
        window_title('Парсер 2ГИС', 'Parser 2GIS'),
        build_layout(urls, output_path, default_result_format, config),
        background_color=theme.BACKGROUND,
        auto_size_text=True,
        finalize=True,
        font=theme.font(11),
        element_padding=(0, 6),
        margins=(0, 0),
        use_ttk_buttons=False,
        resizable=True,
        size=theme.window_size(),
    )

    # Keep the window usable on small screens
    window.set_min_size((theme.MIN_WINDOW_WIDTH, theme.MIN_WINDOW_HEIGHT))

    # Dark scrollbars for the log area and the window background
    _theme_scrollbars(window)

    # Setup text widgets
    setup_text_widget(window['-IN_URL-'].widget, window.TKroot, menu_clear=False, set_focus=True)
    setup_text_widget(window['-OUTPUT_PATH-'].widget, window.TKroot, menu_clear=False)
    setup_text_widget(window['-LOG-'].widget, window.TKroot, menu_paste=False, menu_cut=False)

    # Forbid user to edit output console,
    # block any keys except ctl+c, ←, ↑, →, ↓
    def log_key_handler(e: tk.Event) -> str | None:
        if e.char == '\x03' or e.keysym in ('Left', 'Up', 'Right', 'Down'):
            return None

        return 'break'

    window['-LOG-'].widget.bind('<Key>', log_key_handler)
    window['-LOG-'].widget.bind('<<Paste>>', lambda e: 'break')
    window['-LOG-'].widget.bind('<<Cut>>', lambda e: 'break')

    # Enable logging queue to be able to handle log in the mainloop
    log_queue: queue.Queue[tuple[str, str]] = queue.Queue()  # Queue of log messages (log_level, log_message)
    setup_gui_logger(log_queue, config.log)

    # Hand cursor for logo
    window['-IMG_LOGO-'].widget.config(cursor='hand2')

    # Highlight the settings button on hover
    def change_settings_color(text_color: str, background_color: str) -> None:
        window['-BTN_SETTINGS-'].update(button_color=(text_color, background_color))  # noqa: F821

    settings_button = window['-BTN_SETTINGS-'].TKButton
    for tk_widget in (settings_button, getattr(settings_button, 'widget', None)):
        if tk_widget is None:
            continue
        tk_widget.bind('<Enter>', generate_event_handler(
            partial(change_settings_color, theme.TEXT, theme.SURFACE_HOVER)))
        tk_widget.bind('<Leave>', generate_event_handler(
            partial(change_settings_color, theme.TEXT_MUTED, theme.BACKGROUND)))

    # Move cursor to the end of the URL input
    window['-IN_URL-'].widget.icursor('end')

    # Parsing thread
    parsing_thread: GUIRunner | None = None

    def parsing_thread_running() -> bool:
        return parsing_thread is not None and parsing_thread.is_alive()

    # Update URL Input element according to `urls` list
    def update_urls_input() -> None:
        urls_length = len(urls) if isinstance(urls, list) else 0
        if urls_length == 0:
            window['-IN_URL-'].update('', disabled=False)  # noqa: F821
        elif urls_length == 1:
            window['-IN_URL-'].update(urls[0], disabled=False)  # noqa: F821
        else:
            window['-IN_URL-'].update(f'<{plural_links(urls_length)}>', disabled=True)  # noqa: F821

    update_urls_input()

    # Pre-define log tags
    for text_color, color in LOG_COLORS.values():
        tag = f'Multiline({text_color},{color},None)'
        window['-LOG-'].tags.add(tag)
        window['-LOG-'].widget.tag_configure(tag, background=color, foreground=text_color)

    # Keep selection tag priority on top
    window['-LOG-'].widget.tag_raise('sel')

    def set_footer_hint(message: str, color: str = theme.TEXT_MUTED) -> None:
        """Update the hint on the left side of the footer."""
        window['-FOOTER_HINT-'].update(message, text_color=color)  # noqa: F821

    def set_status(message: str, color: str = theme.ACCENT) -> None:
        """Update the status label in the log card header."""
        window['-STATUS-'].update(message, text_color=color)  # noqa: F821

    def set_running_state(running: bool) -> None:
        """Swap start/stop buttons and toggle the loading indicator."""
        window['-BTN_START-'].update(visible=not running)  # noqa: F821
        window['-BTN_STOP-'].update(visible=running, disabled=False)  # noqa: F821
        window['-IMG_LOADING-'].update(visible=running)  # noqa: F821

        if running:
            window['-IMG_LOADING-'].update_animation(image_path('loading_dark'),  # noqa: F821
                                                     time_between_frames=50)
        else:
            set_footer_hint('Готов к работе')
            set_status('Завершено', theme.TEXT_MUTED)

    # Main loop
    while True:
        event, values = window.Read(timeout=50)

        # App exit
        if event in (None, '-BTN_EXIT-'):
            if parsing_thread_running():
                assert parsing_thread
                parsing_thread.stop()
                parsing_thread.join()

            break

        # Run settings
        elif event == '-BTN_SETTINGS-':
            gui_settings(config)

        # Run URLs Editor
        elif event == '-BTN_URLS-':
            # Sync urls with input element
            if not window['-IN_URL-'].Disabled:
                urls = [values['-IN_URL-']]

            ret_urls = gui_urls_editor(urls)
            if ret_urls is not None:
                urls = ret_urls
                update_urls_input()

        # Select output file format
        elif event == '-FILE_FORMAT-':
            file_format = values['-FILE_FORMAT-']
            if file_format in RESULT_FILETYPES:
                browse = window['-OUTPUT_PATH_BROWSE-']
                browse.FileTypes = RESULT_FILETYPES[file_format]
                browse.DefaultExtension = f'.{file_format}'

                # Keep the file extension in sync with the selected format
                current_path = values['-OUTPUT_PATH-'] or ''
                if '.' in current_path.rsplit('/', 1)[-1]:
                    new_path = current_path.rsplit('.', 1)[0] + f'.{file_format}'
                    window['-OUTPUT_PATH-'].update(new_path)  # noqa: F821

        # Click logo
        elif event == '-IMG_LOGO-':
            webbrowser.open('https://github.com/interlark/parser-2gis')

        # Click stop
        elif event == '-BTN_STOP-':
            if parsing_thread_running():
                logger.warn('Парсинг остановлен пользователем.')
                assert parsing_thread
                parsing_thread.stop()

                # Disable button until the thread fully stops
                window['-BTN_STOP-'].update(disabled=True)  # noqa: F821
                set_footer_hint('Останавливаю парсинг…', theme.WARNING)

        # Click start
        elif event == '-BTN_START-':
            # Check output file path
            if not values['-OUTPUT_PATH-']:
                gui_error_popup('Отсутствует путь результирующего файла!')
                continue

            # Check output file path
            if not values['-IN_URL-']:
                gui_error_popup('Отсутствует URL!')
                continue

            # Check result format
            if values['-FILE_FORMAT-'] not in ('csv', 'xlsx', 'json'):
                gui_error_popup('Формат результирующего файла должен быть csv, xlsx или json!')
                continue

            # Check if result format match output file extension
            if values['-OUTPUT_PATH-'].split('.')[-1].lower() != values['-FILE_FORMAT-']:
                gui_error_popup('Расширение результирующего файла должно быть *.%s!' % values['-FILE_FORMAT-'])
                continue

            # Sync urls with input element
            if not window['-IN_URL-'].Disabled:
                urls = [values['-IN_URL-']]

            # Run parser
            if not parsing_thread_running():
                parsing_thread = GUIRunner(urls, values['-OUTPUT_PATH-'], values['-FILE_FORMAT-'], config)
                parsing_thread.start()
                set_footer_hint('Парсинг запущен…', theme.ACCENT)

        # Poll log queue
        while True:
            try:
                log_level, log_msg = log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                # Print message to log
                text_color, background_color = LOG_COLORS.get(log_level, (None, None))
                window['-LOG-'].update(log_msg, append=True,
                                       text_color_for_value=text_color,
                                       background_color_for_value=background_color)  # noqa: F821

        # Swap start/stop buttons and reflect parser state
        if parsing_thread_running():
            if window['-BTN_START-'].visible:
                set_running_state(True)
                set_status('Идёт парсинг…')
        elif not window['-BTN_START-'].visible:
            set_running_state(False)

    window.close()
    del window
