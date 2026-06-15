#!/usr/bin/env python3
"""Generate JSON data files for tender lens frontend."""

import sqlite3
import json
import re
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
MACRO_DB = BASE / "macrotender.db"
DETAILS_DB = BASE / "tender_details.db"

def parse_emd(emd_str):
    """Parse EMD string like '1,00,000.00' or 'Rs. 1,00,000' to float."""
    if not emd_str or emd_str.strip() in ('', '-', 'NA', 'N/A', 'nil', 'Nil', 'NIL', '0'):
        return 0.0
    s = re.sub(r'[^\d.]', '', emd_str.replace(',', ''))
    try:
        return float(s) if s else 0.0
    except:
        return 0.0

def parse_date(date_str):
    """Parse date like '29-May-2026 06:25 PM' or '29-May-2026'."""
    if not date_str or date_str.strip() in ('', '-', 'NA'):
        return None
    s = date_str.strip()
    for fmt in ('%d-%b-%Y %I:%M %p', '%d-%b-%Y', '%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt)
        except:
            pass
    return None

def fmt_date(dt):
    if dt is None:
        return ''
    return dt.strftime('%d %b %Y')

def fmt_emd(val):
    if val == 0:
        return '0'
    if val >= 1e7:
        return f'{val/1e7:.2f}Cr'
    if val >= 1e5:
        return f'{val/1e5:.2f}L'
    return f'{val:.0f}'

print("Connecting to databases...")
macro_conn = sqlite3.connect(MACRO_DB)
details_conn = sqlite3.connect(DETAILS_DB)
macro_conn.row_factory = sqlite3.Row
details_conn.row_factory = sqlite3.Row

# ---- data_stats.json ----
print("Generating stats...")
mc = macro_conn.cursor()
mc.execute("SELECT COUNT(*) as cnt FROM tenders")
total_macro = mc.fetchone()['cnt']
mc.execute("SELECT COUNT(*) as cnt FROM tenders WHERE source_status='active'")
active_count = mc.fetchone()['cnt']
mc.execute("SELECT COUNT(*) as cnt FROM tenders WHERE source_status='archived'")
archived_count = mc.fetchone()['cnt']

dc = details_conn.cursor()
dc.execute("SELECT COUNT(*) as cnt FROM tender_details")
total_details = dc.fetchone()['cnt']

# top category from details
dc.execute("SELECT details_json FROM tender_details")
cat_counts = {}
for row in dc.fetchall():
    try:
        d = json.loads(row['details_json'])
        cat = d.get('Product Category', '').strip()
        if cat and cat not in ('', '-', 'NA'):
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
    except:
        pass
top_category = max(cat_counts, key=cat_counts.get) if cat_counts else ''

stats = {
    'total_macro': total_macro,
    'total_details': total_details,
    'active_count': active_count,
    'archived_count': archived_count,
    'top_category': top_category
}
(BASE / 'data_stats.json').write_text(json.dumps(stats))
print(f"  stats: {stats}")

# ---- Load all detail rows ----
print("Loading tender details...")
dc.execute("SELECT internal_id, tender_id, details_json, scraped_at FROM tender_details")
all_details = []
for row in dc.fetchall():
    try:
        d = json.loads(row['details_json'])
        d['_internal_id'] = row['internal_id']
        d['_tender_id'] = row['tender_id']
        all_details.append(d)
    except:
        pass
print(f"  loaded {len(all_details)} detail records")

# ---- data_single.json ----
print("Generating single-source tenders...")
singles = []
for d in all_details:
    ttype = d.get('Tender Type', '').strip()
    if 'single' not in ttype.lower():
        continue
    emd_val = parse_emd(d.get('EMD *', ''))
    pub_dt = parse_date(d.get('ePublished Date', ''))
    bid_end_dt = parse_date(d.get('Bid Submission End Date', ''))
    days_to_close = None
    if pub_dt and bid_end_dt:
        days_to_close = (bid_end_dt - pub_dt).days
    singles.append({
        'org': d.get('Organisation Name', '').strip(),
        'title': d.get('Tender Title', '').strip(),
        'emd': emd_val,
        'emd_fmt': fmt_emd(emd_val),
        'ttype': ttype,
        'pub_date': fmt_date(pub_dt),
        'bid_end': fmt_date(bid_end_dt),
        'location': d.get('Location', '').strip(),
        'ref_num': d.get('Tender Reference Number', '').strip(),
        'tender_id': d.get('_tender_id', ''),
        'days': days_to_close
    })
singles.sort(key=lambda x: x['emd'], reverse=True)
(BASE / 'data_single.json').write_text(json.dumps(singles[:200]))
print(f"  single-source: {len(singles)} found, saved top 200")

# ---- data_rush.json ----
print("Generating rush job tenders...")
rush = []
for d in all_details:
    pub_dt = parse_date(d.get('ePublished Date', ''))
    bid_end_dt = parse_date(d.get('Bid Submission End Date', ''))
    if not pub_dt or not bid_end_dt:
        continue
    days = (bid_end_dt - pub_dt).days
    if days < 0 or days > 7:
        continue
    emd_val = parse_emd(d.get('EMD *', ''))
    rush.append({
        'org': d.get('Organisation Name', '').strip(),
        'title': d.get('Tender Title', '').strip(),
        'emd': emd_val,
        'emd_fmt': fmt_emd(emd_val),
        'days': days,
        'pub_date': fmt_date(pub_dt),
        'bid_end': fmt_date(bid_end_dt),
        'ttype': d.get('Tender Type', '').strip(),
        'tender_id': d.get('_tender_id', '')
    })
rush.sort(key=lambda x: x['emd'], reverse=True)
(BASE / 'data_rush.json').write_text(json.dumps(rush[:200]))
print(f"  rush jobs: {len(rush)} found, saved top 200")

# ---- data_orgs.json ----
print("Generating org counts from macrotender...")
mc.execute("""
    SELECT organisation_name, COUNT(*) as total,
           SUM(CASE WHEN source_status='active' THEN 1 ELSE 0 END) as active
    FROM tenders
    WHERE organisation_name IS NOT NULL AND organisation_name != ''
    GROUP BY organisation_name
    ORDER BY total DESC
    LIMIT 50
""")
orgs = [{'org': r['organisation_name'], 'total': r['total'], 'active': r['active'] or 0}
        for r in mc.fetchall()]
(BASE / 'data_orgs.json').write_text(json.dumps(orgs))
print(f"  orgs: {len(orgs)}")

# ---- data_sectors.json ----
print("Generating sector breakdown...")
sectors = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
sectors_out = [{'category': k, 'count': v} for k, v in sectors[:60]]
(BASE / 'data_sectors.json').write_text(json.dumps(sectors_out))
print(f"  sectors: {len(sectors_out)}")

# ---- data_search.json ----
print("Generating search index...")
search = []
for d in all_details:
    emd_val = parse_emd(d.get('EMD *', ''))
    pub_dt = parse_date(d.get('ePublished Date', ''))
    bid_end_dt = parse_date(d.get('Bid Submission End Date', ''))
    search.append({
        'id': d.get('_internal_id', ''),
        'org': d.get('Organisation Name', '').strip(),
        'title': d.get('Tender Title', '').strip(),
        'emd': emd_val,
        'emd_fmt': fmt_emd(emd_val),
        'ttype': d.get('Tender Type', '').strip(),
        'category': d.get('Product Category', '').strip(),
        'location': d.get('Location', '').strip(),
        'pub_date': fmt_date(pub_dt),
        'bid_end': fmt_date(bid_end_dt),
        'tender_id': d.get('_tender_id', '')
    })
(BASE / 'data_search.json').write_text(json.dumps(search[:5000]))
print(f"  search: {len(search[:5000])} records")

macro_conn.close()
details_conn.close()
print("Done.")
