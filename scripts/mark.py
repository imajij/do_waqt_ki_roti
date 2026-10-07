#!/usr/bin/env python3
"""mark.py <id-prefix> <status> "<note>"  — update a tracker row (status + prepend note)."""
import json, os, sys
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tracker", "applications.json")
a = json.load(open(p))
hit = [r for r in a if r["id"].startswith(sys.argv[1]) and r["status"] != "Skipped"]
for r in hit:
    r["status"] = sys.argv[2]
    r["notes"] = sys.argv[3] + " · " + (r.get("notes") or "")
json.dump(a, open(p, "w"), indent=1, ensure_ascii=False)
print([r["id"] for r in hit])
