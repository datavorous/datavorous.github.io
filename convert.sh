#!/usr/bin/env sh
set -eu

content_dir="${1:-archive/content}"
output_dir="${2:-.}"
stylesheet="style.css"
css_version="$(cksum "$stylesheet" | awk '{print $1}')"

content_dir="${content_dir%/}"
output_dir="${output_dir%/}"
[ -n "$content_dir" ] || content_dir="archive/content"
[ -n "$output_dir" ] || output_dir="."

if [ ! -d "$content_dir" ]; then
  printf 'content directory not found: %s\n' "$content_dir" >&2
  exit 1
fi

if ! command -v cmark >/dev/null 2>&1; then
  printf 'cmark is required to build the site\n' >&2
  exit 1
fi

mkdir -p "$output_dir"

if [ "$(realpath "$output_dir")" != "$(pwd -P)" ]; then
  cp "$stylesheet" "$output_dir/$stylesheet"
fi

html_escape() {
  printf '%s' "$1" |
    sed \
      -e 's/&/\&amp;/g' \
      -e 's/</\&lt;/g' \
      -e 's/>/\&gt;/g' \
      -e 's/"/\&quot;/g'
}

field() {
  key="$1"
  src="$2"
  awk -v key="$key:" '
    BEGIN { in_fm = 0 }
    NR == 1 && $0 == "---" { in_fm = 1; next }
    in_fm && $0 == "---" { exit }
    in_fm && index(tolower($0), tolower(key)) == 1 {
      sub(/^[^:]*:[[:space:]]*/, "")
      print
      exit
    }
  ' "$src"
}

body_html() {
  awk '
    NR == 1 && $0 == "---" { fm = 1; next }
    fm && $0 == "---" { fm = 0; next }
    !fm { print }
  ' "$1" | cmark --unsafe
}

first_heading() {
  awk '
    /^#{1,6}[[:space:]]+/ {
      sub(/^#{1,6}[[:space:]]+/, "")
      print
      exit
    }
  ' "$1"
}

filter_html() {
  sed \
    -e 's/\.md"/.html"/g' \
    -e 's/href="x\.com\//href="https:\/\/x.com\//g' \
    -e 's/href="github\.com\//href="https:\/\/github.com\//g' \
    -e 's/href="substack\.com\//href="https:\/\/substack.com\//g' \
    -e 's/href="linkedin\.com\//href="https:\/\/linkedin.com\//g' \
    -e 's/href="datavorous\.com\//href="https:\/\/datavorous.com\//g' |
    sed -E \
      -e 's#<li>(<a href="[^"]+">[^<]+</a>) \(([A-Z][a-z]+ [0-9]{1,2}, [0-9]{4})\)</li>#<li>\1 <span class="date">(\2)</span></li>#' \
      -e 's#<li>(<a href="[^"]+">[^<]+</a>) ([A-Z][a-z]+ [0-9]{1,2}, [0-9]{4})</li>#<li>\1 <span class="date">\2</span></li>#'
}

is_home() {
  [ "$1" = "$content_dir/index.md" ] || [ "$1" = "./$content_dir/index.md" ]
}

