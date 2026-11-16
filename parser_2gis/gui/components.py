"""Reusable building blocks of the GUI.

Every window is assembled from the helpers below so that spacing,
typography and colors stay consistent across the application.
"""

from __future__ import annotations

from typing import Any, Sequence

from ..common import GUI_ENABLED
from . import theme

if GUI_ENABLED:
    import PySimpleGUI as sg


# Paddings used by the layout (left/right, top/bottom)
GAP = ((0, 0), (0, 10))  # between cards
ROW_PAD = ((0, 0), (0, 8))  # between rows inside a card
CARD_PAD = ((18, 18), (14, 14))  # inside a card


def _background(background: str | None) -> dict[str, Any]:
    """Build `background_color` kwarg if the color is set."""
    return {'background_color': background} if background else {}


def text(content: str, role: tuple = theme.BODY, color: str = theme.TEXT,
         background: str | None = theme.BACKGROUND, **kwargs: Any) -> Any:
    """Build a themable text element.

    Args:
        content: Text to display.
        role: Font role from `theme`.
        color: Text color.
        background: Background color.
        kwargs: Extra PySimpleGUI arguments.

    Returns:
        Text element.
    """
    kwargs.setdefault('pad', (0, 0))
    if 'font' not in kwargs:
        kwargs['font'] = theme.font_of(role)
    return sg.Text(content, text_color=color,
                   **_background(background), **kwargs)


def heading(content: str, background: str | None = theme.BACKGROUND, **kwargs: Any) -> Any:
    """Build a window heading."""
    return text(content, theme.TITLE, theme.TEXT, background, **kwargs)


def caption(content: str, background: str | None = theme.BACKGROUND, **kwargs: Any) -> Any:
    """Build a secondary, muted text."""
    return text(content, theme.SMALL, theme.TEXT_MUTED, background, **kwargs)


def section_caption(content: str, background: str | None = theme.SURFACE, **kwargs: Any) -> Any:
    """Build a card caption (small uppercase-like label)."""
    return text(content.upper(), theme.SECTION, theme.TEXT_MUTED, background, **kwargs)


def separator(background: str = theme.BORDER, pad: tuple = ((0, 0), (0, 0))) -> Any:
    """Build a thin horizontal divider."""
    return sg.HorizontalSeparator(color=background, pad=pad)


def button(label: str, key: str, *, primary: bool = False, danger: bool = False,
           disabled: bool = False, size: tuple | None = None, tooltip: str | None = None,
           visible: bool = True, pad: tuple = (0, 0), **kwargs: Any) -> Any:
    """Build a flat button of one of the app styles.

    Args:
        label: Button text.
        key: Element key.
        primary: Use the accent (call to action) style.
        danger: Use the destructive style.
        disabled: Whether the button starts disabled.
        size: Button size in characters.
        tooltip: Hint shown on hover.
        visible: Whether the button is visible.
        pad: Padding around the button.
        kwargs: Extra PySimpleGUI arguments.

    Returns:
        Button element.
    """
    if primary:
        color, hover = (theme.ACCENT_TEXT, theme.ACCENT), (theme.ACCENT_TEXT, theme.ACCENT_HOVER)
    elif danger:
        color, hover = (theme.DANGER_TEXT, theme.DANGER), (theme.DANGER_TEXT, theme.DANGER_HOVER)
    else:
        color, hover = (theme.TEXT, theme.SURFACE_HOVER), (theme.TEXT, theme.BORDER_STRONG)

    options: dict[str, Any] = dict(
        key=key,
        button_color=color,
        mouseover_colors=hover,
        disabled_button_color=(theme.TEXT_DISABLED, theme.SURFACE),
        border_width=0,
        font=theme.font_of(theme.BUTTON),
        bind_return_key=primary,
        disabled=disabled,
        visible=visible,
        tooltip=tooltip,
        pad=pad,
        # tk buttons keep custom colors on every OS (ttk ones ignore them)
        use_ttk_buttons=False,
    )
    if size is not None:
        options['size'] = size
    options.update(kwargs)

    return sg.Button(label, **options)


def primary_button(label: str, key: str, **kwargs: Any) -> Any:
    """Build an accent button."""
    return button(label, key, primary=True, **kwargs)


def danger_button(label: str, key: str, **kwargs: Any) -> Any:
    """Build a destructive button."""
    return button(label, key, danger=True, **kwargs)


