from __future__ import annotations

import json

from ..common import GUI_ENABLED
from ..paths import data_path
from . import components as ui
from . import theme
from .error_popup import gui_error_popup
from .rubric_selector import gui_rubric_selector
from .utils import ensure_gui_enabled, setup_text_widget, url_query_encode, window_title

if GUI_ENABLED:
    import PySimpleGUI as sg


# Countries available on 2GIS
COUNTRY_CODE_TO_NAME = dict(
    ae='Объединенные Арабские Эмираты', iq='Ирак',
    az='Азербайджан', bh='Бахрейн', by='Беларусь', cl='Чили', cy='Кипр', cz='Чехия',
    eg='Египет', it='Италия', kg='Киргизия', kw='Кувейт', kz='Казахстан', om='Оман',
    qa='Катар', ru='Россия', sa='Саудовская Аравия', uz='Узбекистан')

DEFAULT_COUNTRY_CODE = 'ru'


@ensure_gui_enabled
def gui_urls_generator() -> list[str]:
    """Run URLs generator.

    Run form that can build a bunch of URLs out of query and specified cities.

    Returns:
        List of generated URLs.
    """
    theme.apply_theme()

    # Locate and load cities list
    cities_path = data_path() / 'cities.json'
    if not cities_path.is_file():
        raise FileNotFoundError(f'Файл {cities_path} не найден')

    try:
        with open(cities_path, 'r', encoding='utf-8') as f:
            cities = json.load(f)
    except json.JSONDecodeError as e:
        gui_error_popup(f'Файл {cities_path.name} повреждён:\n{e}')
        return []

    country_name_to_code = {v: k for k, v in COUNTRY_CODE_TO_NAME.items()}

    # Checkbox layouts
    checkbox_layouts = {}
    for country_code in COUNTRY_CODE_TO_NAME.keys():
        layout = []
        for city in cities:
            if city['country_code'] == country_code:
                city_key = f'-CITY-{country_code}-{city["code"]}'
                layout.append([ui.checkbox(city['name'], key=city_key,
                                           background=theme.SURFACE, metadata=city,
                                           pad=((0, 0), (0, 4)))])
        checkbox_layouts[country_code] = sg.Column(
            layout, scrollable=True, vertical_scroll_only=True,
            expand_x=True, expand_y=True, visible=False,
            background_color=theme.SURFACE, pad=((0, 0), (0, 0)),
            sbar_background_color=theme.BORDER_STRONG,
            sbar_trough_color=theme.SURFACE,
            sbar_arrow_color=theme.TEXT_MUTED, sbar_relief='flat',
            sbar_width=10, sbar_arrow_width=10)

    # Window layout
    layout = [
        [ui.heading('Генератор ссылок', background=theme.BACKGROUND)],
        [ui.caption('Выберите города — ссылки добавятся в редактор списка.',
                    background=theme.BACKGROUND, pad=((0, 0), (6, 16)))],
        [
            ui.card('Запрос', [
                [ui.input_field('-IN_QUERY-', pad=((0, 0), (0, 0)))],
            ], pad=((0, 0), (0, 12))),
        ],
        [
            ui.card('Страна и рубрика', [
                [
                    ui.combo_field('-COUNTRY-', sorted(COUNTRY_CODE_TO_NAME.values()),
                                   default_value=COUNTRY_CODE_TO_NAME[DEFAULT_COUNTRY_CODE],
                                   expand_x=True),
                ],
                [
                    sg.Text('Рубрика', font=theme.font_of(theme.BODY),
                            text_color=theme.TEXT_MUTED,
                            background_color=theme.SURFACE, pad=((0, 8), (0, 0))),
                    ui.input_field('-IN_RUBRIC-', default_text='Без рубрики', disabled=True,
                                   pad=((0, 8), (0, 0))),
                    ui.button('Выбрать', key='-BTN_RUBRIC-', size=(10, 1),
                              tooltip='Выбрать рубрику из справочника'),
                ],
            ], pad=((0, 0), (0, 12))),
        ],
        [
            ui.card('Города', [
                [list(checkbox_layouts.values())],
            ], expand_y=True),
        ],
        [
            sg.Text('', key='-SELECTED-', font=theme.font_of(theme.SMALL),
                    text_color=theme.TEXT_MUTED, background_color=theme.BACKGROUND,
                    pad=((0, 0), (14, 0)), expand_x=True),
            ui.button('Снять выделение', key='-BTN_DESELECT_ALL-', size=(17, 1),
                      pad=((0, 8), (14, 0))),
            ui.button('Выделить всё', key='-BTN_SELECT_ALL-', size=(14, 1),
                      pad=((0, 8), (14, 0))),
            ui.primary_button('Готово', key='-BTN_OK-', size=(12, 1),
                              pad=((0, 0), (14, 0))),
        ],
    ]

    window = sg.Window(window_title('Сгенерировать ссылки', 'Generate links'),
                       layout=layout, background_color=theme.BACKGROUND,
                       auto_size_text=True, finalize=True, font=theme.font(11),
                       modal=True, keep_on_top=True, element_padding=(0, 0),
                       margins=(0, 0), use_ttk_buttons=False, resizable=True,
                       size=theme.window_size())

    window.set_min_size((620, 560))

    setup_text_widget(window['-IN_QUERY-'].widget, window.TKroot,
                      menu_clear=False, set_focus=True)

    setup_text_widget(window['-IN_RUBRIC-'].widget, window.TKroot,
                      menu_clear=False, menu_paste=False, menu_cut=False)

    def update_checkbox_layouts(country_name: str) -> None:
        """Bring frame with checkboxes visible that
        belong to `country_name`.

        Args:
            country_name: Name of a country.
        """
        for country_code, column_element in checkbox_layouts.items():
            column_element.update(visible=COUNTRY_CODE_TO_NAME[country_code] == country_name)

        # Reset rubrics
        rubric_input = window['-IN_RUBRIC-']  # noqa: F821
        rubric_input.metadata = None
        rubric_input.update(value='Без рубрики')

        update_selected_counter()

    def select_checkboxes(country_name: str, state: bool = True) -> None:
        """Select all checkboxes that belong to `country_name`.

        Args:
            country_name: Name of a country.
            state: Desired checkboxes' state.
        """
        country_code = country_name_to_code[country_name]
        for element in sum(checkbox_layouts[country_code].Rows, []):
            element.update(state)

        update_selected_counter()

    def get_checkboxes(state: bool | None = None) -> list[sg.Checkbox]:
        """Return all checkboxes.

        Args:
            state: Checkbox state requirement.

        Returns:
            Checkboxes with specified `state`.
        """
        all_checkboxes: list[sg.Checkbox] = sum(sum([x.Rows for x in checkbox_layouts.values()], []), [])
        if isinstance(state, bool):
            all_checkboxes = [x for x in all_checkboxes if x.get() == state]

        return all_checkboxes

    def update_selected_counter() -> None:
        """Update the number of selected cities."""
        count = len(get_checkboxes(state=True))
        window['-SELECTED-'].update(f'Выбрано городов: {count}' if count else '')  # noqa: F821

    def get_selected_urls(query: str) -> list[str]:
        """Get all checked checkboxes among all frames and generate URLs.

        Args:
            query: User's query.

        Returns:
            List of urls.
        """
        urls = []
        rubric = window['-IN_RUBRIC-'].metadata  # noqa: F821
        for checkbox in get_checkboxes(state=True):
            metadata = checkbox.metadata
            base_url = f'https://2gis.{metadata["domain"]}/{metadata["code"]}'
            rest_url = f'/search/{url_query_encode(query)}'
            if rubric:
                rest_url += f'/rubricId/{rubric["code"]}'

            rest_url += '/filters/sort=name'

            url = base_url + rest_url
            urls.append(url)

        return urls

    # Set default layout
    update_checkbox_layouts(COUNTRY_CODE_TO_NAME[DEFAULT_COUNTRY_CODE])

    # Result urls
    ret_urls: list[str] = []

    # Main loop
    while True:
        event, values = window.read()

        if event in (None, ):
            break

        elif event == '-COUNTRY-':
            update_checkbox_layouts(values['-COUNTRY-'])

        elif event == '-BTN_SELECT_ALL-':
            select_checkboxes(values['-COUNTRY-'], True)

        elif event == '-BTN_DESELECT_ALL-':
            select_checkboxes(values['-COUNTRY-'], False)

        elif event == '-BTN_RUBRIC-':
            rubric_dict = gui_rubric_selector(is_russian=values['-COUNTRY-'] == 'Россия')
            if rubric_dict:
                rubric_input = window['-IN_RUBRIC-']
                rubric_label = rubric_dict['label']
                rubric_input.update(value=rubric_label)
                if rubric_label == 'Без рубрики':
                    rubric_input.metadata = None
                else:
                    rubric_input.metadata = rubric_dict
                    window['-IN_QUERY-'].update(value=rubric_label)

        elif event == '-BTN_OK-':
            if not values['-IN_QUERY-'].strip():
                gui_error_popup('Необходимо ввести запрос!')
                continue

            if not get_checkboxes(state=True):
                gui_error_popup('Необходимо выбрать хотя бы один город!')
                continue

            ret_urls = get_selected_urls(values['-IN_QUERY-'])
            break

        # City checkbox toggled
        elif event.startswith('-CITY-'):
            update_selected_counter()

    window.close()
    del window

    return ret_urls
