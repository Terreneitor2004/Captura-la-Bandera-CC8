import unittest

from client.message_adapter import normalize_flag, normalize_players


class MessageAdapterTests(unittest.TestCase):
    def test_standard_player_list(self) -> None:
        players = normalize_players([
            {"id": "abc", "name": "Fabian", "x": 10, "y": 20}
        ])
        self.assertEqual(players["abc"]["name"], "Fabian")

    def test_dictionary_players_from_other_server(self) -> None:
        players = normalize_players({
            "abc": {"name": "Fabian", "x": 10, "y": 20, "score": 0}
        })
        self.assertEqual(players["abc"]["id"], "abc")
        self.assertEqual(players["abc"]["x"], 10)

    def test_carrier_id_is_converted_to_owner(self) -> None:
        flag = normalize_flag({"x": 500, "y": 500, "carrier_id": "abc"})
        self.assertEqual(flag["owner"], "abc")


if __name__ == "__main__":
    unittest.main()
