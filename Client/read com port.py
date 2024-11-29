import serial
import serial.tools.list_ports
def main():
    incoming_data = 0

    # Отримати список доступних COM портів
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("Не знайдено доступних COM портів.")
        return

    print("Доступні порти:")
    for i, port in enumerate(ports):
        print(f"{i + 1}: {port.device}")

    # Вибір порту
    port_index = int(input("Виберіть номер порту: ")) - 1
    com_port = ports[port_index].device

    # Вибір швидкості передачі даних (baud rate)
    baud_rate = 9600

    try:
        # Відкрити COM порт
        ser = serial.Serial(com_port, baud_rate, timeout=1)
        print(f"Підключено до {com_port} на швидкості {baud_rate}.")

        while True:
            # Читання даних з COM порту
            if ser.in_waiting > 0:
                incoming_data = ser.readline().decode('utf-8').rstrip()
                print(f"Отримано: {incoming_data}")
            # if incoming_data == 'Starting Main Loop':

                # user_input = input("Відправити (введіть 'exit' для виходу): ")
                # if user_input.lower() == 'exit':
                #     break
                #
                # ser.write(user_input.encode('utf-8'))

    except serial.SerialException as e:
        print(f"Помилка: {e}")

    finally:
        if ser.is_open:
            ser.close()
            print("COM порт закрито.")


if __name__ == "__main__":
    main()
