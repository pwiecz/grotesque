# -*- coding: utf-8 -*-
#
#       infoview.py
#
#       Copyright © 2011, 2014, 2015, 2017, 2018 Brandon Invergo <brandon@invergo.net>
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
import cgi

from gi.repository import Gtk, Pango

from grotesque import db, util


class InfoView(Gtk.Paned):
    '''This class implements a widget which displays story information.

    '''
    def __init__(self, conn, settings):
        self.conn = conn
        self.settings = settings
        biblio_buffer = Gtk.TextBuffer()
        self._setup_biblio_tags(biblio_buffer)
        self.biblio_view = Gtk.TextView(buffer=biblio_buffer)
        self.biblio_view.set_hexpand(False)
        self.biblio_view.set_vexpand(True)
        self.biblio_view.set_pixels_above_lines(5)
        self.biblio_view.set_pixels_below_lines(5)
        self.biblio_view.set_indent(25)
        self.biblio_view.set_justification(Gtk.Justification.FILL)
        self.biblio_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.biblio_view.set_cursor_visible(False)
        self.biblio_view.set_editable(False)
        biblio_scroll = Gtk.ScrolledWindow()
        biblio_scroll.set_policy(Gtk.PolicyType.AUTOMATIC,
                                 Gtk.PolicyType.AUTOMATIC)
        biblio_scroll.add(self.biblio_view)

        info_buffer = Gtk.TextBuffer()
        # Info: Small & italic
        info_tag = Gtk.TextTag(name='info')
        info_tag.set_property('scale', 0.83)
        info_tag.set_property('style', Pango.Style.ITALIC)
        tag_table = info_buffer.get_tag_table()
        tag_table.add(info_tag)
        self.info_view = Gtk.TextView(buffer=info_buffer)
        self.info_view.set_hexpand(False)
        self.info_view.set_vexpand(True)
        self.info_view.set_cursor_visible(False)
        self.info_view.set_editable(False)
        self.info_view.set_left_margin(10)
        self.info_view.set_right_margin(10)
        self.info_view.set_top_margin(10)
        self.info_view.set_bottom_margin(10)
        self.info_view.set_wrap_mode(Gtk.WrapMode.WORD)
        info_scroll = Gtk.ScrolledWindow()
        info_scroll.set_policy(Gtk.PolicyType.AUTOMATIC,
                                 Gtk.PolicyType.AUTOMATIC)
        info_scroll.add(self.info_view)
        # info_frame = Gtk.Frame()
        # info_frame.add(info_scroll)
        super(InfoView, self).__init__()
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.pack1(biblio_scroll, False, False)
        self.pack2(info_scroll, True, True)

    def _setup_biblio_tags(self, text_buffer):
        # Create all of the tags which will markup the text:
        # Title: XX-large & bold
        title_tag = Gtk.TextTag(name='title')
        title_tag.set_property('scale', 1.2 ** 4)
        title_tag.set_property('weight', Pango.Weight.BOLD)
        title_tag.set_property('justification', Gtk.Justification.CENTER)
        # Headline: X-Large & italic
        headline_tag = Gtk.TextTag(name='headline')
        headline_tag.set_property('scale', 1.2 ** 2)
        headline_tag.set_property('style', Pango.Style.ITALIC)
        headline_tag.set_property('justification', Gtk.Justification.CENTER)
        # Series: X-Large
        series_tag = Gtk.TextTag(name='series')
        series_tag.set_property('scale', 1.2)
        series_tag.set_property('justification', Gtk.Justification.CENTER)
        # Author: Large
        author_tag = Gtk.TextTag(name='author')
        author_tag.set_property('scale', 1.2)
        author_tag.set_property('justification', Gtk.Justification.CENTER)
        # Group: Centered
        group_tag = Gtk.TextTag(name='group')
        group_tag.set_property('justification', Gtk.Justification.CENTER)
        # Year: Centered
        year_tag = Gtk.TextTag(name='year')
        year_tag.set_property('justification', Gtk.Justification.CENTER)
        # Plain text bold
        bold_tag = Gtk.TextTag(name='bold')
        bold_tag.set_property('weight', Pango.Weight.BOLD)
        # Plain text italics
        italics_tag = Gtk.TextTag(name='italics')
        italics_tag.set_property('style', Pango.Style.ITALIC)
        tag_table = text_buffer.get_tag_table()
        for tag in [title_tag, headline_tag, series_tag, author_tag, year_tag,
                    group_tag, bold_tag, italics_tag]:
            tag_table.add(tag)

    def _render_title(self, text_buffer, text_iter, tag_table, story_row):
        if story_row["title"] is None:
            title = ""
        else:
            title = story_row["title"]
        text_buffer.insert_with_tags(
            text_iter,
            u'{0}\n'.format(title),
            tag_table.lookup('title'))
        headline = story_row["headline"]
        if headline not in [None, '']:
            text_buffer.insert_with_tags(
                text_iter,
                u'{0}\n'.format(headline),
                tag_table.lookup('headline'))

    def _insert_blank_line(self, text_buffer, text_iter):
        text_buffer.insert_with_tags(text_iter, u'\n')

    def _render_series(self, text_buffer, text_iter, tag_table, story_row):
        series_id = story_row["series_id"]
        if series_id is None:
            return
        series_row = db.query.select_series(self.conn, series_id)
        if series_row is None:
            return
        series_name = series_row["name"]
        if not series_name:
            return
        series_number = story_row["seriesnumber"]
        if series_number is not None:
            text_buffer.insert_with_tags(
                text_iter,
                u'{0} (part {1})\n'.format(series_name, series_number),
                tag_table.lookup('series'))
        else:
            text_buffer.insert_with_tags(
                text_iter,
                u'{0}\n'.format(series_name),
                tag_table.lookup('series'))

    def _build_author_list(self, author_names):
        if len(author_names) == 1:
            return author_names[0]
        return ", ".join(author_names[:-1]) + " and " + author_names[-1]

    def _render_author(self, text_buffer, text_iter, tag_table, story_row):
        author_ids = db.query.select_story_authors(self.conn, story_row["id"])
        if not author_ids:
            return
        author_names = []
        for author_id in author_ids:
            author_row = db.query.select_author(self.conn, author_id[0])
            author_names.append(author_row["name"])
        authors = self._build_author_list(author_names)
        text_buffer.insert_with_tags(
            text_iter, u'{0}\n'.format(authors),
            tag_table.lookup('author'))

    def _render_group(self, text_buffer, text_iter, tag_table, story_row):
        group_id = story_row["group_id"]
        if group_id is None:
            return
        group_row = db.query.select_group(self.conn, group_id)
        if group_row is None:
            return
        group = group_row["name"]
        if not group:
            return
        if group != "":
            text_buffer.insert_with_tags(text_iter, u'{0}\n'.format(group),
                                         tag_table.lookup("group"))

    def _render_year(self, text_buffer, text_iter, tag_table, story_row):
        if story_row["firstpublished"] is not None:
            yearpublished = str(story_row["firstpublished"].year)
            text_buffer.insert_with_tags(
                text_iter, u'{0}\n'.format(yearpublished),
                tag_table.lookup("year"))

    def _render_rating(self, text_buffer, text_iter, tag_table, story_row):
        annot_row = db.query.select_annotation_by_story(self.conn, story_row["id"])
        if annot_row is not None:
            starrating = annot_row["rating_txt"]
            if starrating:
                text_buffer.insert(text_iter, u'Rating: ')
                text_buffer.insert_with_tags(
                    text_iter, u'{0}\n'.format(starrating),
                    tag_table.lookup("info"))
        ifdb_annot_row = db.query.select_ifdb_annotation_by_story(
            self.conn, story_row["id"])
        if ifdb_annot_row is not None:
            starrating = ifdb_annot_row["star_rating_txt"]
            if starrating:
                text_buffer.insert(text_iter, u'IFDB rating: ')
                text_buffer.insert_with_tags(
                    text_iter, u'{0}\n'.format(starrating),
                    tag_table.lookup("info"))

    def _render_description(self, text_buffer, text_iter, tag_table,
                            story_row):
        description = story_row["description"]
        if description is not None and description != "":
            self._insert_blank_line(text_buffer, text_iter)
            cut_description = self.format_html(description)
            for chunk in cut_description:
                if chunk[1] is None:
                    text_buffer.insert(text_iter, chunk[0])
                else:
                    text_buffer.insert_with_tags(
                        text_iter, chunk[0], tag_table.lookup(chunk[1]))
            text_buffer.insert(text_iter, u'\n')

    def _render_info(self, text_buffer, text_iter, tag_table, story_row):
        genre_ids = db.query.select_story_genres(self.conn, story_row["id"])
        if genre_ids:
            genre_names = []
            for genre_id in genre_ids:
                genre_row = db.query.select_genre(self.conn, genre_id[0])
                genre_names.append(genre_row["name"])
            genres = "\n\t".join(genre_names)
            if len(genre_ids) > 1:
                text_buffer.insert(text_iter, u'Genres:')
                text_buffer.insert_with_tags(
                    text_iter,
                    u'\n\t{0}\n'.format(genres),
                    tag_table.lookup('info'))
            else:
                text_buffer.insert(text_iter, u'Genre:')
                text_buffer.insert_with_tags(
                    text_iter,
                    u' {0}\n'.format(genres),
                    tag_table.lookup('info'))
        tag_ids = db.query.select_story_tags(self.conn, story_row["id"])
        if tag_ids:
            tag_names = []
            for tag_id in tag_ids:
                tag_row = db.query.select_tag(self.conn, tag_id[0])
                tag_names.append(tag_row["name"])
            tags = "\n\t".join(tag_names)
            if len(tag_ids) > 1:
                text_buffer.insert(text_iter, u'Tags:')
                text_buffer.insert_with_tags(
                    text_iter,
                    u'\n\t{0}\n'.format(tags),
                    tag_table.lookup('info'))
            else:
                text_buffer.insert(text_iter, u'Tag:')
                text_buffer.insert_with_tags(
                    text_iter,
                    u' {0}\n'.format(tags),
                    tag_table.lookup('info'))
        forgiveness_id = story_row["forgiveness_id"]
        if forgiveness_id is not None:
            forgiveness_row = db.query.select_forgiveness(self.conn, forgiveness_id)
            forgiveness = forgiveness_row["description"]
        else:
            forgiveness = "Unknown"
        text_buffer.insert(text_iter, 'Forgiveness: ')
        text_buffer.insert_with_tags(
            text_iter,
            u'{0}\n'.format(forgiveness),
            tag_table.lookup('info'))

    def _render_releases(self, text_buffer, text_iter, story_row):
        story_id = story_row["id"]
        story_releases_full = db.query.select_releases_by_story(self.conn,
                                                                story_id)
        story_releases = [release for release in story_releases_full
                          if release["uri"]]
        text_buffer.insert(text_iter, "Releases:\n")
        for release in story_releases:
            default = release["ifid"] == story_row["default_release"]
            rel_format_id = release["format_id"]
            rel_format_rec = db.query.select_format(self.conn, rel_format_id)
            if rel_format_rec is None:
                continue
            rel_format = rel_format_rec["name"]
            rel_uri = release["uri"]
            rel_comment = release["comment"]
            if rel_comment:
                rel_note = ", ".join([rel_format, rel_comment])
            else:
                rel_note = rel_format
            rel_filename = os.path.basename(rel_uri)
            rel_anchor = text_buffer.create_child_anchor(text_iter)
            rel_label = Gtk.Label()
            rel_label.set_track_visited_links(False)
            if default:
                rel_label.set_markup(
                    '\t<b><a href="{0}">{1} ({2})</a></b>'.format(
                        cgi.escape(rel_uri), cgi.escape(rel_filename),
                        cgi.escape(rel_note)))
            else:
                rel_label.set_markup(
                    '\t<a href="{0}">{1} ({2})</a>'.format(
                        cgi.escape(rel_uri), cgi.escape(rel_filename),
                        cgi.escape(rel_note)))
            rel_label.connect("activate-link", self._on_release_clicked)
            self.info_view.add_child_at_anchor(rel_label, rel_anchor)
            rel_label.show()
            text_buffer.insert(text_iter, "\n")

    def _on_release_clicked(self, widget, uri):
        release_rec = db.query.select_release_by_uri(self.conn, uri)
        story_id = release_rec["story_id"]
        try:
            db.launch_story(self.conn, self.settings, story_id,
                            release_rec["ifid"])
        except ValueError as e:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.OK)
            d.set_markup(str(e))
            d.run()
            d.destroy()
            return

    def _render_urls(self, text_buffer, text_iter, story_row):
        url_added = False
        if story_row["url"]:
            text_buffer.insert(text_iter, "On the web:\n")
            url_anchor = text_buffer.create_child_anchor(text_iter)
            url_label = Gtk.Label()
            url_label.set_track_visited_links(False)
            url_label.set_markup(
                '\t<a href="{0}">Homepage</a>'.format(story_row["url"]))
            url_label.set_tooltip_text(story_row["url"])
            self.info_view.add_child_at_anchor(url_label, url_anchor)
            url_label.show()
            text_buffer.insert(text_iter, "\n")
            url_added = True
        ifdb_annot = db.query.select_ifdb_annotation_by_story(
            self.conn, story_row["id"])
        if ifdb_annot and ifdb_annot["url"]:
            if not url_added:
                text_buffer.insert(text_iter, "On the web:\n")
            ifdb_url_anchor = text_buffer.create_child_anchor(text_iter)
            ifdb_url_label = Gtk.Label()
            ifdb_url_label.set_track_visited_links(False)
            ifdb_url_label.set_markup(
                '\t<a href="{0}">IFDB entry</a>'.format(ifdb_annot["url"]))
            ifdb_url_label.set_tooltip_text(ifdb_annot["url"])
            self.info_view.add_child_at_anchor(ifdb_url_label, ifdb_url_anchor)
            ifdb_url_label.show()
            text_buffer.insert(text_iter, "\n")

    def _on_resource_clicked(self, widget, uri):
        try:
            launcher = self.settings.get_resource_launcher()
            util.open_resource(uri, launcher)
        except ValueError as e:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.OK)
            d.set_markup(str(e))
            d.run()
            d.destroy()
            return

    def _render_resources(self, text_buffer, text_iter, tag_table, story_row):
        resources = db.query.select_resources_by_story(self.conn, story_row["id"])
        if not resources:
            return
        text_buffer.insert(text_iter, "Resources:\n")
        for resource in resources:
            if not resource["description"]:
                continue
            resource_anchor = text_buffer.create_child_anchor(text_iter)
            resource_label = Gtk.Label()
            resource_label.set_track_visited_links(False)
            resource_label.set_markup(
                '\t<a href="{0}">{1}</a>'.format(cgi.escape(resource["uri"]),
                                                 cgi.escape(resource["description"])))
            resource_label.connect("activate-link", self._on_resource_clicked)
            self.info_view.add_child_at_anchor(resource_label, resource_anchor)
            resource_label.show()
            text_buffer.insert(text_iter, "\n")

    def render_story(self, story_id):
        '''This method inserts the story information in the text buffer and
        applies the markup tags to properly format it.

        '''
        self.clear()
        biblio_buffer = self.biblio_view.get_buffer()
        biblio_iter = biblio_buffer.get_start_iter()
        biblio_tag_table = biblio_buffer.get_tag_table()
        story_row = db.query.select_story(self.conn, story_id)
        if story_row is None:
            return
        self._render_title(biblio_buffer, biblio_iter, biblio_tag_table, story_row)
        self._render_series(biblio_buffer, biblio_iter, biblio_tag_table, story_row)
        self._insert_blank_line(biblio_buffer, biblio_iter)
        self._render_author(biblio_buffer, biblio_iter, biblio_tag_table, story_row)
        self._render_group(biblio_buffer, biblio_iter, biblio_tag_table, story_row)
        self._render_year(biblio_buffer, biblio_iter, biblio_tag_table, story_row)
        self._render_description(biblio_buffer, biblio_iter, biblio_tag_table, story_row)
        self._insert_blank_line(biblio_buffer, biblio_iter)
        info_buffer = self.info_view.get_buffer()
        info_iter = info_buffer.get_start_iter()
        info_tag_table = info_buffer.get_tag_table()
        self._render_rating(info_buffer, info_iter, info_tag_table, story_row)
        self._render_info(info_buffer, info_iter, info_tag_table, story_row)
        self._insert_blank_line(info_buffer, info_iter)
        self._render_releases(info_buffer, info_iter, story_row)
        self._render_urls(info_buffer, info_iter, story_row)
        self._render_resources(info_buffer, info_iter, info_tag_table, story_row)

    def clear(self):
        '''This is a helper method to clear the contents of the view.

        '''
        biblio_buffer = self.biblio_view.get_buffer()
        biblio_buffer.set_text('')
        info_buffer = self.info_view.get_buffer()
        info_buffer.set_text('')

    def format_html(self, text):
        """Do *extremely* basic HTML parsing on the description.  These
        sometimes contain some HTML formatting tags like <i> or <b>.
        However, using a full HTML renderer would be overkill.
        """
        tag_formats = {'i': 'italics', 'b': 'bold'}
        text = text.replace('<br/>', '\n')
        text = text.replace('<br />', '\n')
        text = text.replace('<p>', '\n\n')
        text = text.replace('</p>', '')
        cut_text = []
        index = 0
        while index < len(text):
            start = text[index:].find('<')
            if start >= 0:
                if (text[index+start+1] not in tag_formats or
                        text[index+start+2] != ">"):
                    cut_text.append((text[index:index+start+1], None))
                    index += start + 1
                    continue
                cut_text.append((text[index:index+start], None))
                tag = text[index+start+1]
                end = text[index+start+3:].find('</{0}>'.format(tag))
                if end >= 0:
                    cut_text.append((text[index+start+3:index+start+3+end],
                                     tag_formats[tag]))
                    index += start + 3 + end + 4
                else:
                    index += start + 3
            else:
                cut_text.append((text[index:], None))
                break
        return cut_text
