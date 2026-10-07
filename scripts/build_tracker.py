#!/usr/bin/env python3
"""Merge discovered roles into tracker/applications.json and build tracker/dashboard.html.

usage: build_tracker.py            # merge tracker/discovered_*.json (new ids only) + rebuild dashboard
       build_tracker.py --summary  # also print the daily summary
Existing rows keep their status/notes; discovery only adds new ids.
"""
import datetime as dt
import glob
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APPS = os.path.join(ROOT, "tracker", "applications.json")
STATUSES = ["Found", "Tailored", "Ready", "Applied", "Messaged", "Replied", "Interview", "Offer", "Rejected", "Skipped"]
FIELDS = ["id", "company", "role", "source", "jd_url", "apply_url", "ats", "location", "remote", "stipend", "ppo",
          "posted_date", "role_category", "fit_score", "fit_reason", "flags", "status", "date_found", "date_applied",
          "tailored_resume", "match_score", "cover_letter", "contact", "messaged_on", "follow_up_due", "notes"]


def load(path, default):
    try:
        return json.load(open(path))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def merge():
    apps = load(APPS, [])
    known = {a["id"] for a in apps}
    today = dt.date.today().isoformat()
    added = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "tracker", "discovered_*.json"))):
        for j in load(f, []):
            if j.get("id") in known:
                continue
            row = {k: j.get(k) for k in FIELDS}
            row.update(status="Found", date_found=today, notes=j.get("notes") or "")
            apps.append(row)
            known.add(row["id"])
            added += 1
    # fold in tailoring results (tracker/results/<id>.json); results never downgrade a later status
    by_id = {a["id"]: a for a in apps}
    later = {"Ready", "Applied", "Messaged", "Replied", "Interview", "Offer", "Rejected"}
    for f in sorted(glob.glob(os.path.join(ROOT, "tracker", "results", "*.json"))):
        res = load(f, None)
        row = res and by_id.get(res.get("id"))
        if not row:
            continue
        if row.get("status") not in later:
            row["status"] = res.get("status", row.get("status"))
        row["tailored_resume"] = res.get("tailored_resume")
        row["match_score"] = res.get("match_score")
        row["cover_letter"] = res.get("cover_letter")
        flags = res.get("eligibility_flags") or []
        note = res.get("notes") or ""
        row["notes"] = " · ".join(x for x in [note, ("Eligibility: " + "; ".join(flags)) if flags else ""] if x)
    json.dump(apps, open(APPS, "w"), indent=1, ensure_ascii=False)
    return apps, added


def summary(apps):
    today = dt.date.today()
    by = {s: sum(1 for a in apps if a.get("status") == s) for s in STATUSES}
    due = [a for a in apps if a.get("follow_up_due") and a["follow_up_due"] <= today.isoformat()
           and a.get("status") in ("Applied", "Messaged")]
    ready = [a for a in apps if a.get("status") == "Ready"]
    asks = [a for a in apps if "ASK" in (a.get("notes") or "")]
    lines = [f"Daily summary, {today}",
             "Pipeline: " + ", ".join(f"{s} {n}" for s, n in by.items() if n),
             f"Applied today: {sum(1 for a in apps if a.get('date_applied') == today.isoformat())}",
             f"Messages sent today: {sum(1 for a in apps if a.get('messaged_on') == today.isoformat())}",
             f"Replies: {by['Replied']}, interviews: {by['Interview']}, offers: {by['Offer']}",
             f"Needs you: {len(ready)} ready to submit, {len(due)} follow-ups due, {len(asks)} with open questions"]
    for a in ready[:15]:
        lines.append(f"  - SUBMIT: {a['company']}, {a['role']} -> {a.get('apply_url')}")
    for a in due:
        lines.append(f"  - FOLLOW UP: {a['company']} ({a.get('contact')})")
    return "\n".join(lines)


