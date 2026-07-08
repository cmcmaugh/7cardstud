from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Protocol

from .cards import Card, RANKS, SUITS
from .evaluator import best_hand

VALID_ACTIONS = {"fold", "check", "call", "bet", "raise"}


@dataclass(frozen=True)
class DecisionRequest:
    seat_name: str
    street: str
    legal_actions: list[str]
    call_amount: int
    raise_amount: int
    pot: int
    bankroll: int
    private_cards: str
    exposed_cards: str
    visible_table: str
    action_history: list[str]

    def to_prompt(self) -> str:
        return "\n".join(
            [
                "You are playing six-handed $4/$8 limit 7-card stud.",
                "Choose one action only, using JSON like {\"action\":\"call\",\"reason\":\"...\"}.",
                f"Seat: {self.seat_name}",
                f"Street: {self.street}",
                f"Legal actions: {', '.join(self.legal_actions)}",
                f"Call amount: {self.call_amount}",
                f"Raise amount: {self.raise_amount}",
                f"Pot: {self.pot}",
                f"Bankroll: {self.bankroll}",
                f"Your private cards: {self.private_cards}",
                f"Your exposed cards: {self.exposed_cards}",
                f"Visible table: {self.visible_table}",
                f"Action history: {' | '.join(self.action_history[-20:])}",
            ]
        )


@dataclass(frozen=True)
class AgentDecision:
    action: str
    reason: str = ""


class StudAgent(Protocol):
    def decide(self, request: DecisionRequest) -> AgentDecision:
        ...


class RangeEquityStudAgent:
    """Monte Carlo stud agent using live cards, pot odds, and board/action ranges."""

    def __init__(self, name: str, seed: int | None = None, simulations: int = 450) -> None:
        self.name = name
        self.random = random.Random(seed)
        self.simulations = simulations

    def decide(self, request: DecisionRequest) -> AgentDecision:
        estimate = _estimate_equity(request, self.random, self.simulations)
        pot_after_call = request.pot + request.call_amount
        pot_odds = request.call_amount / pot_after_call if pot_after_call else 0.0
        opponents = max(1, len(estimate.opponent_boards))
        value_edge = 0.08 if opponents <= 2 else 0.12
        pressure_edge = 0.16 if opponents <= 2 else 0.22

        if "raise" in request.legal_actions:
            raise_cost = request.call_amount + request.raise_amount
            raise_odds = raise_cost / (request.pot + raise_cost) if request.pot + raise_cost else 1.0
            if estimate.equity >= max(raise_odds + pressure_edge, estimate.fair_share + value_edge):
                return AgentDecision("raise", _reason("raising", estimate, pot_odds))

        if "bet" in request.legal_actions:
            bet_odds = request.raise_amount / (request.pot + request.raise_amount) if request.pot else 1.0
            if estimate.equity >= max(bet_odds + pressure_edge, estimate.fair_share + value_edge):
                return AgentDecision("bet", _reason("betting", estimate, pot_odds))

        if request.call_amount > 0:
            if estimate.equity + estimate.implied_edge < pot_odds:
                return AgentDecision("fold", _reason("folding", estimate, pot_odds))
            return AgentDecision("call", _reason("calling", estimate, pot_odds))

        if "check" in request.legal_actions:
            return AgentDecision("check", _reason("checking", estimate, pot_odds))
        return AgentDecision(request.legal_actions[0], "only legal action")

class FallbackStudAgent:
    def __init__(self, primary: StudAgent, fallback: StudAgent) -> None:
        self.primary = primary
        self.fallback = fallback

    def decide(self, request: DecisionRequest) -> AgentDecision:
        try:
            return self.primary.decide(request)
        except Exception as error:
            decision = self.fallback.decide(request)
            return AgentDecision(
                decision.action,
                f"OpenAI unavailable; local fallback used: {error}",
            )


def normalize_action(decision: AgentDecision, legal_actions: list[str]) -> AgentDecision:
    action = decision.action.lower().strip()
    if action not in VALID_ACTIONS or action not in legal_actions:
        if "check" in legal_actions:
            action = "check"
        elif "call" in legal_actions:
            action = "call"
        else:
            action = "fold"
    return AgentDecision(action, decision.reason)


@dataclass(frozen=True)
class EquityEstimate:
    equity: float
    fair_share: float
    implied_edge: float
    opponent_boards: list[list[Card]]
    samples: int


def _estimate_equity(request: DecisionRequest, random_source: random.Random, simulations: int) -> EquityEstimate:
    hero_cards = _parse_cards(f"{request.private_cards} {request.exposed_cards}")
    opponent_boards = _parse_visible_table(request.visible_table, request.seat_name)
    known_cards = hero_cards + [card for board in opponent_boards for card in board]
    deck = [Card(rank, suit) for suit in SUITS for rank in RANKS if Card(rank, suit) not in known_cards]
    fair_share = 1.0 / (len(opponent_boards) + 1)
    implied_edge = _draw_implied_edge(hero_cards)

    if not opponent_boards:
        return EquityEstimate(1.0, 1.0, implied_edge, opponent_boards, 1)

    wins = 0.0
    completed = 0
    max_attempts = max(simulations * 8, simulations)
    attempts = 0
    while completed < simulations and attempts < max_attempts:
        attempts += 1
        shuffled = deck[:]
        random_source.shuffle(shuffled)
        cursor = 0
        sampled_opponents: list[list[Card]] = []
        accepted = True

        for board in opponent_boards:
            needed = 7 - len(board)
            sample = board + shuffled[cursor : cursor + needed]
            cursor += needed
            if not _range_accepts(request, board, sample, random_source):
                accepted = False
                break
            sampled_opponents.append(sample)

        if not accepted:
            continue

        hero_needed = 7 - len(hero_cards)
        hero_sample = hero_cards + shuffled[cursor : cursor + hero_needed]
        cursor += hero_needed
        hero_score, _ = best_hand(hero_sample)
        scores = [best_hand(cards)[0] for cards in sampled_opponents]
        best_score = max([hero_score, *scores])
        if hero_score == best_score:
            ties = 1 + sum(1 for score in scores if score == hero_score)
            wins += 1.0 / ties
        completed += 1

    if completed == 0:
        return EquityEstimate(fair_share, fair_share, implied_edge, opponent_boards, 0)
    return EquityEstimate(wins / completed, fair_share, implied_edge, opponent_boards, completed)


