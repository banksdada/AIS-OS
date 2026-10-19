import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from scripts.dashboard import lodgify


NOW = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)


def _booking(bid=1, arrival='2026-10-20', departure='2026-10-22',
             guest='Ada Lovelace', thread='t-1', prop_id=7, status='Booked'):
    return {
        'id': bid, 'arrival': arrival, 'departure': departure,
        'guest': {'name': guest, 'email': 'ada@example.com'},
        'thread_uid': thread, 'property_id': prop_id, 'status': status,
        'source': 'Manual', 'is_new': False,
    }


def _thread(messages, guest='Ada Lovelace', uid='t-1'):
    return {
        'thread_uid': uid, 'guest_name': guest, 'guest_email': 'ada@example.com',
        'last_message_date': messages[-1]['date_created'] if messages else None,
        'is_read': False, 'is_closed': False, 'messages': messages,
    }


def _msg(mid, mtype, text, date):
    return {'id': mid, 'type': mtype, 'message': text, 'date_created': date,
            'is_read': False, 'route': 'Email'}


class StripHtmlTests(unittest.TestCase):
    def test_removes_tags_and_collapses_space(self):
        self.assertEqual(lodgify.strip_html('<p>Hi&nbsp;there</p>\n<b>!</b>'), 'Hi there !')

    def test_truncates_to_140_chars(self):
        self.assertEqual(len(lodgify.strip_html('x' * 300)), 140)

    def test_empty_input(self):
        self.assertEqual(lodgify.strip_html(''), '')
        self.assertEqual(lodgify.strip_html(None), '')


class ClassifyUrgentTests(unittest.TestCase):
    def test_access_code(self):
        self.assertIn('access', lodgify.classify_urgent('Hi, what is the access code?'))

    def test_check_in(self):
        self.assertIn('check-in', lodgify.classify_urgent('What time is check in?'))

    def test_problem(self):
        self.assertIn('problem', lodgify.classify_urgent('There is a problem with the heating'))

    def test_plain_message_is_not_urgent(self):
        self.assertEqual(lodgify.classify_urgent('Lovely place, thank you!'), [])


class ThreadAttentionTests(unittest.TestCase):
    def test_owner_replied_means_answered(self):
        thread = _thread([
            _msg(1, 'Renter', 'What is the access code?', '2026-10-19T08:00:00Z'),
            _msg(2, 'Owner', 'It is 1234.', '2026-10-19T09:00:00Z'),
        ])
        result = lodgify.thread_attention(thread, now=NOW, unanswered_minutes=120)
        self.assertFalse(result['needsReply'])
        self.assertFalse(result['unanswered'])
        self.assertEqual(result['urgent'], [])

    def test_unanswered_guest_message_over_threshold(self):
        thread = _thread([
            _msg(1, 'Owner', 'Welcome!', '2026-10-18T08:00:00Z'),
            _msg(2, 'Renter', 'The door code does not work', '2026-10-19T08:00:00Z'),
        ])
        result = lodgify.thread_attention(thread, now=NOW, unanswered_minutes=120)
        self.assertTrue(result['needsReply'])
        self.assertTrue(result['unanswered'])
        self.assertEqual(result['waitingMinutes'], 240)
        self.assertIn('access', result['urgent'])
        self.assertIn('problem', result['urgent'])
        self.assertIn('door code', result['snippet'])

    def test_recent_guest_message_not_yet_overdue(self):
        thread = _thread([
            _msg(1, 'Renter', 'Late arrival around 22:00, is that ok for check in?',
                 '2026-10-19T11:30:00Z'),
        ])
        result = lodgify.thread_attention(thread, now=NOW, unanswered_minutes=120)
        self.assertTrue(result['needsReply'])
        self.assertFalse(result['unanswered'])
        self.assertEqual(result['waitingMinutes'], 30)

    def test_no_messages_returns_none(self):
        self.assertIsNone(lodgify.thread_attention(_thread([]), now=NOW))

    def test_owner_only_thread_returns_none(self):
        thread = _thread([_msg(1, 'Owner', 'Hello', '2026-10-19T08:00:00Z')])
        self.assertIsNone(lodgify.thread_attention(thread, now=NOW))


