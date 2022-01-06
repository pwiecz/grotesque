# -*- coding: utf-8 -*-
#
#       main.py
#
#       Copyright © 2011, 2014 Brandon Invergo <brandon@invergo.net>
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


from gi.repository import Gtk, GdkPixbuf


class FilterStore(Gtk.ListStore):
    '''This class implements a widget which holds information on a library
    filter. It keeps count of the number of occurrances of each item in the
    library. When, for example, there are no more stories by Author X in the
    library, Author X should be removed from the filter.

    '''
    def __init__(self, conn, query_func):
        super(FilterStore, self).__init__(str, int)
        self.conn = conn
        self.query_func = query_func
        self.update()

    def add_item(self, item_id, item_str):
        self.append([item_str, item_id])

    def remove_item(self, item_id):
        row_iter = self.get_iter_first()
        while row_iter:
            if self.get_value(row_iter, 1) == item_id:
                self.remove(row_iter)
                return True
            row_iter = self.iter_next(row_iter)
        return False

    def update(self):
        self.clear()
        self.add_item(-1, "(All)")
        rows = self.query_func(self.conn)
        for row in rows:
            if not row or len(row) != 2 or None in row:
                continue
            self.add_item(row[0], row[1])
