from flask import Flask, request, jsonify

import game.logger

from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/create-story/", methods=['POST'])
def create_story():
    return {"name": str(request.data)}
