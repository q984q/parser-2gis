from __future__ import annotations

import json
from typing import Any

from ..common import GUI_ENABLED
from ..paths import data_path, image_data
from . import components as ui
from . import theme
from .error_popup import gui_error_popup
from .utils import (ensure_gui_enabled, generate_event_handler,
                    invoke_widget_hook, setup_text_widget, window_title)

if GUI_ENABLED:
    import tkinter as tk
    import PySimpleGUI as sg
    from .widgets.sg import RubricsTree
    from .widgets.tk import CustomEntry


def filtered_rubrics(rubrics: dict[str, Any],
                     is_russian: bool = True) -> dict[str, Any]:
    """Filter rubrics on russian/non russian nodes.

    Args:
        rubrics: Loaded rubric dictionary.
        is_russian: Filter criteria.

    Returns:
        Filtered rubric dictionary.
    """
    # Filter nodes
    if is_russian:
        # Rubrics for Russia
        rubrics = {k: v for k, v in rubrics.items() if v.get('isRussian', True)}
    else:
        # Rubrics for non-russian countries
        rubrics = {k: v for k, v in rubrics.items() if v.get('isNonRussian', True)}

    # Fix references
    for node in rubrics.values():
        node['children'] = [x for x in node['children'] if x in rubrics]

    return rubrics


def create_search_widget(column_element: sg.Element, containing_frame: tk.Frame,
                         toplevel_form: sg.Window) -> tk.Widget:
    """Callback for `custom_widget_hook` that creates and
    returns Search Widget."""
    search_widget = CustomEntry(column_element.TKColFrame, width=60,
                                background=theme.BACKGROUND_DEEP, foreground=theme.TEXT,
                                insertbackground=theme.TEXT, borderwidth=0,
                                highlightthickness=0, relief='flat', font=theme.font(11))
    search_widget.pack(side='top', fill='both', expand=True, ipady=6)
    setup_text_widget(search_widget, toplevel_form.TKroot, menu_clear=False)

    return search_widget


def build_layout(rubrics: dict[str, Any]) -> list[list]:
    """Build the rubric selector layout.

    Args:
        rubrics: Filtered rubrics dictionary.

    Returns:
        PySimpleGUI layout.
    """
    return [
        [ui.heading('Выбор рубрики', background=theme.BACKGROUND)],
        [ui.caption('Начните вводить название — дерево отфильтруется.',
                    background=theme.BACKGROUND, pad=((0, 0), (6, 16)))],
        [
            ui.card('Поиск', [
                [sg.Column([[]], key='-COL_SEARCH-', expand_x=True,
                           background_color=theme.BACKGROUND_DEEP, pad=((12, 12), (10, 10)))],
            ], pad=((0, 0), (0, 12))),
        ],
        [
            ui.card('Рубрики', [
                [
                    RubricsTree(rubrics=rubrics,
                                image_parent=image_data('rubric_folder'),
                                image_item=image_data('rubric_item'),
                                headings=[], auto_size_columns=True,
                                select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                                num_rows=26, col0_width=90,
                                key='-TREE-',
                                enable_events=True,
                                expand_x=True, expand_y=True,
                                background_color=theme.BACKGROUND_DEEP,
                                text_color=theme.TEXT,
                                selected_row_colors=(theme.SELECTION_TEXT,
                                                     theme.SELECTION_BACKGROUND),
                                header_background_color=theme.BACKGROUND_DEEP,
                                header_text_color=theme.TEXT_MUTED,
                                border_width=0, row_height=26,
                                justification='left',
                                sbar_background_color=theme.BORDER_STRONG,
                                sbar_trough_color=theme.BACKGROUND_DEEP,
                                sbar_arrow_color=theme.TEXT_MUTED,
                                sbar_relief='flat', sbar_width=10,
                                sbar_arrow_width=10),
                ],
            ], expand_y=True, pad=((0, 0), (0, 4)),
                extra_header=[sg.Text('', key='-STATUS-', font=theme.font_of(theme.SMALL),
                                      text_color=theme.ACCENT,
                                      background_color=theme.SURFACE, pad=(0, 0))]),
        ],
        [
            ui.primary_button('Выбрать', key='-BTN_OK-', size=(12, 1),
                              pad=((0, 8), (16, 0))),
            ui.button('Отмена', key='-BTN_CANCEL-', size=(10, 1),
                      pad=((0, 0), (16, 0))),
            sg.Text('', key='-HINT-', font=theme.font_of(theme.SMALL),
                    text_color=theme.TEXT_DISABLED, background_color=theme.BACKGROUND,
                    expand_x=True, pad=((12, 0), (16, 0))),
            ui.button('Свернуть всё', key='-BTN_COLLAPSE_ALL-', size=(14, 1),
                      pad=((0, 8), (16, 0))),
            ui.button('Развернуть всё', key='-BTN_EXPAND_ALL-', size=(16, 1),
                      pad=((0, 0), (16, 0))),
        ],
    ]


