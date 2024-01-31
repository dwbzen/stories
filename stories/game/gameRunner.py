'''
Created on Dec 8, 2023

@author: dwbze
'''

from game.storiesGame import StoriesGame
from game.commandResult import CommandResult
from game.player import Player
from game.storiesGameEngine import StoriesGameEngine
from game.gameConstants import GameParametersType

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
            stories_game - a StoriesGame instance. If not None, all previous parameters except debug_flag
              are set from stories_game
            
    """
    def __init__(self, installationId:str, genre:str, total_points:int, log_level:str, game_mode:str, aliases:List[str], stories_game:StoriesGame|None=None):
        """
        Constructor
        """
        self._installationId = installationId
        self._genre = genre
        self._total_points = total_points
        self._game_mode = game_mode 
        debug_flag = log_level == 'debug'
        self._debug = debug_flag           # traces the action by describing each step
        self._game_engine = None           # GameEngine instance
        self._stories_game = stories_game
        
        if stories_game is None:          # create a new StoriesGame
            self.game_engine = StoriesGameEngine(stories_game=None, game_id=None, loglevel=log_level, installationId=installationId)

            result = self.game_engine.create(self._installationId, genre, total_points, game_mode)
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
    def game_id(self) ->str:
        return self._game_id
    
    @property
    def genre(self)->str:
        return self._genre
    
    @property
    def total_points(self)->int:
        return self._total_points

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
                    prompt = f'player {pn}, {current_player.player_initials}, turn={turn_number}: '
                    cmd = input(prompt)
                    if len(cmd) == 0: continue
                    cmd_str = cmd.split(" ")
                    if cmd_str[0] in self._restricted_commands \
                      and self.game_mode != "test_prod" \
                      and self._careersGame.game_parameters_type is GameParametersType.PROD:
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
    
def main():
    parser = argparse.ArgumentParser(description="Run a command-driven Stories Game for 1 to 6 players")
    parser.add_argument("--nplayers", "-n", help="The number of players", type=int, choices=range(1,6), default=3)
    parser.add_argument("--names", help="Comma-separated list of player names. If set, this determines #of players and overrides --players")
    parser.add_argument("--points", help="Total game points", type=int, choices=range(10, 100), default=20)
    parser.add_argument("--params", help="Game parameters type: 'test', 'prod', or 'custom' ", type=str, \
                        choices=["test","prod","custom"], default="test")
    parser.add_argument("--gameid", help="Game ID", type=str, default=None)
    parser.add_argument("--loglevel", help="Set Python logging level", type=str, choices=["debug","info","warning","error","critical"], default="warning")
    parser.add_argument("--genre", help="Story genre", type=str, choices=["horror","romance","noir"], default="horror")
    parser.add_argument("--aliases", help="Comma-separate list of 4 character aliases. This overrides gameParameters settings")
    args = parser.parse_args()
    
    total_points = args.points

    installationId = 'DWBZen2022'  # uniquely identifies 'me' as the game creator
    careers_game = None
    gameId = args.gameid
    current_player = None
    player_names = args.names
    players = None
    player_initials = []
    
    game_mode = "prod" if args.params=="test_prod" else args.params
    game_runner = GameRunner(installationId, args.genre, total_points, args.loglevel, game_mode, args.aliases, stories_game=None)
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
        game_runner.execute_command(f"add player {player_name} {player_id} {initials} {email}")
        # 
        
    game_runner.execute_command("start", current_player)
    game_runner.run_game()

if __name__ == '__main__':
    main()
    