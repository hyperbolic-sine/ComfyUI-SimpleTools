"""Tests for the Resolution Selector size table.

No ComfyUI installation required:

    python -m unittest discover -s tests -v
"""

import importlib.util
import pathlib
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rs = _load("_resolution_selector", "resolution_selector.py")


class ResolutionTableTest(unittest.TestCase):
    def test_matrix_is_complete(self):
        self.assertEqual(len(rs.RESOLUTIONS), len(rs.TIER_SHORT_SIDES))
        for tier, ratios in rs.RESOLUTIONS.items():
            with self.subTest(tier=tier):
                self.assertEqual(list(ratios), rs.ASPECT_RATIOS)

    def test_short_side_matches_tier(self):
        for tier, short in rs.TIER_SHORT_SIDES.items():
            for ratio, (width, height) in rs.RESOLUTIONS[tier].items():
                with self.subTest(tier=tier, ratio=ratio):
                    if tier == "480P" and ratio in ("16:9", "9:16"):
                        continue  # documented 854 px override
                    self.assertEqual(min(width, height), short)

    def test_orientation_follows_ratio(self):
        for tier, ratios in rs.RESOLUTIONS.items():
            for ratio, (width, height) in ratios.items():
                a, b = (int(part) for part in ratio.split(":"))
                with self.subTest(tier=tier, ratio=ratio):
                    if a > b:
                        self.assertGreater(width, height)
                    elif a < b:
                        self.assertLess(width, height)
                    else:
                        self.assertEqual(width, height)

    def test_values_stay_within_one_pixel_of_the_exact_ratio(self):
        for tier, ratios in rs.RESOLUTIONS.items():
            for ratio, (width, height) in ratios.items():
                a, b = (int(part) for part in ratio.split(":"))
                with self.subTest(tier=tier, ratio=ratio):
                    self.assertLess(abs(width / height - a / b), 0.002)

    def test_480p_uses_the_industry_standard(self):
        self.assertEqual(rs.RESOLUTIONS["480P"]["16:9"], (854, 480))
        self.assertEqual(rs.RESOLUTIONS["480P"]["9:16"], (480, 854))

    def test_only_480p_16_9_is_not_a_multiple_of_eight(self):
        """Pipelines that divide by 8 truncate 854 to 848; document the set."""
        odd = {
            (tier, ratio)
            for tier, ratios in rs.RESOLUTIONS.items()
            for ratio, (w, h) in ratios.items()
            if w % 8 or h % 8
        }
        self.assertEqual(odd, {("480P", "16:9"), ("480P", "9:16")})

    def test_get_size_returns_the_table_value(self):
        node = rs.SimpleResolutionSelector()
        for tier, ratios in rs.RESOLUTIONS.items():
            for ratio, expected in ratios.items():
                with self.subTest(tier=tier, ratio=ratio):
                    self.assertEqual(node.get_size(tier, ratio), expected)

    def test_unknown_combination_falls_back_to_1024(self):
        node = rs.SimpleResolutionSelector()
        self.assertEqual(node.get_size("8K", "16:9"), (1024, 1024))
        self.assertEqual(node.get_size("1080P", "2:1"), (1024, 1024))

    def test_legacy_node_key_is_still_registered(self):
        self.assertIs(
            rs.NODE_CLASS_MAPPINGS["ResolutionSelectorJWB"],
            rs.NODE_CLASS_MAPPINGS["SimpleResolutionSelector"],
        )

    def test_route_is_shared_with_the_frontend_extension(self):
        """The backend route and the JS fetch URL must not drift apart."""
        js = (REPO_ROOT / "js" / "resolution_selector.js").read_text(encoding="utf-8")
        self.assertIn(rs.OPTIONS_ROUTE, js)


class PackageContractTest(unittest.TestCase):
    MODULES = (
        "resolution_selector.py",
        "batch_progress.py",
        "simple_counter.py",
        "save_image_clean.py",
    )

    def test_every_module_declares_node_mappings_and_compiles(self):
        for filename in self.MODULES:
            source = (REPO_ROOT / filename).read_text(encoding="utf-8")
            with self.subTest(module=filename):
                compile(source, filename, "exec")
                self.assertIn("NODE_CLASS_MAPPINGS", source)
                self.assertIn("NODE_DISPLAY_NAME_MAPPINGS", source)

    def test_init_exposes_web_directory(self):
        source = (REPO_ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('WEB_DIRECTORY = "./js"', source)

    def test_vhs_requeue_detection(self):
        import sys

        sys.path.insert(0, str(REPO_ROOT))
        try:
            import utils  # noqa: PLC0415 - local import on purpose
        finally:
            sys.path.pop(0)

        self.assertFalse(utils.is_vhs_requeue(None))
        self.assertFalse(utils.is_vhs_requeue({}))
        self.assertFalse(
            utils.is_vhs_requeue({"1": {"class_type": "VHS_BatchManager", "inputs": {}}})
        )
        self.assertTrue(
            utils.is_vhs_requeue(
                {"1": {"class_type": "VHS_BatchManager", "inputs": {"requeue": 1}}}
            )
        )
        self.assertFalse(
            utils.is_vhs_requeue(
                {
                    "1": {"class_type": "KSampler", "inputs": {"requeue": 5}},
                    "2": {"class_type": "VHS_BatchManager", "inputs": {"requeue": 0}},
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
