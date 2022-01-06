# -*- coding: utf-8 -*-
#
#       ifdb.py
#
#       Copyright © 2012, 2013, 2014, 2015, 2018 Brandon Invergo <brandon@invergo.net>
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


import urllib2
from treatyofbabel import ifiction
from treatyofbabel.babelerrors import IFictionError


def fetch_ifiction(ifid=None, tuid=None):
    """Fetch IFiction data from IFDB (http://ifdb.tads.org)

    Args:
        ifid: the IFID to search for (default: None; use the IFID stored
              in self.ifid_list[0])
        tuid: the TUID to search for (default: None; try to use the TUID
              stored in the object's annotation data)
    """
    # Access the IFDB public API
    if ifid is None and tuid is None:
        raise Exception("No IFID or TUID set")
    if tuid is not None:
        url = ''.join(['https://ifdb.tads.org/viewgame?ifiction&id=',
                       tuid])
    else:
        url = ''.join(['https://ifdb.tads.org/viewgame?ifiction&ifid=',
                       ifid])
    try:
        ific = urllib2.urlopen(url)
    except urllib2.HTTPError:
        return None
    ificstring = ific.read()
    try:
        ificdom = ifiction.get_ifiction_dom(ificstring)
    except IFictionError:
        return None
    ificstories = ifiction.get_all_stories(ificdom)
    if not ificstories or len(ificstories) == 0:
        return None
    ificstory = ificstories[0]
    ifiction.move_extra_to_annotation(ificdom, ificstory, ["ifdb"])
    return ificstory


def fetch_cover(url=None, tuid=None, ifid=None):
    if url is None and tuid is None and ifid is None:
        return None
    if url is not None:
        cover_url = url
    elif tuid is not None:
        cover_url = ''.join(["https://ifdb.tads.org/viewgame?ifiction&id=",
                             tuid, "&coverart"])
    else:
        cover_url = ''.join(["https://ifdb.tads.org/viewgame?ifiction&ifid=",
                             ifid, "&coverart"])
    try:
        cover_file = urllib2.urlopen(cover_url)
    except urllib2.HTTPError:
        return None
    cover_data = cover_file.read()
    if cover_data in ["No game was found matching the requested IFID.",
                      "No image is available"]:
        cover_data = None
    return cover_data
