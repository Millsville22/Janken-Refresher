import random
import sys

def bot(choice: str):
    roll = random.randint(0,2)
    match roll:
        case 0:
            choice = "rock"
        case 1:
            choice = "paper"
        case 2:
            choice = "scissors"

    return choice

def compare(player1Choice: str, player2Choice: str, winner: str):
    if player1Choice == player2Choice:
        winner = "tie"
    elif (
        (player1Choice == "rock" and player2Choice == "scissors")
        or (player1Choice == "paper" and player2Choice == "rock")
        or (player1Choice == "scissors" and player2Choice == "paper")
    ):
        winner = "player"
    else:
        winner = "bot"

    return winner

def game(live: bool):
    winner: str = ""
    bot_choice: str = ""
    validUserChoice: bool = False
    while not validUserChoice:
        user_choice = input("Type Rock, Paper, Scissors to play. Type exit to stop: ")
        match user_choice.lower().strip():
            case "rock" | "paper" | "scissors":
                validUserChoice = True
            case "exit":
                print("Quitting the game")
                return False
            case _:
                print("Invalid input")

    bot_choice = bot(bot_choice)
    winner = compare(user_choice, bot_choice, winner)

    print("The bot chose " + bot_choice + "!\nthe winner is " + winner)

    validUserChoice = False
    while not validUserChoice:
        replay = input("Would you like to play again? Enter yes or no.")
        match replay.lower().strip():
            case "yes":
                validUserChoice = True
                live = True
            case "no":
                validUserChoice = True
                live = False
                print("You have chosen to end the game.")
            case _:
                print("Invalid input")

    return live


def main():
    live = True
    print("Welcome to Janken!")
    while live:
        live = game(live)

    return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
        sys.exit(0)