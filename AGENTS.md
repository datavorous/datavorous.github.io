# Site design rules

The site uses a white page, neutral grays, blue and purple links, system sans serif text, and monospace code. The tokens in `style.css` are the source of truth.

Reading pages use a `72ch` outer width. Side padding leaves roughly 65–70 characters of text per line on desktop; the column contracts with the viewport and font size. Main spacing uses 8, 16, 24, 32, and 48px steps. Use smaller increments only inside dense charts and diagrams.

| Role | Rule |
| --- | --- |
| Reading text | System sans serif, 16px, 1.6 line height |
| Page title | System sans serif, 32px, medium weight |
| Homepage name | System sans serif, 36–48px, medium weight |
| Section heading | System sans serif, 24px, medium weight |
| Subsection heading | System sans serif, 18px, medium weight |
| Navigation | System sans serif, 15px |
| Dates, metadata, labels | System sans serif, 14px, quiet gray |
| Code | System monospace |

Use one `h1` for each page title. Use `h2` for main sections and `h3` for sections within them. Keep links underlined so they remain identifiable in the grayscale palette.

| Color role | Value | Usage |
| --- | --- | --- |
| Paper | `#fff` | Page background |
| Ink | `#242424` | Main text and headings |
| Quiet | `#5c5c5c` | Dates, metadata, secondary text |
| Faint | `#767676` | Labels and small markers |
| Postscript | `#494949` | Closing notes after the horizontal rule; links stay blue |
| Rule | `#d6d6d6` | Dividers and borders |
| Wash | `#f4f4f4` | Code blocks and diagrams |
| Link | `#245b90` | Unvisited links |
| Link hover | `#174772` | Hover and keyboard focus |
| Visited | `#66507b` | Visited links |
