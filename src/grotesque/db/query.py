# query.py --- 

# Copyright (C) 2017, 2018 Brandon Invergo <brandon@invergo.net>

# Author: Brandon Invergo <brandon@invergo.net>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import sqlite3


def get_db_version(conn):
    c = conn.cursor()
    c.execute("SELECT version FROM grotesque")
    versions = c.fetchall()
    versions.sort()
    if not versions:
        return None
    return versions[-1][0]


def db_version_in_db(conn, version):
    c = conn.cursor()
    c.execute("SELECT id FROM grotesque WHERE version=?", (version,))
    return c.fetchone() is not None


def set_db_version(conn, version):
    c = conn.cursor()
    if db_version_in_db(conn, version):
        return
    c.execute("INSERT INTO grotesque (version) VALUES (?)", (version,))
    conn.commit()


def select_group(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT * FROM groups WHERE id=?", (group_id,))
    return c.fetchone()


def select_group_by_name(conn, group_name, case_insensitive=False):
    c = conn.cursor()
    if case_insensitive:
        c.execute("SELECT * FROM groups WHERE name=? COLLATE NOCASE",
                  (group_name,))
    else:
        c.execute("SELECT * FROM groups WHERE name=?", (group_name,))
    return c.fetchone()


def select_all_groups(conn):
    c = conn.cursor()
    c.execute("SELECT id, name FROM groups ORDER BY name ASC")
    return c.fetchall()


def insert_group(conn, group_name):
    c = conn.cursor()
    c.execute("INSERT INTO groups (name) VALUES (?)", (group_name,))
    conn.commit()
    return c.lastrowid


def delete_group(conn, group_id):
    c = conn.cursor()
    c.execute("DELETE FROM groups WHERE id=?", (group_id,))
    conn.commit()


def select_series(conn, series_id):
    c = conn.cursor()
    c.execute("SELECT * FROM series WHERE id=?", (series_id,))
    return c.fetchone()


def select_series_by_name(conn, series_name, case_insensitive=False):
    c = conn.cursor()
    if case_insensitive:
        c.execute("SELECT * FROM series WHERE name=? COLLATE NOCASE",
                  (series_name,))
    else:
        c.execute("SELECT * FROM series WHERE name=?", (series_name,))
    return c.fetchone()


def select_all_series(conn):
    c = conn.cursor()
    c.execute("SELECT id, name FROM series ORDER BY name ASC")
    return c.fetchall()


def insert_series(conn, series_name):
    c = conn.cursor()
    c.execute("INSERT INTO series (name) VALUES (?)", (series_name,))
    conn.commit()
    return c.lastrowid


def delete_series(conn, series_id):
    c = conn.cursor()
    c.execute("DELETE FROM series WHERE id=?", (series_id,))
    conn.commit()


def select_forgiveness(conn, forgiveness_id):
    c = conn.cursor()
    c.execute("SELECT * FROM forgiveness WHERE id=?", (forgiveness_id,))
    return c.fetchone()


def select_forgiveness_by_description(conn, description):
    c = conn.cursor()
    c.execute("SELECT * FROM forgiveness WHERE description=?", (description,))
    return c.fetchone()


def select_all_forgiveness(conn):
    c = conn.cursor()
    c.execute("SELECT id, description FROM forgiveness ORDER BY id ASC")
    return c.fetchall()


def fill_forgiveness(conn):
    c = conn.cursor()
    c.execute("INSERT INTO forgiveness (description) VALUES (\"Unknown\")")
    c.execute("INSERT INTO forgiveness (description) VALUES (\"Merciful\")")
    c.execute("INSERT INTO forgiveness (description) VALUES (\"Polite\")")
    c.execute("INSERT INTO forgiveness (description) VALUES (\"Tough\")")
    c.execute("INSERT INTO forgiveness (description) VALUES (\"Nasty\")")
    c.execute("INSERT INTO forgiveness (description) VALUES (\"Cruel\")")
    conn.commit()


def select_format(conn, format_id):
    c = conn.cursor()
    c.execute("SELECT * FROM formats WHERE id=?", (format_id,))
    return c.fetchone()


def select_format_by_name(conn, format_name, case_insensitive=False):
    c = conn.cursor()
    if case_insensitive:
        c.execute("SELECT * FROM formats where name=? COLLATE NOCASE",
                  (format_name,))
    else:
        c.execute("SELECT * FROM formats where name=?", (format_name,))
    return c.fetchone()


def select_all_formats(conn):
    c = conn.cursor()
    c.execute("SELECT id, name FROM formats ORDER BY name ASC")
    return c.fetchall()


def insert_format(conn, name, command):
    c = conn.cursor()
    c.execute("INSERT INTO formats (name, command) VALUES (?, ?)",
              (name, command))
    conn.commit()
    return c.lastrowid


def delete_format(conn, format_id):
    c = conn.cursor()
    c.execute("DELETE FROM formats WHERE id=?", (format_id,))
    conn.commit()


def update_format(conn, format_id, row):
    c = conn.cursor()
    for key in row:
        if key == "id":
            continue
        c.execute("UPDATE formats SET {0}=? where id=?".format(key),
                  (row[key], format_id))
    conn.commit()


def select_story(conn, story_id):
    c = conn.cursor()
    c.execute("SELECT * FROM stories WHERE id=?", (story_id,))
    return c.fetchone()


def select_story_by_title(conn, title, case_insensitive=False):
    c = conn.cursor()
    if case_insensitive:
        c.execute("SELECT * FROM stories WHERE title=? COLLATE NOCASE",
                  (title,))
    else:
        c.execute("SELECT * FROM stories WHERE title=?", (title,))
    return c.fetchone()


def select_stories_by_group(conn, group_id):
    c = conn.cursor()
    c.execute("SELECT * FROM stories WHERE group_id=?", (group_id,))
    return c.fetchall()


def select_stories_by_series(conn, series_id):
    c = conn.cursor()
    c.execute("SELECT * FROM stories WHERE series_id=?", (series_id,))
    return c.fetchall()


def select_all_stories(conn):
    c = conn.cursor()
    c.execute("SELECT * FROM stories")
    return c.fetchall()


def select_all_story_years(conn):
    c = conn.cursor()
    c.execute("SELECT DISTINCT firstpublished FROM stories "
              "ORDER BY firstpublished ASC")
    return c.fetchall()


def select_all_story_langs(conn):
    c = conn.cursor()
    c.execute("SELECT DISTINCT language FROM stories "
              "ORDER BY language ASC")
    return c.fetchall()


def insert_story(conn, title, language, headline, firstpublished,
                 group_id, description, series_id, series_number,
                 forgiveness_id, url, bafn, default_release):
    if select_story_by_title(conn, title) is not None:
        return None
    c = conn.cursor()
    c.execute("INSERT INTO stories (title, language, headline, "
              "firstpublished, group_id, description, series_id, "
              "seriesnumber, forgiveness_id, url, bafn, default_release) "
              "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (title, language, headline, firstpublished, group_id,
               description, series_id, series_number, forgiveness_id, url,
               bafn, default_release))
    conn.commit()
    return c.lastrowid


