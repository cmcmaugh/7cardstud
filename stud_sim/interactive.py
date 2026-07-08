from __future__ import annotations

from dataclasses import dataclass
import os
from uuid import uuid4

from .agents import AgentDecision, DecisionRequest, RangeEquityStudAgent, normalize_action
from .cards import Deck, card_list
from .evaluator import best_hand, hand_name
from .game import GameConfig, Seat, _board_rank


@dataclass
class PendingDecision:
    request: DecisionRequest
    seat_index: int


class InteractiveStudHand:
    def __init__(
        self,
        players: int = 6,
        human_seat: int = 0,
        seed: int | None = None,
        config: GameConfig | None = None,
        agent_simulations: int | None = None,
        advisor_simulations: int | None = None,
    ) -> None:
        if not 2 <= players <= 8:
            raise ValueError("players must be between 2 and 8")
        if not 0 <= human_seat < players:
            raise ValueError("human_seat is zero-based and must be within players")
        self.id = uuid4().hex
        self.config = config or GameConfig()
        self.seed = seed
        self.deck = Deck(seed)
        self.human_seat = human_seat
        self.agent_simulations = agent_simulations or int(os.environ.get("STUD_AGENT_SIMS", "450"))
        self.advisor_simulations = advisor_simulations or int(os.environ.get("STUD_ADVISOR_SIMS", "900"))
        self.advisor = RangeEquityStudAgent(
            "Advisor",
            seed=(seed or 0) + 100_000,
            simulations=self.advisor_simulations,
        )
        self.seats = [
            Seat(
                name="Hero" if index == human_seat else f"Seat {index + 1}",
                agent=RangeEquityStudAgent(
                    f"Seat {index + 1}",
                    seed=(seed or 0) + index,
                    simulations=self.agent_simulations,
                ),
            )
            for index in range(players)
        ]
        self.pot = 0
        self.log: list[str] = []
        self.street = "third"
        self.current_bet = 0
        self.street_put_in: dict[str, int] = {}
        self.raises = 0
        self.acted_since_raise: set[str] = set()
        self.round_starter_index = 0
        self.next_index = 0
        self.pending: PendingDecision | None = None
        self.last_decision_review: dict[str, object] | None = None
        self._last_private_cards_log = ""
        self.complete = False
        self.winner: str | None = None

    def start(self) -> dict[str, object]:
        self._ante()
        self._deal_third()
        bring_in = min(self.active_seats(), key=lambda seat: (seat.cards_up[0].value, seat.cards_up[0].suit))
        self._commit(bring_in, self.config.bring_in)
        self.log.append(f"{bring_in.name} brings in for ${self.config.bring_in}")
        self._begin_betting("third", self._next_index(bring_in), self.config.bring_in)
        return self.advance()

    def act(self, action: str) -> dict[str, object]:
        if not self.pending:
            raise ValueError("there is no pending human decision")
        request = self.pending.request
        decision = normalize_action(AgentDecision(action, "chosen by human"), request.legal_actions)
        recommended = normalize_action(self.advisor.decide(request), request.legal_actions)
        self.last_decision_review = _decision_review(request, decision, recommended)
        self._apply_action(self.seats[self.pending.seat_index], decision)
        self.pending = None
        return self.advance()

    def advance(self) -> dict[str, object]:
        while not self.complete:
            if len(self.active_seats()) <= 1:
                self._award_pot()
                break

            seat = self._next_active_seat()
            call_amount = max(0, self.current_bet - self.street_put_in[seat.name])
            legal = self._legal_actions(call_amount)
            request = self._decision_request(seat, legal, call_amount)

            if self.seats.index(seat) == self.human_seat:
                self.pending = PendingDecision(request=request, seat_index=self.human_seat)
                self._log_human_private_cards()
                return self.snapshot()

            decision = normalize_action(seat.agent.decide(request), legal)
            self._apply_action(seat, decision)

            if self._round_complete():
                self._next_street_or_showdown()

        return self.snapshot()

    def snapshot(self) -> dict[str, object]:
        pending = None
        if self.pending:
            request = self.pending.request
            seat = self.seats[self.pending.seat_index]
            bet_unit = self.config.small_bet if self.street in {"third", "fourth"} else self.config.big_bet
            raise_target = self._raise_target(self.current_bet, bet_unit)
            pending = {
                "seat": request.seat_name,
                "street": request.street,
                "legal_actions": request.legal_actions,
                "action_costs": {
                    "fold": 0,
                    "check": 0,
                    "call": request.call_amount,
                    "bet": bet_unit,
                    "raise": max(0, raise_target - self.street_put_in[seat.name]),
                },
                "call_amount": request.call_amount,
                "raise_amount": request.raise_amount,
                "private_cards": request.private_cards,
                "exposed_cards": request.exposed_cards,
                "visible_table": request.visible_table,
            }
        return {
            "hand_id": self.id,
            "complete": self.complete,
            "winner": self.winner,
            "pot": self.pot,
            "street": self.street,
            "last_decision_review": self.last_decision_review,
            "pending_decision": pending,
            "seats": [
                {
                    "name": seat.name,
                    "position": index,
                    "bankroll": seat.bankroll,
                    "in_play": seat.contribution,
                    "started_current_round": index == self.round_starter_index and not self.complete,
                    "folded": seat.folded,
                    "exposed_cards": card_list(seat.cards_up),
                    "private_cards": card_list(seat.cards_down) if index == self.human_seat or self.complete else "",
                    "private_count": len(seat.cards_down),
                }
                for index, seat in enumerate(self.seats)
            ],
            "log": self.log,
        }

    def active_seats(self) -> list[Seat]:
        return [seat for seat in self.seats if not seat.folded]

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

    def _deal_street(self, street: str) -> None:
        for seat in self.active_seats():
            if street == "seventh":
                seat.cards_down.append(self.deck.deal())
            else:
                seat.cards_up.append(self.deck.deal())
        self.log.append(f"{street.title()} street: {self._visible_table()}")

    def _begin_betting(self, street: str, start_index: int, forced_bet: int) -> None:
        self.street = street
        self.current_bet = forced_bet
        self.street_put_in = {
            seat.name: forced_bet if forced_bet and seat.contribution >= forced_bet else 0 for seat in self.seats
        }
        self.raises = 0
        self.acted_since_raise = set()
        self.round_starter_index = start_index
        self.next_index = start_index

    def _next_active_seat(self) -> Seat:
        while True:
            seat = self.seats[self.next_index]
            self.next_index = (self.next_index + 1) % len(self.seats)
            if not seat.folded:
                return seat

    def _apply_action(self, seat: Seat, decision: AgentDecision) -> None:
        call_amount = max(0, self.current_bet - self.street_put_in[seat.name])
        bet_unit = self.config.small_bet if self.street in {"third", "fourth"} else self.config.big_bet
        if decision.action == "fold":
            seat.folded = True
            self.log.append(f"{seat.name} folds ({decision.reason})")
        elif decision.action in {"check", "call"}:
            if call_amount:
                self._commit(seat, call_amount)
                self.street_put_in[seat.name] += call_amount
                self.log.append(f"{seat.name} calls ${call_amount} ({decision.reason})")
            else:
                self.log.append(f"{seat.name} checks ({decision.reason})")
            self.acted_since_raise.add(seat.name)
        elif decision.action in {"bet", "raise"}:
            target_bet = self._raise_target(self.current_bet, bet_unit)
            add_amount = target_bet - self.street_put_in[seat.name]
            self._commit(seat, add_amount)
            self.street_put_in[seat.name] += add_amount
            self.current_bet = target_bet
            self.raises += 1
            self.acted_since_raise = {seat.name}
            verb = "bets" if decision.action == "bet" else "raises"
            self.log.append(f"{seat.name} {verb} to ${self.current_bet} ({decision.reason})")

    def _round_complete(self) -> bool:
        active_names = {seat.name for seat in self.active_seats()}
        return bool(active_names) and active_names.issubset(self.acted_since_raise) and all(
            self.street_put_in[name] == self.current_bet for name in active_names
        )

    def _next_street_or_showdown(self) -> None:
        order = ["third", "fourth", "fifth", "sixth", "seventh"]
        street_index = order.index(self.street)
        if street_index == len(order) - 1:
            self._award_pot()
            return
        next_street = order[street_index + 1]
        self._deal_street(next_street)
        first = max(self.active_seats(), key=lambda seat: _board_rank(seat.cards_up))
        self._begin_betting(next_street, self.seats.index(first), 0)

    def _award_pot(self) -> None:
        active = self.active_seats()
        if len(active) == 1:
            winner = active[0]
            winner.bankroll += self.pot
            self.winner = winner.name
            self.complete = True
            self.log.append(f"{winner.name} wins ${self.pot} uncontested")
            return

        scored = []
        for seat in active:
            score, cards = best_hand(seat.cards)
            scored.append((score, seat, cards))
            self.log.append(f"{seat.name} shows {card_list(seat.cards)}: {hand_name(score)}")
        score, winner, cards = max(scored, key=lambda item: item[0])
        winner.bankroll += self.pot
        self.winner = winner.name
        self.complete = True
        self.log.append(f"{winner.name} wins ${self.pot} with {hand_name(score)} ({card_list(list(cards))})")

    def _legal_actions(self, call_amount: int) -> list[str]:
        can_raise = self.raises < self.config.max_raises
        if call_amount:
            actions = ["fold", "call"]
            if can_raise:
                actions.append("raise")
            return actions
        actions = ["check"]
        if self.current_bet == 0 and can_raise:
            actions.append("bet")
        return actions

    def _raise_target(self, current_bet: int, bet_unit: int) -> int:
        if current_bet == 0:
            return bet_unit
        if self.street == "third" and current_bet == self.config.bring_in:
            return self.config.small_bet
        return current_bet + bet_unit

    def _decision_request(self, seat: Seat, legal: list[str], call_amount: int) -> DecisionRequest:
        bet_unit = self.config.small_bet if self.street in {"third", "fourth"} else self.config.big_bet
        return DecisionRequest(
            seat_name=seat.name,
            street=self.street,
            legal_actions=legal,
            call_amount=call_amount,
            raise_amount=bet_unit,
            pot=self.pot,
            bankroll=seat.bankroll,
            private_cards=card_list(seat.cards_down),
            exposed_cards=card_list(seat.cards_up),
            visible_table=self._visible_table(),
            action_history=self.log,
        )

    def _commit(self, seat: Seat, amount: int) -> None:
        amount = min(amount, seat.bankroll)
        seat.bankroll -= amount
        seat.contribution += amount
        self.pot += amount

    def _visible_table(self) -> str:
        return " | ".join(f"{seat.name}: {card_list(seat.cards_up)}" for seat in self.seats if not seat.folded)

    def _next_index(self, seat: Seat) -> int:
        return (self.seats.index(seat) + 1) % len(self.seats)

    def _log_human_private_cards(self) -> None:
        private_cards = card_list(self.seats[self.human_seat].cards_down)
        if private_cards and private_cards != self._last_private_cards_log:
            self.log.append(f"Hero private cards: {private_cards}")
            self._last_private_cards_log = private_cards


