# agent notes — datavorous.github.io

this file is for future claude instances working on this portfolio. read it before making changes.

---

## what this site is

a personal portfolio for sagnik bhattacharjee (handle: datavorous). cs student, class of 2029. the site is intentionally minimal — pure html/css, no js, no frameworks. it should stay that way unless there's a strong reason not to.

---

## file structure

```
index.html          — the entire site. one page.
index.css           — all styles.
llms.txt            — structured summary for ai agents (keep in sync with index.html changes)
robots.txt          — allows all ai crawlers, disallows /old/
sitemap.xml         — only indexes the homepage
media/
  iiith.jpg         — iiit hyderabad logo (downloaded from linkedin, do not re-fetch)
  stealth.jpg       — generic stealth startup logo (used for all undisclosed employers)
  me.jpg            — profile photo (not yet added, placeholder in html)
old/                — old content, disallowed from indexing, do not link to
```

---

## voice and writing style

- **proper capitalization** in all visible text. sentence case for prose (capitalize sentence starts, the pronoun "i" -> "I", and proper nouns), acronyms uppercase (npu -> NPU, vtcm -> VTCM, gpu -> GPU, llm -> LLM, etc.), brands/orgs in their real casing (Qualcomm, GitHub, Micron, BuyMeACoffee). headings use sentence case, not title case. job titles use title case (Research Intern, SDE Intern). this REPLACED the old all-lowercase aesthetic (changed jun 2026 at the user's request) — do not revert to all-lowercase.
- **stays lowercase**: the handle `datavorous`, the email/urls, and lowercase-branded repo names (sameshi, spheni, dunefetch, yars). these are proper names that are styled lowercase.
- **no em dashes** (`—`) in visible site text. use a regular hyphen (`-`) instead. (llms.txt is machine-facing and keeps its existing em dashes.)
- **terse**. say less. if a sentence can be shorter, make it shorter.
- **narrative over lists** where possible. the writeups and project descriptions are prose, not bullets.
- **no over-explanation**. don't justify choices or add context that isn't needed.
- **first person** (`i`, not `the author`). informal but not sloppy.

---

## sections and their purpose

### header
name + alias + nav links + profile photo (avatar). nav links use favicons from google's service. on small screens, nav labels are hidden — only favicons show. resume link has no favicon.

### bio / experience
short 2-line intro followed by an `experience` h2 and a list of internships. each entry has:
- a logo (30px square, rounded)
- role · org (inline)
- date on its own line (below)
- focus description on its own line (below date)

all employer logos come from `media/`. undisclosed startups use `media/stealth.jpg`. do not use external logo urls — they expire.

### writeups
a single narrative paragraph with inline links. the spotify playlist line sits below it as a muted note. this section is prose, not a list.

### projects
a short narrative intro followed by exactly 3 featured projects (sameshi, spheni, dunefetch) with inline social proof (hn, reddit callouts). below the list, a single `writeup-prose` paragraph collapses the rest of the github repos and mentions yars as the most-used.

### webring
a wrapping list of friends' sites, each with their favicon. currently 17 members. format: favicon + name, no descriptions.

---

## css conventions

- font: `DM Sans`, 19px, light warm feel
- inline `code` uses `--code-inline` (a darker rose than `--code-bg`) so it stands out; `pre` blocks keep `--code-bg`
- `h2`/`h3` no longer force `text-transform: lowercase`, and `.webring-label` is no longer uppercase — capitalization comes from the html now
- max-width: `680px` on `main`, centered with `margin: 0 auto`
- background: warm cream gradient on `html` (`#fffcf7 → #fef4e2`), fixed
- selection color: `#ffd166` (yellow)
- **no dark mode** — was removed because favicons have white rings that look bad on dark backgrounds
- em dashes in css content are fine (e.g. `::before`/`::after`), only remove them from visible text

### key classes
- `.fav` — inline favicon images (1em, vertical-align, border-radius 3px)
- `.exp-logo` — employer logos (30px square, rounded border)
- `.exp-text` — flex container for role/org/date/focus
- `.exp-date` — own line, tabular nums
- `.exp-focus` — own line, muted, small
- `.writeup-prose` — narrative paragraph style (0.9rem, line-height 1.8)
- `.section-note` — small muted supplementary line
- `.nav-label` — text label in nav links, hidden on mobile (≤540px)
- `.webring-links` — wrapping flex list of webring members

---

## favicons

always use google's favicon service:
```
https://www.google.com/s2/favicons?domain=DOMAIN&sz=16
```
add `class="fav"` to all favicon images. use `alt=""` (decorative).

---

## ai/crawler files

if content changes significantly, update `llms.txt` to match. it is the primary document ai agents read. keep it accurate and concise. the sitemap only lists the homepage — do not add `/old/` paths or subpages unless the user explicitly wants them indexed.

---

## things to never do

- add dark mode (removed deliberately)
- use em dashes in visible text
- revert visible text to all-lowercase (the site now uses proper capitalization)
- force `text-transform: lowercase/uppercase` on headings or labels
- add javascript
- link to anything inside `/old/`
- add verbose descriptions or over-explain anything
- use `display: block` or `margin: auto` on `.fav` images (breaks inline layout)
- re-fetch employer logos from linkedin urls (they expire — use the saved local files)
