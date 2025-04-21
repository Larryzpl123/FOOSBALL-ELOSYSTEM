Name Normalization & Merging:
“LarryZhong”, “Larry Zhong”, “Larry_Zhong”, etc., are merged automatically.

Ranks:
Besides Elo scores (offense, defense, average), players now earn an un-droppable rank based on thresholds:
• <150: iron
• ≥150: copper
• ≥250: silver
• ≥450: gold
• ≥850: plat
• ≥1650: diamond
• ≥2900: ultra

Commands:
add – Add new player with clear stats. Format:
• add <name> (to add with default stats)
• or add <name>, <offense>, <defense>, <played>, <wins>, <avg>, <rank_d>, <rank_o>, <rank_a>
• (exactly 9 comma‑separated fields; otherwise a wrong‑command error is output).
combine <player1> , <player2> – Merge two players’ stats.
rank <criteria> – Show ranking list by criteria.
• Supported criteria are: a (average), o (offense), d (defense), t (times played), r (win rate), a-rank (average rank), o-rank (offense rank), d-rank (defense rank).
Other commands remain:
• <team1> <winType> <team2> – Regular game processing
• pp – Print detailed player stats (with highest overall rank)
• best – Show best players by various metrics
• name – Print player names alphabetically
• exit – Quit the program