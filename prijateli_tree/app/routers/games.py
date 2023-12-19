import glob
import json
import logging
from http import HTTPStatus
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from prijateli_tree.app.database import (
    Game,
    GameAnswer,
    GamePlayer,
    GameSession,
    GameSessionPlayer,
    get_db,
)

from prijateli_tree.app.utils.constants import (
    DENIR_FACTOR,
    FILE_MODE_READ,
    STANDARD_ENCODING,
    WINNING_SCORE,
)

from prijateli_tree.app.utils.games import (
    did_player_win,
    get_bag_color,
    get_current_round,
    get_game_and_player,
    get_lang_from_player_id,
    get_previous_answers,
    get_session_player_from_player,
    raise_exception_if_none,
)


logger = logging.getLogger()
router = APIRouter()

base_dir = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(Path(base_dir, "../templates")))

languages = {}
for lang in glob.glob("prijateli_tree/app/languages/*.json"):
    with open(lang, FILE_MODE_READ, encoding=STANDARD_ENCODING) as file:
        languages.update(json.load(file))
logger.debug("Language files imported.")


###############################
#
#        BEGIN API
#
###############################


@router.get(
    "/{game_id}/player/{player_id}/start_of_game", response_class=HTMLResponse
)
def start_of_game(
    request: Request,
    game_id: int,
    player_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """
    Function that returns the start of game page and
    template.
    """
    template_text = languages[get_lang_from_player_id(player_id, db)]

    result = {
        "request": request,
        "player_id": player_id,
        "game_id": game_id,
        "points": WINNING_SCORE,
        "text": template_text,
    }

    return templates.TemplateResponse("start_of_game.html", result)


@router.get("/{game_id}/player/{player_id}/round")
def view_round(
    request: Request,
    game_id: int,
    player_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """
    Function that returns the current round
    """
    game, player = get_game_and_player(game_id, player_id, db)

    template_text = languages[player.language.abbr]
    current_round = get_current_round(game_id, db)
    template_data = {
        "practice_game": game.practice,
        "first_round": current_round == 1,
        "current_round": current_round,
        "text": template_text,
        "player_id": player_id,
        "game_id": game_id,
    }
    # Get current round
    if current_round == 1:
        template_data["ball"] = player.initial_ball
    elif current_round > game.rounds:
        redirect_url = request.url_for(
            "end_of_game", game_id=game_id, player_id=player_id
        )
        return RedirectResponse(url=redirect_url, status_code=HTTPStatus.FOUND)
    else:
        template_data["previous_answers"] = get_previous_answers(
            game_id, player_id, db
        )

    return templates.TemplateResponse(
        "round.html", {"request": request, **template_data}
    )


@router.post("/{game_id}/player/{player_id}/answer")
def route_add_answer(
    request: Request,
    game_id: int,
    player_id: int,
    player_answer: str = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """
    Function that updates the player's guess in the database
    """
    game = db.query(Game).filter_by(id=game_id).one_or_none()
    raise_exception_if_none(game, detail="game not found")

    current_round = get_current_round(game_id, db)

    if (
        not db.query(GameAnswer)
        .filter_by(game_player_id=player_id, round=current_round)
        .one_or_none()
    ):
        # Getting correct answer and current round
        correct_answer = get_bag_color(game.game_type.bag)

        # Record the answer
        new_answer = GameAnswer(
            game_player_id=player_id,
            player_answer=player_answer,
            correct_answer=correct_answer,
            round=current_round,
        )

        db.add(new_answer)
        db.commit()
        db.refresh(new_answer)

    redirect_url = request.url_for(
        "waiting", game_id=game_id, player_id=player_id
    )

    return RedirectResponse(url=redirect_url, status_code=HTTPStatus.SEE_OTHER)


@router.get("/{game_id}/all_set", response_class=JSONResponse)
def all_set(
    game_id: int,
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Determines if all players have submitted a guess in the current round
    """
    players = db.query(GamePlayer).filter_by(game_id=game_id).all()
    n_answers = 0
    for player in players:
        if player.answers:
            this_round = max([a.round for a in player.answers])
            n_answers += this_round

    ready = n_answers % len(players) == 0
    game_over = player.game.rounds == this_round
    return JSONResponse(content={"ready": ready, "game_over": game_over})


@router.get(
    "/{game_id}/player/{player_id}/waiting", response_class=HTMLResponse
)
def waiting(
    request: Request,
    game_id: int,
    player_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """
    Wait screen shows until all players are ready to move to the next section
    """
    template_text = languages[get_lang_from_player_id(player_id, db)]

    result = {
        "request": request,
        "game_id": game_id,
        "player_id": player_id,
        "text": template_text,
    }

    return templates.TemplateResponse("waiting.html", result)



@router.put(
    "/{game_id}/player/{player_id}/update_score", response_class=JSONResponse
)
def update_score(
    game_id: int,
    player_id: int,
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Function that updates the player's score in the database
    """
    game, player = get_game_and_player(game_id, player_id, db)
    if not player.completed_game:
        player.completed_game = True
        if not game.practice:
            session_player = get_session_player_from_player(player, db)
            game_status = did_player_win(game, player_id, db)
            session_player.correct_answers += game_status["is_correct"]
            session_player.points += game_status["is_correct"] * WINNING_SCORE
        db.commit()
        db.refresh(player)

    return JSONResponse(content={"status": "success"})


@router.get("/survey/{player_id}", response_class=HTMLResponse)
def get_qualtrics(
    request: Request,
    player_id: int,
    db: Session = Depends(get_db),
) -> Response:
    return templates.TemplateResponse("qualtrics.html", {"request": request})


@router.get("/survey/{player_id}")
def get_qualtrics(
    request: Request,
    player_id: int,
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse("qualtrics.html", {"request": request})


@router.get("/current_score/{player_id}", response_class=JSONResponse)
def route_get_score(
    request: Request,
    player_id: int,
    db: Session = Depends(get_db),
) -> JSONResponse:
    session_player_id = (
        db.query(GamePlayer).filter_by(id=player_id).one().session_player_id
    )

    session_player = (
        db.query(GameSessionPlayer)
        .filter_by(id=session_player_id)
        .one_or_none()
    )
    if session_player is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="GameSessionPlayer not found",
        )
    return JSONResponse(content={"points": session_player.points})


@router.get(
    "/{game_id}/player/{player_id}/end_of_game", response_class=HTMLResponse
)
def end_of_game(
    request: Request,
    game_id: int,
    player_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """
    Function that returns the end of game page and
    template.
    """

    game, player = get_game_and_player(game_id, player_id, db)
    game_status = did_player_win(game, player_id, db)

    points = 0
    if game_status["is_correct"]:
        points = WINNING_SCORE

    template_text = languages[player.language.abbr]

    result = {
        "request": request,
        "player_id": player_id,
        "game_id": game_id,
        "points": points,
        "text": template_text,
        "practice_game": game.practice,
    }

    # add information about winning and ball colors
    result.update(game_status)

    return templates.TemplateResponse("end_of_game.html", result)


@router.get("/{game_id}/player/{player_id}/next_game")
def go_to_next_game(
    request: Request,
    game_id: int,
    player_id: int,
    db: Session = Depends(get_db),
):
    """
    Moves player to first round of next game or ends the session
    """
    game, player = get_game_and_player(game_id, player_id, db)

    if game.next_game_id is None:
        # TODO: end of session screen
        return JSONResponse(content={"to be continued": "end of round"})


    next_player_id = (
        db.query(GamePlayer)
        .filter_by(user_id=player.user_id, game_id=game.next_game_id)
        .one()
        .id
    )

    raise_exception_if_none(next_player_id, detail="next player not found")

    # Check if this game is practice
    if game.practice:
        # Check if next game is practice
        next_game = db.query(Game).filter_by(id=game.next_game_id).one()
        # If next game is NOT practice
        if not next_game.practice:
            # Show end of practice screen
            redirect_url = request.url_for(
                "real_game_transition",
                game_id=next_game.id,
                player_id=next_player_id,
            )

            return RedirectResponse(
                redirect_url,
                status_code=HTTPStatus.FOUND,
            )

    # next_player_id
    redirect_url = request.url_for(
        "start_of_game",
        game_id=game.next_game_id,
        player_id=next_player_id,
    )

    return RedirectResponse(
        redirect_url,
        status_code=HTTPStatus.FOUND,
    )


@router.get(
    "/{game_id}/player/{player_id}/real_game_transition",
    response_class=HTMLResponse,
)
def real_game_transition(
    request: Request,
    game_id: int,
    player_id: int,
    db: Session = Depends(get_db),
) -> Response:
    """
    Function that returns the start of game page and
    template.
    """

    template_text = languages[get_lang_from_player_id(player_id, db)]

    result = {
        "request": request,
        "player_id": player_id,
        "game_id": game_id,
        "points": WINNING_SCORE,
        "text": template_text,
    }

    return templates.TemplateResponse("real_game_transition.html", result)


###########################################
# Utilities
###########################################


@router.get("/session/{session_id}", response_class=HTMLResponse)
def route_session_access(
    request: Request, session_id: int, db: Session = Depends(get_db)
) -> Response:
    # Do some logic things
    session = db.query(GameSession).filter_by(id=session_id).one_or_none()

    raise_exception_if_none(session, "session not found")

    return templates.TemplateResponse(
        "new_session.html", context={"request": request}
    )


@router.get("/{game_id}", response_class=JSONResponse)
def route_game_access(
    game_id: int, db: Session = Depends(get_db)
) -> JSONResponse:
    game = db.query(Game).filter_by(id=game_id).one_or_none()
    raise_exception_if_none(game, detail="game not found")
    return JSONResponse(
        content={
            "game_id": game_id,
            "rounds": game.rounds,
            "practice": game.practice,
        }
    )


@router.get("/{game_id}/player/{player_id}", response_class=JSONResponse)
def route_game_player_access(
    game_id: int, player_id: int, db: Session = Depends(get_db)
) -> JSONResponse:
    # tests to ensure game and player exists
    game, player = get_game_and_player(game_id, player_id, db)

    return JSONResponse(content={"game_id": game_id, "player_id": player_id})


###########################################
# Unused
###########################################


@router.post("/ready", response_class=JSONResponse)
def confirm_player(
    player_id: int,
    game_id: int,
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Confirms if the player is ready for the game
    """

    game, player = get_game_and_player(game_id, player_id, db)

    player.ready = True
    db.commit()

    return JSONResponse(content={"status": "Player is ready!"})


@router.post(
    "/{game_id}/player/{player_id}/denirs", response_class=JSONResponse
)
def score_to_denirs(
    game_id: int,
    player_id: int,
    db: Session = Depends(get_db),
) -> JSONResponse:
    """
    Function that calculates the denirs for the player
    given all of their scores
    """
    total_score = 0
    game, player = get_game_and_player(game_id, player_id, db)

    for answer in player.answers:
        if answer.player_answer == answer.correct_answer:
            total_score += WINNING_SCORE

    denirs = total_score * DENIR_FACTOR

    return JSONResponse(content={"reward": f"You have made {denirs} denirs!"})
