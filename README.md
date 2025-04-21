Name Normalization & Merging: <br />
“LarryZhong”, “Larry Zhong”, “Larry_Zhong”, etc., are merged automatically. <br />

Ranks: <br />
Besides Elo scores (offense, defense, average), players now earn an un-droppable rank based on thresholds: <br />
• <150: iron <br />
• ≥150: copper <br />
• ≥250: silver <br />
• ≥450: gold <br />
• ≥850: plat <br />
• ≥1650: diamond <br />
• ≥2900: ultra <br />

Commands: <br /> 
add – Add new player with clear stats. Format: <br />
• add <name> (to add with default stats) <br />
• or add <name>, <offense>, <defense>, <played>, <wins>, <avg>, <rank_d>, <rank_o>, <rank_a> <br />
• (exactly 9 comma‑separated fields; otherwise a wrong‑command error is output). <br />
combine <player1> , <player2> – Merge two players’ stats. <br />
rank <criteria> – Show ranking list by criteria. <br />
• Supported criteria are: a (average), o (offense), d (defense), t (times played), r (win rate), a-rank (average rank), o-rank (offense rank), d-rank (defense rank). <br />
Other commands remain: <br />
• <team1> <winType> <team2> – Regular game processing <br />
• pp – Print detailed player stats (with highest overall rank) <br />
• best – Show best players by various metrics <br />
• name – Print player names alphabetically <br />
• exit – Quit the program <br />
