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
                if p.player_initials.lower() == lc_pid or p.player_id  == lc_pid or p.player_name.lower() == lc_pid:
                    player = p
                    break
        return player
    
    def check_errors(self)->bool:
        """Return True if checking for player errors.
            Bypassing error checks is useful for testing.
            The value is set in the gameParameters JSON file as "bypass_error_checks".
            This simply returns the negative of that value.
            @see GameParameters
        """
        return self.stories_game.check_errors()
    
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
        check_errors = self.check_errors()   # check for errors?
        if current_player.number == self.game_state.number_of_players() - 1:    # If I am the last player
            omit_types = self._check_types_to_omit()
        result = current_player.end_turn(check_errors)
        if result.return_code is CommandResult.SUCCESS:
            npn = self.game_state.set_next_player()
            next_player = self.game_state.current_player
            message = f"{result.message}. {next_player.player_initials}'s turn, player# {npn}."
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
    
    def end(self, what:str) ->CommandResult:
        """Ends the round or game, saves the current state and exits.
            Arguments:
                what - "round" to end the current story round, "game" to end the entire game.
                    Ending the game ends the current round and tallies the points for the round,
                    determine a winner or winners, then ends the game.
            Returns:
                CommandResult - for what == "round", the winner's initials is returned in the result properties dict
                    as in {"winner" : "my_initials"}.
                    For what == "game", if the current round is successfully ended, the return_code is set to CommandResult.TERMINATE
                    Otherwise CommandResult.ERROR is returned and the message has the specifics.
            Note that error checking is bypassed if the bypass_error_flags property (determined by
            the parameters file) is True.
        """

        game_points = self.stories_game.game_parameters.game_points
        story_length = self.stories_game.game_parameters.story_length
        bypass_error_checks = self.stories_game.game_parameters.bypass_error_checks
        return_code = CommandResult.SUCCESS
        message = ""
        winner:Player = None
        
        #
        # Try to end the current round first, then if what is "game" also end the entire game.
        # In both cases points are tallied and winner(s) are determined.
        # is ending the round valid? check the number of story cards for each player
        #
        # TODO - score round points based on who came in first, second & third.
        #
        for player in self.game_state.players:
            story_elements_played = player.story_elements_played    # Dict[CardType,int]
            points = story_elements_played[CardType.STORY]   # 1 point for every story card
            points += (story_elements_played[CardType.STORY] - story_length)   # bonus/penalty points for every card over/under the minimum
            player.points = points
            pm = json.dumps(story_elements_played, cls=CardTypeEncoder)
            if winner is None or winner.points > player.points:
                winner = player
            if bypass_error_checks or \
                (story_elements_played[CardType.TITLE] == 1 and \
                 story_elements_played[CardType.OPENING] == 1 and \
                 story_elements_played[CardType.CLOSING] == 1):
                #
                # looks good!
                message = f"{message} Player: {player.player_initials} played cards: {pm}\n "
            else:    # something missing
                message = f"{message} Player: {player.player_initials} has not played necessary cards: {pm}\n "
                return_code = CommandResult.ERROR
                    
        if return_code is CommandResult.SUCCESS:
            message = f"The {what} is over and the winner with {winner.points} is {winner.player_initials}"
            if what == "game":
                return_code = CommandResult.TERMINATE

        result = CommandResult(return_code, message, True)
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
        
    def draw(self, what:str, action_type:ActionType) ->CommandResult:
        """Draw a card from the deck OR from the top of the global discard deck
                what - what to draw or where to draw from:
                       new - draw a card from the main card deck
                       discard - draw the top of the global discard deck
                       <type> - any of: "title", "opening", "opening/story", "story", "closing", "action"
                action_type - if what == "action", the ActionType to draw: "meanwhile", "trade_lines", "steal_lines",
                        "stir_pot", "draw_new", "change_name"
            Returns:
                CommandResult with return_code set to SUCCESS or ERROR (if there are no cards left to draw from),
                    and message set to an error message OR if SUCCESS, the card_type drawn.
            Specifying the card and action_type are for testing purposes only.        
            Note game_state.types_to_omit is a List[CardType] to omit drawing. This is set globally
            for example when all players have played a Title card, a Title card will no longer be drawn.
        """
        player = self.game_state.current_player 
        return self.draw_for(player, what, action_type)
    
    def draw_for(self, player:Player, what:str, action_type:ActionType=None, ordinal:int=1)->CommandResult:
        """Draw one new card for a given player, omitting card types that are no longer needed. 
            Arguments:
                player - the Player to draw a card for
                what - what to draw or where to draw from:
                       new - draw a card from the main card deck
                       discard - draw the top of the global discard deck
                       <type> - any of: "title", "opening", "opening/story", "story", "closing", "action"
                action_type - if what == "action", the ActionType to draw: "meanwhile", "trade_lines", "steal_lines",
                        "stir_pot", "draw_new", "change_name"
            @see StoriesGame.draw_card() 
        """
        card,message = self.stories_game.draw_card(what, action_type)
        if card is None:    # must be an error, message has the error message
            result = CommandResult(CommandResult.ERROR, message, done_flag=False)
        else:
            # add this drawn card to the player hand
            player._story_card_hand.add_card(card)
            player.card_drawn = True
            message = f"{ordinal}. {player.player_initials} drew a {card.card_type.value} ({card.number}): {card.text}"
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
        
    
    def play(self, card_number:int, *args) ->CommandResult:
        """Play a story/action card from a player's hand OR the discard deck
            Arguments:
                card_number - the StoryCard to play.
                args - additional arguments, depending on the type of action card played.
                    
            Examples: play 110        ; play a single story card
                      play 200 110    ; play a MEANWHILE ActionCard (#200), adding "Meanwhile" to story card 110
            Use the command "help action <action card type>" for more information
            about a specific action card. For example, "help action change_name"
            The story card text is added to the end of the story for card types of "Opening/Story" and "Story"
            For "Title", "Opening" and "Closing" if there is an existing story card of that type
            in the player's story, it is replaced with the new one, otherwise it's added to the end.
        """
        player = self.game_state.current_player
        story_card = player.story_card_hand.get_card(card_number)
        if story_card is None:
                message = f"Invalid card number {card_number}"
                result = CommandResult(CommandResult.ERROR, message, False)
        
        elif story_card.card_type is CardType.ACTION:
            result = self.execute_action_card(player, story_card, args)
            
        else:
            card_played = player.play_card(story_card)
            if card_played is None:
                message = f"Invalid card number {card_number}"
                result = CommandResult(CommandResult.ERROR, message, False)
            else:
                message = f"You played {card_played.number}. {card_played.text}"
                result = CommandResult(CommandResult.SUCCESS, message, True)
                
        return result
    
    def insert(self, line_number:int, card_number:int )->CommandResult:
        """Insert a story card into your current story.
            Arguments:
                line_number - the line# in your current story to insert a new card after.
                card_number - the number of a story card in your hand
            Returns:
                CommandResult.ERROR if the card_number or line_number is invalid (doesn't exist)
                else CommandResult.SUCCESS
        """
        player = self.game_state.current_player
        story_card = player.story_card_hand.get_card(card_number)
        story_card_list = player.story_card_hand.my_story_cards
        if story_card is None:
                message = f"Invalid card number {card_number}"
                result = CommandResult(CommandResult.ERROR, message, False)
        #
        # check that the line_number exists
        #
        if line_number < 0 or line_number >= story_card_list.size():
                message = f"Invalid line number {line_number} you naughty person"
                result = CommandResult(CommandResult.ERROR, message, False)
        else:
            card_played = player.play_card(story_card, line_number)
            message = f"You played {card_played.number}. {card_played.text} after line# {line_number}"
            result = CommandResult(CommandResult.SUCCESS, message, True)
            
        return result
    
    def replace(self, line_number:int, card_number:int )->CommandResult:
        """Replace a card in your current story with one in your hand.
            Arguments:
                line_number - the line# in your current story to replace
                card_number - the number of a story card in your hand
            Returns:
                CommandResult.ERROR if the card_number or line_number is invalid (doesn't exist)
                else CommandResult.SUCCESS
                
            The card being replaced is automatically discarded.
            Operation is the same as playing a TITLE, OPENING or CLOSING
            when that card type is in your current story.
        """
        player = self.game_state.current_player
        story_card = player.story_card_hand.get_card(card_number)
        story_card_hand = player.story_card_hand
        story_card_list = story_card_hand.my_story_cards
        if story_card is None:
                message = f"Invalid card number {card_number}"
                result = CommandResult(CommandResult.ERROR, message, False)
        #
        # check that the line_number exists
        #
        if line_number < 0 or line_number >= story_card_list.size():
                message = f"Invalid line number {line_number}"
                result = CommandResult(CommandResult.ERROR, message, False)
        else:
            result = CommandResult(CommandResult.ERROR, "Replace not implemented yet", False)
        
        return result
    
    def pass_card(self, card_number:int,  initials:str="me")->CommandResult:
        """Pass a card in the designated player's hand to (the hand of) the next player (to the left).
            Arguments:
                card_number - the number of the card to pass. It must exist in the current player's hand
                initials - the initials of the player doing the passing. Defaults to 'me' indicating the current player.
            This command does nothing in a solo game.
        """
        player = self.game_state.current_player if initials=="me" else self.get_player(initials)
        npn = self._game_state.get_next_player_number(player)
        if player.number == npn:    # nothing to do
            return CommandResult(CommandResult.SUCCESS, "No other players to pass to!", True)
            
        story_card = player.remove_card(card_number)
        if story_card is None:
                message = f"Invalid card number {card_number}"
                return CommandResult(CommandResult.ERROR, message, False)
            
        next_player:Player = self.game_state.players[npn]
        next_player.add_card(story_card)
        return CommandResult(CommandResult.SUCCESS, f"Card #{card_number} removed from {player.player_initials}'s hand and given to {next_player.player_initials}")

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
            
        elif what.lower()=="all":    # show story cards by card_type
            n = 1
            for card_type in ["Title", "Opening", "Opening/Story", "Story", "Closing", "Action"]:
                cards = self.stories_game.get_cards_by_type(card_type)
                for card in cards:
                    message = f"{message}{n}. {card}"
                    n += 1
            done_flag = True
            return_code = CommandResult.SUCCESS
        
        elif what.lower()=="deck":    # show all cards in the deck in the order they appear in the deck
            n = 1
            cards = self.stories_game.get_cards()
            for card in cards:
                message = f"{message}{n}. {card}"
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
    
    def info(self, initials:str)->CommandResult:
        """Provide information on the game currently in progress.
           Get player information
        """
        player = self.game_state.current_player if initials is None else self.get_player(initials)
        return_code = CommandResult.SUCCESS
        if player is None:
            return_code = CommandResult.ERROR
            message = f"There is no such player"
        else:
            message = player.info()
        return CommandResult(return_code, message)
        
    def log_message(self, message):
        """Logs a given message to the log file and console if debug flag is set
        """
        self.log(message)

    def execute_action_card(self,  player:Player, action_card:StoryCard, args) -> CommandResult:
        """Executes a StoryCard that has an ActionType
            Arguments:
                player - a Player instance
                action_card - a StoryCard with card_type CardType.ACTION
                args - a single card number OR a comma-separated list of additional card numbers or strings
                
            Examples of Action cards:
                meanwhile: play 249 110           ; card #249 is the meanwhile ActionCard, 110 is a story card
                
                draw_new:  play 250 100 119 143   ; card #250 is the draw_new ActionCard, the cards to replace with new ones are 110,119,143
                
                trade_lines:  play 251 BRI  1 2        ; card #251 is the trade_lines Action Card, 
                                                         1 is the line 1 story card in my story, 
                                                         2 is the line 2 story card in an opponent's (BRI) story (so visible to all)

                steal_lines:  play 252 Brian 4    ; card #252 is a steal_lines ActionCard. Steal line#4 from Brian's  story and place it in my hand
                
                stir_pot: play 266  151     ; card #266 is a stir_pot ActionCard. Each player selects a card from their hand 
                                              and passes it to the person to their left. Card #151 is the current player's card to pass.
                                              Remaining players use the 'pass <card_number>' command.
                                              
                change_name: play 272 3 Brian/He        ; card #272 is a change_name ActionCard, 3 is line 3 in my current story.
                                                          change instances of "Brian" in that card to "He"
                                                        
                compose: play 273  She knew it was a mistake!    ; card #273 is a COMPOSE ActionCard. 
                                                                   The StoryCard text is "She knew it was a mistake!"
                                                                   
                NOTES: story line numbering starts at 0, which will be a Title story card.
                Change_name supported only in the online version of the game.
                In the above examples the opponent's name is "Brian" and his initials are "BRI"
                The get_player API works for both.
        """
        action_type = action_card.action_type        # ActionType
        num_args = len(args)
        card_numbers = []
        story_cards = []
        
        message = f'{player.player_initials} Playing  {action_card.action_type}: {action_card.text}'
        min_args = action_card.min_arguments
        max_args = action_card.max_arguments

        self.log(message)
        #
        # check number of arguments is within range
        #
        if num_args < min_args or num_args > max_args:
            message = f"{action_card.action_type} requires from {min_args} to {max_args} additional card numbers."
            return self._log_error(message)

        return_code = CommandResult.SUCCESS
        done_flag = True
        match(action_type):
            case ActionType.DRAW_NEW:
                # Discard up to 4 cards and draw replacements
                message = ""
                for arg in args:
                    num = int(arg)
                    story_card = player.story_card_hand.get_card(num)
                    if story_card is None:
                        message = f"You are not holding a card with number {num}"
                        return self._log_error(message)
                        
                    player.remove_card(num)
                    draw_result:CommandResult = self.draw_for(player, "new")
                    message = f"{message}\n{draw_result.message}"
                    return_code = draw_result.return_code
                    if return_code != CommandResult.SUCCESS:
                        break
            
            case ActionType.MEANWHILE:    # requires an additional card to come after the "Meanwhile, "
                num = int(args[0])
                story_card = player.story_card_hand.get_card(num)
                if story_card is None:
                    message = f"You are not holding a card with number {num}"
                    return self._log_error(message)
                
                action_card_played = player.play_card(action_card)
                story_card_played = player.play_card(story_card)
                message = f"You played {action_card_played.number}. {action_card_played.text} and {story_card_played.number}. {story_card_played.text}"
                
            case ActionType.STEAL_LINES:
                # Steal a story card played by another player
                target_player_name = args[0]    # name or initials work
                line_number = int(args[1])    # a line# in an opponents story
                target_player:Player = self.get_player(target_player_name)
                if target_player is None:
                    message = f"No such player: {target_player_name}"
                    return self._log_error(message)
                story_cards = target_player.story_card_hand.my_story_cards
                if line_number >= story_cards.size():
                    message = f"Invalid line number: {line_number}"
                    return self._log_error(message)
                story_card = story_cards.get(line_number)
                #
                # put story_card in my hand and remove from the target_players hand
                #
                player.add_card(story_card)
                target_player.remove_card(story_card.number)
                
                message = f"You played {action_card.number}. {action_card.action_type.value}, stealing line {line_number} from {target_player.player_name} "
            
            case ActionType.TRADE_LINES:
                # Trade an Opening or Story element that has been played with that from another player's story
                message = f"{action_card.number}. {action_card.action_type.value} not available."
            
            case ActionType.REORDER_LINES:
                message = f"{action_card.number}. {action_card.action_type.value} not yet implemented."
            
            case ActionType.COMPOSE:
                text = " ".join(args)
                #
                # create a new StoryCard from the text provided, 
                # add it to the player's hand, then play that card
                #
                genre = self.stories_game.genre
                card_number = self.stories_game.story_card_deck.next_card_number
                story_card = StoryCard(genre, CardType.STORY, text, card_number)
                player.add_card(story_card)
                result = self.play(card_number)
                if result.return_code is CommandResult.SUCCESS:
                    self.stories_game.story_card_deck.next_card_number = card_number + 1
                message = f"You played {action_card.number}. {action_card.text} {result.message}"
                    
            case ActionType.STIR_POT:
                # Each player selects a story element from their deck and passes it to the person to their left
                # if the randomize_picks game parameter is set to True, the selection is done at random automatically
                # otherwise each player must run a pass_card <card_number> command.
                #
                message = f"{action_card.number}. {action_card.action_type.value} not yet implemented but soon."
                    
            case ActionType.CHANGE_NAME:
                # Change up to 2 character names on a selected story card (that has been played) to a different alias or pronoun
                # Example: given the following story line #3:
                # 3. Cheryl woke up in a cold sweat. She had been dreaming of her life with Don, but in each dream, she was watching her own funeral.
                # play 222 3 Cheryl/Alice Don/Travis    results in:
                # 3. Alice woke up in a cold sweat. She had been dreaming of her life with Travis, but in each dream, she was watching her own funeral.
                # requires 2 or 3 arguments: the story line number to change
                # up to 2 changes, each formatted as <before>/<after>
                #
                story_cards = player.story_card_hand.my_story_cards
                nlines = story_cards.size()
                nargs = len(args)
                story_card = None
                for i in range(nargs):
                    if i == 0:
                        story_line_number = int(args[0])    # starts at 0
                        if story_line_number > nlines-1:
                            message = f"Invalid story line number {story_line_number}"
                            return_code = CommandResult.ERROR
                            break
                        else:
                            continue
                    else:
                        names = args[i].split("/")
                        if len(names) != 2:
                            message = "Change name must have a before and after separated by a /"
                            return_code = CommandResult.ERROR
                            break
                        story_card = story_cards.get(story_line_number)
                        story_card.text = story_card.text.replace(names[0], names[1])
                        
                if return_code == CommandResult.SUCCESS:
                    action_card_played = player.play_card(action_card)
                    message = f"You played {action_card_played.number}. {action_card_played.text} on {story_card.number}. {story_card.text}"
            
        result = CommandResult(return_code, message, done_flag)
        return result
    
    def _log_error(self, message)->CommandResult:
        self.log(message)
        return CommandResult(CommandResult.ERROR, message, False)
    
        