def _decision_review(
    request: DecisionRequest,
    chosen: AgentDecision,
    recommended: AgentDecision,
) -> dict[str, object]:
    correct = chosen.action == recommended.action
    review: dict[str, object] = {
        "correct": correct,
        "chosen_action": chosen.action,
        "recommended_action": recommended.action,
        "explanation": "Matched the range-equity recommendation." if correct else recommended.reason,
    }
    if not correct:
        review["prompt"] = "\n".join(
            [
                "Analyze this 7-card stud decision.",
                "",
                "Game: six-handed $4/$8 limit 7-card stud",
                f"Street: {request.street}",
                f"Pot before my action: ${request.pot}",
                f"Legal actions: {', '.join(request.legal_actions)}",
                f"Call amount: ${request.call_amount}",
                f"Raise amount: ${request.raise_amount}",
                f"My private cards: {request.private_cards}",
                f"My exposed cards: {request.exposed_cards}",
                f"Visible table: {request.visible_table}",
                f"Recent action: {' | '.join(request.action_history[-12:])}",
                "",
                f"I chose: {chosen.action}",
                f"The simulator's range-equity advisor preferred: {recommended.action}",
                f"Advisor explanation: {recommended.reason}",
                "",
                "Was my action a mistake? Explain using pot odds, live cards, likely opponent ranges, "
                "reverse implied odds, and better alternative lines.",
            ]
        )
    return review
