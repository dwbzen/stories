'''
Created on Dec 7, 2023

@author: don_bacon
'''

from abc import ABC,abstractmethod
import jsonpickle

class StoriesObject(ABC):
    """Abstract Base class for object that have a JSON representation.
    """


    def __init__(self, params):
        '''
        Constructor
        '''
        pass

    @abstractmethod
    def to_JSON(self)->str:
        """Returns my JSON representation. Abstract class.
        """
        ...
    
    def json_pickle(self):
        """A complete JSON representation of this object using jsonpickle.
        """
        return jsonpickle.encode(self, indent=2)
        
    def __repr__(self):
        return self.json_pickle()
    
    def __str__(self)->str:
        return self.to_JSON()
    