#!/usr/bin/env python
# Copyright 2016 Franz Zapata
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from gi.repository import GObject, Gedit

class ASWindowActivatable(GObject.Object, Gedit.WindowActivatable):

  window = GObject.Property(type=Gedit.Window)
  __inst = None
  
  def __init__(self):
    super().__init__()
    ASWindowActivatable.__inst = self

  @classmethod
  def get_instance(cls):
    return cls.__inst
