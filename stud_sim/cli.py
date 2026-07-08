from __future__ import annotations

import argparse
import os
from pathlib import Path

from .agents import FallbackStudAgent, RangeEquityStudAgent
from .game import Seat, StudTable
from .openai_agent import ChatGPTStudAgent


def _load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a 7-card stud simulation.")
    parser.add_argument("--hands", type=int, default=1)
    parser.add_argument("--players", type=int, default=6)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--openai-opponents", action="store_true")
    parser.add_argument("--strict-openai", action="store_true")
    parser.add_argument("--model", default="gpt-5-mini")
    args = parser.parse_args()

    _load_dotenv()

    if not 2 <= args.players <= 8:
        raise SystemExit("--players must be between 2 and 8")

    seats = []
    for index in range(args.players):
        name = f"Seat {index + 1}"
        if args.openai_opponents:
            openai_agent = ChatGPTStudAgent(name=name, model=args.model)
            fallback = RangeEquityStudAgent(name=name, seed=(args.seed or 0) + index)
            agent = openai_agent if args.strict_openai else FallbackStudAgent(openai_agent, fallback)
        else:
            agent = RangeEquityStudAgent(name=name, seed=(args.seed or 0) + index)
        seats.append(Seat(name=name, agent=agent))

    for hand_number in range(1, args.hands + 1):
        table = StudTable(seats=seats, seed=None if args.seed is None else args.seed + hand_number - 1)
        result = table.play_hand()
        print(f"\n=== Hand {hand_number}: {result.winner} wins ${result.pot} ===")
        for line in result.log:
            print(line)


if __name__ == "__main__":
    main()
