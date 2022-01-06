# -*- coding: utf-8 -*-
#
#       libraryview.py
#
#       Copyright © 2011, 2014, 2015, 2018 Brandon Invergo <brandon@invergo.net>
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


from gi.repository import Gtk


class LibraryView(Gtk.TreeView):
    '''This class implements a widget which displays the contents of the
    library.

    '''
    star_rating_float_col = 15
    ifdb_rating_float_col = 16
    weight_col = 18

    def __init__(self, library):
        self.library = library
        filter_model = self.library.list_store.filter_new(None)
        super(LibraryView, self).__init__(model=filter_model)
        self.set_rules_hint(True)
        self.set_headers_clickable(True)
        # When the user types on the view, it searches by column 1, which will
        # be the story titles.
        self.set_search_column(1)
        self.columns = ['Played', 'Title', 'Author', 'Language', 'Headline',
                        'Year', 'Genre', 'Group', 'Series',
                        'Series Number', 'Forgiveness', 'Tag', 'Date Imported',
                        'Rating', 'IFDB Rating', 'rating_num',
                        'ifdb_rating_num']
        for n, name in enumerate(self.columns[:-2]):
            self.add_column(name, n)

    def add_column(self, name, index):
        # If it's the rating column, we want it to show an image of its star
        # rating, give it a fixed size, and make it sort by the hidden
        # 'rating_num' column which contains the actual rating in text.
        if name in ['Rating', 'IFDB Rating']:
            col_renderer = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(name, col_renderer, text=index,
                                     weight=self.weight_col)
            if name == 'Rating':
                col.set_sort_column_id(self.star_rating_float_col)
            else:
                col.set_sort_column_id(self.ifdb_rating_float_col)
            col.set_resizable(False)
            col.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
        # If it's the played column, which tracks whether or not the user has
        # already played the game, we want to show a check button and give
        # the column a fixed size.
        elif name == 'Played':
            col_renderer = Gtk.CellRendererToggle()
            col_renderer.connect('toggled', self.on_played_toggled)
            col = Gtk.TreeViewColumn(name, col_renderer, active=index)
            col.set_sort_column_id(index)
            col.set_resizable(False)
            col.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
        # For the rest of the columns, they will show text and the user can set
        # their size.
        else:
            col_renderer = Gtk.CellRendererText()
            col = Gtk.TreeViewColumn(name, col_renderer, text=index,
                                     weight=self.weight_col)
            col.set_sort_column_id(index)
            col.set_resizable(True)
            col.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        col.set_reorderable(True)
        self.append_column(col)

    def get_col_by_title(self, col_title):
        '''This helper method returns a colummn given its title.

        '''
        col_num = self.columns.index(col_title)
        return self.get_column(col_num)

    def get_col_number(self, col_title):
        '''This helper method returns the column number of a column given its
        title.

        '''
        return self.columns.index(col_title)

    def on_played_toggled(self, renderer, path):
        '''This method handles clicks on the played check buttons.

        '''
        self.library.toggle_story_played(
            self.library.list_store.get_iter_from_string(path))
