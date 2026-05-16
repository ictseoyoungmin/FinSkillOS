from __future__ import annotations

import unittest

from streamlit.testing.v1 import AppTest


class StreamlitUiSmokeTests(unittest.TestCase):
    def test_default_sample_dataset_is_selected(self) -> None:
        app = AppTest.from_file("app.py", default_timeout=15)
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertGreaterEqual(len(app.selectbox), 1)
        self.assertEqual(app.selectbox[0].value, "multi_asset_portfolio.csv")

    def test_theme_selector_accepts_light_mode(self) -> None:
        app = AppTest.from_file("app.py", default_timeout=15)
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertGreaterEqual(len(app.selectbox), 3)
        self.assertEqual(app.selectbox[2].value, "Dark")

        app.selectbox[2].set_value("Light")
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.selectbox[2].value, "Light")

    def test_topbar_primary_action_label_is_current(self) -> None:
        app = AppTest.from_file("app.py", default_timeout=15)
        app.run()
        self.assertEqual(len(app.exception), 0)
        self.assertGreaterEqual(len(app.button), 1)
        self.assertEqual(app.button[0].label, "Generate Dashboard")

    def test_sample_analysis_renders_all_navigation_tabs(self) -> None:
        app = AppTest.from_file("app.py", default_timeout=15)
        app.run()
        self.assertEqual(len(app.exception), 0)

        self.assertGreaterEqual(len(app.selectbox), 1)
        app.selectbox[0].set_value("multi_asset_portfolio.csv")
        app.run()
        self.assertEqual(len(app.exception), 0)

        nav_labels = [
            "⌂  Overview",
            "◎  Data Profile",
            "↗  Return Analysis",
            "◇  Risk Analysis",
            "◌  Diversification",
            "✦  Insights",
            "▣  Applied Rules",
            "▤  Reports",
        ]
        self.assertGreaterEqual(len(app.radio), 1)
        for label in nav_labels:
            app.radio[0].set_value(label)
            app.run()
            self.assertEqual(len(app.exception), 0, msg=f"{label} rendered with exception(s)")

    def test_reports_tab_separates_available_and_planned_exports(self) -> None:
        app = AppTest.from_file("app.py", default_timeout=15)
        app.run()
        self.assertEqual(len(app.exception), 0)

        app.radio[0].set_value("▤  Reports")
        app.run()
        self.assertEqual(len(app.exception), 0)

        markdown_text = "\n".join(str(markdown.value) for markdown in app.markdown)
        self.assertIn("Available Exports", markdown_text)
        self.assertIn("Planned Extensions", markdown_text)


if __name__ == "__main__":
    unittest.main()
