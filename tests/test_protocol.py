import unittest

from common.protocol import JsonLineBuffer, ProtocolError, decode_udp_message, encode_tcp_message


class ProtocolTests(unittest.TestCase):
    def test_tcp_message_ends_with_newline(self) -> None:
        result = encode_tcp_message({"type": "join", "v": 1, "name": "Fabián"})
        self.assertTrue(result.endswith(b"\n"))
        self.assertIn("Fabián".encode("utf-8"), result)

    def test_missing_type_is_rejected(self) -> None:
        with self.assertRaises(ProtocolError):
            encode_tcp_message({"v": 1})

    def test_partial_tcp_message(self) -> None:
        buffer = JsonLineBuffer()
        self.assertEqual(buffer.feed(b'{"type":"join","v":'), [])
        result = buffer.feed(b'1,"name":"Ana"}\n')
        self.assertEqual(result[0]["name"], "Ana")

    def test_two_tcp_messages_together(self) -> None:
        buffer = JsonLineBuffer()
        result = buffer.feed(b'{"type":"interact"}\n{"type":"input","dir":{"x":1,"y":0}}\n')
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["type"], "interact")
        self.assertEqual(result[1]["type"], "input")

    def test_udp_message(self) -> None:
        result = decode_udp_message(b'{"type":"discover","v":1}')
        self.assertEqual(result["type"], "discover")


if __name__ == "__main__":
    unittest.main()
