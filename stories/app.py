"""
Created on Aug 12, 2024

@author: don_bacon

"""
import uvicorn
from fastapi import FastAPI, Depends, status, Form
from datetime import date, datetime
from fastapi.responses import JSONResponse, Response

from game.storiesGameEngine import StoriesGameEngine
from game.storiesGame import StoriesGame

from server.gameManager import StoriesGameManager, Game
from server.playerManager import StoriesPlayer, StoriesPlayerManager

manager = StoriesGameManager()
playerManager = StoriesPlayerManager()
app = FastAPI()

@app.get("/")
def hello_world():
    return "Hello, World!"

@app.get("/info/{initials}", status_code=200)
def info(initials:str, response: Response):
    playerinfo = playerManager.getUserByInitials(initials)
    if playerinfo is None:
        response.status_code = status.HTTP_404_NOT_FOUND
    return playerinfo

@app.post("/player/",  status_code=201)
def create_player(player:StoriesPlayer):
    print(player)
    return playerManager.create_player(player)

@app.put('/game/{userId}', status_code=201)
def createGame(userId:str):
    """Create a new StoriesGame and returns the Id
    """
    return manager.create(userId)

#@app.get("/game/{gameId}", status_code=200)
#def get(game:StoriesGame=Depends(manager)):
#    return {}


