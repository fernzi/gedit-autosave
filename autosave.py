# Copyright © 2016-2024 Fern Zapata
# This program is subject to the terms of the GNU GPL, version 3
# or, at your option, any later version. If a copy of it was not
# included with this file, see https://www.gnu.org/licenses/.

import datetime
from pathlib import Path

from gi.repository import Gedit, Gio, GObject

# You can change here the default folder for unsaved files.
SAVEDIR = Path("~/.gedit_unsaved/").expanduser()


class ASWindowActivatable(GObject.Object, Gedit.WindowActivatable):
    window = GObject.Property(type=Gedit.Window)

    def do_activate(self):
        self.id_unfocus = self.window.connect_after(
            "focus-out-event", self.on_unfocused
        )

    def do_deactivate(self):
        self.window.disconnect(self.id_unfocus)
        if self.timeout is not None:
            GObject.source_remove(self.timeout)

    def is_any_dialog_active(self) -> bool:
        return any(
            w.is_active()
            for w in self.window.list_toplevels()
            if not isinstance(w, Gedit.Window)
        )

    def on_unfocused(self, *_):
        # This could theoretically fail in some situation where
        # a dialog takes more than 200ms to appear, but I don't
        # know any other way to do the check after dialogs open.
        self.timeout = GObject.timeout_add(200, self.save)

    def save(self) -> bool:
        if self.is_any_dialog_active():
            # Don't autosave when the focused window is a Gedit dialog.
            return False

        for n, doc in enumerate(self.window.get_unsaved_documents()):
            file = doc.get_file()

            if doc.is_untouched() or file.is_readonly():
                continue

            if file.get_location() is None:
                # Provide a default filename
                now = datetime.datetime.now()
                SAVEDIR.mkdir(parents=True, exist_ok=True)
                filename = str(
                    SAVEDIR / now.strftime(f"%Y%m%d-%H%M%S-{n+1}.txt")
                )
                file.set_location(Gio.file_parse_name(filename))

            Gedit.commands_save_document(self.window, doc)

        self.timeout = None
        return False


class ASViewActivatable(GObject.Object, Gedit.ViewActivatable):
    view = GObject.Property(type=Gedit.View)
    timer = 2000

    def __init__(self):
        super().__init__()
        self.timeout = None

    def do_activate(self):
        self.window = self.view.get_toplevel()
        self.doc = self.view.get_buffer()
        self.conn = self.doc.connect("changed", self.on_changed)

    def do_deactivate(self):
        self.doc.disconnect(self.conn)
        self.remove_timeout()

    def remove_timeout(self):
        if self.timeout is not None:
            GObject.source_remove(self.timeout)
            self.timeout = None

    def on_changed(self, *_):
        f = self.doc.get_file()
        if f.is_readonly() or f.get_location() is None:
            return
        self.remove_timeout()
        self.timeout = GObject.timeout_add(
            self.timer,
            self.save,
            priority=GObject.PRIORITY_LOW,
        )

    def save(self):
        if self.doc.get_modified():
            Gedit.commands_save_document(self.window, self.doc)
        self.timeout = None
        return False
