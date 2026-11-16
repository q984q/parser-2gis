from __future__ import annotations

import textwrap

from ..common import GUI_ENABLED
from . import theme
from .utils import ensure_gui_enabled

if GUI_ENABLED:
    import PySimpleGUI as sg


@ensure_gui_enabled
def gui_error_popup(error_msg: str) -> None:
    """Run error modal window.

    Args:
        error_msg: Error message.
    """
    theme.apply_theme()

    # Adjust error message width
    error_msg = '\n'.join(
        textwrap.wrap(error_msg, width=58, replace_whitespace=False, break_on_hyphens=False)
    )

    # Window layout
    layout = [
        [
            sg.Column([
                [
                    sg.Text('Что-то пошло не так', font=theme.font_of(theme.SECTION),
                            text_color=theme.DANGER, background_color=theme.BACKGROUND,
                            pad=((0, 0), (0, 10))),
                ],
                [
                    sg.Text(error_msg, font=theme.font_of(theme.BODY),
                            text_color=theme.TEXT, background_color=theme.BACKGROUND,
                            pad=((0, 0), (0, 18))),
                ],
                [
                    sg.Button('Закрыть', key='-BTN_CLOSE-', size=(12, 1),
                              button_color=(theme.DANGER_TEXT, theme.DANGER),
                              mouseover_colors=(theme.DANGER_TEXT, theme.DANGER_HOVER),
                              border_width=0, font=theme.font_of(theme.BUTTON),
                              focus=True, bind_return_key=True, pad=(0, 0)),
                ],
            ], background_color=theme.BACKGROUND, pad=((22, 22), (18, 18)),
                expand_x=True, element_justification='left'),
        ],
    ]

    window = sg.Window('Ошибка', layout, background_color=theme.BACKGROUND,
                       auto_size_text=True, finalize=True, font=theme.font(11),
                       modal=True, keep_on_top=True, element_padding=(0, 6),
                       margins=(0, 0), use_ttk_buttons=False)

    while True:
        event, _ = window.Read()

        # Close window
        if event in (None, '-BTN_CLOSE-'):
            break

    window.close()
    del window
