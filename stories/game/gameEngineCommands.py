'''
Created on Dec 22, 2023

@author: don_bacon
'''

from game.gameConstants import GameConstants, ActionType, CardType, CardTypeEncoder
from game.gameConstants import PlayMode, PlayerRole, ParameterType, Direction
from game.storiesGame import StoriesGame
from game.commandResult import CommandResult
from game.gameState import GameState
from game.player import Player
from game.team import Team
from game.storyCard import StoryCard
from game.storyCardList import StoryCardList

from typing import List
import logging, json, re
from game.gameParameters import GameParameters
from game.gameUtils import GameUtils

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
        self._play_mode = self._stories_game.play_mode
        self._game_parameters = self._stories_game.game_parameters
    
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
    def play_mode(self)->PlayMode:
        return self._play_mode
    
    @property
    def game_parameters(self)->GameParameters:
        return self._game_parameters
        
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
        if command.lower() == "update":    # special treatment for keyword arguments
            # update requires 3 arguments: what (for example 'player'), target (for example 'dwb')
            # and keyword arguments (Dict), for example role='team_lead',name='Donnie'
            # 
            if len(command_args) != 4:   # 'update' + 3 args
                return CommandResult(CommandResult.ERROR,  message=f'Invalid update command: "{command_args}"',  done_flag=False)
            command = f"update('{command_args[1]}','{command_args[2]}',{command_args[3]})"
        else:
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
                if p.player_initials.lower() == lc_pid or p.login_id  == lc_pid or p.player_name.lower() == lc_pid:
                    player = p
                    break
        return player
    
    def _get_player_for_play_mode(self, player)->CommandResult:
        """Gets the Director or Team lead of a given player.
            If successful, the player instance is returned in the command result properties: 
                player = result.properties["target_player"] 
        """

        if self.play_mode is PlayMode.COLLABORATIVE:
            result = self._get_director()
            result.properties["target_player"]  = result.properties["director"]

        elif self.play_mode is PlayMode.TEAM:
            team_name = player.my_team_name
            result = self._get_team_lead(team_name)
            result.properties["target_player"]  = result.properties["team_lead"]

        else:    # PlayMode.INDIVIDUAL
            result = CommandResult(CommandResult.SUCCESS, message=None, properties={"target_player":player})
                
        return result
 
    def _get_card_in_story(self, player:Player, card_id:str|int)->dict:
        """Gets the designated card number from a player's current story (StoryCardHand.my_story_cards)
            Arguments:
                player - the current player.
                card_id - a card number or ordinal in the form #n where n is a valid line in the player's story.
            Returns: a dict with the keys "storyCard" (the StoryCard instance) and "index" (the index of that card in my_story_cards)
            
            In a collaborative game, the game's Director holds the story.
            In a team game, the player's team lead holds the story.
        """
        storyCard = None
        story_cards = self._get_story_cards(player)    # returns the appropriate StoryCardList, depending on the game mode & player
        if isinstance(card_id, int):
            storyCard = story_cards.find_card(card_id)    # will be None if card number not in the list
            index = story_cards.index_of(card_id)
        else:    # card_id is the ordinal from the listing, 1 through #cards
            index = int(card_id[1:])
            storyCard = story_cards.get(index)   # will be None if index is not valid

        return {"storyCard" : storyCard, "index" : index}
    
    def _get_card(self, player:Player, card_id:str|int) ->StoryCard:
        """Get a specific StoryCard from a player's hand.
            Arguments:
                player - the current Player 
                card_id - one of: a card number, 
                          a card number or ordinal in the form #n where n is a valid line in the player's hand,
                          or the word "last" to get the last card drawn.
        """
        if isinstance(card_id, str):
            if card_id == "last" and player.story_card_hand.last_card_drawn_number >= 0:
                card_number = player.story_card_hand.last_card_drawn_number
            elif card_id.startswith("#"):    # card_id is the ordinal from the listing, 1 through #cards
                ordinal = int(card_id[1:])
                card_number = self._get_card_number_from_list(player, ordinal)
                if card_number < 0:
                    message = f"Invalid line number: {ordinal}"
                    result = CommandResult(CommandResult.ERROR, message, False)
                    return result
            else:
                card_number = int(card_id)
                
        else:    # card_id is an int
            card_number = card_id
            
        story_card = player.story_card_hand.get_card(card_number)
        return story_card
    
    def check_errors(self)->bool:
        """Return True if checking for player errors.
            Bypassing error checks is useful for testing.
            The value is set in the gameParameters JSON file as "bypass_error_checks".
            This simply returns the negative of that value.
            @see GameParameters
        """
        return not self.game_parameters.bypass_error_checks
    
    #####################################
    #
    # Game engine command functions
    #
    #####################################

    def add(self, what, player_name, initials, login_id, email, role_name) -> CommandResult:
        """Add a new player or team to the Game.
            Note - team semantics TBD
        """
        if what == 'player':
            player_role = PlayerRole.PLAYER if role_name is None else PlayerRole[role_name.upper()]
            player = Player(name=player_name, login_id=login_id, initials=initials, email=email, game_id=None, player_role=player_role)
            self._stories_game.add_player(player)        # adds to GameState which also sets the player number
            message = player.to_JSON()
            self.log(message)
            result = CommandResult(CommandResult.SUCCESS, message=message)
        elif what == 'team':    # really should use add_team command
            name = player_name  # in this context, this is the team name
            args = initials     # in this context, this is a comma-seperated list of initials
            result = self.add_team(name, args)
        elif what == 'director':
            # find the player with the given initials and
            # update the role to PlayerRole.DIRECTOR
            #
            player = self.get_player(initials)
            if player is None:
                result = CommandResult(CommandResult.ERROR, message=f"No player with initials {initials} is in this game. Please 'add player' first")
            else:
                player.player_role = PlayerRole.DIRECTOR
                result =  CommandResult(CommandResult.SUCCESS, message=f"Player {initials} is now the Director")
        else:
            message = f"Cannot add {what} here."
            result = CommandResult(CommandResult.ERROR, message=message, done_flag=False)
            
        return result

    def add_team(self, name, args:str) ->CommandResult:
        """Add players to a new or existing team
            Arguments:
                name - the team name, can be new or existing team
                args - a comma-separated list of player initials
            Note that the first player listed is assigned the TEAM_LEAD role.
            This can be changed with the 'update player' command (which is TBD)
        """
        if self.game_state.get_team(name) is None:
            players = []
            plist = args.split(',')
            result = self._get_players(plist)
            return_code = result.return_code
            if return_code == CommandResult.SUCCESS:
                message = f"Players added to team {name} {result.message} "
                team = Team(name)
                players = result.properties["members"]
                for i in range(len(players)):
                    # default the first player in the list as TEAM_LEAD
                    player_role = PlayerRole.TEAM_LEAD if i==0 else PlayerRole.PLAYER
                    team.add_member(players[i], player_role)
                    players[i].my_team_name = name
                self.game_state.add_team(team)
            else:    # some players don't exist
                message = result.message
        else:
            message=f"team: '{name}' already exists"
            return_code = CommandResult.WARNING
        
        return CommandResult(return_code, message=message)
    
    def _get_players(self, pids:List[str]) ->CommandResult:
        """Returns a List[Player] given a list of player initials.
            If SUCCESS, the player list is the result property "members"
            Otherwise the message has the player ids not found.
        """
        players = []
        message = ""
        return_code = CommandResult.SUCCESS
        for pid in pids:    # player initials
            player = self.game_state.get_player_by_initials(pid)
            if player is not None:
                players.append(player)
                message = f"{message} {pid} "
            else:
                return_code = CommandResult.ERROR
                message = f"{message} No such player: {pid} "
        result = CommandResult(return_code, message)
        result.properties = {"members":players}
        return result

    def update(self, what:str, target:str, **kwargs)->CommandResult:
        """Update select properties of a Player, Team, or StoriesGame
            Arguments:
                what - the object to update: player, team, game
                target - the target player (initials), team (team name), game_id or 'this'
                kwargs - keyword arguments (dict) for the specified object
            
            target == 'player', supported Player properties are role, player_name, player_role, and player_email
                      Example: update player dwb player_role='team_lead',player_email='foo@gmail.com'
            target == 'team', supported Team property is name
                      Example: update team Team_XXX name='Team_USA'
            target == 'game', the target is 'this' in reference to the current game, or a valid game_id
                      Supported properties are total_points and game_id. Examples:
                        update game DWBZen2022_20240723_110800_032649_78393 game_id='DWBZen2024_20240723'
                        update game this total_points='30'
            
            When changing a player's role from PLAYER to either TEAM_LEAD or DIRECTOR,
            if there is already a player with that role, their new role will be PLAYER.
            Changing a team name will also change the team name of players in that team.
            
            TODO finish the implementation
            
        """
        self.log(f"update: what: {what}, target: {target}, kwargs: {kwargs} {type(kwargs)}")
        return CommandResult(CommandResult.SUCCESS, message=f"what: {what}, target: {target}, kwargs: {kwargs}")

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
        current_player = self.game_state.current_player

        check_errors = self.check_errors()   # check for errors?
        max_cards = self.game_parameters.max_cards_in_hand
        result = current_player.end_turn(check_errors, max_cards)
        if result.return_code is CommandResult.SUCCESS:
            npn = self.game_state.set_next_player()
            next_player = self.game_state.current_player
            result.message = f"{result.message}. {next_player.player_initials}'s turn, player# {npn}."
            result.properties = {"playerId" : next_player.player_initials}
        else:
            pass

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
            
            TODO - update for team and collaborative play modes
            TODO - score round points based on story ranking (who came in first, second & third)
        """
        game_points = self.game_parameters.game_points
        story_length = self.game_parameters.story_length
        bypass_error_checks = self.game_parameters.bypass_error_checks
        return_code = CommandResult.SUCCESS
        message = ""
        winner:Player = None
        
        #
        # Try to end the current round first, then if what is "game" also end the entire game.
        # In both cases points are tallied and winner(s) are determined.
        # is ending the round valid? check the number of story cards for each player
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
                message = f"{message} Player: {player.player_initials} has not played necessary story elements: {pm}\n "
                return_code = CommandResult.ERROR
                    
        if return_code is CommandResult.SUCCESS:
            message = f"The {what} is over!"
            if self.play_mode is not PlayMode.COLLABORATIVE:
                message = f"{message} and the winner with {winner.points} points is {winner.player_initials}"
            if what == "game":
                self.stories_game.end(what=what)
                enddate = GameUtils.get_datetime()
                message = f"{message} {enddate}"
                return_code = CommandResult.TERMINATE

        result = CommandResult(return_code, message, True)
        self.log(message)
        return result

    def find(self, card_type:str, action_type:str=None)->CommandResult:
        """Find a specific CardType in a player's hand.
            Arguments:
                card_type - a CardType.value - title,story,opening,closing, or action.
                action_type - an optional ActionType.value - meanwhile, trade_lines, etc.
            If the given card_type is found the card number (of the first instance found) is returned in
            the ComandResult properties with the key "number". If not found the card number returned is -1.
            If used in a script, the syntax is: num=find story
            and used in a conditional, for example: if num>0:
        """
        result = CommandResult()
        player:Player = self.game_state.current_player 
        result = self._get_player_for_play_mode(player)    # the Player maintaining the story
        target_player:Player = result.properties["target_player"]
        ct = CardType[card_type.upper()]
        at = ActionType[action_type.upper()] if action_type is not None else None
        index = target_player.story_card_hand.cards.find_first(ct, at)
        if index >= 0:
            the_card = target_player.story_card_hand.cards[index]
            result.properties = {"number":the_card.number}
            message = f"Found card# {the_card.number} for type {card_type}"
            if action_type is not None:
                message = f"{message}, action type: {action_type}"
            result.message = message
        else:
            result.properties = {"number":-1}
            result.message = f"No card of type {card_type} was found"
        return result
        
    
    def _check_types_to_omit(self)->List[CardType]:
        """Check if all players have played a TITLE and/or OPENING story card.
            Return: List[CardType] that have been played by all players
            
            NOTE - due to rules change and additional ActionCard type, this is no longer needed.
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
        
    def draw(self, what:str, action_type:ActionType, initials=None) ->CommandResult:
        """Draw a card from the deck OR from the top of the global discard deck
                what - what to draw or where to draw from:
                       new - draw a card from the main card deck
                       discard - draw the top of the global discard deck
                       <type> - any of: "title", "opening", "opening/story", "story", "closing", "action"
                action_type - if what == "action", the ActionType to draw: "meanwhile", "trade_lines", "steal_lines",
                        "stir_pot", "draw_new", "change_name"
                initials - optional player id (initials or id)
            Returns:
                CommandResult with return_code set to SUCCESS or ERROR (if there are no cards left to draw from),
                    and message set to an error message OR if SUCCESS, the card_type drawn.
            Specifying the card and action_type are for testing purposes only.        
            Note game_state.types_to_omit is a List[CardType] to omit drawing. This is set globally
            for example when all players have played a Title card, a Title card will no longer be drawn.
        """
        player = self.game_state.current_player if initials is None else self.get_player(initials)
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
            Returns:
                CommandResult with properties "number" and "text" which have the StoryCard.number and .text respectively.
            The last_card_drawn_number in the player's story_card_hand is also updated with the new card's number.
            @see StoriesGame.draw_card() 
        """
        card,message = self.stories_game.draw_card(what, action_type)
        if card is None:    # must be an error, message has the error message
            result = CommandResult(CommandResult.ERROR, message, done_flag=False)
        else:
            if player is None:
                result = CommandResult(CommandResult.ERROR, "Player not found")
            else:
                # add this drawn card to the player hand
                player._story_card_hand.add_card(card)
                player.card_drawn = True
                message = f"{ordinal}. {player.player_initials} drew a {card.card_type.value} ({card.number}): {card.text}"
                result = CommandResult(CommandResult.SUCCESS, message, properties={"number": str(card.number), "text": str(card)}  )
            
        return result

    def discard(self, card_number:int, initials:str|None)->CommandResult:
        """Discard card as indicated by card_number from a player's hand
            and adds to the game discard deck.
        """
        player = self.game_state.current_player if initials is None else self.get_player(initials)
        card_discarded = player.discard(card_number)
        if card_discarded is None:
            message = f"You are not holding a card with number {card_number}"
            result = CommandResult(CommandResult.ERROR, message, False)
            
        else:
            message = f"You are discarding card# {card_number}. {card_discarded.text}"
            self.stories_game.add_to_discard(card_discarded)
            result = CommandResult(CommandResult.SUCCESS, message, True)
        return result
    
    def play(self, card_id:int|str, *args) ->CommandResult:
        """Play a story/action card from a player's hand OR the discard deck
            Arguments:
                card_id - the StoryCard to play, or the string "last"
                    to play the most recent card drawn.
                args - additional arguments for ACTION cards, depending on the ActionType of the card played.
            
            Returns:
                CommandResult - If the CommandResult return_code is SUCCESS, the StoryCard instance is returned
                                in the result properties with key "story_card_played"
                    
            Examples: play 110        ; play a single story card
                      play 200 110    ; play a MEANWHILE ActionCard (#200), adding "Meanwhile" to story card 110
                      
            Use the command "help action <action card type>" for more information  (TODO)
            about a specific action card. For example, "help action change_name"
            
            The story card text is added to the end of the story for card types of "Opening/Story" and "Story"
            For "Title", "Opening" and "Closing" if there is an existing story card of that type
            in the player's story, it is replaced with the new one, otherwise it's added to the end.
            
            TODO: If the story already has a Closing, playing a "Story" or "Opening/Story" will
            insert that story element before the Closing.
            
            In a collaborative game all the players maintain their own hand,
            but the player with the DIRECTOR PlayerRole maintains the common story.
            In a team game, the TEAM_LEAD of each team maintains the story common to the team.
            
            If the CommandResult is successful, the StoryCard instance is returned
            in the result properties with key "story_card_played"
            
            Notes - When inserting a TITLE, OPENING or CLOSING story element, the existing one (if it exists) is replaced.
            In a collaborative PlayMode, if the automated_draw configuration parameter is True,
            then after the card is played a new card is drawn automatically.
            
        """
        player = self.game_state.current_player
        self.log(f"play: player initials: {player.player_initials}, play_mode: {self.play_mode.value} ")
        if isinstance(card_id, str):
            if card_id == "last" and player.story_card_hand.last_card_drawn_number >= 0:
                card_number = player.story_card_hand.last_card_drawn_number
            elif card_id.startswith("#"):    # card_id is the ordinal from the listing, 1 through #cards
                ordinal = int(card_id[1:])
                card_number = self._get_card_number_from_list(player, ordinal)
                if card_number < 0:
                    message = f"Invalid line number: {ordinal}"
                    result = CommandResult(CommandResult.ERROR, message, False)
                    return result
            else:
                card_number = int(card_id)
                
        else:    # card_id is an int
            card_number = card_id
            
        story_card = player.story_card_hand.get_card(card_number)
        if story_card is None:
                message = f"Invalid card number: {card_number}"
                result = CommandResult(CommandResult.ERROR, message, False)
        
        elif story_card.card_type is CardType.ACTION:
            # this could result in playing 2 StoryCards depending in the ActionType
            result = self.execute_action_card(player, story_card, args)
            # remove the card just played from the player's hand
            player.story_card_hand.remove_card(story_card.number)
            
        else:
            if self._play_mode is PlayMode.COLLABORATIVE:
                #
                # find the player with the DIRECTOR role (which could be the current player) and play the card as that player
                #
                result = self._get_director()
                if result.is_successful():
                    director:Player = result.properties["director"]
                    player.remove_card(card_number)
                    director.add_card(story_card)
                    self.log(f"play. director: {director.player_initials} player: {player.player_initials}")
                    result = self._play_card(director, story_card, as_player=player)
                else:
                    result.message = f"{result.message}\nA Director is required for collaborative games. Please add one."
                    
            elif self._play_mode is PlayMode.TEAM:
                team_name = player.my_team_name
                result = self._get_team_lead(team_name)
                if result.is_successful():
                    team_lead:Player = result.properties["team_lead"]
                    player.remove_card(card_number)
                    team_lead.add_card(story_card)
                    result = self._play_card(team_lead, story_card, as_player=player)
                else:
                    result.message = f"{result.message}\nA team lead is required for team games. Please add one to team '{team_name}'"         
            else:
                result = self._play_card(player, story_card)
                
        if result.is_successful():
            result.properties = {"story_card_played":story_card}
            if self.stories_game.game_parameters.automatic_draw:    # and self.play_mode is PlayMode.COLLABORATIVE:
                num_cards = self.stories_game.game_parameters.max_cards_in_hand - player.story_card_hand.hand_size()
                if num_cards > 0:
                    for i in range(num_cards):
                        draw_result = self.draw(what="new", action_type=None)
                        result.message = f"{result.message} {draw_result.message}"
            
        return result
    
    def play_type(self, card_type:str, *args):
        """Draws a card of a given type and plays it. Primary use of play_type is in scripting and testing.
            Arguments:
                card_type - a valid CardType
                args - additional arguments needed for Action cards, depending on the ActionType
            
            Note that this works for story element types only, NOT action cards.
            For action cards, first draw the action type you want,
            for example "draw action meanwhile", then use "play last" to play the card.
            
            TODO - enable playing action cards
        """
        result = self.draw(card_type, action_type=None)
        if result.is_successful():
            card_number = result.properties["number"]
            play_result = self.play(card_number)
            result.message = f"{result.message}\n{play_result.message}"
        return result
    
    def _play_card(self, player:Player, story_card:StoryCard, as_player:Player=None)->CommandResult:
        """Plays a StoryCard for a given Player.
            Arguments:
                player - the Player playing this card
                story_card - A StoryCard that has a card type not CardType.ACTION
                as_player - in a Collaborative or Team game, the player actually playing the card instead of the Director/Team Lead.
            Returns:
                CommandResult indicating SUCCESS or ERROR
                
            Note - When inserting a TITLE, OPENING or CLOSING story element, the existing one (if it exists) is replaced.
            Adding a TITLE inserts it as the first line if not replacing an existing title.
            
        """
        card_played = player.play_card(story_card)
        if card_played is None:
            message = f"Invalid card {story_card.number}"
            result = CommandResult(CommandResult.ERROR, message, False)
        else:
            if as_player is not None:
                message = f"{as_player.player_initials} played card# {card_played.number}. {card_played.text}"
            else:
                message = f"{player.player_initials} played card# {card_played.number}. {card_played.text}"
            result = CommandResult(CommandResult.SUCCESS, message, True)
            result.properties = {"story_card_played" : card_played}
        return result
    
    def _get_director(self)->CommandResult:
        """Finds and returns the game director.
            Returns: a CommandResult indicating SUCCESS or ERROR.
                If return_code is CommandResult.SUCCESS, the director Player instance
                is in the result properties with the key "director"
        """
        director:Player = None
        if self._play_mode is PlayMode.COLLABORATIVE:
            #
            # find the player with the DIRECTOR role (which could be the current player) and play the card as that player
            #
            # self.game_state
            directors = self.game_state.get_players_by_role(PlayerRole.DIRECTOR)
            if len(directors) != 1:     # There is not a DIRECTOR in the game or there are more than one
                result = CommandResult(CommandResult.ERROR, "No director was found", False)
            else:
                director = directors[0]     # there can only be 1 director
                result = CommandResult(CommandResult.SUCCESS, "", properties={"director":director})
        else:
            result = CommandResult(CommandResult.ERROR, "No director in a non-Collaborative game", False)
            
        return result
    
    def _get_team_lead(self, team_name:str)->CommandResult:
        """Finds and returns the team lead for a given team
            Arguments:
                team_name - the name of an existing team
            Returns: a CommandResult indicating SUCCESS or ERROR.
                If return_code is CommandResult.SUCCESS, the TEAM_LEAD Player instance
                is in the result properties with the key "team_lead"
        """
        team_lead:Player = None
        if self._play_mode is PlayMode.TEAM:
            #
            # find the player with the DIRECTOR role (which could be the current player) and play the card as that player
            #
            # self.game_state
            team_leads = self.game_state.get_team_players_by_role(team_name, PlayerRole.TEAM_LEAD)
            if len(team_leads) != 1:     # There is not a TEAM_LEAD for this team or there are more than one
                result = CommandResult(CommandResult.ERROR, f"No team lead for '{team_name}' was found", False)    
            else:
                team_lead = team_leads[0]
                result = CommandResult(CommandResult.SUCCESS, "", properties={"team_lead":team_lead})
        else:
            result = CommandResult(CommandResult.ERROR, "No team leads in a non-Team game", False)
        
        return result
    

    def _get_story_cards(self, player:Player)->StoryCardList:
        target_player = player
        story_cards = []
        if self._play_mode is PlayMode.TEAM:
            team_name = player.my_team_name
            result = self._get_team_lead(team_name)
            if result.return_code == CommandResult.SUCCESS:
                target_player = result.properties["team_lead"]
                story_cards = target_player.story_card_hand.my_story_cards
            else:
                self._log_error(result.message)
                
        elif self._play_mode is PlayMode.COLLABORATIVE:
            result = self._get_director()
            if result.return_code == CommandResult.SUCCESS:
                target_player = result.properties["director"]
                story_cards = target_player.story_card_hand.my_story_cards
            else:
                self._log_error(result.message)
        else:    # PlayMode.INDIVIDUAL
            story_cards = target_player.story_card_hand.my_story_cards
        return story_cards
        
                    
    def insert(self, line_number:int, card_number:int, how="after" )->CommandResult:
        """Insert a story card into your current story.
            Arguments:
                line_number - the line# in your current story to insert the new card
                card_number - the number of a story card in your hand
                how - insert "before" or "after" (the default) the given line_number
            Returns:
                CommandResult.ERROR if the card_number or line_number is invalid (doesn't exist)
                else CommandResult.SUCCESS
            TODO - implement how='before', currently all inserts done after (the default) a given line_number
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
            message = f"You played {card_played.number}. {card_played.text} {how} line# {line_number}"
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
    
    def pass_card(self, card_number:int, direction:Direction,  initials:str|None=None)->CommandResult:
        """Pass a card in the designated player's hand to (the hand of) another player as indicated by direction.
            Arguments:
                card_number - the number of the card to pass. It must exist in the current player's hand
                direction - Direction.RIGHT, LEFT or ANY  to pick a random direction.
                initials - the initials of the player doing the passing. Defaults to None indicating the current player.
            This command does nothing in a solo game.
        """
        player = self.game_state.current_player if initials is None else self.get_player(initials)
        if direction is Direction.LEFT:
            npn = self._game_state.get_next_player_number(player)
        elif direction is Direction.RIGHT:
            npn = self._game_state.get_previous_player_number(player)
        else:    # random direction
            roll = GameUtils.roll(1)   # returns 1-element List[int] random 1 though 6
            npn = self._game_state.get_next_player_number(player) if roll[0] <=3 else self._game_state.get_previous_player_number(player)
        
        if player.number == npn:    # nothing to do
            return CommandResult(CommandResult.SUCCESS, "No other players to pass to!", True)
            
        story_card = player.remove_card(card_number)
        if story_card is None:
                message = f"Invalid card number {card_number}"
                return CommandResult(CommandResult.ERROR, message, False)
            
        next_player:Player = self.game_state.players[npn]
        next_player.add_card(story_card)
        return CommandResult(CommandResult.SUCCESS, f"Card #{card_number} removed from {player.player_initials}'s hand and given to {next_player.player_initials}")

    def list(self, what='hand', initials:str='me', how='numbered', display_format='text') ->CommandResult:
        """List the cards held by the current player
            Arguments: what - 'hand', 'story'
                initials - a player's initials, defaults to the current player "me"
                how - 'numbered' for a numbered list, 'regular', the default, for no numbering
                display_format - 'text' or 'json'
                
            Returns: CommandResult.message. If display_format == 'text', this is the stringified list of str(card) in the player's hand or story
            If 'json', the message contains the to_JSON with no indent.
            By default when what=="hand", the lines are sorted by CardType: ACTION, TITLE, OPENING, OPENING_STORY, STORY, CLOSING, and number
            
        """
        # TODO
        player = self.game_state.current_player if initials=="me" else self.get_player(initials)
        return_code = CommandResult.SUCCESS
        if what == 'hand':
            message = self._list(player.story_card_hand, how, sort_list=True, display_format=display_format)
        elif what == 'story':
            result = self.read(how, initials, display_format)
            return result
        else:
            message = f"I don't understand what '{what}' is"
            return_code = CommandResult.ERROR
        
        return CommandResult(return_code, message)
    
    def _list(self, story_card_hand, how:str, sort_list=False, display_format='text') ->str:
        """List the cards in a player's StoryCardHand
           Arguments:
               story_card_hand - a player's StoryCardHand
               how - "numbered" to number the entries (1 through #cards)
               sort_list - if True the list will be sorted by CardType.
               display_format - 'text' or 'json'
            Returns: the list as a string
            The card with the number == last_card_drawn_number is highlighted with an "*"
            @see StoryCardHand.sort()
        """
        last_drawn = story_card_hand.last_card_drawn_number
        if sort_list:
            cards = story_card_hand.sort()    # StoryCardList
        else:
            cards = story_card_hand.cards.cards
        if how=="numbered":
            n = 1
            if display_format == 'text':
                card_text = ""
                for card in cards:
                    tag = "*" if card.number == last_drawn else ""
                    card_text = card_text + f"{tag}{n}. {str(card)}"
                    n += 1
            elif display_format == 'json':
                card_text = GameEngineCommands.to_JSON(cards, last_drawn, numbered=True)
            else:
                card_text = f"I don't understand what '{display_format}' is"
                
        else:    # not numbered
            if display_format == 'text':
                card_text = str(story_card_hand.cards)
            elif display_format == 'json':
                card_text = GameEngineCommands.to_JSON(cards, last_drawn, numbered=False)
            else:
                card_text = f"I don't understand what '{display_format}' is"           
            
        return card_text
    
    @staticmethod
    def to_JSON(cards:List[StoryCard], last_drawn:int, numbered:bool=True):
        cards_list = []
        n = 1
        for story_card in cards:
            tag = "*" if story_card.number == last_drawn else " "
            card_text = f"{tag}{n}. {story_card.card_type.value}: {story_card.number}. {story_card.text}"
            cards_list.append(card_text.strip())
            n += 1
        cards_dict = {"cards" : cards_list}
        message = json.dumps(cards_dict)
        return message
    
    def _get_card_number_from_list(self, player, ordinal, sort_list=True):
        """Returns the number of the card in the players hand at a given ordinal position (starting with 1)
            Returns -1 if ordinal is out of range
        """
        cards = player.story_card_hand.sort() if sort_list else player.story_card_hand.cards.cards    # List[StoryCard]
        ind = ordinal - 1
        card_number = -1
        if ind < len(cards):
            card_number = cards[ind].number 
        return card_number

    def set(self, player:Player, parameter_type:ParameterType, val:str|int)->CommandResult:
        """Set a game configuration parameter. 
        Arguments: 
            player - the Player using this command. Already authorized.
            what - the parameter to set. The following game parameters are supported:
                bypass_error_checks - boolean 0 or 1 
                story_length - int >= 4
                max_cards_in_hand - range(5, 16)
                automatic_draw - boolean 0 or 1
                character_alias - dict. Keys must be in ["Michael", "Nick", "Samantha", "Vivian" ]
             val - the value to set, subject to the above conditions. 
            
        In a collaborative or team game, only the director or a team lead may execute the set command
        """
        result = CommandResult()
        ptype = parameter_type.value
        match(parameter_type):
            case ParameterType.AUTOMATIC_DRAW:
                # val needs to be 0 or 1
                if isinstance(val, int):
                    bval = (val == 1)
                    self.game_parameters.automatic_draw = bval
                    result.message = f"{ptype} set to {bval}"
                else:
                    result.return_code = CommandResult.ERROR
                    result.message = f"Invalid set value {val} for {ptype}"
            case ParameterType.BYPASS_ERROR_CHECKS:
                if isinstance(val, int):
                    bval = (val == 1)
                    self.game_parameters.bypass_error_checks = bval
                    result.message = f"{ptype} set to {bval}"
                else:
                    result.return_code = CommandResult.ERROR
                    result.message = f"Invalid set value {val} for {ptype}"
    
        return result

    def set_player_property(self, player:Player, val:str)->CommandResult:
        """
            Arguments:
                player - the Player using this command. Already authorized.
                val - the set string in the form  [ <player_initials> | <player_number> ].<property>=value or
    
        """
        return CommandResult(CommandResult.SUCCESS, "TODO")
    
    def show(self, what)->CommandResult:
        """Displays 
            Arguments:
                what - what to display: 
                       discard - top card of the discard pile) 
                       all 
                or a story element class: "Title", "Opening", "Opening/Story", "Story", "Closing", "Action"
            Returns: CommandResult.message is the str(card) for discard, a numbered list of str for story element classes.
        """
        message = ""
        show_what = what.lower()
        return_code = CommandResult.SUCCESS
        if show_what=="discard":
            card,message = self.stories_game.get_discard()
            return_code = CommandResult.SUCCESS if card is not None else CommandResult.ERROR
            
        elif show_what=="all":    # show story cards by card_type
            n = 1
            for card_type in ["Action", "Title", "Opening", "Opening/Story", "Story", "Closing"]:
                cards = self.stories_game.get_story_cards_by_type(card_type)
                for card in cards:
                    message = f"{message}{n}. {card}"
                    n += 1
        
        elif show_what=="deck":    # show all cards in the deck in the order they appear in the deck
            n = 1
            cards = self.stories_game.get_cards()
            for card in cards:
                message = f"{message}{n}. {card}"
                n += 1
            
        elif show_what.startswith("param"):
            message = str(self.game_parameters)
            
        elif show_what.startswith("json"):    # full command is jsonparameters
            message = self.game_parameters.to_JSON()
                
        else:    # display all the elements of a given story class
            return_code = CommandResult.SUCCESS
            card_type = what.title()     # just in case
            cards = self.stories_game.get_cards_by_type(card_type)    # what must be a valid card_type.value
            if len(cards) > 0:   # List[str]
                n = 1
                for card in cards:
                    message = f"{message}{n}.  {card}"
                    n += 1
        result = CommandResult(return_code, message)
        
        return result
        
    def read(self, numbered:bool, initials:str=None, display_format='text', indent=0)->CommandResult:
        """Display a player's story in a readable format.
            Arguments:
                numbered - if True number the lines starting at 1 with the first story card.
                        The Title and Closing line(s) are not numbered.
                initials - the player's initials if other than the current player
                display_format - "text", "json" or "dict"
                
            In a COLLABORATIVE game mode the Director maintains the common story.
            In TEAM Play, the player's team lead maintains the story for the team.
        """
        player = self.game_state.current_player if initials is None else self.get_player(initials)
        self.log(f"read: player initials: {player.player_initials}, play_mode: {self._play_mode.value} ")
        return_code = CommandResult.SUCCESS
        if self._play_mode is PlayMode.COLLABORATIVE:
            result = self._get_director()
            if result.is_successful():
                player = result.properties["director"]
                self.log(f"director: {player.player_initials}")
                message = player.story_card_hand.my_story_cards.to_string(numbered)
            else:
                message = result.message
                return_code = CommandResult.ERROR
            
        elif self._play_mode is PlayMode.TEAM:
            team_name = player.my_team_name
            result = self._get_team_lead(team_name)
            if result.is_successful():
                player = result.properties["team_lead"]
                message = player.story_card_hand.my_story_cards.to_string(numbered)
            else:
                message = f"{result.message}\nA team lead is required for team games. Please add one to team '{team_name}'"   
                return_code = CommandResult.WARNING
        
        props = player.story_card_hand.my_story_cards.to_dict(how="full")    # key is "cards" 
        if display_format == "text":
            message = player.story_card_hand.my_story_cards.to_string(numbered)
        elif display_format == "json" or display_format == "dict":
            message = player.story_card_hand.my_story_cards.to_JSON(indent=indent)

        return CommandResult(return_code, message, properties=props)
    
    def publish(self, numbered:bool=True, initials:str=None, display_format='dict')->CommandResult:
        """Publish a story to MongoDB, associated with this gameID and player_initials.
            The story does not need to be completed in order to be published.
            Only one story for this game/player can be published.
            Any subsequent publish commands overwrites the existing one.
            Arguments:
                numbered - if True number the lines starting at 1 with the first story card.
                           The Title and Closing line(s) are not numbered.
                           Default is True
                initials - the player's initials if other than the current player
                display_format - "text", "json" or "dict"  Default value is "dict"
            Note that the default output format is a dictionary as the story is persisted to MongoDB.
            The "re_read" command converts and displays in "read" format.
        """
        result = self._get_director()
        if result.is_successful():    # in a COLABORATIVE game, publish as the game's Director
            player = result.properties["director"]
        else:
            player = self.game_state.current_player if initials is None else self.get_player(initials)
        player_id = player.player_initials
        game_id = self.stories_game.game_id
        result =  self.read(numbered, initials=player_id, display_format=display_format, indent=2)
        if result.return_code == CommandResult.SUCCESS:
            story = result.properties
            story["game_id"] = game_id
            story["initials"] = player_id
            self.stories_game.data_manager.add_game_story(game_id, player_id, story)
            
        return result

    def re_read(self, game_id, initials:str=None)->CommandResult:        
        player = self.game_state.current_player if initials is None else self.get_player(initials)
        player_id = player.player_initials
        result = self.stories_game.data_manager.get_game_story(game_id, player_id)
        if result.is_successful():
            gs = result.properties["game_story"]    # Dict
            # need to reformat the json to a readable story
            # and return that in result.message
            cards = gs["cards"]
            message = ""
            for card in cards:
                message = f'{message}{card["text"]}'    # assume each line terminated with a newline
            result.message = message
        return result

    def save_game(self, gamefile_base_name:str, game_id:str, how='json', source='mongo') -> CommandResult:
        """Save the complete serialized game state so it can be restarted at a later time.
            Arguments:
                how - serialization format to use: 'json', 'jsonpickle' or 'pkl' (pickle)
            NOTE that the game state is automatically saved in pkl format after each player's turn.
            NOTE saving in JSON format saves only the GameState; pkl and jsonpickle persist StoriesGame
        """
        extension = 'pkl' if how=='pkl' else 'json'
        filename = f'{gamefile_base_name}.{extension}'      # folder/filename
        result = CommandResult()
        if how=="json":
            result.message = "save game (JSON) not yet implemented - but soon!"
        elif how=='pkl':
            result.message = "save game (pkl) not yet implemented - but soon!"
        else:
            result.message = f"Unknown format {how}"
            result.return_code = CommandResult.ERROR
        return result
        
    
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
    
    def team_info(self, team_name='all')->CommandResult:
        """Displays info for a given team or all teams
            Arguments:
                team_name - an existing team name or 'all' (the default)
            Returns: a CommandResult, the message contains the team info
        """
        result = CommandResult()
        
        
        return result
        
        
    def log_message(self, message):
        """Logs a given message to the log file and console if debug flag is set
        """
        self.log(message)

    def execute_action_card(self,  player:Player, action_card:StoryCard, args) -> CommandResult:
        """Executes a StoryCard that has an ActionType
            Arguments:
                player - a Player instance
                action_card - a StoryCard with card_type CardType.ACTION
                args - a single card number OR a space-separated list of additional card numbers or strings
                      of #n where n is the line number of a story, for example when using "meanwhile".
                      This can be used in place of the card number.
                
            Examples of Action cards:
                meanwhile: play 249 110           ; card #249 is the meanwhile ActionCard, 110 is a story card
                           play 249 #3            ; card #249 is the meanwhile ActionCard. Place the "meanwhile" before line #3 of the story.
                
                draw_new:  play 250 100 119 143   ; card #250 is the draw_new ActionCard, the cards to replace with new ones are 110,119,143
                
                trade_lines:  play 251 BRI  1 2        ; card #251 is the trade_lines Action Card, 
                                                         1 is the line 1 story card in an opponent's (BRI) story (so visible to all) 
                                                         2 is the line 2 story card in my story

                steal_lines:  play 252 Brian 4    ; card #252 is a steal_lines ActionCard. Steal line#4 from Brian's  story and place it in my hand
                
                stir_pot: play 266          ; card #266 is a stir_pot ActionCard. 
                                              Each player selects a card from their hand and passes it to the person to their left, 
                                              OR selection and direction (left/right) is done automatically.
                                              Players use the 'pass <card_number>' command if not automatic.
                                              
                change_name: play 272 3 He/Brian        ; card #272 is a change_name ActionCard, 3 is line 3 in my current story.
                                                          change instances of "Brian" in that card to "He"
                                                          The change is case-sensitive and changes whole words only.
                                                        
                compose: play 273  She knew it was a mistake!    ; card #273 is a COMPOSE ActionCard. 
                                                                   The StoryCard text is "She knew it was a mistake!"
                
                call_in_favors:  play 274   ; card #274 is a CALL_IN_FAVORS ActionCard.
                                              Every player must then pass a Gateway card (randomly selected)
                                              to the player who played the action card.
                                                                   
                NOTES: story line numbering starts at 0, which will be a Title story card.
                Change_name supported only in the online version of the game.
                In the above examples the player's name is "Brian" and his initials are "BRI"
                In COLLABORATIVE and TEAM play mode, relevant actions are 
                played against the director's and team lead's story respectively.
                
                TODO - implement REORDER_LINES, CALL_IN_FAVORS
                TODO - test STEAL_LINES, TRADE_LINES  for individual, team and collaborative play
        """
        action_type = action_card.action_type        # ActionType
        num_args = len(args)
        
        message = f'{player.player_initials} Playing  {action_card.action_type}: {action_card.text}'
        min_args = action_card.min_arguments
        max_args = action_card.max_arguments

        self.log(message)
        #
        # check number of arguments is within range
        #
        if num_args < min_args or num_args > max_args:
            message = f"{action_card.action_type} requires from {min_args} to {max_args} additional card numbers. You specified {num_args}"
            return self._log_error(message)

        return_code = CommandResult.SUCCESS
       
        if action_type is ActionType.DRAW_NEW:
            # Discard up to 4 cards and draw replacements
            message = ""
            for arg in args:
                num = int(arg)   # self._get_card(player, arg)
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
            
        elif action_type is ActionType.MEANWHILE:    
            # requires an additional card to come after the "Meanwhile," or a line number in the current story
            # In the following examples, card #187 is the Action card MEANWHILE,
            #  #3 is the line number in the current story maintained by the player, team lead, or director depending on the play mode
            #  92 is a StoryCard
            # play 187  #3  - Insert a "Meanwhile" before line 3
            # play 187  92  - Add a "Meanwhile" to the end of the story, the play card #92
            # NOTE that both cards, 187 and 92, must be in the player's hand (the player executing the play)
            #
            card_id = args[0]
            insert_mode = isinstance(card_id, str) and card_id.startswith("#")      # insert the "Meanwhile..." before a given line
            
            result = self._get_player_for_play_mode(player)    # the Player maintaining the story (current player, Director or Team Lead)
            target_player = result.properties["target_player"]
            if not target_player._story_card_hand.cards.card_exists(action_card.number):
                #
                # add the Meanwhile StoryCard to the target_player's hand
                #
                player.remove_card(action_card.number)
                target_player.add_card(action_card)
            
            if insert_mode:
                index = int(card_id[1:])
                action_card_played = target_player.play_card(action_card, insert_after_line=index-1)
                message = f"You played {action_card_played.number}. {action_card_played.text}" if action_card_played is not None \
                          else f"Line number {index} is invalid"
            else:
                story_card = self._get_card(player, card_id)
                action_card_played = target_player.play_card(action_card)
                play_result:CommandResult = self._play_card(target_player, story_card, as_player=player)
                if play_result.is_successful():
                    story_card_played = play_result.properties["story_card_played"]
                    message = f"You played {action_card_played.number}. {action_card_played.text} and {story_card_played.number}. {story_card_played.text}"
                else:
                    message = play_result.message
                    return_code = play_result.return_code
            
        elif action_type is ActionType.COMPOSE:
            text = " ".join(args) + "\n"

            #
            # create a new StoryCard from the text provided, 
            # add it to the player's hand, then play that card
            # For teams, the card is added to the player's team lead
            # In a collaborative game, the card is added to the game Director's hand
            #
            result = self._get_player_for_play_mode(player)    # the Player maintaining the story
            target_player = result.properties["target_player"]
            if not target_player._story_card_hand.cards.card_exists(action_card.number):
                #
                # add the COMPOSE action card to the target_player's hand
                #
                player.remove_card(action_card.number)
                target_player.add_card(action_card)
            
            action_card_played = target_player.play_card(action_card)
            # create a new StoryCard for the bespoke text
            genre = self.stories_game.genre
            card_number = self.stories_game.story_card_deck.next_card_number
            story_card = StoryCard(genre, CardType.STORY, text, card_number)
            
            player.add_card(story_card)
            result = self.play(card_number)
            if result.return_code is CommandResult.SUCCESS:
                self.stories_game.story_card_deck.next_card_number = card_number + 1
            message = f"You played {action_card.number}. {action_card.text} {result.message}"
                
        elif action_type is ActionType.STEAL_LINES:
            # Steal a story card played by another player
            # Note that this action card doesn't make sense in a collaborative game
            # In a team game, you can only steal lines from members of another team
            if self.play_mode is PlayMode.COLLABORATIVE:
                message = "Steal lines not available in collaborative play mode."
                return self._log_error(message)
            
            target_player_name = args[0]    # name or initials work
            line_number = int(args[1])    # a line# in an opponents story
            target_player:Player = self.get_player(target_player_name)
            if target_player is None:
                message = f"No such player: {target_player_name}"
                return self._log_error(message)
            
            if self.play_mode is PlayMode.TEAM:
                # target player needs to be in a different team than the player executing this command
                if target_player.my_team_name == player.my_team_name:
                    message = "target player must be in a different team than you."
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
            
        elif action_type is ActionType.TRADE_LINES:
            # Trade an Opening or Story element that has been played with that from another player's story
            # Note that this action card doesn't make sense in a collaborative game
            # In a team game, you can only steal lines from members of another team
            target_player_name = args[0]    # name or initials work
            target_line_number = int(args[1])      # a line# in an opponents story
            my_line_number = int(args[2])          # a line# in my story
            target_player:Player = self.get_player(target_player_name)
            if target_player is None:
                message = f"No such player: {target_player_name}"
                return self._log_error(message)
            target_story_cards = target_player.story_card_hand.my_story_cards
            if target_line_number >= target_story_cards.size():
                message = f"Invalid line number: {target_line_number}"
                return self._log_error(message)
            target_story_card = target_story_cards.get(target_line_number)    # my opponent's StoryCard
            my_story_cards = player.story_card_hand.my_story_cards
            if my_line_number >= my_story_cards.size():
                message = f"Invalid line number: {my_line_number}"
                return self._log_error(message)
            my_story_card = my_story_cards.get(my_line_number)
            #
            # swap the lines:
            # put target_story_card in my story at line my_line_number
            # an my_story_card in target_story_cards at target_line_number
            #
            message = f"{action_card.number}. {action_card.action_type.value} not available."
            
        elif action_type is ActionType.REORDER_LINES:
            message = f"{action_card.number}. {action_card.action_type.value} not yet implemented."
            return_code = CommandResult.WARNING
            
        elif action_type is ActionType.CALL_IN_FAVORS:
            # Select one card at random from all other players. 
            # In team play, select a random card from each player in other teams. Not valid in a collaborative game.
            message = f"{action_card.number}. {action_card.action_type.value} not yet implemented."
            return_code = CommandResult.WARNING
                    
        elif action_type is ActionType.STIR_POT:
            # Each player selects a story element from their deck and passes it to the person to their left
            # if the randomize_picks game parameter is set to True, the selection is done at random automatically
            # otherwise each player must run a pass_card <card_number> command.
            #
            # NOTE that enforcement of this interactive mode is not currently enforced.
            if self.game_parameters.automatic_draw:
                message = ""
                for player in self.game_state.players:
                    card = player.story_card_hand.cards.pick_any()
                    result:CommandResult = self.pass_card(card.number, Direction.LEFT, initials=player.player_initials)
                    if not result.is_successful():
                        return result
                    else:
                        message = f"{message}\n{result.message}"
            else:
                message = f"{action_card.action_type.value} interactive mode not enforced. Each player must pass_card <card_number> left."
                return_code = CommandResult.WARNING
                    
        elif action_type is ActionType.CHANGE_NAME:
            # Change up to 2 character names on a selected story card (that has been played) to a different alias or pronoun
            # Example: given the following story line #3:
            # 3. Cheryl woke up in a cold sweat. She had been dreaming of her life with Don, but in each dream, she was watching her own funeral.
            # play 222 3 Cheryl/Alice Don/Travis    results in:
            # 3. Alice woke up in a cold sweat. She had been dreaming of her life with Travis, but in each dream, she was watching her own funeral.
            # requires 2 or 3 arguments: the story line number to change
            # up to 2 changes, each formatted as <before>/<after>
            # Note that this is case-sensitive and affects whole words only
            
            story_cards = self._get_story_cards(player)
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
                        message = "Change name must have a before and after separated by a '/'"
                        return_code = CommandResult.ERROR
                        break
                    
                    story_card = story_cards.get(story_line_number)
                    regstr = f"\\b{names[0]}\\b|^{names[0]}"
                    regx = re.compile(regstr, re.IGNORECASE)
                    m = regx.subn(names[1], story_card.text)
                    
                    story_card.text = m[0]
                    
            if return_code == CommandResult.SUCCESS:
                action_card_played = player.play_card(action_card)
                message = f"You played {action_card_played.number}. {action_card_played.text} on {story_card.number}. {story_card.text}"
            
        result = CommandResult(return_code, message)
        return result
    
    def _log_error(self, message)->CommandResult:
        self.log(message)
        return CommandResult(CommandResult.ERROR, message, False)
    
        