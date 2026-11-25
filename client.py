import socket
import sys

HOST_IP = '10.80.93.19'
#HOST_IP = '127.0.0.1'
PORT_NO = 5556

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"Connecting to {HOST_IP}:{PORT_NO}...", flush=True)

    try:
        client.connect((HOST_IP, PORT_NO))
        print("Socket connected! Waiting for server data...\n", flush=True)
    except ConnectionRefusedError:
        print("Connection refused: Make sure server.py is running first.", flush=True)
        return

    while True:
        data = client.recv(1024).decode()
        if not data:
            break

        print(data, end="", flush=True)


        if data.endswith(": "):
            move = input()
            client.sendall(move.encode())

    client.close()

if __name__ == '__main__':
    try:
        start_client()
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
        sys.exit(0)