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

from typing import List
import logging, json


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
            At the end of the last player's turn, check if all players have
            played a TITLE and/or OPENING story card.
            If so, add the CardType(s) to the GameState types_to_omit.
            So on subsequent draws these card types are skipped.
        """
        current_player = self.game_state.current_player
        omit_types = []
        if current_player.number == self.game_state.number_of_players - 1:
            omit_types = self._check_types_to_omit()
        result = current_player.end_turn()
        if result.return_code is CommandResult.SUCCESS:
            npn = self.game_state.set_next_player()
            next_player = self.game_state.current_player
            message = f"{result.message}. {next_player.player_initials}'s turn."
        else:
            message = result.message
        if len(omit_types) > 0:
            self.game_state.add_card_types_to_omit(omit_types)
            msg = ",".join([x.value for x in omit_types])
            message = f"{message}\nCard types omitted from future draws: {msg}"
            #
            # remove cards having a card type in types_to_omit 
            # from the current_player's (the player whose turn is done) hand and replace with new cards
            #
            msg = self._update_player_hand(current_player, omit_types)
        return result
    
    def _check_types_to_omit(self)->List[CardType]:
        """Check if all players have played a TITLE and/or OPENING story card.
            Return: List[CardType] that have been played by all players
        """
        omit_types:List[CardType] = []
        omit_title = True
        omit_opening = True
        for player in self.game_state.players:
            omit_title &= player.story_elements_played[CardType.TITLE]>0
            omit_opening &= player.story_elements_played[CardType.OPENING]>0
        if omit_title:
            omit_types.append(CardType.TITLE)
        if omit_opening:
            omit_types.append(CardType.OPENING)
        return omit_types
    
    def _update_player_hand(self, current_player, omit_types:List[CardType])->str:
        """Update a player's hand to remove cards of a given type
            and replace with new drawn cards.
        """
        ncards = 0    # number of cards removed from the player's hand
        message = ""
        for card_type in omit_types:
            ncards += current_player.story_card_hand.discard_cards(card_type)
        for i in range(ncards):
            result = self.draw_for(current_player, "new", i)
            message = f"{message}\n{result.message}"
            
        return message
    
    def draw_for(self, player:Player, what:str="new", ordinal:int=1):
        """Draw one new card for a given player, omitting card types
            that are no longer needed. 
        """
        types_to_omit = self.game_state.types_to_omit    # possibly empty List[CardType]
        card,message = self.stories_game.draw_card(what, types_to_omit)
        if card is None:    # must be an error, message has the error message
            result = CommandResult(CommandResult.ERROR, message, done_flag=False)
        else:
            # add this drawn card to the player hand
            player._story_card_hand.add_card(card)
            player.card_drawn = True
            message = f"{ordinal}. {player.player_initials} drew a {card.card_type.value} ({card.number}): {card.text}"
            result = CommandResult(CommandResult.SUCCESS, message, done_flag=False)
            
        return result
    
    def draw(self, what:str="new") ->CommandResult:
        """Draw a card from the deck OR from the top of the global discard deck
            Arguments:
                what - 'new' : draw a card from the main deck. 'discard' : draw the top card from the game discard deck
                types_to_omit - a List[CardType] to omit drawing.
            Returns:
                CommandResult with return_code set to SUCCESS or ERROR (if there are no cards left to draw from),
                    and message set to an error message OR if SUCCESS, the card_type drawn.
        """
        player = self.game_state.current_player
        result = self.draw_for(player, what)
        result.message = f"{result.message}\n Please play or discard 1 card."
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
        
    
    def play(self, card_number:int, card_numbers:str|None) ->CommandResult:
        """Play a story/action card from a player's hand OR the discard deck
            Arguments:
                card_number - the StoryCard to play.
                card_numbers - additional comma-separated card numbers or None. card_numbers is required for certain types of action cards.
                    
            Example: play 110    ; play a single story card
        """
        player = self.game_state.current_player
        story_card = player.story_card_hand.get_card(card_number)
        if story_card is None:
                message = f"Invalid card number {card_number}"
                result = CommandResult(CommandResult.ERROR, message, False)
        
        elif story_card.card_type is CardType.ACTION:
            result = self._execute_action_card(player, story_card, str(card_numbers))
            
        else:
            card_played = player.play_card(story_card)
            if card_played is None:
                message = f"Invalid card number {card_number}"
                result = CommandResult(CommandResult.ERROR, message, False)
            else:
                message = f"You played {card_played.number}. {card_played.text}"
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
            
        elif what.lower()=="all":
            n = 1
            for card_type in ["Title", "Opening", "Opening/Story", "Story", "Closing", "Action"]:
                cards = self.stories_game.get_cards_by_type(card_type)
                for card in cards:
                    message = f"{message}{n}.  {card}"
                    n += 1
            done_flag = True
            return_code = CommandResult.SUCCESS            
                
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
        
    def read(self, numbered:bool, initials:str=None)->CommandResult:
        """Display a player's story in a readable format.
            Arguments:
                numbered - if True number the lines starting at 1 with the first story card.
                        The Title and Closing line(s) are not numbered.
                initials - the player's initials if other than the current player
        """
        player = self.game_state.current_player if initials is None else self.get_player(initials)
        done_flag = True
        message = player.story_card_hand.my_story_cards.to_string(numbered)

        return CommandResult(CommandResult.SUCCESS, message, done_flag)
    
    def status(self, initials:str=None)->CommandResult:
        player = self.game_state.current_player if initials is None else self.get_player(initials)
        message = json.dumps(player.story_elements_played, cls=CardTypeEncoder)
        return CommandResult(CommandResult.SUCCESS, message, True)
        
    def log_message(self, message):
        """Logs a given message to the log file and console if debug flag is set
        """
        self.log(message)

    def _execute_action_card(self,  player:Player, action_card:StoryCard, cards:str|None) -> CommandResult:
        """Executes a StoryCard that has an ActionType
            Arguments:
                player - a Player instance
                action_card - a StoryCard with card_type CardType.ACTION
                cards - a comma-separated list of additional card numbers or None
                
            Examples of Action cards:
                meanwhile: play 249 110           ; card #249 is the meanwhile ActionCard, 110 is a story card
                draw_new:  play 250 100,119,143   ; card #25 0 is the draw_new ActionCard, the cards to replace with new ones are 110,119,143
                trade_lines:  play 251 178,92     ; card #251 is the trade_lines Action Card, 
                                                    178 is a story card in my story, 92 is a story card in an opponent's story (so visible to all)
                steal_lines:  play 252 93   ; card #252 is a steal_lines ActionCard, 93 is a story card in an opponent's story
                                              The stolen card goes in my hand
                stir_pot: play 266          ; card #266 is a stir_pot ActionCard. 
                                              Each player selects a card from their hand and passes it to the person to their left
                change_name: play 272 151 Brian,He    ; card #272 is a change_name ActionCard, 272 is a card in my current story.
                                                        change instances of "Brian" in that card to "He"
                NOTE that change_name supported only in the online version of the game
        """
        action_type = action_card.action_type        # ActionType
        card_numbers = [] if cards is None else cards.split(",")
        story_cards = []
        for num in card_numbers:
            sc = player.story_card_hand.get_card(num)
            if sc is None:
                message = f"You are not holding a card with number {num}"
                self.log(message)
                return CommandResult(CommandResult.ERROR, message, False)
            else:
                story_cards.append(sc)
        
        message = f'{player.player_initials} Playing  {action_card.action_type}: {action_card.text}'
        min_args = action_card.min_arguments
        max_args = action_card.max_arguments
        num_args = len(story_cards)
        self.log(message)
        #
        # check number of arguments is within range
        #
        if num_args < min_args or num_args > max_args:
            message = f"{action_card.action_type} requires from {min_args} to {max_args} additional card numbers."
            self.log(message)
            return CommandResult(CommandResult.ERROR, message, False)
        return_code = CommandResult.SUCCESS
        done_flag = True
        match(action_type):
            case ActionType.DRAW_NEW:
                pass    # Discard up to 4 cards and draw replacements
            case ActionType.MEANWHILE:    # requires an additional card to come after the "Meanwhile..."
                story_card = story_cards[0]
                action_card_played = player.play_card(action_card)
                story_card_played = player.play_card(story_card)
                message = f"You played {action_card_played.number}. {action_card_played.text} and {story_card_played.number}. {story_card_played.text}"
                
            case ActionType.STEAL_LINES:
                # Steal a story card played by another player4
                message = f"{action_card.number}. {action_card.action_type.value} not yet implemented."
            
            case ActionType.TRADE_LINES:
                # Trade an Opening or Story element that has been played with that from another player's story
                message = f"{action_card.number}. {action_card.action_type.value} not yet implemented."
                    
            case ActionType.STIR_POT:
                # Each player selects a story element from their deck and passes it to the person to their left
                message = f"{action_card.number}. {action_card.action_type.value} not yet implemented."
                    
            case ActionType.CHANGE_NAME:
                # Change the character name on a selected story card to a different alias or pronoun
                message = f"{action_card.number}. {action_card.action_type.value} not yet implemented."    
        
        result = CommandResult(return_code, message, done_flag)
        return result
        