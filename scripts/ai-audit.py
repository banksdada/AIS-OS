#!/usr/bin/env python3
"""AI Adoption Audit renderer — the repeatable audit tool.

Takes a JSON spec of research findings and renders a print-ready audit:
a one-page A4 summary (HTML) and the full document (HTML), optionally
exported to PDF via headless Chrome.

Usage:
    python3 scripts/ai-audit.py render --spec spec.json --out-dir OUT [--pdf]
    python3 scripts/ai-audit.py spec --company "Acme Ltd"   # writes a blank spec

The judgement stays with the analyst; the tool guarantees every audit ships
with the same structure, the same evidence discipline and the same finish.
"""
import argparse, datetime, json, os, subprocess, sys

STATE_PILL = {'0': 'b0', '1': 'b0', '2': 'b1', '3': 'b2'}
BLANK = {
    'company': 'ACME LTD',
    'title': 'AI Adoption Audit',
    'prepared_by': 'Banks Dada',
    'date': datetime.date.today().isoformat(),
    'positioning_quote': 'Company phrase or policy anchor the audit hangs on.',
    'method_note': 'Built from public information only. Every current-state claim carries an evidence tag; every inference is labelled. Where evidence is thin, the finding is framed as a question.',
    'why_now': 'One paragraph: why this company, why this moment.',
    'business_model': [['Element', 'How it works', 'Evidence'], ['Core product', '…', '…']],
    'ratings': [{'domain': 'Data platform', 'state': 0, 'evidence': '…'}],
    'strategic': {'title': 'The strategic twist', 'body': 'The one finding that re-frames AI as revenue, not cost.'},
    'opportunities': [{'horizon': 'Now 0–90d', 'title': '…', 'detail': '…', 'boundary': '…', 'measure': '…'}],
    'governance': ['One-page policy; human sign-off default for anything external'],
    'first90': [{'span': 'D1–30', 'body': 'Floor time; use-case register scored impact/effort/risk'}],
    'risks': ['Transformation stacking', 'Shadow AI'],
    'sources': ['company site', 'job adverts', 'press'],
}

CSS = """
@page { size: A4; margin: 14mm; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Georgia, 'Times New Roman', serif; color: #1c2b45; background: #fff;
  font-size: %(fs)s; line-height: 1.45; padding: %(pad)s; }
header { border-bottom: 3px solid #1c2b45; padding-bottom: 8px; margin-bottom: 10px;
  display: flex; justify-content: space-between; align-items: flex-end; }
h1 { font-size: 17px; } h2 { font-size: 11px; text-transform: uppercase; letter-spacing: 1.1px;
  border-bottom: 1px solid #c9d3e0; margin: 10px 0 5px; padding-bottom: 2px; }
.sub { font-size: 10px; color: #5a6b85; font-style: italic; }
.meta { text-align: right; font-size: 9px; color: #5a6b85; }
.cols { display: flex; gap: 16px; } .col { flex: 1; }
table { width: 100%%; border-collapse: collapse; font-size: 9.5px; }
th, td { text-align: left; padding: 3px 5px; border-bottom: 1px solid #e3e8f0; vertical-align: top; }
th { background: #f0f3f8; font-family: Helvetica, Arial, sans-serif; font-size: 8.5px;
  text-transform: uppercase; letter-spacing: .5px; }
.pill { display: inline-block; padding: 1px 6px; border-radius: 8px; font-family: Helvetica, Arial; font-size: 8px; font-weight: bold; }
.b0 { background: #f6d7d7; color: #7c1f1f; } .b1 { background: #f8e8c8; color: #7a5a10; } .b2 { background: #d9e8d1; color: #2f5d28; }
ul { padding-left: 14px; font-size: 9.8px; } li { margin-bottom: 3px; }
.tag { font-family: Helvetica, Arial; font-weight: bold; font-size: 8.5px; text-transform: uppercase; color: #3d5a8a; }
.quote { font-style: italic; color: #3d5a8a; padding: 5px 8px; border-left: 3px solid #3d5a8a; background: #f4f7fb; margin: 6px 0; font-size: 10px; }
section.block { margin-bottom: 8px; } footer { margin-top: 10px; border-top: 1px solid #c9d3e0; padding-top: 5px;
  font-size: 8.5px; color: #5a6b85; font-family: Helvetica, Arial; }
"""


