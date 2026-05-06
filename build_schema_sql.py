#!/usr/bin/env python3
"""
Emit a Turso-ready schema.sql:
  - DROP / CREATE the universities table
  - INSERT all 48 dummy rows
Output: /sessions/clever-optimistic-volta/mnt/outputs/schema.sql
"""
import re, json
from pathlib import Path

HTML = Path("/sessions/clever-optimistic-volta/mnt/outputs/RDO_iOS_Home.html").read_text(encoding="utf-8")
OUT  = Path("/sessions/clever-optimistic-volta/mnt/outputs/schema.sql")

m = re.search(r"(?:let|const) UNI_DATA\s*=\s*(\[.*?\])\s*;", HTML, re.DOTALL)
raw = m.group(1)
data = json.loads(re.sub(r"([{,]\s*)([a-zA-Z_][\w]*)\s*:", r'\1"\2":', raw))

def sql_str(s):
    return "'" + str(s).replace("'", "''") + "'"

lines = []
lines.append("-- Turso / libSQL seed for the universities table")
lines.append("-- Run this once after creating your Turso database.")
lines.append("")
lines.append("DROP TABLE IF EXISTS universities;")
lines.append("")
lines.append("CREATE TABLE universities (")
lines.append("  id INTEGER PRIMARY KEY,")
lines.append("  name_ar TEXT NOT NULL,")
lines.append("  name_en TEXT NOT NULL,")
lines.append("  postdoc_r INTEGER DEFAULT 0,")
lines.append("  postdoc_allocated INTEGER DEFAULT 0,")
lines.append("  postdoc_disbursed INTEGER DEFAULT 0,")
lines.append("  postdoc_launched INTEGER DEFAULT 0,")
lines.append("  postdoc_status TEXT DEFAULT '',")
lines.append("  infra_allocated INTEGER DEFAULT 0,")
lines.append("  infra_disbursed INTEGER DEFAULT 0,")
lines.append("  infra_status TEXT DEFAULT '',")
lines.append("  hqr_allocated INTEGER DEFAULT 0,")
lines.append("  hqr_disbursed INTEGER DEFAULT 0,")
lines.append("  hqr_status TEXT DEFAULT '',")
lines.append("  updated_at TEXT DEFAULT (datetime('now'))")
lines.append(");")
lines.append("")
lines.append("-- Seed data (48 universities)")

for u in data:
    p = u.get("postdoc",{}) or {}
    i = u.get("infra",{})   or {}
    h = u.get("hqr",{})     or {}
    vals = [
        str(u["id"]),
        sql_str(u["name_ar"]),
        sql_str(u["name_en"]),
        str(p.get("r",0) or 0),
        str(p.get("allocated",0) or 0),
        str(p.get("disbursed",0) or 0),
        str(p.get("launched",0) or 0),
        sql_str(p.get("status","") or ""),
        str(i.get("allocated",0) or 0),
        str(i.get("disbursed",0) or 0),
        sql_str(i.get("status","") or ""),
        str(h.get("allocated",0) or 0),
        str(h.get("disbursed",0) or 0),
        sql_str(h.get("status","") or ""),
    ]
    lines.append(
        "INSERT INTO universities (id,name_ar,name_en,postdoc_r,postdoc_allocated,"
        "postdoc_disbursed,postdoc_launched,postdoc_status,infra_allocated,"
        "infra_disbursed,infra_status,hqr_allocated,hqr_disbursed,hqr_status) "
        f"VALUES ({','.join(vals)});"
    )

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Wrote {OUT} — {len(data)} rows, {OUT.stat().st_size} bytes")