def delete_story(conn, story_id):
    c = conn.cursor()
    c.execute("DELETE FROM stories WHERE id=?", (story_id,))
    conn.commit()


def update_story(conn, story_id, row):
    c = conn.cursor()
    for key in row:
        if key == "id":
            continue
        c.execute("UPDATE stories SET {0}=? where id=?".format(key),
                  (row[key], story_id))
    conn.commit()


def select_author(conn, author_id):
    c = conn.cursor()
    c.execute("SELECT * FROM authors WHERE id=?", (author_id,))
    return c.fetchone()


def select_author_by_name(conn, author_name, case_insensitive=False):
    c = conn.cursor()
    if case_insensitive:
        c.execute("SELECT * FROM authors WHERE name=? COLLATE NOCASE",
                  (author_name,))
    else:
        c.execute("SELECT * FROM authors WHERE name=?", (author_name,))
    return c.fetchone()


def select_all_authors(conn):
    c = conn.cursor()
    c.execute("SELECT id, name FROM authors ORDER BY name ASC")
    return c.fetchall()


def select_story_authors(conn, story_id):
    c = conn.cursor()
    c.execute("""
SELECT authors.id FROM authors
    JOIN story_author ON authors.id = story_author.author_id
    JOIN stories ON story_author.story_id = stories.id
WHERE stories.id = ?""", (story_id,))
    return c.fetchall()


