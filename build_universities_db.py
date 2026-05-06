#!/usr/bin/env python3
"""
Build universities.sqlite from the UNI_DATA array embedded in RDO_iOS_Home.html.

Schema:
  CREATE TABLE universities (
    id INTEGER PRIMARY KEY,
    name_ar TEXT NOT NULL,
    name_en TEXT NOT NULL,
    postdoc_r INTEGER, postdoc_allocated INTEGER, postdoc_disbursed INTEGER,
    postdoc_launched INTEGER, postdoc_status TEXT,
    infra_allocated INTEGER, infra_disbursed INTEGER, infra_status TEXT,
    hqr_allocated INTEGER, hqr_disbursed INTEGER, hqr_status TEXT
  );
"""
import re
import json
import sqlite3
from pathlib import Path

HTML = Path("/sessions/clever-optimistic-volta/mnt/outputs/RDO_iOS_Home.html").read_text(encoding="utf-8")
DB_PATH = Path("/tmp/universities.sqlite")
FINAL_PATH = Path("/sessions/clever-optimistic-volta/mnt/outputs/universities.sqlite")

# Pull the UNI_DATA=[ ... ]; block out of the HTML
m = re.search(r"const UNI_DATA\s*=\s*(\[.*?\])\s*;", HTML, re.DOTALL)
if not m:
    raise SystemExit("UNI_DATA array not found in HTML")
raw = m.group(1)

# The literal is JS — keys are unquoted and strings use double quotes already.
# Convert it to JSON by quoting bareword keys.
js_to_json = re.sub(r"([{,]\s*)([a-zA-Z_][\w]*)\s*:", r'\1"\2":', raw)

data = json.loads(js_to_json)
print(f"Parsed {len(data)} universities")

if DB_PATH.exists():
    DB_PATH.unlink()

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("""
CREATE TABLE universities (
    id INTEGER PRIMARY KEY,
    name_ar TEXT NOT NULL,
    name_en TEXT NOT NULL,
    postdoc_r INTEGER DEFAULT 0,
    postdoc_allocated INTEGER DEFAULT 0,
    postdoc_disbursed INTEGER DEFAULT 0,
    postdoc_launched INTEGER DEFAULT 0,
    postdoc_status TEXT DEFAULT '',
    infra_allocated INTEGER DEFAULT 0,
    infra_disbursed INTEGER DEFAULT 0,
    infra_status TEXT DEFAULT '',
    hqr_allocated INTEGER DEFAULT 0,
    hqr_disbursed INTEGER DEFAULT 0,
    hqr_status TEXT DEFAULT ''
);
""")

rows = []
for u in data:
    p = u.get("postdoc", {}) or {}
    i = u.get("infra", {}) or {}
    h = u.get("hqr", {}) or {}
    rows.append((
        u["id"], u["name_ar"], u["name_en"],
        p.get("r", 0) or 0,
        p.get("allocated", 0) or 0,
        p.get("disbursed", 0) or 0,
        p.get("launched", 0) or 0,
        p.get("status", "") or "",
        i.get("allocated", 0) or 0,
        i.get("disbursed", 0) or 0,
        i.get("status", "") or "",
        h.get("allocated", 0) or 0,
        h.get("disbursed", 0) or 0,
        h.get("status", "") or "",
    ))

cur.executemany("""
INSERT INTO universities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", rows)

conn.commit()

# Quick verification
cur.execute("SELECT COUNT(*) FROM universities")
print("Row count:", cur.fetchone()[0])
cur.execute("SELECT id, name_en, postdoc_r FROM universities WHERE postdoc_r > 0 ORDER BY postdoc_r DESC LIMIT 5")
print("Top-5 by postdoc researchers:")
for r in cur.fetchall():
    print(" ", r)

conn.close()
# Copy from /tmp to the final mounted location.
# (sqlite + the FUSE mount don't always agree on locking, and shutil.copyfile
#  occasionally truncates to 0 bytes — using raw bytes write+fsync avoids that.)
data = DB_PATH.read_bytes()
with open(FINAL_PATH, "wb") as f:
    f.write(data)
    f.flush()
    import os
    os.fsync(f.fileno())
print("Wrote", FINAL_PATH, FINAL_PATH.stat().st_size, "bytes")
