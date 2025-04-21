#!/usr/bin/env python3
import math
import os
import re

# Global constants
FILE_NAME = "elo.txt"
K_FACTOR = 32
RATING_MIN = 100   # default starting rating is 100
RATING_MAX = 2999  # not passing PEAK

# Multipliers for win types
WIN_TYPE_MULTIPLIERS = {
    "win": 1.0,
    "smallwin": 0.75,
    "closewin": 0.5,
    "bigwin": 1.25,
    "perfectwin": 1.5
}

# Data structure for player records
players = {}

def canonicalize(name):
    return ''.join(c for c in name.lower() if c.isalnum())

def update_player_avg(key):
    data = players[key]
    data["avg"] = round((data["offense"] + data["defense"]) / 2)

def merge_record(key, new_display, off, deff, played, wins):
    old = players[key]
    total_played = old["played"] + played
    if total_played > 0:
        new_off = round((old["offense"] * old["played"] + off * played) / total_played)
        new_def = round((old["defense"] * old["played"] + deff * played) / total_played)
    else:
        new_off, new_def = off, deff
    new_wins = old["wins"] + wins
    players[key] = {
        "display": old["display"],
        "offense": new_off,
        "defense": new_def,
        "played": total_played,
        "wins": new_wins
    }
    update_player_avg(key)

