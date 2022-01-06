# -*- coding: utf-8 -*-
#
#       mainwindow.py
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


from gi.repository import Gtk

from dialogs.settingsassistant import SettingsAssistant
from mainwindow import MainWindow


class Gui:
    def __init__(self):
        pass

    def setup_assistant(self, settings):
        SettingsAssistant(settings, None, Gtk.main_quit)
        Gtk.main()

    def main_window(self, library_filename, settings):
        MainWindow(library_filename, settings)
        Gtk.main()
