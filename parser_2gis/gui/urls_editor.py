from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..common import GUI_ENABLED
from . import components as ui
from . import theme
from .urls_generator import gui_urls_generator
from .utils import ensure_gui_enabled, invoke_widget_hook, setup_text_widget, window_title

if TYPE_CHECKING:
    import tkinter as tk

if GUI_ENABLED:
    import PySimpleGUI as sg
    from .widgets.tk import LineNumberedText


def create_text_widget(column_element: sg.Element, containing_frame: tk.Frame,
                       toplevel_form: sg.Window) -> tk.Widget:
    """Callback for `custom_widget_hook` that creates and
    returns Line Numbered Text Widget."""
    # Create and setup Line Numbered Text Widget
    urls_widget = LineNumberedText(column_element.TKColFrame,
                                   background_color=theme.BACKGROUND_DEEP,
                                   foreground=theme.TEXT,
                                   numbers_color=theme.TEXT_DISABLED,
                                   selection_background=theme.SELECTION_BACKGROUND,
                                   selection_foreground=theme.SELECTION_TEXT)
    urls_widget.pack(side='top', fill='both', expand=True)
    urls_widget.linenumbers.configure(background=theme.BACKGROUND_DEEP)

    setup_text_widget(urls_widget.text, toplevel_form.TKroot)
    return urls_widget


def build_layout() -> list[list[Any]]:
    """Build the URLs editor layout.

    Returns:
        PySimpleGUI layout.
    """
    return [
        [ui.heading('Список ссылок', background=theme.BACKGROUND)],
        [ui.caption('Каждая ссылка должна быть на отдельной строке.',
                    background=theme.BACKGROUND, pad=((0, 0), (6, 14)))],
        [
            sg.Column([[]], key='-COL_URLS-', size=(0, 0), expand_x=True, expand_y=True,
                      background_color=theme.BACKGROUND_DEEP, pad=(0, 0)),
        ],
        [
            ui.primary_button('Готово', key='-BTN_OK-', size=(12, 1),
                              pad=((0, 8), (16, 0))),
            ui.button('Сгенерировать', key='-BTN_BUILD-', size=(15, 1),
                      tooltip='Собрать ссылки по городам и рубрикам',
                      pad=((0, 8), (16, 0))),
            ui.button('Отмена', key='-BTN_CANCEL-', size=(10, 1), pad=((0, 0), (16, 0))),
            sg.Text('', key='-COUNTER-', font=theme.font_of(theme.SMALL),
                    text_color=theme.TEXT_MUTED, background_color=theme.BACKGROUND,
                    pad=((12, 0), (16, 0))),
        ],
    ]


@ensure_gui_enabled
def gui_urls_editor(urls: list[str]) -> list[str] | None:
    """Run URLs editor.

    Args:
        urls: Currently set urls.

    Returns:
        List of URLs or `None` on cancel.
    """
    theme.apply_theme()

    with invoke_widget_hook(sg.PySimpleGUI, '-COL_URLS-', create_text_widget) as get_widget:
        window = sg.Window(window_title('Ссылки', 'URLs'), layout=build_layout(),
                           background_color=theme.BACKGROUND, finalize=True,
                           auto_size_text=True, font=theme.font(11), modal=True,
                           keep_on_top=True, element_padding=(0, 0), margins=(0, 0),
                           use_ttk_buttons=False, resizable=True,
                           size=theme.window_size(theme.DEFAULT_WINDOW_WIDTH,
                                                  theme.DEFAULT_WINDOW_HEIGHT - 60))

        # Get `LineNumberedText` widget
        urls_widget = get_widget()
        assert urls_widget

    window.set_min_size((560, 420))

    # Insert existing links
    urls_widget.text.insert('insert', '\n'.join(urls))

    # Focus on custom widget
    urls_widget.text.focus_set()

    def update_counter(event: Any = None) -> None:
        """Show the number of non-empty lines in the editor."""
        urls_content = urls_widget.text.get('1.0', 'end')[:-1]
        count = len([x for x in urls_content.splitlines() if x.strip()])
        window['-COUNTER-'].update(f'Ссылок: {count}' if count else '')  # noqa: F821

    urls_widget.text.bind('<<Change>>', update_counter)
    update_counter()

    # Result urls
    ret_urls = None

    # Main loop
    while True:
        event, _ = window.read()
        if event in (None, '-BTN_CANCEL-'):
            break

        elif event == '-BTN_BUILD-':
            generated_urls = gui_urls_generator()
            if generated_urls:
                urls_content = urls_widget.text.get('1.0', 'end')[:-1]
                join_character = '\n' if urls_content and urls_content[-1:] != '\n' else ''
                urls_widget.text.insert('end', join_character + '\n'.join(generated_urls))
                update_counter()

        elif event == '-BTN_OK-':
            urls_content = urls_widget.text.get('1.0', 'end')[:-1]
            ret_urls = [x for x in urls_content.splitlines() if x.strip()]
            break

    window.close()
    del window

    return ret_urls
