import socket
import threading
import sys

HOST_IP = '10.80.93.19'
PORT_NO = 5556
PLAYERS_PER_MATCH = 2

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

def determine_winner(p1_move, p2_move, p1_score, p2_score):
    if p1_move == p2_move:
        p1_score.ties += 1
        p2_score.ties += 1
        return "It's a tie!", "It's a tie!"

    wins = {'rock': 'scissors', 'paper': 'rock', 'scissors': 'paper'}
    if wins[p1_move] == p2_move:
        p1_score.wins += 1
        p2_score.losses += 1
        return "You win!", "You lose!"
    else:
        p1_score.losses +=1
        p2_score.wins += 1
        return "You lose!", "You win!"

def handle_player(conn, player_id, match_id, round_num, state):
    try:
        prompt = f"[Match {match_id} - Round {round_num}] Enter rock, paper, sissors, or 'exit': "
        conn.sendall(prompt.encode())

        while not state['stop_event'].is_set():
            data = conn.recv(1024)
            if not data:
                print(f"[Match {match_id}] Player {player_id} closed their client.")
                state['stop_reason'] = f"Player {player_id} disconnected."
                state['stop_event'].set()
                return
                #raise ConnectionResetError()

            move = data.decode().strip().lower()
            if move == 'exit':
                print(f"[Match {match_id}] Player {player_id} exited the match.")
                state['stop_reason'] = f"Player {player_id} left the match."
                state['stop_event'].set()
                return

            if move in ('rock', 'paper', 'scissors'):
                with state['lock']:
                    state['moves'][player_id] = move
                conn.sendall("Move locked in. Waiting for opponent...\n".encode())
                break
            else:
                conn.sendall("Invalid move. Enter rock, paper, or scissors: ".encode())

    except (ConnectionResetError, BrokenPipeError, OSError):
        print(f"[Match {match_id}] Player {player_id} lost connection.")
        state['stop_reason'] = f"Player {player_id} disconnected."
        state['stop_event'].set()


class Score:
    wins: int = 0
    losses: int = 0
    ties: int = 0


def run_head_to_head(match_id, pair_conns):
    state = {
        'players': {1: pair_conns[0], 2: pair_conns[1]},
        'p1_score': Score(),
        'p2_score': Score(),
        'moves': {},
        'lock': threading.Lock(),
        'stop_event': threading.Event(),
        'stop_reason': "Match ended."
    }

    round_num = 1

    try:
        while not state['stop_event'].is_set():
            # Reset moves each round
            state['moves'].clear()
            threads = []

            for player_id in range(1, PLAYERS_PER_MATCH + 1):
                conn = state['players'][player_id]
                t = threading.Thread(
                    target = handle_player,
                    args=(conn, player_id, match_id, round_num, state),
                    daemon=True
                )
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            # Check for exit or disconnects
            if state['stop_event'].is_set() or len(state['moves']) < PLAYERS_PER_MATCH:
                print(f"[Match {match_id}] Aborted due to disconnect.")
                with state['lock']:
                    for remaining_conn in state['players'].values():
                        try:
                            remaining_conn.sendall("\nOppoenent disconnected. Match Closed.\n".encode())
                            remaining_conn.close()
                        except OSError:
                            pass
                    state['players'].clear()
                    pass
                continue

            # Send round results
            m1, m2 = state['moves'][1], state['moves'][2]
            p1_msg, p2_msg = determine_winner(m1, m2, state['p1_score'], state['p2_score'])
            try:
                pair_conns[0].sendall(f"\nYou chose {m1}, opponent chose {m2}, {p1_msg}\n".encode())
                pair_conns[0].sendall(f"\nWins={state['p1_score'].wins} Losses={state['p1_score'].losses} Ties= {state['p1_score'].ties}\n".encode())
                pair_conns[1].sendall(f"\nYou chose {m2}, opponent chose {m1}, {p2_msg}\n".encode())
                pair_conns[1].sendall(f"\nWins={state['p2_score'].wins} Losses={state['p2_score'].losses} Ties= {state['p2_score'].ties}\n".encode())
            except OSError:
                pass

            print(f"[Match {match_id}] - Round {round_num}] {m1} vs {m2}")
            round_num += 1
    finally:
        for conn in pair_conns:
            try:
                conn.close()
            except OSError:
                pass
        print(f"[Match {match_id}] All sockets closed.")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4 TCP socket
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # allow port reuse immediately after server shutdown
    server.bind((HOST_IP, PORT_NO))  # bind host address and port together
    server.listen(2)
    print(f"Server listening on {HOST_IP}:{PORT_NO}. Waiting for 2 players...")

    waiting_player = None
    match_counter = 0

    try:
        while True:
            conn, addr = server.accept()
            if waiting_player is None:
                try:
                    conn.sendall("Connected! Waiting for an oppoenent to join...\n".encode())
                    waiting_player = (conn, addr)
                    print(f"Player queued from {addr}. Waiting for a partner...")
                except OSError:
                    conn.close()

            else:
                p1_conn, p1_addr = waiting_player
                try:
                    p1_conn.sendall("Opponent matched! Starting game...\n".encode())
                except OSError:
                    p1_conn.close()
                    conn.sendall("Connected! Waiting for an oppoenent to join...\n".encode())
                    waiting_player = (conn, addr)
                    print(f"Previous queued player dropped. {addr} is now waiting...")
                    continue

                match_counter += 1
                print(f"[Match {match_counter}] Paired {p1_addr} vs {addr}")
                waiting_player = None

                match_thread = threading.Thread(
                    target=run_head_to_head,
                    args=(match_counter, [p1_conn, conn]),
                    daemon=True
                )
                match_thread.start()

    except KeyboardInterrupt:
        print(f"\nShutting down matchmaking server...")
    finally:
        if waiting_player:
            waiting_player[0].close()
        server.close()

if __name__ == '__main__':
    try:
        start_server()
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
        sys.exit(0)