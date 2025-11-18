from flask import Flask, render_template, redirect, url_for, request, session, jsonify
import random
from collections import deque
import time
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'


def generate_easy_pairs(n=18):
    pairs = []
    used = set()
    while len(pairs) < n:
        a, b = random.randint(2, 12), random.randint(2, 12)
        expr = f"{a}×{b}"
        value = str(a * b)
        if value not in used:
            pairs.append((expr, value))
            used.add(value)
    return pairs

def generate_medium_pairs(n=32):
    pairs = []
    used = set()
    while len(pairs) < n:
        if random.random() < 0.5:
            a, b = random.randint(10, 30), random.randint(2, 12)
            expr = f"{a}×{b}"
            value = str(a * b)
        else:
            b = random.randint(2, 12)
            value_num = random.randint(20, 100)
            a = value_num * b
            expr = f"{a}÷{b}"
            value = str(value_num)
        if value not in used:
            pairs.append((expr, value))
            used.add(value)
    return pairs

def generate_profi_pairs(n=50):
    pairs = []
    used = set()
    attempts = 0
    max_attempts = n * 10

    while len(pairs) < n and attempts < max_attempts:
        a, b = random.randint(10, 50), random.randint(2, 12)
        c = random.randint(2, 20)
        left = f"{a}×{b}"
        if (a * b) % c == 0:
            right = f"{a*b}÷{c}"
        else:
            right = f"{c}×{(a*b)//c}"
        value = str(a * b)

        if value not in used and left != right and left not in used and right not in used:
            pairs.append((left, right))
            used.add(value)
            used.add(left)
            used.add(right)
        attempts += 1

    if len(pairs) < n:
        raise ValueError(f"Could only generate {len(pairs)} unique pairs out of requested {n}")

    return pairs



def pad_board(b):
    rows, cols = len(b), len(b[0])
    new_board = [[None] * (cols + 2)]
    for row in b:
        new_board.append([None] + row + [None])
    new_board.append([None] * (cols + 2))
    return new_board

def init_game(level='easy'):
    global board, selected, pairs, reverse_pairs, board_size, TIME_LIMIT
    selected = []


    if level == 'easy':
        board_size = 6
        pairs = dict(generate_easy_pairs())
        TIME_LIMIT = 240
    elif level == 'medium':
        board_size = 8
        pairs = dict(generate_medium_pairs())
        TIME_LIMIT = 480
    elif level == 'profi':
        board_size = 10
        pairs = dict(generate_profi_pairs())
        TIME_LIMIT = 960
    else:
        board_size = 6
        pairs = dict(generate_easy_pairs())
        TIME_LIMIT = 240

    reverse_pairs = {v: k for k, v in pairs.items()}
    generate_valid_board()

    # Store in session
    session['board'] = board
    session['pairs'] = pairs
    session['reverse_pairs'] = reverse_pairs
    session['board_size'] = board_size
    session['selected'] = []



def in_bounds(r, c):
    return 0 <= r < len(board) and 0 <= c < len(board[0])

def is_match(word1, word2):
    return (pairs.get(word1) == word2) or (reverse_pairs.get(word1) == word2)

def has_valid_moves():
    items = [(r, c) for r in range(len(board)) for c in range(len(board[0])) if board[r][c]]
    for i, (r1, c1) in enumerate(items):
        for r2, c2 in items[i+1:]:
            if is_match(board[r1][c1], board[r2][c2]) and is_path_clear(board, r1, c1, r2, c2):
                return True
    return False

def is_path_clear(board, r1, c1, r2, c2):
    rows, cols = len(board), len(board[0])
    visited = [[[float('inf')] * 4 for _ in range(cols)] for _ in range(rows)]

    queue = deque()
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    for d, (dr, dc) in enumerate(directions):
        nr, nc = r1 + dr, c1 + dc
        if in_bounds(nr, nc) and (board[nr][nc] is None or (nr, nc) == (r2, c2)):
            visited[nr][nc][d] = 0
            queue.append((nr, nc, d, 0))

    while queue:
        r, c, dir, turns = queue.popleft()

        if (r, c) == (r2, c2):
            return True

        for d, (dr, dc) in enumerate(directions):
            nr, nc = r + dr, c + dc
            if not in_bounds(nr, nc):
                continue
            if (nr, nc) != (r2, c2) and board[nr][nc] is not None:
                continue
            new_turns = turns + (dir != d)
            if new_turns <= 2 and visited[nr][nc][d] > new_turns:
                visited[nr][nc][d] = new_turns
                queue.append((nr, nc, d, new_turns))

    return False


def generate_valid_board():
    while True:
        words = list(pairs.keys()) + list(reverse_pairs.keys())
        random.shuffle(words)
        real_board = [words[i:i + board_size] for i in range(0, len(words), board_size)]
        padded = pad_board(real_board)
        global board
        board = padded
        if has_valid_moves():
            break



selected = []

def is_game_complete():
    inner_board = [row[1:-1] for row in board[1:-1]]
    return all(cell is None for row in inner_board for cell in row)

def reshuffle_preserve_nones(board, board_size):
    inner_elements = []
    for i in range(1, board_size + 1):
        for j in range(1, board_size + 1):
            if board[i][j] is not None:
                inner_elements.append(board[i][j])
    
    random.shuffle(inner_elements)

    idx = 0
    for i in range(1, board_size + 1):
        for j in range(1, board_size + 1):
            if board[i][j] is not None:
                board[i][j] = inner_elements[idx]
                idx += 1


