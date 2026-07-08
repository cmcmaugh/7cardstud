from __future__ import annotations

from dataclasses import dataclass
import random

RANKS = "23456789TJQKA"
SUITS = "cdhs"
RANK_VALUE = {rank: index + 2 for index, rank in enumerate(RANKS)}
SUIT_SYMBOL = {"c": "♣", "d": "♦", "h": "♥", "s": "♠"}


@dataclass(frozen=True, order=True)
class Card:
    rank: str
    suit: str

    @property
    def value(self) -> int:
        return RANK_VALUE[self.rank]

    def short(self, symbols: bool = True) -> str:
        suit = SUIT_SYMBOL[self.suit] if symbols else self.suit
        return f"{self.rank}{suit}"


class Deck:
    def __init__(self, seed: int | None = None) -> None:
        self.cards = [Card(rank, suit) for suit in SUITS for rank in RANKS]
        self.random = random.Random(seed)
        self.random.shuffle(self.cards)

    def deal(self) -> Card:
        return self.cards.pop()

    def burn(self) -> Card:
        return self.deal()


def card_list(cards: list[Card], symbols: bool = True) -> str:
    return " ".join(card.short(symbols=symbols) for card in cards)