def select_author_stories(conn, author_id):
    c = conn.cursor()
    c.execute("""
SELECT stories.id FROM stories
    JOIN story_author ON stories.id = story_author.story_id
    JOIN authors ON story_author.author_id = authors.id
WHERE authors.id = ?""", (author_id,))
    return c.fetchall()


def insert_author(conn, name, email=None, url=None):
    c = conn.cursor()
    c.execute("INSERT INTO authors (name, email, url) VALUES (?, ?, ?)",
              (name, email, url))
    conn.commit()
    return c.lastrowid


def delete_author(conn, author_id):
    c = conn.cursor()
    c.execute("DELETE FROM authors WHERE id=?", (author_id,))
    conn.commit()


def update_author(conn, author_id, row):
    c = conn.cursor()
    for key in row:
        if key == "id":
            continue
        c.execute("UPDATE authors SET {0}=? where id=?".format(key),
                  (row[key], author_id))
    conn.commit()


def add_author_to_story(conn, author_id, story_id):
    c = conn.cursor()
    c.execute("INSERT INTO story_author (author_id, story_id) VALUES (?, ?)",
              (author_id, story_id))
    conn.commit()


def remove_author_from_story(conn, author_id, story_id):
    c = conn.cursor()
    c.execute("DELETE FROM story_author WHERE author_id=? AND story_id=?",
              (author_id, story_id))


def select_genre(conn, genre_id):
    c = conn.cursor()
    c.execute("SELECT * FROM genres WHERE id=?", (genre_id,))
    return c.fetchone()


def select_genre_by_name(conn, genre_name, case_insensitive=False):
    c = conn.cursor()
    if case_insensitive:
        c.execute("SELECT id FROM genres WHERE name=? COLLATE NOCASE",
                  (genre_name,))
    else:
        c.execute("SELECT id FROM genres WHERE name=?", (genre_name,))
    return c.fetchone()


def select_all_genres(conn):
    c = conn.cursor()
    c.execute("SELECT id, name FROM genres ORDER BY name ASC")
    return c.fetchall()


def select_story_genres(conn, story_id):
    c = conn.cursor()
    c.execute("""
SELECT genres.id FROM genres
    JOIN story_genre ON genres.id = story_genre.genre_id
    JOIN stories ON story_genre.story_id = stories.id
WHERE stories.id = ?""", (story_id,))
    return c.fetchall()


def select_genre_stories(conn, genre_id):
    c = conn.cursor()
    c.execute("""
SELECT stories.id FROM stories
    JOIN story_genre ON stories.id = story_genre.story_id
    JOIN genres ON story_genre.genre_id = genres.id
WHERE genres.id = ?""", (genre_id,))
    return c.fetchall()


def insert_genre(conn, name):
    c = conn.cursor()
    c.execute("INSERT INTO genres (name) VALUES (?)", (name,))
    conn.commit()
    return c.lastrowid


def delete_genre(conn, genre_id):
    c = conn.cursor()
    c.execute("DELETE FROM genres WHERE id=?", (genre_id,))
    conn.commit()


def add_genre_to_story(conn, genre_id, story_id):
    c = conn.cursor()
    c.execute("INSERT INTO story_genre (genre_id, story_id) VALUES (?, ?)",
              (genre_id, story_id))
    conn.commit()


def remove_genre_from_story(conn, genre_id, story_id):
    c = conn.cursor()
    c.execute("DELETE FROM story_genre WHERE genre_id=? AND story_id=?",
              (genre_id, story_id))
    conn.commit()


def insert_cover(conn, story_id, img_format, height, width, description, data):
    c = conn.cursor()
    c.execute("INSERT INTO covers (story_id, format, height, width, "
              "description, data) VALUES (?, ?, ?, ?, ?, ?)",
              (story_id, img_format, height, width, description,
               sqlite3.Binary(data)))
    conn.commit()
    return c.lastrowid


