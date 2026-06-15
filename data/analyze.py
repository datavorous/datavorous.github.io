import sqlite3, json, os
from datetime import datetime
from collections import Counter, defaultdict
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker

# register DM Sans from local fonts
_font_dir = os.path.expanduser('~/.local/share/fonts/dm-sans')
for f in os.listdir(_font_dir):
    if f.endswith('.ttf'):
        try:
            fm.fontManager.addfont(os.path.join(_font_dir, f))
        except Exception:
            pass
matplotlib.rcParams['font.family'] = 'DM Sans'

OUTDIR = os.path.dirname(os.path.abspath(__file__))

BG     = '#fff5f7'
PALE   = '#fce4ed'
ACCENT = '#c2185b'
MUTED  = '#9e8490'
TEXT   = '#1a0f14'
GOLD   = '#f06292'
RED    = '#b71c1c'

MONTHS = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,
          'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}

def parse_date(s):
    if not s: return None
    try:
        parts = s.strip().split()
        d,m,y = parts[0].split('-')
        return datetime(int(y), MONTHS[m], int(d))
    except: return None

def style(fig, ax):
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PALE)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(MUTED)
    ax.spines['bottom'].set_color(MUTED)
    ax.title.set_color(TEXT)
    ax.title.set_fontsize(9)
    ax.title.set_fontweight('500')
    ax.xaxis.label.set_color(MUTED)
    ax.xaxis.label.set_fontsize(8)
    ax.yaxis.label.set_color(MUTED)
    ax.yaxis.label.set_fontsize(8)

def short(s, n=28):
    s = s.lower()
    abbr = {
        'ministry of railways': 'railways',
        'bharat heavy electricals limited': 'bhel',
        'oil and natural gas corporation limited': 'ongc',
        'indian air force': 'air force',
        'indiaNoil': 'ioc',
        'sports authority of india': 'sai',
        'bharat petroleum corporation limited': 'bpcl',
        'department of defence research and development': 'drdo',
        'ihq of mod (army)-(oscc)': 'army (oscc)',
        'council of scientific and industrial research': 'csir',
        'dr. ram manohar lohia hospital': 'rml hospital',
        'directorate of purchase and stores': 'dir. purchase & stores',
        'garden reach shipbuilders and engineers ltd.': 'grse',
        'hindustan urvarak and rasayan limited': 'hurl',
        'ntpc limited': 'ntpc',
        'ihq of mod (navy)': 'navy hq',
        'mangalore refinary and petrochemicals limited': 'mrpl',
        'security printing and minting corp of india ltd': 'spmcil',
        'all india institute of medical sciences-rishikesh': 'aiims rishikesh',
        'department of fertilisers': 'dept. fertilisers',
        'municipal corporation of delhi': 'mcd',
        'delhi development authority': 'dda',
        'defence psus': 'defence psus',
        'ordnance factory board': 'ordnance factories',
        'eastern coalfields limited': 'eastern coalfields',
        'department of posts': 'dept. of posts',
        'south eastern coalfields limited': 'se coalfields',
        'directorate of purchase and stores, dae': 'dir. purchase, dae',
        'border roads organisation': 'border roads',
        'electronics division, bhel': 'bhel electronics',
        'hindustan aeronautics limited': 'hal',
        'food corporation of india': 'fci',
        'western coalfields limited': 'western coalfields',
        'national aluminium company limited,nalco': 'nalco',
        'ihq of mod (army)': 'army hq',
        'department of defence production': 'dept. defence prod.',
    }
    if s in abbr: return abbr[s]
    return s[:n]

con = sqlite3.connect(os.path.join(OUTDIR, 'tender_details.db'))
rows = con.execute('SELECT details_json FROM tender_details').fetchall()
DATA = [json.loads(r[0]) for r in rows]
print(f'loaded {len(DATA)} records')

