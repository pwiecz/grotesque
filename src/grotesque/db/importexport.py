# importexport.py --- 

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


from treatyofbabel import ifiction
import query


def export_ific_id(conn, doc, story_node, story_id):
    story_rec = query.select_story(conn, story_id)
    if story_rec["bafn"] is not None:
        bafn = unicode(story_rec["bafn"])
    else:
        bafn = None
    default_rel = story_rec["default_release"]
    ifids = [default_rel]
    release_recs = query.select_releases_by_story(conn, story_id)
    for release_rec in release_recs:
        if release_rec["ifid"] != default_rel:
            ifids.append(release_rec["ifid"])
            continue
        format_id = release_rec["format_id"]
        if format_id is None:
            continue
        format_rec = query.select_format(conn, format_id)
        format_name = format_rec["name"]
        if "blorbed" in format_name:
            format_name = format_name.replace("blorbed ", "")
    ifiction.add_identification(
            doc, story_node, ifids, format_name, bafn)


def export_ific_biblio(conn, doc, story_node, story_id):
    story_rec = query.select_story(conn, story_id)
    if story_rec["firstpublished"] is None:
        firstpub = u""
    else:
        firstpub = unicode(story_rec["firstpublished"])
    if story_rec["seriesnumber"] is None:
        seriesnumber = u""
    else:
        seriesnumber = unicode(story_rec["seriesnumber"])
    biblio = {"title": story_rec["title"],
              "language": story_rec["language"],
              "headline": story_rec["headline"],
              "firstpublished": firstpub,
              "description": story_rec["description"],
              "seriesnumber": seriesnumber}
    if story_rec["group_id"]:
        group_rec = query.select_genre(conn, story_rec["group_id"])
        if group_rec is not None:
            biblio["group"] = group_rec["name"]
    if story_rec["series_id"]:
        series_rec = query.select_series(conn, story_rec["series_id"])
        if series_rec is not None:
            biblio["series"] = series_rec["name"]
    if story_rec["forgiveness_id"]:
        forgive_rec = query.select_forgiveness(
            conn, story_rec["series_id"])
        if forgive_rec is not None:
            biblio["forgiveness"] = forgive_rec["description"]
    author_ids = query.select_story_authors(conn, story_id)
    authors = []
    for author_id in author_ids:
        author_rec = query.select_author(conn, author_id[0])
        if author_rec is not None:
            authors.append(author_rec["name"])
    if len(authors) > 2:
        authors_tmp = authors[:-1]
        authors_tmp.extend(["and", authors[-1]])
        authors = authors_tmp
    if len(authors) > 0:
        biblio["author"] = ", ".join(authors)
    genre_ids = query.select_story_genres(conn, story_id)
    genres = []
    for genre_id in genre_ids:
        genre_rec = query.select_genre(conn, genre_id[0])
        if genre_rec is not None:
            genres.append(genre_rec["name"])
    if len(genres) > 0:
        biblio["genre"] = "/".join(genres)
    ifiction.add_bibliographic(doc, story_node, False, **biblio)


def export_ific_rsrc(conn, doc, story_node, story_id):
    resource_recs = query.select_resources_by_story(conn, story_id)
    for rec in resource_recs:
        ifiction.add_resource(
            doc, story_node, rec["uri"], rec["description"])


def export_ific_cntct(conn, doc, story_node, story_id):
    author_ids = query.select_story_authors(conn, story_id)
    for author_id in author_ids:
        author_rec = query.select_author(conn, author_id[0])
        if author_rec is None:
            continue
        if author_rec["url"] is None and author_rec["email"] is None:
            continue
        ifiction.add_contact(
            doc, story_node, author_rec["url"], author_rec["email"])


def export_ific_cover(conn, doc, story_node, story_id):
    cover_rec = query.select_cover_by_story(conn, story_id)
    if cover_rec:
        if cover_rec["format"] == "jpeg":
            cover_format = "jpg"
        else:
            cover_format = cover_rec["format"]
        ifiction.add_cover(
            doc, story_node, cover_format, cover_rec["height"],
            cover_rec["width"], cover_rec["description"])


def export_ific_rels(conn, doc, story_node, story_id):
    release_recs = query.select_releases_by_story(conn, story_id)
    for release_rec in release_recs:
        if release_rec["release_date"] is None:
            continue
        if release_rec["version"] is None:
            version = u""
        else:
            version = unicode(release_rec["version"])
        ifiction.add_release(
            doc, story_node, release_date, version, release_rec["compiler"],
            release_rec["compiler_version"])


def export_ific_annot(conn, doc, story_node, story_id):
    annot_rec = query.select_annotation_by_story(conn, story_id)
    if annot_rec is not None:
        if annot_rec["rating"] is None:
            rating = u""
        else:
            rating = unicode(annot_rec["rating"])
        if annot_rec["played"] is None:
            played = u""
        else:
            played = unicode(annot_rec["played"])
        if annot_rec["imported"] is None:
            imported = u""
        else:
            imported = unicode(annot_rec["imported"])
    else:
        rating = None
        played = None
        imported = None
    release_recs = query.select_releases_by_story(conn, story_id)
    files = [{"ifid": rec["ifid"], "uri": rec["uri"]}
             for rec in release_recs if rec["uri"] is not None]
    ifiction.add_annotation(
        doc, story_node, "grotesque", {"rating": rating,
                                       "notes": annot_rec["notes"],
                                       "played": played,
                                       "imported": imported,
                                       "storyfile": files})


def export_ific_ifdb_annot(conn, doc, story_node, story_id):
    ifdb_annot_rec = query.select_ifdb_annotation_by_story(conn, story_id)
    if ifdb_annot_rec is not None:
        if ifdb_annot_rec["avg_rating"] is None:
            avg_rating = u""
        else:
            avg_rating = unicode(ifdb_annot_rec["avg_rating"])
        if ifdb_annot_rec["star_rating"] is None:
            star_rating = u""
        else:
            star_rating = unicode(ifdb_annot_rec["star_rating"])
        if ifdb_annot_rec["rating_count_avg"] is None:
            rating_count_avg = u""
        else:
            rating_count_avg = unicode(ifdb_annot_rec["rating_count_avg"])
        if ifdb_annot_rec["rating_count_tot"] is None:
            rating_count_tot = u""
        else:
            rating_count_tot = unicode(ifdb_annot_rec["rating_count_tot"])
        if ifdb_annot_rec["updated"] is None:
            updated = u""
        else:
            updated = unicode(ifdb_annot_rec["updated"])
        ifiction.add_annotation(
            doc, story_node, "ifdb",
            {"tuid": ifdb_annot_rec["tuid"],
             "url": ifdb_annot_rec["url"],
             "coverUrl": ifdb_annot_rec["cover_url"],
             "avgRating": avg_rating,
             "starRating": star_rating,
             "ratingCountAvg": rating_count_avg,
             "ratingCountTot": rating_count_tot,
             "updated": updated})
