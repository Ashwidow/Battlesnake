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
    queue = deque([tuple(start_pos.values())])
    visited.add(tuple(start_pos.values()))

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

def get_occupied_spaces(game_state: typing.Dict) -> set:
    """Get all occupied spaces on the board"""
    occupied = set()

    for snake in game_state['board']['snakes']:
        for segment in snake['body'][:-1]:  # Exclude tail as it will move
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
    occupied = get_occupied_spaces(game_state)

    score = 0

    # Flood fill - favor moves with more space
    space_available = flood_fill(next_pos, board_width, board_height, occupied)
    score += space_available * 10

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

        # Only avoid if opponent is STRICTLY longer
        if opponent_length > my_length and distance_to_opponent <= 2:
            score -= 150  # Avoid strictly stronger snakes
        # Be aggressive when we're longer or equal
        elif opponent_length <= my_length and distance_to_opponent <= 3:
            score += 80  # Hunt equal or weaker snakes aggressively
            # Extra aggressive when we're longer
            if opponent_length < my_length:
                score += 50

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

    head = game_state["you"]["body"][0]
    neck = game_state["you"]["body"][1]
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']
    my_length = len(game_state['you']['body'])

    #Prevent Snake from running into itself
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
        for segment in snake["body"][:-1]:  # Exclude tail
          if (segment["x"] == head["x"] + 1) and (segment["y"] == head["y"]):
              is_move_safe["right"] = False
          if (segment["x"] == head["x"] - 1) and (segment["y"] == head["y"]):
              is_move_safe["left"] = False
          if (segment["x"] == head["x"]) and (segment["y"] == head["y"] + 1):
              is_move_safe["up"] = False
          if (segment["x"] == head["x"]) and (segment["y"] == head["y"] - 1):
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
            # Only avoid if opponent is STRICTLY longer (we win ties and longer matchups)
            if opponent_length > my_length:
                if opp_move["x"] == head["x"] + 1 and opp_move["y"] == head["y"]:
                    is_move_safe["right"] = False
                if opp_move["x"] == head["x"] - 1 and opp_move["y"] == head["y"]:
                    is_move_safe["left"] = False
                if opp_move["x"] == head["x"] and opp_move["y"] == head["y"] + 1:
                    is_move_safe["up"] = False
                if opp_move["x"] == head["x"] and opp_move["y"] == head["y"] - 1:
                    is_move_safe["down"] = False

    #Score each safe move
    move_scores = {}
    for direction in ["up", "down", "left", "right"]:
        move_scores[direction] = calculate_move_score(game_state, direction, is_move_safe)

    # Find the best move
    best_move = max(move_scores, key=move_scores.get)
    best_score = move_scores[best_move]

    # If best move is deadly, pick any safe move
    if best_score < -100000:
        safe_moves = [m for m, safe in is_move_safe.items() if safe]
        if safe_moves:
            best_move = random.choice(safe_moves)
            print(f"MOVE {game_state['turn']}: Emergency move {best_move}")
        else:
            # No safe moves - try to survive
            best_move = "up"
            print(f"MOVE {game_state['turn']}: No safe moves! Attempting {best_move}")
    else:
        print(f"MOVE {game_state['turn']}: {best_move} (score: {best_score:.1f})")

    return {"move": best_move}


#Begin Server Pull
if __name__ == "__main__":
    from server import run_server

    run_server({
        "info": info,
        "start": start,
         "move": move,
        "end": end
    })
