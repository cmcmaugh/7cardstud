from stud_sim.agents import DecisionRequest, _dead_exposed_cards_from_history, _estimate_equity
from stud_sim.cards import Card
import random


def test_dead_exposed_cards_include_folded_prior_street_boards() -> None:
    history = [
        "Antes posted: pot $6",
        "Third street: Hero: 5♥ | Seat 2: K♣ | Seat 3: 7♣ | Seat 4: 8♣ | Seat 5: 8♠ | Seat 6: 8♦",
        "Seat 5 folds",
        "Seat 6 folds",
        "Fourth street: Hero: 5♥ 9♠ | Seat 2: K♣ J♠ | Seat 3: 7♣ 2♥ | Seat 4: 8♣ 5♠",
    ]

    dead = set(_dead_exposed_cards_from_history(history))

    assert Card("8", "s") in dead
    assert Card("8", "d") in dead


def test_equity_accounts_for_folded_dead_exposed_cards() -> None:
    request = DecisionRequest(
        seat_name="Hero",
        street="fourth",
        legal_actions=["fold", "call", "raise"],
        call_amount=4,
        raise_amount=4,
        pot=26,
        bankroll=190,
        private_cards="6♣ 7♥",
        exposed_cards="5♥ 9♠",
        visible_table="Hero: 5♥ 9♠ | Seat 2: K♣ J♠ | Seat 3: 7♣ 2♥ | Seat 4: 8♣ 5♠",
        action_history=[
            "Third street: Hero: 5♥ | Seat 2: K♣ | Seat 3: 7♣ | Seat 4: 8♣ | Seat 5: 8♠ | Seat 6: 8♦",
            "Seat 5 folds",
            "Seat 6 folds",
            "Fourth street: Hero: 5♥ 9♠ | Seat 2: K♣ J♠ | Seat 3: 7♣ 2♥ | Seat 4: 8♣ 5♠",
        ],
    )

    estimate = _estimate_equity(request, random.Random(11), 80)

    assert estimate.equity < 0.35
