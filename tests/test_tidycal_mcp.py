import unittest
from unittest.mock import patch

from scripts import tidycal_mcp


class DashboardDataTests(unittest.TestCase):
    def setUp(self):
        tidycal_mcp._CACHE.update(expires=0, data=None)

    def tearDown(self):
        tidycal_mcp._CACHE.update(expires=0, data=None)

    def test_unconfigured_dashboard_shape_is_disconnected(self):
        with patch.object(tidycal_mcp, '_load_config', return_value=None):
            payload = tidycal_mcp.dashboard_data()

        self.assertFalse(payload['connected'])
        self.assertEqual(payload['bookings'], [])
        self.assertEqual(payload['bookingTypes'], [])
        self.assertIn('tidycal_mcp.py login', payload['detail'])

    def test_connected_payload_excludes_guest_personal_data(self):
        tool_results = {
            'get-current-user': {},
            'list-bookings': {'structuredContent': {'bookings': [{
                'booking_type': {'title': 'Consultation'},
                'starts_at': '2026-10-17T10:00:00Z',
                'ends_at': '2026-10-17T10:30:00Z',
                'status': 'confirmed',
                'guest': {'name': 'Private Guest', 'email': 'guest@example.com'},
                'answers': [{'answer': 'private response'}],
            }]}},
            'list-booking-types': {'structuredContent': {'booking_types': [{
                'title': 'Consultation',
                'duration': 30,
                'price': 100,
            }]}},
        }
        with patch.object(tidycal_mcp, '_load_config', return_value={'client_id': 'test'}), \
             patch.object(tidycal_mcp, '_call_tools', return_value=tool_results):
            payload = tidycal_mcp.dashboard_data()

        self.assertTrue(payload['connected'])
        self.assertEqual(payload['bookings'], [{
            'title': 'Consultation',
            'startsAt': '2026-10-17T10:00:00Z',
            'endsAt': '2026-10-17T10:30:00Z',
            'status': 'confirmed',
        }])
        self.assertEqual(payload['bookingTypes'], [{'title': 'Consultation', 'duration': 30}])
        serialized = str(payload)
        self.assertNotIn('guest@example.com', serialized)
        self.assertNotIn('Private Guest', serialized)
        self.assertNotIn('private response', serialized)
        self.assertNotIn('100', serialized)


if __name__ == '__main__':
    unittest.main()
