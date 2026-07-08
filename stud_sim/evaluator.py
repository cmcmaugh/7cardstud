from __future__ import annotations

from collections import Counter
from itertools import combinations

from .cards import Card

CATEGORY_NAMES = {
    8: "straight flush",
    7: "four of a kind",
    6: "full house",
    5: "flush",
    4: "straight",
    3: "three of a kind",
    2: "two pair",
    1: "one pair",
    0: "high card",
}


def evaluate_five(cards: tuple[Card, ...]) -> tuple[int, tuple[int, ...]]:
    values = sorted((card.value for card in cards), reverse=True)
    counts = Counter(values)
    groups = sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)
    is_flush = len({card.suit for card in cards}) == 1
    straight_high = _straight_high(values)

    if is_flush and straight_high:
        return 8, (straight_high,)
    if groups[0][1] == 4:
        quad = groups[0][0]
        kicker = max(value for value in values if value != quad)
        return 7, (quad, kicker)
    if groups[0][1] == 3 and groups[1][1] == 2:
        return 6, (groups[0][0], groups[1][0])
    if is_flush:
        return 5, tuple(values)
    if straight_high:
        return 4, (straight_high,)
    if groups[0][1] == 3:
        trips = groups[0][0]
        kickers = tuple(value for value in values if value != trips)
        return 3, (trips, *kickers)
    if groups[0][1] == 2 and groups[1][1] == 2:
        pairs = sorted((groups[0][0], groups[1][0]), reverse=True)
        kicker = max(value for value in values if value not in pairs)
        return 2, (*pairs, kicker)
    if groups[0][1] == 2:
        pair = groups[0][0]
        kickers = tuple(value for value in values if value != pair)
        return 1, (pair, *kickers)
    return 0, tuple(values)


def best_hand(cards: list[Card]) -> tuple[tuple[int, tuple[int, ...]], tuple[Card, ...]]:
    if len(cards) < 5:
        raise ValueError("at least five cards are required")
    best_cards = max(combinations(cards, 5), key=evaluate_five)
    return evaluate_five(best_cards), best_cards


def hand_name(score: tuple[int, tuple[int, ...]]) -> str:
    return CATEGORY_NAMES[score[0]]


def _straight_high(values: list[int]) -> int | None:
    unique = sorted(set(values), reverse=True)
    if set([14, 5, 4, 3, 2]).issubset(unique):
        return 5
    for start in range(len(unique) - 4):
        window = unique[start : start + 5]
        if window[0] - window[-1] == 4:
            return window[0]
    return None
