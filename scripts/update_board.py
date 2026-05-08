import json
import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BOARD_FILE = REPO_ROOT / "board.json"
README_FILE = REPO_ROOT / "README.md"

REPO = os.environ.get("GITHUB_REPOSITORY", "OWNER/REPO")

WINNING_LINES = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],   
    [0, 3, 6], [1, 4, 7], [2, 5, 8],   
    [0, 4, 8], [2, 4, 6],              
]


def load_state():
    with open(BOARD_FILE) as f:
        return json.load(f)


def save_state(state):
    with open(BOARD_FILE, "w") as f:
        json.dump(state, f, indent=2)


def whose_turn(board):
    x = board.count("X")
    o = board.count("O")
    return "X" if x == o else "O"


def check_winner(board):
    for line in WINNING_LINES:
        a, b, c = line
        if board[a] and board[a] == board[b] == board[c]:
            return {"winner": board[a], "line": line}
    if all(cell != "" for cell in board):
        return {"winner": "draw", "line": None}
    return {"winner": None, "line": None}


def apply_move(state, index, username):
    board = state["board"]

    if check_winner(board)["winner"] is not None:
        return False, "the game is already over — start a new round"

    if not (0 <= index <= 8):
        return False, f"invalid cell index: {index}"

    if board[index] != "":
        return False, f"cell {index} is already taken"

    symbol = whose_turn(board)
    board[index] = symbol
    state["moves"].append({"index": index, "symbol": symbol, "user": username})
    return True, None


def reset_game(state):
    state["board"] = ["", "", "", "", "", "", "", "", ""]
    state["moves"] = []


def render_board_table(board, winning_line=None):
    rows = []
    rows.append("|   |   |   |")
    rows.append("|---|---|---|")
    for r in range(3):
        cells = []
        for c in range(3):
            i = r * 3 + c
            value = board[i] if board[i] else " "

            if winning_line and i in winning_line:
                value = f"**{value}**"
            cells.append(value)
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)


def render_move_links(board, game_over):
    if game_over:
        return ""

    symbol = whose_turn(board)

    rows = []
    rows.append(f"### Click a cell to play **{symbol}**:")
    rows.append("")
    rows.append("|   |   |   |")
    rows.append("|---|---|---|")

    for r in range(3):
        cells = []
        for c in range(3):
            i = r * 3 + c
            if board[i]:
                cells.append(board[i])
            else:
                title = f"tictactoe%7Cmove%7C{i}"
                body = "Just+click+%27Submit+new+issue%27+below.+You+don%27t+need+to+do+anything+else."
                url = f"https://github.com/{REPO}/issues/new?title={title}&body={body}"
                cells.append(f"[ play ]({url})")
        rows.append("| " + " | ".join(cells) + " |")

    return "\n".join(rows)


def render_reset_link():
    title = "tictactoe%7Creset"
    body = "Just+click+%27Submit+new+issue%27+below."
    url = f"https://github.com/{REPO}/issues/new?title={title}&body={body}"
    return f"[Start a new game]({url})"


def render_readme(state, status_message=""):
    board = state["board"]
    result = check_winner(board)
    game_over = result["winner"] is not None

    parts = ["# Tic-Tac-Toe on my GitHub Profile", ""]
    parts.append("Anyone with a GitHub account can play. Click a cell to make a move.")
    parts.append("")

    if result["winner"] == "draw":
        parts.append("## It's a draw!")
    elif result["winner"]:
        parts.append(f"##  **{result['winner']}** wins!")
    else:
        parts.append(f"## Turn: **{whose_turn(board)}**")
    parts.append("")

    parts.append(render_board_table(board, result["line"]))
    parts.append("")

    if game_over:
        parts.append(render_reset_link())
    else:
        parts.append(render_move_links(board, game_over))
        parts.append("")
        parts.append("---")
        parts.append(render_reset_link())
    parts.append("")

    if status_message:
        parts.append("")
        parts.append(f"> _{status_message}_")

    return "\n".join(parts) + "\n"


def parse_command(title):
    parts = title.strip().split("|")
    if len(parts) < 2 or parts[0] != "tictactoe":
        return None, None
    if parts[1] == "reset":
        return "reset", None
    if parts[1] == "move" and len(parts) == 3:
        try:
            index = int(parts[2])
            return "move", index
        except ValueError:
            return None, None
    return None, None


def main():
    if len(sys.argv) < 3:
        print("usage: update_board.py <issue_title> <issue_user>")
        sys.exit(1)

    issue_title = sys.argv[1]
    issue_user = sys.argv[2]

    command, arg = parse_command(issue_title)
    state = load_state()

    status = ""
    if command == "move":
        ok, err = apply_move(state, arg, issue_user)
        if not ok:
            status = f"@{issue_user}'s move was rejected: {err}"
        else:
            status = f"@{issue_user} played in cell {arg}"
    elif command == "reset":
        reset_game(state)
        status = f"@{issue_user} started a new game"
    else:
        status = f"unrecognized command from @{issue_user}"

    save_state(state)

    readme = render_readme(state, status)
    with open(README_FILE, "w") as f:
        f.write(readme)


if __name__ == "__main__":
    main()
