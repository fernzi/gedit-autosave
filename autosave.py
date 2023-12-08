# Copyright © 2016-2023 Fern Zapata
# This program is subject to the terms of the GNU GPL, version 3
# or, at your option, any later version. If a copy of it was not
# included with this file, see https://www.gnu.org/licenses/.

import datetime
from pathlib import Path

from gi.repository import Gdk, Gedit, Gio, GObject


def on_key_press(widget, event):
    global Ctrl_S
    if event.state == Gdk.ModifierType.CONTROL_MASK and event.keyval == Gdk.KEY_s:
        Ctrl_S = True


# You can change here the default folder for unsaved files.
dirname = Path("~/.gedit_unsaved/").expanduser()

Ctrl_S = False


class ASWindowActivatable(GObject.Object, Gedit.WindowActivatable):
    window = GObject.Property(type=Gedit.Window)

    def __init__(self):
        super().__init__()

    def do_activate(self):
        self.id_unfocus = self.window.connect("focus-out-event", self.on_unfocused)
        self.id_ctrl_s = self.window.connect("key-press-event", on_key_press)

    def do_deactivate(self):
        self.window.disconnect(self.id_unfocus)
        self.window.disconnect(self.id_ctrl_s)

    def on_unfocused(self, *args):
        global Ctrl_S
        if Ctrl_S:
            Ctrl_S = False
            # Skip to user specified file name
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

    def on_changed(self, *args):
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
