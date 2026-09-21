#!/usr/bin/env python3
"""Zero-dependency Anki .apkg builder (Python standard library only).

An .apkg file is a ZIP archive containing:
  - collection.anki2 : a SQLite database in Anki schema v11
  - media            : a JSON map of media files (empty here -> "{}")

We use only sqlite3, zipfile, json, hashlib, time, tempfile from the stdlib.
No genanki, no network.

IDs are derived deterministically from content via sha256 so that re-importing
an updated deck UPDATES the existing notes/cards rather than duplicating them.

Usage:
    python3 build_apkg.py [cards.tsv] [out.apkg]

Defaults:
    cards.tsv -> ./cka-cards.tsv (next to this script)
    out.apkg  -> ./CKA-Deck.apkg

TSV format (tab-separated):
    Front<TAB>Back<TAB>tags
Header lines beginning with '#' are ignored:
    #separator:tab
    #html:true
    #tags column:3
"""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import time
import zipfile

DECK_NAME = "CKA Exam Prep"
MODEL_NAME = "CKA Basic (Q/A)"

CSS = """\
.card {
  font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 18px;
  line-height: 1.5;
  color: #1a1a2e;
  background: #f7f8fc;
  text-align: left;
  padding: 20px;
}
.tag {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  color: #ffffff;
  background: #326ce5;
  border-radius: 4px;
  padding: 2px 8px;
  margin-right: 6px;
}
hr#answer {
  border: none;
  border-top: 2px solid #326ce5;
  margin: 14px 0;
}
code, pre {
  font-family: "SF Mono", "Cascadia Code", Consolas, monospace;
  background: #eceff4;
  border-radius: 4px;
}
code { padding: 1px 5px; }
pre {
  padding: 12px;
  overflow-x: auto;
  border-left: 3px solid #326ce5;
}
b, strong { color: #204080; }
"""

FRONT_TMPL = "{{Front}}"
BACK_TMPL = '{{FrontSide}}\n<hr id="answer">\n{{Back}}'


def stable_id(*parts):
    """Deterministic 63-bit integer id from sha256 of the given parts."""
    h = hashlib.sha256("\x1f".join(str(p) for p in parts).encode("utf-8")).hexdigest()
    # 15 hex digits -> 60 bits, safely positive and within SQLite INTEGER range.
    return int(h[:15], 16)


def parse_tsv(path):
    cards = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n").rstrip("\r")
            if not line:
                continue
            if line.startswith("#"):
                continue
            cols = line.split("\t")
            if len(cols) < 2:
                raise ValueError(
                    "Expected at least 2 tab-separated columns, got: %r" % (line,)
                )
            front = cols[0]
            back = cols[1]
            tags = cols[2] if len(cols) >= 3 else ""
            cards.append((front, back, tags))
    return cards


def build_models_json(model_id):
    return {
        str(model_id): {
            "id": model_id,
            "name": MODEL_NAME,
            "type": 0,
            "mod": 0,
            "usn": -1,
            "sortf": 0,
            "did": None,
            "tmpls": [
                {
                    "name": "Card 1",
                    "ord": 0,
                    "qfmt": FRONT_TMPL,
                    "afmt": BACK_TMPL,
                    "bqfmt": "",
                    "bafmt": "",
                    "did": None,
                    "bfont": "",
                    "bsize": 0,
                }
            ],
            "flds": [
                {
                    "name": "Front",
                    "ord": 0,
                    "sticky": False,
                    "rtl": False,
                    "font": "Arial",
                    "size": 20,
                    "media": [],
                },
                {
                    "name": "Back",
                    "ord": 1,
                    "sticky": False,
                    "rtl": False,
                    "font": "Arial",
                    "size": 20,
                    "media": [],
                },
            ],
            "css": CSS,
            "latexPre": "",
            "latexPost": "",
            "req": [[0, "any", [0]]],
            "tags": [],
            "vers": [],
        }
    }