def load_data():
    if not os.path.exists(FILE_NAME):
        return
    with open(FILE_NAME, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            line = line.rstrip(".")
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
            if canon in players:
                merge_record(canon, disp, off, deff, played, wins)
            else:
                players[canon] = {
                    "display": disp,
                    "offense": off,
                    "defense": deff,
                    "played": played,
                    "wins": wins
                }
                update_player_avg(canon)

def save_data():
    for key in players:
        update_player_avg(key)
    sorted_players = sorted(players.items(), key=lambda kv: (-kv[1]["avg"], kv[1]["display"]))
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        for key, data in sorted_players:
            played = data["played"]
            wins = data["wins"]
            win_rate = round((wins / played) * 100) if played > 0 else 0
            line = f"{data['display']}, {data['offense']}, {data['defense']}, {played}, {win_rate}, {data['avg']}.\n"
            f.write(line)

def print_players():
    if not players:
        print("No player data available.")
        return
    for key in players:
        update_player_avg(key)
    sorted_list = sorted(players.items(), key=lambda kv: (-kv[1]["avg"], kv[1]["display"]))
    print("DisplayName, AverageRating, OffenseRating, DefenseRating, TimesPlayed, WinRate")
    print("Rating from 100 to 2999")
    for rank, (key, data) in enumerate(sorted_list, start=1):
        played = data["played"]
        wins = data["wins"]
        win_rate = round((wins / played) * 100) if played > 0 else 0
        player_str = f"{data['display']}, A-{data['avg']}, O-{data['offense']}, D-{data['defense']}, T-{played}, R-{win_rate}"
        print(f"{rank} - {player_str}")

def get_or_create_player(raw_name):
    canon = canonicalize(raw_name)
    if canon not in players:
        players[canon] = {
            "display": raw_name,
            "offense": RATING_MIN,
            "defense": RATING_MIN,
            "played": 0,
            "wins": 0
        }
        update_player_avg(canon)
    return players[canon]

def adjust_opponent_rating(opponent_rating, player_rating):
    if opponent_rating == RATING_MIN and player_rating > 150:
        return 150
    return opponent_rating

def update_rating(curr_rating, score, opposition_rating, multiplier):
    expected = 1 / (1 + math.pow(10, (adjust_opponent_rating(opposition_rating, curr_rating) - curr_rating) / 400))
    change = multiplier * K_FACTOR * (score - expected)
    if change < 0 and curr_rating <= RATING_MIN:
        return RATING_MIN, 0  # Return min rating and no change
    new_rating = curr_rating + change
    new_rating = round(new_rating)
    if new_rating < RATING_MIN:
        new_rating = RATING_MIN
    if new_rating > RATING_MAX:
        new_rating = RATING_MAX
    return new_rating, change  # Return new rating and change

def parse_team(team_str):
    team_str = team_str.strip()
    if ";" in team_str:
        offense_part, defense_part = team_str.split(";", 1)
        offense_players = [p.strip() for p in offense_part.split(",") if p.strip()]
        defense_players = [p.strip() for p in defense_part.split(",") if p.strip()]
    else:
        offense_players = [p.strip() for p in team_str.split(",") if p.strip()]
        defense_players = []
    return offense_players, defense_players

def print_best_players():
    if not players:
        print("No player data available.")
        return
    
    best_avg = max(players.items(), key=lambda kv: kv[1]["avg"])
    best_offense = max(players.items(), key=lambda kv: kv[1]["offense"])
    best_defense = max(players.items(), key=lambda kv: kv[1]["defense"])
    most_played = max(players.items(), key=lambda kv: kv[1]["played"])
    highest_win_rate = max(players.items(), key=lambda kv: (kv[1]["wins"] / kv[1]["played"]) if kv[1]["played"] > 0 else 0)

    print("Best Players:")
    print(f"Best Average: {best_avg[1]['display']} (A-{best_avg[1]['avg']})")
    print(f"Best Offense: {best_offense[1]['display']} (O-{best_offense[1]['offense']})")
    print(f"Best Defense: {best_defense[1]['display']} (D-{best_defense[1]['defense']})")
    print(f"Most Time Played: {most_played[1]['display']} (T-{most_played[1]['played']})")
    win_rate = (highest_win_rate[1]["wins"] / highest_win_rate[1]["played"]) * 100 if highest_win_rate[1]["played"] > 0 else 0
    print(f"Highest Win Rate: {highest_win_rate[1]['display']} (R-{win_rate:.2f}%)")

    #best

def get_average_rating(names, role):
    if not names:
        return None
    total = 0
    count = 0
    for name in names:
        data = get_or_create_player(name)
        total += data[role]
        count += 1
    return total / count if count > 0 else 0

def calculate_expected_win_rate(player_rating, opponent_rating):
    expected = 1 / (1 + math.pow(10, (opponent_rating - player_rating) / 400))
    return expected * 100  # Return as percentage

def process_game(command):
    pattern = r"^(.*?)\s*(win|smallwin|closewin|bigwin|perfectwin)\s*(.*?)$"
    match = re.match(pattern, command, re.IGNORECASE)
    if not match:
        print("Command format not recognized. Please try again.")
        return
    team1_str, win_type, team2_str = match.groups()
    win_type = win_type.lower().strip()
    if win_type not in WIN_TYPE_MULTIPLIERS:
        print("Invalid win type.")
        return
    base_multiplier = WIN_TYPE_MULTIPLIERS[win_type]
    team1_off, team1_def = parse_team(team1_str)
    team2_off, team2_def = parse_team(team2_str)

    # Create or get players
    for name in team1_off + team1_def + team2_off + team2_def:
        get_or_create_player(name)

    # Determine average opponent ratings
    opp_for_team1 = get_average_rating(team2_def, "defense") if team2_def else get_average_rating(team2_off, "offense")
    opp_off_team1 = get_average_rating(team2_off, "offense") if team2_off else get_average_rating(team2_def, "defense")
    opp_for_team2 = get_average_rating(team1_def, "defense") if team1_def else get_average_rating(team1_off, "offense")
    opp_off_team2 = get_average_rating(team1_off, "offense") if team1_off else get_average_rating(team1_def, "defense")

    # Update ratings for team 1
    for name in team1_off:
        player = get_or_create_player(name)
        new_off, change_off = update_rating(player["offense"], 1, opp_for_team1 if opp_for_team1 is not None else 1500, base_multiplier)
        player["offense"] = new_off
        player["played"] += 1
        player["wins"] += 1
        print("--------------------------------------------------------------------------------")
        print(f"{player['display']} - Off rate change: {change_off:.2f}")

    for name in team1_def:
        player = get_or_create_player(name)
        new_def, change_def = update_rating(player["defense"], 1, opp_off_team1 if opp_off_team1 is not None else 1500, base_multiplier)
        player["defense"] = new_def
        player["played"] += 1
        print(f"{player['display']} - Def rate: {change_def:.2f}")

    # Update ratings for team 2
    for name in team2_off:
        player = get_or_create_player(name)
        new_off, change_off = update_rating(player["offense"], 0, opp_for_team2 if opp_for_team2 is not None else 1500, base_multiplier)
        player["offense"] = new_off
        player["played"] += 1
        print(f"{player['display']} - Off rate change: {change_off:.2f}")

    for name in team2_def:
        player = get_or_create_player(name)
        new_def, change_def = update_rating(player["defense"], 0, opp_off_team2 if opp_off_team2 is not None else 1500, base_multiplier)
        player["defense"] = new_def
        player["played"] += 1
        print(f"{player['display']} - Def rating change: {change_def:.2f}")

    print("--------------------------------------------------------------------------------")

    namelist1 = []
    namelist2 = []
    winrates1 = []
    winrates2 = []

    # Print expected win rates
    for name in team1_off + team1_def:
        player = players[canonicalize(name)]
        expected_win_rate = calculate_expected_win_rate(player["offense"], opp_for_team1)
        print(f"{player['display']}: {expected_win_rate:.2f}%")
        namelist1.append(player['display'])  # Use f-string without quotes
        winrates1.append(expected_win_rate)   # Store as a number

    for name in team2_off + team2_def:
        player = players[canonicalize(name)]
        expected_win_rate = calculate_expected_win_rate(player["defense"], opp_off_team2)
        print(f"{player['display']}: {expected_win_rate:.2f}%")
        namelist2.append(player['display'])  # Use f-string without quotes
        winrates2.append(expected_win_rate)   # Store as a number

    print("--------------------------------------------------------------------------------")

    # Calculate average win rates
    le1 = len(winrates1)
    if le1 == 2:
        avg_winrate1 = (winrates1[0] + winrates1[1]) / 2
    else:
        avg_winrate1 = winrates1[0]  # Only one player

    le2 = len(winrates2)
    if le2 == 2:
        avg_winrate2 = (winrates2[0] + winrates2[1]) / 2
    else:
        avg_winrate2 = winrates2[0]  # Only one player

    # Prepare team names for printing
    team1_display = f"{namelist1[0]} + {namelist1[1]}" if le1 == 2 else namelist1[0]
    team2_display = f"{namelist2[0]} + {namelist2[1]}" if le2 == 2 else namelist2[0]

    print(f"{team1_display} = {avg_winrate1:.2f}% vs {team2_display} = {avg_winrate2:.2f}%")

    print("--------------------------------------------------------------------------------")


    for key in players:
        update_player_avg(key)

    save_data()
    print("Game processed and ratings updated.")


def main():
    load_data()
    save_data()
    print("Foosball Elo rating system started.")
    print("Commands:")
    print(" - teama typewin teamb  (e.g., \"JustinCheng ; LarryZhong closewin ParkerHoppy ; ThayerMahan\")")
    print(" - Type 'pp' to print player statistics (sorted by average rating).")
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
        elif command == "":
            continue
        else:
            process_game(command)

if __name__ == '__main__':
    main()
