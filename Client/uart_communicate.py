import threading
import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, scrolledtext


class UARTCommunication:
    def __init__(self):
        self.ser = None

    def list_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def open_port(self, port, baud_rate=9600):
        try:
            self.ser = serial.Serial(port, baud_rate, timeout=1)
            print(self.ser.is_open)
            return f"Connected to {port}"
        except Exception as e:
            self.ser = None
            return f"Error: {e}"

    def send_message(self, message):
        if self.ser and self.ser.is_open:
            self.ser.write((message + "\n").encode())
            return f"Sent: {message}"
        return "Port not opened"

    def receive_message(self):
        if self.ser and self.ser.is_open:
            try:
                response = self.ser.readline().decode().strip()
                if response:
                    return response
            except Exception as e:
                return f"Error: {e}"
        return "Port not opened"

    def close_port(self):
        if self.ser and self.ser.is_open:
            self.ser.close()


def receive_thread(uart, output_text, status_label, stop_event):
    while not stop_event.is_set():
        response = uart.receive_message()
        if response and response != "Port not opened":
            output_text.insert(tk.END, f"Received: {response}\n")
            output_text.see(tk.END)
        stop_event.wait(0.1)  # Затримка між отриманнями даних


def start_gui():
    uart = UARTCommunication()
    stop_event = threading.Event()

    root = tk.Tk()
    root.title("UART Communication Interface")

    port_label = tk.Label(root, text="Select Port:")
    port_label.grid(row=0, column=0, padx=10, pady=10)
    port_var = tk.StringVar()
    port_combobox = ttk.Combobox(root, textvariable=port_var, values=uart.list_ports(), state="readonly")
    port_combobox.grid(row=0, column=1, padx=10, pady=10)

    def open_port_callback():
        status = uart.open_port(port_var.get())
        status_label.config(text=status)
        if "Connected" in status:
            stop_event.clear()
            threading.Thread(target=receive_thread, args=(uart, output_text, status_label, stop_event), daemon=True).start()

    open_button = tk.Button(root, text="Open Port", command=open_port_callback)
    open_button.grid(row=0, column=2, padx=10, pady=10)

    message_label = tk.Label(root, text="Message:")
    message_label.grid(row=1, column=0, padx=10, pady=10)
    message_entry = tk.Entry(root)
    message_entry.grid(row=1, column=1, padx=10, pady=10)

    def send_message_callback():
        status = uart.send_message(message_entry.get())
        status_label.config(text=status)

    send_button = tk.Button(root, text="Send", command=send_message_callback)
    send_button.grid(row=1, column=2, padx=10, pady=10)

    output_text = scrolledtext.ScrolledText(root, width=50, height=10, wrap=tk.WORD)
    output_text.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

    status_label = tk.Label(root, text="Status: Not connected", fg="blue")
    status_label.grid(row=3, column=0, columnspan=3, padx=10, pady=10)

    def on_closing():
        stop_event.set()
        uart.close_port()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    start_gui()
