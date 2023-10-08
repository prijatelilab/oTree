"""
Contains baseline structure for the game.
"""

# Global imports
import random

# Local imports
from prijateli_tree.app.controllers.players import Player


class Game:
    def __init__(self, max_rounds, structure_type):
        self.players = []
        self.max_rounds = max_rounds
        self.current_round = 0
        self.network_structure = None
        # Bag compositions
        self.bags = {
            "red": ["red", "red", "red", "red", "blue", "blue"],
            "blue": ["blue", "blue", "blue", "blue", "red", "red"],
        }

    def decide_structure(self):
        """
        Returns a dictionary of player_id: [neighbor_ids] pairs.
        """
        pass

    def add_player(self, player):
        self.players.append(player)

    def setup_game(self):
        self.network_structure = self.decide_structure()
        self.bag = self.draw_bag()

    def draw_bag(self):
        """
        Randomly selects either a red or blue bag.
        """
        return random.choice(["red", "blue"])

    def distribute_balls(self):
        for player in self.players:
            ball = self.draw_ball_from_bag()
            player.observe(ball)  # Hypothetical method

    def draw_ball_from_bag(self):
        # Randomly draw a ball based on the bag's composition
        ball = random.choice(self.bags[self.bag])
        # Remove the drawn ball from the bag
        self.bags[self.bag].remove(ball)
        return ball

    def play_round(self):
        if self.current_round == 0:
            # First round logic: Players simply observe and make guesses
            for player in self.players:
                ball = self.draw_ball_from_bag()
                player.observe(ball)
                guess = player.make_guess()
                self.guesses[player.player_id] = guess
        else:
            # Players observe their ball and previous guesses of neighbors
            for player in self.players:
                ball = self.draw_ball_from_bag()
                player.observe(ball)
                neighbor_guesses = self.get_neighbor_guesses(player)
                player.observe_others_guesses(neighbor_guesses)
                updated_guess = (
                    player.update_guess()
                )  # Assuming players might change their guess
                self.guesses[player.player_id] = updated_guess

        self.current_round += 1

    def get_neighbor_guesses(self, player):
        """
        Returns a dictionary of player_id: guess pairs for the player's neighbors.
        """
        neighbor_guesses = {}
        for neighbor in self.network_structure[player.player_id]:
            neighbor_guesses[neighbor] = self.guesses[neighbor]
        return neighbor_guesses

    def play_game(self):
        self.setup_game()
        while self.current_round < self.max_rounds:
            self.play_round()
        self.end_game()

    def end_game(self):
        # Logic to inform players about the drawn bag and results
        pass
