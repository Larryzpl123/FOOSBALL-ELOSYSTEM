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
    (2222, "master"),
    (1650, "diamond"),
    (1234, "jade"),
    (850, "plat"),
    (450, "gold"),
    (250, "silver"),
    (200, "copper"),
    (150, "bronze"),
    (0,   "iron")
]

# Special values for hidden and special ranks.
HIDDEN_RANK = "lz"  # when a player should be hidden
SPECIAL_IM = "im"   # special flag printed as "importal"

# Order for comparing ranking strings (the full words). 
RANK_ORDER = {
    "iron": 1,
    "bronze": 2,
    "copper": 3,
    "silver": 4,
    "gold": 5,
    "plat": 6,
    "jade": 7,
    "diamond": 8,
    "master": 9,
    "ultra": 10,
    HIDDEN_RANK: 10,
    SPECIAL_IM: 10  # treat im as highest; will print as "importal"
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
}

# Create an inverse dictionary to convert an initial letter back to a full rank name.
RANK_FULL = {v: k for k, v in RANK_INITIAL.items()}

players = {}

def canonicalize(name):
    return ''.join(c for c in name.lower() if c.isalnum())

def get_hidden_rank():
    letters = string.ascii_lowercase
    return "L" + ''.join(random.choice(letters) for _ in range(4)) + "Z" + ''.join(random.choice(letters) for _ in range(4))

def get_rank_display(rank):
    if rank == HIDDEN_RANK:
        return get_hidden_rank()
    if rank == SPECIAL_IM:
        return "importal"
    if rank in RANK_FULL:
        return RANK_FULL[rank]
    return rank

def get_computed_rank(score):
    for threshold, rank in RANK_THRESHOLDS:
        if score >= threshold:
            return rank
    return "iron"

def update_player_avg(key):
    data = players[key]
    data["avg"] = round((data["offense"] + data["defense"]) / 2)

def update_player_ranks(key):
    rec = players[key]
    new_o = get_computed_rank(rec["offense"])
    new_d = get_computed_rank(rec["defense"])
    new_a = get_computed_rank(rec["avg"])
    for field, new_val in (("rank_o", new_o), ("rank_d", new_d), ("rank_a", new_a)):
        current = rec.get(field, "iron")
        if current in (HIDDEN_RANK, SPECIAL_IM):
            continue
        if RANK_ORDER[new_val] > RANK_ORDER.get(current, 1):
            rec[field] = new_val
        else:
            rec[field] = current

def highest_overall_rank(key):
    rec = players[key]
    ranks = [rec.get("rank_o", "iron"), rec.get("rank_d", "iron"), rec.get("rank_a", "iron")]
    if any(r in (HIDDEN_RANK, SPECIAL_IM) for r in ranks):
        return get_hidden_rank()
    best = max(ranks, key=lambda r: RANK_ORDER.get(r, 1))
    return get_rank_display(best)

def get_rank_order(rank):
    if rank in RANK_ORDER:
        return RANK_ORDER[rank]
    elif rank in RANK_FULL:
        return RANK_ORDER[RANK_FULL[rank]]
    else:
        return 1

def get_rank_indicator(key):
    rec = players[key]
    rank_o = rec.get("rank_o", "iron")
    rank_d = rec.get("rank_d", "iron")
    order_o = get_rank_order(rank_o)
    order_d = get_rank_order(rank_d)
    if order_o > order_d:
        return "(o)"
    elif order_d > order_o:
        return "(d)"
    else:
        return "(a)"

def merge_record(key, new_display, off, deff, played, wins, rank_d=None, rank_o=None, rank_a=None):
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
        "display": old["display"],
        "offense": new_off,
        "defense": new_def,
        "played": total_played,
        "wins": new_wins,
        "avg": round((new_off + new_def) / 2),
        "rank_d": choose_rank(old.get("rank_d", "iron"), rank_d if rank_d else get_computed_rank(new_def)),
        "rank_o": choose_rank(old.get("rank_o", "iron"), rank_o if rank_o else get_computed_rank(new_off)),
        "rank_a": choose_rank(old.get("rank_a", "iron"), rank_a if rank_a else get_computed_rank(round((new_off + new_def) / 2)))
    }

def get_or_create_player(name):
    key = canonicalize(name)
    if key not in players:
        players[key] = {
            "display": name,
            "offense": RATING_MIN,
            "defense": RATING_MIN,
            "played": 0,
            "wins": 0,
            "avg": RATING_MIN,
            "rank_d": get_computed_rank(RATING_MIN),
            "rank_o": get_computed_rank(RATING_MIN),
            "rank_a": get_computed_rank(RATING_MIN)
        }
        if "zhong" in key:
            players[key]["rank_d"] = HIDDEN_RANK
            players[key]["rank_o"] = HIDDEN_RANK
            players[key]["rank_a"] = HIDDEN_RANK
    return players[key]

