"""
Created on Aug 12, 2024

@author: don_bacon

"""
import uvicorn
from fastapi import FastAPI, Depends, status, Form
from datetime import date, datetime
from fastapi.responses import JSONResponse

from game.storiesGameEngine import StoriesGameEngine

from server.gameManager import StoriesGameManager, Game
from server.playerManager import StoriesPlayer, StoriesPlayerManager

manager = StoriesGameManager()
playerManager = StoriesPlayerManager()
app = FastAPI()

@app.put('/game/{userId}', status_code=201)
def createGame(userId:str):
    """Create a new StoriesGame and returns the Id
    """
    return manager.create(userId)

@app.get("/", status_code=200)
def get(game: StoriesGameEngine=Depends(manager)):
    return {}


