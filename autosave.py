# Copyright © 2016-2023 Fern Zapata
# This program is subject to the terms of the GNU GPL, version 3
# or, at your option, any later version. If a copy of it was not
# included with this file, see https://www.gnu.org/licenses/.

import datetime
from pathlib import Path

from gi.repository import Gedit, Gio, GObject

# You can change here the default folder for unsaved files.
dirname = Path("~/.gedit_unsaved/").expanduser()


class ASWindowActivatable(GObject.Object, Gedit.WindowActivatable):
    window = GObject.Property(type=Gedit.Window)
    saving: bool

    def __init__(self):
        super().__init__()
        self.saving = False

    def do_activate(self):
        self.saveas_action = self.window.lookup_action("save-as")
        self.save_action = self.window.lookup_action("save")

        self.id_unfocus = self.window.connect("focus-out-event", self.on_unfocused)
        self.id_saveas = self.saveas_action.connect("activate", self.on_save)
        self.id_save = self.save_action.connect("activate", self.on_save)

    def do_deactivate(self):
        self.window.disconnect(self.id_unfocus)
        self.save_action.disconnect(self.id_save)
        self.saveas_action.disconnect(self.id_saveas)

    def on_save(self, *_):
        file = self.window.get_active_document().get_file()
        if file.get_location() is None:
            self.saving = True

    def on_unfocused(self, *_):
        if self.saving:
            # Don't auto-save when the save dialog's open.
            self.saving = False
            return

        for n, doc in enumerate(self.window.get_unsaved_documents()):
            if doc.is_untouched():
                # Nothing to do
                continue
            if doc.get_file().is_readonly():
                # Skip read-only files
                continue
            file_ = doc.get_file()

            if file_.get_location() is None:
                # Provide a default filename
                now = datetime.datetime.now()
                Path(dirname).mkdir(parents=True, exist_ok=True)
                filename = str(dirname / now.strftime(f"%Y%m%d-%H%M%S-{n+1}.txt"))
                doc.get_file().set_location(Gio.file_parse_name(filename))

            Gedit.commands_save_document(self.window, doc)


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
