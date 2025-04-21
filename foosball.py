#!/usr/bin/env python3
import math
import os
import re
import random
import string

# Global constants
FILE_NAME = "elo.txt"
K_FACTOR = 32
RATING_MIN = 100   # default starting rating
RATING_MAX = 2999  # maximum rating (not passing PEAK)

# Multipliers for win types
WIN_TYPE_MULTIPLIERS = {
    "win": 1.0,
    "smallwin": 0.75,
    "closewin": 0.5,
    "bigwin": 1.25,
    "perfectwin": 1.5
}

# Ranking thresholds (un-droppable, once reached, always kept)
RANK_THRESHOLDS = [
    (2900, "ultra"),
    (1650, "diamond"),
    (850, "plat"),
    (450, "gold"),
    (250, "silver"),
    (150, "copper"),
    (0,   "iron")
]

# Special values for hidden and special ranks.
HIDDEN_RANK = "lz"  # when a player should be hidden
SPECIAL_IM = "im"   # special flag printed as "importal"

# Order for comparing ranking strings (the full words). 
RANK_ORDER = {
    "iron": 1,
    "copper": 2,
    "silver": 3,
    "gold": 4,
    "plat": 5,
    "diamond": 6,
    "ultra": 7,
    HIDDEN_RANK: 8,
    SPECIAL_IM: 8  # treat im as highest; will print as "importal"
}

# Dictionary for converting a full rank to its initial letter.
RANK_INITIAL = {
    "iron": "i",
    "copper": "c",
    "silver": "s",
    "gold": "g",
    "plat": "p",
    "diamond": "d",
    "ultra": "u"
    # Hidden rank is not directly mapped because we always generate it.
}

# Data structure for player records.
# Each record: display, offense, defense, played, wins, avg, rank_o, rank_d, rank_a.
players = {}

# --- Utility functions ---

def canonicalize(name):
    """Convert name to a lowercase alphanumeric string (ignore spaces and punctuation)."""
    return ''.join(c for c in name.lower() if c.isalnum())

def get_hidden_rank():
    """
    Return a random hidden rank string in the format:
       L + (4 random lowercase letters) + Z + (4 random lowercase letters)
    For example: LrjsuZisas
    """
    letters = string.ascii_lowercase
    return "L" + ''.join(random.choice(letters) for _ in range(4)) + "Z" + ''.join(random.choice(letters) for _ in range(4))

def get_rank_display(rank):
    """
    Converts a stored rank (e.g., iron, copper, etc.) to its initial letter.
    If the rank is hidden (HIDDEN_RANK), returns a generated hidden rank string.
    Also handles the special im flag.
    """
    if rank == HIDDEN_RANK:
        return get_hidden_rank()
    if rank == SPECIAL_IM:
        return "importal"
    return RANK_INITIAL.get(rank, rank)

def get_computed_rank(score):
    """Compute the rank (as a full string) for a given score based on thresholds."""
    for threshold, rank in RANK_THRESHOLDS:
        if score >= threshold:
            return rank
    return "iron"

def update_player_avg(key):
    """Update the average rating for a given player record."""
    data = players[key]
    data["avg"] = round((data["offense"] + data["defense"]) / 2)

def update_player_ranks(key):
    """
    Update stored rank fields for offense, defense, and average.
    Ranks never drop – if a new computed rank is higher (by order) than stored, update.
    """
    rec = players[key]
    new_o = get_computed_rank(rec["offense"])
    new_d = get_computed_rank(rec["defense"])
    new_a = get_computed_rank(rec["avg"])
    for field, new_val in (("rank_o", new_o), ("rank_d", new_d), ("rank_a", new_a)):
        current = rec.get(field, "iron")
        # If already hidden or special, do not change
        if current in (HIDDEN_RANK, SPECIAL_IM):
            continue
        if RANK_ORDER[new_val] > RANK_ORDER.get(current, 1):
            rec[field] = new_val
        else:
            rec[field] = current  # keep the better rank

