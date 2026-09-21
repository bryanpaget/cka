#!/usr/bin/env python3
"""Verify a built CKA deck: valid zip + SQLite with matching card counts.

Checks that the .apkg is a real zip containing collection.anki2 + media,
that the SQLite opens, and that notes == cards == the number of cards in
the source TSV. Exits non-zero on any failure.

Usage:
    python3 verify_apkg.py [deck.apkg] [cards.tsv]
"""

import os
import sqlite3
import sys
import tempfile
import zipfile


def count_tsv_cards(path):
    with open(path, encoding="utf-8") as fh:
        return sum(1 for line in fh if line.strip() and not line.startswith("#"))


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    apkg = argv[1] if len(argv) > 1 else os.path.join(here, "CKA-Deck.apkg")
    tsv = argv[2] if len(argv) > 2 else os.path.join(here, "cka-cards.tsv")

    if not zipfile.is_zipfile(apkg):
        sys.exit("FAIL: not a valid zip: %s" % apkg)

    with zipfile.ZipFile(apkg) as zf:
        names = set(zf.namelist())
        for required in ("collection.anki2", "media"):
            if required not in names:
                sys.exit("FAIL: missing %s in apkg" % required)
        tmp = tempfile.mkdtemp()
        zf.extract("collection.anki2", tmp)

    con = sqlite3.connect(os.path.join(tmp, "collection.anki2"))
    notes = con.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    cards = con.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    con.close()

    expected = count_tsv_cards(tsv)
    print("notes=%d cards=%d expected=%d" % (notes, cards, expected))
    if not (notes == cards == expected):
        sys.exit("FAIL: count mismatch")
    print("OK: deck verified with %d cards." % cards)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
