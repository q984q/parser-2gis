"""Dark theme for the GUI.

Module contains the single source of truth for colors, fonts and
global PySimpleGUI options used by every window of the application.
"""

from __future__ import annotations

from ..common import GUI_ENABLED, running_mac, running_windows

if GUI_ENABLED:
    import tkinter as tk
    import tkinter.font as tkfont

    import PySimpleGUI as sg


# --------------------------------------------------------------------------- #
#                                  Palette                                    #
# --------------------------------------------------------------------------- #

# Backgrounds
BACKGROUND = '#0F1512'  # window background
BACKGROUND_DEEP = '#0A0F0D'  # inputs, log area, tree
SURFACE = '#151D19'  # elevated blocks (cards, tables header)
SURFACE_HOVER = '#1D2823'

# Lines and dividers
BORDER = '#243129'
BORDER_STRONG = '#34463C'

# Text
TEXT = '#E8F0EC'
TEXT_MUTED = '#8CA69A'
TEXT_DISABLED = '#5C7266'

# Accent (2GIS green)
ACCENT = '#46D07F'
ACCENT_HOVER = '#5BE194'
ACCENT_TEXT = '#042213'
ACCENT_SOFT = '#17352A'  # accent tinted background (selection, chips)

# Semantic colors
DANGER = '#E4675C'
DANGER_HOVER = '#F07C71'
DANGER_TEXT = '#1B0503'
WARNING = '#E5A94A'

# Log
LOG_BACKGROUND = '#0A0F0D'
LOG_TEXT = '#C6D6CD'
LOG_ERROR_BACKGROUND = '#3A1713'
LOG_ERROR_TEXT = '#FFB4A8'
LOG_WARNING_BACKGROUND = '#3A2C12'
LOG_WARNING_TEXT = '#FFD79B'

# Selections
SELECTION_TEXT = '#EAF6EF'
SELECTION_BACKGROUND = '#1E4A37'

# Tooltip
TOOLTIP_BACKGROUND = '#E7F1EB'

# Window geometry
MIN_WINDOW_WIDTH = 760
MIN_WINDOW_HEIGHT = 520
DEFAULT_WINDOW_WIDTH = 920
DEFAULT_WINDOW_HEIGHT = 700

# --------------------------------------------------------------------------- #
#                                   Fonts                                     #
# --------------------------------------------------------------------------- #

_FONT_CANDIDATES = {
    'sans': ('Inter', 'SF Pro Text', 'Segoe UI', 'Helvetica Neue',
             'DejaVu Sans', 'Noto Sans', 'Liberation Sans', 'Arial'),
    'mono': ('JetBrains Mono', 'SF Mono', 'Consolas', 'Cascadia Code',
             'DejaVu Sans Mono', 'Noto Sans Mono', 'Liberation Mono',
             'Courier New'),
}

# Families used when the system fonts can't be probed yet
_SYSTEM_FAMILIES = {
    'windows': {'sans': 'Segoe UI', 'mono': 'Consolas'},
    'mac': {'sans': 'Helvetica Neue', 'mono': 'Menlo'},
    'linux': {'sans': 'DejaVu Sans', 'mono': 'DejaVu Sans Mono'},
}


def _system_fallbacks() -> dict[str, str]:
    """Return font families that are almost surely installed on the OS."""
    if running_windows():
        return dict(_SYSTEM_FAMILIES['windows'])
    if running_mac():
        return dict(_SYSTEM_FAMILIES['mac'])
    return dict(_SYSTEM_FAMILIES['linux'])


def _ensure_tk_root() -> None:
    """Make sure a hidden Tk root exists so that fonts can be probed."""
    if getattr(tk, '_default_root', None) is not None:
        return

    try:
        from PySimpleGUI.PySimpleGUI import _get_hidden_master_root

        _get_hidden_master_root()
    except Exception:  # pragma: no cover - depends on the display server
        pass


def _available_families() -> set[str]:
    """Return lowercased families available for the default Tk root.

    Returns:
        Set of families or empty set when the Tk root doesn't exist yet.
    """
    if not GUI_ENABLED:
        return set()

    _ensure_tk_root()
    root = getattr(tk, '_default_root', None)
    if root is None:
        return set()

    try:
        return {family.lower() for family in tkfont.families(root)}
    except tk.TclError:  # pragma: no cover - depends on the display server
        return set()


def _pick_family(kind: str) -> str:
    """Pick the first available font family of the desired `kind`."""
    available = _available_families()
    if not available:
        return _system_fallbacks()[kind]

    for candidate in _FONT_CANDIDATES[kind]:
        if candidate.lower() in available:
            return candidate

    return _system_fallbacks()[kind]


# Resolved by `apply_theme` once the application starts
FONT_FAMILY = _system_fallbacks()['sans']
FONT_FAMILY_MONO = _system_fallbacks()['mono']


def font(size: int = 11, bold: bool = False, mono: bool = False) -> tuple:
    """Build a font tuple out of the resolved theme families.

    Args:
        size: Font size in points.
        bold: Whether the font should be bold.
        mono: Whether to use a monospaced font.

    Returns:
        Font tuple suitable for PySimpleGUI.
    """
    family = FONT_FAMILY_MONO if mono else FONT_FAMILY
    return (family, size, 'bold') if bold else (family, size)