def delete_cover(conn, cover_id):
    c = conn.cursor()
    c.execute("DELETE FROM covers WHERE id=?", (cover_id,))
    conn.commit()


def update_cover(conn, cover_id, row):
    c = conn.cursor()
    for key in row:
        if key == "id":
            continue
        c.execute("UPDATE covers SET {0}=? where id=?".format(key),
                  (row[key], cover_id))
    conn.commit()


def select_cover(conn, cover_id):
    c = conn.cursor()
    c.execute("SELECT * FROM covers WHERE id=?", (cover_id,))
    return c.fetchone()


def select_cover_by_story(conn, story_id):
    c = conn.cursor()
    c.execute("SELECT * FROM covers WHERE story_id=?", (story_id,))
    return c.fetchone()


def insert_annotation(conn, story_id, rating, rating_txt, notes,
                      played, imported):
    c = conn.cursor()
    c.execute("INSERT INTO annotation (story_id, rating, rating_txt, notes, "
              "played, imported) VALUES (?, ?, ?, ?, ?, ?)",
              (story_id, rating, rating_txt, notes, played, imported))
    conn.commit()
    return c.lastrowid


def delete_annotation(conn, annot_id):
    c = conn.cursor()
    c.execute("DELETE FROM annotation WHERE id=?", (annot_id,))
    conn.commit()


def update_annotation(conn, annot_id, row):
    c = conn.cursor()
    for key in row:
        if key == "id":
            continue
        c.execute("UPDATE annotation SET {0}=? where id=?".format(key),
                  (row[key], annot_id))
    conn.commit()


def select_annotation(conn, annot_id):
    c = conn.cursor()
    c.execute("SELECT * FROM annotation WHERE id=?", (annot_id,))
    return c.fetchone()


def select_annotation_by_story(conn, story_id):
    c = conn.cursor()
    c.execute("SELECT * FROM annotation WHERE story_id=?", (story_id,))
    return c.fetchone()


def insert_ifdb_annotation(conn, story_id, tuid, url, cover_url,
                           avg_rating, star_rating, star_rating_txt,
                           rating_count_avg, rating_count_tot, updated):
    c = conn.cursor()
    c.execute("INSERT INTO ifdb_annotation (story_id, tuid, url, cover_url, "
              "avg_rating, star_rating, star_rating_txt, rating_count_avg, "
              "rating_count_tot, updated) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, "
              "?)",
              (story_id, tuid, url, cover_url, avg_rating, star_rating,
               star_rating_txt, rating_count_avg, rating_count_tot, updated))
    conn.commit()
    return c.lastrowid


def delete_ifdb_annotation(conn, annot_id):
    c = conn.cursor()
    c.execute("DELETE FROM ifdb_annotation WHERE id=?", (annot_id,))
    conn.commit()


def update_ifdb_annotation(conn, annot_id, row):
    c = conn.cursor()
    for key in row:
        if key == "id":
            continue
        c.execute("UPDATE ifdb_annotation SET {0}=? where id=?".format(key),
                  (row[key], annot_id))
    conn.commit()


def select_ifdb_annotation(conn, annot_id):
    c = conn.cursor()
    c.execute("SELECT * FROM ifdb_annotation WHERE id=?", (annot_id,))
    return c.fetchone()


def select_ifdb_annotation_by_story(conn, story_id):
    c = conn.cursor()
    c.execute("SELECT * FROM ifdb_annotation WHERE story_id=?", (story_id,))
    return c.fetchone()


def insert_release(conn, ifid, story_id, uri, version, release_date, compiler,
                   compiler_version, comment, format_id):
    c = conn.cursor()
    c.execute("INSERT INTO releases (ifid, story_id, uri, version, "
              "release_date, compiler, compiler_version, comment, format_id) "
              "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (ifid, story_id, uri, version, release_date, compiler,
               compiler_version, comment, format_id))
    conn.commit()
    return c.lastrowid


def delete_release(conn, ifid):
    c = conn.cursor()
    c.execute("DELETE FROM releases WHERE ifid=?", (ifid,))
    conn.commit()


