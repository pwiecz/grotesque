# addremove.py --- 

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


import datetime
import os.path
import warnings

from grotesque import util, ifdb
from treatyofbabel.utils import _imgfuncs
from treatyofbabel.babelerrors import BabelError, IFictionError
from treatyofbabel import ifiction
import treatyofbabel
import query


def add_story_biblio(conn, biblio, ident, contact, ific_source=None):
    try:
        pub_date = util.normalize_date(
            biblio["firstpublished"])
    except:
        pub_date = ""
    if "forgiveness" in biblio:
        forgiveness_row = query.select_forgiveness_by_description(
            conn, biblio["forgiveness"])
        if forgiveness_row is not None:
            forgiveness = forgiveness_row["id"]
        else:
            forgiveness = 1
    else:
        forgiveness = 1
    if "group" in biblio:
        story_group_row = query.select_group_by_name(
            conn, biblio["group"])
        if story_group_row is not None:
            story_group = story_group_row["id"]
        else:
            story_group = query.insert_group(
                conn, biblio["group"])
    else:
        story_group = None
    if "series" in biblio:
        story_series_row = query.select_series_by_name(
            conn, biblio["series"])
        if story_series_row is not None:
            story_series = story_series_row["id"]
        else:
            story_series = query.insert_series(
                conn, biblio["series"])
    else:
        story_series = None
    # IFDB stores story URLs in the contact section
    if (ific_source == "ifdb" and
            (contact is not None and "url" in contact)):
        url = contact["url"]
        if url:
            url = url.strip()
    else:
        url = None
    title = biblio.get("title")
    if title:
        title = title.strip()
    language = biblio.get("language")
    if language:
        language = language.strip()
    headline = biblio.get("headline")
    if headline:
        headline = headline.strip()
    description = biblio.get("description")
    if description:
        description = description.strip()
    seriesnumber = biblio.get("seriesnumber")
    if seriesnumber:
        seriesnumber = seriesnumber.strip()
    bafn = ident.get("bafn")
    if bafn:
        bafn = bafn.strip()
    story_id = query.insert_story(
        conn,
        title,
        language,
        headline,
        pub_date,
        story_group,
        description,
        story_series,
        seriesnumber,
        forgiveness,
        url,
        bafn,
        None)
    return story_id


def add_story_format(conn, ifformat, command):
    if "blorbed" in ifformat:
        raw_format = ifformat.replace("blorbed ", "")
    else:
        raw_format = ifformat.strip()
    format_id = query.insert_format(conn, ifformat, command)
    return format_id


def add_story_release(conn, story_id, ifid, ifformat, command, uri=None):
    if ifformat is not None:
        story_format_row = query.select_format_by_name(conn, ifformat)
        if story_format_row is not None:
            format_id = story_format_row["id"]
        else:
            format_id = add_story_format(conn, ifformat, command)
    else:
        format_id = None
    if not query.select_release(conn, ifid):
        query.insert_release(conn, ifid, story_id, uri, None, None, None, None,
                             None, format_id)
    else:
        query.update_release(conn, ifid, {"uri": uri})
        if format_id is not None:
            query.update_release(conn, ifid, {"format_id": format_id})


def add_story_authors(conn, story_id, biblio):
    """Parse the authors text to get a list of all the authors involved."""
    authors = util.parse_list_str(biblio["author"])
    for author in authors:
        # Only add the author's real name to the filter (no pen names).
        author_real_name = author.split('(')[0].strip()
        if author_real_name == '':
            continue
        author_row = query.select_author_by_name(conn, author_real_name)
        if not author_row:
            author_id = query.insert_author(conn, author_real_name)
        else:
            author_id = author_row["id"]
        query.add_author_to_story(conn, author_id, story_id)


def add_story_genres(conn, story_id, biblio):
    """Parse genre to get a list of all genres named."""
    if biblio["genre"] is None:
        return
    genres = util.parse_list_str(biblio["genre"])
    for genre in genres:
        if not genre:
            continue
        genre_row = query.select_genre_by_name(conn, genre.lower())
        if not genre_row:
            genre_id = query.insert_genre(conn, genre.lower())
        else:
            genre_id = genre_row["id"]
        query.add_genre_to_story(conn, genre_id, story_id)


