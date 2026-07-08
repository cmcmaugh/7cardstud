from __future__ import annotations

from dataclasses import dataclass, field

from .agents import DecisionRequest, StudAgent, normalize_action
from .cards import Card, Deck, card_list
from .evaluator import best_hand, hand_name

STREETS = ["third", "fourth", "fifth", "sixth", "seventh"]


@dataclass
class Seat:
    name: str
    agent: StudAgent
    bankroll: int = 200
    cards_down: list[Card] = field(default_factory=list)
    cards_up: list[Card] = field(default_factory=list)
    folded: bool = False
    contribution: int = 0

    @property
    def cards(self) -> list[Card]:
        return [*self.cards_down, *self.cards_up]


@dataclass
class GameConfig:
    ante: int = 1
    bring_in: int = 2
    small_bet: int = 4
    big_bet: int = 8
    max_raises: int = 3


@dataclass
class HandResult:
    log: list[str]
    winner: str
    pot: int


class StudTable:
    def __init__(self, seats: list[Seat], config: GameConfig | None = None, seed: int | None = None) -> None:
        if not 2 <= len(seats) <= 8:
            raise ValueError("stud requires between 2 and 8 seats")
        self.seats = seats
        self.config = config or GameConfig()
        self.seed = seed
        self.deck = Deck(seed)
        self.pot = 0
        self.log: list[str] = []

    def play_hand(self) -> HandResult:
        self._reset_hand()
        self._ante()
        self._deal_third()
        self._bring_in_and_betting()

        for street in ["fourth", "fifth", "sixth", "seventh"]:
            if len(self.active_seats()) <= 1:
                break
            self._deal_street(street)
            self._betting_round(street, self._first_to_act(street), forced_bet=0)

        winner = self._award_pot()
        return HandResult(self.log, winner.name, self.pot)

    def active_seats(self) -> list[Seat]:
        return [seat for seat in self.seats if not seat.folded]

    def _reset_hand(self) -> None:
        self.deck = Deck(self.seed)
        self.pot = 0
        self.log.clear()
        for seat in self.seats:
            seat.cards_down.clear()
            seat.cards_up.clear()
            seat.folded = False
            seat.contribution = 0

    def _ante(self) -> None:
        for seat in self.seats:
            self._commit(seat, self.config.ante)
        self.log.append(f"Antes posted: pot ${self.pot}")

    def _deal_third(self) -> None:
        for _ in range(2):
            for seat in self.seats:
                seat.cards_down.append(self.deck.deal())
        for seat in self.seats:
            seat.cards_up.append(self.deck.deal())
        self.log.append("Third street: " + self._visible_table())

    def _bring_in_and_betting(self) -> None:
        bring_in = min(self.active_seats(), key=lambda seat: (seat.cards_up[0].value, seat.cards_up[0].suit))
        self._commit(bring_in, self.config.bring_in)
        self.log.append(f"{bring_in.name} brings in for ${self.config.bring_in}")
        self._betting_round("third", self._next_index(bring_in), forced_bet=self.config.bring_in)

    def _deal_street(self, street: str) -> None:
        for seat in self.active_seats():
            if street == "seventh":
                seat.cards_down.append(self.deck.deal())
            else:
                seat.cards_up.append(self.deck.deal())
        self.log.append(f"{street.title()} street: {self._visible_table()}")

    def _betting_round(self, street: str, start_index: int, forced_bet: int) -> None:
        bet_unit = self.config.small_bet if street in {"third", "fourth"} else self.config.big_bet
        current_bet = forced_bet
        street_put_in = {seat.name: forced_bet if forced_bet and seat.contribution >= forced_bet else 0 for seat in self.seats}
        raises = 0
        acted_since_raise: set[str] = set()
        index = start_index

        while len(self.active_seats()) > 1:
            seat = self.seats[index]
            index = (index + 1) % len(self.seats)
            if seat.folded:
                continue

            call_amount = max(0, current_bet - street_put_in[seat.name])
            can_raise = raises < self.config.max_raises
            legal = self._legal_actions(call_amount, current_bet, can_raise)
            request = self._decision_request(seat, street, legal, call_amount, bet_unit)
            decision = normalize_action(seat.agent.decide(request), legal)

            if decision.action == "fold":
                seat.folded = True
                self.log.append(f"{seat.name} folds ({decision.reason})")
            elif decision.action in {"check", "call"}:
                if call_amount:
                    self._commit(seat, call_amount)
                    street_put_in[seat.name] += call_amount
                    self.log.append(f"{seat.name} calls ${call_amount} ({decision.reason})")
                else:
                    self.log.append(f"{seat.name} checks ({decision.reason})")
                acted_since_raise.add(seat.name)
            elif decision.action in {"bet", "raise"}:
                target_bet = self._raise_target(street, current_bet, bet_unit)
                add_amount = target_bet - street_put_in[seat.name]
                self._commit(seat, add_amount)
                street_put_in[seat.name] += add_amount
                current_bet = target_bet
                raises += 1
                acted_since_raise = {seat.name}
                verb = "bets" if decision.action == "bet" else "raises"
                self.log.append(f"{seat.name} {verb} to ${current_bet} ({decision.reason})")

            active_names = {active.name for active in self.active_seats()}
            if active_names and active_names.issubset(acted_since_raise):
                if all(street_put_in[name] == current_bet for name in active_names):
                    break

    def _legal_actions(self, call_amount: int, current_bet: int, can_raise: bool) -> list[str]:
        if call_amount:
            actions = ["fold", "call"]
            if can_raise:
                actions.append("raise")
            return actions
        actions = ["check"]
        if current_bet == 0 and can_raise:
            actions.append("bet")
        return actions

    def _raise_target(self, street: str, current_bet: int, bet_unit: int) -> int:
        if current_bet == 0:
            return bet_unit
        if street == "third" and current_bet == self.config.bring_in:
            return self.config.small_bet
        return current_bet + bet_unit

    def _decision_request(
        self, seat: Seat, street: str, legal: list[str], call_amount: int, raise_amount: int
    ) -> DecisionRequest:
        return DecisionRequest(
            seat_name=seat.name,
            street=street,
            legal_actions=legal,
            call_amount=call_amount,
            raise_amount=raise_amount,
            pot=self.pot,
            bankroll=seat.bankroll,
            private_cards=card_list(seat.cards_down),
            exposed_cards=card_list(seat.cards_up),
            visible_table=self._visible_table(),
            action_history=self.log,
        )

    def _first_to_act(self, street: str) -> int:
        active = self.active_seats()
        if street == "fourth":
            first = max(active, key=lambda seat: _board_rank(seat.cards_up))
        else:
            first = max(active, key=lambda seat: _board_rank(seat.cards_up))
        return self.seats.index(first)

    def _award_pot(self) -> Seat:
        active = self.active_seats()
        if len(active) == 1:
            winner = active[0]
            winner.bankroll += self.pot
            self.log.append(f"{winner.name} wins ${self.pot} uncontested")
            return winner

        scored = []
        for seat in active:
            score, cards = best_hand(seat.cards)
            scored.append((score, seat, cards))
            self.log.append(f"{seat.name} shows {card_list(seat.cards)}: {hand_name(score)}")
        score, winner, cards = max(scored, key=lambda item: item[0])
        winner.bankroll += self.pot
        self.log.append(f"{winner.name} wins ${self.pot} with {hand_name(score)} ({card_list(list(cards))})")
        return winner

    def _commit(self, seat: Seat, amount: int) -> None:
        amount = min(amount, seat.bankroll)
        seat.bankroll -= amount
        seat.contribution += amount
        self.pot += amount

    def _visible_table(self) -> str:
        return " | ".join(f"{seat.name}: {card_list(seat.cards_up)}" for seat in self.seats if not seat.folded)

    def _next_index(self, seat: Seat) -> int:
        return (self.seats.index(seat) + 1) % len(self.seats)


def _board_rank(cards: list[Card]) -> tuple[int, list[int]]:
    values = sorted([card.value for card in cards], reverse=True)
    return (len(values) - len(set(values)), values)
