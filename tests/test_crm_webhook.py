import json
import os
import tempfile
import unittest
from unittest.mock import patch

from scripts.dashboard import crm_capture as crm


class SanitizeTests(unittest.TestCase):
    def test_keeps_name_email_stage(self):
        clean = crm.sanitize({'name': 'Ada Lovelace', 'email': 'ada@example.com', 'stage': 'Lead'})
        self.assertEqual(clean, {'name': 'Ada Lovelace', 'email': 'ada@example.com', 'stage': 'Lead'})

    def test_name_falls_back_to_local_part(self):
        clean = crm.sanitize({'email': 'ada@example.com'})
        self.assertEqual(clean['name'], 'ada')

    def test_stage_defaults_to_lead(self):
        clean = crm.sanitize({'email': 'a@b.com'})
        self.assertEqual(clean['stage'], 'Lead')

    def test_missing_or_invalid_email_is_rejected(self):
        self.assertIsNone(crm.sanitize({'name': 'No Email'}))
        self.assertIsNone(crm.sanitize({'email': 'not-an-email'}))
        self.assertIsNone(crm.sanitize({'email': '   '}))

    def test_non_object_is_rejected(self):
        self.assertIsNone(crm.sanitize(['a', 'list']))
        self.assertIsNone(crm.sanitize('text'))

    def test_truncates_long_fields(self):
        clean = crm.sanitize({'name': 'n' * 500, 'email': 'a@' + 'b' * 500 + '.com'})
        self.assertLessEqual(len(clean['name']), crm.MAX_NAME)
        self.assertLessEqual(len(clean['email']), crm.MAX_EMAIL)

    def test_extra_fields_are_dropped(self):
        clean = crm.sanitize({'email': 'a@b.com', 'problem': 'secret', 'ip': '1.2.3.4'})
        self.assertEqual(set(clean), {'name', 'email', 'stage'})


class CaptureTests(unittest.TestCase):
    def test_capture_passes_name_email_stage_to_tracker(self):
        contact = {'name': 'Ada', 'email': 'ada@example.com', 'stage': 'Lead'}
        with patch.object(crm.subprocess, 'run') as run:
            run.return_value.returncode = 0
            crm.capture(contact, tracker_path='/tmp/tracker.py')
        args = run.call_args[0][0]
        self.assertIn('add', args)
        self.assertIn('Ada', args)
        self.assertIn('ada@example.com', args)
        self.assertIn('Lead', args)


class LogEventTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self._root = patch.object(crm, '_REPO_ROOT', self._dir.name)
        self._root.start()

    def tearDown(self):
        self._root.stop()
        self._dir.cleanup()

    def test_writes_newest_first_valid_json(self):
        crm.log_event({'name': 'A', 'email': 'a@b.com', 'stage': 'Lead'}, True)
        crm.log_event({'name': 'B', 'email': 'b@b.com', 'stage': 'Lead'}, False, 'boom')
        path = os.path.join(self._dir.name, 'data', 'crm-captures.json')
        with open(path) as f:
            records = json.load(f)
        self.assertEqual(records[0]['name'], 'B')
        self.assertFalse(records[0]['ok'])
        self.assertEqual(records[1]['name'], 'A')

    def test_corrupt_file_is_recovered(self):
        path = os.path.join(self._dir.name, 'data', 'crm-captures.json')
        os.makedirs(os.path.dirname(path))
        with open(path, 'w') as f:
            f.write('{not json')
        record = crm.log_event({'name': 'A', 'email': 'a@b.com', 'stage': 'Lead'}, True)
        self.assertEqual(record['name'], 'A')


if __name__ == '__main__':
    unittest.main()
