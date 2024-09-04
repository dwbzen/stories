'''
Created on Sep 2, 2024

@author: don_bacon
'''

from fastapi.encoders import jsonable_encoder
from typing import Any, List
import json, dotenv
from uuid import uuid4
from pydantic import Field, BaseModel
from pymongo import MongoClient
from datetime import datetime

class PlayerGameHistory(BaseModel):
    #
    # the history if games played by a given player
    #
    player_id:str = Field(default=None)    # reference to StoriesPlayer.id
    game_id:str = Field(alias="gameId", default=None)    # reference to GameInfo
    # current role for this game. Role depends on the Game playMode
    # PlayerRole: player, team_lead, director, team_member, unassigned
    player_role:str = Field(default="unassigned")
    number: int = Field(default=0)    # the assigned player number (ordinal 0 - #players-1) for this game
    createdDate: datetime = Field(default=datetime.now())

class HistoryManager(object):
    """
        TODO
    """

    def __init__(self):
        """Just a stub for now
        """
        self.config = dotenv.dotenv_values(".env")
        self.mongo_client = MongoClient(self.config["DB_URL"])
        self.db_name = self.config["DB_NAME_HISTORY"]
        self.database = self.mongo_client[self.db_name]
        
    def get_player_game_history(self, player_id:str, game_id:str)->PlayerGameHistory:
        pass
    
        