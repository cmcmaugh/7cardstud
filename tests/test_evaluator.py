from stud_sim.cards import Card
from stud_sim.evaluator import best_hand, hand_name


def test_best_hand_finds_straight_flush() -> None:
    cards = [
        Card("A", "s"),
        Card("K", "s"),
        Card("Q", "s"),
        Card("J", "s"),
        Card("T", "s"),
        Card("2", "c"),
        Card("2", "d"),
    ]

    score, _ = best_hand(cards)

    assert hand_name(score) == "straight flush"


def test_wheel_straight_counts_as_straight() -> None:
    cards = [
        Card("A", "s"),
        Card("2", "d"),
        Card("3", "c"),
        Card("4", "h"),
        Card("5", "s"),
        Card("K", "c"),
        Card("9", "d"),
    ]

    score, _ = best_hand(cards)

    assert hand_name(score) == "straight"
    assert score[1] == (5,)
