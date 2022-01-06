# -*- coding: utf-8 -*-
#
#       libraryfilterview.py
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


from gi.repository import Gtk
import locale


class LibraryFilterView(Gtk.TreeView):
    '''This class implements the view which displays library filters.

    '''
    def __init__(self, library):
        super(LibraryFilterView, self).__init__()
        self.set_headers_visible(False)
        self.set_rules_hint(True)
        self.library = library
        self.filter_model = None

    def select_all(self):
        select = self.get_selection()
        select.select_path(0)

    def set_filter_type(self, type_text):
        '''This model sets which model to display in the view.

        '''
        # Get the model based on the filter type
        self.filter_model = {
            'Author': self.library.author_store,
            'Year': self.library.year_store,
            'Genre': self.library.genre_store,
            'Group': self.library.group_store,
            'Series': self.library.series_store,
            'Forgiveness': self.library.forgiveness_store,
            'Minimum Rating': self.library.rating_store,
            'Minimum IFDB Rating': self.library.ifdb_rating_store,
            'Language': self.library.lang_store,
            'Tag': self.library.tag_store}.get(
                type_text)
        # Sort the contents of the model
        self.sorted_model = Gtk.TreeModelSort.new_with_model(
            self.filter_model)
        self.sorted_model.set_sort_func(0, self._sort, type_text)
        self.set_model(self.sorted_model)
        # If the view already has columns defined, remove them.
        old_columns = self.get_columns()
        if old_columns:
            for old_column in old_columns:
                self.remove_column(old_column)
        # Otherwise, just make a normal text column.
        filter_renderer = Gtk.CellRendererText()
        str_col = Gtk.TreeViewColumn('filter', filter_renderer, text=0)
        str_col.set_sort_column_id(0)
        self.append_column(str_col)
        id_renderer = Gtk.CellRendererText()
        id_col = Gtk.TreeViewColumn('filter', id_renderer, text=1)
        id_col.set_visible(False)
        id_col.set_sort_column_id(0)
        self.append_column(id_col)
        if type_text == "Forgiveness":
            self.sorted_model.set_sort_column_id(1, Gtk.SortType.ASCENDING)
        else:
            self.sorted_model.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        self.select_all()

    def _sort(self, model, iter1, iter2, filter_type):
        '''This method defines how to sort the contents of the filter store,
        accounting for the "(All)" entries, which should remain at the top.

        '''
        value1 = model.get_value(iter1, 0)
        value2 = model.get_value(iter2, 0)
        if value1 == '(All)':
            return -1
        elif value2 == '(All)':
            return 1
        elif filter_type in ["Minimum Rating", "Minimum IFDB Rating"]:
            if value1 < value2:
                return -1
            elif value1 > value2:
                return 1
            else:
                return 0
        else:
            return locale.strcoll(value1, value2)

    def _filter_visible(self, model, row_iter, data):
        '''This method determines whether or not a story should be visible
        given the current filter.

        '''
        (filter_type, filter_text, filter_id, filter_col) = data
        if filter_text == '(All)':
            return True
        else:
            value = model.get_value(row_iter, filter_col)
            if filter_type in ['rating_num', 'ifdb_rating_num']:
                return float(filter_id)/2.0 + 0.5 <= value
            else:
                return value and filter_text in value

    def filter_library(self, filter_type, filter_text, filter_id, filter_col):
        '''This method filters the library.

        '''
        self.filter_model = self.library.list_store.filter_new(None)
        self.filter_model.set_visible_func(
            self._filter_visible, (filter_type, filter_text, filter_id,
                                   filter_col))
        self.filter_model.refilter()
        sortable_filter_model = Gtk.TreeModelSort.new_with_model(
            self.filter_model)
        sortable_filter_model.connect("sort-column-changed",
                                      self.on_library_sort_column_changed)
        sort_col, sort_order = self.library.list_store.get_sort_column_id()
        sortable_filter_model.set_sort_column_id(
            sort_col, sort_order)
        return sortable_filter_model

    def on_library_sort_column_changed(self, sortable_model):
        sort_col, sort_order = sortable_model.get_sort_column_id()
        self.library.list_store.set_sort_column_id(sort_col, sort_order)