# Font roles
TITLE = (15, True, False)
SUBTITLE = (10, False, False)
SECTION = (9, True, False)
BODY = (10, False, False)
VALUE = (10, True, False)
BUTTON = (10, True, False)
SMALL = (9, False, False)
LOG = (10, False, True)


def font_of(role: tuple) -> tuple:
    """Resolve a font role descriptor into a font tuple.

    Args:
        role: Font descriptor, e.g. `theme.TITLE`.

    Returns:
        Font tuple suitable for PySimpleGUI.
    """
    size, bold, mono = role
    return font(size, bold=bold, mono=mono)


# --------------------------------------------------------------------------- #
#                              Global options                                 #
# --------------------------------------------------------------------------- #

_THEME_NAME = 'Parser2GISDark'

_THEME = {
    'BACKGROUND': BACKGROUND,
    'TEXT': TEXT,
    'INPUT': BACKGROUND_DEEP,
    'TEXT_INPUT': TEXT,
    'SCROLL': SURFACE,
    'BUTTON': (ACCENT_TEXT, ACCENT),
    'PROGRESS': (ACCENT, BACKGROUND_DEEP),
    'BORDER': 0,
    'SLIDER_DEPTH': 0,
    'PROGRESS_DEPTH': 0,
    'ACCENT1': ACCENT,
    'ACCENT2': ACCENT_SOFT,
    'ACCENT3': TEXT_MUTED,
}


def apply_theme() -> None:
    """Apply the theme to every window created after this call.

    The function is idempotent, so it can be safely called for each window.
    """
    global FONT_FAMILY, FONT_FAMILY_MONO

    if not GUI_ENABLED:
        return

    FONT_FAMILY = _pick_family('sans')
    FONT_FAMILY_MONO = _pick_family('mono')

    sg.theme_add_new(_THEME_NAME, dict(_THEME))
    sg.theme(_THEME_NAME)

    sg.set_options(
        font=font(11),
        text_color=TEXT,
        element_text_color=TEXT,
        background_color=BACKGROUND,
        element_background_color=BACKGROUND,
        text_element_background_color=BACKGROUND,
        input_elements_background_color=BACKGROUND_DEEP,
        input_text_color=TEXT,
        scrollbar_color=SURFACE,
        button_color=(ACCENT_TEXT, ACCENT),
        border_width=0,
        element_padding=(0, 4),
        margins=(0, 0),
        use_ttk_buttons=False,
        ttk_theme='clam',
        tooltip_font=font(10),
        tooltip_time=350,
        sbar_trough_color=BACKGROUND_DEEP,
        sbar_background_color=BORDER_STRONG,
        sbar_arrow_color=TEXT_MUTED,
        sbar_relief='flat',
        sbar_width=10,
        sbar_arrow_width=10,
    )

    _patch_tooltip_colors()


def _patch_tooltip_colors() -> None:
    """Paint PySimpleGUI tooltips with the theme colors.

    PySimpleGUI reads tooltip colors from module globals, so they
    can't be changed through `sg.set_options`.
    """
    try:
        import PySimpleGUI.PySimpleGUI as SGCore  # noqa: N813

        SGCore.TOOLTIP_BACKGROUND_COLOR = TOOLTIP_BACKGROUND
    except Exception:  # pragma: no cover - tooltips are a cosmetic feature
        pass


def window_size(width: int = DEFAULT_WINDOW_WIDTH,
                height: int = DEFAULT_WINDOW_HEIGHT) -> tuple[int, int]:
    """Fit the window size into the screen.

    Args:
        width: Desired width in pixels.
        height: Desired height in pixels.

    Returns:
        Size that fits the current screen with a small margin.
    """
    if not GUI_ENABLED:
        return (width, height)

    try:
        screen_width, screen_height = sg.Window.get_screen_size()
    except Exception:  # pragma: no cover - depends on the display server
        return (width, height)

    if not screen_width or not screen_height:  # pragma: no cover - headless
        return (width, height)

    return (min(width, int(screen_width * 0.9)),
            min(height, int(screen_height * 0.88)))


def setup_text_widget_colors(widget: tk.Widget, *, background: str = BACKGROUND_DEEP,
                             foreground: str = TEXT, insert: str | None = None) -> None:
    """Apply theme colors to a widget created outside of PySimpleGUI.

    Args:
        widget: Tk widget (Text, Entry, Canvas...) to be painted.
        background: Background color.
        foreground: Text color.
        insert: Color of the text cursor.
    """
    options = dict(background=background, foreground=foreground,
                   highlightthickness=0, borderwidth=0)
    try:
        widget.configure(**options)
    except tk.TclError:  # pragma: no cover - widget without such options
        for key, value in options.items():
            try:
                widget.configure(**{key: value})
            except tk.TclError:
                pass

    try:
        widget.configure(insertbackground=insert or foreground,
                         selectbackground=SELECTION_BACKGROUND,
                         selectforeground=SELECTION_TEXT)
    except tk.TclError:  # pragma: no cover - widget without such options
        pass

    # Entry widgets look thin without an inner padding
    if widget.winfo_class() == 'Entry':
        try:
            widget.configure(relief='flat')
        except tk.TclError:  # pragma: no cover - widget without such options
            pass
