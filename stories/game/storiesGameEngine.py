'''
Created on Dec 8, 2023

@author: don_bacon
'''

from game.storiesGame import StoriesGame
from game.commandResult import CommandResult
from game.player import  Player
from game.storyCard import StoryCard
from game.environment import Environment
from game.gameState import GameState
from game.logger import Logger
from game.gameUtils import GameUtils
from game.gameConstants import GenreType, GameConstants, CardType, ActionType
from game.gameEngineCommands import GameEngineCommands

from datetime import datetime
import random, json
from typing import List
import os, logging, sys
from threading import Lock


class StoriesGameEngine(object):
    """Stories game engine
    Valid commands and arguments. 
    BNF format: [optional argument]  ; comment "text"  (group argument options)
    Default arguments are shown first followed by alternatives separated by | to indicate "or"
    Valid commands defined in GameConstants
    
    Command :: <done> | <draw> | <discard> | <list> | <play> | <read>
        <draw> :: "draw"  ("new"|"discard")     ; draw a card from the main deck or the top card in the discard pile
        <list> :: "list" ("hand"|"story")  [player_initials] [<how>] 
            <how> :: "regular" | "numbered"
        <ls> :: "ls" ("hand"|"story")  [player_initials]     ; short for regular list
        <ln> :: "ln" ("hand"|"story")  [player_initials]     ; short for numbered list
        <done> :: "done" | "next"               ; done with my turn - next player's turn
        <end game> :: "end game"                ; saves the current game state then ends the game
        <pass> :: "pass" <card_number>          ; pass the designated card in a player's hand to the player on his/her left (the next player)
        <play> :: "play" <card_number[,card_number]>          ; play 1 story card, or comma-separated list consisting of a multi-card action card, and a story card.
        <discard> :: "discard" <card_number>    ; discard the selected card and place it on top of the game discard pile
        <read> :: "read" ["numbered"]           ; Display a player's story in a readable format. Card numbers are also displayed
                                                  if the optional "numbered" argument is included.
        <rn> ::                                 ; alias for "read numbered"
        <show> :: "show"                        ; show the top card in the discard pile
        
        <card_number> :: <integer> 
              
    Play sequence:
        draw 
        play or discard a card
        next
    """

    _lock = Lock()

    def __init__(self, stories_game:StoriesGame=None, game_id:str=None, loglevel='warning', installationId=""):
        """
        """
        self._stories_game = stories_game    # create a new StoriesGame with create()
        self._debug = False                  # traces the action by describing each step and logs to a file
        self._start_date_time = datetime.now()
        self._installationId = installationId      # provided by the UI or the GameRunner
        self._current_player = None
        self._admin_player = Player(number=-1, name='Administrator', player_id="admin00", initials='admin')
        
        self._game_state = None             # set with create()
        self._automatic_run = False         # set to True if running a script
        self._game_id = self._create_game_id(installationId) if game_id is None else game_id
        
        self._init_logging(loglevel, self._game_id)
        
    def _init_logging(self, loglevel:str, game_id):
        
        log_levels = {"debug":logging.DEBUG, "info":logging.INFO, "warning":logging.WARNING, "error":logging.ERROR, "critical":logging.CRITICAL}
        level = log_levels[loglevel]
        self._debug = (loglevel=='debug')
        
        self._logfile_filename = f'{game_id}_log'
        self._turn_history_filename = f'{game_id}_turnHistory'
        
        self._dataRoot = Environment.get_environment().package_base

        self._logfile_folder = os.path.join(self._dataRoot, 'log')
        self._gamefile_folder = os.path.join(self._dataRoot, 'games')
        
        self._logfile_path = os.path.join(self._logfile_folder, self._logfile_filename + ".log")
        self._turn_history_path = os.path.join(self._logfile_folder, self._turn_history_filename + ".json")
        
        self._game_filename_base = os.path.join(f'{self._gamefile_folder}', f'{game_id}_game')
        
        if(not os.path.exists(self._logfile_folder)):
            os.mkdir(self._logfile_folder)
        
        if(not os.path.exists(self._gamefile_folder)):
            os.mkdir(self._gamefile_folder)
        
        # configure the logger
        self._logger = Logger(self._game_id, self._logfile_path, level=level)
    
    def _create_game_id(self, installation_id) ->str :
        """Create a unique game id (guid) for this game.
            This method acquires a lock to insure uniqueness in a multi-process/web environment.
            Format is based on current date and time and installationId for example ZenAlien2013_20220908-140952-973406-27191
        """
        StoriesGameEngine._lock.acquire()
        gid = GameUtils.create_guid(installation_id)
        StoriesGameEngine._lock.release()
        return gid

    def log_info(self, *message):
        """Write info-level message to the log file and if debug is set, also to the console
        """
        txt = " ".join(message)
        if self._debug:
            print(txt)
        logging.info(txt)
            
    def log_message(self, *message) -> CommandResult:
        """The command version of log.
        """
        self.log_info(*message)
        return CommandResult(CommandResult.SUCCESS)
    
    def execute_command(self, command:str, aplayer:Player, args:list=[]) -> CommandResult:
        """Executes a command for a given Player.
            This also updates Turn.commands.
            Arguments:
                command - the command name, for example "roll".
                args - a possibly empty list of additional string arguments
                player - a Player reference. If None, admin_player is used.
            Returns: a CommandResult object. See game.CommandResult for details
        
        """
        player = aplayer
        if aplayer is None:
            player = self._admin_player
            
        commands = command.split(';')
        messages = ""
        for command in commands:
            logging.debug(f'{player.player_initials}: {command}')
            if command is None or len(command) == 0:
                return CommandResult(CommandResult.SUCCESS)
            cmd_result = self._evaluate(command, args)
            player.add_command(command)    # adds to player's command history
            
            if command.lower() != "log_message":      # no need to log twice
                logging.debug(f'  {player.player_initials} results: {cmd_result.return_code} {cmd_result.message}')
            messages += cmd_result.message + "\n"
        
        cmd_result.message = messages
        return cmd_result

    def _evaluate(self, commandTxt, args=[]) -> CommandResult:
        """Evaulates a command string with eval()
            Arguments:
                commandTxt - the command name + any arguments to evaluate.
                args - an optional list of additional arguments
            Returns - a CommandResult
        """
        command_result = GameEngineCommands.parse_command_string(commandTxt, args)
        if command_result.return_code != CommandResult.SUCCESS:     # must be an error
            return command_result
        
        command = "self." + command_result.message
        command_result = None
        logging.debug("_evaluate: " + command)
        try:
            command_result = eval(command)
        except Exception as ex:
            message = f'"{command}" : Invalid command format or syntax\n exception: {str(ex)}'
            command_result = CommandResult(CommandResult.ERROR,  message=message,  done_flag=False, exception=ex)
            logging.error(message)
            print(message, file=sys.stderr)
        return command_result
        
    def game_status(self) -> CommandResult:
        """Get information about the current game in progress and return in JSON format
        """
        message =  self.game_state.to_JSON()
        # TODO
        return CommandResult(CommandResult.SUCCESS, message=message)
    
    @property
    def stories_game(self)->StoriesGame:
        return self._stories_game
    
    @property
    def debug(self)->bool:
        return self._debug
    
    @debug.setter
    def debug(self, value:bool):
        self._debug = value
    
    @property
    def installationId(self)->str:
        return self._installationId
    
    @property
    def game_id(self)->str:
        return self._game_id
    
    def create(self, installationId:str, genre:str, total_points:int, game_parameters_type="test") -> CommandResult:
        """Create a new StoriesGame for a given genre.
            Initialize GameEngineCommands
        """
        self._installationId = installationId
        self._stories_game = StoriesGame(installationId, genre, total_points, self._game_id, game_parameters_type)
        self._game_state = self._stories_game.game_state
        self._game_state.game_id = self._game_id
        
        # initialize GameEngineCommands
        self._gameEngineCommands = GameEngineCommands(self._stories_game)
        self._gameEngineCommands.debug = self._debug
        
        message = f'{{"game_id":"{self._game_id}", "installationId":"{installationId}"}}'
        self.log_info(message)    # INFO
        return CommandResult(CommandResult.SUCCESS, message=message)
    
    
    #####################################
    #
    # Game engine action implementations
    #
    #####################################

    def add(self, what, player_name, initials=None, player_id=None, email=None) -> CommandResult:
        """Add a new player to the Game. Other 'adds' TBD
    
        """
        return self._gameEngineCommands.add(what, player_name, initials, player_id, email)

    def start(self) -> CommandResult:
        message = f'Starting game {self.game_id}'

        self.log_info(message)
        self._game_state.set_next_player()    # sets the player number to 0 and the curent_player Player reference
        self._game_state.started = True
        self._stories_game.start_game()       # sets the start datetime
                
        return CommandResult(CommandResult.SUCCESS, message, True)
    
    def end(self) ->CommandResult:
        """Ends the game, saves the current state if specified, and exits.
        """
        self.log_info("Ending game: " + self.game_id)
        self._stories_game.end_game()
        result = CommandResult(CommandResult.TERMINATE, "Game is complete" , True)
        #
        # TODO - determine the winner, save the game if specified
        #
        return result
    
    def done(self)-> CommandResult:
        """End the current player's turn and go to the next player.
        """
        return self._gameEngineCommands.done()
    
    def next(self) -> CommandResult:
        """Synonym for done - go to the next player
        """
        return self.done()
    
    def draw(self, what:str="new") ->CommandResult:
        """Draw a card from the deck OR from the top of the global discard deck
        """
        return self._gameEngineCommands.draw(what)
    
    def discard(self, card_number:int):
        """Discard cards as indicated by their card_number from a player's hand.
        """
        return self._gameEngineCommands.discard(card_number)
    
    def play(self, card_number:int, cards:str=None) ->CommandResult:
        """Play 1 or 2 cards: 1 story card, or 1 multi-card action card and a story card
        """
        return self._gameEngineCommands.play(card_number, cards)
    
    def pass_card(self, card_number:int)->CommandResult:
        """Pass a card in the current player's hand to the hand of the next player (to the left).
            Arguments:
                card_number - the number of the card to pass. It must exist in the current player's hand
            This command does nothing in a solo game.
        """
        return self._gameEngineCommands.pass_card(card_number)

    def list(self, what='hand', initials:str='me', how='numbered') ->CommandResult:
        """List the Experience or Gateway cards held by the current player
            Arguments: 
                what - "hand" or "story"
                initials - optional player initials
                how - "regular" or "numbered"
            Returns: CommandResult.message is the stringified list of str(card).
            
        """
        return self._gameEngineCommands.list(what, initials, how)
    
    def ls(self, what='hand', initials:str='me', how='regular') ->CommandResult:
        """Alias for list
        """
        return self.list(what, initials, how)
    
    def list_numbered(self)->CommandResult:
        """Alias for 'list hand me numbered'
        """
        return self.list(how="numbered")
    
    def ln(self, what='hand', initials:str='me', how='numbered')->CommandResult:
        """Alias for 'list hand me numbered'
        """
        return self.list(what, initials, how)
    
    def show(self, what="discard")->CommandResult:
        """Displays the top card of the discard pile OR story elements
            Returns: CommandResult.message is the str(card)
        """
        return self._gameEngineCommands.show(what)
        
    def read(self, numbered:bool=False, initials:str=None)->CommandResult:
        """Display a player's story in a readable format.
        """
        return self._gameEngineCommands.read(numbered, initials)
    
    def rn(self, initials:str=None)->CommandResult:
        return self.read(True, initials)

    def status(self, initials:str=None)->CommandResult:
        return self._gameEngineCommands.status(initials)
    

        