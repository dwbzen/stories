'''
Created on Aug 12, 2024

@author: don_bacon
'''

from fastapi.encoders import jsonable_encoder
import pymongo
from typing import Dict, List
import json
import dotenv
import string
from uuid import uuid4
from pydantic import Field, BaseModel
from pymongo import MongoClient
from datetime import datetime

from server.playerManager import StoriesPlayer, StoriesPlayerManager

from game.storiesGameEngine import StoriesGameEngine
from game.storiesGame import StoriesGame
from game.player import Player
from game.commandResult import CommandResult
from game.gameConstants import PlayerRole

class Game(BaseModel):
    """Persisted stories Games
    """
    id: str = Field(default=None)
    game_id:str = Field(default=None)
    genre:str = Field(...)    # GenreType - horror, noir, romance
    gameParametersType:str = Field(...)    # test, prod, or custom
    playMode:str = Field(...)     # collaborative, team, or individual
    installation_id:str = Field(...)
    createdBy: str = Field(default=None)
    createdDate: datetime = Field(default=datetime.now())
    startDate: datetime = Field(default=None)
    endDate: datetime = Field(default=None)
    errorNumber:int = Field(default=0)    # not persisted, obviously
    errorText:str = Field(default="")     # not persisted

class GameInfo(BaseModel):
    """The query/request view of a given Game
    """
    installation_id:str  = Field(...)
    game_id:str = Field(default="None")    # assigned when the StoriesGame is created
    genre:str = Field(...)    # GenreType - horror, noir, romance
    gameParametersType:str = Field(...)    # test, prod, or custom
    playMode:str = Field(...)     # collaborative, team, or individual
    # the initials of an individual player (individual play), or
    # the team lead (team play), or
    # the player initiating a collaborative game
    playerId:str = Field(default=None)
    # True if this game is currently active - i.e. being played, False otherwise
    # set to True when a 'start' command is issued
    active:bool = Field(default=False)
    players: List[str] = Field(default=[])
    
class StoriesGameManager(object):
    
    def __init__(self):
        """
            Constructor
        """
        self.games:Dict[str,StoriesGameEngine] = {}    # StoriesGameEngine has a StoriesGame reference
        self.config = dotenv.dotenv_values(".env")
        self.db_url = self.config["DB_URL"]
        self.db_name = self.config["DB_NAME"]    # stories DB
        result,message = self.db_init()
        if result:
            self.games_collection = self.stories_db["games"]
        else:
            print(message)
        
        self.stories_game = None
        self.playerManager = StoriesPlayerManager()

    def db_init(self)->(bool,str):
        message = None
        result = True
        try:
            mongo_client = pymongo.MongoClient(self.db_url)
            self.stories_db = mongo_client[self.db_name]
            self.mongo_client = mongo_client
        except Exception as ex:
            message = f'MongoDB error, exception: {str(ex)}'
            result = False
            
        return result,message
        
    def create_game(self, gameInfo:GameInfo)->Game:
        #
        print(f"gameInfo: {gameInfo}")
        storiesPlayer:StoriesPlayer = self.playerManager.getUserByInitials(gameInfo.playerId)
        if storiesPlayer is None:
            return Game(errorNumber=1, errorText="No such user")
        
        gameInfo.players = [storiesPlayer.initials]
        game_engine = StoriesGameEngine(installationId=gameInfo.installation_id)
        theGame = Game(installation_id=gameInfo.installation_id, genre=gameInfo.genre, \
                       gameParametersType=gameInfo.gameParametersType, playMode=gameInfo.playMode)
        theGame.id = uuid4()
        theGame.createdBy = storiesPlayer.initials
        #
        # create the StoriesGame and if successful, persist Game to the DB
        #
        result = game_engine.create(gameInfo.installation_id, gameInfo.genre, 0, gameInfo.playMode, 'mongo', gameInfo.gameParametersType)
        if result.return_code != CommandResult.SUCCESS:
            theGame.errorNumber = 2
            theGame.errorText = "Could not create a StoriesGame"
        else:
            stories_game = game_engine.stories_game
            game_id = stories_game.game_id
            theGame.game_id = game_id
            
            #
            # add the initiating player to the game and assign the role of Director
            # and start the game
            #
            self.games[game_id] = game_engine
            self.add_player(storiesPlayer, game_id, player_role=PlayerRole.DIRECTOR)
            result = game_engine.start(what="game")
            if result.is_successful():
                theGame.startDate = datetime.now()
                self.games_collection.insert_one(jsonable_encoder(theGame))
        return theGame
    
    def add_player(self, storiesPlayer:StoriesPlayer, gameId:str, player_role:PlayerRole=PlayerRole.PLAYER)->CommandResult:
        """Adds a player to the game with a given game_id
        """
        game_engine = self.games[gameId]
        command = f"add player {storiesPlayer.name} {storiesPlayer.initials} {storiesPlayer.login_id} {storiesPlayer.email}"
        result = game_engine.execute_command(command, aplayer=None)
        if result.is_successful():
            if player_role is PlayerRole.DIRECTOR:
                command = f"add director {storiesPlayer.name} {storiesPlayer.initials}"
                result = game_engine.execute_command(command, aplayer=None)
        return result
    
    def get_game_status(self, game_id):
        status = None
        if game_id in self.games:
            game_engine:StoriesGameEngine = self.games[game_id]
            result = game_engine.game_status()
            if result.is_successful():
                status = result.message
        return status
    
    def list_cards(self, game_id:str, initials:str):
        cards = None
        if game_id in self.games:
            game_engine:StoriesGameEngine = self.games[game_id]
            result = game_engine.lnj(what='hand', initials=initials,  how='numbered')
            cards = result.message
        return cards
    
    def get_game(self, id:str)->GameInfo:
        """TODO
        """
        return None
        
