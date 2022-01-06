# -*- coding: utf-8 -*-
#
#       infopaned.py
#
#       Copyright © 2011, 2014, 2015, 2017, 2018 Brandon Invergo <brandon@invergo.net>
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

from gi.repository import Gtk, GdkPixbuf

from infoview import InfoView
from grotesque import db

COVERART_PADDING = 20


class InfoPaned(Gtk.Paned):
    '''This class implements the widget which holds story information and
    cover art

    '''
    def __init__(self, settings, conn):
        super(InfoPaned, self).__init__()
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.settings = settings
        self.conn = conn
        self.coverart_file = None
        self.coverart = Gtk.Image()
        # Create a label that will be displayed when no coverart exists for a
        # file
        self.no_coverart_label = Gtk.Label('cover art unavailable')
        self.no_coverart_label.set_selectable(False)
        self.no_coverart_label.set_line_wrap(True)
        self.no_coverart_label.set_justify(Gtk.Justification.CENTER)
        self.no_coverart_label.show()
        self.text_view = InfoView(self.conn, self.settings)
        self.pack1(self.coverart, True, True)
        self.pack2(self.text_view, True, True)

    def refresh_coverart(self, story_id):
        '''This method refreshes the coverart, resizing it in the event that
        its container has changed size.

        '''
        if story_id is not None:
            cover_row = db.query.select_cover_by_story(self.conn, story_id)
        # If the file doesn't have coverart, display the label...
        # if not self.coverart_file or not os.path.exists(self.coverart_file):
        if (story_id is None or not cover_row or
                cover_row["format"] not in ["jpeg", "png", "gif"]):
            if self.coverart in self.get_children():
                self.remove(self.coverart)
                self.add1(self.no_coverart_label)
            return
        # ...otherwise display the coverart.
        if self.no_coverart_label in self.get_children():
            self.remove(self.no_coverart_label)
            self.add1(self.coverart)
        self.coverart.clear()
        pixbuf_loader = GdkPixbuf.PixbufLoader.new_with_type(
            cover_row["format"])
        pixbuf_loader.write(cover_row["data"])
        pixbuf_loader.close()
        pixbuf = pixbuf_loader.get_pixbuf()
        pixbuf_w = pixbuf.get_width()
        pixbuf_h = pixbuf.get_height()
        ratio = float(pixbuf_h) / float(pixbuf_w)
        max_size = self.get_position() - COVERART_PADDING
        # If the image is bigger than the frame in either dimension, it
        # should be scaled to fit.
        if pixbuf_w > max_size or pixbuf_h > max_size:
            if pixbuf_w == pixbuf_h:
                new_width = max_size
                new_height = max_size
            elif pixbuf_w > pixbuf_h:
                new_width = max_size
                new_height = int(ratio * new_width)
            else:
                new_height = max_size
                new_width = int(1 / ratio * new_height)
            scaled_buf = pixbuf.scale_simple(new_width, new_height,
                                             GdkPixbuf.InterpType.TILES)
            self.coverart.set_from_pixbuf(scaled_buf)
        else:
            self.coverart.set_from_pixbuf(pixbuf)

    def show_story(self, story_id):
        '''This method renders the textual description and the coverart for a
        given story.

        '''
        self.text_view.render_story(story_id)
        self.refresh_coverart(story_id)

    def clear(self):
        '''This method clears all the information from the view.

        '''
        self.text_view.clear()
        self.coverart_file = None
        self.refresh_coverart(None)

    def show_coverart(self, do_show):
        '''This method handles showing/hiding the coverart view.

        '''
        if do_show:
            self.coverart.show()
        else:
            self.coverart.hide()
