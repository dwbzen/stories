'''
Created on Dec 8, 2023

@author: don_bacon
'''

from game.storiesGame import StoriesGame
from game.commandResult import CommandResult
from game.player import Player
from game.storiesGameEngine import StoriesGameEngine
from game.gameConstants import GameParametersType, PlayMode

from typing import List
import argparse, time
import logging


class GameRunner(object):
    """A command-line text version of Stories game play used for testing and simulating web server operation.
        Arguments:
            installationId - the installation ID to use
            genre - the story genre: horror, romance, noir
            total_points - total game points
            debug_flag - set to True for debugging output
            game_mode - 'test', 'prod', 'test-prod' or 'custom'
            play_mode - 'individual', 'team' or 'collaborative'
            source - 'mongo' or 'text'
            aliases - 
            stories_game - a StoriesGame instance. If not None, all previous parameters except debug_flag
              are set from stories_game
            
    """
    def __init__(self, installationId:str, genre:str, total_points:int, log_level:str, game_mode:str, \
                 play_mode:PlayMode, source:str, aliases:List[str], stories_game:StoriesGame|None=None):
        """
        Constructor
        """
        self._installationId = installationId
        self._genre = genre
        self._total_points = total_points
        self._game_mode = game_mode 
        self._source = source
        self._play_mode = play_mode
        self._log_level = log_level
        debug_flag = log_level == 'debug'
        self._debug = debug_flag           # traces the action by describing each step
        self._game_engine = None           # GameEngine instance
        self._stories_game = stories_game
        
        if stories_game is None:          # create a new StoriesGame
            self.game_engine = StoriesGameEngine(stories_game=None, game_id=None, loglevel=log_level, installationId=installationId)

            result = self.game_engine.create(self._installationId, genre, total_points, self._play_mode, self._source, game_mode)
            if result.return_code != CommandResult.SUCCESS:
                logging.error("Could not create a StoriesGame")
            
            self._stories_game = self.game_engine.stories_game
            self._game_id = self._stories_game.game_id
            pass
        else:   # restore an existing game
            raise ValueError(f"Sorry restore game is not implemented,")
        if aliases is not None:
            character_aliases = aliases.split(",")          # there should be 4 names
            self._stories_game.set_character_aliases(character_aliases)
    
        self._restricted_commands = ["set", "deal"]             # can not be played in production mode
        self._action_commands = ["draw", "play", "discard" ]    # increment turns for solo game
        
    @property
    def stories_game(self)->StoriesGame:
        return self._stories_game
    
    @stories_game.setter
    def stories_game(self, agame:StoriesGame):
        self._stories_game = agame
        
    @property
    def installationId(self)->str:
        return self._installationId
    
    @property
    def game_mode(self)->str:
        return self._game_mode
    
    @property
    def play_mode(self)->PlayMode:
        return self._play_mode

    @property
    def game_id(self) ->str:
        return self._game_id
    
    @property
    def genre(self)->str:
        return self._genre
    
    @property
    def total_points(self)->int:
        return self._total_points
    
    @property
    def log_level(self)->str:
        return self._log_level

    @property
    def debug(self)->bool:
        return self._debug

    def create_game(self, game_id=None, game_mode="test") -> CommandResult:
        result = self.game_engine.create(self.installationId, self.genre, self.total_points, game_id, game_mode)
        #self._storiesGame = self.game_engine.storiesGame
        return None

    def execute_command(self, cmd, aplayer:Player=None) -> CommandResult:
        """Command format is command name + optional arguments
            The command and arguments passed to the game engine for execution
            Arguments:
                cmd - the command string
                aplayer - a Player reference. If None, the engine executes the command as Administrator (admin) user.
            Returns:
                result - result dictionary (result, message, done)
        """
            
        result = self.game_engine.execute_command(cmd, aplayer)
        return result

    def run_game(self):
        """Run the main player input loop. Each player in turn is prompted
            for a command. The command is then executed and if no errors
            this is repeated for the next player.
            Play continues until a player issues an 'end' command.
        """
        game_over = False
        game_state = self._stories_game.game_state
        nplayers = game_state.number_of_players()
        while not game_over:
            for i in range(nplayers):
                # 
                current_player = game_state.current_player
                pn = current_player.number
                done = False
                while not done:
                    turn_number = game_state.turn_number
                    prompt = f'player: {pn}, {current_player.player_initials}, turn={turn_number}: '
                    cmd = input(prompt)
                    if len(cmd) == 0: continue
                    cmd_str = cmd.split(" ")
                    if cmd_str[0] in self._restricted_commands \
                      and self.game_mode != "test_prod" \
                      and self._stories_game.game_parameters_type is GameParametersType.PROD:
                        print( f"'{cmd_str[0]}' command not allowed in production mode")
                        continue
                    result = self.execute_command(cmd, current_player)
                    print(result.message)
                    done = result.done_flag
                    if result.return_code == CommandResult.TERMINATE:
                        game_over = True
                    if nplayers == 1 and cmd_str[0] in self._action_commands:
                        game_state.increment_turns()
                        
                if game_over:
                    break
                
    def run_script(self, filePath:str, delay:int, log_comments=True)->CommandResult:
        """Runs a script file.
            A script file has one legit command or a statement per line.
            Use "add player..." to add players to the game, for example
            "add player Don DWB dwb20230113 dwbzen@gmail.com 20 10 30" for a 60 point game
            By default players are human. To add computer player, include "computer" as the last argument.
            For example "add player ComputerPlayer_1 CP_1 cp120230516 dwbzen@gmail.com 20 20 20 computer"
            Lines that begin with "# " are comments and are written to the log file as-is.
            Statements have Python syntax and are used to check results, control looping.
            All statements end in a "{" (for loop init), "}" (end loop) or ";" to differentiate from game commands.
            The following statements are supported:
            assignment
               (variable) = (value)
            looping
               while (expression) {
                   (statements and/or commands):
            logical
               if (variable) == (value):
                   (commands)
               else:
                   (commands)
            statements ending with ";"  are evaluated with the Python exec() or eval() functions.
            assignments are evaluated with exec(), "counter=1"  ->  exec("counter=1")
            The while condition is evaluated with eval(), "while counter<limit" -> eval("counter<limit")
            other statements evaluated with exec(), "counter+=1"  ->  exec("counter+=1")
            The logic assumes the loop body will be evaluated at least once.
        """
        turn_number = 1
        game_state = self._stories_game.game_state
        self.game_engine.automatic_run = True
        current_player = None
        with open(filePath, "r") as fp:
            scriptText = fp.readlines()
            fp.close()
            line_number = 0
            script_lines = len(scriptText)
            loop_start = -1
            loop_end = 0
            continue_loop = False
        fp.close()
        #
        result = None
        while line_number < script_lines:
            line = scriptText[line_number]
            if len(line) > 0:
                cmd = line.strip("\t\n ")   # drop tabs, spaces and  \n
                if len(cmd) == 0:
                    line_number +=1
                    continue
                
                elif cmd.startswith("#"):    # comment line
                    if log_comments:
                        logging.info(f'log_message {cmd}')
                        result = None
                    else:
                        result = None
                        
                elif cmd.startswith("add player "):
                    result = self.execute_command(cmd, None)
                    
                elif cmd.endswith(";"):    # use exec()
                    statement = cmd[:-1]
                    try:
                        exec(statement)
                        result = CommandResult(CommandResult.SUCCESS, statement, False)
                    except Exception as ex:
                        message = f'"{statement}" : Invalid exec statement\nexception: {str(ex)}'
                        result = CommandResult(CommandResult.ERROR,  message,  False, exception=ex)
                        logging.error(message)
                        
                elif cmd.endswith("{"):   # a while loop, execute the condition with eval()
                    ind = cmd.find(" ")
                    if ind > 0:    # isolate the conditional: if, while
                        condition = cmd[:-1][ind+1:]    # assumes "while "
                        result = CommandResult(CommandResult.SUCCESS, condition, False)
                        try:
                            continue_loop = eval(condition)
                            if not continue_loop:
                                line_number = loop_end
                            else:
                                loop_start = line_number
                        except Exception as ex:
                            message = f'"{condition}" : Invalid eval statement\nexception: {str(ex)}'
                            result = CommandResult(CommandResult.ERROR,  message,  False, exception=ex)
                            logging.error(message)
                    else:
                        logging.warn(f"{cmd} is not a valid condition")
                        
                elif cmd.endswith("}"):    # end of the loop
                    loop_end = line_number
                    line_number = loop_start - 1   # back to the while, -1 because line_number incremented below
                    result = CommandResult(CommandResult.SUCCESS, cmd, False)
                    
                else:
                    current_player = game_state.current_player
                    result = self.execute_command(cmd, current_player)
                    turn_number += 1
                
                if result is not None:
                    if self.debug:
                        print(f'"{cmd}":\n {result.message}')
                    if result.return_code == CommandResult.TERMINATE:
                        break
                    
                line_number +=1
                time.sleep(delay)
        if result is None:
            result = CommandResult(CommandResult.SUCCESS, message="END OF SCRIPT")
        return result

    