def _fetch_story_cover(conn, story_id, ific_story, orig_cover):
    annotation = ifiction.get_annotation(ific_story)
    if annotation is None:
        return False
    if "ifdb" not in annotation:
        return False
    if "cover_url" in annotation["ifdb"]:
        data = ifdb.fetch_cover(url=annotation["ifdb"]["cover_url"])
    elif "tuid" in annotation["ifdb"]:
        data = ifdb.fetch_cover(tuid=annotation["ifdb"]["tuid"])
    else:
        return False
    if data is None:
        return False
    img_format = _imgfuncs.deduce_img_format(data)
    if img_format == "jpeg":
        width, height = _imgfuncs.get_jpeg_dim(data)
    elif img_format == "png":
        width, height = _imgfuncs.get_png_dim(data)
    elif img_format == "gif":
        width, height = _imgfuncs.get_gif_dim(data)
    else:
        biblio = query.select_story(conn, story_id)
        warnings.warn("unsupported image format for {0}".format(
            biblio["title"]))
        return False
    description = None
    if orig_cover is not None:
        query.update_cover(conn, orig_cover["id"],
                           {"height": height,
                            "width": width,
                            "format": img_format,
                            "description": description,
                            "data": data})
    else:
        query.insert_cover(
            conn, story_id, img_format, height, width,
            description, data)
    return True


def _extract_story_cover(conn, story_id, filename, orig_cover):
    try:
        cover = treatyofbabel.get_cover(filename)
    except BabelError:
        return False
    if cover is None:
        return False
    if orig_cover is not None:
        query.update_cover(conn, orig_cover["id"],
                           {"height": cover.height,
                            "width": cover.width,
                            "format": cover.img_format,
                            "description": cover.description,
                            "data": cover.data})
    else:
        query.insert_cover(conn, story_id, cover.img_format,
                           cover.height, cover.width, cover.description,
                           cover.data)
    return True


def _add_cover_stub(conn, story_id, ific_story, orig_cover):
    cover_info = ifiction.get_cover(ific_story)
    if cover_info is None:
        return False
    if orig_cover is not None and orig_cover["data"]:
        warnings.warn("cowardly refusing to replace existing cover data "
                      "with IFiction skeleton data")
        return False
    query.insert_cover(
        conn, story_id, cover_info["format"],
        cover_info["height"], cover_info["width"],
        cover_info["description"], "")


def add_story_cover(conn, story_id, filename, ific_story, fetch_coverart):
    orig_cover = query.select_cover_by_story(conn, story_id)
    if fetch_coverart:
        fetch_success = _fetch_story_cover(conn, story_id, ific_story,
                                           orig_cover)
        if fetch_success:
            return True
    if filename is not None:
        extract_success = _extract_story_cover(conn, story_id, filename,
                                               orig_cover)
        if extract_success:
            return True
    return _add_cover_stub(conn, story_id, ific_story, orig_cover)


def add_story_annotation(conn, story_id, annotation):
    if (annotation is not None and
            "grotesque" in annotation and
            "rating" in annotation["grotesque"]):
        rating = float(annotation["grotesque"]["rating"])
        if not rating:
            rating = 0.0
    else:
        rating = 0.0
    rating_txt = util.render_star_rating(rating)
    notes = ""
    if (annotation is not None and "grotesque" in annotation and
            "played" in annotation["grotesque"]):
        played_str = annotation["grotesque"]["played"]
        if played_str == "True":
            played = True
        else:
            played = False
    else:
        played = False
    imported = datetime.date.today()
    query.insert_annotation(conn, story_id, rating, rating_txt,
                         notes, played, imported)


def add_story_ifdb_annotation(conn, story_id, annotation):
    if "ifdb" not in annotation:
        return
    tuid = annotation["ifdb"].get("tuid")
    url = annotation["ifdb"].get("link")
    if url is None:
        url = annotation["ifdb"].get("url")
    if "coverart" in annotation["ifdb"]:
        cover_url = annotation["ifdb"]["coverart"].get("url")
    elif "coverurl" in annotation["ifdb"]:
        cover_url = annotation["ifdb"]["coverurl"]
    else:
        cover_url = None
    if "averagerating" in annotation["ifdb"]:
        avg_rating = float(annotation["ifdb"].get("averagerating"))
    elif "avgrating" in annotation["ifdb"]:
        avg_rating = float(annotation["ifdb"].get("avgrating"))
    else:
        avg_rating = 0.0
    try:
        star_rating = float(annotation["ifdb"].get("starrating"))
    except:
        star_rating = 0.0
    star_rating_txt = util.render_star_rating(star_rating)
    try:
        rating_count_avg = int(annotation["ifdb"].get("ratingcountavg"))
    except:
        rating_count_avg = 0
    try:
        rating_count_tot = int(annotation["ifdb"].get("ratingcounttot"))
    except:
        rating_count_tot = 0
    query.insert_ifdb_annotation(conn, story_id, tuid, url, cover_url,
                              avg_rating, star_rating, star_rating_txt,
                              rating_count_avg, rating_count_tot,
                              datetime.date.today())