def reshuffle_board():
    flat = [board[i][j] for i in range(1, board_size+1) for j in range(1, board_size+1) if board[i][j] is not None]
    if not flat:
        return False
    while True:
        random.shuffle(flat)
        idx = 0
        for i in range(1, board_size+1):
            for j in range(1, board_size+1):
                if board[i][j] is not None:
                    board[i][j] = flat[idx]
                    idx += 1
        if has_valid_moves():
            return True



@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/start/<level>')
def start_game(level):
    session['difficulty'] = level
    init_game(level)
    session['end_time'] = time.time() + TIME_LIMIT
    return redirect(url_for('game'))

@app.route('/set_difficulty/<level>')
def set_difficulty(level):
    session['difficulty'] = level
    init_game(level)
    session['end_time'] = time.time() + TIME_LIMIT
    return redirect(url_for('game'))


@app.route('/reset')
def reset():
    init_game('easy')
    session['end_time'] = time.time() + TIME_LIMIT
    return redirect(url_for('game'))

@app.route('/timeout')
def timeout():
    return render_template('game_over.html')

@app.route('/congrats')
def congrats():
    return render_template('congrats.html')


@app.route('/game')
def game():
    time_left = int(max(0, session.get('end_time', time.time()) - time.time()))
    if time_left <= 0:
        return redirect(url_for('timeout'))

    # Load state from session
    current_board = session.get('board', board)
    current_selected = session.get('selected', [])

    cropped_board = [row[1:-1] for row in current_board[1:-1]]
    board_with_indices = [(i, list(enumerate(row))) for i, row in enumerate(cropped_board)]
    message = None
    return render_template('index.html', board_with_indices=board_with_indices, selected=current_selected, time_left=time_left, time_limit=TIME_LIMIT)

@app.route('/api/select/<int:row>/<int:col>', methods=['POST'])
def api_select_tile(row, col):
    """AJAX endpoint for tile selection - no page reload"""
    # Load state from session
    current_board = session.get('board')
    if not current_board:
        return jsonify({'error': 'No game in progress'}), 400

    current_selected = session.get('selected', [])
    current_pairs = session.get('pairs', {})
    current_reverse_pairs = session.get('reverse_pairs', {})
    current_board_size = session.get('board_size', 6)

    # Convert selected to list of tuples if needed
    current_selected = [tuple(item) if isinstance(item, list) else item for item in current_selected]

    if (row, col) in current_selected:
        current_selected.remove((row, col))
    else:
        current_selected.append((row, col))

    matched = False
    reshuffled = False
    game_won = False

    if len(current_selected) == 2:
        (r1, c1), (r2, c2) = current_selected
        word1, word2 = current_board[r1+1][c1+1], current_board[r2+1][c2+1]

        # Check if match using session pairs
        is_valid_match = (current_pairs.get(word1) == word2) or (current_reverse_pairs.get(word1) == word2)

        if is_valid_match and is_path_clear(current_board, r1+1, c1+1, r2+1, c2+1):
            current_board[r1+1][c1+1] = None
            current_board[r2+1][c2+1] = None
            matched = True

        current_selected = []
        remaining = [cell for row in current_board for cell in row if cell]

        # Update session with modified board
        session['board'] = current_board
        session['selected'] = current_selected

        if not remaining:
            game_won = True

        # Check if valid moves exist
        if not game_won:
            items = [(r, c) for r in range(len(current_board)) for c in range(len(current_board[0])) if current_board[r][c]]
            has_moves = False
            for i, (r1, c1) in enumerate(items):
                for r2, c2 in items[i+1:]:
                    w1, w2 = current_board[r1][c1], current_board[r2][c2]
                    is_valid = (current_pairs.get(w1) == w2) or (current_reverse_pairs.get(w1) == w2)
                    if is_valid and is_path_clear(current_board, r1, c1, r2, c2):
                        has_moves = True
                        break
                if has_moves:
                    break

            if not has_moves:
                # Reshuffle
                flat = [current_board[i][j] for i in range(1, current_board_size+1) for j in range(1, current_board_size+1) if current_board[i][j] is not None]
                if flat:
                    random.shuffle(flat)
                    idx = 0
                    for i in range(1, current_board_size+1):
                        for j in range(1, current_board_size+1):
                            if current_board[i][j] is not None:
                                current_board[i][j] = flat[idx]
                                idx += 1
                    session['board'] = current_board
                    reshuffled = True
    else:
        # Update selected in session
        session['selected'] = current_selected

    # Return updated board state
    cropped_board = [row[1:-1] for row in current_board[1:-1]]

    return jsonify({
        'success': True,
        'board': cropped_board,
        'selected': current_selected,
        'matched': matched,
        'reshuffled': reshuffled,
        'game_won': game_won
    })

@app.route('/select/<int:row>/<int:col>')
def select_tile(row, col):
    """Fallback route for non-JS browsers"""
    return redirect(url_for('game'))




if __name__ == '__main__':
    # Don't initialize session outside request context
    # port = int(os.environ.get('PORT', 5000))
    # app.run(host='0.0.0.0', port=port)
    app.run(debug=True)
