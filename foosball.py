#!/usr/bin/env python3
import customtkinter as ctk
import tkinter as tk
import sys
import math
import os
import re
import random
import string

# ==============================================================================
#
# ELO LOGIC CORE
# This class encapsulates all the original logic from your script.
#
# ==============================================================================
class EloLogic:
    def __init__(self):
        # --- Constants ---
        self.FILE_NAME = "elo.txt"
        self.K_FACTOR = 32
        self.RATING_MIN = 100
        self.RATING_MAX = 2999
        self.WIN_TYPE_MULTIPLIERS = {
            "win": 1.0, "smallwin": 0.75, "closewin": 0.5,
            "bigwin": 1.25, "perfectwin": 1.5
        }
        self.RANK_THRESHOLDS = [
            (2999, "ultra"), (2900, "grand-master"), (2666, "super-master"),
            (2468, "master"), (2222, "diamond"), (1650, "emerald"),
            (1234, "jade"), (850, "plat"), (450, "gold"), (250, "silver"),
            (200, "copper"), (150, "bronze"), (125, "steel"), (99, "iron")
        ]
        self.HIDDEN_RANK = "lz"
        self.SPECIAL_IM = "im"
        self.RANK_ORDER = {
            "iron": 0, "steel": 1, "bronze": 2, "copper": 3, "silver": 4,
            "gold": 5, "plat": 6, "jade": 7, "emerald": 8, "diamond": 9,
            "master": 10, "super-master": 11, "grand-master": 12, "ultra": 13,
            self.HIDDEN_RANK: 13, self.SPECIAL_IM: 13
        }
        self.RANK_PROTECTION_THRESHOLDS = [
            (150, 34), (200, 21), (400, 13), (850, 8), (1234, 5), (1650, 3),
            (2222, 2), (2468, 1), (2666, 0), (2900, -1), (float('inf'), -2)
        ]
        
        # --- State ---
        self.players = {}
        self.load_data()

    def canonicalize(self, name):
        return ''.join(c for c in name.lower() if c.isalnum())

    def get_hidden_rank(self):
        letters = string.ascii_lowercase
        return "L" + ''.join(random.choice(letters) for _ in range(4)) + "Z" + ''.join(random.choice(letters) for _ in range(4))

    def get_rank_display(self, rank):
        if rank == self.HIDDEN_RANK: return self.get_hidden_rank()
        if rank == self.SPECIAL_IM: return "importal"
        return rank

    def get_computed_rank(self, score):
        for threshold, rank in self.RANK_THRESHOLDS:
            if score >= threshold:
                return rank
        return "iron"

    def get_or_create_player(self, name):
        key = self.canonicalize(name)
        if key not in self.players:
            self.players[key] = {
                "display": name, "offense": self.RATING_MIN, "defense": self.RATING_MIN,
                "played": 0, "wins": 0, "avg": self.RATING_MIN,
                "rank_d": self.get_computed_rank(self.RATING_MIN),
                "rank_o": self.get_computed_rank(self.RATING_MIN),
                "rank_a": self.get_computed_rank(self.RATING_MIN)
            }
            if "zhong" in key:
                self.players[key]["rank_d"] = self.HIDDEN_RANK
                self.players[key]["rank_o"] = self.HIDDEN_RANK
                self.players[key]["rank_a"] = self.HIDDEN_RANK
        return self.players[key]

    def load_data(self):
        if not os.path.exists(self.FILE_NAME): return
        with open(self.FILE_NAME, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip().rstrip(".")
                if not line: continue
                parts = [x.strip() for x in line.split(",")]
                if len(parts) < 5: continue
                
                try:
                    disp, off, deff, played, win_rate = parts[0], int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                    canon = self.canonicalize(disp)
                    wins = round((win_rate / 100) * played) if played > 0 else 0
                    avg = int(parts[5]) if len(parts) >= 6 and parts[5].isdigit() else round((off + deff) / 2)
                    rank_d = parts[6] if len(parts) >= 7 else self.get_computed_rank(deff)
                    rank_o = parts[7] if len(parts) >= 8 else self.get_computed_rank(off)
                    rank_a = parts[8] if len(parts) >= 9 else self.get_computed_rank(avg)

                    self.players[canon] = {
                        "display": disp, "offense": off, "defense": deff,
                        "played": played, "wins": wins, "avg": avg,
                        "rank_d": rank_d, "rank_o": rank_o, "rank_a": rank_a
                    }
                    if "zhong" in canon:
                        self.players[canon].update({"rank_d": self.HIDDEN_RANK, "rank_o": self.HIDDEN_RANK, "rank_a": self.HIDDEN_RANK})
                except (ValueError, IndexError):
                    continue

    def save_data(self):
        for key in self.players:
            data = self.players[key]
            data["avg"] = round((data["offense"] + data["defense"]) / 2)
        
        sorted_players = sorted(self.players.items(), key=lambda kv: (-kv[1]["avg"], kv[1]["display"]))
        with open(self.FILE_NAME, "w", encoding="utf-8") as f:
            for _, data in sorted_players:
                win_rate = round((data["wins"] / data["played"]) * 100) if data["played"] > 0 else 0
                f.write(
                    f"{data['display']}, {data['offense']}, {data['defense']}, {data['played']}, {win_rate}, {data['avg']}, "
                    f"{data.get('rank_d', 'iron')}, {data.get('rank_o', 'iron')}, {data.get('rank_a', 'iron')}.\n"
                )
        print("Data saved successfully.")

    def update_rating(self, curr_rating, score, opposition_rating, multiplier):
        expected = 1 / (1 + math.pow(10, (opposition_rating - curr_rating) / 400))
        change = multiplier * self.K_FACTOR * (score - expected)
        
        adjustment = 0
        for threshold, adj in self.RANK_PROTECTION_THRESHOLDS:
            if curr_rating <= threshold:
                adjustment = adj
                break
        
        if score in (0, 1):
            change += adjustment
            if score == 0: change = min(change, 0)
        
        if change < 0 and curr_rating <= self.RATING_MIN: return self.RATING_MIN, 0
        
        new_rating = max(min(round(curr_rating + change), self.RATING_MAX), self.RATING_MIN)
        return new_rating, new_rating - curr_rating

    def process_game(self, command):
        pattern = r"^(.*?)\s*(win|smallwin|closewin|bigwin|perfectwin)\s*(.*?)$"
        match = re.match(pattern, command, re.IGNORECASE)
        if not match:
            print("❌ Invalid game format. Use: player1, player2 win player3, player4")
            return

        team1_str, win_type, team2_str = match.groups()
        win_type = win_type.lower()

        def parse_team(team_str):
            off = [p.strip() for p in team_str.split(";")[-1].split(",") if p.strip()]
            deff = [p.strip() for p in team_str.split(";")[0].split(",") if p.strip()] if ";" in team_str else []
            return off, deff

        team1_off, team1_def = parse_team(team1_str)
        team2_off, team2_def = parse_team(team2_str)
        
        all_player_names = team1_off + team1_def + team2_off + team2_def
        if not all_player_names:
            print("❌ No players found in command.")
            return

        for name in all_player_names: self.get_or_create_player(name)

        def get_avg_rating(names, role):
            if not names: return None
            return sum(self.get_or_create_player(n)[role] for n in names) / len(names)

        # Determine opponent ratings for calculation
        opp_def_for_t1_off = get_avg_rating(team2_def, "defense") or get_avg_rating(team2_off, "avg")
        opp_off_for_t1_def = get_avg_rating(team2_off, "offense") or get_avg_rating(team2_def, "avg")
        opp_def_for_t2_off = get_avg_rating(team1_def, "defense") or get_avg_rating(team1_off, "avg")
        opp_off_for_t2_def = get_avg_rating(team1_off, "offense") or get_avg_rating(team1_def, "avg")

        print("📊 Rating Changes:")
        # --- Update Team 1 (Winners) ---
        for name in team1_off:
            p = self.get_or_create_player(name)
            new_r, change = self.update_rating(p["offense"], 1, opp_def_for_t1_off, self.WIN_TYPE_MULTIPLIERS[win_type])
            print(f"  - {p['display']} (O): {p['offense']} → {new_r} ({change:+.0f})")
            p.update({"offense": new_r, "played": p["played"] + 1, "wins": p["wins"] + 1})
        for name in team1_def:
            p = self.get_or_create_player(name)
            new_r, change = self.update_rating(p["defense"], 1, opp_off_for_t1_def, self.WIN_TYPE_MULTIPLIERS[win_type])
            print(f"  - {p['display']} (D): {p['defense']} → {new_r} ({change:+.0f})")
            p.update({"defense": new_r, "played": p["played"] + 1, "wins": p["wins"] + 1})

        # --- Update Team 2 (Losers) ---
        for name in team2_off:
            p = self.get_or_create_player(name)
            new_r, change = self.update_rating(p["offense"], 0, opp_def_for_t2_off, self.WIN_TYPE_MULTIPLIERS[win_type])
            print(f"  - {p['display']} (O): {p['offense']} → {new_r} ({change:+.0f})")
            p.update({"offense": new_r, "played": p["played"] + 1})
        for name in team2_def:
            p = self.get_or_create_player(name)
            new_r, change = self.update_rating(p["defense"], 0, opp_off_for_t2_def, self.WIN_TYPE_MULTIPLIERS[win_type])
            print(f"  - {p['display']} (D): {p['defense']} → {new_r} ({change:+.0f})")
            p.update({"defense": new_r, "played": p["played"] + 1})
            
        self.save_data()

    def print_players(self, filter_rank=None):
        if not self.players:
            print("No player data available.")
            return

        sorted_list = sorted(self.players.values(), key=lambda p: (-p["avg"], p["display"]))
        
        if filter_rank:
            valid_ranks = {r[1] for r in self.RANK_THRESHOLDS}
            if filter_rank not in valid_ranks:
                print(f"❌ Invalid rank '{filter_rank}'. Valid ranks are: {', '.join(valid_ranks)}")
                return
            sorted_list = [p for p in sorted_list if self.get_computed_rank(p['avg']) == filter_rank]

        header = f"{'#':<3} {'Name':<15} {'Avg':>5} {'Off':>5} {'Def':>5} {'Games':>5} {'Win%':>5} {'Rank':<15}"
        print("🏆 Player Rankings:")
        print(header)
        print("-" * len(header))
        for idx, data in enumerate(sorted_list, 1):
            win_rate = round((data["wins"] / data["played"]) * 100) if data["played"] > 0 else 0
            rank = self.get_rank_display(self.get_computed_rank(data['avg']))
            print(f"{idx:<3} {data['display']:<15} {data['avg']:>5} {data['offense']:>5} {data['defense']:>5} {data['played']:>5} {win_rate:>4.0f}% {rank:<15}")

    def print_best_players(self):
        if not self.players:
            print("No player data available.")
            return
        
        print("⭐ Top Performers:")
        best_avg = max(self.players.values(), key=lambda x: x["avg"])
        best_off = max(self.players.values(), key=lambda x: x["offense"])
        best_def = max(self.players.values(), key=lambda x: x["defense"])
        most_played = max(self.players.values(), key=lambda x: x["played"])
        
        # Filter for players with a minimum number of games for meaningful win rate
        min_games = 5
        eligible_players = [p for p in self.players.values() if p["played"] >= min_games]
        if eligible_players:
            highest_win = max(eligible_players, key=lambda x: (x["wins"] / x["played"]))
            win_rate = (highest_win["wins"] / highest_win["played"]) * 100
            print(f"  - Highest Win Rate (>{min_games} games): {highest_win['display']} ({win_rate:.1f}%)")
        
        print(f"  - Best Average: {best_avg['display']} (A-{best_avg['avg']})")
        print(f"  - Best Offense: {best_off['display']} (O-{best_off['offense']})")
        print(f"  - Best Defense: {best_def['display']} (D-{best_def['defense']})")
        print(f"  - Most Played:  {most_played['display']} (T-{most_played['played']})")

    def process_combine_command(self, command):
        match = re.match(r"^combine\s+(.*?)\s+to\s+(.*?)\.?$", command, re.IGNORECASE)
        if not match:
            print("❌ Invalid format. Use: combine <old_name> to <new_name>")
            return
        
        src_name, dest_name = match.group(1).strip(), match.group(2).strip()
        src_key, dest_key = self.canonicalize(src_name), self.canonicalize(dest_name)
        
        if src_key not in self.players or dest_key not in self.players:
            print("❌ One or both players not found.")
            return

        src, dest = self.players[src_key], self.players[dest_key]
        total_played = src["played"] + dest["played"]
        if total_played > 0:
            dest["offense"] = round((dest["offense"] * dest["played"] + src["offense"] * src["played"]) / total_played)
            dest["defense"] = round((dest["defense"] * dest["played"] + src["defense"] * src["played"]) / total_played)
        dest["played"] = total_played
        dest["wins"] += src["wins"]
        
        del self.players[src_key]
        print(f"✅ Merged '{src_name}' into '{dest_name}'.")
        self.save_data()

    def process_name_command(self):
        if not self.players:
            print("No player data available.")
            return
            
        sorted_list = sorted(self.players.values(), key=lambda p: p["display"].lower())
        print("📋 Player List (Alphabetical):")
        for data in sorted_list:
            win_rate = round((data["wins"] / data["played"]) * 100) if data["played"] > 0 else 0
            print(f"  - {data['display']:<15} | Avg: {data['avg']}, Off: {data['offense']}, Def: {data['defense']}, Played: {data['played']}, Win: {win_rate}%")


# ==============================================================================
#
# GUI APPLICATION
# This class builds the user interface and handles user interaction.
#
# ==============================================================================

class TextboxRedirector:
    """Redirects print() statements to a CTkTextbox widget."""
    def __init__(self, textbox):
        self.textbox = textbox

    def write(self, text):
        self.textbox.insert("end", text)
        self.textbox.see("end") # Auto-scroll

    def flush(self):
        pass

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.elo_logic = EloLogic()

        # --- Window Setup ---
        self.title("Foosball ELO Tracker")
        self.geometry("800x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Widgets ---
        # Top frame for buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")

        # Main output textbox
        self.output_textbox = ctk.CTkTextbox(self, font=("Consolas", 12))
        self.output_textbox.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.output_textbox.insert("end", "Welcome to the Foosball ELO System!\n")
        self.output_textbox.configure(state="disabled") # Make it read-only

        # Bottom frame for input
        input_frame = ctk.CTkFrame(self)
        input_frame.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.command_entry = ctk.CTkEntry(input_frame, placeholder_text="Enter command or game result...")
        self.command_entry.grid(row=0, column=0, padx=(5,0), pady=5, sticky="ew")

        # --- Suggestion Box ---
        self.suggestion_listbox = tk.Listbox(input_frame, bg="#2A2D2E", fg="white", selectbackground="#1F6AA5",
                                             highlightthickness=0, borderwidth=1, relief="flat", font=("Arial", 11))
        # Place it initially off-screen
        self.suggestion_listbox.place(x=-1000, y=-1000)

        # --- Buttons ---
        self.pp_button = ctk.CTkButton(button_frame, text="Show All Players (pp)", command=lambda: self.run_command("pp"))
        self.pp_button.pack(side="left", padx=5)

        self.best_button = ctk.CTkButton(button_frame, text="Best Players", command=lambda: self.run_command("best"))
        self.best_button.pack(side="left", padx=5)
        
        self.name_button = ctk.CTkButton(button_frame, text="List Names", command=lambda: self.run_command("name"))
        self.name_button.pack(side="left", padx=5)

        self.save_button = ctk.CTkButton(button_frame, text="Save & Exit", command=self.on_exit)
        self.save_button.pack(side="right", padx=5)

        # --- Bindings ---
        self.command_entry.bind("<Return>", self.execute_command_from_entry)
        self.command_entry.bind("<KeyRelease>", self.update_suggestions)
        self.suggestion_listbox.bind("<Double-Button-1>", self.on_suggestion_select)
        self.bind("<Button-1>", self.hide_suggestions) # Hide when clicking away
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

        # --- Redirect stdout ---
        self.redirector = TextboxRedirector(self.output_textbox)
        sys.stdout = self.redirector

    def run_command(self, cmd_text):
        """A generic function to run a command and display its output."""
        self.output_textbox.configure(state="normal")
        print(f"\n> {cmd_text}\n" + "-"*40)
        
        if cmd_text.lower().startswith("pp"):
            parts = cmd_text.strip().split()
            filter_rank = parts[1].lower() if len(parts) > 1 else None
            self.elo_logic.print_players(filter_rank)
        elif cmd_text.lower() == "best":
            self.elo_logic.print_best_players()
        elif cmd_text.lower().startswith("combine"):
            self.elo_logic.process_combine_command(cmd_text)
        elif cmd_text.lower() == "name":
            self.elo_logic.process_name_command()
        else:
            self.elo_logic.process_game(cmd_text)

        self.output_textbox.configure(state="disabled")

    def execute_command_from_entry(self, event=None):
        """Executes command from the entry box."""
        command = self.command_entry.get()
        if command:
            self.run_command(command)
            self.command_entry.delete(0, "end")
        self.hide_suggestions()

    def update_suggestions(self, event=None):
        """Update and show the suggestion listbox based on entry text."""
        if event.keysym in ("Return", "Up", "Down", "Escape"): 
            self.hide_suggestions()
            return

        text = self.command_entry.get()
        words = text.split()
        
        if not text or text.endswith(" "):
            current_word = ""
            context_words = words
        else:
            current_word = words[-1]
            context_words = words[:-1]

        suggestions = set()
        player_names = [p['display'] for p in self.elo_logic.players.values()]
        win_types = list(self.elo_logic.WIN_TYPE_MULTIPLIERS.keys())
        commands = ["pp", "best", "combine", "name"]
        ranks = [r[1] for r in self.elo_logic.RANK_THRESHOLDS]

        # Context-based suggestion logic
        if not context_words: # First word
            suggestions.update(commands)
            suggestions.update(player_names)
        elif context_words[0] == "pp" and len(context_words) == 1:
            suggestions.update(ranks)
        elif context_words[0] == "combine":
            suggestions.update(player_names)
            if len(context_words) == 2: suggestions.add("to")
        else: # Likely a game result
            suggestions.update(player_names)
            if not any(w in win_types for w in context_words):
                suggestions.update(win_types)
        
        filtered_suggestions = sorted([s for s in suggestions if s.lower().startswith(current_word.lower())])
        
        if filtered_suggestions:
            self.suggestion_listbox.delete(0, "end")
            for item in filtered_suggestions:
                self.suggestion_listbox.insert("end", item)
            
            x = self.command_entry.winfo_x() + self.winfo_x() + 10
            y = self.command_entry.winfo_y() + self.command_entry.winfo_height() + self.winfo_y() + 5
            width = self.command_entry.winfo_width()
            self.suggestion_listbox.place(x=x, y=y, width=width)
        else:
            self.hide_suggestions()

    def on_suggestion_select(self, event=None):
        """Autocomplete the entry with the selected suggestion."""
        selection = self.suggestion_listbox.get(self.suggestion_listbox.curselection())
        text = self.command_entry.get()
        
        if text.endswith(" "):
            new_text = text + selection + " "
        else:
            last_space = text.rfind(" ")
            new_text = text[:last_space+1] + selection + " "
            
        self.command_entry.delete(0, "end")
        self.command_entry.insert(0, new_text)
        self.hide_suggestions()
        self.command_entry.focus_set()

    def hide_suggestions(self, event=None):
        self.suggestion_listbox.place_forget()

    def on_exit(self):
        """Handle window close event."""
        sys.stdout = sys.__stdout__ # Restore stdout
        self.elo_logic.save_data()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
