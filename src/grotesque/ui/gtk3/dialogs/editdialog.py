# -*- coding: utf-8 -*-
#
#       editdialog.py
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
import datetime
import re

from gi.repository import Gtk, Pango, GdkPixbuf

from grotesque import db, ifdb, util
import treatyofbabel
from treatyofbabel import ifiction
from treatyofbabel.utils import _imgfuncs
from treatyofbabel.babelerrors import BabelError


PADDING = 10
MAX_IMG_SIZE = 500


class EditDialog(Gtk.Dialog):
    '''This dialog is for editing stories.

    '''
    def __init__(self, conn, settings, parent=None, on_import=False):
        if on_import:
            super(EditDialog, self).__init__(
                "Story Information", parent, Gtk.DialogFlags.MODAL,
                ("Skip", Gtk.ResponseType.REJECT,
                 "Done", Gtk.ResponseType.ACCEPT))
        else:
            super(EditDialog, self).__init__(
            "Story Information", parent, Gtk.DialogFlags.MODAL,
            ("Done", Gtk.ResponseType.ACCEPT))
        self.conn = conn
        self.settings = settings
        self.library = parent.library
        self.set_default_size(1024, 768)
        self._meta_fields = {}
        self._cover_widgets = {}
        self.story_id = None
        self.edited = False
        self.init_complete = False
        self.widget_updated = False
        self.forgiveness = [f["description"] for f in
                            db.query.select_all_forgiveness(self.conn)]
        self.notebook = Gtk.Notebook()
        meta_grid = self._build_meta_grid()
        self.notebook.append_page(meta_grid, Gtk.Label("Metadata"))
        cover_view = self._build_cover_view()
        self.notebook.append_page(cover_view, Gtk.Label("Cover Art"))
        release_list = self._build_release_list()
        self.notebook.append_page(release_list, Gtk.Label("Releases"))
        resource_list = self._build_resource_list()
        self.notebook.append_page(resource_list, Gtk.Label("Resources"))
        vbox = self.get_child()
        self.notebook.set_hexpand(True)
        self.notebook.set_vexpand(True)
        vbox.add(self.notebook)
        vbox.show_all()

    def _build_meta_grid(self):
        vbox = Gtk.Grid()
        vbox.set_orientation(Gtk.Orientation.VERTICAL)
        vbox.set_column_spacing(PADDING)
        vbox.set_border_width(PADDING)
        grid = Gtk.Grid()
        grid.set_row_spacing(PADDING)
        grid.set_column_spacing(PADDING)
        grid.set_border_width(PADDING)
        (bib_frame, bib_rows) = self._build_biblio_frame()
        (grot_frame, grot_rows) = self._build_grotesque_frame()
        (ifdb_frame, ifdb_rows) = self._build_ifdb_frame()
        grid.attach(bib_frame, 0, 0, 25, bib_rows)
        grid.attach(grot_frame, 25, 0, 1, grot_rows)
        grid.attach(ifdb_frame, 25, grot_rows, 1, ifdb_rows)
        ifdb_fetch_button = Gtk.Button()
        ifdb_fetch_button.set_label("Fetch from IFDB")
        ifdb_fetch_button.connect("clicked", self._on_ifdb_fetch)
        play_button = Gtk.Button()
        play_button.set_label("Launch story")
        play_button.connect("clicked", self._on_launch_story_clicked)
        grid.show_all()
        grid.set_vexpand(True)
        grid.set_hexpand(True)
        vbox.add(grid)
        button_box = Gtk.ButtonBox(Gtk.Orientation.HORIZONTAL)
        button_box.set_layout(Gtk.ButtonBoxStyle.START)
        button_box.set_spacing(PADDING)
        button_box.pack_start(play_button, False, False, PADDING)
        button_box.pack_start(ifdb_fetch_button, False, False, PADDING)
        vbox.add(button_box)
        vbox.show_all()
        return vbox

    def _match_partial_string(self, completion, key, tree_iter, sep, column):
        if sep:
            key = key.split(sep)[-1]
        model = completion.get_model()
        val = model.get_value(tree_iter, column)
        if val is None:
            return False
        return key in val.lower() and val != "(All)"

    def _on_list_completion(self, completion, model, tree_iter, entry, sep):
        text = entry.get_text()
        if not text:
            return False
        val = model.get_value(tree_iter, 0)
        if sep in text:
            text_base = text.rpartition(sep)[0]
            entry.set_text(sep.join([text_base, val]))
        else:
            entry.set_text(val)
        entry.set_position(-1)
        return True

    def _build_biblio_frame(self):
        field_labels = ["Title", "Author", "Group", "Headline",
                        "First published", "Language", "Genre", "Series",
                        "Series number", "Forgiveness", "Description",
                        "URL", "Tags"]
        field_cols = {"Title": 1, "Author": 0, "Group": 0, "Language":
                      0, "Genre": 0, "Series": 0, "Tags": 0}
        field_models = {
            'Title': self.library.list_store,
            'Author': self.library.author_store,
            'Year': self.library.year_store,
            'Genre': self.library.genre_store,
            'Group': self.library.group_store,
            'Series': self.library.series_store,
            'Language': self.library.lang_store,
            'Tags': self.library.tag_store}
        cur_row = 0
        frame = Gtk.Frame()
        frame.set_label("Bibliographic")
        sub_grid = Gtk.Grid()
        sub_grid.set_border_width(PADDING)
        sub_grid.set_row_spacing(PADDING/2)
        sub_grid.set_row_homogeneous(False)
        frame.add(sub_grid)
        for field in field_labels:
            field_key = field.lower().replace(" ", "")
            field_label = Gtk.Label(label="{0}: ".format(field))
            field_label.set_alignment(0, 0.5)
            if field == "Description":
                field_buffer = Gtk.TextBuffer()
                field_buffer.connect("changed", self._on_edit_biblio,
                                     field_key)
                field_view = Gtk.TextView(buffer=field_buffer)
                field_view.connect("focus-out-event",
                                   self._on_biblio_widget_changed,
                                   field_key)
                field_view.set_wrap_mode(Gtk.WrapMode.WORD)
                field_view.show()
                scroll = Gtk.ScrolledWindow()
                scroll.set_policy(Gtk.PolicyType.AUTOMATIC,
                                  Gtk.PolicyType.AUTOMATIC)
                scroll.add(field_view)
                scroll.set_property("expand", True)
                sub_grid.attach(field_label, 0, cur_row, 1, 1)
                sub_grid.attach(scroll, 1, cur_row, 1, 10)
                self._meta_fields[field_key] = field_buffer
                cur_row += 10
            elif field == "Forgiveness":
                field_combo = Gtk.ComboBoxText.new()
                field_combo.connect("changed", self._on_biblio_widget_changed,
                                    None, field_key)
                for forgive in self.forgiveness:
                    field_combo.append_text(forgive)
                sub_grid.attach(field_label, 0, cur_row, 1, 1)
                sub_grid.attach(field_combo, 1, cur_row, 1, 1)
                field_combo.set_property("expand", True)
                self._meta_fields[field_key] = field_combo
                cur_row += 1
            else:
                field_entry = Gtk.Entry()
                field_entry_buf = field_entry.get_buffer()
                field_entry_buf.connect("inserted-text",
                                        self._on_biblio_entry_insert,
                                        field_key)
                field_entry_buf.connect("deleted-text",
                                        self._on_biblio_entry_delete,
                                        field_key)
                field_entry.connect("focus-out-event",
                                    self._on_biblio_widget_changed,
                                    field_key)
                if field in field_cols:
                    field_complete = Gtk.EntryCompletion()
                    field_complete.set_inline_completion(False)
                    field_complete.set_popup_single_match(True)
                    field_complete.set_model(field_models[field])
                    if field == "Title":
                        field_complete.set_text_column(1)
                    else:
                        field_complete.set_text_column(0)
                    if field in ["Genre", "Tags"]:
                        sep = "/"
                        field_complete.connect("match-selected",
                                               self._on_list_completion,
                                               field_entry, sep)
                        field_entry.set_tooltip_text(
                            ''.join(['Separate multiple items with "/" ',
                                    '(e.g. "fantasy/cave-crawl")']))
                    elif field == "Author":
                        sep = ", "
                        field_complete.connect("match-selected",
                                               self._on_list_completion,
                                               field_entry, sep)
                        field_entry.set_tooltip_text(
                            ''.join(['Separate multiple authors with ", " ',
                                    '(e.g. "Dave Lebling, Marc Blank")']))
                    else:
                        sep = None
                    field_complete.set_match_func(self._match_partial_string,
                                                  sep, field_cols[field])
                    field_entry.set_completion(field_complete)
                sub_grid.attach(field_label, 0, cur_row, 1, 1)
                sub_grid.attach(field_entry, 1, cur_row, 1, 1)
                field_entry.set_property("expand", True)
                self._meta_fields[field_key] = field_entry
                cur_row += 1
        return (frame, cur_row+1)

    def _build_grotesque_frame(self):
        frame = Gtk.Frame()
        frame.set_label("General")
        sub_grid = Gtk.Grid()
        sub_grid.set_border_width(PADDING)
        sub_grid.set_row_spacing(PADDING/2)
        frame.add(sub_grid)
        frame.show_all()
        imported_label = Gtk.Label()
        imported_label.set_text("Date imported: ")
        imported_label.set_alignment(0, 0.5)
        imported_date_label = Gtk.Label()
        sub_grid.attach(imported_label, 0, 0, 1, 1)
        sub_grid.attach(imported_date_label, 1, 0, 1, 1)
        self._meta_fields["imported"] = imported_date_label
        played_label = Gtk.Label()
        played_label.set_text("Played: ")
        played_label.set_alignment(0, 0.5)
        played_toggle = Gtk.CheckButton()
        played_toggle.connect("toggled", self._on_biblio_widget_changed,
                              None, "played")
        sub_grid.attach(played_label, 0, 1, 1, 1)
        sub_grid.attach(played_toggle, 1, 1, 1, 1)
        self._meta_fields["played"] = played_toggle
        rating_label = Gtk.Label()
        rating_label.set_text("Rating: ")
        rating_label.set_alignment(0, 0.5)
        rating_combo = Gtk.ComboBoxText()
        for rating in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0,
                       3.5, 4.0, 4.5, 5.0]:
            rating_txt = util.render_star_rating(rating)
            rating_combo.append_text(rating_txt)
        rating_combo.connect("changed", self._on_biblio_widget_changed,
                             None, "rating")
        sub_grid.attach(rating_label, 0, 2, 1, 1)
        sub_grid.attach(rating_combo, 1, 2, 1, 1)
        self._meta_fields["rating"] = rating_combo
        return (frame, 3)

    def _build_ifdb_frame(self):
        frame = Gtk.Frame()
        frame.set_label("IFDB")
        sub_grid = Gtk.Grid()
        sub_grid.set_border_width(PADDING)
        frame.add(sub_grid)
        frame.show_all()
        fields = ["TUID", "IFDB URL", "Cover art URL", "Average rating",
                  "Star rating", "Rating count (average)",
                  "Rating count (total)", "Last updated"]
        for n, field in enumerate(fields):
            field_label = Gtk.Label()
            field_label.set_text("{0}: ".format(field))
            field_label.set_alignment(0, 0.5)
            field_data_label = Gtk.Label()
            field_data_label.set_alignment(0, 0.5)
            field_data_label.set_selectable(True)
            if "URL" in field:
                field_data_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
                field_data_label.set_max_width_chars(10)
                field_data_label.set_track_visited_links(False)
            sub_grid.attach(field_label, 0, n, 1, 1)
            sub_grid.attach(field_data_label, 1, n, 1, 1)
            field_key = field.lower().replace(" ", "")
            field_key = field_key.replace("(", "").replace(")", "")
            self._meta_fields[field_key] = field_data_label
        refresh_button = Gtk.Button.new_from_icon_name(
            "view-refresh", Gtk.IconSize.BUTTON)
        refresh_button.connect("clicked", self._on_ifdb_refresh)
        sub_grid.attach(refresh_button, 2, n, 1, 1)
        return (frame, len(fields))

    def _build_release_list(self):
        # Columns: 0: Default, 1: IFID, 2: format, 3: URI, 4: Version,
        # 5: Release date, 6: Compiler 7: Compiler version, 8: Comment
        vbox = Gtk.Grid()
        vbox.set_orientation(Gtk.Orientation.VERTICAL)
        vbox.set_row_spacing(PADDING)
        vbox.set_border_width(PADDING)
        self.release_store = Gtk.ListStore(
            bool, str, str, str, str, str, str, str, str)
        self.release_view = Gtk.TreeView(self.release_store)
        default_col_renderer = Gtk.CellRendererToggle()
        default_col_renderer.set_property("radio", True)
        default_col_renderer.set_activatable(True)
        default_col_renderer.connect(
            "toggled", self._on_release_default_toggled)
        default_col = Gtk.TreeViewColumn(
            "Default", default_col_renderer, active=0)
        default_col.set_resizable(False)
        default_col.set_reorderable(False)
        self.release_view.append_column(default_col)
        col_names = ["IFID", "Format", "File", "Version", "Release Date",
                     "Compiler", "Compiler Version", "Comment"]
        for n, col_name in enumerate(col_names):
            col_renderer = Gtk.CellRendererText()
            if col_name in ["File", "IFID"]:
                col_renderer.set_property(
                    "ellipsize", Pango.EllipsizeMode.MIDDLE)
                col_renderer.set_property(
                    "width-chars", 25)
            if col_name not in ["IFID", "Format", "File"]:
                col_renderer.set_property("editable", True)
                col_renderer.set_property("placeholder-text",
                                          "Edit...")
                col_renderer.connect("edited", self._on_release_info_edited,
                                     col_name)
            col = Gtk.TreeViewColumn(
                col_name, col_renderer, text=n+1)
            col.set_resizable(True)
            col.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            col.set_reorderable(True)
            self.release_view.append_column(col)
        button_box = Gtk.ButtonBox(Gtk.Orientation.HORIZONTAL)
        button_box.set_layout(Gtk.ButtonBoxStyle.START)
        button_box.set_spacing(PADDING)
        add_button = Gtk.Button()
        add_button.set_label("Add...")
        add_button.connect("clicked", self._on_add_release)
        rem_button = Gtk.Button()
        rem_button.set_label("Remove")
        rem_button.connect("clicked", self._on_remove_release)
        play_button = Gtk.Button()
        play_button.set_label("Launch release")
        play_button.connect("clicked", self._on_launch_release_clicked)
        button_box.pack_start(add_button, False, False, PADDING)
        button_box.pack_start(rem_button, False, False, PADDING)
        button_box.pack_start(play_button, False, False, PADDING)
        self.release_view.set_vexpand(True)
        self.release_view.set_hexpand(True)
        vbox.add(self.release_view)
        vbox.add(button_box)
        vbox.show_all()
        return vbox

    def _build_resource_list(self):
        # Columns: 0: URI, 1: description
        vbox = Gtk.Grid()
        vbox.set_orientation(Gtk.Orientation.VERTICAL)
        vbox.set_row_spacing(PADDING)
        vbox.set_border_width(PADDING)
        self.resource_store = Gtk.ListStore(str, str)
        self.resource_view = Gtk.TreeView(self.resource_store)
        col_names = ["URI", "Description"]
        for n, col_name in enumerate(col_names):
            col_renderer = Gtk.CellRendererText()
            col_renderer.set_property(
                "ellipsize", Pango.EllipsizeMode.MIDDLE)
            col_renderer.set_property(
                    "width-chars", 25)
            if col_name == "Description":
                col_renderer.set_property("editable", True)
                col_renderer.set_property("placeholder-text",
                                          "Edit...")
                col_renderer.connect("edited", self._on_resource_info_edited,
                                     col_name)
            col = Gtk.TreeViewColumn(
                col_name, col_renderer, text=n)
            col.set_resizable(True)
            col.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            col.set_reorderable(True)
            self.resource_view.append_column(col)
        button_box = Gtk.ButtonBox(Gtk.Orientation.HORIZONTAL)
        button_box.set_layout(Gtk.ButtonBoxStyle.START)
        button_box.set_spacing(PADDING)
        add_button = Gtk.Button()
        add_button.set_label("Add...")
        add_button.connect("clicked", self._on_add_resource)
        rem_button = Gtk.Button()
        rem_button.set_label("Remove")
        rem_button.connect("clicked", self._on_remove_resource)
        open_button = Gtk.Button()
        open_button.set_label("Open")
        open_button.connect("clicked", self._on_open_resource_clicked)
        button_box.pack_start(add_button, False, False, PADDING)
        button_box.pack_start(rem_button, False, False, PADDING)
        button_box.pack_start(open_button, False, False, PADDING)
        self.resource_view.set_vexpand(True)
        self.resource_view.set_hexpand(True)
        vbox.add(self.resource_view)
        vbox.add(button_box)
        vbox.show_all()
        return vbox

    def _build_cover_view(self):
        vbox = Gtk.Grid()
        vbox.set_orientation(Gtk.Orientation.VERTICAL)
        vbox.set_row_spacing(PADDING)
        vbox.set_border_width(PADDING)
        grid = Gtk.Grid()
        grid.set_row_spacing(PADDING)
        grid.set_column_spacing(PADDING)
        grid.set_border_width(PADDING)
        image_frame = Gtk.Frame()
        image_frame.set_label("Cover Image")
        image = Gtk.Image()
        image.set_padding(PADDING, PADDING)
        image.set_size_request(MAX_IMG_SIZE, MAX_IMG_SIZE)
        self._cover_widgets["image"] = image
        image_frame.add(image)
        grid.attach(image_frame, 0, 0, 23, 23)
        info_frame = Gtk.Frame()
        info_frame.set_label("Image Information")
        subgrid = Gtk.Grid()
        subgrid.set_row_spacing(PADDING)
        subgrid.set_column_spacing(PADDING)
        subgrid.set_border_width(PADDING)
        format_label = Gtk.Label()
        format_label.set_text("Format: ")
        format_label.set_alignment(0, 0.5)
        subgrid.attach(format_label, 0, 0, 1, 1)
        format_text = Gtk.Label()
        format_text.set_alignment(0, 0.5)
        subgrid.attach(format_text, 1, 0, 1, 1)
        self._cover_widgets["format"] = format_text
        dim_label = Gtk.Label()
        dim_label.set_text("Dimensions: ")
        dim_label.set_alignment(0, 0.5)
        subgrid.attach(dim_label, 0, 1, 1, 1)
        dim_text = Gtk.Label()
        dim_text.set_alignment(0, 0.5)
        self._cover_widgets["dimensions"] = dim_text
        subgrid.attach(dim_text, 1, 1, 1, 1)
        desc_label = Gtk.Label()
        desc_label.set_text("Description: ")
        desc_label.set_alignment(0, 0.5)
        subgrid.attach(desc_label, 0, 2, 1, 1)
        desc_entry = Gtk.Entry()
        desc_entry.set_property("expand", True)
        self._cover_widgets["description"] = desc_entry
        subgrid.attach(desc_entry, 1, 2, 1, 1)
        info_frame.add(subgrid)
        grid.attach(info_frame, 23, 0, 2, 3)
        grid.show_all()
        grid.set_hexpand(True)
        grid.set_vexpand(True)
        vbox.add(grid)
        import_button = Gtk.Button()
        import_button.set_label("Import...")
        import_button.connect("clicked", self._on_import_cover)
        remove_button = Gtk.Button()
        remove_button.set_label("Remove")
        remove_button.connect("clicked", self._on_remove_cover)
        button_box = Gtk.ButtonBox(Gtk.Orientation.HORIZONTAL)
        button_box.set_spacing(PADDING)
        button_box.set_layout(Gtk.ButtonBoxStyle.START)
        button_box.pack_start(import_button, False, False, PADDING)
        button_box.pack_start(remove_button, False, False, PADDING)
        vbox.add(button_box)
        return vbox

    def _refresh_coverart(self):
        cover_row = db.query.select_cover_by_story(self.conn, self.story_id)
        if not cover_row or cover_row["format"] not in ["jpeg", "png", "gif"]:
            self._cover_widgets["image"].clear()
            return
        self._cover_widgets["format"].set_text(cover_row["format"])
        self._cover_widgets["dimensions"].set_text(
            "{0}x{1} (pixels)".format(cover_row["width"], cover_row["height"]))
        if cover_row["description"] is not None:
            self._cover_widgets["description"].set_text(
                cover_row["description"])
        else:
            self._cover_widgets["description"].set_text("")
        self._cover_widgets["image"].clear()
        pixbuf_loader = GdkPixbuf.PixbufLoader.new_with_type(
            cover_row["format"])
        pixbuf_loader.write(cover_row["data"])
        pixbuf_loader.close()
        pixbuf = pixbuf_loader.get_pixbuf()
        pixbuf_w = pixbuf.get_width()
        pixbuf_h = pixbuf.get_height()
        ratio = float(pixbuf_h) / float(pixbuf_w)
        # If the image is bigger than the frame in either dimension, it
        # should be scaled to fit.
        if pixbuf_w > MAX_IMG_SIZE or pixbuf_h > MAX_IMG_SIZE:
            if pixbuf_w == pixbuf_h:
                new_width = MAX_IMG_SIZE
                new_height = MAX_IMG_SIZE
            elif pixbuf_w > pixbuf_h:
                new_width = MAX_IMG_SIZE
                new_height = int(ratio * new_width)
            else:
                new_height = MAX_IMG_SIZE
                new_width = int(1 / ratio * new_height)
            scaled_buf = pixbuf.scale_simple(new_width, new_height,
                                             GdkPixbuf.InterpType.TILES)
            self._cover_widgets["image"].set_from_pixbuf(scaled_buf)
        else:
            self._cover_widgets["image"].set_from_pixbuf(pixbuf)

    def _maybe_set(self, field, text):
        if text == self._meta_fields[field]:
            return
        if text is None:
            self._meta_fields[field].set_text("")
            return
        if field != "firstpublished":
            try:
                self._meta_fields[field].set_text(text)
            except:
                self._meta_fields[field].set_text(str(text))
            return
        try:
            pub_date = util.normalize_date(str(text))
        except:
            self._meta_fields[field].set_text("")
        else:
            self._meta_fields[field].set_text(pub_date)

    def _fill_ifdb_annotation(self, ific_story):
        annotation = ifiction.get_annotation(ific_story)
        if annotation is None or "ifdb" not in annotation:
            for field in ["tuid", "ifdburl", "coverarturl", "averagerating",
                          "starrating", "ratingcountaverage",
                          "ratingcounttotal", "lastupdated"]:
                self._meta_fields[field].set_text("")
            return
        ifdb_annot = annotation["ifdb"]
        self._maybe_set("tuid", ifdb_annot.get("tuid"))
        if "link" in ifdb_annot:
            self._meta_fields["ifdburl"].set_markup(
                "<a href=\"{0}\">{0}</a>".format(ifdb_annot["link"]))
        else:
            self._meta_fields["ifdburl"].set_text("")
        if "coverart" in ifdb_annot and "url" in ifdb_annot["coverart"]:
            cover_url = ifdb_annot["coverart"]["url"]
            cover_url = cover_url.replace("&", "&amp;")
            self._meta_fields["coverarturl"].set_markup(
                "<a href=\"{0}\">{0}</a>".format(cover_url))
        else:
            cover_url = None
            self._meta_fields["coverarturl"].set_markup("")
        self._maybe_set("averagerating", ifdb_annot.get("averagerating"))
        if "starrating" in ifdb_annot:
            star_rating_txt = util.render_star_rating(
                float(ifdb_annot["starrating"]))
        else:
            star_rating_txt = ""
        self._meta_fields["starrating"].set_text(star_rating_txt)
        self._maybe_set("ratingcountaverage",
                        str(ifdb_annot.get("ratingcountavg")))
        self._maybe_set("ratingcounttotal",  ifdb_annot.get("ratingcounttot"))
        last_updated = str(datetime.date.today())
        self._meta_fields["lastupdated"].set_text(last_updated)
        ifdb_row = {"tuid": ifdb_annot.get("tuid"),
                    "url": ifdb_annot.get("link"),
                    "cover_url": cover_url,
                    "avg_rating": ifdb_annot.get("averagerating"),
                    "star_rating": ifdb_annot.get("starrating"),
                    "star_rating_txt": star_rating_txt,
                    "rating_count_avg": ifdb_annot.get("ratingcountavg"),
                    "rating_count_tot": ifdb_annot.get("ratingcounttot"),
                    "updated": last_updated}
        annot_row = db.query.select_ifdb_annotation_by_story(
            self.conn, self.story_id)
        if annot_row:
            annot_id = annot_row["id"]
            db.query.update_ifdb_annotation(self.conn, annot_id, ifdb_row)
        else:
            db.query.insert_ifdb_annotation(self.conn, self.story_id, **ifdb_row)


    def _fill_metadata_from_ifdb(self, tuid=None, ifid=None):
        if tuid is None and ifid is None:
            return
        if tuid is not None:
            ific_story = ifdb.fetch_ifiction(tuid=tuid)
        else:
            ific_story = ifdb.fetch_ifiction(ifid=ifid)
        if ific_story is None:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.OK)
            d.set_markup("No record found on IFDB")
            d.run()
            d.destroy()
            return
        biblio = ifiction.get_bibliographic(ific_story)
        new_title = biblio.get("title")
        story_row = db.query.select_story_by_title(self.conn, new_title, True)
        title_exists = story_row and story_row["id"] != self.story_id
        if title_exists:
            merged = self._show_merge_story_dialog(
                new_title, story_row["id"])
            if merged:
                self.widget_update = False
                self.merged = True
                return
            else:
                n = 2
                while db.query.select_story_by_title(
                        self.conn, new_title + " [{0}]".format(n)):
                    n += 1
                new_title = new_title + " [{0}]".format(n)
        self._maybe_set("title", new_title)
        self._edit_generic(new_title, "title")
        self._maybe_set("author", biblio.get("author"))
        self._edit_author(biblio.get("author"))
        self._maybe_set("group", biblio.get("group"))
        self._edit_group(biblio.get("group"))
        self._maybe_set("headline", biblio.get("headline"))
        self._edit_generic(biblio.get("headline"), "headline")
        self._maybe_set("firstpublished", biblio.get("firstpublished"))
        try:
            pub_date = util.normalize_date(biblio.get("firstpublished"))
        except:
            pass
        else:
            self._edit_generic(pub_date, "firstpublished")
        self._maybe_set("language", biblio.get("language"))
        self._edit_generic(biblio.get("language"), "language")
        self._maybe_set("genre", biblio.get("genre"))
        self._edit_genre(biblio.get("genre"))
        self._maybe_set("series", biblio.get("series"))
        self._edit_series(biblio.get("series"))
        self._maybe_set("seriesnumber", biblio.get("seriesnumber"))
        self._edit_seriesnumber(biblio.get("seriesnumber"))
        if "forgiveness" in biblio and biblio["forgiveness"] is not None:
            try:
                self._meta_fields["forgiveness"].set_active(
                    self.forgiveness.index(biblio["forgiveness"]))
            except:
                self._meta_fields["forgiveness"].set_active(
                    self.forgiveness.index("Unknown"))
        else:
            self._meta_fields["forgiveness"].set_active(
                self.forgiveness.index("Unknown"))
        self._edit_forgiveness(biblio.get("forgiveness"))
        self._maybe_set("description", biblio.get("description"))
        self._edit_generic(biblio.get("description"), "description")
        # IFDB stores story URLs in the contact section
        contact = ifiction.get_contact(ific_story)
        if contact is not None:
            self._maybe_set("url", contact.get("url"))
            self._edit_generic(contact.get("url"), "url")
        else:
            self._meta_fields["url"].set_text("")
            self._edit_generic("", "url")
        self._fill_ifdb_annotation(ific_story)
        self.edited = True

    def _fill_metadata_from_db(self):
        story = db.query.select_story(self.conn, self.story_id)
        if not story:
            return
        self._maybe_set("title", story["title"])
        author_ids = db.query.select_story_authors(self.conn, self.story_id)
        if author_ids:
            authors_list = [db.query.select_author(self.conn, author_id[0])["name"]
                            for author_id in author_ids]
            authors = ", ".join(authors_list)
        else:
            authors = ""
        self._meta_fields["author"].set_text(authors)
        self._maybe_set("description", story["description"])
        group = db.query.select_group(self.conn, story["group_id"])
        if group:
            self._maybe_set("group", group["name"])
        else:
            self._meta_fields["group"].set_text("")
        self._maybe_set("headline", story["headline"])
        self._maybe_set("firstpublished", story["firstpublished"])
        self._maybe_set("language", story["language"])
        genre_ids = db.query.select_story_genres(self.conn, self.story_id)
        if genre_ids:
            genres_list = [db.query.select_genre(self.conn, genre_id[0])["name"] for
                           genre_id in genre_ids]
            genres = "/".join(genres_list)
        else:
            genres = ""
        self._meta_fields["genre"].set_text(genres)
        series = db.query.select_series(self.conn, story["series_id"])
        if series:
            self._maybe_set("series", series["name"])
        else:
            self._meta_fields["series"].set_text("")
        self._maybe_set("seriesnumber", story["seriesnumber"])
        forgiveness = db.query.select_forgiveness(self.conn, story["forgiveness_id"])
        if forgiveness:
            self._meta_fields["forgiveness"].set_active(forgiveness["id"]-1)
        else:
            self._meta_fields["forgiveness"].set_active(0)
        self._maybe_set("url", story["url"])
        tag_ids = db.query.select_story_tags(self.conn, self.story_id)
        if tag_ids:
            tags_list = [db.query.select_tag(self.conn, tag_id[0])["name"] for
                           tag_id in tag_ids]
            tags = "/".join(tags_list)
        else:
            tags = ""
        self._meta_fields["tags"].set_text(tags)
        annotation = db.query.select_annotation_by_story(self.conn, self.story_id)
        if annotation:
            date_added = annotation["imported"]
            self._meta_fields["imported"].set_text(str(date_added))
            rating = annotation["rating"]
            if rating is None:
                rating = 0.0
            self._meta_fields["rating"].set_active(int(rating*2))
            played = annotation["played"]
            self._meta_fields["played"].set_active(played)
        else:
            self._meta_fields["imported"].set_text("")
            self._meta_fields["rating"].set_active(0)
            self._meta_fields["played"].set_active(False)
        ifdb_annot = db.query.select_ifdb_annotation_by_story(
            self.conn, self.story_id)
        if ifdb_annot:
            self._meta_fields["tuid"].set_text(ifdb_annot["tuid"])
            self._meta_fields["ifdburl"].set_markup(
                "<a href=\"{0}\">{0}</a>".format(ifdb_annot["url"]))
            if ifdb_annot["cover_url"] is not None:
                cover_url = ifdb_annot["cover_url"].replace("&", "&amp;")
                self._meta_fields["coverarturl"].set_markup(
                    "<a href=\"{0}\">{0}</a>".format(cover_url))
            self._meta_fields["averagerating"].set_text(
                str(ifdb_annot["avg_rating"]))
            self._meta_fields["starrating"].set_text(
                ifdb_annot["star_rating_txt"])
            self._meta_fields["ratingcountaverage"].set_text(
                str(ifdb_annot["rating_count_avg"]))
            self._meta_fields["ratingcounttotal"].set_text(
                str(ifdb_annot["rating_count_tot"]))
            self._meta_fields["lastupdated"].set_text(
                str(ifdb_annot["updated"]))
        else:
            for field in ["tuid", "ifdburl", "coverarturl", "averagerating",
                          "starrating", "ratingcountaverage",
                          "ratingcounttotal", "lastupdated"]:
                self._meta_fields[field].set_text("")

    def _fill_releases(self):
        self.release_store.clear()
        if self.story_id is None:
            return
        story = db.query.select_story(self.conn, self.story_id)
        releases = db.query.select_releases_by_story(self.conn, self.story_id)
        for release in releases:
            default = (story["default_release"] == release["ifid"])
            if not release["uri"]:
                continue
            if release["release_date"] is not None:
                release_date = str(release["release_date"])
            else:
                release_date = ""
            ifformat = db.query.select_format(self.conn, release["format_id"])
            if release["version"] is None:
                version = ""
            else:
                version = str(release["version"])
            if release["compiler_version"] is None:
                compiler_version = ""
            else:
                compiler_version = str(release["compiler_version"])
            if release["comment"] is None:
                comment = ""
            else:
                comment = release["comment"]
            self.release_store.append(
                [default, release["ifid"], ifformat["name"], release["uri"],
                 version, release_date, release["compiler"], compiler_version,
                 comment])

    def _fill_resources(self):
        self.resource_store.clear()
        if self.story_id is None:
            return
        story = db.query.select_story(self.conn, self.story_id)
        resources = db.query.select_resources_by_story(self.conn, self.story_id)
        for resource in resources:
            if not resource["uri"]:
                continue
            if resource["description"] is None:
                description = ""
            else:
                description = resource["description"]
            self.resource_store.append(
                [resource["uri"], description])

    def load_story(self, story_id):
        if story_id is None:
            return
        self.init_complete = False
        self.story_id = story_id
        self._fill_metadata_from_db()
        self._fill_releases()
        self._fill_resources()
        self._refresh_coverart()
        self.edited = False
        self.merged = False
        self.notebook.set_current_page(0)
        self.init_complete = True

    def _edit_forgiveness(self, forgive_txt):
        if not forgive_txt:
            forgive_txt = "Unknown"
        forgive_row = db.query.select_forgiveness_by_description(
            self.conn, forgive_txt)
        if forgive_row:
            db.query.update_story(self.conn, self.story_id,
                            {"forgiveness_id": forgive_row["id"]})

    def _edit_author(self, author_txt):
        authors = util.parse_list_str(author_txt)
        old_authors = set([row["id"] for row in db.query.select_story_authors(
            self.conn, self.story_id)])
        new_authors = set()
        for author in authors:
            # Only add the author's real name to the filter (no pen names).
            author_real_name = author.split('(')[0]
            if author_real_name == '':
                continue
            author_row = db.query.select_author_by_name(
                self.conn, author_real_name)
            if not author_row:
                author_id = db.query.insert_author(self.conn, author_real_name)
            else:
                author_id = author_row["id"]
                if author_id in old_authors:
                    new_authors.add(author_id)
                    continue
            db.query.add_author_to_story(self.conn, author_id, self.story_id)
            new_authors.add(author_id)
        for old_author in old_authors.difference(new_authors):
            db.query.remove_author_from_story(
                self.conn, old_author, self.story_id)
            if not db.query.select_author_stories(self.conn, old_author):
                db.query.delete_author(self.conn, old_author)

    def _edit_group(self, group_txt):
        if not group_txt:
            group_id = None
        else:
            group_row = db.query.select_group_by_name(self.conn, group_txt)
            if not group_row:
                group_id = db.query.insert_group(self.conn, group_txt)
            else:
                group_id = group_row["id"]
        db.query.update_story(self.conn, self.story_id,
                        {"group_id": group_id})

    def _edit_genre(self, genre_txt):
        genres = util.parse_list_str(genre_txt)
        old_genres = set([row["id"] for row in db.query.select_story_genres(
            self.conn, self.story_id)])
        new_genres = set()
        for genre in genres:
            if not genre:
                continue
            genre_row = db.query.select_genre_by_name(self.conn, genre.lower())
            if not genre_row:
                genre_id = db.query.insert_genre(self.conn, genre.lower())
            else:
                genre_id = genre_row["id"]
                if genre_id in old_genres:
                    new_genres.add(genre_id)
                    continue
            db.query.add_genre_to_story(self.conn, genre_id, self.story_id)
            new_genres.add(genre_id)
        for old_genre in old_genres.difference(new_genres):
            db.query.remove_genre_from_story(
                self.conn, old_genre, self.story_id)
            if not db.query.select_genre_stories(self.conn, old_genre):
                db.query.delete_genre(self.conn, old_genre)

    def _edit_tags(self, tag_txt):
        tags = util.parse_list_str(tag_txt)
        old_tags = set([row["id"] for row in db.query.select_story_tags(
            self.conn, self.story_id)])
        new_tags = set()
        for tag in tags:
            if not tag:
                continue
            tag_row = db.query.select_tag_by_name(self.conn, tag.lower())
            if not tag_row:
                tag_id = db.query.insert_tag(self.conn, tag.lower())
            else:
                tag_id = tag_row["id"]
                if tag_id in old_tags:
                    new_tags.add(tag_id)
                    continue
            db.query.add_tag_to_story(self.conn, tag_id, self.story_id)
            new_tags.add(tag_id)
        for old_tag in old_tags.difference(new_tags):
            db.query.remove_tag_from_story(
                self.conn, old_tag, self.story_id)
            if not db.query.select_tag_stories(self.conn, old_tag):
                db.query.delete_tag(self.conn, old_tag)

    def _edit_series(self, series_txt):
        if not series_txt:
            series_id = None
        else:
            series_row = db.query.select_series_by_name(self.conn, series_txt)
            if not series_row:
                series_id = db.query.insert_series(self.conn, series_txt)
            else:
                series_id = series_row["id"]
        db.query.update_story(self.conn, self.story_id,
                        {"series_id": series_id})

    def _edit_seriesnumber(self, seriesnumber):
        if not seriesnumber:
            seriesnumber = None
        db.query.update_story(self.conn, self.story_id,
                        {"seriesnumber": seriesnumber})

    def _edit_generic(self, new_txt, field):
        db.query.update_story(self.conn, self.story_id,
                        {field: new_txt})

    def _edit_rating(self, rating_txt):
        if not rating_txt:
            rating_txt = ""
        rating = util.star_rating_to_float(rating_txt)
        annot_row = db.query.select_annotation_by_story(
            self.conn, self.story_id)
        if annot_row:
            db.query.update_annotation(self.conn, self.story_id,
                                 {"rating": rating,
                                  "rating_txt": rating_txt})

    def _edit_played(self, played):
        annot_row = db.query.select_annotation_by_story(
            self.conn, self.story_id)
        if annot_row:
            db.query.update_annotation(self.conn, self.story_id,
                                 {"played": played})

    def _on_edit_biblio(self, widget, field):
        self.widget_update = True

    def _on_biblio_widget_changed(self, widget, event, field):
        if not self.init_complete:
            self.widget_update = False
            return
        if field == "forgiveness":
            forgive_txt = widget.get_active_text()
            self._edit_forgiveness(forgive_txt)
            self.edited = True
            return
        elif field == "rating":
            rating_txt = widget.get_active_text().decode('utf-8')
            self._edit_rating(rating_txt)
            self.edited = True
            return
        elif field == "played":
            played = widget.get_active()
            self._edit_played(played)
            self.edited = True
            return
        if not self.widget_update:
            return
        if field == "author":
            author_txt = widget.get_text().decode('utf-8')
            self._edit_author(author_txt)
        elif field == "group":
            group_txt = widget.get_text().decode('utf-8')
            self._edit_group(group_txt)
        elif field == "genre":
            genre_txt = widget.get_text().decode('utf-8')
            self._edit_genre(genre_txt)
        elif field == "tags":
            tag_txt = widget.get_text().decode('utf-8')
            self._edit_tags(tag_txt)
        elif field == "series":
            series_txt = widget.get_text().decode('utf-8')
            self._edit_series(series_txt)
        elif field == "seriesnumber":
            seriesnumber = widget.get_text().decode('utf-8')
            self._edit_seriesnumber(seriesnumber)
        elif field == "description":
            txt_buffer = widget.get_buffer()
            start = txt_buffer.get_start_iter()
            end = txt_buffer.get_end_iter()
            new_txt = txt_buffer.get_text(start, end, True).decode('utf-8')
            self._edit_generic(new_txt, field)
        elif field == "title":
            txt_buffer = widget.get_buffer()
            new_title = txt_buffer.get_text().decode('utf-8')
            story_row = db.query.select_story_by_title(self.conn, new_title,
                                                       True)
            title_exists = story_row and story_row["id"] != self.story_id
            if title_exists:
                merged = self._show_merge_story_dialog(
                    new_title, story_row["id"])
                if merged:
                    self.widget_update = False
                    self.merged = True
                    return
                else:
                    n = 2
                    while db.query.select_story_by_title(
                            self.conn, new_title + " [{0}]".format(n)):
                        n += 1
                    new_title = new_title + " [{0}]".format(n)
                    txt_buffer.set_text(new_title, len(new_title))
            self._edit_generic(new_title, field)
        else:
            txt_buffer = widget.get_buffer()
            new_txt = txt_buffer.get_text().decode('utf-8')
            if field == "firstpublished":
                try:
                    new_txt = util.normalize_date(str(new_txt))
                except:
                    new_txt = ""
            self._edit_generic(new_txt, field)
        self.edited = True
        self.widget_update = False

    def _on_biblio_entry_insert(self, widget, position, chars, n_chars, field):
        self._on_edit_biblio(widget, field)

    def _on_biblio_entry_delete(self, widget, position, n_chars, field):
        self._on_edit_biblio(widget, field)

    def _on_launch_story_clicked(self, button):
        """The edit dialog has a play button on it, so the user can launch a
        file while editing it to help figure out some information. This method
        handles clicks on it.

        """
        db.launch_story(self.conn, self.settings, self.story_id)

    def _on_ifdb_refresh(self, button):
        ifdb_annot = db.query.select_ifdb_annotation_by_story(
            self.conn, self.story_id)
        if not ifdb_annot:
            return
        tuid = ifdb_annot["tuid"]
        if not tuid:
            return
        ific_story = ifdb.fetch_ifiction(tuid=tuid)
        self._fill_ifdb_annotation(ific_story)

    def _on_launch_release_clicked(self, button):
        selection = self.release_view.get_selection()
        if selection is None:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.OK)
            d.set_markup("No release selected")
            d.run()
            d.destroy()
            return
        (model, row) = selection.get_selected()
        if row is None:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.OK)
            d.set_markup("No release selected")
            d.run()
            d.destroy()
            return
        ifid = self.release_store.get_value(row, 1)
        db.launch_release(self.conn, self.settings, ifid)

    def _on_open_resource_clicked(self, button):
        selection = self.resource_view.get_selection()
        if selection is None:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.OK)
            d.set_markup("No resource selected")
            d.run()
            d.destroy()
            return
        (model, row) = selection.get_selected()
        if row is None:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.OK)
            d.set_markup("No resource selected")
            d.run()
            d.destroy()
            return
        uri = self.resource_store.get_value(row, 0)
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

    def _import_cover_data(self, cover_data):
        if not cover_data or cover_data == "No image is available":
            return
        img_format = _imgfuncs.deduce_img_format(cover_data)
        if img_format == "jpeg":
            width, height = _imgfuncs.get_jpeg_dim(cover_data)
        elif img_format == "png":
            width, height = _imgfuncs.get_png_dim(cover_data)
        elif img_format == "gif":
            width, height = _imgfuncs.get_gif_dim(cover_data)
        else:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.OK)
            d.set_markup("Unknown image format")
            d.run()
            d.destroy()
            return
        description = None
        orig_cover = db.query.select_cover_by_story(self.conn, self.story_id)
        if orig_cover is not None:
            db.query.update_cover(self.conn, orig_cover["id"],
                                  {"height": height,
                                   "width": width,
                                   "format": img_format,
                                   "description": description,
                                   "data": cover_data})
        else:
            db.query.insert_cover(self.conn, self.story_id, img_format, height,
                                  width, description, cover_data)
        self._refresh_coverart()

    def _import_cover_from_file(self, filename):
        if not os.path.exists(filename):
            return
        with open(filename, 'rb') as h:
            data = h.read()
        self._import_cover_data(data)

    def _import_cover_from_ifdb(self, tuid=None, ifid=None):
        if tuid is None and ifid is None:
            return
        if tuid is not None:
            data = ifdb.fetch_cover(tuid=tuid)
        else:
            data = ifdb.fetch_cover(ifid=ifid)
        self._import_cover_data(data)

    def _on_import_cover(self, button):
        file_chooser = Gtk.FileChooserDialog(
            "Select the cover art file", self,
            Gtk.FileChooserAction.OPEN,
            ("Cancel", Gtk.ResponseType.CANCEL,
             "Solect", Gtk.ResponseType.ACCEPT))
        file_chooser.set_select_multiple(False)
        response = file_chooser.run()
        file_chooser.hide()
        if response == Gtk.ResponseType.ACCEPT:
            filepaths = file_chooser.get_filenames()
            if len(filepaths) > 0:
                self._import_cover_from_file(filepaths[0])
        file_chooser.destroy()

    def _on_remove_cover(self, button):
        cover_id = db.query.select_cover_by_story(self.conn, self.story_id)
        if not cover_id:
            return
        db.query.delete_cover(self.conn, cover_id["id"])
        self._refresh_coverart()

    def _on_add_release(self, button):
        """Set a story's file location via a file finder dialog."""
        file_chooser = Gtk.FileChooserDialog(
            "Select the location of the story file", self,
            Gtk.FileChooserAction.OPEN,
            ("Cancel", Gtk.ResponseType.CANCEL, "Select",
             Gtk.ResponseType.ACCEPT))
        file_chooser.set_select_multiple(False)
        response = file_chooser.run()
        file_chooser.hide()
        if response == Gtk.ResponseType.ACCEPT:
            filepaths = file_chooser.get_filenames()
        else:
            return
        filepath = filepaths[0]
        file_chooser.destroy()
        try:
            story_format = treatyofbabel.deduce_format(filepath)
        except BabelError:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR, Gtk.ButtonsType.OK)
            d.set_markup("Unrecognized story format")
            d.run()
            d.destroy()
            return False
        if "blorbed" in story_format:
            raw_format = story_format.split()[1].strip()
        elif story_format.strip() == "executable":
            with open(filename) as h:
                buf = h.read()
            if is_win32_executable(buf):
                raw_format = "win32"
            else:
                raw_format = "dos"
        else:
            raw_format = story_format.strip()
        format_row = db.query.select_format_by_name(self.conn, raw_format)
        if not format_row:
            try:
                launcher = self.settings.get_launcher(raw_format)
            except:
                d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                      Gtk.MessageType.ERROR,
                                      Gtk.ButtonsType.OK)
                d.set_markup("Unrecognized story format")
                d.run()
                d.destroy()
            return False
            format_id = db.query.insert_format(self.conn, raw_format, launcher)
        else:
            format_id = format_row["id"]
        try:
            ifids = treatyofbabel.get_ifids(filepath)
        except:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.OK)
            d.set_markup("Could not deduce IFIDs for this file")
            d.run()
            d.destroy()
            return False
        if db.query.select_release(self.conn, ifids[0]) is not None:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.OK)
            d.set_markup("A release with this IFID is already in the database")
            d.run()
            d.destroy()
            return False
        db.query.insert_release(self.conn, ifids[0], self.story_id, filepath,
                                None, None, None, None, None, format_id)
        self.release_store.append([False, ifids[0], raw_format, filepath,
                                   None, None, None, None, None])

    def _on_remove_release(self, button):
        selection = self.release_view.get_selection()
        if selection is None:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.OK)
            d.set_markup("No release selected")
            d.run()
            d.destroy()
            return
        (model, row) = selection.get_selected()
        if row is None:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.OK)
            d.set_markup("No release selected")
            d.run()
            d.destroy()
            return
        ifid = self.release_store.get_value(row, 1)
        db.query.delete_release(self.conn, ifid)
        self.release_store.remove(row)

    def _on_release_info_edited(self, renderer, path, new_text, col_name):
        col_num = ["Version", "Release Date",
                     "Compiler", "Compiler Version", "Comment"].index(col_name)+4
        row_iter = self.release_store.get_iter(path)
        ifid = self.release_store.get_value(row_iter, 1)
        field = col_name.lower()
        if col_name == "Release Date":
            field = field.replace(" ", "_")
            try:
                new_text = util.normalize_date(str(new_text))
            except:
                return
        else:
            field = field.replace(" ", "")
        db.query.update_release(self.conn, ifid, {field: new_text})
        self.release_store.set_value(row_iter, col_num, new_text)
        self.edited = True

    def _on_add_resource(self, button):
        story_row = db.query.select_story(self.conn, self.story_id)
        if story_row is None:
            return
        default_rel = story_row["default_release"]
        default_rel_row = db.query.select_release(self.conn, default_rel)
        default_rel_uri = default_rel_row["uri"]
        default_rel_dir = os.path.dirname(default_rel_uri)
        file_chooser = Gtk.FileChooserDialog(
            "Select the location of the resource file", self,
            Gtk.FileChooserAction.OPEN,
            ("Cancel", Gtk.ResponseType.CANCEL, "Select",
             Gtk.ResponseType.ACCEPT))
        file_chooser.set_select_multiple(True)
        file_chooser.set_current_folder(default_rel_dir)
        response = file_chooser.run()
        file_chooser.hide()
        if response == Gtk.ResponseType.ACCEPT:
            filepaths = file_chooser.get_filenames()
        else:
            return
        file_chooser.destroy()
        for uri in filepaths:
            db.query.insert_resource(self.conn, self.story_id, uri)
            self.resource_store.append([uri, ""])

    def _on_remove_resource(self, button):
        selection = self.resource_view.get_selection()
        if selection is None:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.OK)
            d.set_markup("No resource selected")
            d.run()
            d.destroy()
            return
        (model, row) = selection.get_selected()
        if row is None:
            d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                  Gtk.MessageType.ERROR,
                                  Gtk.ButtonsType.OK)
            d.set_markup("No resource selected")
            d.run()
            d.destroy()
            return
        uri = self.resource_store.get_value(row, 0)
        resource_row = db.query.select_resource_by_uri(self.conn, uri)
        resource_id = resource_row["id"]
        db.query.delete_resource(self.conn, resource_id)
        self.resource_store.remove(row)

    def _on_resource_info_edited(self, renderer, path, new_text, col_name):
        col_num = ["URI", "Description"].index(col_name)
        row_iter = self.resource_store.get_iter(path)
        uri = self.resource_store.get_value(row_iter, 0)
        resource_row = db.query.select_resource_by_uri(self.conn, uri)
        resource_id = resource_row["id"]
        field = col_name.lower()
        db.query.update_resource(self.conn, resource_id, {field: new_text})
        self.resource_store.set_value(row_iter, col_num, new_text)
        self.edited = True

    def _on_ifdb_fetch(self, button):
        """The edit dialog has a search button on it. This method handles
        clicks on that button. It grabs the currently entered tuid and searches
        IFDB with it.

        """
        ifdb_dialog = Gtk.Dialog(
            "Story IFDB entry", self, Gtk.DialogFlags.MODAL,
            ("Cancel", Gtk.ResponseType.CANCEL,
             "OK", Gtk.ResponseType.ACCEPT))
        ifdb_dialog.connect("response", self._on_ifdb_dialog_accept)
        vbox = ifdb_dialog.get_child()
        vbox.set_spacing(PADDING/2)
        ifdb_dialog.stack = Gtk.Stack()
        ifdb_dialog.stack.set_homogeneous(True)
        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(ifdb_dialog.stack)
        stack_switcher.set_halign(Gtk.Align.CENTER)
        url_hbox = Gtk.Grid()
        url_hbox.set_orientation(Gtk.Orientation.HORIZONTAL)
        url_hbox.set_column_spacing(PADDING/2)
        url_label = Gtk.Label()
        url_label.set_text("URL: ")
        ifdb_dialog.url_entry = Gtk.Entry()
        ifdb_dialog.url_entry.set_property(
            "placeholder-text",
            "https://ifdb.tads.org/viewgame?id=XXXXXXXXXXXXXXXX")
        ifdb_dialog.url_entry.connect("activate", self._on_ifdb_dialog_activate,
                                      ifdb_dialog)
        url_hbox.add(url_label)
        ifdb_dialog.url_entry.set_hexpand(True)
        url_hbox.add(ifdb_dialog.url_entry)
        ifdb_dialog.stack.add_titled(url_hbox, "URL", "URL")
        ifdb_dialog.stack.set_visible_child(url_hbox)
        ifid_hbox = Gtk.Grid()
        ifid_hbox.set_orientation(Gtk.Orientation.HORIZONTAL)
        ifid_hbox.set_column_spacing(PADDING/2)
        ifid_label = Gtk.Label()
        ifid_label.set_text("IFID: ")
        ifdb_dialog.ifid_combo = Gtk.ComboBoxText.new_with_entry()
        release_rows = db.query.select_releases_by_story(self.conn, self.story_id)
        releases = [row["ifid"] for row in release_rows]
        for release in releases:
            ifdb_dialog.ifid_combo.append_text(release)
        ifdb_dialog.ifid_combo.set_hexpand(True)
        ifid_hbox.add(ifid_label)
        ifid_hbox.add(ifdb_dialog.ifid_combo)
        ifdb_dialog.stack.add_titled(ifid_hbox, "IFID", "IFID")
        ifdb_dialog.stack.show_all()
        stack_switcher.show_all()
        opt_hbox = Gtk.Grid()
        opt_hbox.set_orientation(Gtk.Orientation.HORIZONTAL)
        opt_hbox.set_column_spacing(PADDING/2)
        label2 = Gtk.Label()
        label2.set_text("Fetch cover: ")
        ifdb_dialog.toggle = Gtk.CheckButton()
        ifdb_dialog.toggle.set_active(True)
        opt_hbox.add(label2)
        opt_hbox.add(ifdb_dialog.toggle)
        vbox.add(stack_switcher)
        vbox.add(ifdb_dialog.stack)
        vbox.add(opt_hbox)
        vbox.show_all()
        ifdb_dialog.show()

    def _on_ifdb_dialog_activate(self, entry, ifdb_dialog):
        ifdb_dialog.emit("response", Gtk.ResponseType.OK)

    def _on_ifdb_dialog_accept(self, ifdb_dialog, response_id):
        if response_id == Gtk.ResponseType.CANCEL:
            ifdb_dialog.destroy()
            return
        fetch_cover = ifdb_dialog.toggle.get_active()
        if ifdb_dialog.stack.get_visible_child_name() == "URL":
            url = ifdb_dialog.url_entry.get_text().lower().strip()
            if ((not url or url.count("=") != 1 or
                 (not url.startswith("http://ifdb.tads.org/viewgame?id=") and
                  not url.startswith("https://ifdb.tads.org/viewgame?id=")))):
                d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                      Gtk.MessageType.ERROR,
                                      Gtk.ButtonsType.OK)
                d.set_markup("Invalid IFDB URL")
                d.run()
                d.destroy()
                ifdb_dialog.url_entry.set_text("")
            else:
                tuid = url.split("=")[1]
                self._fill_metadata_from_ifdb(tuid=tuid)
                if fetch_cover:
                    self._import_cover_from_ifdb(tuid=tuid)
        else:
            ifid = ifdb_dialog.ifid_combo.get_active_text()
            self._fill_metadata_from_ifdb(ifid=ifid)
            if fetch_cover:
                self._import_cover_from_ifdb(ifid=ifid)
        ifdb_dialog.destroy()

    def _on_release_default_toggled(self, renderer, path):
        row_iter = self.release_store.get_iter_first()
        new_ifid = None
        while row_iter is not None:
            row_path = self.release_store.get_path(row_iter)
            if row_path.to_string() == path:
                self.release_store[row_iter][0] = True
                new_ifid = self.release_store.get_value(row_iter, 1)
            else:
                self.release_store[row_iter][0] = False
            row_iter = self.release_store.iter_next(row_iter)
        if new_ifid is None:
            return
        db.query.update_story(self.conn, self.story_id,
                              {"default_release": new_ifid})

    def _merge_releases_with_story(self, merge_id):
        release_rows = db.query.select_releases_by_story(self.conn,
                                                         self.story_id)
        for release_row in release_rows:
            ifid = release_row["ifid"]
            db.query.update_release(self.conn, ifid, {"story_id": merge_id})

    def _merge_resources_with_story(self, merge_id):
        resource_rows = db.query.select_resources_by_story(self.conn,
                                                           self.story_id)
        for resource_row in resource_rows:
            res_id = resource_row["id"]
            db.query.update_resource(self.conn, res_id, {"story_id": merge_id})

    def _show_merge_story_dialog(self, new_title, merge_id):
        d = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                              Gtk.MessageType.QUESTION,
                              Gtk.ButtonsType.YES_NO)
        d.set_markup("A story with the title \"{0}\" already exists in your "
                     "library. Would you like to merge this file with that "
                     "story?".format(new_title))
        response = d.run()
        d.destroy()
        if response == Gtk.ResponseType.YES:
            self._merge_releases_with_story(merge_id)
            self._merge_resources_with_story(merge_id)
            db.query.delete_story(self.conn, self.story_id)
            self.load_story(merge_id)
            return True
        else:
            return False