@ensure_gui_enabled
def gui_rubric_selector(is_russian: bool = True) -> dict[str, Any] | None:
    """Run rubric selector.

    Run form that could help user to specify rubric.

    Args:
        is_russian: Whether rubrics for Russia or not.

    Returns:
        Dictionary representing selected rubric
        or `None` if nothing selected.
    """
    theme.apply_theme()

    # Locate and load rubrics list
    rubric_path = data_path() / 'rubrics.json'
    if not rubric_path.is_file():
        raise FileNotFoundError(f'Файл {rubric_path} не найден')

    try:
        with open(rubric_path, 'r', encoding='utf-8') as f:
            rubrics = filtered_rubrics(json.load(f), is_russian=is_russian)
    except json.JSONDecodeError as e:
        gui_error_popup(f'Файл {rubric_path.name} повреждён:\n{e}')
        return None

    with invoke_widget_hook(sg.PySimpleGUI, '-COL_SEARCH-', create_search_widget) as get_widget:
        window = sg.Window(window_title('Выбор рубрики', 'Select rubric'),
                           layout=build_layout(rubrics), background_color=theme.BACKGROUND,
                           finalize=True, auto_size_text=True, font=theme.font(11),
                           modal=True, keep_on_top=True, element_padding=(0, 0),
                           margins=(0, 0), use_ttk_buttons=False, resizable=True,
                           size=theme.window_size(theme.DEFAULT_WINDOW_WIDTH - 60,
                                                  theme.DEFAULT_WINDOW_HEIGHT - 40))

        # Get search widget
        search_widget = get_widget()
        assert search_widget

    window.set_min_size((560, 520))

    # On Linux\MacOS created window could be behind its parent
    window.bring_to_front()

    # Focus on custom widget
    search_widget.focus_set()

    # Hide tree header
    window['-TREE-'].widget.configure(show='tree')

    # Perform rubrics search on text changed
    def perform_rubric_search() -> None:
        query = search_widget.get()
        window['-TREE-'].filter(query)  # noqa: F821
        window['-HINT-'].update('Ничего не найдено' if query and not window['-TREE-'].Widget.get_children() else '')  # noqa: F821

    search_widget.bind('<<Change>>', generate_event_handler(perform_rubric_search))

    # Return rubric
    ret_rubric = None

    # Main loop
    while True:
        event, values = window.read()

        if event in (None, '-BTN_CANCEL-'):
            ret_rubric = None
            break

        elif event == '-BTN_OK-':
            if not ret_rubric:
                gui_error_popup('Рубрика не выбрана!')
                continue
            break

        # Update status bar
        elif event == '-TREE-':
            tree_values = values['-TREE-']
            if tree_values:
                node = rubrics[tree_values[0]]
                is_leaf = not bool(node['children'])
                if is_leaf:
                    ret_rubric = rubrics[tree_values[0]]
                    window['-STATUS-'].update(ret_rubric['label'])
                else:
                    ret_rubric = None
                    window['-STATUS-'].update('')
            else:
                ret_rubric = None
                window['-STATUS-'].update('')

        elif event == '-BTN_EXPAND_ALL-':
            window['-TREE-'].expand()

        elif event == '-BTN_COLLAPSE_ALL-':
            window['-TREE-'].expand(expand=False)

    window.close()
    del window

    return ret_rubric
