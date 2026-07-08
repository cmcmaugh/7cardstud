from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from .interactive import InteractiveStudHand

HANDS: dict[str, InteractiveStudHand] = {}
HAND_SESSIONS: dict[str, "GameSession"] = {}


@dataclass
class GameSession:
    players: int
    human_seat: int
    seed: int | None
    hand_number: int
    bankrolls: list[int]

    def next_seed(self) -> int | None:
        if self.seed is None:
            return None
        return self.seed + self.hand_number - 1


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>7-Card Stud</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #121416;
      color: #f3f0e8;
    }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: #121416; }
    button, input, select { font: inherit; }
    .app { max-width: 1120px; margin: 0 auto; padding: 24px; }
    header { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 18px; }
    h1 { margin: 0; font-size: 26px; line-height: 1.1; }
    .controls { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .toolbar { display: flex; gap: 8px; flex-wrap: wrap; margin: 16px 0; min-height: 44px; }
    button {
      border: 1px solid #4f5d56;
      border-radius: 7px;
      color: #f8f5ec;
      background: #26352e;
      min-height: 40px;
      padding: 0 14px;
      cursor: pointer;
    }
    button.primary { background: #b9412f; border-color: #de705f; }
    button:disabled { opacity: .45; cursor: not-allowed; }
    input, select {
      background: #1c2022;
      color: #f3f0e8;
      border: 1px solid #4f5d56;
      border-radius: 7px;
      min-height: 40px;
      padding: 0 10px;
      width: 92px;
    }
    main { display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 18px; }
    .table {
      min-height: 560px;
      border: 1px solid #3c4a43;
      border-radius: 8px;
      background: radial-gradient(ellipse at center, #1f6a47 0%, #164d37 58%, #123629 100%);
      padding: 18px;
      position: relative;
    }
    .status { display: flex; justify-content: space-between; gap: 12px; color: #e7dcc8; margin-bottom: 14px; }
    .seats {
      position: relative;
      min-height: 500px;
      margin-top: 8px;
    }
    .table-felt {
      position: absolute;
      inset: 86px 118px 86px;
      border: 1px solid rgba(243,240,232,.22);
      border-radius: 999px;
      background: rgba(3, 17, 12, .28);
      box-shadow: inset 0 0 60px rgba(0,0,0,.22);
      pointer-events: none;
    }
    .seat {
      border: 1px solid rgba(243,240,232,.24);
      border-radius: 8px;
      background: rgba(11, 19, 16, .66);
      padding: 12px;
      min-height: 126px;
      width: clamp(176px, 26%, 230px);
      position: absolute;
      transform: translate(-50%, -50%);
    }
    .seat.hero { border-color: #f2c14e; box-shadow: inset 0 0 0 1px rgba(242,193,78,.3); }
    .seat.starter { outline: 2px solid #5fd0a5; outline-offset: -4px; }
    .seat.folded { opacity: .55; }
    .seat h2 { margin: 0 0 8px; font-size: 15px; font-weight: 700; }
    .badges { display: flex; gap: 6px; flex-wrap: wrap; min-height: 22px; margin-bottom: 6px; }
    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 20px;
      border-radius: 999px;
      padding: 0 8px;
      background: #235b48;
      color: #dff8ed;
      font-size: 12px;
      font-weight: 700;
    }
    .cards { display: flex; gap: 6px; flex-wrap: wrap; min-height: 38px; margin: 8px 0; }
    .card {
      display: inline-grid;
      place-items: center;
      width: 34px;
      height: 46px;
      border-radius: 5px;
      background: #faf8ef;
      color: #191817;
      font-weight: 800;
      font-size: 15px;
      border: 1px solid #d6d0c2;
    }
    .card.red { color: #b92225; }
    .meta { margin: 0; color: #d8d0c2; font-size: 13px; line-height: 1.35; }
    aside { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
    .panel {
      border: 1px solid #333a3d;
      border-radius: 8px;
      background: #1a1d1f;
      padding: 14px;
    }
    .panel h2 { margin: 0 0 10px; font-size: 16px; }
    .decision { color: #f2c14e; font-weight: 700; }
    .thinking {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: #7be0ad;
      font-weight: 700;
    }
    .thinking::before {
      content: "";
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: #7be0ad;
      animation: pulse 900ms ease-in-out infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: .35; transform: scale(.8); }
      50% { opacity: 1; transform: scale(1); }
    }
    .review {
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid #2a3033;
    }
    .review strong.right { color: #7be0ad; }
    .review strong.wrong { color: #ff9a88; }
    .prompt {
      width: 100%;
      min-height: 170px;
      margin-top: 10px;
      padding: 10px;
      resize: vertical;
      border-radius: 7px;
      border: 1px solid #4f5d56;
      background: #111416;
      color: #f3f0e8;
      font: 12px/1.4 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }
    .log {
      margin: 0;
      padding: 0;
      list-style: none;
      max-height: 390px;
      overflow: auto;
      color: #d8d0c2;
      font-size: 13px;
      line-height: 1.45;
    }
    .log li { padding: 7px 0; border-top: 1px solid #2a3033; }
    .error { color: #ff9a88; min-height: 20px; }
    @media (max-width: 840px) {
      .app { padding: 16px; }
      header, main { display: block; }
      .controls { margin-top: 12px; }
      .seats { display: grid; grid-template-columns: 1fr; gap: 12px; min-height: 0; }
      .table-felt { display: none; }
      .seat { position: static; transform: none; width: 100%; }
      aside { margin-top: 16px; }
      .table { min-height: 0; }
    }
  </style>
</head>
<body>
  <div class="app">
    <header>
      <h1>7-Card Stud</h1>
      <div class="controls">
        <button class="primary" id="newHand">Start Hand</button>
        <button id="resetGame">Reset Game</button>
      </div>
    </header>
    <main>
      <section class="table" aria-live="polite">
        <div class="status">
          <strong id="street">No hand</strong>
          <span id="pot">Pot $0</span>
        </div>
        <div class="toolbar" id="actions"></div>
        <div class="seats" id="seats"></div>
      </section>
      <aside>
        <section class="panel">
          <h2>Decision</h2>
          <div id="decision">Start a hand.</div>
          <div class="error" id="error"></div>
        </section>
        <section class="panel">
          <h2>Log</h2>
          <ul class="log" id="log"></ul>
        </section>
      </aside>
    </main>
  </div>
  <script>
    let currentHandId = null;
    let currentComplete = false;
    const $ = (id) => document.getElementById(id);

    function cardNode(text) {
      const span = document.createElement("span");
      span.className = "card" + (text.includes("♥") || text.includes("♦") ? " red" : "");
      span.textContent = text;
      return span;
    }

    function renderCards(container, text) {
      container.textContent = "";
      const cards = text ? text.split(" ").filter(Boolean) : [];
      if (!cards.length) {
        const p = document.createElement("p");
        p.className = "meta";
        p.textContent = "No cards shown";
        container.appendChild(p);
        return;
      }
      cards.forEach((card) => container.appendChild(cardNode(card)));
    }

    function render(state) {
      currentHandId = state.hand_id;
      currentComplete = Boolean(state.complete);
      $("street").textContent = `${state.complete ? "Complete" : state.street} · Hand ${state.hand_number || 1}`;
      $("pot").textContent = `Pot $${state.pot}`;
      $("newHand").style.display = state.complete ? "inline-block" : "none";
      $("newHand").textContent = state.complete ? "Continue" : "Start Hand";
      const pending = state.pending_decision;
      const decision = $("decision");
      decision.textContent = "";
      const current = document.createElement("div");
      current.innerHTML = pending
        ? `<span class="decision">${pending.street}</span><br>${pending.private_cards} / ${pending.exposed_cards}<br>Call $${pending.call_amount}`
        : state.complete ? `Winner: ${state.winner}` : "Waiting";
      decision.appendChild(current);
      if (state.last_decision_review) {
        const review = state.last_decision_review;
        const block = document.createElement("div");
        block.className = "review";
        const verdict = document.createElement("strong");
        verdict.className = review.correct ? "right" : "wrong";
        verdict.textContent = review.correct
          ? `Good decision: ${review.chosen_action}`
          : `Review: chose ${review.chosen_action}, advisor prefers ${review.recommended_action}`;
        block.appendChild(verdict);
        const detail = document.createElement("p");
        detail.className = "meta";
        detail.textContent = review.explanation;
        block.appendChild(detail);
        if (!review.correct && review.prompt) {
          const prompt = document.createElement("textarea");
          prompt.className = "prompt";
          prompt.readOnly = true;
          prompt.value = review.prompt;
          block.appendChild(prompt);
        }
        decision.appendChild(block);
      }

      const actions = $("actions");
      actions.textContent = "";
      (pending ? pending.legal_actions : []).forEach((action) => {
        const button = document.createElement("button");
        const cost = pending.action_costs ? pending.action_costs[action] : 0;
        button.textContent = cost ? `${action} $${cost}` : action;
        button.onclick = () => act(action);
        actions.appendChild(button);
      });

      const seats = $("seats");
      seats.textContent = "";
      const felt = document.createElement("div");
      felt.className = "table-felt";
      seats.appendChild(felt);
      const seatCount = Math.max(state.seats.length, 2);
      state.seats.forEach((seat, index) => {
        const angle = (90 + (index * 360 / seatCount)) * Math.PI / 180;
        const left = 50 + Math.cos(angle) * 36;
        const top = 50 + Math.sin(angle) * 39;
        const section = document.createElement("section");
        section.className = "seat" + (seat.name === "Hero" ? " hero" : "") + (seat.started_current_round ? " starter" : "") + (seat.folded ? " folded" : "");
        section.style.left = `${left}%`;
        section.style.top = `${top}%`;
        const title = document.createElement("h2");
        title.textContent = `${seat.name} · stack $${seat.bankroll}${seat.folded ? " · folded" : ""}`;
        section.appendChild(title);
        const badges = document.createElement("div");
        badges.className = "badges";
        if (seat.started_current_round) {
          const starter = document.createElement("span");
          starter.className = "badge";
          starter.textContent = "acts first";
          badges.appendChild(starter);
        }
        section.appendChild(badges);
        const chips = document.createElement("p");
        chips.className = "meta";
        chips.textContent = `In play: $${seat.in_play || 0}`;
        section.appendChild(chips);
        const exposed = document.createElement("div");
        exposed.className = "cards";
        renderCards(exposed, seat.exposed_cards);
        section.appendChild(exposed);
        if (seat.private_cards) {
          const privateCards = document.createElement("div");
          privateCards.className = "cards";
          renderCards(privateCards, seat.private_cards);
          section.appendChild(privateCards);
        }
        seats.appendChild(section);
      });

      const log = $("log");
      log.textContent = "";
      state.log.forEach((line) => {
        const li = document.createElement("li");
        li.textContent = line;
        log.appendChild(li);
      });
      log.scrollTop = log.scrollHeight;
    }

    async function request(path, options = {}) {
      $("error").textContent = "";
      const response = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || response.statusText);
      return data;
    }

    async function newHand() {
      try {
        if (currentHandId && currentComplete) {
          render(await request(`/hands/${currentHandId}/continue`, { method: "POST", body: "{}" }));
        } else {
          const body = { players: 6, human_seat: 1 };
          render(await request("/hands", { method: "POST", body: JSON.stringify(body) }));
        }
      } catch (error) {
        $("error").textContent = error.message;
      }
    }

    async function resetGame() {
      currentHandId = null;
      currentComplete = false;
      $("newHand").style.display = "inline-block";
      $("newHand").textContent = "Start Hand";
      $("street").textContent = "No hand";
      $("pot").textContent = "Pot $0";
      $("actions").textContent = "";
      $("seats").textContent = "";
      $("log").textContent = "";
      $("decision").textContent = "Start a hand.";
      $("error").textContent = "";
    }

    async function act(action) {
      if (!currentHandId) return;
      try {
        $("actions").textContent = "";
        const waiting = document.createElement("span");
        waiting.className = "thinking";
        waiting.textContent = "Opponents acting";
        $("actions").appendChild(waiting);
        render(await request(`/hands/${currentHandId}/actions`, { method: "POST", body: JSON.stringify({ action }) }));
      } catch (error) {
        $("actions").textContent = "";
        $("error").textContent = error.message;
      }
    }

    $("newHand").onclick = newHand;
    $("resetGame").onclick = resetGame;
  </script>
</body>
</html>
"""


class StudHTTPRequestHandler(BaseHTTPRequestHandler):
    server_version = "StudSimHTTP/0.1"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send_html(INDEX_HTML)
            return

        parts = self._path_parts(path)
        if len(parts) == 2 and parts[0] == "hands":
            hand = HANDS.get(parts[1])
            if not hand:
                self._send_error(HTTPStatus.NOT_FOUND, "unknown hand_id")
                return
            self._send_json(_snapshot_with_session(hand))
            return

        self._send_error(HTTPStatus.NOT_FOUND, "not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/hands":
                self._create_hand(payload)
                return

            parts = self._path_parts(path)
            if len(parts) == 3 and parts[0] == "hands" and parts[2] == "actions":
                self._act(parts[1], payload)
                return
            if len(parts) == 3 and parts[0] == "hands" and parts[2] == "continue":
                self._continue(parts[1])
                return

            self._send_error(HTTPStatus.NOT_FOUND, "not found")
        except ValueError as error:
            self._send_error(HTTPStatus.BAD_REQUEST, str(error))

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _create_hand(self, payload: dict[str, Any]) -> None:
        players = int(payload.get("players", 6))
        human_seat = int(payload.get("human_seat", 1)) - 1
        seed = payload.get("seed")
        if seed in ("", None):
            seed = None
        else:
            seed = int(seed)
        session = GameSession(
            players=players,
            human_seat=human_seat,
            seed=seed,
            hand_number=1,
            bankrolls=[200 for _ in range(players)],
        )
        hand = _start_session_hand(session)
        self._send_json(_snapshot_with_session(hand), HTTPStatus.CREATED)

    def _act(self, hand_id: str, payload: dict[str, Any]) -> None:
        hand = HANDS.get(hand_id)
        if not hand:
            self._send_error(HTTPStatus.NOT_FOUND, "unknown hand_id")
            return
        action = str(payload.get("action", ""))
        self._send_json(_snapshot_with_session(hand, hand.act(action)))

    def _continue(self, hand_id: str) -> None:
        hand = HANDS.get(hand_id)
        session = HAND_SESSIONS.get(hand_id)
        if not hand or not session:
            self._send_error(HTTPStatus.NOT_FOUND, "unknown hand_id")
            return
        if not hand.complete:
            self._send_error(HTTPStatus.BAD_REQUEST, "hand is not complete")
            return

        session.bankrolls = [seat.bankroll for seat in hand.seats]
        session.hand_number += 1
        next_hand = _start_session_hand(session)
        self._send_json(_snapshot_with_session(next_hand), HTTPStatus.CREATED)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("invalid JSON") from error
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def _path_parts(self, path: str) -> list[str]:
        return [part for part in path.strip("/").split("/") if part]

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        self._send_json({"error": message}, status)


def build_server(host: str, port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), StudHTTPRequestHandler)


def _start_session_hand(session: GameSession) -> InteractiveStudHand:
    hand = InteractiveStudHand(
        players=session.players,
        human_seat=session.human_seat,
        seed=session.next_seed(),
    )
    for seat, bankroll in zip(hand.seats, session.bankrolls):
        seat.bankroll = bankroll
    HANDS[hand.id] = hand
    HAND_SESSIONS[hand.id] = session
    hand.start()
    return hand


def _snapshot_with_session(
    hand: InteractiveStudHand,
    snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = dict(snapshot or hand.snapshot())
    session = HAND_SESSIONS.get(hand.id)
    if session:
        state["hand_number"] = session.hand_number
        state["session_bankrolls"] = [seat.bankroll for seat in hand.seats]
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the 7-card stud HTTP server.")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    args = parser.parse_args()

    server = build_server(args.host, args.port)
    print(f"Serving 7-card stud at http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
