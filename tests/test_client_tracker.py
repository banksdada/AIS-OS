import importlib.util
import os
import unittest

_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts", "client-tracker.py",
)
_spec = importlib.util.spec_from_file_location("client_tracker", _PATH)
ct = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ct)


class StageListTests(unittest.TestCase):
    def test_eight_stages(self):
        self.assertEqual(len(ct.STAGES), 8)

    def test_pipeline_order(self):
        self.assertEqual(ct.STAGES, [
            "Lead", "Contacted", "Qualified", "Proposal",
            "Negotiation", "Won", "Lost", "Dormant",
        ])

    def test_every_stage_has_a_style(self):
        # A stage with no colour would silently lose its formatting.
        for stage in ct.STAGES:
            self.assertIn(stage, ct.STAGE_STYLE, f"{stage} has no STAGE_STYLE entry")

    def test_style_keys_match_stages(self):
        self.assertEqual(set(ct.STAGE_STYLE), set(ct.STAGES))


class ValidStageTests(unittest.TestCase):
    def test_exact_match(self):
        self.assertTrue(ct.valid_stage("Proposal"))

    def test_case_insensitive(self):
        self.assertTrue(ct.valid_stage("proposal"))
        self.assertTrue(ct.valid_stage("WON"))

    def test_rejects_typo(self):
        self.assertFalse(ct.valid_stage("Proposel"))

    def test_rejects_old_free_text(self):
        # The value that was actually in the sheet before validation existed.
        self.assertFalse(ct.valid_stage("client"))

    def test_rejects_empty(self):
        self.assertFalse(ct.valid_stage(""))

    def test_canonicalises_case(self):
        self.assertEqual(ct.canonical_stage("won"), "Won")
        self.assertEqual(ct.canonical_stage("NEGOTIATION"), "Negotiation")

    def test_canonical_passes_through_unknown(self):
        self.assertEqual(ct.canonical_stage("bogus"), "bogus")


class AddClientTests(unittest.TestCase):
    def test_invalid_stage_refuses_and_does_not_write(self):
        class FakeSheets:
            def append(self, **kwargs):
                raise AssertionError("must not write on an invalid stage")

        class FakeService:
            def spreadsheets(self):
                return FakeSheets()

        self.assertFalse(ct.add_client(FakeService(), "X", "x@y.com", "Bogus"))

    def test_add_defaults_are_valid(self):
        self.assertTrue(ct.valid_stage("Lead"))


class UpdateStageTests(unittest.TestCase):
    def test_invalid_stage_refuses_and_does_not_write(self):
        class FakeValues:
            def get(self, **kwargs):
                raise AssertionError("must not read on an invalid stage")

        class FakeSheets:
            def values(self):
                return FakeValues()

        class FakeService:
            def spreadsheets(self):
                return FakeSheets()

        self.assertFalse(ct.update_stage(FakeService(), "X", "Bogus"))


class TabNameTests(unittest.TestCase):
    def test_dropdown_source_uses_the_stages_tab(self):
        self.assertEqual(ct.STAGES_TAB, "Stages")

    def test_stage_column_is_c(self):
        self.assertEqual(ct.STAGES_COLUMN, "C")


class RowTintTests(unittest.TestCase):
    def test_every_stage_has_a_row_tint(self):
        for stage in ct.STAGES:
            self.assertIn(stage, ct.STAGE_ROW_TINT, f"{stage} has no row tint")

    def test_tint_keys_match_stages(self):
        self.assertEqual(set(ct.STAGE_ROW_TINT), set(ct.STAGES))

    def test_tints_are_light_enough_for_text(self):
        # A dark tint would hide the dark body text. Every channel must stay
        # high (light), since data text is WA_COLORS['midnight'].
        for stage, tint in ct.STAGE_ROW_TINT.items():
            for channel in ("red", "green", "blue"):
                self.assertGreater(
                    tint[channel], 0.8,
                    f"{stage} {channel} is too dark for readable dark text")


class PaletteTests(unittest.TestCase):
    def test_zebra_is_defined_and_light(self):
        z = ct.WA_COLORS["zebra"]
        for channel in ("red", "green", "blue"):
            self.assertGreater(z[channel], 0.9)

    def test_amber_flag_has_contrasting_text(self):
        bg = ct.WA_COLORS["amber"]
        fg = ct.WA_COLORS["amber_fg"]
        # Sanity: text far darker than the amber background.
        self.assertLess(sum(fg.values()), sum(bg.values()))


if __name__ == "__main__":
    unittest.main()
