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
    agent_simulations: int = 90
    advisor_simulations: int = 180

    def next_seed(self) -> int | None:
        if self.seed is None:
            return None
        return self.seed + self.hand_number - 1


def start_hand() -> str:
    session = BrowserSession(bankrolls=[200 for _ in range(6)])
    hand = _start_session_hand(session)
    return _json(_snapshot_with_session(hand))


def continue_hand(hand_id: str) -> str:
    hand = HANDS.get(hand_id)
    session = HAND_SESSIONS.get(hand_id)
    if not hand or not session:
        raise ValueError("unknown hand_id")
    if not hand.complete:
        raise ValueError("hand is not complete")

    session.bankrolls = [seat.bankroll for seat in hand.seats]
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
    hand = InteractiveStudHand(
        players=session.players,
        human_seat=session.human_seat,
        seed=session.next_seed(),
        agent_simulations=session.agent_simulations,
        advisor_simulations=session.advisor_simulations,
    )
    for seat, bankroll in zip(hand.seats, bankrolls):
        seat.bankroll = bankroll
    HANDS[hand.id] = hand
    HAND_SESSIONS[hand.id] = session
    hand.start()
    return hand


def _snapshot_with_session(
    hand: InteractiveStudHand,
    snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = dict(snapshot or hand.snapshot())
    session = HAND_SESSIONS.get(hand.id)
    if session:
        state["hand_number"] = session.hand_number
        state["session_bankrolls"] = [seat.bankroll for seat in hand.seats]
    return state


def _json(payload: dict[str, Any]) -> str:
    return json.dumps(payload)
