# 7-Card Stud Simulator

This is a small CLI and browser simulator for six-handed $4/$8 limit 7-card stud. The table engine is local and deterministic enough to test, while computer seats use range-equity decisions based on live cards, pot odds, board texture, betting history, and weighted opponent ranges.

## Run locally

```bash
python3 -m stud_sim.cli --hands 1 --seed 7
```

By default the opponents use local range-equity agents.

## Play in a browser

Run the local HTTP server:

```bash
python3 -m stud_sim.http_server --host 127.0.0.1 --port 8080
```

Then open:

```text
http://127.0.0.1:8080
```

The browser UI starts interactive hands, shows your private and exposed cards, and offers the legal actions for each decision. The JSON API is:

- `POST /hands`: start an interactive hand.
- `GET /hands/{hand_id}`: inspect a hand.
- `POST /hands/{hand_id}/actions`: submit `fold`, `check`, `call`, `bet`, or `raise`.

## Easy Local Launch

For someone playing locally, install Python 3 and download this project.

On Windows, double-click:

```text
play-poker.bat
```

On macOS or Linux, run:

```bash
./play-poker.sh
```

If the shell script is not executable yet:

```bash
chmod +x play-poker.sh
./play-poker.sh
```

The launcher picks a free local port, starts the game, and opens the browser automatically.

## In-Browser Pyodide Version

There is also an experimental static version that runs the Python game engine in the browser with Pyodide.

Run it locally with:

```bash
python3 run_pyodide.py
```

Or serve the repo root with any static server and open:

```text
/pyodide/
```

This version keeps the Python game logic, avoids Render cold starts, and can be hosted as static files. It downloads Pyodide from the official CDN, so the first page load is larger than the server-backed version.

To host it on GitHub Pages, enable Pages for the repository and open:

```text
https://cmcmaugh.github.io/7cardstud/pyodide/
```

## Deploy on Render

The included `render.yaml` defines a free Python web service. Render provides the `PORT` environment variable; the service starts with:

```bash
python3 -m stud_sim.http_server --host 0.0.0.0 --port $PORT
```

To deploy:

1. Push this project to a GitHub repository.
2. In Render, create a new Blueprint or Web Service from that repository.
3. If using the blueprint, Render will read `render.yaml`.
4. Open the generated `*.onrender.com` URL.

Game state is currently in memory, so a Render restart resets active hands and bankrolls.

## Run with OpenAI-backed opponents

Set an API key and enable the OpenAI agent adapter:

```bash
export OPENAI_API_KEY=...
python3 -m stud_sim.cli --hands 1 --seed 7 --openai-opponents --model gpt-5-mini
```

Each opponent gets its own `ChatGPTStudAgent` instance. The adapter stores the previous OpenAI response id per seat when the API returns one, so later streets continue that opponent's session context.

The OpenAI adapter is intentionally isolated in `stud_sim/openai_agent.py`; the simulator can be extended with richer table context or a different model without touching the game engine.

## Run as an MCP server

The MCP server runs over stdio and exposes tools an MCP client can call:

- `stud_play_hand`: simulate a complete local hand.
- `stud_start_interactive_hand`: start a hand where the human controls one seat.
- `stud_act`: submit the human player's next action for that hand.
- `stud_get_hand`: inspect an interactive hand.
- `stud_evaluate_cards`: evaluate 5 to 7 cards.

Run it directly with:

```bash
python3 -m stud_sim.mcp_server
```

Add it to an MCP client config with an absolute working directory path:

```toml
[mcp_servers.stud_sim]
command = "python3"
args = ["-m", "stud_sim.mcp_server"]
cwd = "/home/conor/projects/poker"
```

The client receives a `pending_decision` containing the human player's private cards, exposed cards, legal actions, pot, and table state, then can call `stud_act` with `fold`, `check`, `call`, `bet`, or `raise`.
