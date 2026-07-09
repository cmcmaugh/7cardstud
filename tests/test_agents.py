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


def test_agent_value_raises_buried_aces_on_third_street() -> None:
    request = DecisionRequest(
        seat_name="Hero",
        street="third",
        legal_actions=["fold", "call", "raise"],
        call_amount=2,
        raise_amount=4,
        pot=9,
        bankroll=199,
        private_cards="A♠ A♦",
        exposed_cards="J♣",
        visible_table="Hero: J♣ | Seat 3: K♥ | Seat 4: Q♣ | Seat 5: 3♦ | Seat 6: 8♦",
        action_history=[
            "Antes posted: pot $5",
            "Third street: Hero: J♣ | Seat 3: K♥ | Seat 4: Q♣ | Seat 5: 3♦ | Seat 6: 8♦",
            "Seat 5 brings in for $2",
            "Seat 6 calls $2",
            "Hero private cards: A♠ A♦",
        ],
    )

    decision = RangeEquityStudAgent("Advisor", seed=2, simulations=900).decide(request)

    assert decision.action == "raise"


def test_agent_does_not_use_implied_odds_on_seventh_street() -> None:
    request = DecisionRequest(
        seat_name="Hero",
        street="seventh",
        legal_actions=["fold", "call", "raise"],
        call_amount=8,
        raise_amount=8,
        pot=269,
        bankroll=120,
        private_cards="A♠ Q♦ 9♠",
        exposed_cards="3♦ 5♦ 8♣ 4♣",
        visible_table=(
            "Hero: 3♦ 5♦ 8♣ 4♣ | Seat 3: T♣ A♥ 4♠ 8♥ | "
            "Seat 5: 3♠ K♦ 6♠ T♦ | Seat 6: Q♠ K♠ 6♥ 2♠"
        ),
        action_history=[
            "Sixth street: Hero: 3♦ 5♦ 8♣ 4♣ | Seat 3: T♣ A♥ 4♠ 8♥ | Seat 5: 3♠ K♦ 6♠ T♦ | Seat 6: Q♠ K♠ 6♥ 2♠",
            "Seventh street: Hero: 3♦ 5♦ 8♣ 4♣ | Seat 3: T♣ A♥ 4♠ 8♥ | Seat 5: 3♠ K♦ 6♠ T♦ | Seat 6: Q♠ K♠ 6♥ 2♠",
            "Seat 5 bets to $8",
            "Seat 6 calls $8",
            "Hero private cards: A♠ Q♦ 9♠",
        ],
    )

    decision = RangeEquityStudAgent("Advisor", seed=4, simulations=180).decide(request)

    assert decision.action == "fold"


def test_agent_tightens_weak_third_street_peels() -> None:
    request = DecisionRequest(
        seat_name="Hero",
        street="third",
        legal_actions=["fold", "call", "raise"],
        call_amount=2,
        raise_amount=4,
        pot=6,
        bankroll=199,
        private_cards="4♥ 3♣",
        exposed_cards="9♦",
        visible_table="Hero: 9♦ | Seat 2: 8♠ | Seat 3: 5♦",
        action_history=[
            "Antes posted: pot $4",
            "Third street: Hero: 9♦ | Seat 2: 8♠ | Seat 3: 5♦ | Seat 6: 6♠",
            "Seat 3 brings in for $2",
            "Seat 6 folds",
            "Hero private cards: 4♥ 3♣",
        ],
    )

    decision = RangeEquityStudAgent("Advisor", seed=8, simulations=180).decide(request)

    assert decision.action == "fold"


def test_agent_still_continues_playable_third_street_three_flush() -> None:
    request = DecisionRequest(
        seat_name="Hero",
        street="third",
        legal_actions=["fold", "call", "raise"],
        call_amount=2,
        raise_amount=4,
        pot=8,
        bankroll=199,
        private_cards="K♥ 3♥",
        exposed_cards="A♥",
        visible_table="Hero: A♥ | Seat 2: K♣ | Seat 3: J♣ | Seat 4: 2♠",
        action_history=[
            "Antes posted: pot $6",
            "Third street: Hero: A♥ | Seat 2: K♣ | Seat 3: J♣ | Seat 4: 2♠ | Seat 5: 5♣ | Seat 6: T♠",
            "Seat 4 brings in for $2",
            "Seat 5 folds",
            "Seat 6 folds",
            "Hero private cards: K♥ 3♥",
        ],
    )

    decision = RangeEquityStudAgent("Advisor", seed=9, simulations=180).decide(request)

    assert decision.action in {"call", "raise"}
