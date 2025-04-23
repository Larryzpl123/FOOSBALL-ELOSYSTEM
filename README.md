A simple foosball elo system.

• The foosball.py is the offline execution MAIN file <br />
• The index.html is scoreboard <br />
• The 2index.html is online execution file <br />
• And elo.txt is the database file <br />

Functions:

Name Normalization & Merging: <br />
“LarryZhong”, “Larry Zhong”, “Larry_Zhong”, etc., are merged automatically. <br />

Ranks: <br />
Besides Elo scores (offense, defense, average), players now earn an un-droppable rank based on thresholds: <br />
• <150: 1 - iron <br />
• ≥150: 2 - bronze <br />
• ≥200: 3 - copper <br />
• ≥250: 4 - silver <br />
• ≥450: 5 - gold <br />
• ≥850: 6 - plat <br />
• ≥1234: 7 - jade <br />
• ≥1650: 8 - emerald <br />
• ≥2222: 9 - diamond <br />
• ≥2468: 10 - master <br />
• ≥2900: 11 - ultra <br />
5 hidden ranks <br />

Commands: <br /> 
• <team1> <winType> <team2> – Regular game processing <br />
• pp – Print detailed player stats (with highest overall rank) <br />
• best – Show best players by various metrics <br />
• name – Print player names alphabetically <br />
• combine a to b – Combine player and their stats <br />
• exit – Save and quit the program <br />