def input_field(key: str, *, default_text: str = '', disabled: bool = False,
                expand_x: bool = True, pad: tuple = (0, 0), **kwargs: Any) -> Any:
    """Build a dark input field."""
    kwargs.setdefault('font', theme.font_of(theme.BODY))
    return sg.Input(default_text, key=key, disabled=disabled,
                    background_color=theme.BACKGROUND_DEEP, text_color=theme.TEXT,
                    disabled_readonly_background_color=theme.BACKGROUND_DEEP,
                    disabled_readonly_text_color=theme.TEXT_MUTED,
                    border_width=0, expand_x=expand_x, pad=pad, **kwargs)


def multiline_log(key: str, **kwargs: Any) -> Any:
    """Build a read-only looking, monospaced multiline area (log, output)."""
    return sg.Multiline(key=key,
                        background_color=theme.LOG_BACKGROUND,
                        text_color=theme.LOG_TEXT,
                        border_width=0,
                        font=theme.font_of(theme.LOG),
                        sbar_background_color=theme.BORDER_STRONG,
                        sbar_trough_color=theme.LOG_BACKGROUND,
                        sbar_arrow_color=theme.TEXT_MUTED,
                        sbar_relief='flat',
                        sbar_width=10,
                        sbar_arrow_width=10,
                        pad=(0, 0),
                        **kwargs)


def combo_field(key: str, values: Sequence[str], *, default_value: str | None = None,
                pad: tuple = (0, 0), **kwargs: Any) -> Any:
    """Build a dark drop-down field."""
    return sg.Combo(values, key=key, default_value=default_value, readonly=True,
                    enable_events=True, background_color=theme.BACKGROUND_DEEP,
                    text_color=theme.TEXT, button_background_color=theme.BACKGROUND_DEEP,
                    button_arrow_color=theme.TEXT_MUTED,
                    font=theme.font_of(theme.BODY), pad=pad, **kwargs)


def spin_field(key: str, values: Sequence[int], *, initial_value: int | None = None,
               pad: tuple = (0, 0), **kwargs: Any) -> Any:
    """Build a dark numeric field."""
    return sg.Spin(values, key=key, initial_value=initial_value,
                   background_color=theme.BACKGROUND_DEEP, text_color=theme.TEXT,
                   font=theme.font_of(theme.BODY), pad=pad, **kwargs)


def checkbox(content: str, key: str, *, default: bool = False,
             background: str = theme.SURFACE, tooltip: str | None = None,
             pad: tuple = ((0, 0), (0, 8)), **kwargs: Any) -> Any:
    """Build a dark checkbox."""
    return sg.Checkbox(content, key=key, default=default, enable_events=True,
                       background_color=background, text_color=theme.TEXT,
                       checkbox_color=theme.BORDER_STRONG,
                       font=theme.font_of(theme.BODY), tooltip=tooltip, pad=pad,
                       **kwargs)


def card(title: str | None, body: list[list[Any]], *, key: str | None = None,
         background: str = theme.SURFACE, expand_x: bool = True,
         expand_y: bool = False, pad: tuple = GAP,
         extra_header: Sequence[Any] = (), inner_pad: tuple = CARD_PAD) -> Any:
    """Build a card: an elevated block with optional header and inner padding.

    Args:
        title: Card title, `None` to skip the header.
        body: Card content rows.
        key: Element key.
        background: Card background color.
        expand_x: Whether the card fills the window width.
        expand_y: Whether the card fills the window height.
        pad: Outer padding around the card.
        extra_header: Elements placed on the right side of the header.
        inner_pad: Padding inside the card.

    Returns:
        Column element that represents the card.
    """
    rows: list[list[Any]] = []

    if title is not None:
        header: list[Any] = [section_caption(title, background, pad=((0, 0), (0, 8)))]
        if extra_header:
            header.append(sg.Push(background_color=background))
            header.extend(extra_header)
        rows.append(header)

    rows.extend(body)

    inner = sg.Column(rows, background_color=background, pad=inner_pad,
                      expand_x=expand_x, expand_y=expand_y,
                      element_justification='left', vertical_alignment='top')

    return sg.Column([[inner]], key=key, background_color=background, pad=pad,
                     expand_x=expand_x, expand_y=expand_y)
