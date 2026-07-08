# 7-Card Stud $4/$8 Limit Poker: Probability Study Notes

## Purpose

This note is a math-first framework for learning $4/$8 limit 7-card stud. The goal is to make each decision by estimating:

- hand probabilities,
- opponent ranges,
- Bayesian updates from exposed cards and betting,
- equity against likely hands,
- pot odds and cost to continue,
- expected value.

It is not a complete strategy chart. It is a way to think clearly at the table.

## Game Structure

Baseline assumption for these notes: the game starts six-handed with whole-number betting amounts.

For these notes, use this structure:

- $1 ante from each player,
- $2 bring-in,
- $4 small bet on third and fourth street,
- $8 big bet on fifth, sixth, and seventh street.

The deal and betting sequence:

- Each player antes before the cards are dealt.
- Each player receives two downcards and one upcard on third street.
- The lowest upcard usually posts the $2 bring-in.
- Another player may complete the third-street bet to $4.
- Bets are $4 on third and fourth street.
- Bets are $8 on fifth, sixth, and seventh street.
- Seventh street is dealt face down.

Six-handed, the starting pot is:

```text
6 antes * $1 = $6
$2 bring-in = $2
pot after bring-in = $8
```

If a player completes to $4, the bring-in player has already posted $2 and needs to call $2 more.

## Six-Handed Baseline

Starting six-handed matters because there are fewer opponents than in a full ring stud game, but still enough exposed cards to make dead-card tracking valuable.

At the start of third street:

- 6 players are dealt 3 cards each,
- 18 total cards are out of the deck,
- you know your 3 cards,
- you can see 5 opponent door cards,
- 10 opponent hole cards are unknown.

This means your first estimate is always incomplete. You can see enough to judge whether your hand is live, but not enough to know exactly how many blockers are hidden.

Six-handed effects:

- antes matter more because the pot is contested by fewer players,
- steals and resteals become more important,
- high cards gain value,
- buried pairs can be strong because they are concealed,
- weak low pairs and dead draws still become expensive quickly,
- visible dead cards are especially important because every exposed card represents a larger share of the table.

For these notes, assume all probability and equity estimates begin from a six-handed deal unless stated otherwise.

## Information Available

Stud is an information-rich poker game because many cards are exposed. On every street, track:

- your hidden cards,
- your exposed cards,
- all folded exposed cards,
- all active opponents' exposed cards,
- betting actions,
- position relative to the bettor,
- number of players still in the hand,
- pot size,
- future betting cost.

Dead cards are central. A dead card is any card you have seen that cannot help you or an opponent later.

Example:

If you start with three hearts and four other hearts are already exposed or folded, your flush draw is much weaker than it looks.

## Basic Probability Ideas

### Outs

An out is an unseen card that improves your hand enough to matter.

Approximate probability of improving on the next card:

```text
outs / unseen cards
```

In stud, unseen cards are not always `52 - known cards`, because opponents have hidden cards. However, for practical table estimates, known exposed cards should be removed from the deck.

### Dead Outs

Do not count exposed cards as outs.

If you have four to a flush on fifth street, there are normally 9 cards of that suit left in the deck. But if 4 cards of that suit are already visible elsewhere, you may only have 5 live flush outs.

### Dirty Outs

Some outs improve you but may still leave you second best.

Example:

You are drawing to two pair while an opponent shows three suited cards and likely has a flush draw. Pairing may help, but it may not be enough by showdown.

## Bayesian Thinking

Bayesian poker reasoning means updating your belief after each new piece of evidence.

Use this structure:

```text
prior belief + new evidence = updated belief
```

### Prior Belief

Before betting action, estimate likely starting hands from exposed cards and position.

Examples:

- A player completes with an ace up: likely strong pair, three high cards, three-flush, or steal.
- A tight player calls a completion with a low door card: often a pair, live draw, or concealed strength.
- A loose player calls with weak exposed cards: range is wider.

### Evidence

Evidence includes:

- exposed cards,
- who bet,
- who called,
- who raised,
- whether scary cards appeared,
- whether an opponent keeps betting into resistance,
- whether their board connects logically.

### Updated Belief

After each street, ask:

- What hands does their betting represent?
- What hands are consistent with their exposed cards?
- What hands are now less likely?
- Did their new card improve their visible board?
- Are they betting because they improved, because they already had strength, or because they are representing?

Example:

An opponent starts with `K` up, completes, then catches `K` on fourth and bets. Your updated belief should heavily weight trip kings or at least split kings. If one king was already dead on third street, trips become less likely, but still possible.

## Equity