def update_release(conn, ifid, row):
    c = conn.cursor()
    for key in row:
        if key == "id":
            continue
        c.execute("UPDATE releases SET {0}=? where ifid=?".format(key),
                  (row[key], ifid))
    conn.commit()


def select_release(conn, ifid):
    c = conn.cursor()
    c.execute("SELECT * FROM releases WHERE ifid=?", (ifid,))
    return c.fetchone()


def select_releases_by_story(conn, story_id):
    c = conn.cursor()
    c.execute("SELECT * FROM releases WHERE story_id=?", (story_id,))
    return c.fetchall()


def select_release_by_uri(conn, uri):
    c = conn.cursor()
    c.execute("SELECT * FROM releases WHERE uri=?", (uri,))
    return c.fetchone()


def select_tag(conn, tag_id):
    c = conn.cursor()
    c.execute("SELECT * FROM tags WHERE id=?", (tag_id,))
    return c.fetchone()


def select_tag_by_name(conn, tag_name, case_insensitive=False):
    c = conn.cursor()
    if case_insensitive:
        c.execute("SELECT id FROM tags WHERE name=? COLLATE NOCASE",
                  (tag_name,))
    else:
        c.execute("SELECT id FROM tags WHERE name=?", (tag_name,))
    return c.fetchone()


def select_story_tags(conn, story_id):
    c = conn.cursor()
    c.execute("""
SELECT tags.id FROM tags
    JOIN story_tag ON tags.id = story_tag.tag_id
    JOIN stories ON story_tag.story_id = stories.id
WHERE stories.id = ?""", (story_id,))
    return c.fetchall()


def select_tag_stories(conn, tag_id):
    c = conn.cursor()
    c.execute("""
SELECT stories.id FROM stories
    JOIN story_tag ON stories.id = story_tag.story_id
    JOIN tags ON story_tag.tag_id = tags.id
WHERE tags.id = ?""", (tag_id,))
    return c.fetchall()


def select_all_tags(conn):
    c = conn.cursor()
    c.execute("SELECT id, name FROM tags ORDER BY name ASC")
    return c.fetchall()


def insert_tag(conn, name):
    c = conn.cursor()
    c.execute("INSERT INTO tags (name) VALUES (?)", (name,))
    conn.commit()
    return c.lastrowid


def delete_tag(conn, tag_id):
    c = conn.cursor()
    c.execute("DELETE FROM tags WHERE id=?", (tag_id,))
    conn.commit()


def add_tag_to_story(conn, tag_id, story_id):
    c = conn.cursor()
    c.execute("INSERT INTO story_tag (tag_id, story_id) VALUES (?, ?)",
              (tag_id, story_id))
    conn.commit()


def remove_tag_from_story(conn, tag_id, story_id):
    c = conn.cursor()
    c.execute("DELETE FROM story_tag WHERE tag_id=? AND story_id=?",
              (tag_id, story_id))


def insert_resource(conn, story_id, uri):
    c = conn.cursor()
    c.execute("INSERT INTO resources (story_id, uri) VALUES (?, ?)",
              (story_id, uri))
    conn.commit()
    return c.lastrowid


def delete_resource(conn, res_id):
    c = conn.cursor()
    c.execute("DELETE FROM resources WHERE id=?", (res_id,))
    conn.commit()


def update_resource(conn, res_id, row):
    c = conn.cursor()
    for key in row:
        if key == "id":
            continue
        c.execute("UPDATE resources SET {0}=? where id=?".format(key),
                  (row[key], res_id))
    conn.commit()


def select_resource(conn, res_id):
    c = conn.cursor()
    c.execute("SELECT * FROM resources WHERE id=?", (res_id,))
    return c.fetchone()


def select_resource_by_uri(conn, res_uri):
    c = conn.cursor()
    c.execute("SELECT * FROM resources WHERE uri=?", (res_uri,))
    return c.fetchone()


def select_resources_by_story(conn, story_id):
    c = conn.cursor()
    c.execute("SELECT * FROM resources WHERE story_id=?", (story_id,))
    return c.fetchall()