def dashboard(apps):
    esc = lambda s: html.escape(str(s if s is not None else ""))  # noqa: E731
    counts = {s: sum(1 for a in apps if a.get("status") == s) for s in STATUSES}
    order = {s: i for i, s in enumerate(["Ready", "Tailored", "Found", "Applied", "Messaged", "Replied",
                                         "Interview", "Offer", "Rejected", "Skipped"])}
    rows = sorted(apps, key=lambda a: (order.get(a.get("status"), 99), -(a.get("match_score") or 0), -(a.get("fit_score") or 0)))
    trs = []
    for a in rows:
        resume = a.get("tailored_resume") or ""
        rel = os.path.relpath(os.path.join(ROOT, resume), os.path.join(ROOT, "tracker")) if resume else ""
        trs.append(
            f"<tr data-status='{esc(a.get('status'))}' data-cat='{esc(a.get('role_category'))}'>"
            f"<td><b>{esc(a.get('company'))}</b></td><td>{esc(a.get('role'))}</td>"
            f"<td><span class='pill s-{esc(a.get('status'))}'>{esc(a.get('status'))}</span></td>"
            f"<td class='num'>{esc(a.get('match_score') or '')}</td><td class='num'>{esc(a.get('fit_score') or '')}</td>"
            f"<td>{esc(a.get('location'))}{' · Remote' if a.get('remote') else ''}</td>"
            f"<td>{esc(a.get('stipend') or '')}</td><td>{esc(a.get('ppo') or '')}</td><td>{esc(a.get('source'))}</td>"
            f"<td>{'<a href=' + chr(39) + esc(a.get('jd_url')) + chr(39) + ' target=_blank>JD</a>' if a.get('jd_url') else ''}"
            f"{' · <a href=' + chr(39) + esc(a.get('apply_url')) + chr(39) + ' target=_blank>Apply</a>' if a.get('apply_url') else ''}</td>"
            f"<td>{'<a href=' + chr(39) + esc(rel.replace('.json', '.pdf')) + chr(39) + '>PDF</a>' if resume else ''}</td>"
            f"<td>{esc(a.get('date_applied') or '')}</td><td>{esc(a.get('contact') or '')}</td>"
            f"<td>{esc(a.get('follow_up_due') or '')}</td><td class='notes'>{esc(a.get('notes') or '')}</td></tr>")
    tiles = "".join(f"<button class='tile' data-f='{s}'><span>{counts[s]}</span>{s}</button>" for s in STATUSES)
    page = f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Internship Tracker</title><style>
:root{{--bg:#f7f7f5;--fg:#1a1a1a;--mut:#666;--card:#fff;--line:#e3e3e0;--acc:#2f5bd3}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151515;--fg:#eee;--mut:#999;--card:#1e1e1e;--line:#333;--acc:#7da2ff}}}}
body{{margin:0;padding:16px;font:14px/1.4 -apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--fg)}}
h1{{font-size:20px;margin:0 0 4px}} .mut{{color:var(--mut)}}
.tiles{{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}}
.tile{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 12px;color:var(--fg);cursor:pointer;font:inherit}}
.tile span{{display:block;font-size:20px;font-weight:600}} .tile.on{{border-color:var(--acc);outline:1px solid var(--acc)}}
input{{padding:8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg);width:min(360px,100%)}}
.wrap{{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:8px;margin-top:10px}}
table{{border-collapse:collapse;width:100%;min-width:1100px}} th,td{{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{position:sticky;top:0;background:var(--card);font-size:12px;color:var(--mut);cursor:pointer}} .num{{text-align:right;font-variant-numeric:tabular-nums}}
.notes{{max-width:280px;font-size:12px;color:var(--mut)}} a{{color:var(--acc)}}
.pill{{padding:2px 8px;border-radius:99px;font-size:12px;border:1px solid var(--line);white-space:nowrap}}
.s-Ready{{border-color:#d08a00}} .s-Applied,.s-Messaged{{border-color:var(--acc)}} .s-Interview,.s-Offer,.s-Replied{{border-color:#1f9d55}} .s-Skipped,.s-Rejected{{opacity:.6}}
</style></head><body>
<h1>Internship Tracker</h1><div class='mut'>Updated {dt.datetime.now():%Y-%m-%d %H:%M} · {len(apps)} opportunities · rebuild with <code>python3 scripts/build_tracker.py</code></div>
<div class='tiles'>{tiles}</div>
<input id='q' placeholder='Filter by company, role, location…'>
<div class='wrap'><table><thead><tr><th>Company</th><th>Role</th><th>Status</th><th>Match</th><th>Fit</th><th>Location</th><th>Stipend</th><th>PPO</th><th>Source</th><th>Links</th><th>Resume</th><th>Applied</th><th>Contact</th><th>Follow-up</th><th>Notes</th></tr></thead>
<tbody>{''.join(trs)}</tbody></table></div>
<script>
let f=null;const q=document.getElementById('q');
function apply(){{const t=q.value.toLowerCase();document.querySelectorAll('tbody tr').forEach(r=>{{r.style.display=((!f||r.dataset.status===f)&&r.innerText.toLowerCase().includes(t))?'':'none'}})}}
document.querySelectorAll('.tile').forEach(b=>b.onclick=()=>{{f=f===b.dataset.f?null:b.dataset.f;document.querySelectorAll('.tile').forEach(x=>x.classList.toggle('on',x.dataset.f===f));apply()}});
q.oninput=apply;
document.querySelectorAll('th').forEach((th,i)=>th.onclick=()=>{{const tb=document.querySelector('tbody');const rs=[...tb.rows];const num=th.classList.contains('num')||i===3||i===4;
rs.sort((a,b)=>{{const x=a.cells[i].innerText,y=b.cells[i].innerText;return num?(+y||0)-(+x||0):x.localeCompare(y)}});rs.forEach(r=>tb.appendChild(r))}});
</script></body></html>"""
    open(os.path.join(ROOT, "tracker", "dashboard.html"), "w").write(page)


if __name__ == "__main__":
    apps, added = merge()
    dashboard(apps)
    print(f"merged {added} new; {len(apps)} total")
    if "--summary" in sys.argv:
        print(summary(apps))
