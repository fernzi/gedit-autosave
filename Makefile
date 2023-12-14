install:
	@mkdir -p ~/.local/share/gedit/plugins
	@cp autosave{.{plugin,py},_config.glade} ~/.local/share/gedit/plugins -fv

uninstall:
	@rm -fv ~/.local/share/gedit/plugins/autosave{.{plugin,py},_config.glade}