Equity is your share of the pot if the hand were checked down from the current point.

```text
equity = probability you win at showdown
```

If the pot is $40 and your equity is 25%, your theoretical share is:

```text
$40 * 0.25 = $10
```

Equity depends on:

- your current made hand,
- your drawing potential,
- dead cards,
- number of opponents,
- opponent ranges,
- chance of future betting,
- reverse implied odds.

In multiway stud pots, weak one-pair hands often lose equity quickly. Strong live draws and hands that can improve to hidden monsters gain value.

## Pot Odds

Pot odds compare the cost to call with the current pot.

```text
pot odds = call cost / (pot after you call)
```

Example:

The pot is $40. It costs $4 to call.

```text
call cost = $4
pot after call = $44
required equity = 4 / 44 = 9.1%
```

You need more than 9.1% equity for a call to show immediate profit, ignoring future betting.

## Cost To Continue

Stud decisions are not just one-card decisions. A cheap call on fourth street can lead to expensive calls on fifth and sixth street.

On third and fourth street, bets are small: $4.

On fifth street and later, bets are big: $8.

Before calling, estimate:

- cost to call now,
- chance you will face more bets,
- cost of future streets,
- chance you will be forced to fold later,
- chance your improvement will be obvious and kill action,
- chance your improvement will still be second best.

Example:

Calling $4 on fourth with a weak backdoor draw may look cheap, but if you often have to call $8 on fifth and $8 on sixth, the real cost is much higher.

## Expected Value

Expected value estimates the average profit or loss of a decision.

Simple call EV:

```text
EV(call) = equity * final pot - cost to continue
```

This is simplified because final pot size is uncertain. A more practical version is:

```text
EV(call) = chance of winning * money won - chance of losing * money lost
```

Example:

You estimate:

- 25% chance to win,
- $40 final pot when you win,
- $8 more total cost when you lose.

```text
EV = 0.25 * 40 - 0.75 * 8
EV = 10 - 6
EV = +$4
```

This would be a profitable continue if your assumptions are accurate.

## Street-By-Street Questions

### Third Street

Ask:

- Are my cards live?
- Do I have a pair, three-flush, three-straight, or high-card strength?
- Are my key ranks dead?
- Are my suit cards dead?
- Who has higher upcards behind me?
- Can I steal the antes?
- If I call, am I likely to be raised?

Most important concept: start with live cards.

### Fourth Street

Ask:

- Did I improve?
- Did my opponent improve visibly?
- Is my draw still live?
- Is the pot multiway or heads-up?
- Is the bet still cheap enough to peel?

Fourth street is often where speculative hands either gain enough equity or should be released.

### Fifth Street

Ask:

- Am I willing to pay big bets now?
- Did the board texture change?
- Is my hand strong enough to continue against the likely range?
- If drawing, are my outs live and clean?
- Can I win extra bets if I hit?

Fifth street is the major commitment point because the bet size doubles.

### Sixth Street

Ask:

- What is my current equity?
- What final-card outs do I have?
- Is the pot large enough to call?
- Can I raise for value?
- Am I drawing dead or nearly dead?

By sixth street, pot odds may justify calls with live draws, but weak made hands can be very expensive.

### Seventh Street

Ask:

- What hands can my opponent have given the full betting line?
- What worse hands call if I bet?
- What better hands fold if I bet?
- If facing a bet, how often is this a bluff?
- Is the pot large enough to make a crying call?

In limit poker, large pots often justify thin river calls because the price is fixed.

## Practical Table Method

For each decision, run this checklist:

1. Count the pot.
2. Count the cost to call.
3. Count your live outs.
4. Discount dirty outs.
5. Estimate opponent ranges from exposed cards and betting.
6. Estimate your equity.
7. Compare equity to pot odds.
8. Consider future big-bet costs.
9. Choose fold, call, bet, or raise.

## Simple Study Exercises

After each session, record hands in this format:

```text
Street:
Pot size:
Cost to call:
Your hand:
Your board:
Opponent boards:
Dead cards:
Estimated outs:
Estimated equity:
Decision:
Result:
Review:
```

Then ask:

- Did I count dead cards correctly?
- Did I overcount dirty outs?
- Did I call small bets that forced bad big-bet decisions later?
- Did I fold hands with enough pot odds?
- Did I update opponent ranges after new evidence?

## Core Lesson

Good 7-card stud decisions come from combining visible-card probability with betting-line inference.

The strongest habit to build is this:

```text
Do not ask only "Do I like my hand?"
Ask "Given the pot, live cards, opponent range, and future cost, is this decision profitable?"
```
