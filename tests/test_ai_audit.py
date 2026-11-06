import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.dirname(__file__) + '/..')
spec = importlib.util.spec_from_file_location('aia', os.path.join(ROOT, 'scripts/ai-audit.py'))
aia = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aia)

FIXTURE = os.path.join(ROOT, 'projects/job-search/interviews/mplc-2026-11-06/mplc-audit-spec.json')


def sample_spec():
    return json.load(open(FIXTURE, encoding='utf-8'))


class RenderRules(unittest.TestCase):
    def test_onepager_escapes_dangerous_text(self):
        s = sample_spec()
        s['positioning_quote'] = '<script>alert(1)</script>'
        html = aia.build_onepager(s)
        self.assertNotIn('<script>alert', html)
        self.assertIn('&lt;script&gt;', html)

    def test_state_pill_colours(self):
        s = sample_spec()
        s['ratings'] = [{'domain': 'x', 'state': 0, 'evidence': 'e'}]
        rows = aia.ratings_rows(s)
        self.assertIn('pill b0', rows)
        s['ratings'] = [{'domain': 'x', 'state': 3, 'evidence': 'e'}]
        rows = aia.ratings_rows(s)
        self.assertIn('pill b2', rows)

    def test_string_state_label_defaults_amber(self):
        s = sample_spec()
        s['ratings'] = [{'domain': 'x', 'state': '1–2', 'evidence': 'e'}]
        rows = aia.ratings_rows(s)
        self.assertIn('pill b1', rows)
        self.assertIn('1–2', rows)

    def test_onepager_renders_strategic_twist_when_present(self):
        html = aia.build_onepager(sample_spec())
        self.assertIn('The strategic twist', html)

    def test_opportunities_grouped_by_horizon(self):
        s = sample_spec()
        html = aia.build_full(s)
        self.assertIn('Opportunities — Now 0–90d', html)
        self.assertIn('Opportunities — Next 3–12m', html)
        self.assertIn('Opportunities — Beyond 12m', html)

    def test_optional_sections_absent_without_error(self):
        s = sample_spec()
        s.pop('strategic')
        s.pop('risks')
        s.pop('business_model')
        for html in (aia.build_onepager(s), aia.build_full(s)):
            self.assertNotIn('strategic twist', html)
            self.assertNotIn('Risks', html)

    def test_business_model_header_uses_first_row(self):
        s = sample_spec()
        html = aia.build_onepager(s)
        self.assertIn('<th>Element</th>', html)
        self.assertNotIn('<th>Core product</th>', html)

    def test_full_doc_contains_all_core_sections(self):
        html = aia.build_full(sample_spec())
        for marker in ('Current-state assessment', 'Governance', 'First 90 days', 'Method and honest limits'):
            self.assertIn(marker, html)

    def test_blank_spec_sets_company_and_valid_json(self):
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        r = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts/ai-audit.py'), 'spec',
                            '--company', 'Acme Widgets', '--out', path],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        data = json.load(open(path))
        self.assertEqual(data['company'], 'Acme Widgets')
        os.unlink(path)

    def test_missing_chrome_explains_instead_of_crashing(self):
        with patch.object(aia.os.path, 'exists', lambda p: False):
            with self.assertRaises(SystemExit) as ctx:
                aia.chrome_pdf('/tmp/x.html', '/tmp/x.pdf')
        self.assertIn('Chrome', str(ctx.exception))


class ServeRules(unittest.TestCase):
    def setUp(self):
        sp = importlib.util.spec_from_file_location(
            'audit_page', os.path.join(ROOT, 'scripts', 'dashboard', 'audit_page.py'))
        self.ap = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(self.ap)

    def test_page_embeds_default_spec(self):
        html = self.ap.page_html()
        self.assertIn('"company": "MPLC"', html)

    def test_page_has_no_double_percent_css_bug(self):
        self.assertNotIn('%%', self.ap.page_html())

    def test_render_kind_and_validation(self):
        s = sample_spec()
        self.assertIn('<!DOCTYPE html>', self.ap.render(s, 'onepager'))
        self.assertIn('Opportunities —', self.ap.render(s, 'full'))
        with self.assertRaises(ValueError) as ctx:
            self.ap.render(s, 'slide')
        self.assertIn('unknown kind', str(ctx.exception))
        broken = dict(s)
        broken.pop('sources')
        with self.assertRaises(ValueError) as ctx:
            self.ap.render(broken, 'onepager')
        self.assertIn('sources', str(ctx.exception))
        with self.assertRaises(ValueError) as ctx:
            self.ap.render(['not', 'a', 'dict'], 'onepager')
        self.assertIn('JSON object', str(ctx.exception))

    def test_handle_render_size_guard_runs_before_parse(self):
        big = (json.dumps(sample_spec()) + ' ' * 300_000).encode()
        with self.assertRaises(ValueError) as ctx:
            self.ap.handle_render(big)
        self.assertIn('too large', str(ctx.exception))

    def test_handle_render_bad_json(self):
        with self.assertRaises(Exception):
            self.ap.handle_render(b'{oops')


if __name__ == '__main__':
    unittest.main()
