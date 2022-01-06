# -*- coding: utf-8 -*-
#
#       library.py
#
#       Copyright © 2011, 2014, 2015, 2017, 2018 Brandon Invergo <brandon@invergo.net>
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


import locale
import datetime

from gi.repository import Gtk, Pango

from filterstore import FilterStore
from grotesque import db, util, ifdb
from treatyofbabel import ifiction


class Library:
    '''A class to store the user's library of interactive fiction.

    '''
    def __init__(self, conn):
        self.conn = conn
        # The main list store contains the following columns: 0:
        # played state, 1: title, 2: author, 3: language, 4: headline,
        # 5: publishing date, 6: genre, 7: group, 8: series, 9: series
        # number, 10: forgiveness, 11: tags, 12: date imported 13: star rating
        # text, 14: IFDB rating text, 15: star rating float, 16: IFDB
        # rating float, 17: story id, 18: text weight
        self.list_store = Gtk.ListStore(bool, str, str, str, str, str, str,
                                        str, str, int, str, str, str, str, str,
                                        float, float, int, Pango.Weight)
        self.list_store.set_sort_column_id(1, Gtk.SortType.ASCENDING)
        for col in range(1, 13):
            self.list_store.set_sort_func(col, self._sort, None)
        self.story_id_col = 17
        self.weight_col = 18
        # The following Filterstores keep track of which authors, years, etc
        # are currently represented in the library so the user may filter it by
        # them.
        self.author_store = FilterStore(self.conn, db.query.select_all_authors)
        self.year_store = FilterStore(self.conn, self._all_pub_years)
        self.genre_store = FilterStore(self.conn, db.query.select_all_genres)
        self.group_store = FilterStore(self.conn, db.query.select_all_groups)
        self.series_store = FilterStore(self.conn, db.query.select_all_series)
        self.forgiveness_store = FilterStore(self.conn,
                                             db.query.select_all_forgiveness)
        self.rating_store = FilterStore(self.conn, self._all_star_ratings)
        self.ifdb_rating_store = FilterStore(self.conn, self._all_star_ratings)
        self.lang_store = FilterStore(self.conn, self._all_langs)
        self.tag_store = FilterStore(self.conn, db.query.select_all_tags)
        stories = db.query.select_all_stories(self.conn)
        for story_row in stories:
            self.add_story_from_db_rec(story_row)

    def update_filter_stores(self):
        self.author_store.update()
        self.year_store.update()
        self.genre_store.update()
        self.group_store.update()
        self.series_store.update()
        self.tag_store.update()

    def add_story_from_db_rec(self, story_row, row_iter=None):
        """Add a story to the liststore from a database row.

        """
        if not story_row:
            return
        annotation = db.query.select_annotation_by_story(self.conn,
                                                         story_row["id"])
        if annotation:
            played = bool(annotation["played"])
            rating = annotation["rating"]
            rating_txt = annotation["rating_txt"]
            imported = str(annotation["imported"])
        else:
            played = False
            rating = 0.0
            rating_txt = util.render_star_rating(0.0)
            imported = ""
        if played:
            text_weight = Pango.Weight.NORMAL
        else:
            text_weight = Pango.Weight.BOLD
        ifdb_annotation = db.query.select_ifdb_annotation_by_story(
            self.conn, story_row["id"])
        if ifdb_annotation:
            ifdb_rating = ifdb_annotation["star_rating"]
            ifdb_rating_txt = ifdb_annotation["star_rating_txt"]
        else:
            ifdb_rating = 0.0
            ifdb_rating_txt = util.render_star_rating(0.0)
        author_ids = db.query.select_story_authors(self.conn, story_row["id"])
        authors_list = [db.query.select_author(self.conn, author_id[0])["name"] for
                        author_id in author_ids]
        authors = ", ".join(authors_list)
        if story_row["firstpublished"] is not None:
            yearpublished = str(story_row["firstpublished"].year)
        else:
            yearpublished = ""
        genre_ids = db.query.select_story_genres(self.conn, story_row["id"])
        if genre_ids:
            genres_list = [db.query.select_genre(self.conn, genre_id[0])["name"] for
                           genre_id in genre_ids]
            genres = "/".join(genres_list)
        else:
            genres = ""
        if story_row["group_id"] is not None:
            group_row = db.query.select_group(self.conn, story_row["group_id"])
            group = group_row["name"]
        else:
            group = ""
        if story_row["series_id"] is not None:
            series_row = db.query.select_series(self.conn, story_row["series_id"])
            series = series_row["name"]
        else:
            series = ""
        if story_row["forgiveness_id"] is not None:
            forgive_row = db.query.select_forgiveness(
                self.conn, story_row["forgiveness_id"])
            forgiveness = forgive_row["description"]
        else:
            forgiveness = ""
        tag_ids = db.query.select_story_tags(self.conn, story_row["id"])
        if tag_ids:
            tags_list = [db.query.select_tag(self.conn, tag_id[0])["name"] for
                           tag_id in tag_ids]
            tags = "/".join(tags_list)
        else:
            tags = ""
        if row_iter is None:
            row_iter = self.list_store.insert(-1)
        self.list_store.set_row(row_iter,
                                [played, story_row["title"], authors,
                                 story_row["language"],
                                 story_row["headline"], yearpublished,
                                 genres, group, series,
                                 story_row["seriesnumber"],
                                 forgiveness, tags, imported, rating_txt,
                                 ifdb_rating_txt, rating, ifdb_rating,
                                 story_row["id"], text_weight])

    def story_iter(self, story_id):
        row_iter = self.list_store.get_iter_first()
        while row_iter:
            row_story_id = self.get_story_id(row_iter)
            if row_story_id == story_id:
                return row_iter
            row_iter = self.list_store.iter_next(row_iter)
        return None

    def _all_star_ratings(self, conn):
        return [(n, rating) for (n, rating) in
                enumerate(util.STAR_RATINGS[1:])]

    def _all_pub_years(self, conn):
        pub_rows = db.query.select_all_story_years(conn)
        years = set()
        for row in pub_rows:
            if row is not None and row[0] is not None:
                years.add(row[0].year)
        return [(n, str(year)) for (n, year) in enumerate(years)]

    def _all_langs(self, conn):
        lang_rows = db.query.select_all_story_langs(conn)
        langs = set()
        for row in lang_rows:
            if row is not None and row[0] is not None:
                langs.add(row[0])
        return [(n, str(lang)) for (n, lang) in enumerate(langs)]

    def toggle_story_played(self, row_iter):
        """Toggle a story's played state."""
        story_id = self.get_story_id(row_iter)
        annot_row = db.query.select_annotation_by_story(self.conn, story_id)
        cur_played = annot_row["played"]
        if cur_played:
            self.list_store.set_value(row_iter, 0, False)
            db.query.update_annotation(self.conn, annot_row["id"],
                                 {"played": False})
            self.list_store.set_value(row_iter, self.weight_col,
                                      Pango.Weight.BOLD)
        else:
            self.list_store.set_value(row_iter, 0, True)
            db.query.update_annotation(self.conn, annot_row["id"],
                                 {"played": True})
            self.list_store.set_value(row_iter, self.weight_col,
                                      Pango.Weight.NORMAL)

    def refresh_ifdb(self, row_iter):
        """Refresh a story's IFDB annotation (rating, etc.)."""
        story_id = self.get_story_id(row_iter)
        ifdb_annot_row = db.query.select_ifdb_annotation_by_story(
            self.conn, story_id)
        if not ifdb_annot_row:
            return
        tuid = ifdb_annot_row["tuid"]
        if not tuid:
            return
        ific_story = ifdb.fetch_ifiction(tuid=tuid)
        annotation = ifiction.get_annotation(ific_story)
        ifdb_annot = annotation["ifdb"]
        if "coverart" in ifdb_annot and "url" in ifdb_annot["coverart"]:
            cover_url = ifdb_annot["coverart"]["url"]
            cover_url = cover_url.replace("&", "&amp;")
        else:
            cover_url = None
        if "starrating" in ifdb_annot:
            star_rating_txt = util.render_star_rating(
                float(ifdb_annot["starrating"]))
        else:
            star_rating_txt = ""
        last_updated = str(datetime.date.today())
        new_ifdb_row = {"tuid": ifdb_annot.get("tuid"),
                        "url": ifdb_annot.get("link"),
                        "cover_url": cover_url,
                        "avg_rating": ifdb_annot.get("averagerating"),
                        "star_rating": ifdb_annot.get("starrating"),
                        "star_rating_txt": star_rating_txt,
                        "rating_count_avg": ifdb_annot.get("ratingcountavg"),
                        "rating_count_tot": ifdb_annot.get("ratingcounttot"),
                        "updated": last_updated}
        db.query.update_ifdb_annotation(self.conn, ifdb_annot_row["id"],
                                        new_ifdb_row)
        self.add_story_from_db_rec(
            db.query.select_story(self.conn, story_id), row_iter)

    def mark_story_played(self, row_iter):
        """Mark a story as having been played."""
        story_id = self.get_story_id(row_iter)
        annot_row = db.query.select_annotation_by_story(self.conn, story_id)
        db.query.update_annotation(self.conn, annot_row["id"], {"played": True})
        self.list_store.set_value(row_iter, 0, True)
        self.list_store.set_value(row_iter, self.weight_col,
                                  Pango.Weight.NORMAL)

    def get_story_id(self, row_iter):
        """This is a small helper method to return a story file."""
        if row_iter is None:
            return None
        return self.list_store.get_value(row_iter, self.story_id_col)

    def _sort(self, model, iter1, iter2, data):
        col, _ = model.get_sort_column_id()
        value1 = model.get_value(iter1, col)
        value2 = model.get_value(iter2, col)
        if value1 is None:
            return 1
        elif value2 is None:
            return -1
        return locale.strcoll(value1, value2)
