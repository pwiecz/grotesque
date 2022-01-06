# -*- coding: utf-8 -*-
#
#       util.py
#
#       Copyright © 2015, 2017, 2018 Brandon Invergo <brandon@invergo.net>
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
import subprocess

from grotesque import settings

STAR_RATINGS = [u"", u"½", u"★", u"★½", u"★★", u"★★½", u"★★★",
                u"★★★½", u"★★★★", u"★★★★½", u"★★★★★"]
RATING_VALUES = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]

def render_star_rating(rating):
    """Return a star representation of a floating point rating, on a scale
    of 0 to 5.

    """
    if rating < 0.0 or rating > 5.0:
        raise ValueError("Rating must be between 0.0 and 5.0")
    return STAR_RATINGS[int(rating*2)]


def star_rating_to_float(rating_txt):
    """Return a floating point value related to a star rating text."""
    if rating_txt not in STAR_RATINGS:
        raise ValueError
    return RATING_VALUES[STAR_RATINGS.index(rating_txt)]


def parse_list_str(list_str):
    """Parse strings which may be lists separated by commas or slashes,
    such as author lists or genre lists.

    """
    if not list_str:
        return []
    itemized = list_str.split(',')
    itemized = [item.strip() for item in itemized]
    final_list = itemized
    for item in itemized:
        for linker in ['and ', '&', '/']:
            if linker in item:
                item_split = item.split(linker)
                if item in final_list:
                    final_list.remove(item)
                final_list.extend(
                    [sub_item.strip() for sub_item in item_split])
    return final_list


def normalize_date(date_str):
    if not date_str:
        return None
    if "-" in date_str:
        date_split = date_str.split("-")
    elif "/" in date_str:
        date_split = date_str.split("/")
    else:
        date_split = [date_str]
    for part in date_split:
        try:
            int(part)
        except:
            raise ValueError("Invalid date string")
    if len(date_split) == 3:
        return date_str
    if len(date_split) == 2:
        return date_str + "-01"
    if len(date_split) == 1:
        return date_str + "-01-01"
    return None


def open_resource(uri, launcher):
    if not launcher:
        raise ValueError("No resource launcher set")
    try:
        subprocess.call([launcher, uri])
    except subprocess.CalledProcessError as e:
        raise ValueError("Failed to open {0}: {1}".format(uri, str(e)))
