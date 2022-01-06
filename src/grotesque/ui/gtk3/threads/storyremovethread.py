# -*- coding: utf-8 -*-
#
#       storyremovethread.py
#
#       Copyright © 2011, 2014, 2017 Brandon Invergo <brandon@invergo.net>
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


import threading

from gi.repository import Gtk

from grotesque import db


class StoryRemoveThread(threading.Thread):
    '''This class handles removing stories from the library in a threaded
    manner.  This is predominantly in order to provide a progress bar,
    since this process can take a couple seconds if many stories are
    selected.

    '''
    def __init__(self, library, row_iters, conn, dialog):
        threading.Thread.__init__(self)
        self.library = library
        self.row_iters = row_iters
        self.conn = conn
        self.dialog = dialog
        self.stopthread = threading.Event()

    def stop(self):
        self.stopthread.set()

    def remove_stories(self):
        for n, row_iter in enumerate(self.row_iters):
            # If the current iter somehow points to a row that doesn't exist,
            # continue.
            if not row_iter:
                continue
            story_id = self.library.get_story_id(row_iter)
            db.remove_story(self.conn, story_id)
            # Remove the entry from the library list store
            self.library.list_store.remove(row_iter)
            # Advance the progress bar.
            self.dialog.progressbar.set_fraction(float(n + 1) /
                                                 float(len(self.row_iters)))
            yield True
        self.dialog.response(Gtk.ResponseType.OK)
        self.library.update_filter_stores()
        yield False
