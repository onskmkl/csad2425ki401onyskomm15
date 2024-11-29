import threading
import serial
import serial.tools.list_ports
import json
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter import messagebox


class UARTCommunication:
    """
    Class to handle UART communication, including opening ports, sending and receiving messages.
    """

    def __init__(self):
        """
        Initializes the UARTCommunication instance.
        """
        self.ser = None

    def list_ports(self):
        """
        Lists all available serial ports.

        @return A list of available serial port names.
        """
        return [port.device for port in serial.tools.list_ports.comports()]

    def open_port(self, port, baud_rate=9600):
        """
        Opens a specified serial port with a given baud rate.

        @param port The serial port to open.
        @param baud_rate The baud rate for the port (default is 9600).
        @return A message indicating whether the port was opened successfully or an error occurred.
        """
        try:
            self.ser = serial.Serial(port, baud_rate, timeout=1)
            return f"Connected to {port}"
        except Exception as e:
            self.ser = None
            return f"Error: {e}"

    def send_message(self, message):
        """
        Sends a message over the open serial port in JSON format.

        @param message The message (dictionary) to send.
        @return A message indicating success or an error if sending failed.
        """
        if self.ser and self.ser.is_open:
            try:
                json_message = json.dumps(message)
                self.ser.write((json_message + "\n").encode())
                return f"Sent: {json_message}"
            except Exception as e:
                return f"Error: {e}"
        return "Port not opened"

    def receive_message(self):
        """
        Receives a message from the serial port, attempting to parse it as JSON.

        @return The parsed JSON message if successful, or an error message if receiving failed.
        """
        if self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    response = self.ser.readline().decode().strip()
                    if response:
                        json_response = json.loads(response)
                        return json_response
            except json.JSONDecodeError:
                return "Error: Invalid JSON received"
            except Exception as e:
                return f"Error: {e}"
        return "Port not opened"


def update_game_board(board, buttons):
    """
    Updates the GUI game board with the current board state.

    @param board A 2D list representing the game board.
    @param buttons The GUI button widgets for each cell in the game board.
    """
    for i in range(3):
        for j in range(3):
            buttons[i][j].config(text=board[i][j])


def send_move(uart, row, col):
    """
    Sends a MOVE command with the selected row and column to the UART.

    @param uart The UARTCommunication instance for sending the command.
    @param row The row of the move.
    @param col The column of the move.
    """
    message = {"command": "MOVE", "row": row, "col": col}
    uart.send_message(message)


def set_mode(uart, mode):
    """
    Sends a MODE command to the UART to set the game mode.

    @param uart The UARTCommunication instance for sending the command.
    @param mode The game mode to set (e.g., 0 for User vs User).
    """
    message = {"command": "MODE", "mode": mode}
    uart.send_message(message)


def reset_game(uart):
    """
    Sends a RESET command to the UART to reset the game.

    @param uart The UARTCommunication instance for sending the command.
    """
    message = {"command": "RESET"}
    uart.send_message(message)


def auto_receive(uart, buttons, output_text, root):
    """
    Periodically checks for incoming messages on the UART and updates the GUI accordingly.
    """
    try:
        if uart.ser and uart.ser.is_open:
            response = uart.receive_message()
            print(response)
            if response and response != "Port not opened":
                if isinstance(response, dict):
                    if "board" in response:
                        update_game_board(response["board"], buttons)
                    else:
                        output_text.insert(tk.END, f"Game status: {response.get('message', 'No message')}\n")

                    if response.get("type") == "win_status":
                        thread = threading.Thread(target=messagebox.showinfo, args=("Win Status", response.get("message", "No message")))
                        thread.start()

                else:
                    output_text.insert(tk.END, f"Received: {response}\n")
                output_text.see(tk.END)
    except Exception as e:
        output_text.insert(tk.END, f"Error: {str(e)}\n")
    root.after(100, lambda: auto_receive(uart, buttons, output_text, root))



def start_gui():
    """
    Initializes and runs the GUI for the Tic-Tac-Toe game, handling UART communication and game interactions.
    """
    uart = UARTCommunication()

    root = tk.Tk()
    root.title("TicTacToe Game Interface")

    # GUI components for port selection and status
    port_label = tk.Label(root, text="Select Port:")
    port_label.grid(row=0, column=0, padx=10, pady=10)
    port_var = tk.StringVar()
    port_combobox = ttk.Combobox(root, textvariable=port_var, values=uart.list_ports(), state="readonly")
    port_combobox.grid(row=0, column=1, padx=10, pady=10)

    def open_port_callback():
        """
        Opens the selected port and starts auto-receive if successful.
        """
        status = uart.open_port(port_var.get())
        status_label.config(text=status)
        if "Connected" in status:
            auto_receive(uart, buttons, output_text, root)
        else:
            output_text.insert(tk.END, f"Failed to connect: {status}\n")

    open_button = tk.Button(root, text="Open Port", command=open_port_callback)
    open_button.grid(row=0, column=2, padx=10, pady=10)

    # GUI game board buttons
    buttons = [[None for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            button = tk.Button(root, text=" ", width=10, height=3,
                               command=lambda row=i, col=j: send_move(uart, row, col))
            button.grid(row=i + 1, column=j, padx=5, pady=5)
            buttons[i][j] = button

    # Game mode selection components
    mode_label = tk.Label(root, text="Select Game Mode:")
    mode_label.grid(row=4, column=0, padx=10, pady=10)
    mode_var = tk.StringVar(value="User vs User")
    mode_combobox = ttk.Combobox(root, textvariable=mode_var,
                                 values=["User vs User", "User vs AI", "AI vs AI"],
                                 state="readonly")
    mode_combobox.grid(row=4, column=1, padx=10, pady=10)

    def set_mode_callback():
        """
        Sets the game mode based on the user's selection.
        """
        mode_index = mode_combobox.current()
        set_mode(uart, mode_index)
        status_label.config(text=f"Game mode set to {mode_combobox.get()}")

    mode_button = tk.Button(root, text="Set Mode", command=set_mode_callback)
    mode_button.grid(row=4, column=2, padx=10, pady=10)

    # Reset button for resetting the game
    reset_button = tk.Button(root, text="Reset", command=lambda: reset_game(uart))
    reset_button.grid(row=5, column=1, padx=10, pady=10)

    # Output text area for displaying messages
    output_text = scrolledtext.ScrolledText(root, width=50, height=10, wrap=tk.WORD)
    output_text.grid(row=6, column=0, columnspan=3, padx=10, pady=10)

    # Status label for connection information
    status_label = tk.Label(root, text="Status: Not connected", fg="blue")
    status_label.grid(row=7, column=0, columnspan=3, padx=10, pady=10)

    root.mainloop()


if __name__ == "__main__":
    start_gui()
