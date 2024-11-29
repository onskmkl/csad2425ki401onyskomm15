import unittest
from unittest.mock import patch, MagicMock
import serial
from UART_COMMUNICATION_SW import UARTCommunication  # Замініть на ім'я вашого файлу

class TestUARTCommunication(unittest.TestCase):

    @patch('serial.tools.list_ports.comports')
    def test_list_ports(self, mock_comports):
        # Мокаємо список портів
        mock_comports.return_value = [
            MagicMock(device='COM11'),
            MagicMock(device='COM12')
        ]

        uart = UARTCommunication()
        ports = uart.list_ports()

        # Перевіряємо, чи повернутий список портів правильний
        self.assertEqual(ports, ['COM11', 'COM12'])

    @patch('serial.Serial')
    def test_open_port_success(self, mock_serial):
        uart = UARTCommunication()

        # Тестуємо успішне відкриття порту
        status = uart.open_port('COM11')
        self.assertIn('Connected to COM11', status)

        # Перевіряємо, чи створився об'єкт серіалу
        mock_serial.assert_called_with('COM11', 9600, timeout=1)

    @patch('serial.Serial')
    def test_open_port_failure(self, mock_serial):
        # Мокаємо виключення при відкритті порту
        mock_serial.side_effect = serial.SerialException("Could not open port")

        uart = UARTCommunication()
        status = uart.open_port('COM11')

        # Перевіряємо, чи повертається правильне повідомлення про помилку
        self.assertIn('Error: Could not open port COM11', status)

    @patch('serial.Serial')
    def test_send_message(self, mock_serial):
        mock_serial_instance = MagicMock()
        mock_serial.return_value = mock_serial_instance

        uart = UARTCommunication()
        uart.open_port('COM11')
        status = uart.send_message('Test Message')

        # Перевіряємо, чи повідомлення було надіслано
        mock_serial_instance.write.assert_called_with(b'Test Message\n')
        self.assertIn('Sent: Test Message', status)

    @patch('serial.Serial')
    def test_receive_message(self, mock_serial):
        mock_serial_instance = MagicMock()
        mock_serial_instance.readline.return_value = b'Test Response\n'
        mock_serial.return_value = mock_serial_instance

        uart = UARTCommunication()
        uart.open_port('COM11')
        response = uart.receive_message()

        # Перевіряємо, чи отримане повідомлення правильне
        self.assertEqual(response, 'Test Response')

if __name__ == '__main__':
    unittest.main()