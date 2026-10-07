# Internship Application Engine

**An AI hiring partner that runs your internship hunt end to end.**

It audits your profiles like a recruiter would, fixes them, finds roles across job boards and company career pages, writes a truthful one-page resume and cover letter for every job, fills in the applications up to the final screen, drafts recruiter outreach, and tracks everything in a dashboard. You review each application and click Submit.

It runs as a **Claude Code skill** plus a handful of small scripts. Nothing here is a hosted service; it all runs on your machine with your own logins.

---

## Contents
1. [What it does](#1-what-it-does)
2. [How it works (architecture)](#2-how-it-works-architecture)
3. [Requirements](#3-requirements)
4. [Installation, step by step](#4-installation-step-by-step)
5. [First run: setting up your profile](#5-first-run-setting-up-your-profile)
6. [The seven phases in detail](#6-the-seven-phases-in-detail)
7. [Daily workflow](#7-daily-workflow)
8. [Folder structure](#8-folder-structure)
9. [Data formats](#9-data-formats)
10. [Scripts reference](#10-scripts-reference)
11. [Safety rules and platform limits](#11-safety-rules-and-platform-limits)
12. [Troubleshooting](#12-troubleshooting)
13. [Sharing this setup and privacy](#13-sharing-this-setup-and-privacy)
14. [FAQ](#14-faq)

---

## 1. What it does

| Phase | Output |
|---|---|
| **1. Hiring-partner audit** | A blunt report covering your resume, LinkedIn, GitHub, and portfolio. Each issue gets "why this gets you rejected", a severity, and the exact fix |
| **2. Optimize** | LinkedIn edits (logged before → after), GitHub cleanup, CI and tests pushed, and a **master resume** that becomes the single source of truth |
| **3. Find roles** | A few dozen live internships matched to your roles, cities, stipend floor and eligibility, with each full job description saved to disk |
| **4. Tailor and apply** | For every job: a one-page tailored resume (PDF), a keyword-match score, a cover letter, and drafted application answers. The form is filled in your browser up to the final Submit |
| **5. Outreach** | Personalized LinkedIn connection notes and DMs for recruiters, hiring managers and engineers, batched for your approval and kept within safe daily limits |
| **6. Tracker** | `tracker/dashboard.html` with every opportunity, its status, match score, resume used, contact and follow-up date, plus a daily summary |
| **7. Memory and skill** | Your preferences and feedback are saved, and the workflow improves as patterns emerge |

**Guarantees**
- **Nothing is invented.** Tailored resumes only select, reorder and reword facts from your master resume. A fact-checker flags any number or skill that doesn't trace back to it.
- **You click Submit.** Claude fills the form and stops at the final screen.
- **Claude asks instead of guessing** on work authorization, salary or CTC, demographics, legal declarations, passwords and addresses.

---

## 2. How it works (architecture)

```
                         ┌──────────────────────────────┐
           you  ───────▶ │  Claude Code + this skill     │  (skill/SKILL.md = the playbook)
                         └──────────────┬───────────────┘
        ┌──────────────────┬────────────┼─────────────────┬──────────────────┐
        ▼                  ▼            ▼                 ▼                  ▼
  gh CLI (GitHub)   ego-lite browser   web search /   parallel sub-agents   local scripts
  audit, CI, pins   (your logins:      public APIs    (discovery, tailoring) (render, score,
  repo cleanup      LinkedIn, Gmail,   Greenhouse,                           fact-check, PDF,
                    Unstop, Workday…)  Lever, Ashby,                         tracker)
                                       LinkedIn guest
        └──────────────────┴────────────┴─────────────────┴──────────────────┘
                                        ▼
            resumes/   outreach/   tracker/   profile-audit/   memory/   DECISIONS.md
```

**The resume pipeline**
```
resumes/master/master.json ──(sub-agent picks and rewords true bullets for one JD)──▶ resumes/tailored/<Co>_<Role>_<date>.json
      │                                                                                  │
      │                                    scripts/score.py  ◀── tracker/jds/<id>.txt ────┤  keyword match: under 70 → improve, under 55 → skip
      │                                    scripts/fact_check.py ◀───────────────────────┤  nothing untraceable to the master
      ▼                                                                                  ▼
scripts/render_resume.py ──▶ .html ──▶ scripts/html2pdf.mjs (browser print, auto-fit to one A4 page) ──▶ .pdf
```

**The application pipeline**
1. Discovery agents write `tracker/discovered_*.json` and `tracker/jds/<id>.txt`.
2. `build_tracker.py` merges them into `tracker/applications.json`, removing duplicates. Every new row starts as `Found`.
3. Tailoring agents run 4–6 at a time in parallel, 5–6 jobs each. They write the tailored JSON and HTML, the cover letter, the answers, and `tracker/results/<id>.json`. Those rows become `Tailored`.
4. Claude renders the PDFs, fact-checks them, and fills each application in the browser. Those rows become `Ready`.
5. You review and click Submit, and Claude marks the row `Applied` with a 7-day follow-up date.
6. Outreach drafts go out after the application, once you approve them. Rows move to `Messaged`, then `Replied`, then `Interview`.

---

## 3. Requirements

### Accounts
| Account | Why | Required? |
|---|---|---|
| **Claude Code** (Claude Pro, Max, Team or Enterprise, or API) | Runs the skill and agents | Yes |
| **LinkedIn** | Profile edits, Easy Apply, outreach, people search | Yes |
| **GitHub** | Profile audit, repo cleanup, pushing CI and tests | Recommended |
| **Gmail** (or any webmail) | Verification codes, Workday account emails, recruiter replies | Recommended |
| Unstop, YC Work at a Startup, Internshala, Wellfound, Instahyre | Platform-specific applications | Optional, as you need them |
| Workday | Created per company during applications (one account per employer) | As needed |

### Software
| Tool | Version tested | Install |
|---|---|---|
| macOS (Linux works with small path changes) | Darwin 25 | — |
| **Claude Code** CLI | latest | `npm install -g @anthropic-ai/claude-code`, or the desktop app |
| **ego-lite browser** + **`ego-browser` CLI and skill** | latest | Install Ego Lite, then confirm `ego-browser --help` works. The skill lives at `~/.claude/skills/ego-browser/`. Claude drives this browser using **your** logged-in sessions |
| **GitHub CLI** `gh` | 2.x | `brew install gh`, then `gh auth login` |
| **Python** | 3.9+ (standard library only, nothing to `pip install`) | Preinstalled on macOS, or `brew install python` |
| **git** | any | Preinstalled with the Xcode CLT |

> **Why ego-lite?** It's a Chromium browser built for agents. Claude works inside your real logged-in sessions, you can watch every action, and you can take control at any time. Claude stops when you do. It's also how PDFs are rendered: Chrome's `Page.printToPDF` gives a clean, ATS-parseable text layer.

### Optional
- `gh auth refresh -h github.com -s user` lets Claude edit your GitHub bio and location from the CLI. Pins still need the browser, signed in to GitHub.
- A password manager. Workday makes you create a separate account for every company.

---

## 4. Installation, step by step

### 4.1 Get the folder
```bash
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/imajij/do_waqt_ki_roti.git internship-engine
cd internship-engine
cp memory/preferences.example.md memory/preferences.md          # fill in, or let Claude do it on first run
cp resumes/master/master.example.json resumes/master/master.json # Claude builds the real one from your resume
```
The `.gitignore` keeps your personal campaign data (resumes, tracker, outreach, audits, preferences) out of git, so pulling template updates never conflicts with your data and you can't push it by accident.

### 4.2 Install the skill into Claude Code
Symlink it so edits to `skill/SKILL.md` take effect immediately:
```bash
mkdir -p ~/.claude/skills
ln -sfn "$PWD/skill" ~/.claude/skills/internship-engine
ls ~/.claude/skills/internship-engine/SKILL.md   # should exist
```
For a single-project install, use `<project>/.claude/skills/internship-engine` instead.

### 4.3 Install and connect the browser
1. Install **Ego Lite** and open it once.
2. Check the CLI from a terminal:
   ```bash
   ego-browser nodejs -e 'const t = await taskSpace("smoke test"); await t.page("p1").goto("https://example.com"); console.log(await t.page("p1").title()); await t.finish({keep:[]});'
   ```
   It should print `Example Domain`.
3. In the Ego Lite window, **log in** to LinkedIn, Gmail and GitHub. Add any other boards you plan to use (Unstop, workatastartup.com).

### 4.4 GitHub CLI
```bash
gh auth login                               # pick SSH or HTTPS
gh auth refresh -h github.com -s user       # optional: lets Claude set your bio and location
gh auth status
```

### 4.5 Verify the scripts
```bash
python3 scripts/render_resume.py --help 2>/dev/null || head -25 scripts/render_resume.py
python3 scripts/score.py 2>&1 | head -3      # prints usage/traceback = OK, script runs
```

### 4.6 Folder skeleton (if starting empty)
```bash
mkdir -p profile-audit resumes/{master,tailored} outreach/{cover_letters/pdf,answers,drafts,posts} tracker/{jds,results} memory skill scripts
echo '[]' > tracker/applications.json
echo '[]' > outreach/sent_log.json
```

---

## 5. First run: setting up your profile

Start Claude Code **inside the folder**:
```bash
cd ~/projects/internship-engine && claude
```
Then give it everything in one message:
```
Run the internship engine for me.
Resume: ~/Downloads/My_Resume.pdf
Portfolio: https://mysite.dev   LinkedIn: linkedin.com/in/me   GitHub: myuser (orgs: X, Y)
Target roles: Backend, Full-Stack, DevOps intern
Locations: Remote, Bengaluru, Pune
Minimum stipend: ₹40,000/month (brand/learning can override)
PPO target: ≥ ₹20 LPA
Graduation: Aug 2028   Start: immediately   Duration: 2–6 months
Dream companies: …   Avoid: …
Work authorization: Indian citizen, no sponsorship needed for India
I will click Submit myself.
```
Claude will:
1. Copy your resume into `resumes/master/` and write `memory/preferences.md`.
2. Run **Phase 1** (the audit) and show you the report in `profile-audit/<date>_audit.md`.
3. **Wait for your approval** before changing anything. You can approve all of it ("fix everything"), or pick by ID ("approve G1, L2–L5; skip P12").

Open questions go into **`DECISIONS.md`**, numbered. Answer them in chat by number ("1 – my title was X; 12 – approved").

---

## 6. The seven phases in detail

### Phase 1: Hiring-partner audit
What gets checked:
- **Resume:** ATS parse (text layer, single column), graduation date, vague bullets versus measurable ones, metrics you can defend, skills backed by bullets, broken links (for example private repos that 404), length, and special characters.
- **LinkedIn**, read in the browser: headline keywords, About, banner, Featured, a description on every role, skills (top 5 plus ~30), Open to Work titles and locations, and consistency with your resume on titles, dates and education.
- **GitHub**, via `gh`: pins, bio, profile README, **secrets committed to public repos** (paths only, values never shown), resume claims versus the actual code, CI and tests on flagship repos, and forks or class work cluttering your profile.
- **Portfolio:** time until real content appears, what a visitor learns in 5 seconds, mobile layout, dead links, a stale resume PDF, OG/SEO tags.

Every issue is written as **Issue | Why it gets you rejected | Severity | Exact fix**, with a "Fix first" list at the top.

### Phase 2: Optimize
- **Master resume:** `resumes/master/master.json` holds every true fact, tagged by role family. Unconfirmed metrics go under `verify` and never reach a tailored resume.
- **LinkedIn**, edited in the browser: intro, About, experience descriptions, skills linked to roles, education, and Open to Work. "Share with network" prompts are always dismissed, so nothing gets posted. Every change is logged in `profile-audit/linkedin-changes.md`.
- **GitHub:**
  - Repos with leaked credentials and class work are made **private**.
  - Untouched forks, and repos serving GitHub Pages or linked from your portfolio, are **archived** instead, so they stay public and no links break. Nothing is deleted.
  - Flagship repos get CI, tests and benchmarks.
  - Topics and descriptions are added, and the profile README is rewritten.
  - Everything is logged in `profile-audit/github-changes.md`.

### Phase 3: Find roles
Sources, highest-yield first:
1. **Public ATS APIs.** These are free, reliable and include the full JD:
   - Greenhouse `boards-api.greenhouse.io/v1/boards/<slug>/jobs?content=true`
   - Lever `api.lever.co/v0/postings/<slug>?mode=json`
   - Ashby `api.ashbyhq.com/posting-api/job-board/<slug>`
2. **LinkedIn guest search** (no login, at most 1 request per second): `linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?...`
3. **Unstop, YC (Work at a Startup), HN "Who is hiring", Wellfound, Instahyre.**
4. Naukri, Indeed and Glassdoor usually block automated access.

Roles are filtered against `memory/preferences.md` (role, city, stipend, eligibility such as graduation batch, work authorization, final-year-only rules), deduplicated, and ranked by fit and recency.

### Phase 4: Tailor and apply
For each job:
1. **Analyze the JD:** required and preferred skills, responsibilities, stack, the exact ATS phrases, and eligibility blockers.
2. **Tailor:** a summary for this company; the 3–4 most relevant experiences and 1–3 projects; bullets reworded into the JD's vocabulary with the facts unchanged; required skills listed first. Education goes right after the summary, because graduation year is a screening filter.
3. **Score** with `scripts/score.py`. Under 70 → add truthful missing keywords. Under 55, or core requirements you don't have → skip it as a poor fit.
4. **Fact-check** with `scripts/fact_check.py`.
5. **Render** to PDF, auto-fit to one A4 page.
6. **Cover letter** (150–220 words, specific to the company) and **answers** to likely form questions. Salary, notice period, work authorization and demographics are marked `ASK CANDIDATE`.
7. **Apply:** Claude opens the form in ego-lite, uploads the tailored PDF, fills every field it can verify, and **stops at Submit**.

| Platform | Claude fills | You do |
|---|---|---|
| Greenhouse / Lever | Name, contact, resume, cover letter, links, education, yes/no availability | Work-auth, visa, demographics, consent → **Submit** |
| LinkedIn Easy Apply | Contact, tailored resume upload, screening questions with truthful answers | **Submit application** |
| YC Work at a Startup | A personal note to the founder | **Send** |
| Unstop | Clicks through to the company's ATS. Native "Quick Apply" submits your Unstop profile in one click, so Claude leaves it for you | Quick Apply → **Submit** |
| Workday | Resume autofill, fixes parser errors, experience, education, contact method | Create an account (password), address, legal questions → **Submit** |
| Keka / SmartRecruiters / others | Everything verifiable | Captcha, gender, current salary → **Submit** |

**Review mode:** the first 5 applications need your explicit approval. After that, Claude prepares applications in batches and you spot-check each one before you submit. Flag a problem and it goes back to full approval mode.

### Phase 5: Outreach
- For each company you've applied to, Claude finds 1–3 people: a recruiter or university recruiter, the hiring manager, and an engineer, preferably alumni of your school.
- Each message references one specific thing about the person or team, names the role, and gives one proof point. Connection notes are 300 characters or fewer.
- Drafts go to `outreach/drafts/` for approval. Once you approve a style, similar messages need less review.
- **Limits:** at most 15–20 messages per day, spaced out, and **only after** the application is submitted. One follow-up after about 7 days, never more.

### Phase 6: Tracker
`tracker/applications.json`, viewed through `tracker/dashboard.html`. Statuses:
`Found → Tailored → Ready → Applied → Messaged → Replied → Interview → Offer / Rejected / Skipped`

### Phase 7: Memory and learning
- `memory/preferences.md`: roles, cities, stipend and PPO, timing, confirmed facts, and approved default answers.
- `memory/feedback.md`: wording you like or dislike, message tone, and what got replies or interviews.
- The "Lessons" section of `skill/SKILL.md` is updated when a pattern or failure shows up.

---

## 7. Daily workflow

```bash
cd ~/projects/internship-engine && claude
```
Then say **"Run today's internship batch."** A typical day:

1. `python3 scripts/build_tracker.py --summary` to see what needs you.
2. Answer anything new in `DECISIONS.md`.
3. Claude finds new roles, tailors the top ones, and fills the forms in your browser.
4. **You submit** the batch, then reply "submitted".
5. Claude marks them Applied, then drafts or sends approved outreach within the daily limit.
6. Follow-ups that are due get a one-time nudge.

Open the dashboard any time: `open tracker/dashboard.html`

---

## 8. Folder structure

```
internship-engine/
├── README.md                  ← this guide
├── DECISIONS.md               ← numbered questions Claude won't guess; answer by number
├── .gitignore                 ← blocks .env / credential files
├── skill/
│   └── SKILL.md               ← the playbook Claude follows (symlinked into ~/.claude/skills)
├── memory/
│   ├── preferences.md         ← roles, cities, stipend, timing, confirmed facts, approved defaults
│   └── feedback.md            ← what you like / what converts
├── profile-audit/
│   ├── <date>_audit.md        ← Phase-1 report
│   ├── linkedin-changes.md    ← every LinkedIn edit, before → after
│   └── github-changes.md      ← every repo made private / archived
├── resumes/
│   ├── master/                ← master.json (source of truth), master.html/.pdf, your original
│   └── tailored/              ← <Company>_<Role>_<YYYY-MM-DD>.json/.html/.pdf, one per job
├── outreach/
│   ├── templates.md           ← connection note / DM / follow-up / cold-email templates
│   ├── cover_letters/         ← <stem>.md  (+ pdf/<stem>_CoverLetter.pdf)
│   ├── answers/               ← <stem>.md  drafted application answers
│   ├── drafts/                ← outreach batches awaiting approval
│   ├── posts/                 ← LinkedIn post drafts for you to publish
│   └── sent_log.json          ← every message sent
├── tracker/
│   ├── applications.json      ← one row per opportunity (the database)
│   ├── dashboard.html         ← generated view (filters, sort, links to PDFs)
│   ├── discovered_*.json      ← raw discovery output
│   ├── jds/<id>.txt           ← full job descriptions (needed for tailoring)
│   └── results/<id>.json      ← tailoring results merged into the tracker
└── scripts/
    ├── render_resume.py       ← JSON → ATS-friendly HTML
    ├── html2pdf.mjs           ← HTML → one-page A4 PDF via the browser
    ├── score.py               ← JD ↔ resume keyword match
    ├── fact_check.py          ← flags anything not traceable to master.json
    ├── build_tracker.py       ← merge discoveries/results, build dashboard, daily summary
    ├── mark.py                ← update a tracker row's status/notes
    └── TAILOR_AGENT_PROMPT.md ← instructions given to each tailoring sub-agent
```

---

## 9. Data formats

### `resumes/master/master.json` (source of truth)
```jsonc
{
  "name": "…", "contact": {"location","phone","email","portfolio","linkedin","github"},
  "headline_options": {"backend": "…", "fullstack": "…", "devops": "…", "fde": "…", "mobile": "…", "swe": "…"},
  "education": [{"school","degree","location","dates","details":[…]}],
  "experience": [{
     "id": "acme", "company": "…", "title": "…", "location": "…", "dates": "Jun 2026 – Present",
     "bullets": [{"text": "…", "tags": ["backend","devops"]}],
     "verify":  [{"text": "unconfirmed metric", "note": "DECISIONS #4"}]   // never used in tailored resumes
  }],
  "open_source": [{"id","name","stack","desc","link","bullets":[…]}],
  "projects":    [{"id","name","stack","desc","link","tags","bullets":[…]}],
  "skills": {"Languages": […], "Backend": […], …}
}
```
Tags: `backend, fullstack, frontend, mobile, devops, fde, ai, rust, swe`.

### Tailored resume (`resumes/tailored/*.json`)
Same idea, flattened: `summary`, `experience[].bullets` (as strings), `open_source`, `projects`, `skills`, `education`, `section_order`. The full schema is documented at the top of `scripts/render_resume.py`.

### Tracker row (`tracker/applications.json`)
```jsonc
{ "id": "stripe-software-engineer-intern", "company": "Stripe", "role": "Software Engineer, Intern",
  "source": "Greenhouse API", "jd_url": "…", "apply_url": "…", "ats": "greenhouse",
  "location": "Bengaluru", "remote": false, "stipend": null, "ppo": null, "posted_date": "2026-10-01",
  "role_category": "swe", "fit_score": 88, "match_score": 100, "flags": ["stipend unknown"],
  "status": "Applied", "date_found": "…", "date_applied": "…", "follow_up_due": "…",
  "tailored_resume": "resumes/tailored/Stripe_SWE-Intern_2026-10-07.json", "cover_letter": "…",
  "contact": "…", "messaged_on": null, "notes": "…" }
```

---

## 10. Scripts reference

| Command | What it does |
|---|---|
| `python3 scripts/render_resume.py resumes/master/master.json resumes/master/master.html --master --unicode` | Renders the master resume. `--master` includes every confirmed bullet, and `--unicode` keeps typographic characters |
| `python3 scripts/render_resume.py <tailored>.json <tailored>.html` | Renders a tailored resume. ASCII-safe by default (`→` becomes `->`, `×` becomes `x`, `−` becomes `-`) for older ATS |
| `ego-browser nodejs < scripts/html2pdf.mjs` | Prints every `{html, pdf}` pair listed in `tracker/.pdf_jobs.json`. Auto-fits to one A4 page (10pt down to 9pt) and reports `pages` and `fontPt`. Run it from the engine folder or set `ENGINE_DIR` |
| `python3 scripts/score.py tracker/jds/<id>.txt <tailored>.json --master resumes/master/master.json` | Keyword match as JSON: `score`, `matched`, `missing`, `missing_but_in_master` (can add truthfully), `true_gaps` (never add) |
| `python3 scripts/fact_check.py [files…]` | Flags numbers, skills, employers or dates in tailored resumes that aren't in the master, and any `[VERIFY]` fact that slipped in |
| `python3 scripts/build_tracker.py [--summary]` | Merges `discovered_*.json` and `results/*.json` into the tracker and rebuilds `dashboard.html`. `--summary` prints the daily summary |
| `python3 scripts/mark.py <id-prefix> <Status> "<note>"` | Updates tracker rows by hand |

Example of the full tailoring loop for one job:
```bash
J=tracker/jds/acme-backend-intern.txt; R=resumes/tailored/Acme_Backend-Intern_2026-10-08
python3 scripts/score.py $J $R.json --master resumes/master/master.json
python3 scripts/fact_check.py $R.json
python3 scripts/render_resume.py $R.json $R.html
echo "[{\"html\":\"$PWD/$R.html\",\"pdf\":\"$PWD/$R.pdf\"}]" > tracker/.pdf_jobs.json
ego-browser nodejs < scripts/html2pdf.mjs
```

---

## 11. Safety rules and platform limits

These come from real incidents during the first run.

| Platform | Limit / behavior | What the engine does |
|---|---|---|
| **LinkedIn** | Automated Easy Apply and DMs are against LinkedIn's user agreement, and fast bursts trigger "We couldn't submit your application" | Claude fills forms but **you click Submit**. Pace is 4–6 Easy Apply forms per batch, and **LinkedIn pauses for the day after about 10 submissions** or the first error. Outreach is at most 15–20 per day, sent only after you've applied |
| **Internshala** | Logged-out scraping from the same network you apply from can get the **account put on hold** (it happened on day 1) | Don't scrape Internshala. Find roles elsewhere, or open listings by hand. If you do get a hold, it often reverts within 24 hours; otherwise email complaints@internshala.com |
| **Workday** | One account per company. **A few wrong passwords lock the account** | Use a password manager. Claude never types passwords. To unlock: "Forgot your password?" or wait 30–60 minutes |
| **Unstop** | "Quick Apply" is a one-click submit of your Unstop profile | Claude never clicks it. "Apply" on external listings just redirects to the company's ATS |
| **Greenhouse / Lever** | Dropdowns often block automated clicks | Claude focuses the field, types, then presses Enter. It always checks the country (+91 vs +246/+591) and the phone number |
| **Resume parsers** (Workday, Keka) | Mangle titles and companies (e.g. a company name replaced by a library name from the bullets) and add junk skills | Claude re-checks every auto-parsed field against the master |
| **Browser tabs** | The browser lets the agent keep **8 tabs** open | Applications go in batches. Submit the batch, then Claude closes those tabs and opens the next |
| **Your clicks** | Clicking inside ego-lite while Claude works hands control to you | Claude stops. Say "continue" when you're done |

**Claude never:** invents a fact, types a password, clicks a final Submit/Send/Quick Apply, posts to your feed, deletes repos, answers demographic, legal or work-authorization questions on its own, or messages anyone before you approve.

---

## 12. Troubleshooting

| Symptom | Fix |
|---|---|
| `ego-browser: command not found` | Reinstall Ego Lite and check that the CLI is on your `PATH`. See `~/.claude/skills/ego-browser/references/install.md` |
| LinkedIn opens a sign-up page | The Ego Lite profile isn't logged in. Log in inside Ego Lite, not your normal Chrome |
| "A browser permission prompt has appeared" | Dismiss the prompt in Ego Lite, then say "continue" |
| "The user has taken control of this task space" | You clicked in the browser. Say "continue" when you're done |
| A tailored PDF runs to 2 pages | `html2pdf.mjs` shrinks the font to 9pt at most. Beyond that, drop the least relevant role or bullet from the JSON and re-render |
| Every PDF reports `fontPt: 10` even when it overflows | The fit must be measured at A4 width; this is already handled in the current `html2pdf.mjs` |
| Scores of 100 on thin job descriptions | The JD had fewer than 6 recognizable keywords, so the number means little. Judge fit by hand |
| Tailoring agents can't find their JD file | Another agent overwrote `tracker/jds/`. Each agent must write only its own ids. Restore from the agents' scratch copies |
| `gh: This API operation needs the "user" scope` | `gh auth refresh -h github.com -s user` |
| LinkedIn "Featured" links fail to preview | Your site is missing OG tags. Add `og:title`, `og:image` and `og:url` |
| Wrong phone number pre-filled in Easy Apply | LinkedIn reuses the number saved in your account. Fix it under LinkedIn Settings → Contact info |

---

## 13. Sharing this setup and privacy

The engine contains **no credentials**: logins live in your browser and the `gh` keyring. It does contain **personal data**: resumes with your phone and email, your address if you saved it to preferences, job history, and contacts.

**This repo is that clean template.** The `.gitignore` excludes every personal folder. If you keep your own campaign under version control, use a **private** repo for it.

**To build a clean template from a used folder by hand:**
```bash
cp -R internship-engine internship-engine-template && cd internship-engine-template
rm -rf resumes/master/* resumes/tailored/* tracker/*.json tracker/jds/* tracker/results/* \
       outreach/cover_letters/* outreach/answers/* outreach/drafts/* outreach/posts/* \
       profile-audit/* memory/* DECISIONS.md
echo '[]' > tracker/applications.json; echo '[]' > outreach/sent_log.json
grep -rIl -e '@gmail.com' -e '+91' . || echo "clean"
```
Keep `skill/`, `scripts/`, `outreach/templates.md`, `README.md` and `.gitignore`.

---

## 14. FAQ

**Will it apply without me?** No. It prepares and fills applications; you press the final button. That keeps you in control and keeps your accounts within platform rules.

**How many applications a day?** 10–20 high-quality, tailored ones is a realistic, safe pace: about 10 LinkedIn Easy Apply, plus any number on Greenhouse, Lever or Workday.

**Can it lie to beat the ATS?** No. Keywords are only added when a true fact supports them. Gaps are listed (`true_gaps`) so you can close them for real.

**What if my resume has a metric I can't back up?** It goes in `verify` in the master and stays off tailored resumes until you confirm how it was measured.

**Can I use it for full-time roles?** Yes. Change the roles in `memory/preferences.md` and the `headline_options` in your master.

**How do I teach it my style?** Just say "I don't like X" or "this framing got replies". It's written to `memory/feedback.md`, and the defaults in `skill/SKILL.md` are updated.
