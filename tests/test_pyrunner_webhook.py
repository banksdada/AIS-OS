import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch

from scripts.dashboard import pyrunner_events as ev

SECRET = 'test-secret'


class SignatureTests(unittest.TestCase):
    def test_valid_signature_is_accepted(self):
        body = b'{"agent":"news","status":"ok"}'
        ts = str(int(time.time()))
        self.assertTrue(ev.verify(SECRET, ts, body, ev.sign(SECRET, ts, body)))

    def test_tampered_body_is_rejected(self):
        ts = str(int(time.time()))
        sig = ev.sign(SECRET, ts, b'{"status":"ok"}')
        self.assertFalse(ev.verify(SECRET, ts, b'{"status":"failed"}', sig))

    def test_wrong_secret_is_rejected(self):
        ts = str(int(time.time()))
        body = b'{}'
        self.assertFalse(ev.verify('other-secret', ts, body, ev.sign(SECRET, ts, body)))

    def test_stale_timestamp_is_rejected(self):
        body = b'{}'
        old = int(time.time()) - ev.MAX_SKEW_SECONDS - 60
        sig = ev.sign(SECRET, str(old), body)
        self.assertFalse(ev.verify(SECRET, str(old), body, sig))

    def test_missing_or_bad_headers_are_rejected(self):
        self.assertFalse(ev.verify(SECRET, 'not-a-number', b'{}', 'sha256=x'))
        self.assertFalse(ev.verify(SECRET, str(int(time.time())), b'{}', None))


class SanitizeTests(unittest.TestCase):
    def test_keeps_only_known_fields_and_truncates(self):
        clean = ev.sanitize({'agent': 'a' * 500, 'status': 'ok', 'message': 'hi', 'extra': 'drop me'})
        self.assertEqual(len(clean['agent']), ev.FIELD_LIMITS['agent'])
        self.assertEqual(clean['status'], 'ok')
        self.assertNotIn('extra', clean)
        self.assertIn('received', clean)

    def test_non_object_is_rejected(self):
        self.assertIsNone(ev.sanitize(['not', 'an', 'object']))
        self.assertIsNone(ev.sanitize('text'))


class StoreTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self._patch = patch.object(ev, 'EVENTS_PATH', os.path.join(self._dir.name, 'events.json'))
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        self._dir.cleanup()

    def test_newest_first_and_capped(self):
        for i in range(ev.MAX_EVENTS + 5):
            ev.record({'agent': f'a{i}'})
        events = ev.load_events(limit=ev.MAX_EVENTS + 50)
        self.assertEqual(len(events), ev.MAX_EVENTS)
        self.assertEqual(events[0]['agent'], f'a{ev.MAX_EVENTS + 4}')

    def test_load_returns_empty_when_missing_or_corrupt(self):
        self.assertEqual(ev.load_events(), [])
        with open(ev.EVENTS_PATH, 'w') as f:
            f.write('{not json')
        self.assertEqual(ev.load_events(), [])

    def test_record_writes_valid_json(self):
        ev.record({'agent': 'x', 'status': 'ok'})
        with open(ev.EVENTS_PATH) as f:
            self.assertEqual(json.load(f)[0]['agent'], 'x')


if __name__ == '__main__':
    unittest.main()
