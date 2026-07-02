import unittest

from survey_payload import build_survey_components, build_survey_embed


class TestSurveyPayload(unittest.TestCase):
    def test_build_survey_embed_empty(self):
        registrations = {
            "Fire": [],
            "Water": [],
            "Earth": [],
            "Wind": [],
            "Whatever": [],
        }
        survey_date = "30-06-2026"

        embed = build_survey_embed(registrations, survey_date)

        self.assertEqual(embed["title"], "Weekly Zone Registration Survey — 30-06-2026")
        self.assertEqual(len(embed["fields"]), 5)
        for field in embed["fields"]:
            self.assertIn("*No registrations yet*", field["value"])

    def test_build_survey_embed_with_users(self):
        registrations = {
            "Fire": ["123", "456"],
            "Water": ["789"],
            "Earth": [],
            "Wind": [],
            "Whatever": [],
        }
        survey_date = "30-06-2026"

        embed = build_survey_embed(registrations, survey_date)

        self.assertEqual(embed["title"], "Weekly Zone Registration Survey — 30-06-2026")
        fire_field = embed["fields"][0]
        self.assertEqual(fire_field["name"], "🔥 Fire")
        self.assertIn("**Count:** 2", fire_field["value"])
        self.assertIn("<@123>, <@456>", fire_field["value"])

        water_field = embed["fields"][1]
        self.assertEqual(water_field["name"], "💧 Water")
        self.assertIn("**Count:** 1", water_field["value"])
        self.assertIn("<@789>", water_field["value"])

    def test_build_survey_components(self):
        components = build_survey_components()

        self.assertEqual(len(components), 1)
        action_row = components[0]
        self.assertEqual(action_row["type"], 1)
        self.assertEqual(len(action_row["components"]), 1)

        select = action_row["components"][0]
        self.assertEqual(select["type"], 3)
        self.assertEqual(select["custom_id"], "survey_select")
        self.assertEqual(select["min_values"], 1)
        self.assertEqual(select["max_values"], 6)
        self.assertGreaterEqual(len(select["options"]), 6)


if __name__ == "__main__":
    unittest.main()