def build_decks_json(deck_id):
    return {
        "1": {
            "id": 1,
            "name": "Default",
            "mod": 0,
            "usn": 0,
            "collapsed": False,
            "desc": "",
            "dyn": 0,
            "conf": 1,
            "extendNew": 10,
            "extendRev": 50,
            "newToday": [0, 0],
            "revToday": [0, 0],
            "lrnToday": [0, 0],
            "timeToday": [0, 0],
        },
        str(deck_id): {
            "id": deck_id,
            "name": DECK_NAME,
            "mod": 0,
            "usn": -1,
            "collapsed": False,
            "desc": "CKA exam prep flashcards.",
            "dyn": 0,
            "conf": 1,
            "extendNew": 10,
            "extendRev": 50,
            "newToday": [0, 0],
            "revToday": [0, 0],
            "lrnToday": [0, 0],
            "timeToday": [0, 0],
        },
    }


def build_dconf_json():
    return {
        "1": {
            "id": 1,
            "name": "Default",
            "mod": 0,
            "usn": 0,
            "maxTaken": 60,
            "autoplay": True,
            "timer": 0,
            "replayq": True,
            "new": {
                "bury": False,
                "delays": [1.0, 10.0],
                "initialFactor": 2500,
                "ints": [1, 4, 0],
                "order": 1,
                "perDay": 20,
                "separate": True,
            },
            "rev": {
                "bury": False,
                "ease4": 1.3,
                "ivlFct": 1.0,
                "maxIvl": 36500,
                "perDay": 200,
                "hardFactor": 1.2,
            },
            "lapse": {
                "delays": [10.0],
                "leechAction": 1,
                "leechFails": 8,
                "minInt": 1,
                "mult": 0.0,
            },
            "dyn": False,
        }
    }


def build_conf_json(deck_id):
    return {
        "nextPos": 1,
        "estTimes": True,
        "activeDecks": [deck_id],
        "sortType": "noteFld",
        "timeLim": 0,
        "sortBackwards": False,
        "addToCur": True,
        "curDeck": deck_id,
        "newBury": True,
        "newSpread": 0,
        "dueCounts": True,
        "curModel": None,
        "collapseTime": 1200,
    }


ANKI2_SCHEMA = """
CREATE TABLE col (
    id integer primary key,
    crt integer not null,
    mod integer not null,
    scm integer not null,
    ver integer not null,
    dty integer not null,
    usn integer not null,
    ls  integer not null,
    conf text not null,
    models text not null,
    decks text not null,
    dconf text not null,
    tags text not null
);
CREATE TABLE notes (
    id integer primary key,
    guid text not null,
    mid integer not null,
    mod integer not null,
    usn integer not null,
    tags text not null,
    flds text not null,
    sfld text not null,
    csum integer not null,
    flags integer not null,
    data text not null
);
CREATE TABLE cards (
    id integer primary key,
    nid integer not null,
    did integer not null,
    ord integer not null,
    mod integer not null,
    usn integer not null,
    type integer not null,
    queue integer not null,
    due integer not null,
    ivl integer not null,
    factor integer not null,
    reps integer not null,
    lapses integer not null,
    left integer not null,
    odue integer not null,
    odid integer not null,
    flags integer not null,
    data text not null
);
CREATE TABLE revlog (
    id integer primary key,
    cid integer not null,
    usn integer not null,
    ease integer not null,
    ivl integer not null,
    lastIvl integer not null,
    factor integer not null,
    time integer not null,
    type integer not null
);
CREATE TABLE graves (
    usn integer not null,
    oid integer not null,
    type integer not null
);
CREATE INDEX ix_notes_usn on notes (usn);
CREATE INDEX ix_cards_usn on cards (usn);
CREATE INDEX ix_revlog_usn on revlog (usn);
CREATE INDEX ix_cards_nid on cards (nid);
CREATE INDEX ix_cards_sched on cards (did, queue, due);
CREATE INDEX ix_revlog_cid on revlog (cid);
CREATE INDEX ix_notes_csum on notes (csum);
"""


