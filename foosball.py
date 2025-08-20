#!/usr/bin/env python3

import math
import os
import re
import random
import string
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from tkinter.font import Font

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
    (2999, "ultra"),
    (2900, "grand-master"),
    (2666, "super-master"),
    (2468, "master"),
    (2222, "diamond"),
    (1650, "emerald"),
    (1234, "jade"),
    (850, "plat"),
    (450, "gold"),
    (250, "silver"),
    (200, "copper"),
    (150, "bronze"),
    (125, "steel"),
    (99,   "iron")
]

# Special values for hidden and special ranks.
HIDDEN_RANK = "lz"  # when a player should be hidden
SPECIAL_IM = "im"   # special flag printed as "importal"

# Order for comparing ranking strings (the full words). 
RANK_ORDER = {
    "iron": 0,
    "steel": 1,
    "bronze": 2,
    "copper": 3,
    "silver": 4,
    "gold": 5,
    "plat": 6,
    "jade": 7,
    "emerald": 8,
    "diamond": 9,
    "master": 10,
    "super-master": 11,
    "grand-master": 12,
    "ultra": 13,
    HIDDEN_RANK: 13,
    SPECIAL_IM: 13  # treat im as highest; will print as "importal"
}

# Dictionary for converting a full rank to its initial letter.
RANK_INITIAL = {
    "iron": "i",
    "steel": "t",
    "copper": "c",
    "silver": "s",
    "gold": "g",
    "plat": "p",
    "jade": "j",
    "emerald": "e",
    "diamond": "d",
    "master":"m",
    "super-master": "p",
    "grand-master": "r",
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

def get_players_data(filter_rank=None):
    if not players:
        return []
    
    valid_ranks = [rank for (_, rank) in RANK_THRESHOLDS]
    if filter_rank is not None:
        if filter_rank not in valid_ranks:
            return []
        filtered_players = []
        for key, data in players.items():
            ranks = [data.get("rank_o", "iron"), data.get("rank_d", "iron"), data.get("rank_a", "iron")]
            valid_player_ranks = [r for r in ranks if r not in (HIDDEN_RANK, SPECIAL_IM)]
            if not valid_player_ranks:
                continue
            highest_rank = max(valid_player_ranks, key=lambda r: RANK_ORDER[r])
            if highest_rank == filter_rank:
                filtered_players.append((key, data))
        sorted_list = sorted(filtered_players, key=lambda kv: (-kv[1]["avg"], kv[1]["display"]))
    else:
        sorted_list = sorted(players.items(), key=lambda kv: (-kv[1]["avg"], kv[1]["display"]))
    
    result = []
    for idx, (key, data) in enumerate(sorted_list, start=1):
        played = data["played"]
        wins = data["wins"]
        win_rate = round((wins / played) * 100) if played > 0 else 0
        overall_rank = highest_overall_rank(key)
        indicator = get_rank_indicator(key)
        rank_display = overall_rank + indicator
        result.append((idx, data['display'], data['avg'], data['offense'], data['defense'], played, win_rate, rank_display))
    
    return result

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

def adjust_opponent_rating(opposition_rating, curr_rating):
    return opposition_rating

# Adjust change, Numero di Fibonacci protection 斐波那契数列排位保护机制
RATING_PROTECTION_THRESHOLDS = [(150, 34),(200, 21),(400, 13),(850, 8),(1234, 5),(1650, 3),(2222, 2),(2468, 1),(2666, 0),(2900, -1),(float('inf'), -2)]

def update_rating(curr_rating, score, opposition_rating, multiplier):
    expected = 1 / (1 + math.pow(10, (adjust_opponent_rating(opposition_rating, curr_rating) - curr_rating) / 400))
    change = multiplier * K_FACTOR * (score - expected)
    
    # 排位保护机制
    adjustment = 0
    for threshold, adj in RATING_PROTECTION_THRESHOLDS:
        if curr_rating <= threshold:
            adjustment = adj
            break
    
    # 处理加分/减分逻辑
    if score in (0, 1):
        change += adjustment
        # 失败时禁止加分
        if score == 0:
            change = min(change, 0)
    
    # 处理最低评分保护
    if change < 0 and curr_rating <= RATING_MIN:
        return RATING_MIN, 0
    
    # 计算最终评分
    new_rating = curr_rating + change
    new_rating = round(new_rating)
    new_rating = max(min(new_rating, RATING_MAX), RATING_MIN)
    
    return new_rating, change

class ELOSystemGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🏆 Foosball ELO System")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e2e')
        
        # Load data on startup
        load_data()
        
        # Style configuration
        self.setup_styles()
        
        # Create main layout
        self.create_layout()
        
        # Command suggestions
        self.command_suggestions = []
        self.current_suggestions = []
        
        # Bind events
        self.setup_bindings()
        
        # Initial display
        self.refresh_display()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#89b4fa', background='#1e1e2e')
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), foreground='#cdd6f4', background='#313244')
        style.configure('Custom.TButton', font=('Arial', 10, 'bold'), foreground='#1e1e2e')
        style.configure('Treeview', background='#313244', foreground='#cdd6f4', fieldbackground='#313244')
        style.configure('Treeview.Heading', background='#45475a', foreground='#cdd6f4', font=('Arial', 10, 'bold'))

    def create_layout(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#1e1e2e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="🏆 Foosball ELO System", style='Title.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Players tab
        self.create_players_tab()
        
        # Game input tab
        self.create_game_tab()
        
        # Command line tab
        self.create_command_tab()

    def create_players_tab(self):
        players_frame = tk.Frame(self.notebook, bg='#1e1e2e')
        self.notebook.add(players_frame, text="📊 Players")
        
        # Control panel
        control_frame = tk.Frame(players_frame, bg='#1e1e2e')
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Rank filter
        tk.Label(control_frame, text="Filter by rank:", bg='#1e1e2e', fg='#cdd6f4', font=('Arial', 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.rank_filter = ttk.Combobox(control_frame, values=['All'] + [rank for _, rank in RANK_THRESHOLDS], width=15)
        self.rank_filter.set('All')
        self.rank_filter.pack(side=tk.LEFT, padx=(0, 10))
        self.rank_filter.bind('<<ComboboxSelected>>', self.on_rank_filter_change)
        
        # Refresh button
        refresh_btn = ttk.Button(control_frame, text="🔄 Refresh", command=self.refresh_display, style='Custom.TButton')
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Best players button
        best_btn = ttk.Button(control_frame, text="🏅 Show Best", command=self.show_best_players, style='Custom.TButton')
        best_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Export names button
        names_btn = ttk.Button(control_frame, text="📋 Export Names", command=self.show_names, style='Custom.TButton')
        names_btn.pack(side=tk.LEFT)
        
        # Players table
        self.create_players_table(players_frame)
        
        # Info panel
        self.create_info_panel(players_frame)

    def create_players_table(self, parent):
        # Table frame
        table_frame = tk.Frame(parent, bg='#1e1e2e')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Treeview
        columns = ('No.', 'Name', 'Avg', 'Off', 'Def', 'Games', 'Win%', 'Rank')
        self.players_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        self.players_tree.heading('No.', text='No.')
        self.players_tree.heading('Name', text='Name')
        self.players_tree.heading('Avg', text='Avg')
        self.players_tree.heading('Off', text='Off')
        self.players_tree.heading('Def', text='Def')
        self.players_tree.heading('Games', text='Games')
        self.players_tree.heading('Win%', text='Win%')
        self.players_tree.heading('Rank', text='Rank')
        
        # Column widths
        self.players_tree.column('No.', width=50, anchor='center')
        self.players_tree.column('Name', width=150, anchor='w')
        self.players_tree.column('Avg', width=70, anchor='center')
        self.players_tree.column('Off', width=70, anchor='center')
        self.players_tree.column('Def', width=70, anchor='center')
        self.players_tree.column('Games', width=70, anchor='center')
        self.players_tree.column('Win%', width=70, anchor='center')
        self.players_tree.column('Rank', width=150, anchor='w')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.players_tree.yview)
        self.players_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.players_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_info_panel(self, parent):
        info_frame = tk.Frame(parent, bg='#313244', relief=tk.RAISED, bd=1)
        info_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        info_label = ttk.Label(info_frame, text="ℹ️ Rank Thresholds", style='Header.TLabel')
        info_label.pack(pady=5)
        
        thresholds_text = ("iron: 100, bronze: 150, copper: 200, silver: 250, gold: 450, "
                          "platinum: 850, jade: 1234, emerald: 1650, diamond: 2222, "
                          "master: 2468, super/grand-master: 2666/2900, ultra: 2999")
        
        info_content = tk.Label(info_frame, text=thresholds_text, bg='#313244', fg='#cdd6f4', 
                               font=('Arial', 9), wraplength=1000, justify=tk.LEFT)
        info_content.pack(padx=10, pady=(0, 10))

    def create_game_tab(self):
        game_frame = tk.Frame(self.notebook, bg='#1e1e2e')
        self.notebook.add(game_frame, text="⚽ New Game")
        
        # Title
        title = ttk.Label(game_frame, text="🎮 Record New Game", style='Title.TLabel')
        title.pack(pady=20)
        
        # Input frame
        input_frame = tk.Frame(game_frame, bg='#313244', relief=tk.RAISED, bd=2)
        input_frame.pack(padx=50, pady=20, fill=tk.X)
        
        # Team 1 input
        tk.Label(input_frame, text="Team 1 (Winners):", bg='#313244', fg='#a6e3a1', 
                font=('Arial', 12, 'bold')).pack(anchor=tk.W, padx=20, pady=(20, 5))
        
        self.team1_entry = tk.Entry(input_frame, font=('Arial', 11), width=60, bg='#45475a', fg='#cdd6f4',
                                   insertbackground='#cdd6f4', relief=tk.FLAT, bd=5)
        self.team1_entry.pack(padx=20, pady=(0, 10))
        
        # Win type selection
        tk.Label(input_frame, text="Win Type:", bg='#313244', fg='#cdd6f4', 
                font=('Arial', 12, 'bold')).pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        win_frame = tk.Frame(input_frame, bg='#313244')
        win_frame.pack(padx=20, pady=(0, 10))
        
        self.win_type = tk.StringVar(value='win')
        win_types = [
            ('win', 'Regular Win (1.0x)', '#89b4fa'),
            ('smallwin', 'Small Win (0.75x)', '#94e2d5'),
            ('closewin', 'Close Win (0.5x)', '#f9e2af'),
            ('bigwin', 'Big Win (1.25x)', '#fab387'),
            ('perfectwin', 'Perfect Win (1.5x)', '#f38ba8')
        ]
        
        for i, (value, text, color) in enumerate(win_types):
            row = i // 3
            col = i % 3
            rb = tk.Radiobutton(win_frame, text=text, variable=self.win_type, value=value,
                               bg='#313244', fg=color, selectcolor='#45475a', 
                               font=('Arial', 10), activebackground='#313244')
            rb.grid(row=row, column=col, sticky=tk.W, padx=10, pady=2)
        
        # Team 2 input
        tk.Label(input_frame, text="Team 2 (Losers):", bg='#313244', fg='#f38ba8', 
                font=('Arial', 12, 'bold')).pack(anchor=tk.W, padx=20, pady=(20, 5))
        
        self.team2_entry = tk.Entry(input_frame, font=('Arial', 11), width=60, bg='#45475a', fg='#cdd6f4',
                                   insertbackground='#cdd6f4', relief=tk.FLAT, bd=5)
        self.team2_entry.pack(padx=20, pady=(0, 20))
        
        # Instructions
        instructions = ("Format: player1, player2 OR offense_players ; defense_players\n"
                       "Example: John, Mary OR John, Mary ; Bob, Alice")
        tk.Label(input_frame, text=instructions, bg='#313244', fg='#6c7086', 
                font=('Arial', 9), justify=tk.CENTER).pack(pady=(0, 15))
        
        # Submit button
        submit_btn = ttk.Button(input_frame, text="🏆 Record Game", command=self.process_gui_game, 
                               style='Custom.TButton')
        submit_btn.pack(pady=(0, 20))
        
        # Results area
        self.game_results = scrolledtext.ScrolledText(game_frame, height=15, bg='#45475a', fg='#cdd6f4',
                                                     font=('Consolas', 10), insertbackground='#cdd6f4')
        self.game_results.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    def create_command_tab(self):
        command_frame = tk.Frame(self.notebook, bg='#1e1e2e')
        self.notebook.add(command_frame, text="💻 Command Line")
        
        # Title
        title = ttk.Label(command_frame, text="💻 Command Line Interface", style='Title.TLabel')
        title.pack(pady=20)
        
        # Quick commands
        quick_frame = tk.Frame(command_frame, bg='#313244', relief=tk.RAISED, bd=2)
        quick_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Label(quick_frame, text="Quick Commands:", bg='#313244', fg='#cdd6f4', 
                font=('Arial', 12, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        button_frame = tk.Frame(quick_frame, bg='#313244')
        button_frame.pack(padx=10, pady=(0, 10))
        
        quick_commands = [
            ("pp", "Show Players", self.cmd_show_players),
            ("best", "Show Best", self.cmd_show_best),
            ("name", "Export Names", self.cmd_show_names),
            ("pp diamond", "Diamond Players", lambda: self.execute_command("pp diamond")),
            ("pp master", "Master Players", lambda: self.execute_command("pp master"))
        ]
        
        for i, (cmd, text, func) in enumerate(quick_commands):
            btn = ttk.Button(button_frame, text=f"{text}", command=func, style='Custom.TButton')
            btn.grid(row=i//3, column=i%3, padx=5, pady=2, sticky='ew')
        
        # Command input with autocomplete
        input_frame = tk.Frame(command_frame, bg='#313244', relief=tk.RAISED, bd=2)
        input_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Label(input_frame, text="Command Input (with autocomplete):", bg='#313244', fg='#cdd6f4', 
                font=('Arial', 12, 'bold')).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        self.command_entry = tk.Entry(input_frame, font=('Consolas', 11), bg='#45475a', fg='#cdd6f4',
                                     insertbackground='#cdd6f4', relief=tk.FLAT, bd=5)
        self.command_entry.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Suggestions listbox
        self.suggestions_frame = tk.Frame(input_frame, bg='#313244')
        self.suggestions_listbox = tk.Listbox(self.suggestions_frame, height=4, bg='#45475a', fg='#cdd6f4',
                                             font=('Consolas', 9), selectbackground='#89b4fa')
        self.suggestions_listbox.pack(fill=tk.X, padx=10)
        
        # Execute button
        execute_btn = ttk.Button
