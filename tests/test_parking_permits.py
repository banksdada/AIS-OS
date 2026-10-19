import unittest
from datetime import date

from scripts import parking_permits as pp


class FindPlatesTests(unittest.TestCase):
    def test_plate_with_keyword(self):
        self.assertEqual(pp.find_plates('Registration Number of my car is J25 STV'), ['J25STV'])

    def test_plate_without_space_and_lowercase(self):
        self.assertEqual(pp.find_plates('reg is dx68ysw thanks'), ['DX68YSW'])

    def test_plate_without_vehicle_keyword_is_ignored(self):
        self.assertEqual(pp.find_plates('Our flight is at BA12 XYZ tomorrow'), [])

    def test_no_plate(self):
        self.assertEqual(pp.find_plates('What time is check in?'), [])

    def test_html_message_text_is_handled_by_caller(self):
        self.assertEqual(pp.find_plates(pp.plain_text('<p>Reg: <b>AB12 CDE</b></p>')), ['AB12CDE'])


class FindVehicleTests(unittest.TestCase):
    def test_make_model_with_colour_before(self):
        self.assertEqual(pp.find_vehicle('My silver Honda Civic, reg AB12CDE'), 'Honda Civic, silver')

    def test_make_only(self):
        self.assertEqual(pp.find_vehicle('We are driving a Toyota.'), 'Toyota')

    def test_no_make(self):
        self.assertEqual(pp.find_vehicle('Registration HK22KKG thanks'), '')


class BuildCandidatesTests(unittest.TestCase):
    TODAY = date(2026, 10, 19)

    def _booking(self, bid=1, status='Booked', departure='2026-10-22T11:00:00Z', thread='t1'):
        return {'id': bid, 'status': status, 'arrival': '2026-10-20', 'departure': departure,
                'guest': {'name': 'Ada Lovelace', 'email': 'ada@example.com'}, 'thread_uid': thread}

    def test_complete_booking_becomes_row(self):
        msgs = {'t1': ['Hi, my reg is AB12 CDE and my silver Honda Civic']}
        rows, skipped = pp.build_candidates([self._booking()], msgs, self.TODAY)
        self.assertEqual(skipped, [])
        self.assertEqual(rows[0]['row'][:6], ['Ada Lovelace', 'ada@example.com', 'AB12CDE',
                                              'Honda Civic, silver', '20/10/2026', '22/10/2026'])
        self.assertEqual(rows[0]['row'][12], '')

    def test_registration_without_make_uses_placeholder(self):
        rows, skipped = pp.build_candidates([self._booking()],
                                            {'t1': ['reg AB12 CDE']}, self.TODAY)
        self.assertEqual(skipped, [])
        self.assertEqual(rows[0]['row'][2:4], ['AB12CDE', 'Not provided'])

    def test_missing_email_creates_row_with_note(self):
        booking = self._booking()
        booking['guest'] = {'name': 'Ada Lovelace', 'email': ''}
        rows, skipped = pp.build_candidates([booking],
                                            {'t1': ['reg AB12 CDE Honda']}, self.TODAY)
        self.assertEqual(skipped, [])
        self.assertEqual(rows[0]['row'][1], '')
        self.assertIn('provide one', rows[0]['row'][12])

    def test_no_registration_is_skipped(self):
        rows, skipped = pp.build_candidates([self._booking()],
                                            {'t1': ['Honda Civic, see you soon']}, self.TODAY)
        self.assertEqual(rows, [])
        self.assertEqual(skipped[0][1], 'no registration in messages')

    def test_ended_stay_is_ignored(self):
        rows, skipped = pp.build_candidates([self._booking(departure='2026-10-01T11:00:00Z')],
                                            {'t1': ['reg AB12 CDE Honda']}, self.TODAY)
        self.assertEqual(rows, [])
        self.assertEqual(skipped, [])


class DropDuplicatesTests(unittest.TestCase):
    def test_same_email_and_checkin_is_duplicate(self):
        cand = [{'row': ['Ada', 'ada@example.com', 'AB12CDE', 'Honda', '20/10/2026', '22/10/2026']}]
        existing = [['Ada', 'ADA@example.com', 'AB12CDE', 'Honda', '20/10/2026', '22/10/2026']]
        fresh, dupes = pp.drop_duplicates(cand, existing)
        self.assertEqual(fresh, [])
        self.assertEqual(len(dupes), 1)

    def test_blank_email_dedupes_on_registration_only(self):
        cand = [{'row': ['Ada', '', 'AB12CDE', 'Not provided', '20/10/2026', '22/10/2026']},
                {'row': ['Bob', '', 'XY11ABC', 'Not provided', '20/10/2026', '21/10/2026']}]
        existing = [['Ada', '', 'AB12CDE', 'Not provided', '20/10/2026', '22/10/2026']]
        fresh, dupes = pp.drop_duplicates(cand, existing)
        self.assertEqual(len(fresh), 1)
        self.assertEqual(fresh[0]['row'][2], 'XY11ABC')
        self.assertEqual(len(dupes), 1)

    def test_new_booking_is_kept(self):
        cand = [{'row': ['Bob', 'bob@example.com', 'XY11ABC', 'Ford', '25/10/2026', '26/10/2026']}]
        existing = [['Ada', 'ada@example.com', 'AB12CDE', 'Honda', '20/10/2026', '22/10/2026']]
        fresh, dupes = pp.drop_duplicates(cand, existing)
        self.assertEqual(len(fresh), 1)
        self.assertEqual(dupes, [])


if __name__ == '__main__':
    unittest.main()
