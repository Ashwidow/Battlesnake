import random
import typing

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

def move(game_state: typing.Dict) -> typing.Dict:

    is_move_safe = {
      "up": True, 
      "down": True, 
      "left": True, 
      "right": True
    }

    head = game_state["you"]["body"][0]
    neck = game_state["you"]["body"][1]

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
    board_width = game_state['board']['width']
    board_height = game_state['board']['height']

    if head["x"] == 0:
      is_move_safe["left"] = False #Head too close to left wall
    if head["y"] == 0:
      is_move_safe["down"] = False #Head too close to bottom wall
    if head["x"] == board_width - 1:
      is_move_safe["right"] = False #Head too close to right wall
    if head["y"] == board_height - 1:
      is_move_safe["up"] = False #Head too close to top wall

    #Prevent snake from colliding with anything
    for everything in game_state['board']['snakes']:
        avoidarea = everything["body"]
        for avoid in avoidarea:
          if (avoid["x"] == head["x"] + 1) and (avoid["y"] == head["y"]):
              is_move_safe["right"] = False 
          if (avoid["x"] == head["x"] - 1) and (avoid["y"] == head["y"]):
              is_move_safe["left"] = False   
          if (avoid["x"] == head["x"]) and (avoid["y"] == head["y"] + 1):
              is_move_safe["up"] = False  
          if (avoid["x"] == head["x"]) and (avoid["y"] == head["y"] - 1):
              is_move_safe["down"] = False

    #Avoid head-to-head collisions
    for snake in game_state['board']['snakes']:
        if snake['id'] == game_state['you']['id']:
            continue

        opponent_head = snake['body'][0]
        opponent_length = len(snake['body'])
        my_length = len(game_state['you']['body'])

        #Predict where opponent heads might move
        possible_moves = [
            {"x": opponent_head["x"] + 1, "y": opponent_head["y"]},
            {"x": opponent_head["x"] - 1, "y": opponent_head["y"]},
            {"x": opponent_head["x"], "y": opponent_head["y"] + 1},
            {"x": opponent_head["x"], "y": opponent_head["y"] - 1}
        ]

        for move in possible_moves:
            if move["x"] == head["x"] + 1 and move["y"] == head["y"] and opponent_length >= my_length:
                is_move_safe["right"] = False
            if move["x"] == head["x"] - 1 and move["y"] == head["y"] and opponent_length >= my_length:
                is_move_safe["left"] = False
            if move["x"] == head["x"] and move["y"] == head["y"] + 1 and opponent_length >= my_length:
                is_move_safe["up"] = False
            if move["x"] == head["x"] and move["y"] == head["y"] - 1 and opponent_length >= my_length:
                is_move_safe["down"] = False

    #Chase weaker opponents
    my_length = len(game_state['you']['body'])
    weakest_snake = None
    min_distance_to_snake = float('inf')

    for snake in game_state['board']['snakes']:
        if snake['id'] == game_state['you']['id']:
            continue

        if len(snake['body']) < my_length:
            opponent_head = snake['body'][0]
            distance = abs(head['x'] - opponent_head['x']) + abs(head['y'] - opponent_head['y'])

            if distance < min_distance_to_snake:
                min_distance_to_snake = distance
                weakest_snake = opponent_head

    #Find the nearest food
    food = game_state['board']['food']
    nearest_food = None
    min_distance_to_food = float('inf')

    for f in food:
        distance = abs(head['x'] - f['x']) + abs(head['y'] - f['y'])
        if distance < min_distance_to_food:
            min_distance_to_food = distance
            nearest_food = f

    #Decide between chasing food or weaker snake
    target = None
    if game_state['you']['health'] < 50 or (nearest_food and min_distance_to_food < min_distance_to_snake):
        target = nearest_food
    elif weakest_snake:
        target = weakest_snake

    if target:
        if target['x'] < head['x'] and is_move_safe['left']:
            return {"move": "left"}
        if target['x'] > head['x'] and is_move_safe['right']:
            return {"move": "right"}
        if target['y'] < head['y'] and is_move_safe['down']:
            return {"move": "down"}
        if target['y'] > head['y'] and is_move_safe['up']:
            return {"move": "up"}

    #Are there any safe moves left?
    safe_moves = []
    for move, isSafe in is_move_safe.items():
        if isSafe:
            safe_moves.append(move)

    if len(safe_moves) == 0:
        print(f"MOVE {game_state['turn']}: No safe moves detected! Moving down")
        return {"move": "down"}

    #Choose a random move from the safe ones
    next_move = random.choice(safe_moves)

    print(f"MOVE {game_state['turn']}: {next_move}")
    return {"move": next_move}


#Begin Server Pull
if __name__ == "__main__":
    from Battlesnake.server import run_server

    run_server({
        "info": info, 
        "start": start, 
         "move": move, 
        "end": end
    })
