install:
	@mkdir -p ~/.local/share/gedit/plugins
	@cp autosave.{plugin,py} ~/.local/share/gedit/plugins -v

uninstall:
	@rm -fv ~/.local/share/gedit/plugins/autosave.{plugin,py}