import json
from io import BytesIO
from http import HTTPStatus

from stud_sim.http_server import HANDS, HAND_SESSIONS, StudHTTPRequestHandler


class FakeHandler(StudHTTPRequestHandler):
    def __init__(self):
        self.status = None
        self.headers = []
        self.wfile = BytesIO()

    def send_response(self, code, message=None):
        self.status = code

    def send_header(self, keyword, value):
        self.headers.append((keyword, value))

    def end_headers(self):
        pass


def decode_response(handler):
    return json.loads(handler.wfile.getvalue().decode("utf-8"))


def test_create_hand_stores_and_returns_started_hand() -> None:
    HANDS.clear()
    HAND_SESSIONS.clear()
    handler = FakeHandler()

    handler._create_hand({"players": 6, "human_seat": 1, "seed": 7})

    assert handler.status == HTTPStatus.CREATED
    state = decode_response(handler)
    assert state["hand_id"] in HANDS
    assert state["pending_decision"] or state["complete"]


def test_act_rejects_unknown_hand() -> None:
    HANDS.clear()
    HAND_SESSIONS.clear()
    handler = FakeHandler()

    handler._act("missing", {"action": "call"})

    assert handler.status == HTTPStatus.NOT_FOUND
    assert decode_response(handler) == {"error": "unknown hand_id"}


def test_continue_starts_next_hand_with_carried_bankrolls() -> None:
    HANDS.clear()
    HAND_SESSIONS.clear()
    handler = FakeHandler()
    handler._create_hand({"players": 2, "human_seat": 1, "seed": 3})
    first = decode_response(handler)
    first_hand = HANDS[first["hand_id"]]
    first_hand.complete = True
    first_hand.seats[0].bankroll = 100
    first_hand.seats[1].bankroll = 300

    next_handler = FakeHandler()
    next_handler._continue(first["hand_id"])
    second = decode_response(next_handler)

    assert next_handler.status == HTTPStatus.CREATED
    assert second["hand_number"] == 2
    assert max(seat["bankroll"] for seat in second["seats"]) > 250


def test_continue_removes_busted_players_between_hands() -> None:
    HANDS.clear()
    HAND_SESSIONS.clear()
    handler = FakeHandler()
    handler._create_hand({"players": 3, "human_seat": 1, "seed": 4})
    first = decode_response(handler)
    first_hand = HANDS[first["hand_id"]]
    first_hand.complete = True
    first_hand.seats[0].bankroll = 200
    first_hand.seats[1].bankroll = 0
    first_hand.seats[2].bankroll = 200

    next_handler = FakeHandler()
    next_handler._continue(first["hand_id"])
    second = decode_response(next_handler)

    assert next_handler.status == HTTPStatus.CREATED
    assert len(second["seats"]) == 2
    assert second["busted_seats"] == [{"name": "Seat 2", "bankroll": 0}]


def test_continue_ends_game_when_hero_busts() -> None:
    HANDS.clear()
    HAND_SESSIONS.clear()
    handler = FakeHandler()
    handler._create_hand({"players": 3, "human_seat": 1, "seed": 5})
    first = decode_response(handler)
    first_hand = HANDS[first["hand_id"]]
    first_hand.complete = True
    first_hand.seats[0].bankroll = 0
    first_hand.seats[1].bankroll = 200
    first_hand.seats[2].bankroll = 200

    next_handler = FakeHandler()
    next_handler._continue(first["hand_id"])
    state = decode_response(next_handler)

    assert next_handler.status == HTTPStatus.OK
    assert state["game_over"] is True
    assert state["busted_seats"] == [{"name": "Hero", "bankroll": 0}]
