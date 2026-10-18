import json
import os
import tempfile
import unittest
from unittest.mock import patch

from scripts.dashboard import newsletter_status as ns


class SanitizeTests(unittest.TestCase):
    def test_keeps_counts_and_drops_personal_fields(self):
        raw = {
            'configured': True,
            'buildCount': 2,
            'recipientCount': 40,
            'recipients': ['person@example.com'],
            'projectPath': '/Users/someone/Desktop/newsletter-project',
            'latestBuild': {'file': 'a.html', 'modified': 'today', 'sizeKb': 12, 'path': '/Users/someone/x'},
        }
        clean = ns.sanitize(raw)
        self.assertEqual(clean['recipientCount'], 40)
        self.assertNotIn('recipients', clean)
        self.assertEqual(clean['projectPath'], 'newsletter-project')
        self.assertEqual(set(clean['latestBuild']), {'file', 'modified', 'sizeKb'})
        self.assertNotIn('person@example.com', json.dumps(clean))

    def test_non_object_is_rejected(self):
        self.assertIsNone(ns.sanitize(['x']))
        self.assertIsNone(ns.sanitize(None))


class StoreTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self._patch = patch.object(ns, 'STATUS_PATH', os.path.join(self._dir.name, 'status.json'))
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        self._dir.cleanup()

    def test_load_is_none_until_stored(self):
        self.assertIsNone(ns.load())

    def test_store_then_load_round_trip(self):
        ns.store(ns.sanitize({'configured': True, 'buildCount': 1}))
        loaded = ns.load()
        self.assertTrue(loaded['configured'])
        self.assertEqual(loaded['buildCount'], 1)


if __name__ == '__main__':
    unittest.main()
