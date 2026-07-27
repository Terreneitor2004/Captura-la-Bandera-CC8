import unittest

from common.discovery import _valid_server_info, broadcast_targets


class DiscoveryTests(unittest.TestCase):
    def test_broadcast_includes_general_and_radmin(self) -> None:
        targets = broadcast_targets()
        self.assertIn("255.255.255.255", targets)
        self.assertIn("26.255.255.255", targets)

    def test_server_info_requires_ctf_v1_fields(self) -> None:
        self.assertTrue(
            _valid_server_info(
                {
                    "type": "server_info",
                    "v": 1,
                    "name": "Servidor",
                    "tcp_port": 8889,
                    "state": "lobby",
                    "players": 1,
                }
            )
        )
        self.assertFalse(
            _valid_server_info(
                {
                    "type": "server_info",
                    "v": 1,
                    "name": "Servidor",
                    "tcp_port": 8889,
                    "state": "countdown",
                    "players": 1,
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
