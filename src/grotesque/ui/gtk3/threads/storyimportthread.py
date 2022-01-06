# -*- coding: utf-8 -*-
#
#       storyimportthread.py
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
import time

from gi.repository import Gtk

from treatyofbabel import ifiction
from treatyofbabel.babelerrors import BabelError
from grotesque import db


class StoryImportThread():
    '''This class handles importing stories into the library in a threaded
    manner. This allows a progress bar to be displayed since the process can
    take some time.

    '''
    def __init__(self, filenames, settings, library, dialog,
                 conn):
        self.settings = settings
        self.filenames = filenames
        self.fetch_metadata = settings.get_fetch_metadata()
        self.fetch_coverart = settings.get_fetch_coverart()
        self.library = library
        self.dialog = dialog
        self.conn = conn
        self.stopthread = False
        self.fails = []
        self.today = datetime.date.today()
        limit = self.settings.get_ifdb_limit()
        self.time_per_req = 60/limit

    def stop(self):
        self.stopthread = True

    def import_stories(self):
        self.msg = ''
        count = 0
        for filename in self.filenames:
            start_time = time.time()
            if self.stopthread:
                yield False
            basename = os.path.split(filename)[1]
            yield True
            self.dialog.info_label.set_text('Importing {0}'.format(basename))
            try:
                story_id, failed = db.add_story_from_file(
                    self.conn, self.settings, filename, self.fetch_metadata,
                    self.fetch_coverart)
            except BabelError:
                count = count + 1
                # Update the progress bar.
                self.dialog.progressbar.set_fraction(
                    float(count) / float(len(self.filenames)))
                continue
            except ValueError:
                count = count + 1
                # Update the progress bar.
                self.dialog.progressbar.set_fraction(
                    float(count) / float(len(self.filenames)))
                continue
            if story_id is None and failed is None:
                count = count + 1
                # Update the progress bar.
                self.dialog.progressbar.set_fraction(
                    float(count) / float(len(self.filenames)))
                continue
            if failed:
                self.fails.append(story_id)
            if story_id is not None:
                story_rec = db.query.select_story(self.conn, story_id)
                self.library.add_story_from_db_rec(story_rec)
                self.library.update_filter_stores()
            count = count + 1
            # Update the progress bar.
            self.dialog.progressbar.set_fraction(
                float(count) / float(len(self.filenames)))
            yield True
            end_time = time.time()
            elapsed_time = end_time - start_time
            if elapsed_time < self.time_per_req:
                 time.sleep(self.time_per_req - elapsed_time)
        self.dialog.response(Gtk.ResponseType.OK)
        yield False
