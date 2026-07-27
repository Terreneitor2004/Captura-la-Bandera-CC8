import unittest

from common import constants as C
from common.protocol import encode_tcp_message
from server.network import CTFServer


class StrictProtocolTests(unittest.TestCase):
    def test_welcome_constants_are_json_integers(self):
        self.assertIsInstance(C.MAP_SIZE, int)
        self.assertIsInstance(C.CIRCLE_RADIUS, int)
        self.assertIsInstance(C.PLAYER_RADIUS, int)
        self.assertIsInstance(C.INTERACT_RADIUS, int)
        self.assertIsInstance(C.PLAYER_SPEED, int)

        message = {
            "type": "welcome",
            "player_id": "abc123",
            "config": {
                "map_size": C.MAP_SIZE,
                "circle_radius": C.CIRCLE_RADIUS,
                "player_radius": C.PLAYER_RADIUS,
                "interact_radius": C.INTERACT_RADIUS,
                "speed": C.PLAYER_SPEED,
                "tick_rate": C.TICK_RATE,
            },
        }
        encoded = encode_tcp_message(message).decode("utf-8")
        self.assertIn('"map_size":1000', encoded)
        self.assertNotIn('"map_size":1000.0', encoded)

    def test_server_info_only_uses_lobby_or_playing(self):
        server = CTFServer()
        for phase, expected in (
            (C.STATE_LOBBY, "lobby"),
            (C.STATE_COUNTDOWN, "playing"),
            (C.STATE_PLAYING, "playing"),
            (C.STATE_FINISHED, "playing"),
        ):
            server.game.phase = phase
            self.assertEqual(server._server_info_message()["state"], expected)

    def test_start_is_sent_before_state(self):
        server = CTFServer()
        sent = []
        server.broadcast = sent.append
        server.log_event = lambda _message: None
        server.game.phase = C.STATE_PLAYING
        server.game.start_message_pending = True

        server._publish_protocol_messages(C.STATE_COUNTDOWN)

        self.assertEqual(sent[0]["type"], "start")
        self.assertEqual(sent[1]["type"], "state")

    def test_no_state_after_game_over(self):
        server = CTFServer()
        sent = []
        server.broadcast = sent.append
        server.log_event = lambda _message: None
        server.game.phase = C.STATE_FINISHED
        server.game.winner = "winner01"
        server.game.game_over_message_pending = True

        server._publish_protocol_messages(C.STATE_PLAYING)

        self.assertEqual([message["type"] for message in sent], ["game_over"])


if __name__ == "__main__":
    unittest.main()
