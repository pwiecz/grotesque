# -*- coding: utf-8 -*-
#
#       settings_dialog.py
#
#       Copyright © 2011, 2014, 2018 Brandon Invergo <brandon@invergo.net>
#       Copyright © 2009, 2010 Per Liedman <per@liedman.net>
#
#       This file is part of Grotesque.
#
#       Grotesque is free software: you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation, either version 3 of the License, or
#       (at your option) any later version.
#
#       Grotesque is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with Grotesque.  If not, see <http://www.gnu.org/licenses/>.

import re

from gi.repository import Gtk, Gdk


class SettingsDialog(Gtk.Dialog):
    '''This class constructs the dialog where the user specifies preferred
    settings.

    '''
    def __init__(self, settings, parent=None):
        super(SettingsDialog, self).__init__(
            'Preferences', parent, Gtk.DialogFlags.MODAL,
            ("Close", Gtk.ResponseType.NONE))
        self.settings = settings
        self.exts_re = re.compile("[a-z0-9]+")
        # The dialog consists of a tabbed notebook.
        notebook = Gtk.Notebook()

        # The first tab contains the general preferences.
        general_vbox = Gtk.Grid()
        general_vbox.set_orientation(Gtk.Orientation.VERTICAL)
        # Create a check button for whether or not to fetch metadata from IFDB.
        fetch_metadata_check = Gtk.CheckButton('Fetch metadata from IFDB')
        fetch_metadata_check.set_active(self.settings.get_fetch_metadata())
        fetch_metadata_check.connect('toggled', self.on_fetch_metadata_toggled)
        # Create a check button for whether or not to fetch coverart from IFDB.
        general_vbox.add(fetch_metadata_check)
        fetch_coverart_check = Gtk.CheckButton('Fetch cover art from IFDB')
        fetch_coverart_check.set_active(self.settings.get_fetch_coverart())
        fetch_coverart_check.connect('toggled', self.on_fetch_coverart_toggled)
        general_vbox.add(fetch_coverart_check)
        # Create a check button for whether or not to display coverart.
        disp_coverart_check = Gtk.CheckButton('Display cover art')
        disp_coverart_check.set_active(self.settings.get_disp_coverart())
        disp_coverart_check.connect('toggled', self.on_disp_coverart_toggled,
                                    parent)
        general_vbox.add(disp_coverart_check)
        general_label = Gtk.Label(label='General')
        notebook.append_page(general_vbox, general_label)

        # The second tab contains preferences relating to IF filetypes and
        # interpreters.
        # Create a list store to hold the preferences.
        self.model = Gtk.ListStore(str, str, str)
        launchers = self.settings.get_launchers()
        launchers.sort()
        for e in launchers:
            ext = self.settings.get_file_exts(e[0])
            self.model.append((e[0], ext, e[1]))
        self.view = Gtk.TreeView(model=self.model)
        renderer = Gtk.CellRendererText()
        # Create a view to display the list store.
        self.view.append_column(Gtk.TreeViewColumn('Format', renderer, text=0))
        self.view.append_column(Gtk.TreeViewColumn('File types', renderer,
                                                   text=1))
        self.view.append_column(Gtk.TreeViewColumn('Interpreter', renderer,
                                                   text=2))
        self.view.connect('button_press_event', self.list_on_button_pressed)
        self.view.set_vexpand(True)
        self.view.set_hexpand(True)
        interpreters_hbox = Gtk.Grid()
        interpreters_hbox.set_orientation(Gtk.Orientation.HORIZONTAL)
        interpreters_hbox.set_column_homogeneous(False)
        interpreters_hbox.set_column_spacing(8)
        interpreters_vbox = Gtk.Grid()
        interpreters_vbox.set_orientation(Gtk.Orientation.VERTICAL)
        interpreters_vbox.set_row_homogeneous(False)
        interpreters_vbox.set_row_spacing(8)
        frame = Gtk.Frame(label=None)
        frame.set_shadow_type(Gtk.ShadowType.IN)
        # Create the buttons for adding, editing and removing interpreters...
        button_add = Gtk.Button("Add")
        button_edit = Gtk.Button("Edit")
        button_remove = Gtk.Button("Remove")
        button_add.connect('clicked', self.on_add)
        button_edit.connect('clicked', self.on_edit)
        button_remove.connect('clicked', self.on_remove)
        frame.add(self.view)
        frame.set_hexpand(True)
        interpreters_vbox.add(button_add)
        interpreters_vbox.add(button_edit)
        interpreters_vbox.add(button_remove)
        interpreters_hbox.add(frame)
        interpreters_hbox.add(interpreters_vbox)
        interpreters_label = Gtk.Label(label='Interpreters')
        notebook.append_page(interpreters_hbox, interpreters_label)

        vbox = self.get_child()
        vbox.pack_end(notebook, True, True, 0)
        self.set_default_size(400, 240)
        self.show_all()

    def on_fetch_metadata_toggled(self, fetch_metadata_check):
        '''This method handles when the user toggles the "Fetch metadata from
        IFDB" check button.

        '''
        fetch_metadata = fetch_metadata_check.get_active()
        self.settings.set_fetch_metadata(fetch_metadata)
        self.settings.save()

    def on_fetch_coverart_toggled(self, fetch_coverart_check):
        '''This method handles when the user toggles the "Fetch coverart from
        IFDB" check button.

        '''
        fetch_coverart = fetch_coverart_check.get_active()
        self.settings.set_fetch_coverart(fetch_coverart)
        self.settings.save()

    def on_disp_coverart_toggled(self, disp_coverart_check, parent):
        '''This method handles when the user toggles the "Display coverart"
        check button.

        '''
        disp_coverart = disp_coverart_check.get_active()
        self.settings.set_disp_coverart(disp_coverart)
        self.settings.save()
        info_paned = parent.info_paned
        info_paned.show_coverart(disp_coverart)

    def on_add(self, widget):
        '''This method handles when the user clicks the Add button on the
        interpreters tab.

        Create and run a dialog for adding a new interpreter.  If the user
        clicks OK, add the interpreter and filetype to the settings.

        '''
        dialog = self.create_interpreter_dialog('', '', '')
        if dialog.run() == Gtk.ResponseType.ACCEPT:
            if_format = dialog.entry_if_format.get_text()
            exts_str = dialog.entry_exts.get_text()
            exts = set(self.exts_re.findall(exts_str))
            exts_str = ','.join(exts)
            interpreter = dialog.entry_interpreter.get_text()
            self.settings.set_launcher(if_format, interpreter)
            self.settings.set_file_exts(if_format, exts_str)
            self.model.append((if_format, exts_str, interpreter))
            self.settings.save()
        dialog.destroy()

    def on_edit(self, widget):
        '''This method handles when the user clicks the Edit button on the
        interpreters tab.

        Get the selected interpreter and create a dialog for editing the
        interpreter's information. If the user clicks OK, remove the old
        information and add the new.

        '''
        selection = self.view.get_selection()
        if selection.count_selected_rows() > 0:
            (model, row_iter) = selection.get_selected()
            if_format = model.get_value(row_iter, 0)
            interpreter = self.settings.get_launcher(if_format)
            exts_str = self.settings.get_file_exts(if_format)
            exts = set(self.exts_re.findall(exts_str))
            dialog = self.create_interpreter_dialog(if_format, exts,
                                                    interpreter)
            if dialog.run() == Gtk.ResponseType.ACCEPT:
                n_if_format = dialog.entry_if_format.get_text()
                n_exts_str = dialog.entry_exts.get_text()
                n_exts = set(self.exts_re.findall(n_exts_str))
                n_exts_str = ','.join(n_exts)
                n_interpreter = dialog.entry_interpreter.get_text()
                if n_if_format != if_format:
                    self.settings.remove_launcher(if_format)
                    model.remove(row_iter)
                    model.append((n_if_format, n_exts_str, n_interpreter))
                elif n_exts != exts:
                    model.set_value(row_iter, 1, n_exts_str)
                elif n_interpreter != interpreter:
                    model.set_value(row_iter, 2, n_interpreter)
                self.settings.set_launcher(n_if_format, n_interpreter)
                self.settings.set_file_exts(n_if_format, n_exts_str)
                self.settings.save()
            dialog.destroy()

    def on_remove(self, widget):
        '''This method handles when the user clicks the Remove button on the
        interpreters tab.

        '''
        selection = self.view.get_selection()
        if selection.count_selected_rows() > 0:
            (model, row_iter) = selection.get_selected()
            self.settings.remove_launcher(model.get_value(row_iter, 0))
            self.settings.save()
            model.remove(row_iter)

    def list_on_button_pressed(self, widget, event):
        '''This method handles double-clicks on the interpreter list.  If the
        user double-clicks an interpreter entry, edit it.

        '''
        if event.button == 1 and event.type == Gdk.EventType._2BUTTON_PRESS:
            self.on_edit(widget)

    def create_interpreter_dialog(self, if_format, exts, interpreter):
        '''This method creates the dialog which is used for adding or editing
        an interpreter.

        '''
        dialog = Gtk.Dialog('Edit interpreter', self,
                            Gtk.DialogFlags.MODAL |
                            Gtk.DialogFlags.DESTROY_WITH_PARENT,
                            ("Cancel", Gtk.ResponseType.REJECT,
                             "OK", Gtk.ResponseType.ACCEPT))
        dialog.entry_if_format = Gtk.Entry()
        dialog.entry_exts = Gtk.Entry()
        dialog.entry_interpreter = Gtk.Entry()
        dialog.entry_if_format.set_text(if_format)
        dialog.entry_exts.set_text(','.join(exts))
        dialog.entry_interpreter.set_text(interpreter)
        table = Gtk.Grid()
        table.set_column_spacing(8)
        table.set_row_spacing(8)
        flabel = Gtk.Label(label='Format:')
        flabel.set_alignment(0.0, flabel.get_alignment()[1])
        table.attach(flabel, 0, 0, 1, 1)
        elabel = Gtk.Label(label='Extensions:')
        table.attach(elabel, 0, 1, 1, 1)
        ilabel = Gtk.Label(label='Interpreter:')
        table.attach(ilabel, 0, 2, 1, 1)
        table.attach(dialog.entry_if_format, 1, 0, 1, 1)
        table.attach(dialog.entry_exts, 1, 1, 1, 1)
        table.attach(dialog.entry_interpreter, 1, 2, 1, 1)
        open_image = Gtk.Image.new_from_icon_name(
            "document-open", Gtk.IconSize.MENU)
        ibutton = Gtk.Button()
        ibutton.set_image(open_image)
        ibutton.connect('clicked', self.on_find_interpreter,
                        dialog.entry_interpreter)
        table.attach(ibutton, 2, 2, 1, 1)
        vbox = dialog.get_child()
        vbox.add(table)
        dialog.show_all()
        return dialog

    def on_find_interpreter(self, widget, entry_interpreter):
        file_chooser = Gtk.FileChooserDialog(
            "Select an interpreter", self, Gtk.FileChooserAction.OPEN,
            ("Cancel", Gtk.ResponseType.CANCEL, "Open",
             Gtk.ResponseType.ACCEPT))
        file_chooser.set_select_multiple(False)
        # Run the dialog
        response = file_chooser.run()
        file_chooser.hide()
        if response == Gtk.ResponseType.ACCEPT:
            # Get the selected files.
            filepath = file_chooser.get_filename()
            if len(filepath) > 0:
                # Launch a dialog to handle the import.
                entry_interpreter.set_text(filepath)
        file_chooser.destroy()
