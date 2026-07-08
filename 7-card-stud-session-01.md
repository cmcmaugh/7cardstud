# 7-Card Stud Session 01: Six-Handed $4/$8 Study

## Baseline Game

Use this structure for all examples unless stated otherwise:

```text
Game:       6-handed $4/$8 limit 7-card stud
Ante:       $1 from each player
Bring-in:   $2
Small bet:  $4 on 3rd and 4th street
Big bet:    $8 on 5th, 6th, and 7th street
```

Six-handed starting pot:

```text
6 antes * $1 = $6
$2 bring-in = $2
Pot after bring-in = $8
```

Third-street betting sequence:

```text
Bring-in:   $2
Complete:   $4
Raise:      $8
Re-raise:   $12
Cap:        $16
```

House cap rules can vary, but this is the working model.

## Core EV Formula

For a call:

```text
EV(call) = equity * pot after call - call cost
```

Example:

```text
Pot before call = $12
Call cost = $4
Pot after call = $16
Equity = 60%

EV(call) = 0.60 * $16 - $4
EV(call) = $9.60 - $4
EV(call) = +$5.60
```

Required equity:

```text
required equity = call cost / pot after call
```

Example:

```text
Call cost = $4
Pot after call = $16
Required equity = 4 / 16 = 25%
```

## Branch EV

When opponents still act, use branches:

```text
EV(action) =
P(branch 1) * EV(branch 1)
+ P(branch 2) * EV(branch 2)
+ P(branch 3) * EV(branch 3)
```

Branch probabilities should come from ranges:

```text
P(branch) =
weighted hands taking that action / total weighted hands in current range
```

The practical progression is:

```text
card probabilities
-> opponent ranges
-> action ranges
-> branch probabilities
-> EV
```

## Scenario 1: Concealed Kings Against Ace-Up Completion

Third street:

```text
Seat 1:  [?] [?]  3♣
Seat 2:  [?] [?]  J♦
Seat 3:  [?] [?]  7♠
Seat 4:  [?] [?]  A♥
Seat 5:  [?] [?]  9♣
You:     K♠ K♦  6♥
```

Action:

```text
Seat 1 brings in for $2.
Seat 2 folds.
Seat 3 folds.
Seat 4 completes to $4.
Seat 5 folds.
Action is on you.
```

Pot before your decision:

```text
Antes:       $6
Bring-in:    $2
Completion:  $4
Pot:        $12
```

Cost to call:

```text
$4
```

Pot after call:

```text
$16
```

Required equity:

```text
4 / 16 = 25%
```

Raw chance Seat 4 has split aces:

```text
P(at least one hidden ace)
= 1 - (41/44 * 40/43)
= 13.3%
```

After Seat 4 completes with `A♥` showing, update upward. The exact posterior depends on the completion range. Against an optimal player, the range includes more than split aces:

```text
split aces
buried premium pairs
live medium/high pairs
three-flushes
three-straights
three broadway cards
steals when remaining boards are weak
```

Decision:

```text
Raise is the best default.
```

Reason:

```text
You have concealed KK.
No kings are dead.
Only one ace is visible.
Seat 4's completion range is wider than split aces.
Seat 1 has shown only forced bring-in strength.
Calling is profitable, but raising likely has higher EV.
```

If you estimate your equity at 60%, call EV is:

```text
EV(call) = 0.60 * $16 - $4
EV(call) = +$5.60
```

If you raise to $8 and Seat 4 re-raises to $12, assume Seat 1 folds.

Pot after Seat 4 re-raises:

```text
Original pot:       $12
Your raise:          $8
Seat 4 extra raise:  $8
Pot:                $28
```

Cost for you to call:

```text
$4
```

Pot after call:

```text
$32
```

Against exactly split aces, concealed kings are about:

```text
~33% equity
```

Against a balanced optimal re-raise range:

```text
~35% to ~40% equity
```

Using 35%:

```text
EV(call re-raise) = 0.35 * $32 - $4
EV = $11.20 - $4
EV = +$7.20
```

This is the EV of the additional $4 call only. It is not the EV of the entire raise line from the original decision.

If instead you cap to $16 and Seat 4 calls:

```text
Current pot:       $28
Your cap cost:      $8
Seat 4 call:        $4
Final pot:         $40
```

Using 35% equity:

