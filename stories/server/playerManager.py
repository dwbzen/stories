'''
Created on Aug 12, 2024

@author: don_bacon
'''

from fastapi.encoders import jsonable_encoder
from datetime import datetime
from uuid import uuid4
from typing import List

import dotenv
import pymongo
from pydantic import BaseModel, Field

class StoriesPlayer(BaseModel):
    """Profile information for Stories players.
    """
    id: str = Field(default=None)
    name: str = Field(...)
    initials: str = Field(...)
    email: str = Field(...)
    login_id:str = Field(default=None)
    phone:str = Field(...)
    play_level:str = Field(default="free")
    permission_level:str = Field(default="user")    # "user", "admin", "super_user"
    active:bool = Field(default=True)
    genres:List[str] = Field(default=[])    # the genres this player can access
    createdDate: datetime = Field(default=datetime.now())

class StoriesPlayerManager(object):
    
    def __init__(self):
        """
            Constructor
        """
        self.config = dotenv.dotenv_values(".env")
        self.db_url = self.config["DB_URL"]
        self.db_name = self.config["DB_NAME"]
        result,message = self.db_init()
        if result:
            self.collection = self.stories_db["players"]
        else:
            print(message)
    
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
       
    def create_player(self, player:StoriesPlayer)->StoriesPlayer:
        player.id = uuid4()
        self.collection.insert_one(jsonable_encoder(player))
        return player
       
    def getUserByUserId(self, playerId: str) -> StoriesPlayer:
        return self.collection.find_one({"_id": playerId})
    
    def getUserByInitials(self, initials:str)->StoriesPlayer:
        info = self.collection.find_one({"initials": initials})    # returns the MongoDB players record as a Dict
        if info is not None:
            player = StoriesPlayer(**info)
        else:    # try upper case
            info = self.collection.find_one({"initials": initials.upper()})
            if info is not None:
                info["initials"] = initials.upper()
                player = StoriesPlayer(**info)
            else:
                player = None
        return player
    
    def deleteUser(self, playerId: str):
        self.collection.delete_one({"_id": playerId})
    
    def updateUser(self, player:StoriesPlayer):
        self.collection.update_one({"_id": player['_id']}, {"$set": {'number': player["number"]}})

def main():
    # quick test
    playerManager = StoriesPlayerManager()
    storiesPlayer = playerManager.getUserByInitials("dwb")
    print(storiesPlayer)
    

if __name__ == '__main__':
    main()
