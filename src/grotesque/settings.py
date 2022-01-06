# -*- coding: utf-8 -*-
#
#       settings.py
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

import os
import platform
from ConfigParser import SafeConfigParser, NoOptionError
import treatyofbabel


class Settings:
    '''This class handles reading from and writing to the program's
    configuration file.

    '''
    DEFAULT_DIMENSIONS = (1024, 768)

    def __init__(self):
        self.config = SafeConfigParser()
        self.config.add_section('General')
        self.config.add_section('Launchers')
        self.config.add_section('File_exts')
        self.config.add_section('Directories')
        self.config.add_section('Window')
        # Get the user's home directory.
        if platform.system() == 'Windows':
            homedir = os.path.expanduser('~')
            appdir = '.grotesque'
            self.configdir = os.path.join(homedir, appdir)
            self.settings_filename = os.path.join(self.configdir,
                                                  'grotesque.cfg')
            self.library_filename = os.path.join(self.configdir,
                                                 'library.db')
        else:
            home_configdir = os.getenv('XDG_CONFIG_HOME')
            if home_configdir is None:
                self.configdir = os.path.join(os.path.expanduser('~'),
                                              '.config', 'grotesque')
            else:
                self.configdir = os.path.join(home_configdir, 'grotesque')
            home_datadir = os.getenv('XDG_DATA_HOME')
            if home_datadir is None:
                self.datadir = os.path.join(os.path.expanduser('~'), '.local',
                                            'share', 'grotesque')
            else:
                self.datadir = os.path.join(home_datadir, 'grotesque')
            # Create a directory for Grotesque.
            # Define program's files.
            self.settings_filename = os.path.join(self.configdir,
                                                  'grotesque.cfg')
            self.library_filename = os.path.join(self.datadir,
                                                 'library.db')

    def load(self):
        return len(self.config.read(self.settings_filename)) > 0

    def save(self):
        with open(self.settings_filename, 'w') as f:
            self.config.write(f)

    def set_ifdb_limit(self, limit):
        if limit <= 0:
            raise ValueError("IFDB connection limit must be greater than 0")
        self.config.set('General', 'IFDBConnLimit', str(limit))

    def get_ifdb_limit(self):
        try:
            limit = int(self.config.get('General', 'IFDBConnLimit'))
        except NoOptionError, ValueError:
            self.set_ifdb_limit(30)
            return 30
        if limit <= 0:
            self.set_ifdb_limit(30)
            return 30
        return limit

    def set_fetch_metadata(self, fetch_metadata):
        self.config.set('General', 'FetchMetadata', str(fetch_metadata))

    def get_fetch_metadata(self):
        str_to_bool = {'True': True, 'False': False}
        try:
            fetch = self.config.get('General', 'FetchMetadata')
        except NoOptionError:
            self.set_fetch_metadata(True)
            return True
        return fetch == 'True'

    def set_fetch_coverart(self, fetch_coverart):
        self.config.set('General', 'FetchCoverArt', str(fetch_coverart))

    def get_fetch_coverart(self):
        try:
            fetch = self.config.get('General', 'FetchCoverArt')
        except NoOptionError:
            self.set_fetch_coverart(True)
            return True
        return fetch == 'True'

    def set_disp_coverart(self, disp_coverart):
        self.config.set('General', 'DispCoverArt', str(disp_coverart))

    def get_disp_coverart(self):
        try:
            disp = self.config.get('General', 'DispCoverArt')
        except NoOptionError:
            self.set_disp_coverart(True)
            return True
        return disp == 'True'

    def get_launcher(self, if_format):
        try:
            return self.config.get('Launchers', if_format)
        except NoOptionError:
            raise ValueError('No interpreter configured for format {0}.'.format(
                if_format))

    def get_launchers(self):
        return self.config.items('Launchers')

    def set_launcher(self, if_format, path):
        self.config.set('Launchers', if_format, path)

    def remove_launcher(self, if_format):
        self.config.remove_option('Launchers', if_format)
        self.config.remove_option('File_exts', if_format)

    def get_resource_launcher(self):
        try:
            return self.config.get('Launchers', 'resource')
        except NoOptionError:
            raise ValueError('No resource launcher configured.')

    def set_resource_launcher(self, path):
        self.config.set('Launchers', 'resource', path)

    def get_file_exts(self, if_format):
        try:
            return self.config.get('File_exts', if_format)
        except NoOptionError:
            if if_format == 'adrift':
                exts = treatyofbabel.formats.adrift.get_file_extensions()
            elif if_format == 'agt':
                exts = treatyofbabel.formats.agt.get_file_extensions()
            elif if_format == 'alan':
                exts = treatyofbabel.formats.alan.get_file_extensions()
            elif if_format in ['dos', 'win32']:
                exts = treatyofbabel.formats.executable.get_file_extensions()
            elif if_format == 'glulx':
                exts = treatyofbabel.formats.glulx.get_file_extensions()
            elif if_format == 'hugo':
                exts = treatyofbabel.formats.hugo.get_file_extensions()
            elif if_format == 'level9':
                exts = treatyofbabel.formats.level9.get_file_extensions()
            elif if_format == 'magscrolls':
                exts = treatyofbabel.formats.magscrolls.get_file_extensions()
            elif if_format == 'tads2':
                exts = treatyofbabel.formats.tads2.get_file_extensions()
            elif if_format == 'tads3':
                exts = treatyofbabel.formats.tads3.get_file_extensions()
            elif if_format == 'zcode':
                exts = treatyofbabel.formats.zcode.get_file_extensions()
            elif if_format == 'twine':
                exts = treatyofbabel.formats.twine.get_file_extensions()
            elif if_format == 'blorb':
                exts = treatyofbabel.wrappers.blorb.get_file_extensions()
            else:
                exts = ''
        return ','.join(exts)

    def set_file_exts(self, if_format, exts):
        self.config.set('File_exts', if_format, exts)

    def get_all_exts(self):
        exts = self.config.items('File_exts')
        if len(exts) == 0:
            for if_format in ['adrift', 'agt', 'alan',
                              'dos', 'win32', 'glulx', 'hugo', 'level9',
                              'magscrolls', 'tads2', 'tads3', 'twine',
                              'zcode', 'blorb']:
                self.set_file_exts(if_format, self.get_file_exts(if_format))
            self.save()
        return self.config.items('File_exts')

    def get_format_from_ext(self, ext):
        if_formats = []
        all_exts = self.config.items('File_exts')
        for if_format, format_ext in all_exts:
            if ext in format_ext:
                if_formats.append(if_format)
        if len(if_formats) != 1:
            return None
        else:
            return if_formats[0]

    def get_game_dir(self):
        try:
            gamedir = self.config.get('Directories', 'Games')
        except NoOptionError:
            self.set_game_dir(os.getcwd())
            return os.getcwd()
        return gamedir

    def set_game_dir(self, dir):
        self.config.set('Directories', 'Games', dir)

    def get_library_filename(self):
        return self.library_filename

    def set_window_size(self, size):
        width, height = size
        if width <= 0 or height <= 0:
            raise ValueError("Window width and height must be positive")
        self.config.set('Window', 'Width', str(width))
        self.config.set('Window', 'Height', str(height))

    def get_window_size(self):
        try:
            width = int(self.config.get('Window', 'Width'))
            height = int(self.config.get('Window', 'Height'))
        except NoOptionError:
            self.set_window_size(self.DEFAULT_DIMENSIONS)
            return self.DEFAULT_DIMENSIONS
        if width <= 0 or height <= 0:
            self.set_window_size(self.DEFAULT_DIMENSIONS)
            return self.DEFAULT_DIMENSIONS
        return (width, height)

    def set_vpaned_percentage(self, percentage):
        '''This method sets the position of the handle splitting the library
        area from the information area of the main window.

        '''
        if percentage < 0 or percentage > 1:
            raise ValueError("VPaned percentage must be between 0 and 1")
        self.config.set('Window', 'VPanedPercentage', str(percentage))

    def get_vpaned_percentage(self):
        '''This method gets the position of the handle splitting the library
        area from the information area of the main window.

        '''
        try:
            perc = float(self.config.get('Window', 'VPanedPercentage'))
        except NoOptionError:
            self.set_vpaned_percentage(0.625)
            return 0.625
        if perc < 0 or perc > 1:
            self.set_vpaned_percentage(0.625)
            return 0.625
        return perc

    def set_filter_percentage(self, percentage):
        '''This method sets the position of the handle splitting the list of
        library filters from the list of library contents in the main window.

        '''
        if percentage < 0 or percentage > 1:
            raise ValueError("Filter percentage must be between 0 and 1")
        self.config.set('Window', 'FilterPercentage', str(percentage))

    def get_filter_percentage(self):
        '''This method gets the position of the handle splitting the list of
        library filters from the list of library contents in the main window.

        '''
        try:
            perc = float(self.config.get('Window', 'FilterPercentage'))
        except NoOptionError:
            self.set_filter_percentage(0.2)
            return 0.2
        if perc < 0 or perc > 1:
            self.set_filter_percentage(0.2)
            return 0.2
        return perc

    def set_filter_type(self, filter_index):
        '''This method sets the type of library filter being used.

        '''
        if filter_index < 0:
            raise ValueError("Filter index must be >= 0")
        self.config.set('Window', 'Filter', str(filter_index))

    def get_filter_type(self):
        '''This method gets the type of library filter to use.

        '''
        try:
            filt_type = int(self.config.get('Window', 'Filter'))
        except NoOptionError:
            self.set_filter_type(0)
            return 0
        if filt_type < 0:
            self.set_filter_type(0)
            return 0
        return filt_type

    def set_column_width(self, title, width):
        '''This method sets the current width of a column of the library view.

        '''
        if width < 0:
            raise ValueError("Column width must be positive: {0} -> {1}".format(title, width))
        self.config.set('Window', '{0}_col_width'.format(title), str(width))

    def get_column_width(self, title):
        '''This method gets the width of a column of the library view.

        '''
        try:
            width = int(self.config.get(
                'Window', '{0}_col_width'.format(title)))
        except NoOptionError:
            self.set_column_width(title, 150)
            return 150
        if width <= 0:
            self.set_column_width(title, 150)
            return 150
        else:
            return width

    def set_column_visible(self, title, visible):
        '''This method sets whether or not a column is visible.

        '''
        self.config.set('Window', '{0}_visible'.format(title), str(visible))

    def get_column_visible(self, title):
        '''This method gets whether or not a column should be visible.

        '''
        try:
            vis = self.config.get('Window', '{0}_visible'.format(title))
        except NoOptionError:
            self.set_column_visible(title, True)
            return True
        return vis == 'True'
