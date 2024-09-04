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

from server.gameManager import StoriesGameManager, Game, GameInfo
from server.playerManager import StoriesPlayer, StoriesPlayerManager

gameManager = StoriesGameManager()
playerManager = StoriesPlayerManager()
app = FastAPI()

@app.get("/")
def hello_world():
    return "Hello, World!"

@app.get("/info/{initials}", status_code=200)
def info(initials:str, response: Response)->StoriesPlayer:
    playerinfo = playerManager.getUserByInitials(initials)
    if playerinfo is None:
        response.status_code = status.HTTP_404_NOT_FOUND
    return playerinfo

@app.post("/player/",  status_code=201)
def create_player(player:StoriesPlayer)->StoriesPlayer:
    print(player)
    return playerManager.create_player(player)

@app.post('/game/', status_code=201)
def createGame(gameInfo:GameInfo, response: Response)->Game:
    """Create a new StoriesGame and returns the server Game instance
    """
    theGame = gameManager.create_game(gameInfo)
    if theGame.errorNumber != 0:
        response.status_code = status.HTTP_404_NOT_FOUND
        response.body = theGame.errorText
    return theGame

@app.get("/status/{gameId}", status_code=200)
def getGameStatus(gameId:str, response:Response):
    game_status = gameManager.get_game_status(gameId)
    print(f"game_status: {game_status}")
    if game_status is None:
        response.status_code = status.HTTP_404_NOT_FOUND
    return game_status

@app.get("/list/{gameId}/{initials}", status_code=200)
def list_cards(gameId, initials:str,  response:Response):
    cards = gameManager.list_cards(gameId, initials)
    if cards is None:
        response.status_code = status.HTTP_404_NOT_FOUND
    return cards


@app.get("/game/{gameId}", status_code=200)
def get(gameId:str):
    return "{TODO}"