def _range_accepts(
    request: DecisionRequest,
    board: list[Card],
    seven_cards: list[Card],
    random_source: random.Random,
) -> bool:
    prior = _board_prior(board) + _action_prior(request, board)
    if prior <= 0:
        return True

    known_count = _street_known_count(request.street)
    current_cards = seven_cards[: max(known_count, len(board))]
    current_score = _made_score(current_cards)
    draw_score = _draw_score(current_cards)
    range_score = current_score + draw_score

    acceptance = 0.30 + min(0.62, range_score / 9.0)
    if prior >= 2:
        acceptance -= 0.22
    elif prior >= 1:
        acceptance -= 0.10
    elif prior <= -1:
        acceptance += 0.12
    return random_source.random() <= max(0.12, min(0.96, acceptance))


def _board_prior(board: list[Card]) -> int:
    if not board:
        return 0
    ranks = [card.rank for card in board]
    pairs = len(ranks) - len(set(ranks))
    high_cards = sum(1 for card in board if card.value >= 11)
    suited = max(sum(1 for card in board if card.suit == suit) for suit in SUITS)
    connected = _connected_count(board)
    return pairs * 2 + (1 if high_cards else 0) + (1 if suited >= 3 else 0) + (1 if connected >= 3 else 0)


def _action_prior(request: DecisionRequest, board: list[Card]) -> int:
    seat = _seat_name_for_board(request.visible_table, board)
    if not seat:
        return 0
    recent = [line for line in request.action_history[-18:] if line.startswith(seat)]
    prior = 0
    for line in recent:
        if "raises" in line or "bets" in line:
            prior += 2
        elif "calls" in line:
            prior += 1
        elif "checks" in line:
            prior -= 1
    return max(-2, min(4, prior))


def _made_score(cards: list[Card]) -> int:
    ranks = [card.rank for card in cards]
    counts = sorted((ranks.count(rank) for rank in set(ranks)), reverse=True)
    if counts and counts[0] >= 4:
        return 8
    if len(counts) >= 2 and counts[0] == 3 and counts[1] >= 2:
        return 7
    if _has_flush(cards):
        return 6
    if _has_straight(cards):
        return 5
    if counts and counts[0] == 3:
        return 4
    if len([count for count in counts if count == 2]) >= 2:
        return 3
    if counts and counts[0] == 2:
        return 2
    return 1 if any(card.value >= 12 for card in cards) else 0


def _draw_score(cards: list[Card]) -> int:
    suited = max(sum(1 for card in cards if card.suit == suit) for suit in SUITS)
    score = 0
    if suited >= 4:
        score += 2
    elif suited == 3:
        score += 1
    connected = _connected_count(cards)
    if connected >= 4:
        score += 2
    elif connected == 3:
        score += 1
    return score


def _draw_implied_edge(cards: list[Card]) -> float:
    return min(0.08, _draw_score(cards) * 0.025)


def _connected_count(cards: list[Card]) -> int:
    values = {card.value for card in cards}
    if 14 in values:
        values.add(1)
    best = 0
    for start in range(1, 11):
        best = max(best, sum(1 for value in range(start, start + 5) if value in values))
    return best


def _has_flush(cards: list[Card]) -> bool:
    return any(sum(1 for card in cards if card.suit == suit) >= 5 for suit in SUITS)


def _has_straight(cards: list[Card]) -> bool:
    return _connected_count(cards) >= 5


def _street_known_count(street: str) -> int:
    return {"third": 3, "fourth": 4, "fifth": 5, "sixth": 6, "seventh": 7}.get(street, 7)


def _parse_visible_table(visible_table: str, hero_name: str) -> list[list[Card]]:
    boards = []
    for segment in visible_table.split("|"):
        if ":" not in segment:
            continue
        name, cards = segment.split(":", 1)
        if name.strip() == hero_name:
            continue
        boards.append(_parse_cards(cards))
    return boards


def _seat_name_for_board(visible_table: str, board: list[Card]) -> str | None:
    board_text = " ".join(card.short() for card in board)
    for segment in visible_table.split("|"):
        if ":" not in segment:
            continue
        name, cards = segment.split(":", 1)
        if _parse_cards(cards) == board or cards.strip() == board_text:
            return name.strip()
    return None


def _parse_cards(text: str) -> list[Card]:
    return [_parse_card(token) for token in text.split() if token.strip()]


def _parse_card(token: str) -> Card:
    token = token.strip()
    if len(token) != 2:
        raise ValueError(f"invalid card: {token}")
    rank = token[0].upper()
    suit = {"♣": "c", "♦": "d", "♥": "h", "♠": "s"}.get(token[1], token[1].lower())
    if rank not in RANKS or suit not in SUITS:
        raise ValueError(f"invalid card: {token}")
    return Card(rank, suit)


def _reason(action: str, estimate: EquityEstimate, pot_odds: float) -> str:
    return (
        f"{action} with {estimate.equity:.0%} simulated equity, "
        f"{estimate.fair_share:.0%} fair share, {pot_odds:.0%} immediate price, "
        f"{estimate.samples} weighted range samples"
    )
