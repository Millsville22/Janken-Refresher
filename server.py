import socket
import threading
import sys

HOST_IP = '10.80.93.19'
#HOST_IP = '127.0.0.1'
PORT_NO = 5556

def get_move(conn, player, moves):
    try:
        conn.sendall(f"Welcome Player {player}! Enter rock, paper, or scissors: ".encode())
        move = conn.recv(1024).decode().strip().lower()

        while move not in ["rock", "paper", "scissors"]:
            conn.sendall("Invalid move. Enter rock, paper, or scissors: ".encode())
            move = conn.recv(1024).decode().strip().lower()

        moves[player] = move
        conn.sendall("Move locked in. Waiting for opponent...\n".encode())
    except ConnectionResetError:
        moves[player] = None

def determine_winner(p1_move, p2_move):
    if p1_move == p2_move:
        return "It's a tie!", "It's a tie!"
    elif (
        (p1_move == "rock" and p2_move == "scissors")
        or (p1_move == "paper" and p2_move == "rock")
        or (p1_move == "scissors" and p2_move == "paper")
    ):
        return "You win!", "You lose!"
    else:
        return "You lose!", "You win!"

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4 TCP socket
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # allow port reuse immediately after server shutdown
    server.bind((HOST_IP, PORT_NO))  # bind host address and port together
    server.listen(2)
    print(f"Server listening on {HOST_IP}:{PORT_NO}. Waiting for 2 players...")

    players=[]
    while len(players) < 2:
        conn, addr = server.accept()
        print(f"Player {len(players) + 1} connected from {addr}")
        players.append(conn)
        if len(players) == 1:
            conn.sendall("Connected! Waiting for Player 2 to join...\n".encode())

    moves = {}

    # Different threads for each player
    t1 = threading.Thread(target=get_move, args=(players[0], 1, moves))
    t2 = threading.Thread(target=get_move, args=(players[1], 2, moves))

    t1.start()
    t2.start()

    print(f"I am here")

    # Waiting for both player's moves
    t1.join()
    t2.join()

    if moves.get(1) and moves.get(2):
        p1_msg, p2_msg = determine_winner(moves[1], moves[2])
        players[0].sendall(f"\nYou chose {moves[1]}, opponent chose {moves[2]}, {p1_msg}\n".encode())
        players[1].sendall(f"\nYou chose {moves[2]}, opponent chose {moves[1]}, {p2_msg}\n".encode())
    else:
        for p in players:
            try:
                p.sendall("\nGame aborted: a player disconnected.\n".encode())
            except OSError:
                pass

    for p in players:
        p.close()
    server.close()
    print("Match finished. Server Closed.")

if __name__ == '__main__':
    try:
        start_server()
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
        sys.exit(0)