'''
Created on Jul 9, 2024

@author: don_bacon
'''
from openai import OpenAI
from game.gameConstants import GenreFilenames, GenreType, CardType
from game.commandResult import CommandResult
from typing import Dict, List


class ChatManager(object):
    '''
    classdocs
    '''


    def __init__(self, resource_folder:str, genre:GenreType, api_key:str=None):
        """
        """
        self._genre = genre
        self._api_key = api_key
        self._resource_folder = resource_folder
        self._system_text = None
        self._model="gpt-4o"
        self._card_types = [CardType.TITLE, CardType.OPENING, CardType.STORY, CardType.CLOSING]
        self._user_text:Dict[CardType,str] = {}    # Dict with the CardType as the key ('Title' for example)
        if api_key is None:
            self._client = OpenAI()
        else:
            self._client = OpenAI(api_key=api_key)
    
    @property
    def genre(self)->GenreType:
        return self._genre
    
    @property
    def api_key(self)->str:
        return self._api_key
    
    @api_key.setter
    def api_key(self, key):
        self._api_key = key
    
    @property
    def system_text(self)->str:
        return self._system_text
    
    def get_user_text(self, card_type:str|CardType)->str:
        if isinstance(card_type, CardType):
            return self._user_text[card_type]
        else:
            return self._user_text[CardType[card_type.upper()]]
    
    def load_chat_files(self) ->CommandResult:
        genre = self._genre.value
        system_filename = f"{self._resource_folder}/genres/{genre}/{GenreFilenames.TRAINING_SYSTEM.value}{genre}.txt"
        user_filename = f"{self._resource_folder}/genres/{genre}/{GenreFilenames.TRAINING_USER.value}{genre}"
        message = f'loaded "{system_filename}" and "{user_filename}" successfully'
        return_code = CommandResult.SUCCESS
        try:
            filename = system_filename
            with open(filename, "r") as fp:
                self._system_text = fp.read()
            fp.close()
            
            for card_type in self._card_types:
                ct = card_type.value
                filename = f"{user_filename}_{ct}.txt"
                print(filename)
                with open(filename, "r") as fp:
                    self._user_text[card_type] = fp.read()
                fp.close()
        except Exception as ex:
            message = f'"{filename}" does not exist\n exception: {str(ex)}'
            return_code = CommandResult.ERROR
        
        return CommandResult(return_code, message=message)
    
    def create_completion(self, system_text:str, user_text:str)->str:
        messages:List[Dict] = []
        system_message = {"role":"system", "content":system_text}
        user_message = {"role":"user", "content":user_text}
        
        messages.append(system_message)
        messages.append(user_message)
        completion = self._client.chat.completions.create(model="gpt-4o", messages=messages)
        
        msg = completion.choices[0].message
        return msg.content
        
    
