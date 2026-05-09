import json
import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BOARD_FILE = REPO_ROOT / "board.json"
README_FILE = REPO_ROOT / "README.md"
IMAGES_DIR = REPO_ROOT / "images"

REPO = os.environ.get("GITHUB_REPOSITORY", "OWNER/REPO")

WINNING_LINES = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8],   
    [0, 3, 6], [1, 4, 7], [2, 5, 8],   
    [0, 4, 8], [2, 4, 6],              
]

COLOR_X = "#c8553d"
COLOR_O = "#2d6a8e"
COLOR_BG = "#fbf6ee"
COLOR_BG_HIGHLIGHT = "#fff4c2"
COLOR_BORDER = "#2b2417"
COLOR_HOVER_HINT = "#8a7e6b"


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


def cell_svg(value, is_winning, is_empty_clickable):
    bg = COLOR_BG_HIGHLIGHT if is_winning else COLOR_BG
    width = 140
    height = 140

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    ]
    parts.append(
        f'<rect width="{width}" height="{height}" fill="{bg}" '
        f'stroke="{COLOR_BORDER}" stroke-width="3"/>'
    )

    if value == "X":
        parts.append(
            f'<line x1="35" y1="35" x2="105" y2="105" '
            f'stroke="{COLOR_X}" stroke-width="10" stroke-linecap="round"/>'
        )
        parts.append(
            f'<line x1="105" y1="35" x2="35" y2="105" '
            f'stroke="{COLOR_X}" stroke-width="10" stroke-linecap="round"/>'
        )
    elif value == "O":
        parts.append(
            f'<circle cx="70" cy="70" r="36" fill="none" '
            f'stroke="{COLOR_O}" stroke-width="10"/>'
        )
    elif is_empty_clickable:
        parts.append(
            f'<text x="70" y="78" text-anchor="middle" '
            f'font-family="Georgia, serif" font-size="20" font-style="italic" '
            f'fill="{COLOR_HOVER_HINT}" opacity="0.55">play</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def write_cell_images(board, winning_line, game_over):
    IMAGES_DIR.mkdir(exist_ok=True)
    for i in range(9):
        is_winning = winning_line is not None and i in winning_line
        is_empty_clickable = (board[i] == "") and not game_over
        svg = cell_svg(board[i], is_winning, is_empty_clickable)
        with open(IMAGES_DIR / f"cell-{i}.svg", "w") as f:
            f.write(svg)


def write_status_banner(state):
    board = state["board"]
    result = check_winner(board)
    width = 440
    height = 60

    if result["winner"] == "draw":
        text = "It's a draw!"
        color = COLOR_BORDER
    elif result["winner"]:
        text = f"{result['winner']} wins!"
        color = COLOR_X if result["winner"] == "X" else COLOR_O
    else:
        text = f"{whose_turn(board)}'s turn"
        color = COLOR_X if whose_turn(board) == "X" else COLOR_O

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" fill="{COLOR_BG}" '
        f'stroke="{COLOR_BORDER}" stroke-width="2" rx="6"/>'
        f'<text x="{width // 2}" y="40" text-anchor="middle" '
        f'font-family="Georgia, serif" font-size="26" font-style="italic" '
        f'fill="{color}">{text}</text>'
        f'</svg>'
    )
    with open(IMAGES_DIR / "status.svg", "w") as f:
        f.write(svg)


def cell_link(i, board, game_over):
    img = f'<img src="images/cell-{i}.svg" width="120" height="120" alt="cell {i}"/>'
    if board[i] == "" and not game_over:
        title = f"tictactoe%7Cmove%7C{i}"
        body = "Just+click+%27Submit+new+issue%27+below."
        url = f"https://github.com/{REPO}/issues/new?title={title}&body={body}"
        return f'<a href="{url}">{img}</a>'
    return img


def render_board_html(board, game_over):
    rows = ['<table><tbody>']
    for r in range(3):
        rows.append("  <tr>")
        for c in range(3):
            i = r * 3 + c
            rows.append(f'    <td align="center" valign="middle">{cell_link(i, board, game_over)}</td>')
        rows.append("  </tr>")
    rows.append("</tbody></table>")
    return "\n".join(rows)


def render_reset_link():
    title = "tictactoe%7Creset"
    body = "Just+click+%27Submit+new+issue%27+below."
    url = f"https://github.com/{REPO}/issues/new?title={title}&body={body}"
    return f"[ Start a new game]({url})"


def render_readme(state, status_message=""):
    board = state["board"]
    result = check_winner(board)
    game_over = result["winner"] is not None

    write_cell_images(board, result["line"], game_over)
    write_status_banner(state)

    parts = []
    parts.append("# tic-tac-toe")
    parts.append("")
    parts.append("_a quiet little game on my GitHub profile — anyone can play_")
    parts.append("")
    parts.append('<img src="images/status.svg" alt="game status"/>')
    parts.append("")
    parts.append(render_board_html(board, game_over))
    parts.append("")

    if game_over:
        parts.append(render_reset_link())
    else:
        parts.append("Click an empty cell to make a move. " + render_reset_link())
    parts.append("")
    parts.append("---")
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
