'''
Created on Dec 8, 2023

@author: don_bacon
'''
import random, math
from datetime import datetime
from typing import List

class GameUtils(object):
    """
    General purpose routines.
    """

    def __init__(self, params):
        self.params = params
    
    @staticmethod
    def shuffle(size:int) -> List[int]:
        """Returns a random sample of the integers from 0 to size-1.
            This represents a shuffle of indexes of some list.
            For example, shuffle(5) could return [0, 4, 1, 2, 3]
            Returns an empty List if size==0
        """
        return random.sample(list(range(0, size)), size) if size>0 else []

    @staticmethod
    def shuffle_list(lines:List) -> List:
        """Shuffle List elements
        """
        nlines = len(lines)
        new_list = []
        line_indexes = GameUtils.shuffle(nlines)
        for ind in range(nlines):
            new_list.append(lines[line_indexes[ind]])
        return new_list
       
    @staticmethod
    def roll(number_of_dice)->List[int]:
        return random.choices(population=[1,2,3,4,5,6],k=number_of_dice)
    
    @staticmethod
    def roll_dice(number_of_faces=6, origin=1, number_of_dice=1)->List[int]:
        """Rolls n-dice with an arbitrary number of faces.
            Arguments:
                number_of_faces - number of faces on a single die, typically 6 (the default), 
                    12, or 20 but can be any positive integer>0.
                origin - numbering start, defaults to 1
                number_of_dice - number of dice to roll, default is 1
        """
        population = list(range(origin, number_of_faces+origin))
        return random.choices(population=population,k=number_of_dice)
    
    @staticmethod
    def get_datetime() -> str:
        """Returns - current date/time (now) formatted as a string, for example: 20220911_120545
        """
        now = datetime.today()
        return '{0:d}{1:02d}{2:02d}_{3:02d}{4:02d}{5:02d}'.format(now.year, now.month, now.day, now.hour, now.minute, now.second)
    
    @staticmethod
    def time_since(base_date:datetime=datetime(2000, 1, 1, 0, 0),  end_date=None, what='seconds', decimals=0) -> int:
        """Gets the number of seconds or days that has passed since a given base date/datetime
            Arguments:
                base_date : the base date, default is 12:00 AM 2000-01-01
                what : 'seconds', 'days', or 'years'
            Returns:
                The seconds or days since the base date to now, truncated to an integer
        """
        end_date = datetime.now() if end_date is None else end_date
        delta = end_date-base_date
        if what=='seconds':
            return delta.total_seconds()
        elif what == 'years':
            if decimals==0:
                return delta.days // 365
            else:
                return round(delta.days / 365, decimals)
        else:   # assume days
            return delta.days
    
    @staticmethod
    def create_guid(installation_id="") ->str:
        today = datetime.now()
        gid = '{0:d}{1:02d}{2:02d}_{3:02d}{4:02d}_{5:04d}'\
            .format(today.year, today.month, today.day, today.hour, today.minute, random.randint(1,9999))
        return f"{installation_id}_{gid}"
    
    @staticmethod
    def create_id(id_type:str)->str:
        """Create a generic global ID for a given id type
        """
        today = datetime.now()
        gid = '{0:d}{1:02d}{2:02d}_{3:02d}{4:02d}{5:02d}__{6:04d}'\
            .format(today.year, today.month, today.day, today.hour, today.minute, today.second, random.randint(1000,9999))
        return f"{id_type}_{gid}"
    
    @staticmethod
    def create_playerid(initials:str) ->str:
        today = datetime.now()
        pid = '{0:d}{1:02d}{2:02d}_{3:02d}{4:02d}{5:02d}'.format(today.year, today.month, today.day, today.hour, today.minute, today.second)
        return f"{initials}_{pid}"
    
    
    
    
    
        