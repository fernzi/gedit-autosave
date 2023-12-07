# Copyright © 2016-2020 Fern Zapata
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime

from gi.repository import GObject, Gedit, Gio, Gdk
from pathlib import Path

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
    self.id_unfocus = self.window.connect('focus-out-event', self.on_unfocused, GObject.PRIORITY_DEFAULT)
    self.id_ctrl_s = self.window.connect("key-press-event", on_key_press)

  def do_deactivate(self):
    self.window.disconnect(self.id_unfocus)
    self.window.disconnect(self.id_ctrl_s)

  def on_unfocused(self, *args):
    global Ctrl_S
    if Ctrl_S:
      Ctrl_S = False
      # skip to user specified file name
      return

    for n, doc in enumerate(self.window.get_unsaved_documents()):
      if doc.is_untouched(): # = not doc.get_modified()
          # nothing to do
          continue
      if doc.get_file().is_readonly():
          # skip read-only files
          continue
      file_ = doc.get_file()

      if file_.get_location() is None:
          # provide a default filename
          now = datetime.datetime.now()
          Path(dirname).mkdir(parents=True, exist_ok=True)
          filename = str(dirname/now.strftime(f"%Y%m%d-%H%M%S-{n+1}.txt"))
          doc.get_file().set_location(Gio.file_parse_name(filename))

      # save the document
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
    self.conn = self.doc.connect('changed', self.on_changed)

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
