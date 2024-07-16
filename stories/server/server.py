from flask import Flask, request, jsonify

import game.logger

from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "Hello, World!"

@app.route("/create-story/", methods=['POST'])
def create_story():
    return {"name": str(request.data)}