# 1. bid window histogram
windows = []
for d in DATA:
    pub = parse_date(d.get('ePublished Date',''))
    end = parse_date(d.get('Bid Submission End Date',''))
    if pub and end:
        days = (end - pub).days
        if 0 <= days <= 90:
            windows.append(days)

fig, ax = plt.subplots(figsize=(8, 3.8))
style(fig, ax)
counts, _, patches = ax.hist(windows, bins=list(range(92)), color=ACCENT, alpha=0.75, edgecolor='none')
for i, p in enumerate(patches):
    if i <= 7:
        p.set_facecolor(RED)
        p.set_alpha(0.9)
ax.axvline(7, color=RED, linewidth=1.2, linestyle='--', alpha=0.7)
ax.axvline(21, color=GOLD, linewidth=1.2, linestyle='--', alpha=0.7)
ax.text(3.5, max(counts)*0.95, 'danger zone', color=RED, fontsize=7, ha='center', va='top')
# annotate 21d on the right axis to avoid collision with the tall bar
ax.annotate('21d peak', xy=(21, max(counts)*0.6), xytext=(35, max(counts)*0.75),
            color=GOLD, fontsize=7,
            arrowprops=dict(arrowstyle='->', color=GOLD, lw=0.8),
            va='center')
ax.set_xlabel('days from publish to bid close')
ax.set_ylabel('tenders')
ax.set_title('bid window distribution')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f'{int(x):,}'))
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'plot_bid_window.png'), dpi=150, bbox_inches='tight')
plt.close()
print('plot 1 done')

# 2. tender type breakdown
types = Counter(d.get('Tender Type','unknown') for d in DATA)
labels = ['open/advertised','limited','nat. competitive bid','single','global','other']
vals = [
    types.get('Open/Advertised',0),
    types.get('Limited',0),
    types.get('National Competitive Bid',0),
    types.get('Single',0),
    types.get('Global Tenders',0),
    sum(v for k,v in types.items() if k not in ('Open/Advertised','Limited','National Competitive Bid','Single','Global Tenders'))
]
colors = [ACCENT, GOLD, '#7a9e7e', RED, '#5b8db8', MUTED]

fig, ax = plt.subplots(figsize=(8, 3.2))
style(fig, ax)
total = sum(vals)
bars = ax.barh(labels, vals, color=colors, alpha=0.85, edgecolor='none', height=0.55)
for bar, v in zip(bars, vals):
    pct = v/total*100
    ax.text(bar.get_width() + 80, bar.get_y() + bar.get_height()/2,
            f'{v:,} ({pct:.1f}%)', va='center', fontsize=7.5, color=TEXT)
ax.set_xlabel('tenders')
ax.set_title('tender type breakdown')
ax.set_xlim(0, max(vals)*1.28)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f'{int(x):,}'))
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'plot_tender_types.png'), dpi=150, bbox_inches='tight')
plt.close()
print('plot 2 done')

# 3. single-source by org
single_by_org = Counter(d.get('Organisation Name','') for d in DATA if d.get('Tender Type')=='Single')
top = single_by_org.most_common(15)
orgs = [short(x[0]) for x in top]
cnts = [x[1] for x in top]

fig, ax = plt.subplots(figsize=(8, 4.5))
style(fig, ax)
y = range(len(orgs))
bars = ax.barh(list(y), cnts, color=RED, alpha=0.8, edgecolor='none', height=0.6)
ax.set_yticks(list(y))
ax.set_yticklabels(orgs, fontsize=8)
for bar, v in zip(bars, cnts):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            str(v), va='center', fontsize=8, color=TEXT)
ax.set_xlabel('single-source tenders')
ax.set_title('single-source by org')
ax.invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'plot_single_source_orgs.png'), dpi=150, bbox_inches='tight')
plt.close()
print('plot 3 done')

