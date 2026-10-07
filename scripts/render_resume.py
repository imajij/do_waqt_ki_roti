#!/usr/bin/env python3
"""Render a resume JSON (tailored schema) to ATS-friendly single-column HTML.

Tailored schema:
{
  "name": str, "contact": {location, phone, email, portfolio, linkedin, github},
  "summary": str,
  "experience":  [{"company","title","location","dates","bullets":[str]}],
  "open_source": [{"name","stack","desc","link","bullets":[str]}],
  "projects":    [{"name","stack","desc","link","bullets":[str]}],
  "skills": {"Group": [str, ...]},
  "education": [{"school","degree","location","dates","details":[str]}],
  "section_order": ["summary","experience","open_source","projects","skills","education"]
}

usage: render_resume.py in.json out.html [--master] [--unicode]
  --master   input is resumes/master/master.json: include every non-[VERIFY] bullet
  --unicode  keep typographic characters (default converts to ASCII for older ATS parsers)
"""
import html
import json
import sys

ASCII_MAP = {
    "→": "->", "−": "-", "×": "x", "–": "-", "—": "-", "µ": "u", "’": "'", "‘": "'",
    "“": '"', "”": '"', "…": "...", "·": "|", "≥": ">=", "≤": "<=", " ": " ",
}

SECTION_TITLES = {
    "summary": "Summary", "experience": "Experience", "open_source": "Open Source",
    "projects": "Projects", "skills": "Technical Skills", "education": "Education",
}

CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
body { font-family: Helvetica, Arial, sans-serif; color: #111; font-size: var(--fs, 10pt); line-height: 1.3;
       margin: 0; padding: 0.42in 0.5in; }
h1 { font-size: 19pt; margin: 0 0 2px; text-align: center; letter-spacing: 0.5px; }
.contact { text-align: center; font-size: 9.2pt; margin-bottom: 6px; }
h2 { font-size: 10.5pt; text-transform: uppercase; letter-spacing: 0.6px; border-bottom: 1px solid #222;
     margin: 9px 0 4px; padding-bottom: 1px; }
.row { display: flex; justify-content: space-between; gap: 12px; }
.entry { margin-bottom: 5px; }
.entry .head { font-weight: bold; }
.entry .sub { font-style: italic; }
.right { white-space: nowrap; }
ul { margin: 1px 0 0 0; padding-left: 15px; }
li { margin: 0 0 1.5px; }
.summary { margin: 0; }
.skills p { margin: 0 0 1.5px; }
"""


def clean(s, ascii_mode):
    if s is None:
        return ""
    if ascii_mode:
        for k, v in ASCII_MAP.items():
            s = s.replace(k, v)
    return html.escape(s)


def master_to_tailored(m):
    def bl(items):
        return [b["text"] for b in items]

    return {
        "name": m["name"],
        "contact": m["contact"],
        "summary": m["headline_options"]["swe"],
        "experience": [
            {k: e[k] for k in ("company", "title", "location", "dates")} | {"bullets": bl(e["bullets"])}
            for e in m["experience"]
        ],
        "open_source": [
            {k: p.get(k) for k in ("name", "stack", "desc", "link")} | {"bullets": bl(p["bullets"])}
            for p in m["open_source"]
        ],
        "projects": [
            {k: p.get(k) for k in ("name", "stack", "desc", "link")} | {"bullets": bl(p["bullets"])}
            for p in m["projects"]
        ],
        "skills": m["skills"],
        "education": m["education"],
        "section_order": ["summary", "experience", "open_source", "projects", "skills", "education"],
    }


def render(r, ascii_mode=True):
    c = lambda s: clean(s, ascii_mode)  # noqa: E731
    ct = r["contact"]
    contact_bits = [ct.get(k) for k in ("location", "phone", "email", "portfolio", "linkedin", "github") if ct.get(k)]
    out = [f"<!doctype html><html><head><meta charset='utf-8'><title>{c(r['name'])} - Resume</title>"
           f"<style>{CSS}</style></head><body>",
           f"<h1>{c(r['name'])}</h1>",
           f"<div class='contact'>{' | '.join(c(b) for b in contact_bits)}</div>"]

    def section(key):
        if key == "summary" and r.get("summary"):
            out.append(f"<h2>{SECTION_TITLES[key]}</h2><p class='summary'>{c(r['summary'])}</p>")
        elif key == "experience" and r.get("experience"):
            out.append(f"<h2>{SECTION_TITLES[key]}</h2>")
            for e in r["experience"]:
                out.append("<div class='entry'><div class='row'>"
                           f"<span class='head'>{c(e['title'])} | {c(e['company'])}</span>"
                           f"<span class='right'>{c(e['dates'])}</span></div>")
                if e.get("location"):
                    out.append(f"<div class='sub'>{c(e['location'])}</div>")
                out.append("<ul>" + "".join(f"<li>{c(b)}</li>" for b in e["bullets"]) + "</ul></div>")
        elif key in ("open_source", "projects") and r.get(key):
            out.append(f"<h2>{SECTION_TITLES[key]}</h2>")
            for p in r[key]:
                meta = " | ".join(x for x in (p.get("stack"), p.get("desc")) if x)
                out.append("<div class='entry'><div class='row'>"
                           f"<span><span class='head'>{c(p['name'])}</span> | <span class='sub'>{c(meta)}</span></span>"
                           f"<span class='right'>{c(p.get('link') or '')}</span></div>")
                out.append("<ul>" + "".join(f"<li>{c(b)}</li>" for b in p["bullets"]) + "</ul></div>")
        elif key == "skills" and r.get("skills"):
            out.append(f"<h2>{SECTION_TITLES[key]}</h2><div class='skills'>")
            for g, items in r["skills"].items():
                out.append(f"<p><b>{c(g)}:</b> {c(', '.join(items))}</p>")
            out.append("</div>")
        elif key == "education" and r.get("education"):
            out.append(f"<h2>{SECTION_TITLES[key]}</h2>")
            for e in r["education"]:
                out.append("<div class='entry'><div class='row'>"
                           f"<span class='head'>{c(e['degree'])} | {c(e['school'])}</span>"
                           f"<span class='right'>{c(e['dates'])}</span></div>")
                if e.get("details"):
                    out.append("<ul>" + "".join(f"<li>{c(d)}</li>" for d in e["details"]) + "</ul>")
                out.append("</div>")

    order = list(r.get("section_order") or SECTION_TITLES.keys())
    # interns: education (with graduation date) goes right after the summary
    if "education" in order:
        order.remove("education")
        order.insert(1 if order and order[0] == "summary" else 0, "education")
    for key in order:
        section(key)
    out.append("</body></html>")
    return "\n".join(out)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    src, dst = args
    data = json.load(open(src))
    if "--master" in flags:
        data = master_to_tailored(data)
    open(dst, "w").write(render(data, ascii_mode="--unicode" not in flags))


if __name__ == "__main__":
    main()
