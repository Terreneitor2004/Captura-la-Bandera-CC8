import unittest

from main import parser


class LauncherEntryTests(unittest.TestCase):
    def test_no_arguments_opens_menu_mode(self) -> None:
        self.assertIsNone(parser().parse_args([]).mode)

    def test_old_server_command_still_exists(self) -> None:
        self.assertEqual(parser().parse_args(["server"]).mode, "server")


if __name__ == "__main__":
    unittest.main()
