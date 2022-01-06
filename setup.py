#!/usr/bin/env python2

from distutils.core import setup
import platform
import os.path


if platform.system() == 'Linux':
    doc_dir = '/usr/share/doc/grotesque-0.9.5.1'
else:
    try:
        from win32com.shell import shellcon, shell
        homedir = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
        appdir = 'Grotesque'
        doc_dir = os.path.join(homedir, appdir)
    except:
        pass


setup(name='grotesque',
      version='0.9.5.1',
      description='An interactive fiction library manager',
      author='Brandon Invergo',
      author_email='brandon@invergo.net',
      url='http://grotesque.invergo.net/',
      packages=['grotesque', 'grotesque.db', 'grotesque.ui', 'grotesque.ui.gtk3',
                'grotesque.ui.gtk3.dialogs', 'grotesque.ui.gtk3.info',
                'grotesque.ui.gtk3.info', 'grotesque.ui.gtk3.library',
                'grotesque.ui.gtk3.threads'],
      package_dir={'grotesque': 'src/grotesque'},
      package_data={'grotesque': ['data/*']},
      requires=['gi.repository.Gtk (>3.0)',
                'pyifbabel (>0.4)'],
      scripts=['grotesque'],
      data_files=[(doc_dir, ['COPYING', 'README', 'NEWS'])],
      classifiers=[
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Development Status :: 4 - beta',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Operating System :: OS Independent',
          'Intended Audience :: End Users/Desktop',
          'Topic :: Games/Entertainment'],)
