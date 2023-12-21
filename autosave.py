# Copyright © 2016-2023 Fern Zapata
# This program is subject to the terms of the GNU GPL, version 3
# or, at your option, any later version. If a copy of it was not
# included with this file, see https://www.gnu.org/licenses/.

import datetime
import json
import gi

from gi.repository import GObject, Gedit, Gio, Gtk, PeasGtk, GLib
from pathlib import Path

gi.require_version("Gtk", "3.0")

# region ############### CONSTANTs #################################
DEFAULT_AUTOSAVE_TIME = 2000 # milliseconds
DEFAULT_TEMP_PATH = "/tmp/.gedit_unsaved"

GEDIT_CONFIG_DIR = Path(GLib.get_user_config_dir())/"gedit"
COFING_FILE = Path(GEDIT_CONFIG_DIR)/"autosave_settings.json"

try:
    with open(COFING_FILE, encoding="utf-8") as conf:
        data = conf.read()
    CONFIG = json.loads(data)
except (FileNotFoundError, json.JSONDecodeError):
    CONFIG = dict(autosave_time=DEFAULT_AUTOSAVE_TIME, temp_path=None)

if CONFIG["temp_path"] is not None:
    TEMP_DIR = Path(CONFIG.get("temp_path", DEFAULT_TEMP_PATH)).expanduser()
    Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)

SOURCE_DIR = Path(__file__).parent.resolve()
# endregion ############### CONSTANTs ###############################


class ASWindowActivatable(GObject.Object, Gedit.WindowActivatable, PeasGtk.Configurable):

    window = GObject.Property(type=Gedit.Window)
    saving: bool

    def __init__(self):
        super().__init__()
        self.saving = False

    def do_activate(self):
        self.actions, self.ids = [], []
        for action in ("save", "save-as", "save-all", "close", "close-all", "open", "quickopen",
                       "config-spell", "check-spell", "inline-spell-checker", "print", "docinfo",
                       "replace"):
            if action in self.window.list_actions():
                self.actions.append(self.window.lookup_action(action))
                self.ids.append(self.actions[-1].connect("activate", self.on_save))
        self.id_unfocus = self.window.connect("focus-out-event", self.on_unfocused)


    def do_deactivate(self):
        self.window.disconnect(self.id_unfocus)
        for action,id_ in zip(self.actions, self.ids):
            action.disconnect(id_)

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
            if file_.get_location() is None and CONFIG["temp_path"] is not None:
                # Provide a default filename
                now = datetime.datetime.now()
                Path(CONFIG["temp_path"]).mkdir(parents=True, exist_ok=True)
                filename = str(Path(CONFIG["temp_path"])/now.strftime(f"%Y%m%d-%H%M%S-{n+1}.txt"))
                doc.get_file().set_location(Gio.file_parse_name(filename))
            else:
                continue

            Gedit.commands_save_document(self.window, doc)

    def do_create_configure_widget(self):
        # Just return your box, PeasGtk will automatically pack it into a box and show it.
        builder = Gtk.Builder()
        builder.add_from_file(str(SOURCE_DIR/"autosave_config.glade"))
        builder.connect_signals(Handler(self))

        window = builder.get_object("window")
        self.autosave_time = builder.get_object("autosave_time")
        self.untitled_savecheck =builder.get_object("untitled_savecheck")
        self.folder = builder.get_object("folder")

        if CONFIG["temp_path"] is None:
            self.folder.unselect_all()
            self.untitled_savecheck.set_active(False)
            self.folder.set_sensitive(False)
        else:
            self.untitled_savecheck.set_active(True)
            self.folder.set_sensitive(True)
            self.folder.set_current_folder(CONFIG["temp_path"])

        # region Signals' binding to the handlers ##############################
        window.connect("destroy", Handler(self).on_window_destroy)
        self.untitled_savecheck.connect("toggled", Handler(self).on_untitled_savecheck_toggled)
        self.folder.connect("selection_changed", Handler(self).on_selection_changed)
        # endregion  ###########################################################

        self.autosave_time.set_value(CONFIG["autosave_time"])

        return window


class Handler:
    def __init__(self, main_window):
        self.main_window = main_window

    def on_window_destroy(self, *args):
        if (as_time:=self.main_window.autosave_time.get_value()) != DEFAULT_AUTOSAVE_TIME:
            CONFIG["autosave_time"] = as_time
        if ( self.main_window.untitled_savecheck.get_active() and
            (folder:=self.main_window.folder.get_filename()) is not None ):
                CONFIG["temp_path"] = folder
        else:
            CONFIG["temp_path"] = None

        with open(COFING_FILE, mode="w", encoding="utf-8") as conf:
            json.dump(CONFIG, conf)


    def on_selection_changed(self, file_chooser):
        folder = file_chooser.get_filename()
        if folder and self.main_window.untitled_savecheck.get_active():
            CONFIG["temp_path"] = str(Path(folder))
        else:
            CONFIG["temp_path"] = None


    def on_untitled_savecheck_toggled(self, toggle_button):
        if toggle_button.get_active():
            self.main_window.folder.set_sensitive(True)
            if (CONFIG["temp_path"]) is None:
                CONFIG["temp_path"] = DEFAULT_TEMP_PATH
                self.main_window.folder.set_current_folder(CONFIG["temp_path"])
        else:
            self.main_window.folder.unselect_all()
            self.main_window.folder.unselect_all()
            self.main_window.folder.set_sensitive(False)
            CONFIG["temp_path"] = None


class ASViewActivatable(GObject.Object, Gedit.ViewActivatable):
    view = GObject.Property(type=Gedit.View)
    timer = CONFIG["autosave_time"]

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
