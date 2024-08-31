'''
Created on Aug 28, 2024

@author: don_bacon
'''

import json
import pymongo
import argparse
from typing import List
from game.commandResult import CommandResult
from game.gameConstants import GenreType

class Install(object):
    '''
    Install MongoDB databases and collections, creating indicies as needed
    '''


    def __init__(self, genre:str, db_names:List[str], mode:str):
        '''
        Constructor
        '''
        self.active = True
        result = self.mongo_init()
        if not result.is_successful():
            self.active = False
            print(result.message)
        self.genre = GenreType[genre.upper()]
        self.mode = mode
        self.db_names = db_names

    def mongo_init(self)->CommandResult:
        """Initializes MongoDB client info using the .env project file
        """
        env_file = f'{self._env.package_base}/.env'
        params = {}
        with open(env_file, "r") as efp:
            for line in efp:
                if len(line)>0:
                    tokens = line.split("=")
                    params[tokens[0]] = tokens[1].rstrip()
        efp.close()
        self._db_url = params["DB_URL"]
        self._db_name = params["DB_NAME"]
        self._db_name_genres = params["DB_NAME_GENRES"]
        
        try:
            mongo_client = pymongo.MongoClient(self._db_url)
            self._stories_db = mongo_client[self._db_name]
            self._genres_db = mongo_client[self._db_name_genres]
            self._mongo_client = mongo_client
            result = CommandResult(CommandResult.SUCCESS)
        except Exception as ex:
            message = f'MongoDB error, exception: {str(ex)}'
            result = CommandResult(CommandResult.ERROR,  message,  False, exception=ex)
        
        return result
    
    def install(self)->CommandResult:
        result = CommandResult()
        # TODO
        return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Install and populate MongoDB tables")
    genres = ["horror","romance","noir"]
    parser.add_argument("--genre", help="Story genre", type=str, choices=genres, default="horror")
    database_names = ["stories", "genres"]
    db_choices = ["all", "stories", "genres"]
    parser.add_argument("--db", help="Database name or 'all'", type=str, choices=db_choices)    # there is no default
    #
    # update - update existing collection(s)
    # replace - replace existing collections with new ones
    # new - remove existing stories and genres databases and add all new tables
    #
    parser.add_argument("--mode", help="Update existing, Replace all, New", type=str, choices=["new","update","replace"], default="new")
    
    args = parser.parse_args()
    dbnames = database_names if args.db == "all" else [args.db]
    installer = Install(args.genre, dbnames, args.mode)
    if installer.active:
        result = installer.install()
    else:
        print("there was an error")
    
    
    