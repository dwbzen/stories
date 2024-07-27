'''
Created on July 19, 2024

@author: don_bacon
'''

from game.player import Player
from game.storiesObject import StoriesObject
from game.gameConstants import PlayerRole
from typing import List, Dict
import json

class Team(StoriesObject):
    """Encapsulates a stories game team. 
        A Team has a name and at least 2 players that are team members.
        One member of the team has the PlayerRole of TEAM_LEAD, the others TEAM_PLAYER
    """


    def __init__(self, team_name):
        """Create a new Team with no members.
        """
        self._name = team_name
        self._members:List[Player] = []
        self._team_lead:Player = None
    
    @property
    def name(self)->str:
        return self._name
    
    @name.setter
    def name(self, newname):
        self._name = newname
    
    @property
    def members(self)->List[Player]:
        return self._members
    
    @property
    def team_lead(self)->Player:
        return self._team_lead
    
    def size(self)->int:
        return len(self.members)
    
    def add_member(self, player:Player, player_role:PlayerRole=PlayerRole.PLAYER):
        """Adds a player to the team (if not already a member).
           This does NOT check if the player is already a member of different team.
            player - a Player instance.
        """
        if player not in self._members:
            player.player_role = player_role
            self._members.append(player)
            if player.player_role is PlayerRole.TEAM_LEAD:
                self._team_lead = player

    def get_member_info(self)->Dict:
        team_members = []
        for player in self.members:
            pdict = {"name" : player.player_name, "number" : player.number, "initials" : player.player_initials, "role":player.player_role.value}
            team_members.append(pdict)
        return team_members
    
    def __repr__(self)->str:    # official string representation
        return self.to_JSON(indent=0)
    
    def __str__(self)->str:
        members = str(self.get_member_info())
        team_text = f"Team {self.name}: {members}"
        return team_text
    
    def to_dict(self)->Dict:
        team_members = self.get_member_info()
        team_dict = {"name":self.name}
        team_dict["members"] = team_members
        return team_dict

    def to_JSON(self):
        return json.dumps(self.to_dict(), indent=2)
        
    