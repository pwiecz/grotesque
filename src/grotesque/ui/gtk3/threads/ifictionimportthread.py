# -*- coding: utf-8 -*-
#
#       ifictionimportthread.py
#
#       Copyright © 2011, 2012, 2014, 2015, 2017, 2018
#                   Brandon Invergo <brandon@invergo.net>
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


import os
import datetime

from gi.repository import Gtk

from treatyofbabel import ifiction
from grotesque import db


class IfictionImportThread():
    '''This class handles importing stories into the library in a threaded
    manner. This allows a progress bar to be displayed since the process can
    take some time.

    '''
    def __init__(self, ifiction_file, settings, library, dialog,
                 conn):
        self.settings = settings
        with open(ifiction_file) as h:
            try:
                doc = ifiction.get_ifiction_dom(h.read())
            except:
                raise IOError("File is not an IFiction file")
        self.story_nodes = ifiction.get_all_stories(doc)
        self.fetch_metadata = settings.get_fetch_metadata()
        self.fetch_coverart = settings.get_fetch_coverart()
        self.library = library
        self.dialog = dialog
        self.conn = conn
        self.stopthread = False
        self.fails = []
        self.today = datetime.date.today()

    def stop(self):
        self.stopthread = True

    def import_ifiction(self):
        self.msg = ''
        count = 0
        for story_node in self.story_nodes:
            if self.stopthread:
                yield False
            story_biblio = ifiction.get_bibliographic(story_node)
            if story_biblio is None or "title" not in story_biblio:
                continue
            story_title = story_biblio["title"]
            yield True
            self.dialog.info_label.set_text(u'Importing "{0}"'.format(story_title))
            story_id, failed = db.import_ifiction(
                self.conn, self.settings, story_node, self.fetch_coverart)
            if failed:
                self.fails.append(story_id)
            if story_id is not None:
                story_rec = db.query.select_story(self.conn, story_id)
                self.library.add_story_from_db_rec(story_rec)
                self.library.update_filter_stores()
            count = count + 1
            # Update the progress bar.
            self.dialog.progressbar.set_fraction(
                float(count) / float(len(self.story_nodes)))
            yield True
        self.dialog.response(Gtk.ResponseType.OK)
        yield False