def add_story_meta(conn, file_ifid, ific_story, ific_source):
    '''Add a story to the library.

    '''
    biblio = ifiction.get_bibliographic(ific_story)
    ident = ifiction.get_identification(ific_story)
    contact = ifiction.get_contact(ific_story)
    story_row = query.select_story_by_title(
        conn, biblio["title"])
    if story_row:
        # The story is already in the database.
        story_id = story_row["id"]
        return story_id
    story_id = add_story_biblio(conn, biblio, ident, contact, ific_source)
    if "author" in biblio:
        add_story_authors(conn, story_id, biblio)
    if "genre" in biblio:
        add_story_genres(conn, story_id, biblio)
    for ifid in ident["ifid_list"]:
        if ifid == file_ifid:
            continue
        add_story_release(conn, story_id, ifid, None, None)
    annotation = ifiction.get_annotation(ific_story)
    if annotation is not None:
        add_story_annotation(conn, story_id, annotation)
        if "ifdb" in annotation:
            add_story_ifdb_annotation(conn, story_id, annotation)
    return story_id


def add_story_stub(conn, file_ifid, filename):
    basename = os.path.split(filename)[1]
    story_id = query.insert_story(
        conn, basename, None, None, None, None, None, None, None,
        None, None, None, None)
    add_story_annotation(conn, story_id, None)
    return story_id


def get_ifiction(filename, ifid, fetch_metadata):
    ific_story = None
    ific_source = None
    if fetch_metadata:
        ific_story = ifdb.fetch_ifiction(ifid=ifid)
        return (ific_story, "ifdb")
    # Either we're not fetching from IFDB or fetching from there
    # failed.  So, try to extract metadata from the file itself.
    try:
        ific_str = treatyofbabel.get_meta(filename)
    except:
        warnings.warn("no IFiction found for {0}".format(filename))
        return (None, None)
    if not ific_str:
        warnings.warn("no IFiction found for {0}".format(filename))
        return (None, None)
    try:
        ific_dom = ifiction.get_ifiction_dom(ific_str)
    except IFictionError:
        warnings.warn("malformed IFiction found for {0}".format(filename))
        return (None, None)
    stories = ifiction.get_all_stories(ific_dom)
    ific_story = stories[0]
    return (ific_story, "extract")


def clean_story_authors(conn, story_id):
    if not story_id:
        return
    author_ids = query.select_story_authors(conn, story_id)
    for (author_id,) in author_ids:
        query.remove_author_from_story(conn, author_id, story_id)
        auth_stories = query.select_author_stories(conn, author_id)
        if not auth_stories:
            query.delete_author(conn, author_id)


def clean_story_genres(conn, story_id):
    if not story_id:
        return
    genre_ids = query.select_story_genres(conn, story_id)
    for (genre_id,) in genre_ids:
        query.remove_genre_from_story(conn, genre_id, story_id)
        if not query.select_genre_stories(conn, genre_id):
            query.delete_genre(conn, genre_id)


def clean_story_groups(conn, story_id):
    if not story_id:
        return
    story_rec = query.select_story(conn, story_id)
    if not story_rec:
        return
    group_id = story_rec["group_id"]
    if not group_id:
        return
    group_stories = query.select_stories_by_group(conn, group_id)
    if len(group_stories) == 1:
        query.delete_group(conn, group_id)


def clean_story_series(conn, story_id):
    if not story_id:
        return
    story_rec = query.select_story(conn, story_id)
    if not story_rec:
        return
    series_id = story_rec["series_id"]
    if not series_id:
        return
    series_stories = query.select_stories_by_series(conn, series_id)
    if len(series_stories) == 1:
        query.delete_series(conn, series_id)


def clean_story_annotation(conn, story_id):
    if not story_id:
        return
    annot_rec = query.select_annotation_by_story(conn, story_id)
    if not annot_rec:
        return
    annot_id = annot_rec["id"]
    query.delete_annotation(conn, annot_id)


def clean_story_ifdb_annotation(conn, story_id):
    if not story_id:
        return
    annot_rec = query.select_ifdb_annotation_by_story(conn, story_id)
    if not annot_rec:
        return
    annot_id = annot_rec["id"]
    query.delete_ifdb_annotation(conn, annot_id)


def clean_story_releases(conn, story_id):
    if not story_id:
        return
    releases = query.select_releases_by_story(conn, story_id)
    for release in releases:
        query.delete_release(conn, release["ifid"])


def clean_story_cover(conn, story_id):
    if not story_id:
        return
    cover_rec = query.select_cover_by_story(conn, story_id)
    if cover_rec is None:
        return
    query.delete_cover(conn, cover_rec["id"])
