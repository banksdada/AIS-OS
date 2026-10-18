import unittest

from scripts.dashboard.generate import summarize_sendfox


class SendfoxSummaryTests(unittest.TestCase):
    def test_uses_total_for_campaigns_and_count_for_contacts(self):
        campaigns = {'total': 137, 'data': [{'title': 'A', 'sent_at': '2026-10-01'}]}
        summary = summarize_sendfox(campaigns, {'count': 842})
        self.assertEqual(summary['campaignCount'], 137)
        self.assertEqual(summary['contactCount'], 842)

    def test_infers_status_from_send_dates(self):
        campaigns = {'data': [
            {'title': 'sent', 'sent_at': '2026-10-01'},
            {'title': 'queued', 'scheduled_at': '2026-11-01'},
            {'title': 'draft'},
        ]}
        statuses = [c['status'] for c in summarize_sendfox(campaigns, {'count': 0})['recentCampaigns']]
        self.assertEqual(statuses, ['sent', 'scheduled', 'draft'])

    def test_bad_shapes_fall_back_to_zero(self):
        summary = summarize_sendfox(None, None)
        self.assertEqual((summary['campaignCount'], summary['contactCount'], summary['recentCampaigns']), (0, 0, []))


if __name__ == '__main__':
    unittest.main()