# 4. EMD vs bid window scatter
pairs_emd, pairs_days, pairs_type = [], [], []
for d in DATA:
    emd = float(d.get('EMD *',0) or 0)
    pub = parse_date(d.get('ePublished Date',''))
    end = parse_date(d.get('Bid Submission End Date',''))
    ttype = d.get('Tender Type','')
    if pub and end and emd > 0:
        days = (end - pub).days
        if 0 < days <= 120 and emd < 2e9:
            pairs_emd.append(emd)
            pairs_days.append(days)
            pairs_type.append(ttype)

fig, ax = plt.subplots(figsize=(8, 4.2))
style(fig, ax)
colors_scatter = [RED if t=='Single' else ACCENT if d<=7 else MUTED
                  for t, d in zip(pairs_type, pairs_days)]
sizes = [20 if t=='Single' else 8 for t in pairs_type]
ax.scatter(pairs_days, pairs_emd, c=colors_scatter, s=sizes, alpha=0.35, edgecolors='none')
ax.axvline(7, color=RED, linewidth=1, linestyle='--', alpha=0.6)
ax.text(7.5, max(pairs_emd)*0.9, '7d', color=RED, fontsize=7)
ax.set_xlabel('bid window (days)')
ax.set_ylabel('emd')
ax.set_title('emd vs bid window')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(
    lambda x,_: f'{x/1e7:.0f}Cr' if x>=1e7 else f'{x/1e5:.0f}L' if x>=1e5 else f'{x:.0f}'))
p1 = mpatches.Patch(color=RED, alpha=0.8, label='single-source')
p2 = mpatches.Patch(color=ACCENT, alpha=0.8, label='rush (<=7d)')
p3 = mpatches.Patch(color=MUTED, alpha=0.8, label='other')
ax.legend(handles=[p1,p2,p3], fontsize=7.5, framealpha=0.5)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'plot_emd_vs_window.png'), dpi=150, bbox_inches='tight')
plt.close()
print('plot 4 done')

# 5. top sectors by EMD total
sector_emd = defaultdict(float)
for d in DATA:
    cat = d.get('Product Category','').strip() or 'unknown'
    emd = float(d.get('EMD *',0) or 0)
    sector_emd[cat] += emd

top_sectors = sorted(sector_emd.items(), key=lambda x:-x[1])[:12]
sec_labels = [x[0].lower()[:30] for x in top_sectors]
sec_vals = [x[1]/1e7 for x in top_sectors]

fig, ax = plt.subplots(figsize=(8, 4.8))
style(fig, ax)
y = range(len(sec_labels))
bars = ax.barh(list(y), sec_vals, color=GOLD, alpha=0.85, edgecolor='none', height=0.6)
ax.set_yticks(list(y))
ax.set_yticklabels(sec_labels, fontsize=8)
for bar, v in zip(bars, sec_vals):
    ax.text(bar.get_width() + max(sec_vals)*0.01, bar.get_y() + bar.get_height()/2,
            f'{v:.0f}Cr', va='center', fontsize=7.5, color=TEXT)
ax.set_xlabel('total emd (crore)')
ax.set_title('emd by sector')
ax.invert_yaxis()
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'plot_sector_emd.png'), dpi=150, bbox_inches='tight')
plt.close()
print('plot 5 done')

# 6. zero-EMD rate by org type
otype_zero = defaultdict(lambda: [0,0])
for d in DATA:
    ot = d.get('Organisation Type','unknown')
    emd = float(d.get('EMD *',0) or 0)
    otype_zero[ot][1] += 1
    if emd == 0:
        otype_zero[ot][0] += 1

short_otypes = {
    'Central Govt. Ministry/Department': 'central govt.',
    'Public Sector Undertakings': 'psus',
    'Public Sector Banks': 'public banks',
    'Autonomous Bos': 'autonomous bodies',
    'Other Govt. Organization': 'other govt.',
}

