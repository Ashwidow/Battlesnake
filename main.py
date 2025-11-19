import random
import typing
from collections import deque

def info() -> typing.Dict:
    print("FIGHT")

    return {
        "apiversion": "1",
        "author": "PythonicFury",
        "color": "#0061ff",
        "head": "bonhomme",
        "tail": "mlh-gene",
    }

def start(game_state: typing.Dict):
    print("GAME START")
def end(game_state: typing.Dict):
    print("GAME OVER")

def flood_fill(start_pos: typing.Dict, board_width: int, board_height: int, occupied_spaces: set) -> int:
    """Calculate available space from a position using flood fill"""
    visited = set()
    start_tuple = (start_pos['x'], start_pos['y'])
    queue = deque([start_tuple])
    visited.add(start_tuple)

    while queue:
        x, y = queue.popleft()

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy

            if (nx, ny) in visited:
                continue
            if nx < 0 or nx >= board_width or ny < 0 or ny >= board_height:
                continue
            if (nx, ny) in occupied_spaces:
                continue

            visited.add((nx, ny))
            queue.append((nx, ny))

    return len(visited)

def get_occupied_spaces(game_state: typing.Dict, exclude_tail_if_safe: bool = False) -> set:
    """Get all occupied spaces on the board"""
    occupied = set()
    food_positions = {(f['x'], f['y']) for f in game_state['board']['food']} if 'food' in game_state['board'] else set()

    for snake in game_state['board']['snakes']:
        # Add body segments
        for i, segment in enumerate(snake['body']):
            is_tail = (i == len(snake['body']) - 1)
            tail_pos = (segment['x'], segment['y'])

            # Only exclude tail if it will definitely move (not on food)
            if exclude_tail_if_safe and is_tail and tail_pos not in food_positions:
                continue

            occupied.add((segment['x'], segment['y']))

    # Add hazards if they exist
    if 'hazards' in game_state['board']:
        for hazard in game_state['board']['hazards']:
            occupied.add((hazard['x'], hazard['y']))

    return occupied

def manhattan_distance(pos1: typing.Dict, pos2: typing.Dict) -> int:
    """Calculate Manhattan distance between two positions"""
    return abs(pos1['x'] - pos2['x']) + abs(pos1['y'] - pos2['y'])

def get_next_position(head: typing.Dict, direction: str) -> typing.Dict:
    """Get the position after moving in a direction"""
    if direction == "up":
        return {"x": head["x"], "y": head["y"] + 1}
    elif direction == "down":
        return {"x": head["x"], "y": head["y"] - 1}
    elif direction == "left":
        return {"x": head["x"] - 1, "y": head["y"]}
    elif direction == "right":
        return {"x": head["x"] + 1, "y": head["y"]}
    return head

def simulate_snake_move(snake_body: list, direction: str, ate_food: bool = False) -> list:
    """Simulate a snake moving in a direction"""
    head = snake_body[0].copy()

    if direction == "up":
        new_head = {"x": head["x"], "y": head["y"] + 1}
    elif direction == "down":
        new_head = {"x": head["x"], "y": head["y"] - 1}
    elif direction == "left":
        new_head = {"x": head["x"] - 1, "y": head["y"]}
    elif direction == "right":
        new_head = {"x": head["x"] + 1, "y": head["y"]}
    else:
        return snake_body

    new_body = [new_head] + snake_body[:-1] if not ate_food else [new_head] + snake_body
    return new_body

def get_valid_moves(head: typing.Dict, board_width: int, board_height: int, occupied: set, neck: typing.Dict = None) -> list:
    """Get all valid moves from a position"""
    valid = []

    for direction in ["up", "down", "left", "right"]:
        next_pos = get_next_position(head, direction)

        # Check bounds
        if next_pos["x"] < 0 or next_pos["x"] >= board_width:
            continue
        if next_pos["y"] < 0 or next_pos["y"] >= board_height:
            continue

        # Check if position is occupied
        if (next_pos["x"], next_pos["y"]) in occupied:
            continue

        # Check neck constraint
        if neck and next_pos["x"] == neck["x"] and next_pos["y"] == neck["y"]:
            continue

        valid.append(direction)

    return valid