def esc(t):
    return str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def header_html(spec):
    return f"""<header><div><h1>{esc(spec['title'])} — {esc(spec['company'])}</h1>
<div class="sub">An external, evidence-based discovery map · Prepared by {esc(spec['prepared_by'])} · {esc(spec['date'])}</div></div>
<div class="meta">Public sources only · Ratings are discovery questions, not verdicts</div></header>"""


def ratings_rows(spec):
    out = []
    for r in spec['ratings']:
        pill = STATE_PILL.get(str(r['state']), 'b1')
        out.append(f"<tr><td>{esc(r['domain'])}</td><td><span class='pill {pill}'>{esc(r['state'])}</span></td><td>{esc(r['evidence'])}</td></tr>")
    return '\n'.join(out)


def opp_rows(spec):
    out = []
    for o in spec['opportunities']:
        out.append(f"<tr><td class='tag'>{esc(o['horizon'])}</td><td><b>{esc(o['title'])}</b> — {esc(o['detail'])}</td>"
                   f"<td>{esc(o['boundary'])}</td><td>{esc(o['measure'])}</td></tr>")
    return '\n'.join(out)


def bm_html(spec, heading):
    if not spec.get('business_model'):
        return ''
    rows = ['<tr>' + ''.join(f'<th>{esc(c)}</th>' for c in spec['business_model'][0]) + '</tr>']
    for r in spec['business_model'][1:]:
        rows.append('<tr>' + ''.join(f'<td>{esc(c)}</td>' for c in r) + '</tr>')
    return f"<h2>{heading}</h2><table>{''.join(rows)}</table>" if heading != 'Business model snapshot' else f"<section class='block'><h2>{heading}</h2><table>{''.join(rows)}</table></section>"


def gov_html(spec, full=False):
    items = ''.join(f'<li>{esc(g)}</li>' for g in spec['governance'])
    h = 'Governance for a consent business' if not full else 'Governance'
    wrap = (lambda inner: f"<section class='block'><h2>{h}</h2><ul>{inner}</ul></section>") if full else (lambda inner: f"<h2>{h}</h2><ul>{inner}</ul>")
    return wrap(items)


def d90_html(spec, full=False):
    items = ''.join(f"<li><span class='tag'>{esc(d['span'])}</span> {esc(d['body'])}</li>" for d in spec['first90'])
    wrap = (lambda inner: f"<section class='block'><h2>First 90 days</h2><ul>{inner}</ul></section>") if full else (lambda inner: f"<h2>First 90 days in the seat</h2><ul>{inner}</ul>")
    return wrap(items)


def risks_html(spec, full=False):
    if not spec.get('risks'):
        return ''
    items = ''.join(f'<li>{esc(r)}</li>' for r in spec['risks'])
    wrap = (lambda inner: f"<section class='block'><h2>Risks &amp; anti-patterns</h2><ul>{inner}</ul></section>") if full else (lambda inner: f"<h2>Risks to name out loud</h2><ul>{inner}</ul>")
    return wrap(items)


def build_onepager(spec):
    strat = ''
    if spec.get('strategic'):
        strat = (f"<h2>The strategic twist</h2><ul><li><span class='tag'>AI as product, not just cost</span> — "
                 f"{esc(spec['strategic']['body'])}</li></ul>")
    return f"""<!DOCTYPE html><html lang="en-GB"><head><meta charset="UTF-8"><title>{esc(spec['title'])} — {esc(spec['company'])}</title>
<style>{CSS % {'fs': '10.5px', 'pad': '16px 20px'}}</style></head><body>
{header_html(spec)}
<div class="quote">{esc(spec['positioning_quote'])}</div>
<div class="cols"><div class="col">
<h2>Where {esc(spec['company'])} stands today</h2>
<table><tr><th>Domain</th><th>State</th><th>Public evidence</th></tr>
{ratings_rows(spec)}</table>
{bm_html(spec, 'Business model')}{strat}</div>
<div class="col">
<h2>Priority moves</h2>
<table><tr><th></th><th>Move</th><th>Human boundary</th><th>Measure</th></tr>
{opp_rows(spec)}</table>
{gov_html(spec)}{d90_html(spec)}{risks_html(spec)}</div></div>
<footer>Built from: {esc(' · '.join(spec['sources']))} — methodology: evidence in, assumptions labelled, humans in the loop, everything measured. {esc(spec['prepared_by'])}</footer>
</body></html>"""