class ArrivalWindowTests(unittest.TestCase):
    def test_date_only_today_is_in_window(self):
        self.assertTrue(lodgify._arrival_window_ok(
            lodgify._parse_dt('2026-10-19'), NOW, 48))

    def test_date_only_day_after_tomorrow_in_48h_window(self):
        self.assertTrue(lodgify._arrival_window_ok(
            lodgify._parse_dt('2026-10-20'), NOW, 48))

    def test_date_only_beyond_window(self):
        self.assertFalse(lodgify._arrival_window_ok(
            lodgify._parse_dt('2026-10-25'), NOW, 48))

    def test_future_datetime_in_window(self):
        arrival = NOW + timedelta(hours=2)
        self.assertTrue(lodgify._arrival_window_ok(arrival, NOW, 48))

    def test_past_datetime_excluded(self):
        arrival = NOW - timedelta(hours=3)
        self.assertFalse(lodgify._arrival_window_ok(arrival, NOW, 48))

    def test_none_is_false(self):
        self.assertFalse(lodgify._arrival_window_ok(None, NOW, 48))


class FetchPanelTests(unittest.TestCase):
    def _fake_request(self, api_key, path, params=None):
        if path == '/v2/reservations/bookings' and params['stayFilter'] == 'Upcoming':
            return {'count': 1, 'items': [_booking()]}
        if path == '/v2/reservations/bookings' and params['stayFilter'] == 'Current':
            return {'count': 1, 'items': [_booking(bid=2, arrival='2026-10-18',
                                                   departure='2026-10-21', thread='t-2')]}
        if path == '/v2/properties':
            return [{'id': 7, 'name': 'Seaview Cottage'}]
        if path == '/v2/messaging/t-1':
            return [_thread([
                _msg(1, 'Renter', 'What time is check in?', '2026-10-19T08:00:00Z'),
            ], uid='t-1')]
        if path == '/v2/messaging/t-2':
            return [_thread([
                _msg(1, 'Renter', 'Hello', '2026-10-18T08:00:00Z'),
                _msg(2, 'Owner', 'Hi!', '2026-10-18T09:00:00Z'),
            ], uid='t-2')]
        raise AssertionError(f'unexpected path {path}')

    def test_fetch_panel_builds_arrivals_and_messages(self):
        with patch.object(lodgify, '_request', side_effect=self._fake_request), \
             patch.dict(os.environ, {'LODGIFY_UNANSWERED_MINUTES': '120',
                                     'LODGIFY_ARRIVAL_HOURS': '48'}, clear=False):
            panel = lodgify.fetch_panel('key', now=NOW)

        # Only the Upcoming booking (2026-10-20) is inside the 48h window;
        # the Current booking arrived yesterday so it feeds messages only.
        self.assertEqual(panel['counts']['arrivals'], 1)
        self.assertEqual(panel['arrivals'][0]['property'], 'Seaview Cottage')
        attention = [m for m in panel['messages'] if m['needsReply']]
        self.assertEqual(len(attention), 1)
        self.assertEqual(attention[0]['guest'], 'Ada Lovelace')
        self.assertIn('check-in', attention[0]['urgent'])
        self.assertTrue(attention[0]['unanswered'])
        self.assertEqual(panel['counts']['unanswered'], 1)


class DashboardDataTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self._cache = os.path.join(self._dir.name, 'lodgify-cache.json')
        self._patch_cache = patch.object(lodgify, 'CACHE_PATH', self._cache)
        self._patch_cache.start()

    def tearDown(self):
        self._patch_cache.stop()
        self._dir.cleanup()

    def test_missing_key_is_not_configured(self):
        with patch.dict(os.environ, {'LODGIFY_API_KEY': ''}, clear=False):
            data = lodgify.dashboard_data()
        self.assertFalse(data['configured'])
        self.assertIn('LODGIFY_API_KEY', data['detail'])

    def test_live_fetch_is_cached_then_reused(self):
        panel = {'arrivals': [], 'messages': [],
                 'counts': {'arrivals': 0, 'needsReply': 0, 'unanswered': 0, 'urgent': 0},
                 'unansweredMinutes': 120, 'arrivalHours': 48}
        with patch.dict(os.environ, {'LODGIFY_API_KEY': 'k'}, clear=False), \
             patch.object(lodgify, 'fetch_panel', return_value=panel) as fetch:
            first = lodgify.dashboard_data()
            second = lodgify.dashboard_data()
        self.assertEqual(fetch.call_count, 1)
        self.assertTrue(first['connected'])
        self.assertEqual(first['source'], 'live')
        self.assertEqual(second['source'], 'cache')
        with open(self._cache) as f:
            self.assertEqual(json.load(f)['panel']['counts']['arrivals'], 0)

    def test_fetch_failure_without_cache_reports_detail(self):
        with patch.dict(os.environ, {'LODGIFY_API_KEY': 'k'}, clear=False), \
             patch.object(lodgify, 'fetch_panel', side_effect=OSError('boom')):
            data = lodgify.dashboard_data()
        self.assertFalse(data['connected'])
        self.assertIn('OSError', data['detail'])


if __name__ == '__main__':
    unittest.main()
