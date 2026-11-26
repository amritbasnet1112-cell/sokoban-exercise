"""第13回 倉庫番・演習版（TODO 1〜3 + 手数制限つき + クリア評価）

第13回 倉庫番演習の完成版。
  TODO 1: WASD でプレイヤーを移動する（盤面外に出ない）
  TODO 2: 壁でプレイヤーの移動をブロックする
  TODO 3: 箱を押せるようにする（壁や他の箱でブロックされる）
  追加要素: ステージ4 と各ステージの手数制限、クリア評価と合計手数の表示
"""

# 画面の原点 (0, 0) は左上。右へ行くほど x が増え、下へ行くほど y が増える。
KEY_TO_VECTOR = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}

# # 壁, . ゴール, $ 箱, @ プレイヤー, * ゴール上の箱, + ゴール上のプレイヤー
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

# 各ステージの最大手数（MAP_TEXT と同じ順番）
MOVE_LIMITS = [10, 20, 30, 25]


def new_board(level_text):
    """ステージの文字列を読み、管理データを作る。引数：文字列。戻り値：辞書。"""
    rows = level_text.splitlines()
    if not rows or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("マップの横幅を揃えてください")
    board = {
        "size": (len(rows[0]), len(rows)),
        "solid": set(),  # 壁の座標集合
        "targets": set(),  # ゴールの座標集合
        "crates": set(),  # 箱の座標集合
        "hero": None,     # プレイヤーの座標
        "steps": 0,
        "limit": MOVE_LIMITS[MAP_TEXT.index(level_text)],  # このステージで使える手数上限
        "past": [],       # Undo 用の履歴
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
    left = board["limit"] - board["steps"]  # 残り手数
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
    """TODO 2: 指定マスに進入できるか判定する。

    (1) 盤面内である AND (2) 壁ではない 場合のみ True を返す。
    （デモ版では壁集合を "walls" と呼ぶが、ここでは board["solid"]）
    """
    inside = in_field(board, destination)
    is_wall = destination in board["solid"]
    return inside and not is_wall


def push_crate(board, crate_position, vector):
    """TODO 3: crate_position にある箱を vector 方向に1マス押せるか試す。

    箱が動けたら True、動けなければ False を返す。
    動けない場合は盤面を変更しない。
    """
    # 箱の移動先座標を計算する
    new_position = next_position(crate_position, vector)

    # 壁または盤面外でブロックされるか？
    if not can_enter(board, new_position):
        return False

    # 別の箱でブロックされるか？
    if new_position in board["crates"]:
        return False

    # 通路が空いているので箱を移動する
    board["crates"].remove(crate_position)
    board["crates"].add(new_position)
    return True


def apply_move(board, direction_key):
    """TODO 1-3: プレイヤーを移動する。移動できたら True を返す。"""
    # W/A/S/D 以外のキーは無視する
    if direction_key not in KEY_TO_VECTOR:
        return False

    # 手順1（TODO 1）: 現在のプレイヤー位置と移動先座標を求める
    vector = KEY_TO_VECTOR[direction_key]
    current = board["hero"]
    target = next_position(current, vector)

    # 手順2（TODO 1 + 2）: 盤面外または壁なら移動できない
    if not can_enter(board, target):
        return False

    # 箱を押す前に現在の箱の集合をコピーして保存し、Undo で復元できるようにする。
    # .copy() で別セットにしないと、履歴が同じ集合を参照して移動後に変わってしまう。
    crates_before = board["crates"].copy()

    # 手順3（TODO 3）: 移動先に箱があるか？あれば押すのを試みる
    if target in board["crates"]:
        pushed = push_crate(board, target, vector)
        if not pushed:
            return False  # 箱が動けない場合はプレイヤーも動かない

    # 手順4: 移動成功。履歴を記録し、プレイヤーを動かし、手数を増やす
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


def rating(board):
    """使った手数の割合から星評価を返す。引数：board。戻り値：文字列。"""
    ratio = board["steps"] / board["limit"]
    if ratio <= 0.5:
        return "★★★"
    elif ratio <= 0.8:
        return "★★☆"
    return "★☆☆"


def start():
    """キー入力・ステージ進行を管理する。戻り値：なし。"""
    index = 0
    total_steps = 0  # 全ステージの合計手数
    board = new_board(MAP_TEXT[index])
    while True:
        print_board(board)
        if completed(board):
            total_steps += board["steps"]
            print(f"ステージクリア！ 使用手数: {board['steps']}手 / 制限: {board['limit']}手")
            print("評価：" + rating(board))
            index += 1
            if index == len(MAP_TEXT):
                print(f"全ステージクリア！ 合計手数: {total_steps}手")
                break
            input("Enterで次のステージへ...")
            board = new_board(MAP_TEXT[index])
            continue
        # 手数制限は completed の後に判定するため、最終手でクリアした場合は成功扱いになる
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