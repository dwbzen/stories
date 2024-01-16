'''
Created on Dec 22, 2023

@author: don_bacon
'''

from game.gameConstants import GameConstants, ActionType, CardType, CardTypeEncoder
from game.storiesGame import StoriesGame
from game.commandResult import CommandResult
from game.gameState import GameState
from game.player import Player
from game.storyCard import StoryCard
from game.storyCardList import StoryCardList

from typing import Tuple, List
import joblib
import random, json, sys
import logging


class GameEngineCommands(object):
    """Implementation of StoriesGame player commands.
        Commands are listed in GameConstants BTW
    """


    def __init__(self, stories_game:StoriesGame):
        '''
        Constructor
        '''
        assert(stories_game is not None)
        self._stories_game = stories_game
        self._game_state = self._stories_game.game_state
        self._debug = False
        self._game_id = stories_game.game_id
    
    @property
    def stories_game(self)->StoriesGame:
        return self._stories_game
    
    @stories_game.setter
    def stories_game(self, thegame):
        self._stories_game = thegame
    
    @property
    def game_state(self)->GameState:
        return self._game_state
        
    @property
    def debug(self):
        return self._debug
    
    @debug.setter
    def debug(self, value):
        self._debug = value
        
    @staticmethod
    def parse_command_string(txt:str, addl_args=[]) -> CommandResult:
        """Parses a command string into an executable string, i.e. that can be executed with eval()
            Returns: if return_code == 0, a CommandResult with commandResult.message as the string to eval()
                else if return_code == 1, commandResult.message has the error message
        """
        command_args = txt.split()
        command = command_args[0]
        if not command in GameConstants.COMMANDS:
            return CommandResult(CommandResult.ERROR,  message=f'Invalid command: "{command}"',  done_flag=False)
        if len(command_args) > 1:
            args = command_args[1:]
            command = command + "("
            for arg in args:
                if arg.isdigit():
                    command = command + arg + ","
                else:
                    command = command + f'"{arg}",'
        
            command = command[:-1]    # remove the trailing comma
        else:
            command = command + "("
            
        if addl_args is not None and len(addl_args) > 0:
            for arg in addl_args:
                command = command + f'"{arg}",'
            command = command[:-1]

        command += ")"
        return CommandResult(CommandResult.SUCCESS, command, False)
            
    def log(self, message):
        """Write message to the log file.

        """
        logging.info(message)
        if self.debug:
            print(message)
            
    def get_player(self, pid:str) -> Player | None :
        """Gets a Player by initials, name, or number
            Arguments:
                pid - string that represents a player number, name or initials
            Returns: Player instance or None if no player with the given ID exists.
            Note that name/initials are NOT case sensitive.
        """
        player = None
        if pid.isdigit():
            player = self.game_state.players[int(pid)]
        else:   # lookup the player by name or initials
            players = self.game_state.players
            lc_pid = pid.lower()
            for p in players:
                if p.player_initials.lower() == lc_pid or p.player_id  == lc_pid:
                    player = p
                    break
        return player
    
    #####################################
    #
    # Game engine command functions
    #
    #####################################

    def add(self, what, player_name, initials=None, player_id=None, email=None) -> CommandResult:
        """Add a new player to the Game. Other 'adds' TBD
    
        """
        if what == 'player':
            player = Player(name=player_name, player_id=player_id, initials=initials, email=email, game_id=None)
            self._stories_game.add_player(player)        # adds to GameState which also sets the player number
            message = player.to_JSON()
            self.log(message)
            result = CommandResult(CommandResult.SUCCESS, message=message)
        else:
            message = f"Cannot add {what} here."
            result = CommandResult(CommandResult.ERROR, message=message, done_flag=False)
            
        return result

    def start(self) -> CommandResult:
        message = f'Starting game {self.game_id}'

        self.log_info(message)
        self.game_state.set_next_player()    # sets the player number to 0 and the curent_player Player reference
        self.game_state.started = True
        self._stories_game.start_game()       # sets the start datetime
                
        return CommandResult(CommandResult.SUCCESS, message, True)
    
    def done(self)-> CommandResult:
        """Complete the current player's turn
        """
        player = self.game_state.current_player
        result = player.end_turn()
        if result.return_code is CommandResult.SUCCESS:
            npn = self.game_state.set_next_player()
            player = self.game_state.current_player

        return result
    
    def draw(self, what:str="new", types_to_omit:List[CardType]=None) ->CommandResult:
        """Draw a card from the deck OR from the top of the global discard deck
            Arguments:
                what - 'new' : draw a card from the main deck. 'discard' : draw the top card from the game discard deck
                types_to_omit - a List[CardType] to omit drawing.
            Returns:
                CommandResult with return_code set to SUCCESS or ERROR (if there are no cards left to draw from),
                    and message set to an error message OR if SUCCESS, the card_type drawn.
        """

        player = self.game_state.current_player
        
        card,message = self.stories_game.draw_card(what, types_to_omit)
        if card is None:    # must be an error, message has the error message
            result = CommandResult(CommandResult.ERROR, message, done_flag=False)
        else:
            # add this drawn card to the player hand
            player._story_card_hand.add_card(card)
            player.card_drawn = True
            message = f"{player.player_initials} drew a {card.card_type.value} card: {card.text}\n Please play or discard 1 card."
            result = CommandResult(CommandResult.SUCCESS, message, done_flag=False)
            
        return result

    def discard(self, card_number:int)->CommandResult:
        """Discard card as indicated by card_number from a player's hand
            and adds to the game discard deck.
        """
        player = self.game_state.current_player
        card_discarded = player.discard(card_number)
        if card_discarded is None:
            message = f"You are not holding a card with number {card_number}"
            result = CommandResult(CommandResult.ERROR, message, False)
            
        else:
            message = f"You are discarding {card_number}. {card_discarded.text}"
            self.stories_game.add_to_discard(card_discarded)
            result = CommandResult(CommandResult.SUCCESS, message, True)
        return result
        
    
    def play(self, card_number:int, **kwargs) ->CommandResult:
        """Play a story/action card
            Arguments:
                card_number - the card in 
        """
        player = self.game_state.current_player
        card_played = player.play_card(card_number)
        if card_played is None:
            message = f"You are not holding a card with number {card_number}"
            result = CommandResult(CommandResult.ERROR, message, False)
            
        else:
            message = f"You played {card_number}. {card_played.text}"
            result = CommandResult(CommandResult.SUCCESS, message, True)

        return result

    def list(self, what='hand', initials:str='me', how='numbered') ->CommandResult:
        """List the cards held by the current player
            Arguments: what - 'hand', 'story'
                initials - a player's initials, defaults to the current player "me"
                how - 'numbered' for a numbered list, 'regular', the default, for no numbering
            Returns: CommandResult.message is the stringified list of str(card) in the player's hand or story
            
        """
        # TODO
        player = self.game_state.current_player if initials=="me" else self.get_player(initials)
        done_flag = True
        return_code = CommandResult.SUCCESS
        if what == 'hand':
            message = str(player.story_card_hand.cards) if how=="regular" else self._list(player.story_card_hand.cards)
        elif what == 'story':
            message = str(player.story_card_hand.my_story_cards) if how=="regular" else self._list(player.story_card_hand.my_story_cards)
        else:
            message = f"I don't understand {what}"
            done_flag = False
            return_code = CommandResult.ERROR
        
        return CommandResult(return_code, message, done_flag)
    
    def _list(self, cards:StoryCardList) ->str:
        card_text = ""
        n = 1
        for card in cards.cards:
            card_text = card_text + f"{n}. {str(card)}"
            n += 1
            
        return card_text
    
    def show(self, what)->CommandResult:
        """Displays the top card of the discard pile
            Arguments:
                what - what to display: discard (top card of the discard pile) 
                or a story element class: "Title", "Opening", "Opening/Story", "Story", "Closing", "Action"
            Returns: CommandResult.message is the str(card) for discard, a numbered list of str for story element classes.
        """
        message = ""
        if what.lower()=="discard":
            card,message = self.stories_game.get_discard()
            return_code = CommandResult.SUCCESS if card is not None else CommandResult.ERROR
            done_flag = True if card is not None else False
        else:    # display all the elements of a given story class
            done_flag = True
            return_code = CommandResult.SUCCESS
            card_type = what.title()     # just in case
            cards = self.stories_game.get_cards_by_type(card_type)    # what must be a valid card_type.value
            if len(cards) > 0:   # List[str]
                n = 1
                for card in cards:
                    message = f"{message}{n}.  {card}"
                    n += 1
            result = CommandResult(return_code, message, done_flag)
        
        return result
        
    def read(self, initials:str=None)->CommandResult:
        """Display a player's story in a readable format.
        """
        player = self.game_state.current_player if initials is None else self.get_player(initials)
        done_flag = True
        message = player.story_card_hand.my_story_cards.to_string()

        return CommandResult(CommandResult.SUCCESS, message, done_flag)
    
    def status(self, initials:str=None)->CommandResult:
        player = self.game_state.current_player if initials is None else self.get_player(initials)
        message = json.dumps(player.story_elements_played, cls=CardTypeEncoder)
        return CommandResult(CommandResult.SUCCESS, message, True)
        
    def log_message(self, message):
        """Logs a given message to the log file and console if debug flag is set
        """
        self.log(message)


    def execute_action_card(self,  player:Player, actionCard:StoryCard) -> CommandResult:
        """Executes a StoryCard that has an ActionType
        """
        action_type = actionCard.action_type        # ActionType
        message = f'{player.player_initials} Playing  {actionCard.action_type}: {actionCard.text}'
        self.log(message)
        match(action_type):
            case ActionType.DRAW_NEW:
                pass    # TODO
            case ActionType.MEANWHILE:
                pass    # TODO
            case ActionType.STEAL_LINES:
                pass    # TODO
            case ActionType.TRADE_LINES:
                pass    # TODO
            case ActionType.STIR_POT:
                pass    # TODO
        
        result = CommandResult(CommandResult.SUCCESS, message=message)
        return result
        