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

from server.gameManager import StoriesGameManager, Game, GameInfo, CardInfo, PlayerInfo, GameID
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

@app.post("/add/", status_code=200)
def add_player(playerInfo:PlayerInfo)->PlayerInfo:
    """Adds an existing player to a given game
    """
    return gameManager.add_player_to_game(playerInfo)

@app.post('/create/', status_code=201)
def createGame(gameInfo:GameInfo, response: Response)->Game:
    """Create a new StoriesGame and returns the server Game instance
    """
    theGame = gameManager.create_game(gameInfo)
    if theGame.errorNumber != 0:
        response.status_code = status.HTTP_404_NOT_FOUND
        response.body = theGame.errorText
    return theGame

@app.get("/game/{gameId}", status_code=200)
def getGame(gameId:str, response:Response):
    game = gameManager.get_game(gameId)
    if game is None:
        response.status_code = status.HTTP_404_NOT_FOUND
    return game

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

@app.post('/play/', status_code=201)
def play_card(card_info:CardInfo):
    result = gameManager.play_card(card_info.game_id, card_info.card_number, card_info.action_args)
    return result

@app.get('/draw/{gameId}/{initials}', status_code=200)
def draw_card(gameId, initials:str,  response:Response):
    card = gameManager.draw_card(gameId, initials)
    return card

@app.get("/read/{gameId}/{initials}", status_code=200)
def read_story(gameId, initials:str,  response:Response):
    thestory = gameManager.read_story(gameId, initials)
    return thestory

@app.put("/next/", status_code=201)
def nextPlayer(gameID:GameID):
    return gameManager.next_player(gameID)

@app.post("/end/", status_code=201)
def endGame(gameID:GameID):
    return gameManager.end_game(gameID)

@app.get("/help/{game_id}")
def get_general_help(game_id):
    return gameManager.get_help(game_id)

@app.get("/help/{game_id}/{card_or_command}")
def get_help(game_id, card_or_command:str):
    return gameManager.get_help(game_id, card_or_command)

@app.get("/help/{game_id}/{card_or_command}/{action_type}")
def get_action_help(game_id, card_or_command:str, action_type:str):
    return gameManager.get_help(game_id, card_or_command, action_type)