def lookahead_survival(game_state: typing.Dict, direction: str, depth: int = 3) -> tuple:
    """
    Look ahead multiple moves to check if we can survive
    Returns (can_survive, min_space_found, trap_score)
    """
    if depth == 0:
        return (True, 100, 0)

    head = game_state["you"]["body"][0]
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']

    # Simulate our move
    next_pos = get_next_position(head, direction)

    # Check if move is out of bounds
    if next_pos["x"] < 0 or next_pos["x"] >= board_width:
        return (False, 0, -1000)
    if next_pos["y"] < 0 or next_pos["y"] >= board_height:
        return (False, 0, -1000)

    # Create occupied spaces for next turn
    occupied = set()

    # Add all snakes' bodies (including tails - they stay if snake eats)
    for snake in game_state['board']['snakes']:
        if snake['id'] == game_state['you']['id']:
            new_body = simulate_snake_move(game_state["you"]["body"], direction)
            # Add our body but NOT the head position (since we're checking space FROM there)
            for i, segment in enumerate(new_body):
                if i > 0:  # Skip head (index 0)
                    occupied.add((segment['x'], segment['y']))
        else:
            # Include enemy tails - they might eat and not move tail
            for segment in snake['body']:
                occupied.add((segment['x'], segment['y']))

    # Add hazards if they exist
    if 'hazards' in game_state['board']:
        for hazard in game_state['board']['hazards']:
            occupied.add((hazard['x'], hazard['y']))

    # Check immediate space availability
    immediate_space = flood_fill(next_pos, board_width, board_height, occupied)

    # If we're in a very tight space, flag it
    # Need space for at least our body length (won't shrink unless we starve)
    required_space = len(game_state["you"]["body"])
    if immediate_space < required_space:
        return (False, immediate_space, -500)

    # Look ahead at possible next moves
    valid_next_moves = get_valid_moves(next_pos, board_width, board_height, occupied)

    if len(valid_next_moves) == 0:
        return (False, 0, -1000)

    if depth == 1:
        return (True, immediate_space, 0)

    # Recursively check next moves
    min_space = immediate_space
    worst_trap_score = 0

    # Get the body state after making the move 'direction'
    new_body_after_move = simulate_snake_move(game_state["you"]["body"], direction)

    for next_dir in valid_next_moves:
        # Create a simulated game state for the NEXT move
        # The body is already updated from moving in 'direction'
        sim_game_state = {
            "you": {
                "id": game_state["you"]["id"],
                "body": new_body_after_move,
                "health": game_state["you"]["health"] - 1
            },
            "board": game_state["board"]
        }

        can_survive, space, trap_score = lookahead_survival(sim_game_state, next_dir, depth - 1)

        if not can_survive:
            return (False, space, trap_score - 200)

        min_space = min(min_space, space)
        worst_trap_score = min(worst_trap_score, trap_score)

    return (True, min_space, worst_trap_score)

def check_cutoff_opportunity(game_state: typing.Dict, direction: str) -> float:
    """
    Check if a move can cut off an opponent's escape routes
    Returns a score bonus for aggressive positioning
    """
    head = game_state["you"]["body"][0]
    my_length = len(game_state["you"]["body"])
    next_pos = get_next_position(head, direction)
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']

    cutoff_score = 0

    for snake in game_state['board']['snakes']:
        if snake['id'] == game_state['you']['id']:
            continue

        opponent_head = snake['body'][0]
        opponent_length = len(snake['body'])

        # Only try to cut off strictly weaker snakes (avoid equal length confrontations)
        if opponent_length >= my_length:
            continue

        # Check if we're near the opponent
        distance = manhattan_distance(next_pos, opponent_head)
        if distance > 4:
            continue

        # Simulate opponent's available space after our move
        occupied = get_occupied_spaces(game_state)
        occupied.add((next_pos['x'], next_pos['y']))

        opponent_space = flood_fill(opponent_head, board_width, board_height, occupied)

        # If opponent has limited space, we're cutting them off
        if opponent_space < opponent_length + 3:
            cutoff_score += 100  # Good cutoff positioning
            if opponent_space < opponent_length:
                cutoff_score += 200  # Deadly trap!

    return cutoff_score

