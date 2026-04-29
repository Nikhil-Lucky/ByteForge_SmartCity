import unittest

from dashboard_page import (
    _coords_for_custom_location,
    _distance_score,
    _extract_custom_location_label,
    _query_needs_exact_location,
)


class DashboardHelperTests(unittest.TestCase):
    def test_query_needs_exact_location_for_near_me_phrases(self):
        self.assertTrue(_query_needs_exact_location("ambulance near me"))
        self.assertTrue(_query_needs_exact_location("closest hospital around me"))
        self.assertFalse(_query_needs_exact_location("ambulance near Indiranagar"))

    def test_extract_custom_location_label_from_text(self):
        self.assertEqual(
            _extract_custom_location_label("Need ambulance near MG Road"),
            "Mg Road",
        )
        self.assertEqual(
            _extract_custom_location_label("Hospital in Koramangala"),
            "Koramangala",
        )

    def test_coords_for_custom_location_are_stable_for_same_label(self):
        first = _coords_for_custom_location("MG Road")
        second = _coords_for_custom_location("MG Road")
        self.assertEqual(first, second)

    def test_distance_score_is_zero_for_same_point(self):
        self.assertEqual(_distance_score(12.9, 77.5, 12.9, 77.5), 0)


if __name__ == "__main__":
    unittest.main()
