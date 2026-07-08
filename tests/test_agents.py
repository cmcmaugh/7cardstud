from stud_sim.agents import DecisionRequest, RangeEquityStudAgent, _dead_exposed_cards_from_history, _estimate_equity
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


def test_agent_value_bets_strong_equity_even_in_small_pot() -> None:
    request = DecisionRequest(
        seat_name="Hero",
        street="sixth",
        legal_actions=["check", "bet"],
        call_amount=0,
        raise_amount=8,
        pot=8,
        bankroll=188,
        private_cards="K♣ 7♣",
        exposed_cards="Q♣ J♦ K♥ Q♠",
        visible_table=(
            "Hero: Q♣ J♦ K♥ Q♠ | Seat 2: 9♠ 5♣ A♠ Q♥ | "
            "Seat 3: 7♥ 2♦ 8♥ K♦ | Seat 4: 6♦ 6♥ 4♦ 8♣"
        ),
        action_history=[
            "Fourth street: Hero: Q♣ J♦ | Seat 2: 9♠ 5♣ | Seat 3: 7♥ 2♦ | Seat 4: 6♦ 6♥",
            "Fifth street: Hero: Q♣ J♦ K♥ | Seat 2: 9♠ 5♣ A♠ | Seat 3: 7♥ 2♦ 8♥ | Seat 4: 6♦ 6♥ 4♦",
            "Sixth street: Hero: Q♣ J♦ K♥ Q♠ | Seat 2: 9♠ 5♣ A♠ Q♥ | Seat 3: 7♥ 2♦ 8♥ K♦ | Seat 4: 6♦ 6♥ 4♦ 8♣",
        ],
    )

    decision = RangeEquityStudAgent("Advisor", seed=3, simulations=180).decide(request)

    assert decision.action == "bet"
