from stud_sim.agents import AgentDecision
from stud_sim.game import Seat, StudTable
from stud_sim.interactive import InteractiveStudHand


class PassiveAgent:
    def decide(self, request):
        if "check" in request.legal_actions:
            return AgentDecision("check", "test passive")
        if "call" in request.legal_actions:
            return AgentDecision("call", "test passive")
        return AgentDecision("fold", "test passive")


def test_play_hand_completes_and_awards_pot() -> None:
    seats = [Seat(name=f"Seat {index}", agent=PassiveAgent()) for index in range(6)]
    table = StudTable(seats, seed=11)

    result = table.play_hand()

    assert result.winner
    assert result.pot > 0
    assert any("wins" in line for line in result.log)


def test_third_street_completion_targets_small_bet() -> None:
    seats = [Seat(name=f"Seat {index}", agent=PassiveAgent()) for index in range(6)]
    table = StudTable(seats, seed=11)

    assert table._raise_target("third", current_bet=2, bet_unit=4) == 4
    assert table._raise_target("third", current_bet=4, bet_unit=4) == 8


def test_interactive_hand_pauses_for_human_action() -> None:
    hand = InteractiveStudHand(players=6, human_seat=0, seed=7)

    state = hand.start()

    assert state["hand_id"] == hand.id
    assert state["pending_decision"] or state["complete"]
    if state["pending_decision"]:
        action = state["pending_decision"]["legal_actions"][0]
        next_state = hand.act(action)
        assert next_state["hand_id"] == hand.id
        assert next_state["last_decision_review"]
