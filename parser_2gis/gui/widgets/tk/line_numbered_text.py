from __future__ import annotations

import tkinter as tk

from .custom_text import CustomText


class TextLineNumbers(tk.Canvas):
    """Numbered Line Widget."""
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.textwidget: tk.Text | None = None
        self.text_color: str | None = None

    def attach(self, textwidget: tk.Text) -> None:
        self.textwidget = textwidget

    def redraw(self) -> None:
        self.delete('all')

        assert self.textwidget, 'Attach textwidget first'
        options = {'font': self.textwidget.cget('font'),
                   'anchor': 'nw'}
        if self.text_color:
            options['fill'] = self.text_color

        lines = []
        i = self.textwidget.index('@0,0')
        while True:
            bbox = self.textwidget.dlineinfo(i)
            if bbox is None:
                break

            lines.append((bbox[1], f'{i}'.split('.')[0]))
            i = self.textwidget.index(f'{i}+1line')

        for y, line_n in lines:
            self.create_text(8, y, text=line_n, **options)

        # Resize the gutter according to the widest line number
        try:
            digits = max((len(line_n) for _, line_n in lines), default=1)
            char_width = int(self.tk.call('font', 'measure',
                                          self.textwidget.cget('font'), '0'))
            self.configure(width=char_width * digits + 14)
        except (tk.TclError, ValueError):  # pragma: no cover - fonts unavailable
            self.configure(width=16)


class LineNumberedText(tk.Frame):
    """Combined Numbered Line and Customized Text Widgets."""
    def __init__(self, *args, background_color: str | None = None,
                 foreground: str | None = None, numbers_color: str | None = None,
                 selection_background: str | None = None,
                 selection_foreground: str | None = None, font: tuple | None = None,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Widget colors
        background_color = background_color or '#0A0F0D'
        foreground = foreground or '#E8F0EC'
        numbers_color = numbers_color or '#5C7266'
        selection_background = selection_background or '#1E4A37'
        selection_foreground = selection_foreground or '#EAF6EF'

        self.configure(background=background_color, borderwidth=0, highlightthickness=0)

        self.text = CustomText(self, background=background_color, foreground=foreground,
                               insertbackground=foreground, selectbackground=selection_background,
                               selectforeground=selection_foreground, borderwidth=0,
                               highlightthickness=0, relief='flat', padx=10, pady=8,
                               font=font or ('TkDefaultFont', 11))

        self.vsb = tk.Scrollbar(self, orient='vertical', command=self.text.yview,
                                background=background_color, troughcolor=background_color,
                                activebackground=numbers_color, borderwidth=0,
                                highlightthickness=0, relief='flat', width=10)
        self.hsb = tk.Scrollbar(self, orient='horizontal', command=self.text.xview,
                                background=background_color, troughcolor=background_color,
                                activebackground=numbers_color, borderwidth=0,
                                highlightthickness=0, relief='flat', width=10)
        self.text.configure(yscrollcommand=self.vsb.set)
        self.text.configure(xscrollcommand=self.hsb.set)
        self.text.configure(wrap='none', undo=True)

        self.linenumbers = TextLineNumbers(self, width=0, background=background_color,
                                           borderwidth=0, highlightthickness=0)
        self.linenumbers.text_color = numbers_color
        self.linenumbers.attach(self.text)

        self.vsb.pack(side='right', fill='y')
        self.hsb.pack(side='bottom', fill='x')
        self.linenumbers.pack(side='left', fill='y')
        self.text.pack(side='right', fill='both', expand=True)

        self.text.bind('<<Change>>', self._on_change)
        self.text.bind('<Configure>', self._on_change)

    def _on_change(self, event: tk.Event) -> None:
        self.linenumbers.redraw()
