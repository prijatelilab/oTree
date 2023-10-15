"""
Contains baseline structure for all three game types.
"""
from prijateli_tree.app.models.database import Game
from prijateli_tree.app.utils.constants import (
    NETWORK_TYPE_INTEGRATED,
    NETWORK_TYPE_SEGREGATED,
    NETWORK_TYPE_SELF_SELECTED,
)
from prijateli_tree.app.utils.database import DatabaseHandler


def integrated_game(game: Game, player_id: int):
    # Fetch a game and player from the database with their
    # respective neighbors

    database = DatabaseHandler()

    # Create integrated network game
    game = Game(NETWORK_TYPE_INTEGRATED)
    game_id = 1
    user_id = 1
    game_type_id = 1
    num_rounds = 5
    practice = False

    # Create game in database
    database.create_game(game_id, user_id, game_type_id, num_rounds, practice)

    # Add player to game table in database
    player_id = 1
    user_id = 1
    game_id = 1
    position = 1
    name_hidden = False

    database.add_player_to_game(player_id, game_id, user_id, position, name_hidden)

    # game = database.fetch_game_by_id(game_id)
    # player = database.fetch_player_by_id(player_id)
    # neighbors = database.fetch_neighbors_for_player_in_game(game_id, player_id)

    #   if game.current_round == 0:
    #       This updates the Neighbor Relationships table
    #       network = create_integrated_network(game_id, game.players)
    #       bag = game.draw_bag()
    #       distribute_balls_to_players(game_id, bag)

    #       # Fetch the ball for the player for this round
    #       player_ball = database.fetch_ball_for_player_in_round(game_id, player_id,
    #                                                             game.current_round)

    #       # Players make their initial guess based on their ball alone
    #       player_initial_guess = player.make_initial_guess(player_ball)
    #       # Update player's guess in PlayerRounds table
    #       database.update_player_guess_for_round(game_id, player_id, game.current_round,
    #                                                player_initial_guess)

    # else:

    #     Fetch the ball for the player for this round
    #     player_ball = database.fetch_ball_for_player_in_round(game_id, player_id, game.current_round)

    #     # Players make their guess based on their ball and the guesses of their neighbors  # noqa: E501
    #     # Fetch neighbors' previous round guesses
    #     neighbor_guesses = database.fetch_guesses_for_neighbors_in_round(game_id,
    #                                                                      neighbors,
    #                                                                      game.current_round - 1)

    #     player_updated_guess = player.update_guess(player_ball, neighbor_guesses)

    #     # Update player's guess in PlayerRounds table
    #     database.update_player_guess_for_round(game_id, player_id, game.current_round,
    #                                            player_updated_guess)

    # # If the game is ending, calculate scores
    # if game.is_ending():
    #     points_won = game.calculate_points(player)
    #     database.update_score(player_id, points_won)

    # # Update any other changes to the game or player in the database
    # database.update_game(game)
    # database.update_player(player)

    return {"game_id": game.id, "player_id": player_id}


def segregated_game(game: Game, player_id: int):
    return {"game_id": game.id, "player_id": player_id}


def self_selected_game(game: Game, player_id: int):
    return {"game_id": game.id, "player_id": player_id}
