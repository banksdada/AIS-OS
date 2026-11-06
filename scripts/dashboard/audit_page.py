"""Serving layer for the AI adoption audit tool (ai-audit.webawesome.co.uk).

Kept separate from scripts/ai-audit.py (the CLI) so both share one renderer.
"""
import importlib.util
import json
import os

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location(
    'ai_audit_cli', os.path.join(_REPO_ROOT, 'scripts', 'ai-audit.py'))
ai_audit_cli = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ai_audit_cli)

MAX_BODY = 200_000
DEFAULT_SPEC_PATH = os.path.join(
    _REPO_ROOT, 'projects', 'job-search', 'interviews',
    'mplc-2026-11-06', 'mplc-audit-spec.json')

PAGE = """<!DOCTYPE html><html lang="en-GB"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Adoption Audit — generator</title>
<style>
 body{font-family:Georgia,serif;background:#f4f6fa;color:#1c2b45;margin:0;padding:24px}
 .wrap{max-width:1100px;margin:0 auto}
 h1{font-size:20px;margin:0 0 4px} .sub{color:#5a6b85;font-style:italic;font-size:12px;margin-bottom:16px}
 .panel{background:#fff;border:1px solid #d7deea;border-radius:8px;padding:14px;margin-bottom:14px}
 textarea{width:100%;height:220px;font:12px/1.4 Menlo,Consolas,monospace;border:1px solid #c9d3e0;
   border-radius:6px;padding:10px;box-sizing:border-box}
 button{font:13px Helvetica,Arial;background:#1c2b45;color:#fff;border:0;border-radius:6px;
   padding:9px 16px;margin-right:8px;cursor:pointer}
 button:hover{background:#3d5a8a} #err{color:#a12626;font-size:13px;min-height:18px;margin:6px 0}
 iframe{width:100%;height:900px;border:1px solid #d7deea;border-radius:8px;background:#fff}
 .how{font-size:12px;color:#5a6b85;margin-top:10px;line-height:1.5}
</style></head><body><div class="wrap">
<h1>AI Adoption Audit — generator</h1>
<div class="sub">Evidence-based discovery map in a JSON spec · one-page A4 and full document out ·
Part of the AIOS at webawesome.co.uk</div>
<div class="panel">
  <textarea id="spec" spellcheck="false">__SPEC__</textarea>
  <div id="err"></div>
  <button onclick="renderDoc('onepager')">One-pager</button>
  <button onclick="renderDoc('full')">Full document</button>
  <button onclick="printFrame()">Print / Save PDF</button>
  <div class="how">Edit the spec (company, ratings, opportunities with human boundaries and
  measures) and render. For a live audit done properly, a human researches every claim first —
  this tool renders the discipline, it does not invent it.</div>
</div>
<div class="panel"><iframe id="out" name="out"></iframe></div>
</div>
<script>
async function renderDoc(kind){
  const err = document.getElementById('err'); err.textContent = '';
  let spec;
  try { spec = JSON.parse(document.getElementById('spec').value); }
  catch (e) { err.textContent = 'Spec is not valid JSON: ' + e.message; return; }
  const r = await fetch('/render', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({kind, spec})});
  const text = await r.text();
  if (!r.ok) { err.textContent = text.slice(0, 300); return; }
  const doc = document.getElementById('out').contentWindow.document;
  doc.open(); doc.write(text); doc.close();
}
function printFrame(){ document.getElementById('out').contentWindow.print(); }
window.addEventListener('load', () => renderDoc('onepager'));
</script></body></html>"""


def load_default_spec():
    try:
        with open(DEFAULT_SPEC_PATH, encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return '{}'


def page_html():
    return PAGE.replace('__SPEC__', load_default_spec())


def render(spec, kind):
    if not isinstance(spec, dict):
        raise ValueError('spec must be a JSON object')
    for field in ('company', 'title', 'ratings', 'opportunities', 'governance', 'first90', 'sources'):
        if field not in spec:
            raise ValueError(f"spec missing required field '{field}'")
    if kind == 'onepager':
        return ai_audit_cli.build_onepager(spec)
    if kind == 'full':
        return ai_audit_cli.build_full(spec)
    raise ValueError(f"unknown kind '{kind}'")


def handle_render(raw_body):
    if len(raw_body) > MAX_BODY:
        raise ValueError('spec too large (200 KB max)')
    data = json.loads(raw_body.decode('utf-8'))
    return render(data.get('spec') or {}, data.get('kind') or 'onepager')
