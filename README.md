# Foosball Elo System Documentation

[For Full Document](https://docs.google.com/document/d/1HumdWiXkus08E6xCJvwAiqdwlruyd_IbUSk8i8qvNzI/edit?usp=sharing)

[ScoreBoard](https://larryzpl123.github.io/FOOSBALL-ELOSYSTEM/index.html)

## Overview

This documentation provides an overview of a simple foosball Elo system, detailing its components, functionality, and the underlying mathematical principles of the Elo rating algorithm and Fibonacci protection.

### File Structure

- **foosball.py**: The main offline execution file for managing player data and game results.
- **index.html**: The scoreboard displaying player rankings and statistics.
- **2index.html**: The online execution file for real-time updates and interactions.
- **elo.txt**: The database file storing player information and Elo ratings.
- **images**： Other Images

---

### Ranks

Players earn un-droppable ranks based on their Elo scores, categorized as follows:

- **<150**: 1 - Iron
- **≥150**: 2 - Bronze
- **≥200**: 3 - Copper
- **≥250**: 4 - Silver
- **≥450**: 5 - Gold
- **≥850**: 6 - Platinum
- **≥1234**: 7 - Jade
- **≥1650**: 8 - Emerald
- **≥2222**: 9 - Diamond
- **≥2468**: 10 - Master
- **≥2900**: 11 - Ultra

Additionally, the system includes 5 hidden ranks for advanced classifications.

---

## Commands in foosball.py / 2index.html

The following commands are available for interacting with the system:

- `<team1> <winType> <team2>`: Process a regular game result.
- `pp`: Print detailed player statistics, including the highest overall rank.
- `best`: Show the best players based on various performance metrics.
- `name`: Print player names in alphabetical order.
- `combine a to b`: Merge player statistics from one player to another.
- `exit`: Save changes and quit the program.
<br/>
example : pp
<br/><br/>

![pp](/Related%20Documents/pp.png "pp")

---

## Elo Algorithm

### How Elo Works Mathematically

The Elo rating system calculates the relative skill levels of players in two-player games. Here's how it works:

1. **Initial Ratings**: Each player starts with a base rating (typically 1500).
2. **Rating Calculation**: After a match, the new ratings are calculated using the formula:

   \[
   R' = R + K \times (S - E)
   \]

   Where:
   - \( R' \) = new rating
   - \( R \) = current rating
   - \( K \) = development coefficient (a value that determines how much ratings can change, typically between 10 and 40)
   - \( S \) = actual score (1 for a win, 0 for a loss)
   - \( E \) = expected score, calculated as:

   \[
   E = \frac{1}{1 + 10^{((R_{opponent} - R)/400)}}
   \]

   This expected score reflects the probability of winning based on current ratings.

### Fibonacci Protection

Fibonacci protection is a method used to stabilize player ratings and prevent drastic changes due to outlier performances. It introduces a mechanism where the adjustment to a player's rating is limited based on a Fibonacci sequence.

1. **Adjustment Limits**: The maximum adjustment after a game is determined by the Fibonacci numbers, which grow exponentially. This means that as players' ratings increase, their ratings become less volatile.
2. **Mathematics of Fibonacci**: The sequence starts as 0, 1, 1, 2, 3, 5, 8, 13, etc. If a player's current rating is high, the maximum adjustment is limited to the next Fibonacci number below a certain threshold. This protects high-rated players from losing too many points in a single match and stabilizes the overall rating system.

### Score Board

![scoreboard](/Related%20Documents/ScoreBoard.png "ScoreBoard")

### HTML OL

![HTMLOL](/Related%20Documents/htmlol.png "HtmlOl")

---

## Conclusion

This foosball Elo system combines robust player rating mechanics with automatic normalization and ranking features to provide an engaging and fair competition environment. The mathematical principles behind the Elo algorithm and Fibonacci protection ensure that ratings reflect true player skill while minimizing volatility.

[ScoreBoard](https://larryzpl123.github.io/FOOSBALL-ELOSYSTEM/index.html)

[For Full Document](https://docs.google.com/document/d/1HumdWiXkus08E6xCJvwAiqdwlruyd_IbUSk8i8qvNzI/edit?usp=sharing)