def load_data():
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
                    "wins": wins,
                    "avg": avg,
                    "rank_d": rank_d if rank_d else get_computed_rank(deff),
                    "rank_o": rank_o if rank_o else get_computed_rank(off),
                    "rank_a": rank_a if rank_a else get_computed_rank(avg)
                }
                if "zhong" in canon:
                    players[canon]["rank_d"] = HIDDEN_RANK
                    players[canon]["rank_o"] = HIDDEN_RANK
                    players[canon]["rank_a"] = HIDDEN_RANK

def save_data():
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

def print_players():
    if not players:
        print("No player data available.")
        return
    print("rank thresholds (ranks don't drop):")
    print("iron: 100, bronze: 150, copper: 200, silver: 250, gold: 450,")
    print("platinum: 850, jade: 1234, diamond: 1650, master: 2222,")
    print("ultra: 2900.")
    sorted_list = sorted(players.items(), key=lambda kv: (-kv[1]["avg"], kv[1]["display"]))
    header = f"{'No.':<3}  {'Name':<15}  {'Avg':>5}  {'Off':>5}  {'Def':>5}  {'T':>3}  {'Win%':>5}  {'Rank (Highest a/o/d)':<15}"
    print(header)
    print("-" * len(header))
    for idx, (key, data) in enumerate(sorted_list, start=1):
        played = data["played"]
        wins = data["wins"]
        win_rate = round((wins / played) * 100) if played > 0 else 0
        overall_rank = highest_overall_rank(key)
        indicator = get_rank_indicator(key)
        rank_display = overall_rank + indicator
        print(f"{idx:<3}  {data['display']:<15}  {data['avg']:>5}  {data['offense']:>5}  {data['defense']:>5}  {played:>3}  {win_rate:>5}  {rank_display:<15}")

def adjust_opponent_rating(opponent_rating, player_rating):
    if opponent_rating == RATING_MIN and player_rating > 1500:
        return 1500
    return opponent_rating

def update_rating(curr_rating, score, opposition_rating, multiplier):
    expected = 1 / (1 + math.pow(10, (adjust_opponent_rating(opposition_rating, curr_rating) - curr_rating) / 400))
    change = multiplier * K_FACTOR * (score - expected)
    if change < 0 and curr_rating <= RATING_MIN:
        return RATING_MIN, 0
    new_rating = curr_rating + change
    new_rating = round(new_rating)
    new_rating = max(min(new_rating, RATING_MAX), RATING_MIN)
    return new_rating, change

def calculate_expected_win_rate(player_rating, opponent_rating):
    expected = 1 / (1 + math.pow(10, (opponent_rating - player_rating) / 400))
    return expected * 100

def parse_team(team_str):
    if ";" in team_str:
        offense_part, defense_part = team_str.split(";", 1)
        offense_players = [p.strip() for p in offense_part.split(",") if p.strip()]
        defense_players = [p.strip() for p in defense_part.split(",") if p.strip()]
    else:
        offense_players = [p.strip() for p in team_str.split(",") if p.strip()]
        defense_players = []
    return offense_players, defense_players

