# -*- coding: utf-8 -*-
#
#       progressdialog.py
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


from gi.repository import Gtk


class ProgressDialog(Gtk.Dialog):
    '''This thread implements a dialog displaying a progress bar and some
    optional textual information.

    '''
    def __init__(self, title, parent=None, interactive=True):
        # If interactive is True, add a Cancel button to the dialog
        if interactive:
            super(ProgressDialog, self).__init__(title, parent,
                                                 Gtk.DialogFlags.MODAL,
                                                 ("Cancel",
                                                  Gtk.ResponseType.REJECT))
            self.set_default_size(320, 128)
        else:
            super(ProgressDialog, self).__init__(title, parent,
                                                 Gtk.DialogFlags.MODAL)
        vbox = self.get_child()
        # If interactive is true, add a label for holding textual information
        if interactive:
            self.info_label = Gtk.Label()
            vbox.pack_start(self.info_label, True, True, 8)
        self.progressbar = Gtk.ProgressBar()
        self.progressbar.set_show_text(True)
        self.progressbar.set_ellipsize(True)
        vbox.pack_start(self.progressbar, True, True, 16)
        vbox.show_all()
