# Copyright © 2016-2024 Fern Zapata
# This program is subject to the terms of the GNU GPL, version 3
# or, at your option, any later version. If a copy of it was not
# included with this file, see https://www.gnu.org/licenses/.

from gi.repository import Gedit, GObject


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
            Gedit.commands_save_document_async(self.window, self.doc)
        self.timeout = None
        return False
