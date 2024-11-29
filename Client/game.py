import threading
import serial
import serial.tools.list_ports
import json
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter import messagebox


class UARTCommunication:
    def __init__(self):
        self.ser = None

    def list_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def open_port(self, port, baud_rate=9600):
        try:
            self.ser = serial.Serial(port, baud_rate, timeout=1)
            return f"Connected to {port}"
        except Exception as e:
            self.ser = None
            return f"Error: {e}"

    def close_port(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser = None
            return "Port closed"
        return "Port not opened"

    def send_message(self, message):
        if self.ser and self.ser.is_open:
            try:
                json_message = json.dumps(message)
                self.ser.write((json_message + "\n").encode())
                return f"Sent: {json_message}"
            except Exception as e:
                return f"Error: {e}"
        return "Port not opened"

    def receive_message(self):
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
        return None


def update_game_board(board, buttons):
    for i in range(3):
        for j in range(3):
            buttons[i][j].config(text=board[i][j])


def send_move(uart, row, col):
    if uart.ser and uart.ser.is_open:
        message = {"command": "MOVE", "row": row, "col": col}
        uart.send_message(message)


def set_mode(uart, mode):
    if uart.ser and uart.ser.is_open:
        message = {"command": "MODE", "mode": mode}
        uart.send_message(message)


def reset_game(uart):
    if uart.ser and uart.ser.is_open:
        message = {"command": "RESET"}
        uart.send_message(message)


def auto_receive(uart, buttons, output_text, root):
    try:
        if uart.ser and uart.ser.is_open:
            response = uart.receive_message()
            if response:
                if isinstance(response, dict):
                    if "board" in response:
                        update_game_board(response["board"], buttons)
                    elif "message" in response:
                        output_text.insert(tk.END, f"Game status: {response['message']}\n")
                        if response.get("type") == "win_status":
                            root.after(0, lambda: messagebox.showinfo("Win Status", response["message"]))
                else:
                    output_text.insert(tk.END, f"Received: {response}\n")
                output_text.see(tk.END)
    except Exception as e:
        output_text.insert(tk.END, f"Error: {str(e)}\n")
    if uart.ser and uart.ser.is_open:
        root.after(100, lambda: auto_receive(uart, buttons, output_text, root))


def start_gui():
    uart = UARTCommunication()

    root = tk.Tk()
    root.title("TicTacToe Game Interface")

    port_label = tk.Label(root, text="Select Port:")
    port_label.grid(row=0, column=0, padx=10, pady=10)
    port_var = tk.StringVar()
    port_combobox = ttk.Combobox(root, textvariable=port_var, values=uart.list_ports(), state="readonly")
    port_combobox.grid(row=0, column=1, padx=10, pady=10)

    def refresh_ports():
        port_combobox["values"] = uart.list_ports()

    refresh_button = tk.Button(root, text="Refresh Ports", command=refresh_ports)
    refresh_button.grid(row=0, column=2, padx=10, pady=10)

    def open_port_callback():
        status = uart.open_port(port_var.get())
        status_label.config(text=status)
        if "Connected" in status:
            auto_receive(uart, buttons, output_text, root)
        else:
            output_text.insert(tk.END, f"Failed to connect: {status}\n")

    def close_port_callback():
        status = uart.close_port()
        status_label.config(text=status)

    open_button = tk.Button(root, text="Open Port", command=open_port_callback)
    open_button.grid(row=1, column=1, padx=10, pady=10)

    close_button = tk.Button(root, text="Close Port", command=close_port_callback)
    close_button.grid(row=1, column=2, padx=10, pady=10)

    buttons = [[None for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            button = tk.Button(root, text=" ", width=10, height=3,
                               command=lambda row=i, col=j: send_move(uart, row, col))
            button.grid(row=i + 2, column=j, padx=5, pady=5)
            buttons[i][j] = button

    mode_label = tk.Label(root, text="Select Game Mode:")
    mode_label.grid(row=5, column=0, padx=10, pady=10)
    mode_var = tk.StringVar(value="User vs User")
    mode_combobox = ttk.Combobox(root, textvariable=mode_var,
                                 values=["User vs User", "User vs AI", "AI vs AI"],
                                 state="readonly")
    mode_combobox.grid(row=5, column=1, padx=10, pady=10)

    def set_mode_callback():
        mode_index = mode_combobox.current()
        if uart.ser and uart.ser.is_open:
            set_mode(uart, mode_index)
            status_label.config(text=f"Game mode set to {mode_combobox.get()}")
            output_text.insert(tk.END, f"Mode set: {mode_combobox.get()}\n")

    mode_button = tk.Button(root, text="Set Mode", command=set_mode_callback)
    mode_button.grid(row=5, column=2, padx=10, pady=10)

    reset_button = tk.Button(root, text="Reset", command=lambda: reset_game(uart))
    reset_button.grid(row=6, column=1, padx=10, pady=10)

    output_text = scrolledtext.ScrolledText(root, width=50, height=10, wrap=tk.WORD)
    output_text.grid(row=7, column=0, columnspan=3, padx=10, pady=10)

    status_label = tk.Label(root, text="Status: Not connected", fg="blue")
    status_label.grid(row=8, column=0, columnspan=3, padx=10, pady=10)

    root.mainloop()


if __name__ == "__main__":
    start_gui()