def build_full(spec):
    paras = ''
    for key, heading in [('method_note', 'Method and honest limits'), ('why_now', 'Why now is the right moment')]:
        if spec.get(key):
            paras += f"<section class='block'><h2>{heading}</h2><p style='font-size:10px'>{esc(spec[key])}</p></section>"
    strat = ''
    if spec.get('strategic'):
        strat = (f"<section class='block'><h2>{esc(spec['strategic']['title'])}</h2>"
                 f"<p style='font-size:10px'>{esc(spec['strategic']['body'])}</p></section>")
    opps = {}
    for o in spec['opportunities']:
        opps.setdefault(o['horizon'], []).append(o)
    opp_html = ''
    for horizon, items in opps.items():
        rows = '\n'.join(f"<tr><td><b>{esc(o['title'])}</b><br>{esc(o['detail'])}</td><td>{esc(o['boundary'])}</td><td>{esc(o['measure'])}</td></tr>" for o in items)
        opp_html += (f"<section class='block'><h2>Opportunities — {esc(horizon)}</h2>"
                     f"<table><tr><th>Move</th><th>Human boundary</th><th>Measure</th></tr>{rows}</table></section>")
    ratings = f"<section class='block'><h2>Current-state assessment</h2><table><tr><th>Domain</th><th>State</th><th>Evidence &amp; reasoning</th></tr>{ratings_rows(spec)}</table></section>"
    srcs = f"<footer>Built from: {esc(' · '.join(spec['sources']))}</footer>"
    return f"""<!DOCTYPE html><html lang="en-GB"><head><meta charset="UTF-8"><title>{esc(spec['title'])} — full</title>
<style>{CSS % {'fs': '11px', 'pad': '18px 22px'}}</style></head><body>
{header_html(spec)}{paras}{bm_html(spec, 'Business model snapshot')}{ratings}{strat}{opp_html}{gov_html(spec, True)}{d90_html(spec, True)}{risks_html(spec, True)}{srcs}</body></html>"""


def chrome_pdf(html_path, pdf_path):
    candidates = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
    ]
    chrome = next((c for c in candidates if os.path.exists(c)), None)
    if not chrome:
        raise SystemExit('Chrome not found — open the HTML and print to PDF instead')
    subprocess.run([chrome, '--headless', '--disable-gpu', '--no-pdf-header-footer',
                    f'--print-to-pdf={pdf_path}', 'file://' + os.path.abspath(html_path)],
                   check=True, capture_output=True, timeout=120)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('render')
    r.add_argument('--spec', required=True)
    r.add_argument('--out-dir', required=True)
    r.add_argument('--pdf', action='store_true')
    s = sub.add_parser('spec')
    s.add_argument('--company', required=True)
    s.add_argument('--out', default=None)
    args = p.parse_args()

    if args.cmd == 'spec':
        blank = json.loads(json.dumps(BLANK))
        blank['company'] = args.company
        dest = args.out or f'ai-audit-{args.company.lower().replace(" ", "-")}.json'
        json.dump(blank, open(dest, 'w', encoding='utf-8'), indent=1)
        print(f'blank spec -> {dest}')
        return

    spec = json.load(open(args.spec, encoding='utf-8'))
    os.makedirs(args.out_dir, exist_ok=True)
    outputs = []
    for name, builder in [('audit-onepager.html', build_onepager), ('audit-full.html', build_full)]:
        path = os.path.join(args.out_dir, name)
        open(path, 'w', encoding='utf-8').write(builder(spec))
        outputs.append(path)
        print('wrote', path)
    if args.pdf:
        for html in outputs:
            pdf = html.replace('.html', '.pdf')
            chrome_pdf(html, pdf)
            print('wrote', pdf)


if __name__ == '__main__':
    main()