render_page() {
  src="$1"
  rel="${src#"$content_dir"/}"
  out="$output_dir/${rel%.md}.html"
  mkdir -p "$(dirname "$out")"

  title="$(field title "$src")"
  if [ -z "$title" ]; then
    title="$(first_heading "$src")"
  fi
  title="${title:-datavorous}"
  subtitle="$(field subtitle "$src")"
  date="$(field date "$src")"
  author="$(field author "$src")"
  image="$(field image "$src")"
  description="$(field description "$src")"
  canonical_url="https://datavorous.com/${rel%index.md}"
  og_type="website"
  case "$rel" in writing/*/index.md) og_type="article" ;; esac
  title_html="$(html_escape "$title")"
  subtitle_html="$(html_escape "$subtitle")"
  date_html="$(html_escape "$date")"
  author_html="$(html_escape "$author")"
  image_html="$(html_escape "$image")"
  description_html="$(html_escape "$description")"
  has_front_matter=0
  case "$(sed -n '1p' "$src")" in
    ---) has_front_matter=1 ;;
  esac
  home_href="$(realpath --relative-to="$(dirname "$out")" "$output_dir/index.html")"
  css_href="$(realpath --relative-to="$(dirname "$out")" "$output_dir/$stylesheet")?v=$css_version"
  body="$(body_html "$src" | filter_html)"

  {
    printf '<!doctype html>\n'
    printf '<html lang="en">\n'
    printf '<head>\n'
    printf '<meta charset="utf-8">\n'
    printf '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
    printf '<title>%s</title>\n' "$title_html"
    printf '<meta name="description" content="%s">\n' "$description_html"
    printf '<link rel="canonical" href="%s">\n' "$canonical_url"
    printf '<meta property="og:type" content="%s">\n' "$og_type"
    printf '<meta property="og:title" content="%s">\n' "$title_html"
    printf '<meta property="og:description" content="%s">\n' "$description_html"
    printf '<meta property="og:url" content="%s">\n' "$canonical_url"
    printf '<link rel="stylesheet" href="%s">\n' "$css_href"
    printf '<script defer src="https://cloud.umami.is/script.js" data-website-id="e63babdf-cd85-4481-ba03-cebb2ac1e44b"></script>\n'
    if is_home "$src"; then
      printf '<meta name="google-site-verification" content="RM0Usoor9mkR_B6WmiJ-G83wdgVEesVfr3Z_ET0CRPs" />\n'
    fi
    case "$rel" in
      writing/raytracer/index.md|writing/garbage-collector/index.md)
        printf '<script defer src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>\n'
        printf '<script defer src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>\n'
        ;;
    esac
    printf '</head>\n'
    printf '<body>\n'
    if is_home "$src"; then
      printf '<main><article class="home">\n'
    else
      printf '<nav class="top"><a href="%s">Home</a><a href="mailto:hi@datavorous.com">Email</a></nav>\n' "$home_href"
      if [ "$rel" = "writing/index.md" ]; then
        printf '<main><article class="writing-index">\n'
      else
        printf '<main><article>\n'
      fi
      if [ "$has_front_matter" -eq 1 ] && [ "$rel" != "writing/index.md" ]; then
        case "$rel" in
          writing/*/index.md) printf '<header class="article-header">\n' ;;
          *) printf '<header>\n' ;;
        esac
      printf '<h1>%s</h1>\n' "$title_html"
      if [ -n "$subtitle" ]; then
        printf '<p class="dek">%s</p>\n' "$subtitle_html"
      fi
      case "$rel" in
        writing/*/index.md)
          [ -z "$date" ] || printf '<p class="meta">%s</p>\n' "$date_html"
          ;;
        *)
          if [ -n "$date" ] || [ -n "$author" ]; then
            printf '<p class="meta">'
            [ -z "$date" ] || printf '%s' "$date_html"
            [ -z "$date" ] || [ -z "$author" ] || printf ' / '
            [ -z "$author" ] || printf '%s' "$author_html"
            printf '</p>\n'
          fi
          ;;
      esac
      if [ -n "$image" ]; then
        printf '<img class="hero" src="%s" alt="%s">\n' "$image_html" "$title_html"
      fi
        printf '</header>\n'
      fi
    fi
    printf '%s\n' "$body"
    case "$rel" in
      writing/*/index.md)
        printf '</article>\n<nav class="article-back" aria-label="Writing"><a href="../">Back to writing</a></nav>\n</main>\n'
        ;;
      *) printf '</article></main>\n' ;;
    esac
    printf '</body>\n'
    printf '</html>\n'
  } > "$out"

  printf '%s -> %s\n' "$src" "$out"
}

find "$content_dir" -type f ! -name '*.md' ! -name 'convert.sh' -print | while IFS= read -r asset; do
  rel="${asset#"$content_dir"/}"
  mkdir -p "$output_dir/$(dirname "$rel")"
  cp "$asset" "$output_dir/$rel"
done

find "$content_dir" -name '*.md' -type f | sort | while IFS= read -r src; do
  render_page "$src"
done