fig, ax = plt.subplots(figsize=(8, 3.0))
style(fig, ax)
otypes = [(short_otypes.get(k, k.lower()), v[0]/v[1]*100, v[1]) for k,v in otype_zero.items() if v[1]>10]
otypes.sort(key=lambda x:-x[1])
labs = [x[0] for x in otypes]
pcts = [x[1] for x in otypes]
cnts2 = [x[2] for x in otypes]
bars = ax.barh(labs, pcts, color=ACCENT, alpha=0.8, edgecolor='none', height=0.45)
for bar, v, n in zip(bars, pcts, cnts2):
    ax.text(bar.get_width()+0.5, bar.get_y()+bar.get_height()/2,
            f'{v:.1f}% (n={n:,})', va='center', fontsize=7.5, color=TEXT)
ax.set_xlabel('% with zero emd')
ax.set_title('zero-emd rate by org type')
ax.set_xlim(0, 110)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'plot_zero_emd_by_orgtype.png'), dpi=150, bbox_inches='tight')
plt.close()
print('plot 6 done')

# 7. active vs archived top orgs
con2 = sqlite3.connect(os.path.join(OUTDIR, 'macrotender.db'))
macro_rows = con2.execute(
    "SELECT organisation_name, source_status, COUNT(*) FROM tenders GROUP BY organisation_name, source_status"
).fetchall()
org_stats = defaultdict(lambda: {'active':0,'archived':0})
for org, status, cnt in macro_rows:
    org_stats[org][status] = cnt

big_orgs = [(org, v['active'], v['archived']) for org,v in org_stats.items()
            if v['active']+v['archived'] > 5000]
big_orgs.sort(key=lambda x: -x[1]/(x[1]+x[2]+1))
top20 = big_orgs[:20]

fig, ax = plt.subplots(figsize=(8, 5.5))
style(fig, ax)
labels20 = [short(x[0]) for x in top20]
active20 = [x[1] for x in top20]
archive20 = [x[2] for x in top20]
y = range(len(labels20))
ax.barh(list(y), active20, color=ACCENT, alpha=0.85, edgecolor='none', height=0.55, label='active')
ax.barh(list(y), archive20, left=active20, color=MUTED, alpha=0.45, edgecolor='none', height=0.55, label='archived')
ax.set_yticks(list(y))
ax.set_yticklabels(labels20, fontsize=7.5)
ax.set_xlabel('tender count')
ax.set_title('active vs archived by org')
ax.legend(fontsize=7.5, framealpha=0.5)
ax.invert_yaxis()
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f'{int(x):,}'))
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'plot_active_vs_archived.png'), dpi=150, bbox_inches='tight')
plt.close()
print('plot 7 done')

# 8. rush tenders by emd bucket
rush = []
for d in DATA:
    pub = parse_date(d.get('ePublished Date',''))
    end = parse_date(d.get('Bid Submission End Date',''))
    emd = float(d.get('EMD *',0) or 0)
    if pub and end:
        days = (end-pub).days
        if 0 < days <= 7:
            rush.append((days, emd))

emd_buckets = ['zero', '<1L', '1L-10L', '10L-1Cr', '>1Cr']
bucket_counts = [0,0,0,0,0]
for _, emd in rush:
    if emd == 0: bucket_counts[0] += 1
    elif emd < 1e5: bucket_counts[1] += 1
    elif emd < 1e6: bucket_counts[2] += 1
    elif emd < 1e7: bucket_counts[3] += 1
    else: bucket_counts[4] += 1

fig, ax = plt.subplots(figsize=(7, 3.2))
style(fig, ax)
bar_colors = [MUTED, '#d4a84b', GOLD, ACCENT, RED]
bars = ax.bar(emd_buckets, bucket_counts, color=bar_colors, alpha=0.85, edgecolor='none', width=0.55)
for bar, v in zip(bars, bucket_counts):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+5, str(v),
            ha='center', fontsize=8.5, color=TEXT)
ax.set_ylabel('tenders')
ax.set_title(f'rush tenders by emd ({len(rush):,} total, window <=7d)')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f'{int(x):,}'))
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, 'plot_rush_emd_buckets.png'), dpi=150, bbox_inches='tight')
plt.close()
print('plot 8 done')

print('\nall plots saved to', OUTDIR)
