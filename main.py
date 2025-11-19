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


# Flood fill algorithm to compute the size of open space from a point

def flood_fill(start, blocked, width, height):
    """Compute the size of the area reachable from start avoiding blocked cells."""
    visited = set()
    queue = deque([start])
    visited.add(start)
    while queue:
        x, y = queue.popleft()
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in blocked and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append((nx, ny))
    return len(visited)


def move(game_state: typing.Dict) -> typing.Dict:
    """Choose a move based on avoiding collisions and maximizing open space, prioritizing food."""
    import math
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']
    head = game_state['you']['body'][0]

    # Build a set of blocked positions (snake bodies)
    blocked = set()
    for snake in game_state['board']['snakes']:
        for segment in snake['body']:
            blocked.add((segment['x'], segment['y']))

    directions = {
        'up': (0, 1),
        'down': (0, -1),
        'left': (-1, 0),
        'right': (1, 0)
    }

    safe_options = []
    for direction, (dx, dy) in directions.items():
        new_x = head['x'] + dx
        new_y = head['y'] + dy
        # Check board boundaries
        if new_x < 0 or new_x >= board_width or new_y < 0 or new_y >= board_height:
            continue
        # Check collisions
        if (new_x, new_y) in blocked:
            continue
        area = flood_fill((new_x, new_y), blocked, board_width, board_height)
        # Distance to nearest food
        min_food_distance = math.inf
        for food in game_state['board']['food']:
            dist = abs(food['x'] - new_x) + abs(food['y'] - new_y)
            if dist < min_food_distance:
                min_food_distance = dist
        safe_options.append((direction, area, min_food_distance))

    if not safe_options:
        return {'move': 'up'}

    safe_options.sort(key=lambda x: (-x[1], x[2]))
    best_direction = safe_options[0][0]
    return {'move': best_direction}


if __name__ == "__main__":
    from server import run_server
    run_server({
        "info": info,
        "start": start,
        "move": move,
        "end": end,
    })