```text
EV(cap) = 0.35 * $40 - $8
EV(cap) = $14.00 - $8
EV(cap) = +$6.00
```

Calling the re-raise:

```text
EV(call) = +$7.20
```

So with 35% equity:

```text
Call the re-raise; do not cap.
```

Incremental cap shortcut:

```text
incremental EV = equity * extra pot created - extra cost
incremental EV = 0.35 * $8 - $4
incremental EV = -$1.20
```

You need 50% equity for the extra raise to break even if called.

## Scenario 2: Split Aces Against King-Up Completion

Third street:

```text
Seat 1:  [?] [?]  2♦
Seat 2:  [?] [?]  Q♣
Seat 3:  [?] [?]  8♥
Seat 4:  [?] [?]  K♠
Seat 5:  [?] [?]  5♣
You:     A♦ 9♦  A♣
```

Action:

```text
Seat 1 brings in for $2.
Seat 2 folds.
Seat 3 folds.
Seat 4 completes to $4.
Seat 5 folds.
Action is on you.
```

Seat 4's pure steal math:

```text
Pot before completion = $8
Completion cost = $4

Required fold frequency for zero-equity steal:
4 / (4 + 8) = 33.3%
```

If called by one player:

```text
Final third-street pot = $16
Required equity = 4 / 16 = 25%
```

From Seat 4's perspective, your raw chance of split aces with `A♣` showing:

```text
P(at least one hidden ace)
= 1 - (41/44 * 40/43)
= 13.3%
```

If Seat 4 does not have a hidden ace, likely made-hand completions include:

```text
split kings
buried QQ
buried JJ
possibly buried TT
```

Before Seat 4 completes, buried JJ with `K♠` showing has roughly this equity against your raw ace-up hand:

```text
vs random A-up hidden cards: ~66%
vs actual split aces:        ~36%
vs no hidden ace:            ~71%
```

Your equity after Seat 4 completes should be estimated against his completion range, not against one exact hand.

Approximate equities for your `A♦ 9♦ A♣`:

```text
vs split kings:        ~68%
vs buried QQ:          ~69%
vs buried JJ:          ~70%
vs buried TT:          ~71%
vs strong three-flush: ~58% to ~65%
vs high-card KQJ:      ~70%+
```

Working estimate:

```text
Your equity after Seat 4 completes: ~65% to ~70%
Use about 68%.
```

Raise is correct.

But equity advantage does not mean raise EV is enormously higher than call EV.

Call EV at 68%:

```text
EV(call) = 0.68 * $16 - $4
EV(call) = $10.88 - $4
EV(call) = +$6.88
```

Raise-call branch at 68%:

```text
Final pot = $24
EV(raise) = 0.68 * $24 - $8
EV(raise) = $16.32 - $8
EV(raise) = +$8.32
```

Incremental value of raising over calling:

```text
0.68 * $8 - $4 = +$1.44
```

So raise is correct, but the immediate EV edge over calling may be only around $1-$2 in a simple branch.

## Scenario 3: Three-Flush / Three-Straight Against King-Up Completion

Third street:

```text
Seat 1:  [?] [?]  4♣
Seat 2:  [?] [?]  Q♥
Seat 3:  [?] [?]  8♠
Seat 4:  [?] [?]  6♦
Seat 5:  [?] [?]  K♣
You:     9♥ T♥  J♥
```

Action:

```text
Seat 1 brings in for $2.
Seat 2 folds.
Seat 3 folds.
Seat 4 folds.
Seat 5 completes to $4.
Action is on you.
```

Pot before your decision:

```text
$12
```

Cost to call:

```text
$4
```

Required equity:

```text
4 / 16 = 25%
```

Your hand:

```text
three-flush
three-straight
three cards to a straight flush
```

Visible dead cards hurt part of the draw:

```text
Q♥ is dead to the heart flush.
8♠ is dead to straight possibilities.
K♣ is dead to straight possibilities.
```

Flush outs:

```text
13 hearts total
- 3 hearts in your hand
- 1 visible dead heart
= 9 live hearts
```

Decision:

```text
Call is the best default.
```

Reason:

```text
You likely have enough equity to continue.
You do not yet have a made hand.
If Seat 5 has split kings, he is unlikely to fold.
If raised/re-raised, your draw becomes more expensive.
```

