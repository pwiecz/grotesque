# -*- coding: utf-8 -*-
#
#       mainwindow.py
#
#       Copyright © 2011, 2014, 2015, 2017, 2018 Brandon Invergo <brandon@invergo.net>
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


import os.path

import gi
from gi.repository import Gtk, Gdk, GObject
from library.library import Library
from library.librarypaned import LibraryPaned
from dialogs.settingsdialog import SettingsDialog
from dialogs.progressdialog import ProgressDialog
from dialogs.editdialog import EditDialog
from info.infopaned import InfoPaned
from threads.storyimportthread import StoryImportThread
from threads.ifictionimportthread import IfictionImportThread
from threads.storyremovethread import StoryRemoveThread
from grotesque import db, util


GROTESQUE_VERSION = "0.10"


class MainWindow(Gtk.Window):
    '''This class implements the main Grotesque window.

    '''
    biblio_width = 600
    info_width = 280


    def __init__(self, conn, settings):
        super(MainWindow, self).__init__(type=Gtk.WindowType.TOPLEVEL)
        self.conn = conn
        # init_complete is used to block certain callbacks from happening while
        # the window is still being constructed.
        self.init_complete = False
        self.set_title('Grotesque')
        self.set_icon_from_file(
            os.path.join(os.path.dirname(__file__), '..', '..', 'data',
                         'grotesque_icon.png'))
        self.connect('delete_event', self.on_close)
        self.settings = settings
        dimensions = settings.get_window_size()
        self.set_default_size(dimensions[0], dimensions[1])
        self.connect('key_press_event', self.on_key_pressed)

        # Create the library and its display widgets.
        self.library = Library(self.conn)
        self.library_paned = LibraryPaned(self.library, self.settings)
        self.library_paned.connect('selection-changed',
                                   self.on_library_selection_changed)
        self.library_paned.connect('double-clicked',
                                   self.on_library_doubleclick)
        filter_percentage = self.settings.get_filter_percentage()
        self.library_paned.set_position(int(dimensions[0] * filter_percentage))

        # Create the info (story description & coverart) area
        vpaned_percentage = self.settings.get_vpaned_percentage()
        self.info_paned = InfoPaned(self.settings, self.conn)
        self.info_paned.connect('notify', self.on_infopaned_notify)
        info_pos = int(dimensions[1] - (dimensions[1] * vpaned_percentage))
        self.info_paned.set_position(info_pos)
        info_width = dimensions[0] - info_pos - self.info_width
        self.info_paned.text_view.set_position(info_width)
        if info_width > self.biblio_width:
            new_margin = (info_width - self.biblio_width)/2
            self.info_paned.text_view.biblio_view.set_left_margin(new_margin)
            self.info_paned.text_view.biblio_view.set_right_margin(new_margin)
        else:
            self.info_paned.text_view.biblio_view.set_left_margin(20)
            self.info_paned.text_view.biblio_view.set_right_margin(20)
        self.info_paned_block = False

        # Pack it all together.
        top_frame = Gtk.Frame()
        self.bottom_frame = Gtk.Frame()
        top_frame.set_shadow_type(Gtk.ShadowType.IN)
        self.bottom_frame.set_shadow_type(Gtk.ShadowType.IN)
        top_frame.add(self.library_paned)
        self.bottom_frame.add(self.info_paned)
        self.info_paned.show_coverart(self.settings.get_disp_coverart())
        toolbar = self.create_toolbar()
        top_frame_box = Gtk.Grid()
        top_frame_box.set_orientation(Gtk.Orientation.VERTICAL)
        top_frame_box.add(toolbar)
        top_frame.set_vexpand(True)
        top_frame_box.add(top_frame)

        self.vpaned = Gtk.Paned()
        self.vpaned.set_orientation(Gtk.Orientation.VERTICAL)
        self.vpaned.connect('notify', self.on_vpaned_notify)
        self.vpaned.pack1(top_frame_box, True, False)
        self.vpaned.pack2(self.bottom_frame, False, False)
        self.vpaned.set_position(int(dimensions[1] * vpaned_percentage))
        self.vpaned_block = False
        self.add(self.vpaned)

        self.show_all()
        self.init_complete = True

    def create_toolbar(self):
        '''This method creates the main toolbar.

        '''
        toolbar = Gtk.Toolbar()
        toolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        separator1 = Gtk.SeparatorToolItem()
        separator2 = Gtk.SeparatorToolItem()
        separator3 = Gtk.SeparatorToolItem()
        button_add = Gtk.ToolButton(icon_name="list-add")
        button_add.set_tooltip_text("Add a story to the library")
        button_dir = Gtk.ToolButton(icon_name="folder")
        button_dir.set_tooltip_text(
            "Import all stories in a directory to the library")
        self.button_play = Gtk.ToolButton(icon_name="media-playback-start")
        self.button_play.set_tooltip_text("Play the selected story")
        button_export = Gtk.ToolButton(icon_name="document-save")
        button_export.set_tooltip_text(
            "Export the library to an IFiction file")
        button_import = Gtk.ToolButton(icon_name="document-open")
        button_import.set_tooltip_text(
            "Import stories from an IFiction file to the library")
        # button_dir.set_label('Import')
        self.button_remove = Gtk.ToolButton(icon_name="list-remove")
        self.button_remove.set_tooltip_text(
            "Remove the selected story/stories from the library")
        self.button_edit = Gtk.ToolButton(icon_name="document-properties")
        self.button_edit.set_tooltip_text(
            "Edit the selected story/stories")
        button_preferences = Gtk.ToolButton(icon_name="preferences-desktop")
        button_preferences.set_tooltip_text(
            "Configure Grotesque")
        button_about = Gtk.ToolButton(icon_name="help-about")
        button_about.set_tooltip_text("About Grotesque")

        toolbar.add(self.button_play)
        toolbar.add(separator1)
        toolbar.add(button_export)
        toolbar.add(button_import)
        toolbar.add(separator2)
        toolbar.add(button_dir)
        toolbar.add(button_add)
        toolbar.add(self.button_remove)
        toolbar.add(self.button_edit)
        toolbar.add(separator3)
        toolbar.add(button_preferences)
        toolbar.add(button_about)
        self.button_play.connect_object('clicked', self.on_play, self)
        button_export.connect_object('clicked', self.on_export, self)
        button_import.connect_object('clicked', self.on_import, self)
        button_dir.connect_object('clicked', self.on_add_dir, self)
        button_add.connect_object('clicked', self.on_add, self)
        self.button_remove.connect_object('clicked', self.on_remove, self)
        self.button_edit.connect_object('clicked', self.on_edit, self)
        button_about.connect_object('clicked', self.on_about, self)
        button_preferences.connect_object('clicked', self.on_preferences, self)

        self.button_play.set_sensitive(False)
        self.button_remove.set_sensitive(False)
        self.button_edit.set_sensitive(False)
        return toolbar

    def play_selection(self):
        '''This method grabs the currently selected story and sends it to be
        launched.

        '''
        selected_stories = self.library_paned.get_selected_stories()
        if not selected_stories:
            return
        selected_story = selected_stories[0]
        story_id = selected_story[0]
        try:
            db.launch_story(self.conn, self.settings, story_id)
        except ValueError as e:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR, Gtk.ButtonsType.OK)
            d.set_markup(str(e))
            d.run()
            d.destroy()
            return
        self.library.mark_story_played(selected_story[1])

    def remove_selection(self):
        '''This method grabs the currently selected stories and creates a
        thread to handle removing them from the library.

        '''
        row_iters = self.library_paned.get_selected_rows()
        if len(row_iters) > 0:
            remove_dialog = ProgressDialog("Removing...", self, False)
            remove_thread = StoryRemoveThread(self.library, row_iters,
                                              self.conn, remove_dialog)
            removing = remove_thread.remove_stories()
            GObject.idle_add(removing.next)
            remove_dialog.run()
            remove_dialog.destroy()
        self.library_paned.filter_view.select_all()
        self.info_paned.clear()

    def do_import_story_dialog(self, filepaths):
        '''This method launches a thread which handles the actual importing of
        story files. If any files failed to be imported properly, the user has
        the option of manually editing their metadata.

        '''
        import_dialog = ProgressDialog("Importing...", self)
        import_thread = StoryImportThread(filepaths, self.settings,
                                          self.library, import_dialog,
                                          self.conn)
        importing = import_thread.import_stories()
        GObject.idle_add(importing.next)
        import_response = import_dialog.run()
        import_dialog.destroy()
        if (import_response == Gtk.ResponseType.REJECT or
                import_response == Gtk.ResponseType.DELETE_EVENT):
            import_thread.stop()
        else:
            # If any files failed to import, create a dialog for editing them.
            if len(import_thread.fails) > 0:
                d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                      Gtk.MessageType.QUESTION,
                                      Gtk.ButtonsType.YES_NO)
                d_msg = ()
                d.set_markup('Metadata could not be retrieved for {0} '
                             'files.\nWould you like to edit them '
                             'now?'.format(len(import_thread.fails)))
                edit_response = d.run()
                d.destroy()
                if edit_response == Gtk.ResponseType.YES:
                    edit_dialog = EditDialog(self.conn, self.settings, self,
                                             True)
                    for n, story_id in enumerate(import_thread.fails):
                        edit_dialog.load_story(story_id)
                        if len(import_thread.fails) > 1:
                            edit_dialog.set_title(
                                'Story Information ({0}/{1})'.format(
                                    n + 1, len(import_thread.fails)))
                        else:
                            edit_dialog.set_title('Story Information')
                        row_iter = self.library.story_iter(story_id)
                        response = edit_dialog.run()
                        if response == Gtk.ResponseType.ACCEPT:
                            if row_iter:
                                self.library.list_store.remove(row_iter)
                            if edit_dialog.merged:
                                story_id = edit_dialog.story_id
                            else:
                                self.library.add_story_from_db_rec(
                                    db.query.select_story(self.conn, story_id))
                                filter_select = self.library_paned.filter_view.get_selection()
                                (model, sel) = filter_select.get_selected_rows()
                                self.library.update_filter_stores()
                                if sel:
                                    filter_select.select_path(sel)
                                else:
                                    self.library_paned.filter_view.select_all()
                        elif response == Gtk.ResponseType.REJECT:
                            db.remove_story(self.conn, story_id)
                            if row_iter is not None:
                                self.library.list_store.remove(row_iter)
                    edit_dialog.destroy()
            # If any errors were encountered during import, display them here.
            if len(import_thread.msg) > 0:
                d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                      Gtk.MessageType.WARNING,
                                      Gtk.ButtonsType.OK)
                d_msg = 'Errors encountered while adding games:\n\n{0}'.format(
                    import_thread.msg)
                d.set_markup(d_msg)
                d.run()
                d.destroy()
            selected_stories = self.library_paned.get_selected_stories()
            if (selected_stories and
                    db.query.select_story(self.conn, selected_stories[0][0])):
                self.info_paned.show_story(selected_stories[0][0])
        self.library_paned.filter_view.select_all()

    def do_import_ifiction_dialog(self, ifiction_file):
        '''This method launches a thread which handles the actual importing of
        an ifiction files.

        '''
        import_dialog = ProgressDialog("Importing...", self)
        import_thread = IfictionImportThread(
            ifiction_file, self.settings, self.library, import_dialog,
            self.conn)
        try:
            importing = import_thread.import_ifiction()
        except IOError:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.CLOSE)
            d_msg1 = 'Selected file is not an IFiction file.'
            d.set_markup(d_msg1)
            d.run()
            d.destroy()
            import_dialog.destroy()
            return
        GObject.idle_add(importing.next)
        import_response = import_dialog.run()
        import_dialog.destroy()
        if (import_response == Gtk.ResponseType.REJECT or
                import_response == Gtk.ResponseType.DELETE_EVENT):
            import_thread.stop()
        else:
            selected_stories = self.library_paned.get_selected_stories()
            if (selected_stories and
                    db.query.select_story(self.conn, selected_stories[0][0])):
                self.info_paned.show_story(selected_stories[0][0])
        self.library_paned.filter_view.select_all()

    def on_vpaned_notify(self, vpaned, gparamspec):
        '''This method catches notify signals from the vpaned widget which
        separates the library view from the info view.  In particular, it is
        used to determine if the handle position has changed.  If it has
        changed, then the handle of the info paned should also be moved so that
        the coverart area is always square.

        '''
        if gparamspec.name == 'position':
            if self.init_complete and not self.vpaned_block:
                self.info_paned_block = True
                dimensions = self.get_size()
                new_width = dimensions[1] - self.vpaned.get_position()
                self.info_paned.set_position(new_width)
                info_width = dimensions[0] - new_width - self.info_width
                self.info_paned.text_view.set_position(info_width)
                if info_width > self.biblio_width:
                    new_margin = (info_width - self.biblio_width)/2
                    self.info_paned.text_view.biblio_view.set_left_margin(new_margin)
                    self.info_paned.text_view.biblio_view.set_right_margin(new_margin)
                else:
                    self.info_paned.text_view.biblio_view.set_left_margin(20)
                    self.info_paned.text_view.biblio_view.set_right_margin(20)
                selected_story = self.library_paned.get_selected_stories()
                if len(selected_story) > 0:
                    self.info_paned.refresh_coverart(selected_story[0][0])
                self.info_paned_block = False

    def on_infopaned_notify(self, hpaned, gparamspec):
        '''This method catches notify signals from the vpaned widget which
        separates the library view from the info view.  If the info paned
        handle is moved, then the vpaned handle should be moved as well to keep
        the cover art area square.

        '''
        if gparamspec.name == 'position':
            if self.init_complete and not self.info_paned_block:
                self.vpaned_block = True
                dimensions = self.get_size()
                new_width = dimensions[0] - self.info_paned.get_position()
                new_height = dimensions[1] - self.info_paned.get_position()
                self.vpaned.set_position(new_height)
                info_width = new_width - self.info_width
                self.info_paned.text_view.set_position(info_width)
                if info_width > self.biblio_width:
                    new_margin = (info_width - self.biblio_width)/2
                    self.info_paned.text_view.biblio_view.set_left_margin(new_margin)
                    self.info_paned.text_view.biblio_view.set_right_margin(new_margin)
                else:
                    self.info_paned.text_view.biblio_view.set_left_margin(20)
                    self.info_paned.text_view.biblio_view.set_right_margin(20)
                selected_story = self.library_paned.get_selected_stories()
                if len(selected_story) > 0:
                    self.info_paned.refresh_coverart(selected_story[0][0])
                self.vpaned_block = False

    def on_key_pressed(self, widget, event):
        '''This method handles keypresses on the main window.

        '''
        if Gdk.keyval_name(event.keyval) == "Delete":
            self.remove_selection()
        elif Gdk.keyval_name(event.keyval) == "Return":
            self.play_selection()

    def on_remove(self, widget):
        '''This method handles the remove toolbar button being clicked.

        '''
        self.remove_selection()

    def on_play(self, widget):
        '''This method handles the play toolbar button being clicked.

        '''
        self.play_selection()

    def on_import(self, widget):
        '''Handle the import toolbar button being clicked.'''
        file_chooser = Gtk.FileChooserDialog(
            "Select an IFiction file to import", self,
            Gtk.FileChooserAction.OPEN,
            ("Cancel", Gtk.ResponseType.CANCEL, "Open",
             Gtk.ResponseType.ACCEPT))
        file_chooser.set_select_multiple(False)
        response = file_chooser.run()
        file_chooser.hide()
        if response == Gtk.ResponseType.ACCEPT:
            ific_file = file_chooser.get_filename()
            if len(ific_file) > 0:
                # Launch a dialog to handle the import.
                self.do_import_ifiction_dialog(ific_file)
        file_chooser.destroy()

    def on_export(self, widget):
        '''Handle the export toolbar button being clicked.'''
        # Create and lanch the file chooser.
        selected_stories = self.library_paned.get_selected_stories()
        story_ids = [story_id for story_id, row_iter in selected_stories]
        file_chooser = Gtk.FileChooserDialog(
            "Select a destination for library IFiction export", self,
            Gtk.FileChooserAction.SAVE,
            ("Cancel", Gtk.ResponseType.CANCEL, "Save",
             Gtk.ResponseType.ACCEPT))
        file_chooser.set_select_multiple(False)
        response = file_chooser.run()
        file_chooser.hide()
        if response == Gtk.ResponseType.ACCEPT:
            ific_file = file_chooser.get_filename()
            with open(ific_file, 'w') as h:
                db.export_ifiction(
                    self.conn, h, story_ids, GROTESQUE_VERSION)
        file_chooser.destroy()

    def on_add(self, widget):
        '''This method handles the add toolbar button ('+' icon, single file)
        being clicked.

        '''
        exts = []
        all_exts = self.settings.get_all_exts()
        for if_format, format_exts in all_exts:
            exts.extend(format_exts.split(','))
        exts_set = set(exts)
        # Create a file filter to only show valid story files.
        story_filter = Gtk.FileFilter()
        story_filter.set_name("Story files")
        for ext in exts_set:
            story_filter.add_pattern('*{0}'.format(ext))
            story_filter.add_pattern('*{0}'.format(ext.upper()))
        all_filter = Gtk.FileFilter()
        # Create a filter to show all files.
        all_filter.set_name("All files")
        all_filter.add_pattern("*")
        # Create the file chooser dialog and add the filters.
        file_chooser = Gtk.FileChooserDialog(
            "Select game files to add", self, Gtk.FileChooserAction.OPEN,
            ("Cancel", Gtk.ResponseType.CANCEL, "Open",
             Gtk.ResponseType.ACCEPT))
        file_chooser.set_select_multiple(True)
        file_chooser.set_current_folder(self.settings.get_game_dir())
        file_chooser.add_filter(story_filter)
        file_chooser.add_filter(all_filter)
        # Run the dialog
        response = file_chooser.run()
        file_chooser.hide()
        if response == Gtk.ResponseType.ACCEPT:
            # Save this directory as the last-accessed one
            self.settings.set_game_dir(file_chooser.get_current_folder())
            self.settings.save()
            # Get the selected files.
            filepaths = file_chooser.get_filenames()
            if len(filepaths) > 0:
                # Launch a dialog to handle the import.
                self.do_import_story_dialog(filepaths)
        file_chooser.destroy()

    def on_add_dir(self, widget):
        '''This method handles the add directory toolbar (folder icon,
        recursive import) being clicked.

        '''
        # Create a list of extensions to handle.
        exts = []
        all_exts = self.settings.get_all_exts()
        for if_format, format_exts in all_exts:
            exts.extend(format_exts.split(','))
        exts_set = set(exts)
        # Create and lanch the file chooser.
        file_chooser = Gtk.FileChooserDialog(
            "Select a directory to add", self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            ("Cancel", Gtk.ResponseType.CANCEL, "Open",
             Gtk.ResponseType.ACCEPT))
        file_chooser.set_select_multiple(False)
        file_chooser.set_current_folder(self.settings.get_game_dir())
        response = file_chooser.run()
        file_chooser.hide()
        if response == Gtk.ResponseType.ACCEPT:
            filepaths = []
            self.settings.set_game_dir(file_chooser.get_current_folder())
            self.settings.save()
            directory = file_chooser.get_filename()
            for dirpath, dirnames, filenames in os.walk(directory):
                # For all the files found, if they have the correct extension,
                # add them for import.
                if len(filenames) > 0:
                    for filename in filenames:
                        extension = os.path.splitext(filename)[1]
                        if extension.lower() in exts_set:
                            filepath = os.path.join(dirpath, filename)
                            filepaths.append(filepath)
            if len(filepaths) > 0:
                # Assuming files were found, run the import dialog.
                self.do_import_story_dialog(filepaths)
        file_chooser.destroy()

    def on_edit(self, widget):
        '''This method handles the edit button being clicked.

        '''

        edit_dialog = EditDialog(self.conn, self.settings, self, False)
        selected_stories = self.library_paned.get_selected_stories()
        for n, selected_story in enumerate(selected_stories):
            story_id, row_iter = selected_story
            edit_dialog.load_story(story_id)
            if len(selected_stories) > 1:
                edit_dialog.set_title(
                    'Story Information ({0}/{1})'.format(
                        n + 1, len(selected_stories)))
            else:
                edit_dialog.set_title('Story Information')
            response = edit_dialog.run()
            if response == Gtk.ResponseType.ACCEPT:
                if edit_dialog.merged:
                    self.library.list_store.remove(row_iter)
                    story_id = edit_dialog.story_id
                if edit_dialog.edited:
                    self.library.add_story_from_db_rec(
                        db.query.select_story(self.conn, story_id), row_iter)
                    filter_select = self.library_paned.filter_view.get_selection()
                    (model, sel) = filter_select.get_selected_rows()
                    self.library.update_filter_stores()
                    filter_select.select_path(sel)
        edit_dialog.destroy()
        if (selected_stories and
                db.query.select_story(self.conn, selected_stories[0][0])):
            self.info_paned.show_story(selected_stories[0][0])

    def on_preferences(self, widget):
        '''This method handles clicks on the preferences button.

        '''
        settings_dialog = SettingsDialog(self.settings, self)
        settings_dialog.run()
        settings_dialog.destroy()

    def on_about(self, widget):
        '''This method handles clicks on the about button.

        '''
        about = Gtk.AboutDialog()
        about.set_program_name('Grotesque')
        about.set_version(' '.join(['Version', GROTESQUE_VERSION]))
        comment = 'Organize and explore your Interactive Fiction library.'
        about.set_comments(comment)
        copyright_per = 'Copyright © 2009, 2010 Per Liedman'
        copyright_brandon = 'Copyright © 2011, 2012, 2014, 2015, 2016, 2017, 2018 Brandon Invergo'
        about.set_copyright('\n'.join([copyright_brandon, copyright_per]))
        about.set_license_type(Gtk.License.GPL_3_0)
        about.set_website('http://grotesque.invergo.net')
        about.set_website_label('Grotesque Website')
        about.set_logo(self.get_icon())
        about.set_authors(['Brandon Invergo', '\n', 'Past Developers:',
                           'Per Liedman'])
        about.show_all()
        about.run()
        about.destroy()

    def on_library_selection_changed(self, library_paned):
        '''This method handles events in which the library selection changed.
        In particulary, this affects displaying info in the info paned and the
        active state of toolbar buttons.

        '''
        row_iters = self.library_paned.get_selected_rows()
        if len(row_iters) == 0:
            return
        if len(row_iters) == 1:
            story = self.library.get_story_id(row_iters[0])
            self.info_paned.show_story(story)
        elif len(row_iters) > 1:
            self.info_paned.clear()
        rows_selected = len(row_iters)
        self.button_play.set_sensitive(rows_selected == 1)
        self.button_edit.set_sensitive(rows_selected > 0)
        self.button_remove.set_sensitive(rows_selected > 0)

    def on_library_doubleclick(self, library_paned):
        self.play_selection()

    def on_close(self, widget, event, data=None):
        '''This method handles the window being closed. In particular, it
        handles saving settings and saving the library before exiting the main
        GTK loop.

        '''
        size = self.get_size()
        pos = self.vpaned.get_position()
        library_pos = self.library_paned.get_position()
        filter_type = self.library_paned.filter_combo.get_active()
        vpaned_percentage = float(pos) / float(size[1])
        library_percentage = float(library_pos) / float(size[0])
        self.settings.set_window_size(size)
        self.settings.set_vpaned_percentage(vpaned_percentage)
        self.settings.set_filter_percentage(library_percentage)
        self.settings.set_filter_type(filter_type)
        for col in self.library_paned.library_view.get_columns():
            width = col.get_width()
            title = col.get_title()
            self.settings.set_column_width(title, width)
            visible = col.get_visible()
            self.settings.set_column_visible(title, visible)
        self.settings.save()
        Gtk.main_quit()
        return False
