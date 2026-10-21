import importlib.util
import os
import unittest

_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts", "pyrunner", "recruiter-message-watch.py",
)
_spec = importlib.util.spec_from_file_location("recruiter_message_watch", _PATH)
rw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rw)

ROLES = ["business analyst", "product owner", "product manager"]


def msg(subject="", sender="", snippet=""):
    return {"id": "1", "from": sender, "subject": subject, "snippet": snippet, "internalDate": 0}


class ClassifyTests(unittest.TestCase):
    def test_role_keywords_in_subject_is_role_match(self):
        m = msg(subject="Business Analyst role - Manchester",
                sender="jane@agency.com", snippet="We are hiring.")
        self.assertEqual(rw.classify(m, ROLES), "role_match")

    def test_product_owner_role_match(self):
        m = msg(subject="Product Owner opportunity",
                sender="recruiter@jobs.com", snippet="")
        self.assertEqual(rw.classify(m, ROLES), "role_match")

    def test_plain_recruiter_still_recruiter(self):
        m = msg(subject="Are you available?", sender="bob@recruitment.com",
                snippet="We have a role that may suit you.")
        self.assertEqual(rw.classify(m, ROLES), "recruiter")

    def test_linkedin_alert_with_job_hint(self):
        m = msg(subject="5 new jobs match your search",
                sender="jobs-noreply@linkedin.com", snippet="See who is hiring.")
        self.assertEqual(rw.classify(m, ROLES), "alert")

    def test_linkedin_marketing_is_dropped(self):
        m = msg(subject="People you may know",
                sender="notifications@linkedin.com", snippet="")
        self.assertIsNone(rw.classify(m, ROLES))

    def test_linkedin_newsletter_is_dropped(self):
        m = msg(subject="Your weekly update",
                sender="news@linkedin.com", snippet="Catch up on your network.")
        self.assertIsNone(rw.classify(m, ROLES))

    def test_unrelated_email_is_dropped(self):
        m = msg(subject="Your Amazon order has shipped",
                sender="ship@amazon.co.uk", snippet="")
        self.assertIsNone(rw.classify(m, ROLES))

    def test_noise_wins_over_role_keyword(self):
        # "is hiring" noise must not be rescued by a lucky role keyword.
        m = msg(subject="Your connection is hiring",
                sender="notifications@linkedin.com",
                snippet="A product manager you follow is hiring.")
        self.assertIsNone(rw.classify(m, ROLES))

    def test_role_match_from_body_not_just_subject(self):
        m = msg(subject="Quick question",
                sender="hire@agency.com",
                snippet="We need a Product Manager for a 6 month contract.")
        self.assertEqual(rw.classify(m, ROLES), "role_match")

    def test_interview_email_is_flagged(self):
        m = msg(subject="Interview invitation", sender="hr@company.co.uk", snippet="")
        self.assertEqual(rw.classify(m, ROLES), "recruiter")

    def test_plain_role_approach_is_recruiter(self):
        # No role keyword, no "recruiter" word — but a human offering a role.
        m = msg(subject="Opportunity", sender="jane@agency.com",
                snippet="Reaching out about a role that may suit you.")
        self.assertEqual(rw.classify(m, ROLES), "recruiter")

    def test_role_word_does_not_rescue_linkedin_noise(self):
        m = msg(subject="People you may know",
                sender="notifications@linkedin.com",
                snippet="Check out this position.")
        self.assertIsNone(rw.classify(m, ROLES))

    def test_linkedin_hiring_noise_dropped_even_with_role_keyword(self):
        m = msg(subject="Your connection is hiring",
                sender="notifications@linkedin.com",
                snippet="A product manager you follow is hiring.")
        self.assertIsNone(rw.classify(m, ROLES))


class RankTests(unittest.TestCase):
    def test_role_match_sorts_before_alert(self):
        self.assertLess(rw.rank("role_match"), rw.rank("alert"))

    def test_unknown_kind_sorts_last(self):
        self.assertGreater(rw.rank("whatever"), rw.rank("alert"))


class BodyTests(unittest.TestCase):
    def test_body_text_falls_back_to_snippet(self):
        m = {"payload": {}, "snippet": "hello   world"}
        self.assertEqual(rw.body_text(m), "hello world")

    def test_body_text_limits_length(self):
        m = {"payload": {}, "snippet": "x" * 5000}
        self.assertEqual(len(rw.body_text(m, limit=100)), 100)


if __name__ == "__main__":
    unittest.main()
