XDG_DATA_HOME ?= $(HOME)/.local/share
PLUGIN_DIR = $(XDG_DATA_HOME)/gedit/plugins/gedit-autosave

install:
	install -Dm644 -t $(PLUGIN_DIR)/autosave autosave/*.py
	install -m644 autosave.plugin $(PLUGIN_DIR)

uninstall:
	$(RM) -rv $(PLUGIN_DIR)

.PHONY: install uninstall