def calculate_move_score(game_state: typing.Dict, direction: str, is_move_safe: typing.Dict) -> float:
    """Calculate a score for a potential move"""
    if not is_move_safe[direction]:
        return -1000000  # Deadly move

    head = game_state["you"]["body"][0]
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']
    my_health = game_state['you']['health']
    my_length = len(game_state['you']['body'])

    next_pos = get_next_position(head, direction)

    score = 0

    # LOOKAHEAD: Check if this move leads to a trap
    can_survive, min_future_space, trap_score = lookahead_survival(game_state, direction, depth=3)
    if not can_survive:
        return -900000  # This leads to a trap!

    score += trap_score  # Add trap penalty/bonus
    score += min_future_space * 5  # Reward moves that maintain space

    # Flood fill - favor moves with more space (exclude safe tails for optimistic view)
    occupied = get_occupied_spaces(game_state, exclude_tail_if_safe=True)
    space_available = flood_fill(next_pos, board_width, board_height, occupied)
    score += space_available * 10

    # AGGRESSIVE: Check for cutoff opportunities
    cutoff_bonus = check_cutoff_opportunity(game_state, direction)
    score += cutoff_bonus

    # Prefer center of board (more options)
    center_x, center_y = board_width // 2, board_height // 2
    distance_to_center = abs(next_pos['x'] - center_x) + abs(next_pos['y'] - center_y)
    score -= distance_to_center * 2

    # Food seeking when hungry
    if my_health < 70 and game_state['board']['food']:
        nearest_food = min(game_state['board']['food'],
                          key=lambda f: manhattan_distance(next_pos, f))
        food_distance = manhattan_distance(next_pos, nearest_food)
        score -= food_distance * 15

        # Very hungry - prioritize food even more
        if my_health < 30:
            score -= food_distance * 30

    # Chase our own tail when safe (creates space)
    my_tail = game_state["you"]["body"][-1]
    tail_distance = manhattan_distance(next_pos, my_tail)
    if my_health > 50 and tail_distance < 3:
        score += 20

    # Aggressive opponent handling
    for snake in game_state['board']['snakes']:
        if snake['id'] == game_state['you']['id']:
            continue

        opponent_head = snake['body'][0]
        opponent_length = len(snake['body'])
        distance_to_opponent = manhattan_distance(next_pos, opponent_head)

        # Avoid equal or longer snakes (head-to-head collision kills both equal snakes)
        if opponent_length >= my_length and distance_to_opponent <= 2:
            score -= 150  # Avoid equal or stronger snakes
        # Be aggressive only when we're strictly longer
        elif opponent_length < my_length and distance_to_opponent <= 3:
            score += 130  # Hunt weaker snakes aggressively

    # Avoid edges slightly
    if next_pos['x'] == 0 or next_pos['x'] == board_width - 1:
        score -= 5
    if next_pos['y'] == 0 or next_pos['y'] == board_height - 1:
        score -= 5

    return score

