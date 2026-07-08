from __future__ import annotations

import argparse
import json
import sys
import traceback
from typing import Any, Callable

from .agents import RangeEquityStudAgent
from .cards import Card, card_list
from .evaluator import best_hand, hand_name
from .game import Seat, StudTable
from .interactive import InteractiveStudHand

HANDS: dict[str, InteractiveStudHand] = {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the 7-card stud MCP server over stdio.")
    parser.parse_args()
    server = MCPServer()
    server.serve()


class MCPServer:
    def __init__(self) -> None:
        self.handlers: dict[str, Callable[[dict[str, Any]], Any]] = {
            "initialize": self.initialize,
            "tools/list": self.tools_list,
            "tools/call": self.tools_call,
            "ping": lambda _params: {},
        }

    def serve(self) -> None:
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                message = json.loads(line)
                response = self.handle(message)
            except Exception as error:
                response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": str(error), "data": traceback.format_exc()},
                }
            if response is not None:
                sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
                sys.stdout.flush()

    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = message.get("method")
        if method and method.startswith("notifications/"):
            return None
        handler = self.handlers.get(method)
        if not handler:
            return self.error(message.get("id"), -32601, f"unknown method: {method}")
        try:
            result = handler(message.get("params") or {})
            return {"jsonrpc": "2.0", "id": message.get("id"), "result": result}
        except ValueError as error:
            return self.error(message.get("id"), -32602, str(error))

    def error(self, request_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    def initialize(self, _params: dict[str, Any]) -> dict[str, Any]:
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "stud-sim", "version": "0.1.0"},
        }

    def tools_list(self, _params: dict[str, Any]) -> dict[str, Any]:
        return {
            "tools": [
                {
                    "name": "stud_play_hand",
                    "description": "Simulate one complete 7-card stud hand with local range-equity opponents.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "players": {"type": "integer", "minimum": 2, "maximum": 8, "default": 6},
                            "seed": {"type": "integer"},
                        },
                    },
                },
                {
                    "name": "stud_start_interactive_hand",
                    "description": "Start a hand where the human controls one seat and opponents act locally.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "players": {"type": "integer", "minimum": 2, "maximum": 8, "default": 6},
                            "human_seat": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 8,
                                "default": 1,
                                "description": "One-based seat number controlled by the human player.",
                            },
                            "seed": {"type": "integer"},
                        },
                    },
                },
                {
                    "name": "stud_act",
                    "description": "Submit the human player's pending action for an interactive hand.",
                    "inputSchema": {
                        "type": "object",
                        "required": ["hand_id", "action"],
                        "properties": {
                            "hand_id": {"type": "string"},
                            "action": {"type": "string", "enum": ["fold", "check", "call", "bet", "raise"]},
                        },
                    },
                },
                {
                    "name": "stud_get_hand",
                    "description": "Return the current state and log for an interactive hand.",
                    "inputSchema": {
                        "type": "object",
                        "required": ["hand_id"],
                        "properties": {"hand_id": {"type": "string"}},
                    },
                },
                {
                    "name": "stud_evaluate_cards",
                    "description": "Evaluate the best five-card poker hand from 5 to 7 cards like As Kd Qh Jc Ts.",
                    "inputSchema": {
                        "type": "object",
                        "required": ["cards"],
                        "properties": {"cards": {"type": "string"}},
                    },
                },
            ]
        }

    def tools_call(self, params: dict[str, Any]) -> dict[str, Any]:
        name = params.get("name")
        arguments = params.get("arguments") or {}
        tools: dict[str, Callable[[dict[str, Any]], Any]] = {
            "stud_play_hand": tool_play_hand,
            "stud_start_interactive_hand": tool_start_interactive_hand,
            "stud_act": tool_act,
            "stud_get_hand": tool_get_hand,
            "stud_evaluate_cards": tool_evaluate_cards,
        }
        tool = tools.get(name)
        if not tool:
            raise ValueError(f"unknown tool: {name}")
        result = tool(arguments)
        return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}


def tool_play_hand(arguments: dict[str, Any]) -> dict[str, Any]:
    players = int(arguments.get("players", 6))
    seed = arguments.get("seed")
    if seed is not None:
        seed = int(seed)
    seats = [
        Seat(name=f"Seat {index + 1}", agent=RangeEquityStudAgent(f"Seat {index + 1}", seed=(seed or 0) + index))
        for index in range(players)
    ]
    table = StudTable(seats=seats, seed=seed)
    result = table.play_hand()
    return {"winner": result.winner, "pot": result.pot, "log": result.log}


def tool_start_interactive_hand(arguments: dict[str, Any]) -> dict[str, Any]:
    players = int(arguments.get("players", 6))
    human_seat = int(arguments.get("human_seat", 1)) - 1
    seed = arguments.get("seed")
    if seed is not None:
        seed = int(seed)
    hand = InteractiveStudHand(players=players, human_seat=human_seat, seed=seed)
    HANDS[hand.id] = hand
    return hand.start()


def tool_act(arguments: dict[str, Any]) -> dict[str, Any]:
    hand = _get_hand(str(arguments.get("hand_id", "")))
    return hand.act(str(arguments.get("action", "")))


def tool_get_hand(arguments: dict[str, Any]) -> dict[str, Any]:
    hand = _get_hand(str(arguments.get("hand_id", "")))
    return hand.snapshot()


def tool_evaluate_cards(arguments: dict[str, Any]) -> dict[str, Any]:
    cards = [_parse_card(token) for token in str(arguments["cards"]).split()]
    score, chosen = best_hand(cards)
    return {"hand": hand_name(score), "score": score, "best_cards": card_list(list(chosen))}


def _get_hand(hand_id: str) -> InteractiveStudHand:
    hand = HANDS.get(hand_id)
    if not hand:
        raise ValueError(f"unknown hand_id: {hand_id}")
    return hand


def _parse_card(token: str) -> Card:
    token = token.strip()
    if len(token) != 2:
        raise ValueError(f"invalid card: {token}")
    rank = token[0].upper()
    suit = token[1].lower()
    suit_aliases = {"♣": "c", "♦": "d", "♥": "h", "♠": "s"}
    suit = suit_aliases.get(suit, suit)
    if rank not in "23456789TJQKA" or suit not in "cdhs":
        raise ValueError(f"invalid card: {token}")
    return Card(rank, suit)


if __name__ == "__main__":
    main()