def highest_overall_rank(key):
    """
    Determine the highest rank (by order) among offense, defense, and average.
    If any is hidden, then return the hidden rank display.
    """
    rec = players[key]
    ranks = [rec.get("rank_o", "iron"), rec.get("rank_d", "iron"), rec.get("rank_a", "iron")]
    # If any is hidden, choose that one.
    if any(r in (HIDDEN_RANK, SPECIAL_IM) for r in ranks):
        return get_hidden_rank()
    best = max(ranks, key=lambda r: RANK_ORDER.get(r, 1))
    return get_rank_display(best)

def merge_record(key, new_display, off, deff, played, wins, rank_d=None, rank_o=None, rank_a=None):
    """
    Merge new record data into an existing record (weighted average by times played).
    """
    old = players[key]
    total_played = old["played"] + played
    if total_played > 0:
        new_off = round((old["offense"] * old["played"] + off * played) / total_played)
        new_def = round((old["defense"] * old["played"] + deff * played) / total_played)
    else:
        new_off, new_def = off, deff
    new_wins = old["wins"] + wins

    def choose_rank(old_rank, new_rank):
        return new_rank if RANK_ORDER.get(new_rank, 0) > RANK_ORDER.get(old_rank, 0) else old_rank

    players[key] = {
        "display": old["display"],  # keep the earlier display name
        "offense": new_off,
        "defense": new_def,
        "played": total_played,
        "wins": new_wins
    }
    update_player_avg(key)
    players[key]["rank_d"] = choose_rank(old.get("rank_d", "iron"), rank_d if rank_d else get_computed_rank(new_def))
    players[key]["rank_o"] = choose_rank(old.get("rank_o", "iron"), rank_o if rank_o else get_computed_rank(new_off))
    players[key]["rank_a"] = choose_rank(old.get("rank_a", "iron"), rank_a if rank_a else get_computed_rank(players[key]["avg"]))

# --- Player Creation ---

def get_or_create_player(name):
    """
    Retrieve the player record for 'name' if it exists;
    otherwise, create a new one with default stats.
    Also, if the player's canonical name contains 'zhong', force all rank fields to HIDDEN_RANK.
    """
    key = canonicalize(name)
    if key not in players:
        players[key] = {
            "display": name,
            "offense": RATING_MIN,
            "defense": RATING_MIN,
            "played": 0,
            "wins": 0
        }
        update_player_avg(key)
        players[key]["rank_d"] = get_computed_rank(players[key]["defense"])
        players[key]["rank_o"] = get_computed_rank(players[key]["offense"])
        players[key]["rank_a"] = get_computed_rank(players[key]["avg"])
        # If the name (canonicalized) contains 'zhong', force the rank to hidden.
        if "zhong" in key:
            players[key]["rank_d"] = HIDDEN_RANK
            players[key]["rank_o"] = HIDDEN_RANK
            players[key]["rank_a"] = HIDDEN_RANK
    return players[key]

# --- File I/O functions ---

