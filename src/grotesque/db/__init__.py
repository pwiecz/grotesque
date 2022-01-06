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


import sqlite3
import datetime
import os.path
import subprocess
import warnings

import treatyofbabel
from treatyofbabel import ifiction
from treatyofbabel.babelerrors import BabelError
from treatyofbabel.formats.executable import is_win32_executable

import schema
import query
import importexport
import addremove


def connect(db_file):
    conn = sqlite3.connect(
        db_file,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn


def close_connection(conn):
    conn.close()


def create_tables(conn):
    c = conn.cursor()
    for stmnt in schema.TABLES:
        c.execute(stmnt)
    conn.commit()


def set_up_db(conn, grotesque_version):
    create_tables(conn)
    query.set_db_version(conn, grotesque_version)
    query.fill_forgiveness(conn)


def add_story_from_ifiction(conn, story_file, ifid, ific_story, ific_source,
                            fetch_coverart):
    if ific_story is None or ific_source is None:
        return None
    story_id = addremove.add_story_meta(conn, ifid, ific_story, ific_source)
    addremove.add_story_cover(conn, story_id, story_file, ific_story,
                              fetch_coverart)
    return story_id


def _file_in_db(conn, filename):
    file_release = query.select_release_by_uri(conn, filename)
    return file_release is not None


def _get_raw_format(filename):
    try:
        ifformat = treatyofbabel.deduce_format(filename)
    except BabelError as e:
        warnings.warn("{0} is of an unknown format; skipping".format(filename))
        raise e
    except ValueError as e:
        warnings.warn("{0} does not contain any data".format(filename))
        raise e
    if "blorbed" in ifformat:
        raw_format = ifformat.split()[1].strip()
    elif ifformat.strip() == "executable":
        with open(filename) as h:
            buf = h.read()
        if is_win32_executable(buf):
            raw_format = "win32"
        else:
            raw_format = "dos"
    else:
        raw_format = ifformat.strip()
    return raw_format


def _get_story_new_ifids(conn, story_ifids, filename, format_id):
    new_ifids = []
    story_ids = set()
    for ifid in story_ifids:
        release_rec = query.select_release(conn, ifid)
        if release_rec is None:
            new_ifids.append(ifid)
            continue
        story_ids.add(release_rec["story_id"])
        if release_rec["uri"] != filename:
            # If a release with that IFID has been previously added,
            # update its associated file
            query.update_release(conn, ifid, {"uri": filename,
                                              "format_id": format_id})
    if len(story_ids) == 0:
        return (None, new_ifids)
    if len(story_ids) > 1:
        raise Exception(("Multiple stories are linked to the IFIDs associated ",
                         "with file {0}".format(filename)))
    story_id = list(story_ids)[0]
    return (story_id, new_ifids)


def _get_story_ific(filename, ifids, fetch_metadata):
    ific_story = None
    if fetch_metadata:
        for ifid in ifids:
            ific_story, ific_source = addremove.get_ifiction(filename, ifid,
                                                             True)
            ific_ifid = ifid
            if ific_story is not None:
                break
    if ific_story is None:
        for ifid in ifids:
            ific_story, ific_source = addremove.get_ifiction(filename, ifid,
                                                             False)
            ific_ifid = ifid
    return (ific_story, ific_source, ific_ifid)


def add_story_from_file(conn, settings, filename, fetch_metadata,
                        fetch_coverart):
    fail = False
    # Check if this file has been added already
    if _file_in_db(conn, filename):
        return (None, None)
    # Get the format and the interpreter command
    raw_format = _get_raw_format(filename)
    try:
        command = settings.get_launcher(raw_format)
    except:
        command = None
    format_rec = query.select_format_by_name(conn, raw_format)
    if format_rec is not None:
        format_id = format_rec["id"]
    else:
        format_id = addremove.add_story_format(conn, raw_format, command)
    # Check if any of this file's IFIDs have already been added
    try:
        ifids = treatyofbabel.get_ifids(filename)
    except (BabelError, ValueError) as e:
        raise e
    story_id, new_ifids = _get_story_new_ifids(conn, ifids, filename, format_id)
    if not new_ifids:
        return (None, None)
    if story_id is None:
        ific_story, ific_source, ifid = _get_story_ific(filename, ifids,
                                                        fetch_metadata)
        if ific_story is None:
            story_id = addremove.add_story_stub(conn, ifid, filename)
            fail = True
        else:
            story_id = addremove.add_story_meta(conn, ifid, ific_story,
                                                ific_source)
            addremove.add_story_cover(conn, story_id, filename, ific_story,
                                      fetch_coverart)
    for ifid in new_ifids:
        addremove.add_story_release(conn, story_id, ifid, raw_format, command,
                                    os.path.realpath(filename))
    # Assume that the user wants the most recent version added
    # to be the default release
    query.update_story(conn, story_id, {"default_release": new_ifids[0]})
    return (story_id, fail)


def remove_story(conn, story_id):
    addremove.clean_story_authors(conn, story_id)
    addremove.clean_story_genres(conn, story_id)
    addremove.clean_story_groups(conn, story_id)
    addremove.clean_story_series(conn, story_id)
    addremove.clean_story_annotation(conn, story_id)
    addremove.clean_story_ifdb_annotation(conn, story_id)
    addremove.clean_story_releases(conn, story_id)
    addremove.clean_story_cover(conn, story_id)
    query.delete_story(conn, story_id)


def export_ifiction(conn, file_handle, story_ids, grotesque_version):
    doc = ifiction.create_ifiction_dom()
    for story_id in story_ids:
        story_node = ifiction.add_story(doc)
        try:
            importexport.export_ific_id(conn, doc, story_node, story_id)
            importexport.export_ific_biblio(conn, doc, story_node, story_id)
            importexport.export_ific_rsrc(conn, doc, story_node, story_id)
            importexport.export_ific_cntct(conn, doc, story_node, story_id)
            importexport.export_ific_cover(conn, doc, story_node, story_id)
            importexport.export_ific_rels(conn, doc, story_node, story_id)
            importexport.export_ific_annot(conn, doc, story_node, story_id)
            importexport.export_ific_ifdb_annot(conn, doc, story_node, story_id)
            ifiction.add_colophon(
                doc, story_node, "Grotesque", unicode(datetime.date.today()),
                unicode(grotesque_version))
            ifiction.merge_story(doc, story_node)
        except Exception as e:
            warnings.warn(e)
            continue
    xml = doc.toprettyxml(indent="\t", encoding="UTF-8")
    file_handle.write(xml)


def import_ifiction(conn, settings, story_node, fetch_coverart):
    ific_annot = ifiction.get_annotation(story_node)
    story_id = addremove.add_story_meta(conn, None, story_node, "import")
    got_cover = False
    if (not ific_annot or "grotesque" not in ific_annot or
        "storyfile" not in ific_annot["grotesque"]):
        ific_biblio = ifiction.get_bibliographic(story_node)
        warnings.warn("".join(["not enough information for {0}",
                               " importing metadata only".format(
                                   ific_biblio["title"])]))
        return (story_id, True)
    story_files = []
    try:
        ifid = ific_annot["grotesque"]["storyfile"]["ifid"]
        filename = ific_annot["grotesque"]["storyfile"]["uri"]
        story_files.append((ifid, filename))
    except:
        for storyfile in ific_annot["grotesque"]["storyfile"]:
            ifid = storyfile["ifid"]
            filename = storyfile["uri"]
            story_files.append((ifid, filename))
    for ifid, filename in story_files:
        if not got_cover:
            got_cover = addremove.add_story_cover(
                conn, story_id, filename, story_node,
                fetch_coverart)
        try:
            ifformat = treatyofbabel.deduce_format(filename)
        except BabelError:
            warnings.warn("{0} is of an unknown format".format(filename))
            raise BabelError
        if "blorbed" in ifformat:
            raw_format = ifformat.split()[1].strip()
        elif ifformat.strip() == "executable":
            with open(filename) as h:
                buf = h.read()
            if is_win32_executable(buf):
                raw_format = "win32"
            else:
                raw_format = "dos"
        else:
            raw_format = ifformat.strip()
        try:
            command = settings.get_launcher(raw_format)
        except:
            command = None
        addremove.add_story_release(conn, story_id, ifid, ifformat,
                                        command, os.path.realpath(filename))
    query.update_story(conn, story_id, {"default_release": story_files[0][0]})
    return (story_id, False)


def launch_story(conn, settings, story_id, release_id=None):
    if story_id is None:
        raise ValueError("No story specified")
    if release_id is None:
        story = query.select_story(conn, story_id)
        release_id = story["default_release"]
        if not release_id:
            releases = query.select_releases_by_story(conn, story_id)
            if not releases:
                raise ValueError("No releases found for story")
            release_id = releases[0]["id"]
            if not release_id:
                raise ValueError("No releases found for story")
    launch_release(conn, settings, release_id)


def launch_release(conn, settings, release_id):
    if release_id is None:
        raise ValueError("No story or release specified")
    release = query.select_release(conn, release_id)
    if not release:
        raise ValueError("Release not found")
    story_file = release["uri"]
    if not story_file or not os.path.exists(story_file):
        raise ValueError("Story file not found")
    story_format = ""
    if not release["format_id"]:
        raise ValueError("Unknown format")
    format_row = query.select_format(conn, release["format_id"])
    if not format_row:
        raise ValueError("Unknown format")
    story_format = format_row["name"]
    if not story_format:
        raise ValueError("Unknown format")
    if "blorbed" in story_format:
        # TODO: allow different interpreters for Blorbed files(?)
        story_format = story_format.split()[1]
    try:
        launcher = settings.get_launcher(story_format)
    except:
        raise ValueError("No launcher set for format {0}".format(story_format))
    try:
        subprocess.call([launcher, story_file])
    except subprocess.CalledProcessError as e:
        raise ValueError("Launcher error: {0}".format(str(e)))