def main():
    parser = argparse.ArgumentParser(description="Run a command-driven Stories Game for 1 to 6 players")
    parser.add_argument("--nplayers", "-n", help="The number of players", type=int, choices=range(0,6), default=3)
    parser.add_argument("--names", help="Comma-separated list of player names. If set, this determines #of players and overrides default players")
    parser.add_argument("--points", help="Total game points. This overrides gameParameters settings", type=int, choices=range(10, 100), default=20)
    parser.add_argument("--params", help="Game parameters type: 'test', 'prod', or 'custom' ", type=str, \
                        choices=["test","prod","custom"], default="test")
    parser.add_argument("--source", help="mongo or text", type=str, choices=['mongo','text'], default='mongo')
    
    parser.add_argument("--restore", "-r", help="Restore game by gameid", action="store_true", default=False)    # TODO - need --gameid for restore
    parser.add_argument("--gameid", help="Game ID", type=str, default=None)
    
    parser.add_argument("--script", help="Execute script file", type=str, default=None)
    parser.add_argument("--delay", help="Delay a specified number of seconds between script commands", type=int, default=0)
    parser.add_argument("--comments", "-c", help="Log comment lines when running a script", type=str, choices=['y','Y', 'n', 'N'], default='Y')
    
    parser.add_argument("--loglevel", help="Set Python logging level", type=str, choices=["debug","info","warning","error","critical"], default="warning")
    parser.add_argument("--genre", help="Story genre", type=str, choices=["horror","romance","noir"], default="horror")
    parser.add_argument("--aliases", help="Comma-separate list of 4 character aliases. This overrides gameParameters settings")
    parser.add_argument("--playmode", help="Play mode: individual, collaborative, team", choices=["individual", "collaborative", "team" ],  default="individual" )
      
    #
    # In a collaborative play mode, players build a common story
    # One player has the PlayerRole of DIRECTOR, the others have a PLAYER role
    # In team play mode,  One player has the PlayerRole of DIRECTOR, the others have a TEAM_MEMBER role
    args = parser.parse_args()
    
    total_points = args.points

    installationId = 'DWBZen2024'  # uniquely identifies 'me' as the game creator
    script_filePath = args.script         # complete file path
    log_comments = args.comments.lower()=='y'
    gameId = args.gameid
    current_player = None
    player_names = args.names
    players = None
    player_initials = []
    
    game_mode = "prod" if args.params=="test_prod" else args.params
    play_mode = PlayMode[args.playmode.upper()]
    game_runner = GameRunner(installationId, args.genre, total_points, args.loglevel, game_mode, play_mode, args.source, args.aliases, stories_game=None)
    
    if script_filePath is not None:
        result = game_runner.run_script(script_filePath, args.delay, log_comments=log_comments)
        if result.return_code == CommandResult.TERMINATE:
            return
        else:
            # continue on in command mode
            game_runner.run_game()
    
    #
    # create players
    #
    nplayers = args.nplayers
    if player_names is not None:
        players = player_names.split(",")
        nplayers = len(players)    # overrides --nplayers
        for p in players:
            p = f"{p.upper()}XX" if len(p) <3 else p.upper()
            player_initials.append(p[0:3])
            
    for i in range(nplayers):
        player_name = f"Player_{i+1}" if players is None else players[i]
        initials = f"PN{i+1}" if players is None else player_initials[i]
        email = f"{player_name}@gmail.com"
        player_id = player_name
        
        game_runner.execute_command(f"add player {player_name} {initials} {player_id} {email}")
        # 
        
    game_runner.execute_command("start game", current_player)
    game_runner.run_game()

if __name__ == '__main__':
    main()
    