def load_data():
    """
    Load player data from file.
    Expected format per line:
      DisplayName, offense, defense, times_played, win_rate, average, rank_d, rank_o, rank_a.
    Merges duplicate records (by canonical name).
    """
    if not os.path.exists(FILE_NAME):
        return
    with open(FILE_NAME, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().rstrip(".")
            if not line:
                continue
            parts = [x.strip() for x in line.split(",")]
            if len(parts) < 5:
                continue
            disp = parts[0]
            canon = canonicalize(disp)
            try:
                off = int(parts[1])
                deff = int(parts[2])
                played = int(parts[3])
                win_rate = int(parts[4])
            except ValueError:
                continue
            wins = round((win_rate / 100) * played) if played > 0 else 0
            avg = int(parts[5]) if len(parts) >= 6 and parts[5].isdigit() else round((off + deff) / 2)
            rank_d = parts[6] if len(parts) >= 7 else None
            rank_o = parts[7] if len(parts) >= 8 else None
            rank_a = parts[8] if len(parts) >= 9 else None
            if canon in players:
                merge_record(canon, disp, off, deff, played, wins, rank_d, rank_o, rank_a)
            else:
                players[canon] = {
                    "display": disp,
                    "offense": off,
                    "defense": deff,
                    "played": played,
                    "wins": wins
                }
                update_player_avg(canon)
                players[canon]["rank_d"] = rank_d if rank_d else get_computed_rank(deff)
                players[canon]["rank_o"] = rank_o if rank_o else get_computed_rank(off)
                players[canon]["rank_a"] = rank_a if rank_a else get_computed_rank(players[canon]["avg"])
                # Force hidden rank if the canonical name indicates zhong.
                if "zhong" in canon:
                    players[canon]["rank_d"] = HIDDEN_RANK
                    players[canon]["rank_o"] = HIDDEN_RANK
                    players[canon]["rank_a"] = HIDDEN_RANK

def save_data():
    """
    Save player data to file.
    Each line is:
      DisplayName, offense, defense, times_played, win_rate, average, rank_d, rank_o, rank_a.
    Sorted by average descending.
    """
    for key in players:
        update_player_avg(key)
        update_player_ranks(key)
    sorted_players = sorted(players.items(), key=lambda kv: (-kv[1]["avg"], kv[1]["display"]))
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        for key, data in sorted_players:
            played = data["played"]
            wins = data["wins"]
            win_rate = round((wins / played) * 100) if played > 0 else 0
            line = f"{data['display']}, {data['offense']}, {data['defense']}, {played}, {win_rate}, {data['avg']}, {data.get('rank_d', 'iron')}, {data.get('rank_o', 'iron')}, {data.get('rank_a', 'iron')}.\n"
            f.write(line)

# --- Display functions ---

def print_players():
    """
    Print player info (sorted by average descending) with aligned columns.
    Also shows the overall rank (using highest_overall_rank).
    """
    if not players:
        print("No player data available.")
        return
    # Update records before printing
    for key in players:
        update_player_avg(key)
        update_player_ranks(key)
    sorted_list = sorted(players.items(), key=lambda kv: (-kv[1]["avg"], kv[1]["display"]))
    header = f"{'No.':<3}  {'Name':<15}  {'Avg':>5}  {'Off':>5}  {'Def':>5}  {'T':>3}  {'Win%':>5}  {'Rank':<10}"
    print(header)
    print("-" * len(header))
    for idx, (key, data) in enumerate(sorted_list, start=1):
        played = data["played"]
        wins = data["wins"]
        win_rate = round((wins / played) * 100) if played > 0 else 0
        overall_rank = highest_overall_rank(key)
        print(f"{idx:<3}  {data['display']:<15}  {data['avg']:>5}  {data['offense']:>5}  {data['defense']:>5}  {played:>3}  {win_rate:>5}  {overall_rank:<10}")

def print_players_alphabetically():
    """Print players sorted alphabetically."""
    if not players:
        print("No player data available.")
        return
    sorted_list = sorted(players.items(), key=lambda kv: kv[1]["display"].lower())
    header = f"{'Name':<15}  {'Avg':>5}  {'Off':>5}  {'Def':>5}  {'T':>3}  {'Win%':>5}"
    print(header)
    print("-" * len(header))
    for key, data in sorted_list:
        played = data["played"]
        wins = data["wins"]
        win_rate = round((wins / played) * 100) if played > 0 else 0
        print(f"{data['display']:<15}  {data['avg']:>5}  {data['offense']:>5}  {data['defense']:>5}  {played:>3}  {win_rate:>5}")

def print_best_players():
    """Print best players by various metrics including rank behind the results."""
    if not players:
        print("No player data available.")
        return
    best_avg = max(players.items(), key=lambda kv: kv[1]["avg"])
    best_offense = max(players.items(), key=lambda kv: kv[1]["offense"])
    best_defense = max(players.items(), key=lambda kv: kv[1]["defense"])
    most_played  = max(players.items(), key=lambda kv: kv[1]["played"])
    highest_win_rate = max(players.items(), key=lambda kv: (kv[1]["wins"] / kv[1]["played"]) if kv[1]["played"] > 0 else 0)

    # For each best result, print the value and also the stored rank (converted to its display)
    print("Best Players:")
    print(f"  Best Average: {best_avg[1]['display']} (A-{best_avg[1]['avg']}, Rank-{get_rank_display(best_avg[1].get('rank_a', 'iron'))})")
    print(f"  Best Offense: {best_offense[1]['display']} (O-{best_offense[1]['offense']}, Rank-{get_rank_display(best_offense[1].get('rank_o', 'iron'))})")
    print(f"  Best Defense: {best_defense[1]['display']} (D-{best_defense[1]['defense']}, Rank-{get_rank_display(best_defense[1].get('rank_d', 'iron'))})")
    print(f"  Most Time Played: {most_played[1]['display']} (T-{most_played[1]['played']})")
    played = highest_win_rate[1]["played"]
    win_rate = (highest_win_rate[1]["wins"] / played) * 100 if played > 0 else 0
    print(f"  Highest Win Rate: {highest_win_rate[1]['display']} (R-{win_rate:.2f}%)")

# --- Command processing functions ---

def parse_team(team_str):
    """
    Dummy implementation for parsing a team string into offense and defense lists.
    Here we assume names separated by semicolons (;) represent two groups.
    In a real scenario, you would further split offense and defense.
    """
    # Split on the semicolon if given; otherwise, assume all names are offense.
    if ";" in team_str:
        names = [x.strip() for x in team_str.split(";")]
        # For simplicity, treat the first name as offense and the rest as defense.
        if names:
            offense = [names[0]]
            defense = names[1:]
        else:
            offense, defense = [], []
    else:
        offense = [team_str.strip()] if team_str.strip() else []
        defense = []
    return offense, defense

def update_rating(current, win, opponent_rating, multiplier):
    """
    Dummy rating updater. In a real Elo system you would compute an expected score etc.
    Here we simply add a constant K_FACTOR (modified by multiplier) if win, subtract if not.
    """
    change = round(K_FACTOR * multiplier)
    if win:
        return current + change, change
    else:
        return current - change, -change

def get_average_rating(names, rating_type):
    """
    Compute the average rating (offense or defense) for a list of players.
    Returns None if the list is empty.
    """
    if not names:
        return None
    total = 0
    count = 0
    for name in names:
        player = get_or_create_player(name)
        total += player[rating_type]
        count += 1
    return total // count if count else None

def process_game(command):
    """
    Process a game result command.
    Format:
      <team1> <win_type> <team2>
    """
    pattern = r"^(.*?)\s*(win|smallwin|closewin|bigwin|perfectwin)\s*(.*?)$"
    match = re.match(pattern, command, re.IGNORECASE)
    if not match:
        print("Game command format not recognized. Please try again.")
        return
    team1_str, win_type, team2_str = match.groups()
    win_type = win_type.lower().strip()
    if win_type not in WIN_TYPE_MULTIPLIERS:
        print("Invalid win type.")
        return
    base_multiplier = WIN_TYPE_MULTIPLIERS[win_type]
    team1_off, team1_def = parse_team(team1_str)
    team2_off, team2_def = parse_team(team2_str)

    # Ensure players exist
    for name in team1_off + team1_def + team2_off + team2_def:
        get_or_create_player(name)

    # Compute opponent rating averages
    opp_for_team1 = get_average_rating(team2_def, "defense") if team2_def else get_average_rating(team2_off, "offense")
    opp_off_team1 = get_average_rating(team2_off, "offense") if team2_off else get_average_rating(team2_def, "defense")
    opp_for_team2 = get_average_rating(team1_def, "defense") if team1_def else get_average_rating(team1_off, "offense")
    opp_off_team2 = get_average_rating(team1_off, "offense") if team1_off else get_average_rating(team1_def, "defense")

    # Update winning team (team1)
    for name in team1_off:
        player = get_or_create_player(name)
        new_off, _ = update_rating(player["offense"], 1, opp_for_team1 if opp_for_team1 is not None else 1500, base_multiplier)
        player["offense"] = new_off
        player["played"] += 1
        player["wins"] += 1
    for name in team1_def:
        player = get_or_create_player(name)
        new_def, _ = update_rating(player["defense"], 1, opp_off_team1 if opp_off_team1 is not None else 1500, base_multiplier)
        player["defense"] = new_def
        player["played"] += 1
        player["wins"] += 1

    # Update losing team (team2)
    for name in team2_off:
        player = get_or_create_player(name)
        new_off, _ = update_rating(player["offense"], 0, opp_for_team2 if opp_for_team2 is not None else 1500, base_multiplier)
        player["offense"] = new_off
        player["played"] += 1
    for name in team2_def:
        player = get_or_create_player(name)
        new_def, _ = update_rating(player["defense"], 0, opp_off_team2 if opp_off_team2 is not None else 1500, base_multiplier)
        player["defense"] = new_def
        player["played"] += 1

    for key in players:
        update_player_avg(key)
        update_player_ranks(key)
    save_data()
    print("Game processed and ratings updated.")

def process_add(command):
    """
    Process the 'add' command.
    Format: 
       add <name>
    or 
       add <name>, <offense>, <defense>, <played>, <wins>, <avg>, <rank_d>, <rank_o>, <rank_a>
    """
    info = command[3:].strip()  # remove "add"
    if not info:
        print("No player info provided.")
        return
    parts = [p.strip() for p in info.split(",")]
    if len(parts) == 1:
        name = parts[0]
        get_or_create_player(name)
        print(f"Player {name} added with default stats.")
    elif len(parts) == 9:
        try:
            name = parts[0]
            off = int(parts[1])
            deff = int(parts[2])
            played = int(parts[3])
            wins = int(parts[4])
            avg = int(parts[5])
            rank_d = parts[6]
            rank_o = parts[7]
            rank_a = parts[8]
        except ValueError:
            print("Error: Incorrect format in add command.")
            return
        canon = canonicalize(name)
        players[canon] = {
            "display": name,
            "offense": off,
            "defense": deff,
            "played": played,
            "wins": wins,
            "avg": avg,
            "rank_d": rank_d,
            "rank_o": rank_o,
            "rank_a": rank_a
        }
        if "zhong" in canon:
            players[canon]["rank_d"] = HIDDEN_RANK
            players[canon]["rank_o"] = HIDDEN_RANK
            players[canon]["rank_a"] = HIDDEN_RANK
        print(f"Player {name} added with specified stats.")
    else:
        print("Wrong command format for add. Expect either 1 or 9 comma-separated fields after 'add'.")
    save_data()

def process_combine(command):
    """
    Process the 'combine' command to merge two player records.
    Format: combine <name1> , <name2>
    """
    info = command[7:].strip()  # remove "combine"
    parts = [p.strip() for p in info.split(",")]
    if len(parts) != 2:
        print("Combine command requires two names separated by a comma.")
        return
    name1, name2 = parts
    canon1 = canonicalize(name1)
    canon2 = canonicalize(name2)
    if canon1 not in players or canon2 not in players:
        print("One of the players does not exist.")
        return
    merge_record(canon1, players[canon1]["display"], players[canon2]["offense"], players[canon2]["defense"], players[canon2]["played"], players[canon2]["wins"])
    del players[canon2]
    print(f"Players {name1} and {name2} combined.")
    save_data()

def process_rank_cmd(command):
    """
    Process the 'rank' command.
    Format: rank <criteria>
    Criteria can be:
       a      -> rank by average (show stored average value and rank_a)
       o      -> rank by offense (show offense value and rank_o)
       d      -> rank by defense (show defense value and rank_d)
       t      -> rank by times played
       r      -> rank by win rate
       a-rank -> rank by stored average rank (and similarly for o-rank, d-rank)
       
    Additionally, if a player's stored rank is hidden (HIDDEN_RANK),
    display the row number as 0 instead of its ordinal placement.
    """
    tokens = command.split()
    if len(tokens) != 2:
        print("Rank command requires a single criteria parameter (e.g., rank a).")
        return
    crit = tokens[1].lower()
    # Prepare sorting, header labels, and value functions
    if crit == "a":
        sorted_list = sorted(players.items(), key=lambda kv: (-kv[1]["avg"], kv[1]["display"]))
        header = f"{'No.':<3}  {'Name':<15}  {'Average':>7}  {'Rank_A':<10}"
        def value_func(item):
            return item[1]["avg"]
        def rank_val(item):
            return item[1].get("rank_a", "iron")
    elif crit == "o":
        sorted_list = sorted(players.items(), key=lambda kv: (-kv[1]["offense"], kv[1]["display"]))
        header = f"{'No.':<3}  {'Name':<15}  {'Offense':>7}  {'Rank_O':<10}"
        def value_func(item):
            return item[1]["offense"]
        def rank_val(item):
            return item[1].get("rank_o", "iron")
    elif crit == "d":
        sorted_list = sorted(players.items(), key=lambda kv: (-kv[1]["defense"], kv[1]["display"]))
        header = f"{'No.':<3}  {'Name':<15}  {'Defense':>7}  {'Rank_D':<10}"
        def value_func(item):
            return item[1]["defense"]
        def rank_val(item):
            return item[1].get("rank_d", "iron")
    elif crit == "t":
        sorted_list = sorted(players.items(), key=lambda kv: (-kv[1]["played"], kv[1]["display"]))
        header = f"{'No.':<3}  {'Name':<15}  {'Played':>7}"
        def value_func(item):
            return item[1]["played"]
        def rank_val(item):
            return ""
    elif crit == "r":
        sorted_list = sorted(players.items(), key=lambda kv: (-(kv[1]["wins"]/kv[1]["played"]) if kv[1]["played"] else 0, kv[1]["display"]))
        header = f"{'No.':<3}  {'Name':<15}  {'Win%':>7}"
        def value_func(item):
            played = item[1]["played"]
            return round((item[1]["wins"] / played) * 100) if played > 0 else 0
        def rank_val(item):
            return ""
    elif crit in ("a-rank", "o-rank", "d-rank"):
        field = {"a-rank": "rank_a", "o-rank": "rank_o", "d-rank": "rank_d"}[crit]
        sorted_list = sorted(players.items(), key=lambda kv: (-RANK_ORDER.get(kv[1].get(field, "iron"), 1), -kv[1]["avg"], kv[1]["display"]))
        header = f"{'No.':<3}  {'Name':<15}  {field.upper():<10}"
        def value_func(item):
            return ""
        def rank_val(item):
            return item[1].get(field, "iron")
    else:
        print("Unsupported rank criteria.")
        return

    print(header)
    print("-" * len(header))
    # Instead of using enumerate directly, if a player has hidden rank (HIDDEN_RANK)
    # we print its row number as 0.
    ordinal = 1
    for key, data in sorted_list:
        stored_rank = rank_val((key, data))
        display_rank = get_rank_display(stored_rank) if stored_rank else ""
        # Determine row number: if rank is hidden, always 0; else show the ordinal.
        num = "0" if stored_rank == HIDDEN_RANK else str(ordinal)
        if crit in ("a", "o", "d"):
            print(f"{num:<3}  {data['display']:<15}  {value_func((key, data)):>7}  {display_rank:<10}")
        elif crit in ("t", "r"):
            print(f"{num:<3}  {data['display']:<15}  {value_func((key, data)):>7}")
        else:
            print(f"{num:<3}  {data['display']:<15}  {display_rank:<10}")
        # Only increment ordinal for non-hidden players.
        if stored_rank != HIDDEN_RANK:
            ordinal += 1

# --- Main command loop ---

def main():
    load_data()
    save_data()
    print("Foosball Elo rating system started.")
    print("Commands:")
    print(" - <teama> <winType> <teamb>  (e.g., \"JustinCheng ; LarryZhong closewin ParkerHoppy ; ThayerMahan\")")
    print(" - Type 'pp' to print player statistics (sorted by average rating).")
    print(" - Type 'best' to show best players (with rank behind each best result).")
    print(" - Type 'name' to show names alphabetically.")
    print(" - Type 'add' to add a new player (e.g., \"add VictorXia\" or with full stats).")
    print(" - Type 'combine' to combine two player stats (e.g., \"combine Player1 , Player2\").")
    print(" - Type 'rank <criteria>' to display rankings. Criteria: a, o, d, t, r, a-rank, o-rank, d-rank.")
    print(" - Type 'exit' to quit.")
    while True:
        command = input("Enter command: ").strip()
        if command.lower() == "exit":
            print("Exiting...")
            break
        elif command.lower() == "pp":
            print_players()
        elif command.lower() == "best":
            print_best_players()
        elif command.lower() == "name":
            print_players_alphabetically()
        elif command.lower().startswith("add "):
            process_add(command)
        elif command.lower().startswith("combine"):
            process_combine(command)
        elif command.lower().startswith("rank"):
            process_rank_cmd(command)
        elif command == "":
            continue
        else:
            process_game(command)

if __name__ == '__main__':
    main()
