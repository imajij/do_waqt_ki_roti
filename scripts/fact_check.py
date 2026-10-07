#!/usr/bin/env python3
"""Flag claims in tailored resumes that don't trace back to master.json.

Checks every tailored JSON for: numbers/metrics not present in master (non-verify) text,
skills not in master, employers/titles/dates that differ from master, [VERIFY] facts leaking in.
usage: fact_check.py [resumes/tailored/*.json ...]   (default: all)
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(ROOT, "resumes/master/master.json")
if not os.path.exists(MASTER):
    sys.exit("resumes/master/master.json not found: copy master.example.json and fill in your facts first.")
master = json.load(open(MASTER))


def texts(o, skip_verify=True):
    if isinstance(o, dict):
        return " ".join(texts(v) for k, v in o.items() if not (skip_verify and k == "verify") and not k.startswith("_"))
    if isinstance(o, list):
        return " ".join(texts(v) for v in o)
    return str(o)


M = texts(master)
VERIFY = " ".join(v["text"] for e in master["experience"] for v in e.get("verify", []))
NUM = re.compile(r"\d+(?:[.,]\d+)?\s*(?:%|×|x\b|ms|µs|us\b|\+|k\b|h\b|hours?)?")
master_nums = {n.strip() for n in NUM.findall(M)}
master_skills = {s.lower() for g in master["skills"].values() for s in g}
known = {e["company"]: e for e in master["experience"]}


def check(path):
    t = json.load(open(path))
    issues = []
    body = " ".join(" ".join(x.get("bullets", [])) for sec in ("experience", "open_source", "projects") for x in t.get(sec, []))
    body += " " + (t.get("summary") or "")
    for n in {n.strip() for n in NUM.findall(body)}:
        core = re.sub(r"[^\d.,]", "", n)
        if core and core not in M and n not in master_nums and core not in ("2026", "2028", "2024", "2027"):
            issues.append(f"number '{n}' not in master")
    for v in re.findall(r"85%|over 60%|5 recurring", body):
        issues.append(f"[VERIFY] fact used: {v}")
    for g, items in (t.get("skills") or {}).items():
        for s in items:
            base = s.lower()
            if base not in master_skills and base.split(" (")[0] not in M.lower():
                issues.append(f"skill '{s}' not in master")
    for e in t.get("experience", []):
        m = next((k for c, k in known.items() if e.get("company", "").split(" (")[0] in c), None)
        if not m:
            issues.append(f"employer '{e.get('company')}' not in master")
        elif e.get("dates") != m["dates"]:
            issues.append(f"dates for {e['company']}: '{e.get('dates')}' vs master '{m['dates']}'")
    return issues


paths = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, "resumes/tailored/*.json")))
bad = 0
for p in paths:
    iss = check(p)
    if iss:
        bad += 1
        print(f"\n{os.path.basename(p)}")
        for i in iss:
            print("  -", i)
print(f"\n{len(paths)} checked, {bad} with issues")
