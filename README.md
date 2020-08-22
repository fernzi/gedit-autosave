# Gedit Autosave Plugin

When activated, this plugin will automatically save your current document while
you edit it, in a Google Docs-like fashion.

Saving occurs 2 seconds after you stop typing and when the window is unfocused.
The plugin doesn't attempt to save read-only or untitled documents.

## Installation

Download the ZIP, and extract on your plugin directory, usually located
at `~/.local/share/gedit/plugins/`, or clone the repository using `git`:

```sh
mkdir -p ~/.local/share/gedit/plugins
cd ~/.local/share/gedit/plugins
git clone https://github.com/fernzi/gedit-autosave.git
```

Afterwards, restart Gedit and activate the plugin from the preferences dialog.
