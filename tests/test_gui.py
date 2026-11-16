"""Tests for the GUI layer that don't need a display server."""

import pytest

from parser_2gis.common import GUI_ENABLED
from parser_2gis.gui import theme
from parser_2gis.gui.app import plural_links

requires_gui = pytest.mark.skipif(not GUI_ENABLED, reason='GUI (PySimpleGUI + tkinter) is not installed')


@pytest.mark.parametrize('count, expected', [
    (0, '0 ссылок'),
    (1, '1 ссылка'),
    (2, '2 ссылки'),
    (4, '4 ссылки'),
    (5, '5 ссылок'),
    (11, '11 ссылок'),
    (14, '14 ссылок'),
    (21, '21 ссылка'),
    (22, '22 ссылки'),
    (25, '25 ссылок'),
    (111, '111 ссылок'),
    (112, '112 ссылок'),
])
def test_plural_links(count, expected):
    assert plural_links(count) == expected


def test_theme_palette_is_dark():
    """The theme must stay dark: background is way darker than text."""
    def luminance(color):
        value = color.lstrip('#')
        red, green, blue = (int(value[i:i + 2], 16) for i in (0, 2, 4))
        return red * 0.299 + green * 0.587 + blue * 0.114

    assert luminance(theme.BACKGROUND) < 40
    assert luminance(theme.BACKGROUND_DEEP) < luminance(theme.BACKGROUND)
    assert luminance(theme.SURFACE) > luminance(theme.BACKGROUND)
    assert luminance(theme.TEXT) - luminance(theme.BACKGROUND) > 120
    assert luminance(theme.TEXT) > luminance(theme.TEXT_MUTED) > luminance(theme.TEXT_DISABLED)


def test_theme_contrast_of_accent_button():
    """Text on the accent button must be readable."""
    def luminance(color):
        value = color.lstrip('#')
        red, green, blue = (int(value[i:i + 2], 16) for i in (0, 2, 4))
        return red * 0.299 + green * 0.587 + blue * 0.114

    assert abs(luminance(theme.ACCENT) - luminance(theme.ACCENT_TEXT)) > 100
    assert abs(luminance(theme.DANGER) - luminance(theme.DANGER_TEXT)) > 100


def test_backgrounds_are_not_transparent():
    """All palette colors must be valid hex colors."""
    colors = [
        theme.BACKGROUND, theme.BACKGROUND_DEEP, theme.SURFACE, theme.SURFACE_HOVER,
        theme.BORDER, theme.BORDER_STRONG, theme.TEXT, theme.TEXT_MUTED,
        theme.TEXT_DISABLED, theme.ACCENT, theme.ACCENT_HOVER, theme.ACCENT_TEXT,
        theme.ACCENT_SOFT, theme.DANGER, theme.DANGER_HOVER, theme.DANGER_TEXT,
        theme.WARNING, theme.LOG_BACKGROUND, theme.LOG_TEXT, theme.LOG_ERROR_BACKGROUND,
        theme.LOG_ERROR_TEXT, theme.LOG_WARNING_BACKGROUND, theme.LOG_WARNING_TEXT,
        theme.SELECTION_TEXT, theme.SELECTION_BACKGROUND, theme.TOOLTIP_BACKGROUND,
    ]
    for color in colors:
        assert color.startswith('#'), color
        assert len(color) == 7, color
        int(color[1:], 16)


def test_font_helpers_return_font_tuples():
    bold_font = theme.font_of(theme.TITLE)
    body_font = theme.font_of(theme.BODY)
    log_font = theme.font_of(theme.LOG)

    assert len(bold_font) == 3 and bold_font[2] == 'bold'
    assert len(body_font) == 2
    assert log_font[0] == theme.FONT_FAMILY_MONO


def test_window_size_fits_small_screen():
    width, height = theme.window_size(1280, 1024)
    assert width <= theme.DEFAULT_WINDOW_WIDTH or width <= 1280
    assert height <= theme.DEFAULT_WINDOW_HEIGHT or height <= 1024
    assert width >= theme.MIN_WINDOW_WIDTH
    assert height >= theme.MIN_WINDOW_HEIGHT


@requires_gui
def test_apply_theme_is_idempotent():
    theme.apply_theme()
    first_family = theme.FONT_FAMILY
    theme.apply_theme()
    assert theme.FONT_FAMILY == first_family


@requires_gui
def test_main_layout_builds_for_any_url_count():
    from parser_2gis.config import Configuration
    from parser_2gis.gui.app import build_layout

    config = Configuration()

    for urls in ([], ['https://2gis.ru/moscow/search/coffee'], ['u1', 'u2']):
        layout = build_layout(urls, 'result.csv', 'csv', config)
        assert layout
        assert len(layout) > 3


@requires_gui
def test_settings_and_editor_layouts_build():
    from parser_2gis.config import Configuration
    from parser_2gis.gui.settings import build_layout as build_settings
    from parser_2gis.gui.urls_editor import build_layout as build_editor

    config = Configuration()

    assert build_settings(config)
    assert build_editor()
