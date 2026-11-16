"""第13回 倉庫番・演習版（TODO 1〜3 + 手数制限つき）

Week 13 Sokoban exercise, completed.
  TODO 1: move the player with WASD (stay inside the board)
  TODO 2: walls block the player
  TODO 3: boxes can be pushed (blocked by walls or other boxes)
  Extra : stage 4 and a move limit for every stage
"""

# Screen origin (0, 0) is top-left. Right -> x increases, down -> y increases.
KEY_TO_VECTOR = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}

# # wall, . goal, $ box, @ player, * box on goal, + player on goal
MAP_TEXT = [
    """#########
#       #
#  .    #
#  $    #
#  @    #
#       #
#########""",
    """##########
#        #
#  ..    #
#  $$    #
#   @    #
#        #
##########""",
    """###########
#         #
#         #
#    #    #
#    #    #
#  . # $  #
#      @  #
###########""",
    """#########
#       #
# .  $  #
#   @   #
# $  .  #
#       #
#########""",
]

# Maximum number of moves for each stage (same order as MAP_TEXT)
MOVE_LIMITS = [10, 20, 30, 25]


def new_board(level_text):
    """ステージの文字列を読み、管理データを作る。引数：文字列。戻り値：辞書。"""
    rows = level_text.splitlines()
    if not rows or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("マップの横幅を揃えてください")
    board = {
        "size": (len(rows[0]), len(rows)),
        "solid": set(),  # wall positions
        "targets": set(),  # goal positions
        "crates": set(),  # box positions
        "hero": None,     # player position
        "steps": 0,
        "limit": MOVE_LIMITS[MAP_TEXT.index(level_text)],  # moves allowed in this stage
        "past": [],       # history for Undo
    }
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            p = (x, y)
            if ch == "#":
                board["solid"].add(p)
            if ch in ".+*":
                board["targets"].add(p)
            if ch in "$*":
                board["crates"].add(p)
            if ch in "@+":
                if board["hero"] is not None:
                    raise ValueError("プレイヤーは1人にしてください")
                board["hero"] = p
    if board["hero"] is None or not board["crates"] or len(board["crates"]) != len(board["targets"]):
        raise ValueError("プレイヤー1人、箱とゴールは同数にしてください")
    return board


def print_board(board):
    """現在の盤面を画面に表示する。引数：board。戻り値：なし。"""
    width, height = board["size"]
    print("\n" * 2 + "=== SOKOBAN : EXERCISE ===")
    print("# 壁  . ゴール  $ 箱  @ プレイヤー  * ゴール上の箱")
    for y in range(height):
        output = ""
        for x in range(width):
            p = (x, y)
            if p == board["hero"]:
                output += "+" if p in board["targets"] else "@"
            elif p in board["crates"]:
                output += "*" if p in board["targets"] else "$"
            elif p in board["solid"]:
                output += "#"
            elif p in board["targets"]:
                output += "."
            else:
                output += " "
        print(output)
    left = board["limit"] - board["steps"]  # moves left
    print(f"移動回数: {board['steps']} (残り {left}) | WASD 移動 / U 戻す / R 再開 / Q 終了")


def in_field(board, point):
    """座標が盤面内か調べる。引数：board, (x,y)。戻り値：bool。"""
    x, y = point
    w, h = board["size"]
    return 0 <= x < w and 0 <= y < h


def next_position(origin, vector):
    """座標の足し算。引数：(x,y), (dx,dy)。戻り値：(x2,y2)。"""
    return (origin[0] + vector[0], origin[1] + vector[1])


def can_enter(board, destination):
    """TODO 2: Can something stand on this cell?

    True only if the cell is (1) inside the board AND (2) not a wall.
    (The demo calls the wall set "walls"; here it is board["solid"].)
    """
    inside = in_field(board, destination)
    is_wall = destination in board["solid"]
    return inside and not is_wall


def push_crate(board, crate_position, vector):
    """TODO 3: Try to push the box at crate_position one cell in direction vector.

    Returns True if the box moved, False if it could not move.
    If it cannot move, nothing is changed.
    """
    # Where would the box end up?
    new_position = next_position(crate_position, vector)

    # Blocked by a wall or the board edge?
    if not can_enter(board, new_position):
        return False

    # Blocked by another box?
    if new_position in board["crates"]:
        return False

    # The way is free: move the box.
    board["crates"].remove(crate_position)
    board["crates"].add(new_position)
    return True


def apply_move(board, direction_key):
    """TODO 1-3: Move the player. Returns True if the move succeeded."""
    # Ignore keys that are not W/A/S/D.
    if direction_key not in KEY_TO_VECTOR:
        return False

    # Step 1 (TODO 1): where is the player now, and where does he want to go?
    vector = KEY_TO_VECTOR[direction_key]
    current = board["hero"]
    target = next_position(current, vector)

    # Step 2 (TODO 1 + 2): outside the board or a wall -> cannot move.
    if not can_enter(board, target):
        return False

    # Save the boxes BEFORE any push, so Undo can restore them.
    # .copy() makes a separate set; without it the history would
    # point to the same set and change when the box moves.
    crates_before = board["crates"].copy()

    # Step 3 (TODO 3): is there a box in the way? Then try to push it.
    if target in board["crates"]:
        pushed = push_crate(board, target, vector)
        if not pushed:
            return False  # box is stuck -> the player does not move either

    # Step 4: the move succeeded. Record history, move player, count step.
    board["past"].append((current, crates_before))
    board["hero"] = target
    board["steps"] += 1
    return True


def step_back(board):
    """Undoを実行。引数：board。戻り値：なし。"""
    if board["past"]:
        board["hero"], board["crates"] = board["past"].pop()
        board["steps"] -= 1


def completed(board):
    """すべての箱がゴール上にあるか調べる。引数：board。戻り値：bool。"""
    return board["crates"] == board["targets"]


def start():
    """キー入力・ステージ進行を管理する。戻り値：なし。"""
    index = 0
    board = new_board(MAP_TEXT[index])
    while True:
        print_board(board)
        if completed(board):
            print("ステージクリア！")
            index += 1
            if index == len(MAP_TEXT):
                print("全ステージクリア！")
                break
            input("Enterで次のステージへ...")
            board = new_board(MAP_TEXT[index])
            continue
        # Move limit: checked AFTER "completed", so clearing the stage
        # on the very last allowed move still counts as a win.
        if board["steps"] >= board["limit"]:
            print("手数オーバー！ステージをやり直します。")
            input("Enterで再挑戦...")
            board = new_board(MAP_TEXT[index])
            continue
        key = input("操作 > ").strip().lower()[:1]
        if key == "q":
            break
        if key == "r":
            board = new_board(MAP_TEXT[index])
        elif key == "u":
            step_back(board)
        else:
            apply_move(board, key)


if __name__ == "__main__":
    start()
