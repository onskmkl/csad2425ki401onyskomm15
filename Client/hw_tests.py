import unittest
import serial
import json
import time

SERIAL_PORT = 'COM3'  # Change to your COM_PORT
BAUD_RATE = 9600


class TicTacToeArduinoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        cls.ser.close()

    def send_command(self, command_dict):
        self.ser.write((json.dumps(command_dict) + '\n').encode())
        time.sleep(0.5)

    def receive_response(self):
        if self.ser.in_waiting > 0:
            line = self.ser.readline().decode().strip()
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                return None
        return None

    def test_initialize_board(self):
        self.send_command({"command": "RESET"})
        response1 = self.receive_response()
        response2 = self.receive_response()
        self.assertIsNotNone(response2)
        if response2["type"] == "game_status":
            self.assertEqual(response2["message"], "Game reset.")
            response2 = self.receive_response()
        self.assertEqual(response2["type"], "board")
        board_state = response2.get("board", [])
        for row in board_state:
            for cell in row:
                self.assertEqual(cell, " ")

    def test_make_valid_move(self):
        self.send_command({"command": "RESET"})
        self.receive_response()
        self.receive_response()

        self.send_command({"command": "MOVE", "row": 0, "col": 0})
        response = self.receive_response()
        self.assertEqual(response["type"], "board")
        board_state = response.get("board", [])
        self.assertEqual(board_state[0][0], "X")

    def test_make_invalid_move(self):
        self.send_command({"command": "RESET"})
        self.receive_response()
        self.receive_response()

        self.send_command({"command": "MOVE", "row": 0, "col": 0})
        self.receive_response()

        self.send_command({"command": "MOVE", "row": 0, "col": 0})
        response = self.receive_response()
        self.assertIsNotNone(response)
        if response["type"] == "error":
            self.assertEqual(response["message"], "Invalid move.")
        else:
            self.assertEqual(response["type"], "board")

    def test_check_win(self):
        self.send_command({"command": "RESET"})
        self.receive_response()
        self.receive_response()

        moves = [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)]
        for row, col in moves:
            self.send_command({"command": "MOVE", "row": row, "col": col})
            self.receive_response()

        response = self.receive_response()
        self.assertEqual(response["type"], "win_status")
        self.assertEqual(response["message"], "Player X wins!")

    def test_draw(self):
        self.send_command({"command": "RESET"})
        self.receive_response()
        self.receive_response()

        moves = [
            (0, 0), (0, 1), (0, 2),
            (1, 1), (1, 0), (1, 2),
            (2, 1), (2, 0), (2, 2)
        ]
        for row, col in moves:
            self.send_command({"command": "MOVE", "row": row, "col": col})
            self.receive_response()

        response = self.receive_response()
        self.assertEqual(response["type"], "win_status")
        self.assertEqual(response["message"], "It's a draw!")

    def test_game_mode_switch(self):
        """Test switching between different game modes."""
        self.send_command({"command": "MODE", "mode": 1})
        responses = {"game_mode": False, "game_status": False, "board": False}
        for _ in range(5):
            response = self.receive_response()
            if response:
                response_type = response["type"]
                if response_type == "game_mode":
                    responses["game_mode"] = True
                    self.assertIn("Game mode set to 1", response["message"])
                elif response_type == "game_status":
                    responses["game_status"] = True
                    self.assertEqual(response["message"], "Game reset.")

                if all(responses.values()):
                    break

        # Change mode to 2 (AI vs AI)
        self.send_command({"command": "MODE", "mode": 2})
        responses = {"game_mode": False, "game_status": False, "board": False}

        for _ in range(5):
            response = self.receive_response()
            if response:
                response_type = response["type"]
                if response_type == "game_mode":
                    responses["game_mode"] = True
                    self.assertIn("Game mode set to 2", response["message"])
                elif response_type == "game_status":
                    responses["game_status"] = True
                    self.assertEqual(response["message"], "Game reset.")
                elif response_type == "board":
                    responses["board"] = True
                    board_state = response["board"]
                    for row in board_state:
                        for cell in row:
                            self.assertEqual(cell, " ")
                if all(responses.values()):
                    break

    def test_handle_ai_vs_ai(self):
        self.send_command({"command": "MODE", "mode": 2})
        self.receive_response()
        self.receive_response()

        while True:
            response = self.receive_response()
            if response and response["type"] == "win_status":
                self.assertIn(response["message"], ["Player X wins!", "Player O wins!", "It's a draw!"])
                break


if __name__ == '__main__':
    unittest.main()
