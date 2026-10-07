# Outreach templates

Rules:
- Personalize line 1 every time, using something real about the person, their team, or the product.
- Name the exact role you applied for.
- Give one proof point taken from your master resume.
- Keep connection notes ≤ 300 characters and DMs ≤ 600.
- Send only after you've submitted the application.
- Send one follow-up after about 7 days. Never send a second one.

`{proof}` means one concrete, true achievement from `resumes/master/master.json`, mapped to the job description.

---

## A. Connection note: engineer on the team (≤300 chars)
> Hi {first}, I saw {specific: your talk/post/PR/team's launch of X}. I just applied for the {role} at {company}. I {proof}. Would love to connect and learn how your team works.

## B. Connection note: recruiter or TA (≤300 chars)
> Hi {first}, I applied for the {role} ({job id/link}) at {company}. I'm a {degree} student at {school} ('{grad year}) with experience in {stack}. I can start {availability}. Happy to share anything that helps your review.

## C. Connection note: alumni (≤300 chars)
> Hi {first}, fellow {school} student here ('{grad year}). I applied for {company}'s {role}. I {proof}. I'd love to hear how you found the move to {company}.

## D. DM after connecting: hiring manager (≤600 chars)
> Hi {first}, thanks for connecting. I applied for {role} because {specific reason tied to their product or stack}. Most relevant from my side: {proof mapped to the JD}. Resume and code: {portfolio} · {github}. If it's useful, I'd value 10 minutes to hear what the team needs most from an intern this quarter.

## E. Follow-up after about 7 days, no reply (once only)
> Hi {first}, a quick follow-up on my {role} application. Since applying I've {small real update}. Still very keen on {company}. Thanks for your time either way!

## F. Cold email (when there's a public address)
Subject: {Role} application: {one-line strongest proof}

> Hi {first},
>
> {One specific line about their product or engineering.} I applied for the {role} on {date}.
>
> - {proof 1 mapped to JD}
> - {proof 2 mapped to JD}
>
> I'm a {degree} student ({school}, '{grad year}) and can start {availability}. Resume attached; code at {github}.
>
> Thanks,
> {name} · {portfolio}

---

## Message log format (`sent_log.json`)
`{"date","company","person","person_url","role_applied","channel":"linkedin-connect|linkedin-dm|email","template","text","status":"drafted|approved|sent|replied","follow_up_due"}`
