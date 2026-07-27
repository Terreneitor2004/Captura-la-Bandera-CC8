import unittest

from client.message_adapter import merge_player_state, normalize_flag, normalize_players


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

    def test_state_preserves_lobby_name(self) -> None:
        previous = {
            "p1": {"id": "p1", "name": "Fabian", "x": 500.0, "y": 500.0}
        }
        state = [{"id": "p1", "x": 125.0, "y": 260.0}]

        players = merge_player_state(state, previous)

        self.assertEqual(players["p1"]["name"], "Fabian")
        self.assertEqual(players["p1"]["x"], 125.0)
        self.assertEqual(players["p1"]["y"], 260.0)


if __name__ == "__main__":
    unittest.main()
