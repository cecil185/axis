"""Flask HTTP server wrapping the game state modules."""

import os

from flask import Flask, jsonify, send_from_directory

import src.state as _state_mod
from .economy import reset_balances
from .serializer import serialize_state
from .territory import ALL_TERRITORY_IDS, is_neutral_start, set_neutral, set_owner
from .units import init_game

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))


@app.get("/state")
def get_state():
    return jsonify(serialize_state())


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.post("/action/reset")
def reset():
    init_game()
    reset_balances()
    _state_mod._current_team = "Red"
    _state_mod._turn = 1
    for i, tid in enumerate(ALL_TERRITORY_IDS):
        if is_neutral_start(tid):
            set_neutral(tid)
        else:
            set_owner(tid, "Red" if i < 15 else "Blue")
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=5000)
