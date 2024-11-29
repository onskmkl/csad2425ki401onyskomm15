import unittest
from unittest.mock import MagicMock, patch
from game import UARTCommunication, send_move, set_mode, reset_game


class TestUARTCommunication(unittest.TestCase):
    def setUp(self):
        self.uart = UARTCommunication()

    @patch('serial.Serial')
    def test_open_port_success(self, mock_serial):
        # Simulate opening the port successfully
        mock_serial.return_value.is_open = True
        result = self.uart.open_port('COM3')
        self.assertEqual(result, "Connected to COM3")
        self.assertTrue(self.uart.ser.is_open)

    @patch('serial.Serial')
    def test_open_port_failure(self, mock_serial):
        # Simulate a failure when opening the port
        mock_serial.side_effect = Exception("Port error")
        result = self.uart.open_port('COM3')
        self.assertIn("Error: Port error", result)
        self.assertIsNone(self.uart.ser)

    @patch('serial.Serial')
    def test_send_message_success(self, mock_serial):
        # Simulate sending a message successfully
        self.uart.ser = mock_serial()
        self.uart.ser.is_open = True
        message = {"command": "MOVE", "row": 1, "col": 2}
        result = self.uart.send_message(message)
        self.assertIn("Sent:", result)

    def test_send_message_no_port(self):
        # Try sending a message when the port is not open
        result = self.uart.send_message({"command": "MOVE"})
        self.assertEqual(result, "Port not opened")

    @patch('serial.Serial')
    def test_receive_message_success(self, mock_serial):
        # Simulate receiving a message
        self.uart.ser = mock_serial()
        self.uart.ser.is_open = True
        self.uart.ser.in_waiting = 1
        self.uart.ser.readline.return_value = b'{"board": [["X", "", ""], ["", "O", ""], ["", "", ""]]}'
        result = self.uart.receive_message()
        self.assertEqual(result, {"board": [["X", "", ""], ["", "O", ""], ["", "", ""]]})

    @patch('serial.Serial')
    def test_receive_message_no_port(self, mock_serial):
        # Test receive when no port is open
        result = self.uart.receive_message()
        self.assertEqual(result, "Port not opened")

    def test_receive_message_invalid_json(self):
        # Simulate an invalid JSON message
        self.uart.ser = MagicMock()
        self.uart.ser.is_open = True
        self.uart.ser.in_waiting = 1
        self.uart.ser.readline.return_value = b'Invalid JSON'
        result = self.uart.receive_message()
        self.assertIn("Error:", result)


class TestGameCommands(unittest.TestCase):
    def setUp(self):
        self.uart = MagicMock()

    def test_send_move(self):
        send_move(self.uart, 1, 1)
        self.uart.send_message.assert_called_once_with({"command": "MOVE", "row": 1, "col": 1})

    def test_set_mode(self):
        set_mode(self.uart, 1)
        self.uart.send_message.assert_called_once_with({"command": "MODE", "mode": 1})

    def test_reset_game(self):
        reset_game(self.uart)
        self.uart.send_message.assert_called_once_with({"command": "RESET"})


if __name__ == '__main__':
    unittest.main()