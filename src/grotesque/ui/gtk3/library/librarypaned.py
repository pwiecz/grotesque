# -*- coding: utf-8 -*-
#
#       librarypaned.py
#
#       Copyright © 2011, 2014, 2015, 2018 Brandon Invergo <brandon@invergo.net>
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


import time

from gi.repository import Gtk, Gdk, GObject

from libraryview import LibraryView
from libraryfilterview import LibraryFilterView


class LibraryPaned(Gtk.Paned):
    '''This class implements the main widget which displays information
    about the library, including the view of the library and the list
    of filters.  Many of the class's methods exist to abstract and
    simplify the process of getting iters which point to valid rows in
    a filtered list store.

    '''
    __gsignals__ = {'selection-changed': (GObject.SignalFlags.RUN_LAST, None,
                                          ()),
                    'double-clicked': (GObject.SignalFlags.RUN_LAST, None,
                                       ())}

    def __init__(self, library, settings):
        super(LibraryPaned, self).__init__()
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.library = library
        self.settings = settings
        self.library_view = LibraryView(self.library)
        self.filter_view = LibraryFilterView(self.library)
        self.col_menu = Gtk.Menu()
        # Get all the columns from the library view.
        view_columns = self.library_view.get_columns()
        for col in view_columns:
            col_title = col.get_title()
            # The 'rating_num' column is only for sorting the star ratings
            # column, so it should be invisible.
            if col_title == 'rating_num':
                col.set_visible(False)
                continue
            width = self.settings.get_column_width(col_title)
            col_visible = self.settings.get_column_visible(col_title)
            col.set_visible(col_visible)
            if col_visible:
                col.set_fixed_width(width)
            header = col.get_button()
            header.connect('button_press_event', self.on_list_header_clicked)
            self.col_menu_item = Gtk.CheckMenuItem(label=col_title)
            self.col_menu_item.set_active(col_visible)
            self.col_menu_item.connect('toggled', self.on_col_menu_toggled)
            self.col_menu.append(self.col_menu_item)
            self.col_menu_item.show()
        selection = self.library_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        selection.connect('changed', self.on_selection_changed)
        self.library_view.connect('button_press_event',
                                  self.on_list_button_pressed)

        library_scroll = Gtk.ScrolledWindow()
        library_scroll.set_policy(Gtk.PolicyType.AUTOMATIC,
                                  Gtk.PolicyType.AUTOMATIC)
        library_scroll.add(self.library_view)
        library_scroll.set_vexpand(True)
        library_scroll.set_hexpand(True)

        filter_scroll = Gtk.ScrolledWindow()
        filter_scroll.set_policy(Gtk.PolicyType.AUTOMATIC,
                                 Gtk.PolicyType.AUTOMATIC)
        filter_scroll.add(self.filter_view)
        filter_scroll.set_vexpand(True)
        filter_scroll.set_hexpand(True)
        filter_selection = self.filter_view.get_selection()
        filter_selection.connect('changed', self.on_filter_selection_changed)

        self.filter_combo = Gtk.ComboBoxText.new()
        self.filter_combo.append_text('Author')
        self.filter_combo.append_text('Group')
        self.filter_combo.append_text('Year')
        self.filter_combo.append_text('Genre')
        self.filter_combo.append_text('Series')
        self.filter_combo.append_text('Forgiveness')
        self.filter_combo.append_text('Language')
        self.filter_combo.append_text('Minimum Rating')
        self.filter_combo.append_text('Minimum IFDB Rating')
        self.filter_combo.append_text('Tag')
        self.filter_combo.set_active(self.settings.get_filter_type())
        self.filter_combo.connect('changed', self.on_filter_combo_changed)
        self.filter_view.set_filter_type(self.filter_combo.get_active_text())

        filter_vbox = Gtk.Grid()
        filter_vbox.set_orientation(Gtk.Orientation.VERTICAL)
        filter_vbox.add(self.filter_combo)
        filter_vbox.add(filter_scroll)

        self.pack1(filter_vbox, True, False)
        self.pack2(library_scroll, True, False)

    def get_selected_rows(self):
        '''This method returns a list of iters pointing to the currently
        selected rows of the potentially filtered library view.

        '''
        selection = self.library_view.get_selection()
        (model, rows) = selection.get_selected_rows()
        row_iters = []
        for row in rows:
            row_iters.append(self.get_filter_iter(row, model))
        return row_iters

    def get_selected_stories(self):
        '''This method returns a list of story files that are currently
        selected as well as the iters that point to their rows in the list
        store.

        '''
        stories = []
        row_iters = self.get_selected_rows()
        for row_iter in row_iters:
            try:
                stories.append(self.library.get_story_id(row_iter))
            except:
                stories.append(None)
        return zip(stories, row_iters)

    def get_filter_iter(self, path, sorted_model):
        '''This is a helper method which simplifies the process of getting a
        valid iter after the library view has been filtered and/or sorted.

        '''
        sortable_filter_iter = sorted_model.get_iter(path)
        filter_iter = sorted_model.convert_iter_to_child_iter(
            sortable_filter_iter)
        filter_model = self.filter_view.filter_model
        if filter_model is None:
            return filter_iter
        filter_selection = self.filter_view.get_selection()
        if filter_selection.count_selected_rows() == 0:
            return filter_iter
        return filter_model.convert_iter_to_child_iter(filter_iter)

    def on_col_menu_toggled(self, col_menu_item):
        '''This method handles the toggling of the check boxes in the library
        view context menu, which are used for activating/deactivating columns.

        '''
        col_title = col_menu_item.get_label()
        col = self.library_view.get_col_by_title(col_title)
        col_visible = col_menu_item.get_active()
        col.set_visible(col_visible)

    def on_list_header_clicked(self, widget, event):
        '''This method handles click events on the header area of the library
        view, which are used to popup the column activation/deactivation menu.

        '''
        if ((event.button == Gdk.BUTTON_SECONDARY and
             event.type == Gdk.EventType.BUTTON_PRESS)):
            if not self.col_menu.get_attach_widget():
                self.col_menu.attach_to_widget(widget.get_toplevel(), None)
            self.col_menu.popup(None, None, None, None, event.button,
                                event.time)
            return True
        return False

    def on_list_button_pressed(self, widget, event):
        '''This method handles button presses on the main content area of the
        library view. A double-click event of the left mouse button is
        sent up to the main window for launching a story, while a
        single right-click pops up a context menu.

        '''
        if event.button == 1 and event.type == Gdk.EventType._2BUTTON_PRESS:
            self.emit('double-clicked')
        if event.button == 3 and event.type == Gdk.EventType.BUTTON_PRESS:
            row_iters = self.get_selected_rows()
            list_context_menu = Gtk.Menu()
            context_menu_played = Gtk.MenuItem(label='Toggle played')
            context_menu_played.connect('activate',
                                        self.on_list_context_played, row_iters)
            list_context_menu.append(context_menu_played)
            context_menu_played.show()
            context_menu_refresh = Gtk.MenuItem(label='Refresh IFDB annotation')
            context_menu_refresh.connect('activate',
                                        self.on_list_context_refresh, row_iters)
            list_context_menu.append(context_menu_refresh)
            context_menu_refresh.show()
            list_context_menu.attach_to_widget(self.library_view, None)
            list_context_menu.popup(None, None, None, None, event.button,
                                    event.time)

    def on_list_context_played(self, menuitem, row_iters):
        '''This method handles clicks on the "Toggle played" context menu
        entry, which marks stories as played or not.

        '''
        for row_iter in row_iters:
            self.library.toggle_story_played(row_iter)

    def on_list_context_refresh(self, menuitem, row_iters):
        '''This method handles clicks on the "Toggle played" context menu
        entry, which marks stories as played or not.

        '''
        limit = self.settings.get_ifdb_limit()
        delay = 60/limit
        for row_iter in row_iters:
            self.library.refresh_ifdb(row_iter)
            time.sleep(delay)
        if len(row_iters) > 0:
            filter_select = self.filter_view.get_selection()
            (model, sel) = filter_select.get_selected_rows()
            self.library.update_filter_stores()
            filter_select.select_path(sel)

    def on_selection_changed(self, selection):
        '''This method handles the library view's selection changing by passing
        it up to the main window.

        '''
        self.emit('selection-changed')

    def on_filter_selection_changed(self, selection):
        '''This method handles the filter selection changing (ie the text by
        which to filter the library).

        '''
        (model, row) = selection.get_selected()
        if not model or not row:
            return
        filter_type = self.filter_combo.get_active_text()
        if filter_type == 'Minimum Rating':
            filter_type = 'rating_num'
        elif filter_type == 'Minimum IFDB Rating':
            filter_type = 'ifdb_rating_num'
        filter_text = model.get_value(row, 0)
        filter_id = model.get_value(row, 1)
        filter_col = self.library_view.get_col_number(filter_type)
        filter_model = self.filter_view.filter_library(
            filter_type, filter_text, filter_id, filter_col)
        self.library_view.set_model(filter_model)

    def on_filter_combo_changed(self, combo):
        '''This method handles the combo box containing the filter types
        changing.

        '''
        new_filter_type = combo.get_active_text()
        self.filter_view.set_filter_type(new_filter_type)
