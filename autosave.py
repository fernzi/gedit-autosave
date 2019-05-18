# Copyright (C) 2016-2019  Fern Zapata
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

from gi.repository import GObject, Gedit


class ASViewActivatable(GObject.Object, Gedit.ViewActivatable):
  view = GObject.Property(type=Gedit.View)
  timer = 2000

  def __init__(self):
    super().__init__()
    self.timeouts = {'process': None, 'save': None}

  def do_activate(self):
    self.window = self.view.get_toplevel()
    self.doc = self.view.get_buffer()
    self.conn = self.doc.connect('changed', self.on_changed)

  def do_deactivate(self):
    self.doc.disconnect(self.conn)
    self.remove_timeouts()
    del self.conn

  def remove_timeouts(self):
    for k,v in self.timeouts.items():
      if v is not None:
        GObject.source_remove(v)
        self.timeouts[k] = None

  def on_changed(self, *args):
    if self.doc.get_encoding() is None:
      return
    if self.doc.get_readonly() or self.doc.is_untitled():
      return
    self.remove_timeouts()
    self.timeouts['process'] = GObject.timeout_add(
      250,
      self.process,
      priority=GObject.PRIORITY_LOW)

  def process(self):
    self.timeouts['save'] = GObject.timeout_add(
      self.timer,
      self.save,
      priority=GObject.PRIORITY_LOW)
    self.timeouts['process'] = None
    return False

  def save(self):
    if not self.doc.is_untouched():
      Gedit.commands_save_document(self.window, self.doc)
    self.timeouts['save'] = None
    return False