def field_checksum(sfld):
    """Anki's fieldChecksum: first 8 hex digits of sha1(sfld) as an int."""
    return int(hashlib.sha1(sfld.encode("utf-8")).hexdigest()[:8], 16)


def build_collection(db_path, cards):
    now = int(time.time())
    now_ms = now * 1000

    model_id = stable_id("model", MODEL_NAME)
    deck_id = stable_id("deck", DECK_NAME)

    conf = build_conf_json(deck_id)
    models = build_models_json(model_id)
    decks = build_decks_json(deck_id)
    dconf = build_dconf_json()

    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        cur.executescript(ANKI2_SCHEMA)

        cur.execute(
            "INSERT INTO col (id, crt, mod, scm, ver, dty, usn, ls, "
            "conf, models, decks, dconf, tags) "
            "VALUES (1, ?, ?, ?, 11, 0, 0, 0, ?, ?, ?, ?, ?)",
            (
                now,
                now_ms,
                now_ms,
                json.dumps(conf),
                json.dumps(models),
                json.dumps(decks),
                json.dumps(dconf),
                json.dumps({}),
            ),
        )

        due = 1
        for front, back, tags in cards:
            # Deterministic guid/note id/card id from the front text.
            guid = hashlib.sha256(("guid" + front).encode("utf-8")).hexdigest()[:10]
            note_id = stable_id("note", front)
            card_id = stable_id("card", front)

            flds = front + "\x1f" + back
            sfld = front
            tag_str = ""
            if tags.strip():
                tag_str = " " + " ".join(tags.split()) + " "

            cur.execute(
                "INSERT OR REPLACE INTO notes "
                "(id, guid, mid, mod, usn, tags, flds, sfld, csum, flags, data) "
                "VALUES (?, ?, ?, ?, -1, ?, ?, ?, ?, 0, '')",
                (
                    note_id,
                    guid,
                    model_id,
                    now,
                    tag_str,
                    flds,
                    sfld,
                    field_checksum(sfld),
                ),
            )

            cur.execute(
                "INSERT OR REPLACE INTO cards "
                "(id, nid, did, ord, mod, usn, type, queue, due, ivl, "
                "factor, reps, lapses, left, odue, odid, flags, data) "
                "VALUES (?, ?, ?, 0, ?, -1, 0, 0, ?, 0, 0, 0, 0, 0, 0, 0, 0, '')",
                (card_id, note_id, deck_id, now, due),
            )
            due += 1

        con.commit()
    finally:
        con.close()


def build_apkg(tsv_path, out_path):
    cards = parse_tsv(tsv_path)
    tmpdir = tempfile.mkdtemp(prefix="apkg_")
    db_path = os.path.join(tmpdir, "collection.anki2")
    build_collection(db_path, cards)

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(db_path, "collection.anki2")
        # No media: Anki still expects a media map file.
        zf.writestr("media", "{}")

    # Best-effort cleanup of the temp db.
    try:
        os.remove(db_path)
        os.rmdir(tmpdir)
    except OSError:
        pass

    return len(cards)


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    tsv_path = argv[1] if len(argv) > 1 else os.path.join(here, "cka-cards.tsv")
    out_path = argv[2] if len(argv) > 2 else os.path.join(here, "CKA-Deck.apkg")

    if not os.path.exists(tsv_path):
        sys.stderr.write("TSV not found: %s\n" % tsv_path)
        return 1

    count = build_apkg(tsv_path, out_path)
    print("Wrote %s with %d cards." % (out_path, count))

    # Keep the GitHub Pages reviewer's copy of the cards in sync with the
    # single source of truth (this TSV). docs/cka-cards.tsv is what index.html
    # fetches, since Pages only serves files under docs/.
    repo_root = os.path.dirname(here)
    docs_tsv = os.path.join(repo_root, "docs", "cka-cards.tsv")
    if os.path.isdir(os.path.dirname(docs_tsv)):
        with open(tsv_path, "r", encoding="utf-8") as src:
            data = src.read()
        with open(docs_tsv, "w", encoding="utf-8") as dst:
            dst.write(data)
        print("Synced %s" % docs_tsv)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
