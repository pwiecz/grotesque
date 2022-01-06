# -*- coding: utf-8 -*-
#
#       main.py
#
#       Copyright © 2014, 2015, 2017, 2018 Brandon Invergo <brandon@invergo.net>
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


GROTESQUE_TABLE = """
CREATE TABLE IF NOT EXISTS grotesque (
    id INTEGER,
    version TEXT,
    PRIMARY KEY (id ASC)
)"""


STORIES_TABLE = """
CREATE TABLE IF NOT EXISTS stories (
    id INTEGER,
    title TEXT,
    language TEXT,
    headline TEXT,
    firstpublished DATE,
    group_id INTEGER,
    description TEXT,
    series_id INTEGER,
    seriesnumber INTEGER,
    forgiveness_id INTEGER,
    url TEXT,
    bafn INTEGER,
    default_release STRING,
    PRIMARY KEY (id ASC),
    CONSTRAINT group_key
        FOREIGN KEY (group_id)
        REFERENCES groups (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT series_key
        FOREIGN KEY (series_id)
        REFERENCES series (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT forgiveness_key
        FOREIGN KEY (forgiveness_id)
        REFERENCES forgiveness (id),
    CONSTRAINT release_key
        FOREIGN KEY (default_release)
        REFERENCES releases (ifid)
)"""


AUTHORS_TABLE = """
CREATE TABLE IF NOT EXISTS authors (
    id INTEGER,
    name TEXT,
    email TEXT,
    url TEXT,
    PRIMARY KEY (id ASC)
)"""


STORY_AUTHOR_TABLE = """
CREATE TABLE IF NOT EXISTS story_author (
    author_id INTEGER,
    story_id INTEGER,
    CONSTRAINT author_key
        FOREIGN KEY (author_id)
        REFERENCES authors (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT story_key
        FOREIGN KEY (story_id)
        REFERENCES stories (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
)"""


GROUPS_TABLE = """
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER,
    name TEXT,
    PRIMARY KEY (id ASC)
)"""


SERIES_TABLE = """
CREATE TABLE IF NOT EXISTS series (
    id INTEGER,
    name TEXT,
    PRIMARY KEY (id ASC)
)"""


FORGIVENESS_TABLE = """
CREATE TABLE IF NOT EXISTS forgiveness (
    id INTEGER,
    description TEXT,
    PRIMARY KEY (id ASC)
)"""


COVERS_TABLE = """
CREATE TABLE IF NOT EXISTS covers (
    id INTEGER,
    story_id INTEGER,
    format TEXT,
    height INTEGER,
    width INTEGER,
    description TEXT,
    data BLOB,
    PRIMARY KEY (id ASC)
    CONSTRAINT story_key
        FOREIGN KEY (story_id)
        REFERENCES stories (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
)"""


FORMATS_TABLE = """
CREATE TABLE IF NOT EXISTS formats (
    id INTEGER,
    name TEXT,
    command TEXT,
    PRIMARY KEY (id ASC)
)"""


GENRES_TABLE = """
CREATE TABLE IF NOT EXISTS genres (
    id INTEGER,
    name TEXT,
    PRIMARY KEY (id ASC)
)"""


STORY_GENRE_TABLE = """
CREATE TABLE IF NOT EXISTS story_genre (
    story_id INTEGER,
    genre_id INTEGER,
    CONSTRAINT story_key
        FOREIGN KEY (story_id)
        REFERENCES stories (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT genre_key
        FOREIGN KEY (genre_id)
        REFERENCES genres (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
)"""


ANNOTATION_TABLE = """
CREATE TABLE IF NOT EXISTS annotation (
    id INTEGER,
    story_id INTEGER,
    rating REAL,
    rating_txt TEXT,
    notes TEXT,
    played INTEGER,
    imported DATE,
    PRIMARY KEY (id ASC),
    CONSTRAINT story_key
        FOREIGN KEY (story_id)
        REFERENCES stories (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
)"""


IFDB_ANNOTATION_TABLE = """
CREATE TABLE IF NOT EXISTS ifdb_annotation (
    id INTEGER,
    story_id INTEGER,
    tuid TEXT,
    url TEXT,
    cover_url TEXT,
    avg_rating REAL,
    star_rating REAL,
    star_rating_txt TEXT,
    rating_count_avg INTEGER,
    rating_count_tot INTEGER,
    updated DATE,
    PRIMARY KEY (id ASC),
    CONSTRAINT story_key
        FOREIGN KEY (story_id)
        REFERENCES stories (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
)"""


RELEASES_TABLE = """
CREATE TABLE IF NOT EXISTS releases (
    ifid TEXT,
    story_id INTEGER,
    uri TEXT,
    version INTEGER,
    release_date DATE,
    compiler TEXT,
    compiler_version TEXT,
    comment TEXT,
    format_id INTEGER,
    PRIMARY KEY (ifid),
    CONSTRAINT story_key
        FOREIGN KEY (story_id)
        REFERENCES stories (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT format_key
        FOREIGN KEY (format_id)
        REFERENCES formats (id)
)"""


TAGS_TABLE = """
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER,
    name TEXT,
    PRIMARY KEY (id ASC)
)"""


STORY_TAG_TABLE = """
CREATE TABLE IF NOT EXISTS story_tag (
    story_id INTEGER,
    tag_id INTEGER,
    CONSTRAINT story_key
        FOREIGN KEY (story_id)
        REFERENCES stories (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT tag_key
        FOREIGN KEY (tag_id)
        REFERENCES tags (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
)"""


RESOURCES_TABLE = """
CREATE TABLE IF NOT EXISTS resources (
    id INTEGER,
    story_id INTEGER,
    uri TEXT,
    description TEXT,
    PRIMARY KEY (id ASC),
    CONSTRAINT story_key
        FOREIGN KEY (story_id)
        REFERENCES stories (id)
         ON DELETE CASCADE
         ON UPDATE CASCADE
)"""


TABLES = [GROTESQUE_TABLE, STORIES_TABLE, AUTHORS_TABLE,
          STORY_AUTHOR_TABLE, GROUPS_TABLE, SERIES_TABLE,
          FORGIVENESS_TABLE, COVERS_TABLE, FORMATS_TABLE,
          GENRES_TABLE, STORY_GENRE_TABLE, ANNOTATION_TABLE,
          IFDB_ANNOTATION_TABLE, RELEASES_TABLE, TAGS_TABLE,
          STORY_TAG_TABLE, RESOURCES_TABLE]
