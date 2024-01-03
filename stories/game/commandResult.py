'''
Created on Dec 7, 2023

@author: don_bacon
'''
from game.storiesObject import StoriesObject
from typing import List
import json

class CommandResult(StoriesObject):
    """Encapsulates the result of a command executed by a game square or the CareersGameEngine
    
    """
    SUCCESS = 0         # Successful result
    ERROR = 1           # There was an error. message contains the error message
    TERMINATE = 2       # terminate the game
    EXECUTE_NEXT = 3    # successful, and execute the next_action for the current player
    NEED_PLAYER_CHOICE = 4  # successful, but need player choice as to what to do next
    

    def __init__(self, return_code:int, message:str=None, done_flag:bool=True, next_action:str=None, exception:Exception=None, choices:List[str]=None):
        """Constructor, baby.
            Arguments:
                return_code - integer return code:
                    SUCCESS = 0  Successful result
                    ERROR = 1  There was an error. message contains the error message
                    TERMINATE = 2  terminate the game
                    EXECUTE_NEXT = 3  success, and execute the next_action for the current player
                message - a message string to be displayed to the player. Can be blank or None, default value is None
                jsonMessage - a JSON formatted message for the server
                done_flag - if  True, this player's turn is completed, False otherwise. Default value is True
                next_action - next action to perform for this player, default is None. 
                        This should be in the format of an executable command

                exception - the Exception instance if the command raised an exception, default is None
                
            jsonMessage has the format: { "userMessage: <message>", "jsonText" : <JSON> }
            where <message> is the user message and jsonText is specific to the result.
            jsonMessage will always include "userMessage". 
        """
        self._return_code = return_code
        self._message = message
        self._json_message = f'{{"userMessage":{message}}}'
        self._done_flag = done_flag
        self._exception = exception
        self._next_action = next_action
        self._choices = choices
    
    @property
    def return_code(self):
        return self._return_code
    
    @return_code.setter
    def return_code(self, value):
        self._return_code = value
    
    @property
    def message(self):
        return self._message
    
    @message.setter
    def message(self, amessage):
        self._message = amessage
    
    @property
    def done_flag(self):
        return self._done_flag
    
    @done_flag.setter
    def done_flag(self, value):
        self._done_flag = value
    
    @property
    def exception(self):
        return self._exception
    
    @exception.setter
    def exception(self, value):
        self._exception = value
        
    @property
    def next_action(self):
        return self._next_action
    
    @next_action.setter
    def next_action(self, value):
        self._next_action = value
        
    @property
    def json_message(self):
        return self._json_message
    
    @json_message.setter
    def json_message(self, value):
        self._json_message = value
        
    def set_json_message_text(self, text, key="jsonText"):
        """Sets the jsonText portion of json_message.
            Use key="userMessage" to set the userMessage
        """
        d = dict(self.json_message)
        d[key] = text
        self._json_message = json.dumps(d)
        
    @property
    def choices(self) -> List[str]:
        return self._choices
    
    @choices.setter
    def choices(self, value:List[str]):
        self._choices = value
        
    def is_successful(self):
        return True if self.return_code == CommandResult.SUCCESS else False
    
    def to_dict(self):
        d = {"return_code" : self.return_code, "done_flag" : self.done_flag, "message" : self.message, "json_message":self.json_message }
        if self.next_action is not None:
            d["next_action"] = self.next_action
        if self.exception is not None:
            d["exception"] = str(self.exception)
        
        return d
        
    def to_JSON(self):
        jstr = json.dumps(self.to_dict())
        return jstr
    
    @staticmethod
    def successfull_result(message=""):
        return CommandResult(CommandResult.SUCCESS, message, True)
        