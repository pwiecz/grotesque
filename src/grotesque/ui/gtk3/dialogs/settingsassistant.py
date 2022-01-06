# -*- coding: utf-8 -*-
#
#       settings_assistant.py
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

from grotesque.which import whichall


class SettingsAssistant:
    '''This class creates the settings wizard which launches the first time
    Grotesque is run.

    '''
    SUGGESTED_INTERPRETERS = [
        ('adrift', ['gargoyle', 'gargoyle-free', 'gargoyle-scare', 'scare']),
        ('alan', ['gargoyle', 'gargoyle-free']),
        ('dos', ['dosbox']),
        ('glulx', ['gargoyle', 'gargoyle-free', 'gargoyle-git', 'git']),
        ('hugo', ['gargoyle', 'gargoyle-free', 'hugor']),
        ('level9', ['gargoyle', 'gargoyle-free']),
        ('tads2', ['gargoyle', 'gargoyle-free', 'gargoyle-tadsr', 'tadsr',
                   'qtads']),
        ('tads3', ['gargoyle', 'gargoyle-free', 'gargoyle-tadsr', 'tadsr',
                   'qtads']),
        ('twine', ['firefox', 'epiphany', 'chromium']),
        ('win32', ['wine']),
        ('zcode', ['gargoyle', 'gargoyle-free', 'gargoyle-frotz', 'frotz',
                   'zoom'])]

    SUGGESTED_RESOURCE_LAUNCHERS = ['xdg-open', 'mimeo', 'rifle']

    INTRO_TEXT = ('It appears this is the first time you have run '
                  '<b><i>Grotesque</i></b>.\n\nPlease take a moment and let '
                  'this assistant guide you through setting up the '
                  'application.')

    INTERPRETERS_INFO = ('To play games using <b><i>Grotesque</i></b>, you '
                         'need to configure an interpreter for each game '
                         'format you wish to play.  An interpreter is a '
                         'program that knows how to play a certain game '
                         'format.\n\nBelow, a number of formats are listed, '
                         'and Grotesque has attempted to guess which '
                         'interpreter to use, based on the programs installed '
                         'on your computer.')

    LAUNCHER_INFO = ('<b><i>Grotesque</i></b> allows you to associate '
                     'other files with an Interactive Fiction game.  For '
                     'example, a game might come with a hint book, a map, '
                     'or other digital "feelies"; or, perhaps you take notes '
                     'during play in a text file.  These are called "resources" '
                     'in Grotesque.\n\nRather than try to guess every possible '
                     'type of resource that a user might want to open, Grotesque '
                     'instead relies on an external program to determine how to '
                     'open any given resource file.  On most GNU/Linux systems, '
                     'this will be <i>xdg-open</i>, however you can set an '
                     'alternative here.')

    COMPLETED_TEXT = 'Setup is complete. Enjoy <b><i>Grotesque</i></b>!'

    def __init__(self, settings, parent=None, on_finish=None):
        self.settings = settings
        self.assistant = Gtk.Assistant()
        self.on_finish = on_finish
        self.selected_interpreters = {}
        if parent is not None:
            self.assistant.set_transient_for(parent)

        intro_page = self.create_welcome_page()
        self.assistant.append_page(intro_page)
        self.assistant.set_page_type(intro_page, Gtk.AssistantPageType.INTRO)
        self.assistant.set_page_title(intro_page, 'Welcome to Grotesque')
        self.assistant.set_page_complete(intro_page, True)

        terp_page = self.create_interpreter_page()
        self.assistant.append_page(terp_page)
        self.assistant.set_page_type(terp_page, Gtk.AssistantPageType.CONTENT)
        self.assistant.set_page_title(terp_page, 'Select interpreters')
        self.assistant.set_page_complete(terp_page, True)

        rsrc_page = self.create_resource_launch_page()
        self.assistant.append_page(rsrc_page)
        self.assistant.set_page_type(rsrc_page, Gtk.AssistantPageType.CONTENT)
        self.assistant.set_page_title(rsrc_page, 'Select resource launcher')
        self.assistant.set_page_complete(rsrc_page, True)

        summary_page = self.create_summary_page()
        self.assistant.append_page(summary_page)
        self.assistant.set_page_type(summary_page,
                                     Gtk.AssistantPageType.SUMMARY)
        self.assistant.set_page_title(summary_page, 'Setup complete')
        self.assistant.set_page_complete(summary_page, True)

        self.assistant.connect('close', self.on_close)
        self.assistant.connect('cancel', self.on_cancel)
        self.assistant.show_all()

    def set_default_config(self):
        self.settings.set_column_visible("Played", False)
        self.settings.set_column_visible("Language", False)
        self.settings.set_column_visible("Headline", False)
        self.settings.set_column_visible("Genre", False)
        self.settings.set_column_visible("Group", False)
        self.settings.set_column_visible("Series", False)
        self.settings.set_column_visible("Series Number", False)
        self.settings.set_column_visible("Forgiveness", False)
        self.settings.set_column_visible("Tag", False)
        self.settings.set_column_width("Title", 350)
        self.settings.set_column_width("Author", 250)
        self.settings.set_column_width("Year", 64)
        self.settings.set_column_width("Date Imported", 144)

    def on_cancel(self, assistant):
        if self.on_finish is not None:
            self.on_finish()
        self.assistant.destroy()

    def on_close(self, assistant):
        for format in self.selected_interpreters:
            self.settings.set_launcher(format,
                                       self.selected_interpreters[format])
        self.settings.set_resource_launcher(self.selected_launcher)
        self.set_default_config()
        if self.on_finish is not None:
            self.on_finish()
        self.assistant.destroy()

    def create_welcome_page(self):
        w = Gtk.Label()
        w.set_line_wrap(True)
        w.set_justify(Gtk.Justification.LEFT)
        w.set_markup(self.INTRO_TEXT)
        w.set_padding(16, 24)
        w.set_max_width_chars(80)
        return w

    def create_interpreter_page(self):
        grid = Gtk.Grid()
        grid.set_row_spacing(8)
        grid.set_column_spacing(8)
        info_label = Gtk.Label()
        info_label.set_line_wrap(True)
        info_label.set_justify(Gtk.Justification.LEFT)
        info_label.set_markup(self.INTERPRETERS_INFO)
        info_label.set_max_width_chars(80)
        info_label.set_padding(16, 24)
        grid.attach(info_label, 0, 0, 12, 5)
        row = 6
        for (story_format, interpreters) in self.SUGGESTED_INTERPRETERS:
            label = Gtk.Label()
            label.set_justify(Gtk.Justification.RIGHT)
            label.set_markup("<b>{0}</b>".format(story_format))
            grid.attach(label, 0, row, 1, 1)
            combo = Gtk.ComboBoxText.new_with_entry()
            first = True
            for terp in interpreters:
                for exe in whichall(terp):
                    combo.append_text(exe)
                    if first:
                        self.selected_interpreters[story_format] = exe
                        combo.set_active(0)
                        first = False
            combo.connect('changed', self.on_interpreter_change, story_format)
            grid.attach(combo, 1, row, 1, 1)
            row = row + 1
        return grid

    def create_resource_launch_page(self):
        grid = Gtk.Grid()
        grid.set_row_spacing(8)
        grid.set_column_spacing(8)
        info_label = Gtk.Label()
        info_label.set_line_wrap(True)
        info_label.set_justify(Gtk.Justification.LEFT)
        info_label.set_markup(self.LAUNCHER_INFO)
        info_label.set_max_width_chars(80)
        info_label.set_padding(16, 24)
        grid.attach(info_label, 0, 0, 12, 5)
        row = 6
        label = Gtk.Label()
        label.set_justify(Gtk.Justification.RIGHT)
        label.set_markup("<b>Resource launcher</b>")
        grid.attach(label, 0, row, 1, 1)
        combo = Gtk.ComboBoxText.new_with_entry()
        first = True
        for prog in self.SUGGESTED_RESOURCE_LAUNCHERS:
            for exe in whichall(prog):
                combo.append_text(exe)
                if first:
                    self.selected_launcher = exe
                    combo.set_active(0)
                    first = False
        combo.connect('changed', self.on_launcher_change)
        grid.attach(combo, 1, row, 1, 1)
        return grid

    def on_interpreter_change(self, widget, if_format):
        self.selected_interpreters[if_format] = widget.get_active_text()

    def on_launcher_change(self, widget):
        self.selected_launcher = widget.get_active_text()

    def create_summary_page(self):
        w = Gtk.Label()
        w.set_line_wrap(True)
        w.set_justify(Gtk.Justification.LEFT)
        w.set_markup(self.COMPLETED_TEXT)
        w.set_padding(16, 24)
        w.set_max_width_chars(80)
        return w
