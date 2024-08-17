'''
Created on Aug 12, 2024

@author: don_bacon
'''

from fastapi.encoders import jsonable_encoder
from typing import Any, List
from datetime import datetime
from uuid import uuid4

import dotenv
from pydantic import BaseModel, Field

class StoriesPlayer(BaseModel):
    name: str = Field(...)
    email: str = Field(...)
    initials: str = Field(...)
    phone:str = Field(...)
    id: str = Field(alias="_id", default=None)
    number: int = Field(default=0)
    createdDate: datetime = Field(default=datetime.now())

class StoriesPlayerManager(object):
    
    def __init__(self):
       """
           Constructor
       """
       self.config = dotenv.dotenv_values(".env")
       self.collection = self.database["players"]
       #
       # TODO determine the DB to use - Mongo or ?
       #
       
    def create_player(self, player:StoriesPlayer)->StoriesPlayer:
       player.id = uuid4()
       self.collection.insert_one(jsonable_encoder(player))      
       
    def getUserByUserId(self, playerId: str) -> StoriesPlayer:
        return self.collection.find_one({"_id": playerId})
    
    def deleteUser(self, playerId: str):
        self.collection.delete_one({"_id": playerId})
    
    def updateUser(self, player: StoriesPlayer):
        self.collection.update_one({"_id": player['_id']}, {"$set": {'number': player["number"]}})
