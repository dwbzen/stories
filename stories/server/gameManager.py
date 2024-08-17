'''
Created on Aug 12, 2024

@author: don_bacon
'''

from fastapi.encoders import jsonable_encoder
from typing import Any, List, Optional, Dict
import json
import dotenv
import random
import string
from pydantic import Field, BaseModel
from pymongo import MongoClient
from datetime import datetime

from server.playerManager import StoriesPlayer, StoriesPlayerManager
from game.storiesGameEngine import StoriesGameEngine
from game.storiesGame import StoriesGame
from game.gameState import GameState
from game.gameConstants import GameConstants
from game.player import Player
from game.gameParameters import GameParameters

class Game(BaseModel):
    '''
    classdocs
    '''

    def __init__(self):
        """
            Constructor
        """
        id: str = Field(alias="_id", default=None)
        gameId: str = Field(alias="game_id", default=None)
        installationId = Field(alias="installation_id", default=None)
        createdBy: str = Field(alias="installationId", default=None)
        createdDate: datetime = Field(...)
        gameState: Any = Field(default=None)    
        storyCardDeck: Any = Field(alias="story_card_deck", default=None)    # CardDeck
        players: Any = Field(default=None)
        updateDate: datetime = Field(...)
        startDate: datetime = Field(default=None)
    

class StoriesGameManager(object):
    
    def __init__(self):
        """
            Constructor
        """
        self.games = {}
        self.config = dotenv.dotenv_values(".env")
        self.openapi_api_key = self.config["OPENAI_API_KEY"]
        self.mongo_client = MongoClient(self.config["DB_URL"])
        self.db_name = self.config["DB_NAME"]
        self.database = self.mongo_client[self.db_name]
        self.database["games"].create_index('players')
        #
        self.playerManager = StoriesPlayerManager()

        
    def create(self, playerId:str):
        gameEngine = StoriesGameEngine(installationId="DWBZen20240814")
        
        
        
        
        