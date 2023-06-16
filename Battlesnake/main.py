
import random
import typing

def info() -> typing.Dict:
    print("FIGHT")

    return {
        "apiversion": "1",
        "author": "TheMuffinSnake",
        "color": "#0061ff",
        "head": "evil",
        "tail": "round-bum",
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

    #Prevent your snake from colliding with anything
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
            
    #Are there any safe moves left?
    safe_moves = []
    for move, isSafe in is_move_safe.items():
        if isSafe:
            safe_moves.append(move)

    if len(safe_moves) == 0:
        print(f"MOVE {game_state['turn']}: No safe moves detected! Moving down")
        return {"move": "down"}

    #Choose a random move from the safe one from logic above
    next_move = random.choice(safe_moves)

    # food = game_state['board']['food']

    print(f"MOVE {game_state['turn']}: {next_move}")
    return {"move": next_move}


# Begin Server Pull
if __name__ == "__main__":
    from Battlesnake.server import run_server

    run_server({
        "info": info, 
        "start": start, 
         "move": move, 
        "end": end
    })
