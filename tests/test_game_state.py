import math
import unittest

from common.constants import (
    CIRCLE_RADIUS,
    FLAG_START_X,
    FLAG_START_Y,
    INTERACT_RADIUS,
    MAP_CENTER_X,
    MAP_CENTER_Y,
    PLAYER_RADIUS,
    PLAYER_SPEED,
    STATE_COUNTDOWN,
    STATE_LOBBY,
    STATE_PLAYING,
)
from server.game_state import GameState


class GameStateTests(unittest.TestCase):
    def test_player_spawns_outside_circle(self) -> None:
        game = GameState()
        player = game.add_player("p1", "Ana")
        distance = math.dist((player.x, player.y), (MAP_CENTER_X, MAP_CENTER_Y))
        self.assertGreaterEqual(distance, CIRCLE_RADIUS + PLAYER_RADIUS)


    def test_server_starts_countdown_manually(self) -> None:
        game = GameState()
        game.add_player("p1", "Ana")

        self.assertEqual(game.phase, STATE_LOBBY)
        started, _ = game.request_start()

        self.assertTrue(started)
        self.assertEqual(game.phase, STATE_COUNTDOWN)
        self.assertIsNotNone(game.countdown_end)

    def test_capture_flag(self) -> None:
        game = GameState()
        player = game.add_player("p1", "Ana")
        game.phase = STATE_PLAYING
        player.x = FLAG_START_X + INTERACT_RADIUS - 1
        player.y = FLAG_START_Y
        self.assertTrue(game.interact("p1"))
        self.assertEqual(game.flag_owner, "p1")

    def test_diagonal_direction_is_accepted(self) -> None:
        game = GameState()
        game.add_player("p1", "Ana")
        game.phase = STATE_PLAYING
        self.assertTrue(game.set_direction("p1", 1, -1))

    def test_invalid_direction_is_rejected(self) -> None:
        game = GameState()
        game.add_player("p1", "Ana")
        game.phase = STATE_PLAYING
        self.assertFalse(game.set_direction("p1", 2, 0))

    def test_horizontal_and_vertical_speed_are_equal(self) -> None:
        game = GameState()
        player = game.add_player("p1", "Ana")
        game.phase = STATE_PLAYING
        player.x = 500.0
        player.y = 500.0

        game.set_direction("p1", 1, 0)
        game.update(0.05)
        horizontal_distance = player.x - 500.0

        player.x = 500.0
        player.y = 500.0
        game.set_direction("p1", 0, 1)
        game.update(0.05)
        vertical_distance = player.y - 500.0

        self.assertAlmostEqual(horizontal_distance, PLAYER_SPEED * 0.05)
        self.assertAlmostEqual(vertical_distance, PLAYER_SPEED * 0.05)
        self.assertAlmostEqual(horizontal_distance, vertical_distance)

    def test_diagonal_speed_is_normalized(self) -> None:
        game = GameState()
        player = game.add_player("p1", "Ana")
        game.phase = STATE_PLAYING
        player.x = 500.0
        player.y = 500.0

        game.set_direction("p1", 1, 1)
        game.update(0.05)
        distance = math.dist((500.0, 500.0), (player.x, player.y))

        self.assertAlmostEqual(distance, PLAYER_SPEED * 0.05)


if __name__ == "__main__":
    unittest.main()