def process_game(command):
    pattern = r"^(.*?)\s*(win|smallwin|closewin|bigwin|perfectwin)\s*(.*?)$"
    match = re.match(pattern, command, re.IGNORECASE)
    if not match:
        print("Command format not recognized.")
        return
    team1_str, win_type, team2_str = match.groups()
    win_type = win_type.lower()
    if win_type not in WIN_TYPE_MULTIPLIERS:
        print("Invalid win type.")
        return
    base_multiplier = WIN_TYPE_MULTIPLIERS[win_type]
    team1_off, team1_def = parse_team(team1_str)
    team2_off, team2_def = parse_team(team2_str)

    for name in team1_off + team1_def + team2_off + team2_def:
        get_or_create_player(name)

    def get_average_rating(names, role):
        if not names:
            return None
        total = sum(get_or_create_player(name)[role] for name in names)
        return total / len(names)

    opp_for_team1 = get_average_rating(team2_def, "defense") if team2_def else get_average_rating(team2_off, "offense")
    opp_off_team1 = get_average_rating(team2_off, "offense") if team2_off else get_average_rating(team2_def, "defense")
    opp_for_team2 = get_average_rating(team1_def, "defense") if team1_def else get_average_rating(team1_off, "offense")
    opp_off_team2 = get_average_rating(team1_off, "offense") if team1_off else get_average_rating(team1_def, "defense")

    opp_for_team1 = opp_for_team1 or 1500
    opp_off_team1 = opp_off_team1 or 1500
    opp_for_team2 = opp_for_team2 or 1500
    opp_off_team2 = opp_off_team2 or 1500

    print("--------------------------------------------------------------------------------")
    for name in team1_off:
        player = get_or_create_player(name)
        new_off, change = update_rating(player["offense"], 1, opp_for_team1, base_multiplier)
        print(f"{player['display']} Offense: {player['offense']} → {new_off} ({change:+.1f})")
        player["offense"] = new_off
        player["played"] += 1
        player["wins"] += 1

    for name in team1_def:
        player = get_or_create_player(name)
        new_def, change = update_rating(player["defense"], 1, opp_off_team1, base_multiplier)
        print(f"{player['display']} Defense: {player['defense']} → {new_def} ({change:+.1f})")
        player["defense"] = new_def
        player["played"] += 1
        player["wins"] += 1

    for name in team2_off:
        player = get_or_create_player(name)
        new_off, change = update_rating(player["offense"], 0, opp_for_team2, base_multiplier)
        print(f"{player['display']} Offense: {player['offense']} → {new_off} ({change:+.1f})")
        player["offense"] = new_off
        player["played"] += 1

    for name in team2_def:
        player = get_or_create_player(name)
        new_def, change = update_rating(player["defense"], 0, opp_off_team2, base_multiplier)
        print(f"{player['display']} Defense: {player['defense']} → {new_def} ({change:+.1f})")
        player["defense"] = new_def
        player["played"] += 1

    team1_players = team1_off + team1_def
    team2_players = team2_off + team2_def

    team1_rates = []
    for name in team1_players:
        player = get_or_create_player(name)
        role = "offense" if name in team1_off else "defense"
        opp_rating = opp_for_team1 if role == "offense" else opp_off_team1
        rate = calculate_expected_win_rate(player[role], opp_rating)
        team1_rates.append(rate)
        print(f"{player['display']} ({role[0].upper()}): {rate:.1f}%")

    team2_rates = []
    for name in team2_players:
        player = get_or_create_player(name)
        role = "offense" if name in team2_off else "defense"
        opp_rating = opp_for_team2 if role == "offense" else opp_off_team2
        rate = calculate_expected_win_rate(player[role], opp_rating)
        team2_rates.append(rate)
        print(f"{player['display']} ({role[0].upper()}): {rate:.1f}%")

    avg_team1 = sum(team1_rates) / len(team1_rates) if team1_rates else 0
    avg_team2 = sum(team2_rates) / len(team2_rates) if team2_rates else 0

    team1_names = " + ".join([get_or_create_player(name)['display'] for name in team1_players])
    team2_names = " + ".join([get_or_create_player(name)['display'] for name in team2_players])
    print(f"\n{team1_names}: {avg_team1:.1f}% vs {team2_names}: {avg_team2:.1f}%")
    print("--------------------------------------------------------------------------------")

    save_data()

def print_best_players():
    if not players:
        print("No player data available.")
        return
    best_avg = max(players.values(), key=lambda x: x["avg"])
    best_off = max(players.values(), key=lambda x: x["offense"])
    best_def = max(players.values(), key=lambda x: x["defense"])
    most_played = max(players.values(), key=lambda x: x["played"])
    highest_win = max(players.values(), key=lambda x: (x["wins"]/x["played"]) if x["played"] else 0)
    
    print("Best Players:")
    print(f"  Best Average: {best_avg['display']} (A-{best_avg['avg']})")
    print(f"  Best Offense: {best_off['display']} (O-{best_off['offense']})")
    print(f"  Best Defense: {best_def['display']} (D-{best_def['defense']})")
    print(f"  Most Played: {most_played['display']} (T-{most_played['played']})")
    if highest_win["played"] > 0:
        win_rate = (highest_win["wins"] / highest_win["played"]) * 100
        print(f"  Highest Win Rate: {highest_win['display']} ({win_rate:.1f}%)")

def main():
    load_data()
    print("Foosball ELO System")
    print("Commands: game, pp, best, exit")
    while True:
        cmd = input("> ").strip()
        if cmd.lower() == "exit":
            save_data()
            break
        elif cmd.lower() == "pp":
            print_players()
        elif cmd.lower() == "best":
            print_best_players()
        else:
            process_game(cmd)

if __name__ == "__main__":
    main()