## Scenario 4: Buried Sixes With King Door Against Ace-Up Completion

Third street:

```text
Seat 1:  [?] [?]  2♠
Seat 2:  [?] [?]  A♦
Seat 3:  [?] [?]  7♣
Seat 4:  [?] [?]  Q♠
Seat 5:  [?] [?]  9♦
You:     6♣ 6♥  K♥
```

Action:

```text
Seat 1 brings in for $2.
Seat 2 completes to $4.
Seat 3 folds.
Seat 4 folds.
Seat 5 folds.
Action is on you.
```

Pot before decision:

```text
$12
```

Cost to call:

```text
$4
```

Required equity:

```text
4 / 16 = 25%
```

Your hand:

```text
buried low pair
king door card
no sixes dead
```

Important range correction:

Seat 2 is not completing on "single ace" as a made hand. Everyone with an ace door has a visible ace. The question is what hidden-card range an optimal player completes with `A♦` showing.

Seat 2 completion range:

```text
split aces
buried pairs
three high cards
three-flushes
three-straights
steals when profitable
```

Approximate hero equity with `6♣ 6♥ K♥`:

```text
vs split aces:       ~35%
vs buried QQ:        ~44%
vs buried JJ/TT:     ~41%
vs live 3-flush:     ~54%
vs random A-up hand: ~60%
```

Working estimate against Seat 2's completion range:

```text
~40% to ~45%
Use about 42%.
```

Call EV at 42%:

```text
EV(call) = 0.42 * $16 - $4
EV(call) = $6.72 - $4
EV(call) = +$2.72
```

Decision:

```text
Call is reasonable/default.
Raise is ambitious unless you expect meaningful fold equity or a wide completion range.
```

## Scenario 5: Buried Queens As Bring-In Against Ace-Up Completion

Third street:

```text
Seat 1:  [?] [?]  5♦
Seat 2:  [?] [?]  J♣
Seat 3:  [?] [?]  3♥
Seat 4:  [?] [?]  A♠
Seat 5:  [?] [?]  8♦
You:     Q♦ Q♠  2♣
```

Action:

```text
You bring in for $2.
Seat 1 folds.
Seat 2 folds.
Seat 3 folds.
Seat 4 completes to $4.
Seat 5 folds.
Action returns to you.
```

Pot before your decision:

```text
Antes:          $6
Your bring-in:  $2
Seat 4:         $4
Pot:           $12
```

You have already posted:

```text
$2
```

Cost to call:

```text
$2 more
```

Pot after call:

```text
$14
```

Required equity:

```text
2 / 14 = 14.3% = 1/7
```

So folding is clearly wrong.

Seat 4's completion range with `A♠` showing should be fairly wide:

```text
split aces
buried premium pairs: KK, QQ, JJ, TT
live medium pairs
live three-flushes
strong three-straights
three broadway cards
ace-up steals / semi-steals
```

Reasons his range is wide:

```text
He has the highest visible card.
Several players already folded.
You show the weak bring-in card.
He can win the antes immediately.
His ace door card has strong fold equity.
```

Approximate Seat 4 equity against your actual buried queens:

```text
If he has split aces:      ~68%
If he has buried KK:       ~67%
If he has buried JJ:       ~41%
If he has buried TT:       ~46%
If he has a spade 3-flush: ~41%
If he has random A-up:     ~36%
```

Against a plausible wide ace-up completion range:

```text
Seat 4 equity: ~50% to ~55%
Your equity:   ~45% to ~50%
```

Decision:

```text
Call is trivially profitable.
Raise is usually the better default because your queens are live and hidden.
```

Reasons to raise:

```text
Your pair is concealed.
No queens are dead.
Seat 4's completion range is wider than split aces.
You punish steals and weaker made hands.
You may force Seat 4 to define his hand.
```

## Study Habits From This Session

Do not ask only:

```text
Do I have enough equity to call?
```

Also ask:

```text
Is raising better than calling?
What worse hands continue?
What better hands re-raise?
Can I win immediately?
How does the opponent's range change after each action?
```

Keep ranges separate:

```text
completion range
call-a-raise range
re-raise range
cap range
```

Common correction:

```text
Split aces are in an ace-up completion range.
But after you raise, split aces may move from the call range into the re-raise range.
```

