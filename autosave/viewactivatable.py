#!/usr/bin/env python
# Copyright 2016 Franz Zapata
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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
