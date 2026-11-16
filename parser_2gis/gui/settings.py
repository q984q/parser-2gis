from __future__ import annotations

import pydantic

from ..common import GUI_ENABLED, report_from_validation_error, unwrap_dot_dict
from ..config import Configuration
from ..logger import logger
from . import components as ui
from . import theme
from .error_popup import gui_error_popup
from .utils import ensure_gui_enabled, window_title

if GUI_ENABLED:
    import PySimpleGUI as sg


def _spin_row(label: str, key: str, values: list[int], initial_value: int,
              tooltip: str) -> list:
    """Build a labelled row with a numeric field on the right.

    Args:
        label: Row label.
        key: Element key.
        values: Allowed values.
        initial_value: Initial value.
        tooltip: Hint shown on hover.

    Returns:
        Row of elements.
    """
    return [
        sg.Text(label, font=theme.font_of(theme.BODY), text_color=theme.TEXT_MUTED,
                background_color=theme.SURFACE, expand_x=True, pad=((0, 8), (0, 0))),
        ui.spin_field(key, values, initial_value=initial_value, size=(8, 1), tooltip=tooltip),
    ]


def build_layout(config: Configuration) -> list[list]:
    """Build the settings window layout.

    Args:
        config: Configuration to be changed.

    Returns:
        PySimpleGUI layout.
    """
    browser_card = ui.card('Браузер', [
        [ui.checkbox('Отключить изображения', key='-CHROME.DISABLE_IMAGES-',
                     default=config.chrome.disable_images,
                     tooltip='Отключить изображения для увеличения скорости работы')],
        [ui.checkbox('Запускать развёрнутым', key='-CHROME.START_MAXIMIZED-',
                     default=config.chrome.start_maximized,
                     tooltip='Запускать браузер развёрнутым во весь экран')],
        [ui.checkbox('Скрытый режим', key='-CHROME.HEADLESS-',
                     default=config.chrome.headless,
                     tooltip='Запускать браузер в скрытом виде')],
        _spin_row('Лимит RAM, МБ', '-CHROME.MEMORY_LIMIT-',
                  [x for x in range(1, 100)], config.chrome.memory_limit,
                  'Лимит оперативной памяти браузера (мегабайт)'),
    ], pad=((0, 0), (0, 14)))

    parser_card = ui.card('Парсер', [
        [ui.checkbox('Показывать города', key='-WRITER.VERBOSE-',
                     default=config.writer.verbose,
                     tooltip='Показывать города в журнале')],
        [ui.checkbox('Точные совпадения', key='-PARSER.SKIP_404_RESPONSE-',
                     default=config.parser.skip_404_response,
                     tooltip='Пропускать ссылки, вернувшие сообщение '
                             '"Точных совпадений нет / Не найдено"')],
        _spin_row('Задержка кликов, мс', '-PARSER.DELAY_BETWEEN_CLICKS-',
                  [x for x in range(1, 100000)], config.parser.delay_between_clicks,
                  'Задержка между кликами по записям (миллисекунд)'),
        _spin_row('Лимит записей', '-PARSER.MAX_RECORDS-',
                  [x for x in range(1, 100000)], config.parser.max_records,
                  'Максимальное количество спарсенных записей с одного URL'),
    ], pad=((0, 0), (0, 14)))

    csv_card = ui.card('Таблицы CSV / XLSX', [
        [ui.checkbox('Добавить колонку «Рубрики»', key='-WRITER.CSV.ADD_RUBRICS-',
                     default=config.writer.csv.add_rubrics,
                     tooltip='Добавить колонку «Рубрики»')],
        [ui.checkbox('Добавлять комментарии', key='-WRITER.CSV.ADD_COMMENTS-',
                     default=config.writer.csv.add_comments,
                     tooltip='Добавлять комментарии к ячейкам Телефон, E-Mail и т.д.')],
        [ui.checkbox('Удалить пустые колонки', key='-WRITER.CSV.REMOVE_EMPTY_COLUMNS-',
                     default=config.writer.csv.remove_empty_columns,
                     tooltip='Удалить пустые колонки по завершении работы парсера')],
        [ui.checkbox('Удалить дубликаты', key='-WRITER.CSV.REMOVE_DUPLICATES-',
                     default=config.writer.csv.remove_duplicates,
                     tooltip='Удалить повторяющиеся записи по завершении работы парсера')],
        _spin_row('Сложные колонки', '-WRITER.CSV.COLUMNS_PER_ENTITY-',
                  [x for x in range(1, 100)], config.writer.csv.columns_per_entity,
                  'Количество колонок для результата с несколькими возможными '
                  'значениями: Телефон_1, Телефон_2 и т.д.'),
    ], pad=((0, 0), (0, 4)))

    return [
        [ui.heading('Настройки', background=theme.BACKGROUND)],
        [ui.caption('Параметры сохраняются и применяются к следующим запускам.',
                    background=theme.BACKGROUND, pad=((0, 0), (6, 16)))],
        [sg.Column([[browser_card], [parser_card], [csv_card]],
                   background_color=theme.BACKGROUND, expand_x=True, expand_y=True,
                   scrollable=True, vertical_scroll_only=True, pad=(0, 0),
                   sbar_background_color=theme.BORDER_STRONG,
                   sbar_trough_color=theme.BACKGROUND,
                   sbar_arrow_color=theme.TEXT_MUTED, sbar_relief='flat',
                   sbar_width=10, sbar_arrow_width=10)],
        [
            ui.primary_button('Сохранить', key='-BTN_SAVE-', size=(12, 1),
                              pad=((0, 8), (16, 0))),
            ui.button('Отмена', key='-BTN_CANCEL-', size=(10, 1),
                      pad=((0, 0), (16, 0))),
        ],
    ]


@ensure_gui_enabled
def gui_settings(config: Configuration) -> None:
    """Run settings.

    Args:
        config: Configuration to be changed.
    """
    theme.apply_theme()

    window = sg.Window(window_title('Настройки', 'Settings'), layout=build_layout(config),
                       background_color=theme.BACKGROUND, auto_size_text=True,
                       finalize=True, font=theme.font(11), modal=True, keep_on_top=True,
                       element_padding=(0, 0), margins=(0, 0), use_ttk_buttons=False,
                       resizable=True, size=theme.window_size(660, 700))

    window.set_min_size((520, 480))

    # Main loop
    while True:
        event, values = window.Read()

        # Close window
        if event in (None, '-BTN_CANCEL-'):
            break

        # Chrome settings
        elif event == '-BTN_SAVE-':
            new_parameters_flat = {k.strip('-').lower(): v for k, v in values.items()}
            new_parameters = unwrap_dot_dict(new_parameters_flat)

            try:
                new_configuration = Configuration(**new_parameters)
                config.merge_with(new_configuration)
                config.save_config()
                break
            except pydantic.ValidationError as e:
                errors = []
                errors_report = report_from_validation_error(e, new_parameters)
                for path, description in errors_report.items():
                    arg = description['invalid_value']
                    error_msg = description['error_message']
                    errors.append(f'[*] Поле: {path}, значение: {arg}, ошибка: {error_msg}')

                gui_error_popup('\n\n'.join(errors))
            except Exception as e:
                # Print the error to console and close the window
                logger.error('Ошибка при сохранении параметров:\n%s', e, exc_info=True)
                break

    window.close()
    del window
