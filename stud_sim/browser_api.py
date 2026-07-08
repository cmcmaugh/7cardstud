from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .interactive import InteractiveStudHand

HANDS: dict[str, InteractiveStudHand] = {}
HAND_SESSIONS: dict[str, "BrowserSession"] = {}


@dataclass
class BrowserSession:
    players: int = 6
    human_seat: int = 0
    seed: int | None = None
    hand_number: int = 1
    bankrolls: list[int] | None = None
    active_seats: list[int] | None = None
    last_table_seats: list[int] | None = None
    game_over: bool = False
    agent_simulations: int = 90
    advisor_simulations: int = 180

    def next_seed(self) -> int | None:
        if self.seed is None:
            return None
        return self.seed + self.hand_number - 1


def start_hand() -> str:
    session = BrowserSession(
        bankrolls=[200 for _ in range(6)],
        active_seats=list(range(6)),
        last_table_seats=[],
    )
    hand = _start_session_hand(session)
    return _json(_snapshot_with_session(hand))


def continue_hand(hand_id: str) -> str:
    hand = HANDS.get(hand_id)
    session = HAND_SESSIONS.get(hand_id)
    if not hand or not session:
        raise ValueError("unknown hand_id")
    if not hand.complete:
        raise ValueError("hand is not complete")

    _update_session_bankrolls(session, hand)
    session.active_seats = [
        index for index in (session.active_seats or []) if (session.bankrolls or [])[index] >= hand.config.ante
    ]
    if len(session.active_seats) < 2 or session.human_seat not in session.active_seats:
        session.game_over = True
        return _json(_snapshot_with_session(hand))
    session.hand_number += 1
    next_hand = _start_session_hand(session)
    return _json(_snapshot_with_session(next_hand))


def act(hand_id: str, action: str) -> str:
    hand = HANDS.get(hand_id)
    if not hand:
        raise ValueError("unknown hand_id")
    return _json(_snapshot_with_session(hand, hand.act(action)))


def reset_game() -> str:
    HANDS.clear()
    HAND_SESSIONS.clear()
    return _json({"reset": True})


def _start_session_hand(session: BrowserSession) -> InteractiveStudHand:
    bankrolls = session.bankrolls or [200 for _ in range(session.players)]
    active_seats = session.active_seats or list(range(session.players))
    if session.human_seat not in active_seats:
        raise ValueError("hero is busted")
    active_human_seat = active_seats.index(session.human_seat)
    hand = InteractiveStudHand(
        players=len(active_seats),
        human_seat=active_human_seat,
        seed=session.next_seed(),
        agent_simulations=session.agent_simulations,
        advisor_simulations=session.advisor_simulations,
    )
    session.last_table_seats = list(active_seats)
    for table_index, original_index in enumerate(session.last_table_seats):
        hand.seats[table_index].bankroll = bankrolls[original_index]
        if original_index != session.human_seat:
            hand.seats[table_index].name = f"Seat {original_index + 1}"
    HANDS[hand.id] = hand
    HAND_SESSIONS[hand.id] = session
    hand.start()
    return hand


def _update_session_bankrolls(session: BrowserSession, hand: InteractiveStudHand) -> None:
    if session.bankrolls is None:
        session.bankrolls = [200 for _ in range(session.players)]
    for table_index, seat in enumerate(hand.seats):
        if session.last_table_seats and table_index < len(session.last_table_seats):
            session.bankrolls[session.last_table_seats[table_index]] = seat.bankroll


def _snapshot_with_session(
    hand: InteractiveStudHand,
    snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = dict(snapshot or hand.snapshot())
    session = HAND_SESSIONS.get(hand.id)
    if session:
        _update_session_bankrolls(session, hand)
        state["hand_number"] = session.hand_number
        state["session_bankrolls"] = session.bankrolls
        active_seats = session.active_seats or []
        state["busted_seats"] = [
            {"name": "Hero" if index == session.human_seat else f"Seat {index + 1}", "bankroll": bankroll}
            for index, bankroll in enumerate(session.bankrolls or [])
            if index not in active_seats
        ]
        state["game_over"] = session.game_over
    return state


def _json(payload: dict[str, Any]) -> str:
    return json.dumps(payload)
