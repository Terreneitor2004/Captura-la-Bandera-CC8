import unittest

from ui.layout import Rect, logical_to_screen


class LayoutTests(unittest.TestCase):
    def test_logical_scale_is_equal_on_both_axes(self) -> None:
        arena = Rect(20, 30, 600, 600)
        origin = logical_to_screen(100, 100, arena)
        horizontal = logical_to_screen(200, 100, arena)
        vertical = logical_to_screen(100, 200, arena)

        horizontal_pixels = abs(horizontal[0] - origin[0])
        vertical_pixels = abs(vertical[1] - origin[1])
        self.assertAlmostEqual(horizontal_pixels, vertical_pixels)


if __name__ == "__main__":
    unittest.main()
