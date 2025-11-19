import logging
import os
import typing
from flask import Flask, request, jsonify

app = Flask("Battlesnake")

def run_server(handlers: typing.Dict):
    @app.get("/")
    def on_info():
        try:
            return jsonify(handlers["info"]())
        except Exception as e:
            logging.error(f"Error in /info: {e}")
            return jsonify({"error": "Server Error"}), 500

    @app.post("/start")
    def on_start():
        try:
            game_state = request.get_json()
            handlers["start"](game_state)
            return jsonify({"status": "ok"})
        except Exception as e:
            logging.error(f"Error in /start: {e}")
            return jsonify({"error": "Server Error"}), 500

    @app.post("/move")
    def on_move():
        try:
            game_state = request.get_json()
            return jsonify(handlers["move"](game_state))
        except Exception as e:
            logging.error(f"Error in /move: {e}")
            return jsonify({"error": "Server Error"}), 500

    @app.post("/end")
    def on_end():
        try:
            game_state = request.get_json()
            handlers["end"](game_state)
            return jsonify({"status": "ok"})
        except Exception as e:
            logging.error(f"Error in /end: {e}")
            return jsonify({"error": "Server Error"}), 500

    @app.after_request
    def identify_server(response):
        response.headers.set("server", "battlesnake/azure/app-service-python")
        return response

    return app

# Import game logic
from main import info, start, move, end

# Create the Flask app instance for Gunicorn
app = run_server({
    "info": info,
    "start": start,
    "move": move,
    "end": end,
})

# For local development
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