def move(game_state: typing.Dict) -> typing.Dict:

    is_move_safe = {
      "up": True,
      "down": True,
      "left": True,
      "right": True
    }

    # Track risky moves separately (potential head-to-head with equal/longer snakes)
    is_move_risky = {
      "up": False,
      "down": False,
      "left": False,
      "right": False
    }

    head = game_state["you"]["body"][0]
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']
    my_length = len(game_state['you']['body'])

    #Prevent Snake from running into itself
    if my_length > 1:
        neck = game_state["you"]["body"][1]
        if neck["x"] < head["x"]:  #Neck is left of head, don't move left
            is_move_safe["left"] = False
        elif neck["x"] > head["x"]:  #Neck is right of head, don't move right
            is_move_safe["right"] = False
        elif neck["y"] < head["y"]:  #Neck is below head, don't move down
            is_move_safe["down"] = False
        elif neck["y"] > head["y"]:  #Neck is above head, don't move up
            is_move_safe["up"] = False

    #Prevent snake from moving out of bounds
    if head["x"] == 0:
      is_move_safe["left"] = False #Head too close to left wall
    if head["y"] == 0:
      is_move_safe["down"] = False #Head too close to bottom wall
    if head["x"] == board_width - 1:
      is_move_safe["right"] = False #Head too close to right wall
    if head["y"] == board_height - 1:
      is_move_safe["up"] = False #Head too close to top wall

    #Prevent snake from colliding with other snake bodies
    for snake in game_state['board']['snakes']:
        # Check all body segments including tail (snake might eat and tail won't move)
        for i, segment in enumerate(snake["body"]):
          # Can move to tail position only if it's the last segment and no food there
          is_tail = (i == len(snake["body"]) - 1)
          has_food_on_tail = is_tail and any(f["x"] == segment["x"] and f["y"] == segment["y"] for f in game_state['board']['food'])

          if (segment["x"] == head["x"] + 1) and (segment["y"] == head["y"]):
              # Unsafe if: not a tail, OR is a tail with food on it
              if not is_tail or has_food_on_tail:
                  is_move_safe["right"] = False
          if (segment["x"] == head["x"] - 1) and (segment["y"] == head["y"]):
              if not is_tail or has_food_on_tail:
                  is_move_safe["left"] = False
          if (segment["x"] == head["x"]) and (segment["y"] == head["y"] + 1):
              if not is_tail or has_food_on_tail:
                  is_move_safe["up"] = False
          if (segment["x"] == head["x"]) and (segment["y"] == head["y"] - 1):
              if not is_tail or has_food_on_tail:
                  is_move_safe["down"] = False

    #Avoid hazards if they exist
    if 'hazards' in game_state['board']:
        for hazard in game_state['board']['hazards']:
            if (hazard["x"] == head["x"] + 1) and (hazard["y"] == head["y"]):
                is_move_safe["right"] = False
            if (hazard["x"] == head["x"] - 1) and (hazard["y"] == head["y"]):
                is_move_safe["left"] = False
            if (hazard["x"] == head["x"]) and (hazard["y"] == head["y"] + 1):
                is_move_safe["up"] = False
            if (hazard["x"] == head["x"]) and (hazard["y"] == head["y"] - 1):
                is_move_safe["down"] = False

    #Advanced head-to-head collision avoidance
    for snake in game_state['board']['snakes']:
        if snake['id'] == game_state['you']['id']:
            continue

        opponent_head = snake['body'][0]
        opponent_length = len(snake['body'])

        #Check all possible opponent moves
        possible_opponent_moves = []

        # Right
        if opponent_head["x"] < board_width - 1:
            possible_opponent_moves.append({"x": opponent_head["x"] + 1, "y": opponent_head["y"]})
        # Left
        if opponent_head["x"] > 0:
            possible_opponent_moves.append({"x": opponent_head["x"] - 1, "y": opponent_head["y"]})
        # Up
        if opponent_head["y"] < board_height - 1:
            possible_opponent_moves.append({"x": opponent_head["x"], "y": opponent_head["y"] + 1})
        # Down
        if opponent_head["y"] > 0:
            possible_opponent_moves.append({"x": opponent_head["x"], "y": opponent_head["y"] - 1})

        for opp_move in possible_opponent_moves:
            # Mark head-to-head with equal or longer snakes as risky (not definitely unsafe)
            if opponent_length >= my_length:
                if opp_move["x"] == head["x"] + 1 and opp_move["y"] == head["y"]:
                    is_move_risky["right"] = True
                if opp_move["x"] == head["x"] - 1 and opp_move["y"] == head["y"]:
                    is_move_risky["left"] = True
                if opp_move["x"] == head["x"] and opp_move["y"] == head["y"] + 1:
                    is_move_risky["up"] = True
                if opp_move["x"] == head["x"] and opp_move["y"] == head["y"] - 1:
                    is_move_risky["down"] = True

    #Score each move
    move_scores = {}
    for direction in ["up", "down", "left", "right"]:
        move_scores[direction] = calculate_move_score(game_state, direction, is_move_safe)

    # Filter to definitely safe moves (not risky, not unsafe)
    safe_moves = {direction: score for direction, score in move_scores.items()
                  if is_move_safe[direction] and not is_move_risky[direction]}

    # Filter to risky but not definitely unsafe moves
    risky_moves = {direction: score for direction, score in move_scores.items()
                   if is_move_safe[direction] and is_move_risky[direction]}

    # Prefer safe moves, but take risky moves over dying
    if safe_moves:
        best_move = max(safe_moves, key=safe_moves.get)
        best_score = safe_moves[best_move]
        print(f"MOVE {game_state['turn']}: {best_move} (score: {best_score:.1f})")
    elif risky_moves:
        # No safe moves, but we have risky options - take the best one
        best_move = max(risky_moves, key=risky_moves.get)
        best_score = risky_moves[best_move]
        print(f"MOVE {game_state['turn']}: RISKY {best_move} - no safe moves! (score: {best_score:.1f})")
    else:
        # No safe or risky moves - pick the least bad option (probably going to die)
        best_move = max(move_scores, key=move_scores.get)
        best_score = move_scores[best_move]
        print(f"MOVE {game_state['turn']}: DESPERATION {best_move}! (score: {best_score:.1f})")

    return {"move": best_move}
