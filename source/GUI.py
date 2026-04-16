"""
GUI.py — Futoshiki Puzzle Solver
Layout:  Header | [Sidebar | Board | Stats Panel] | Status Bar
Modes:   Play (human input) | Algorithm
"""
import copy, os, platform, random, threading, time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from input_output.parse_input import parse_input
from GUI_search.astar import solve_astar
from GUI_search.back_tracking import solve_backtracking
from GUI_search.backward_chaining_solve import backward_chaining_solve
from GUI_search.brute_force import brute_force
from GUI_search.forward_chaining_solve import forward_chaining_solve
from GUI_search.hybrid_backtracking_with_fc import solve_hybrid_backtracking_with_fc
from FOL.kb import KnowledgeBase

# CHERRY BLOSSOM PINK PALETTE
# Brand
C_CHERRY      = "#F2AEBC"   # Primary cherry blossom pink
C_PETAL_L     = "#FDE8EE"   # Light petal — sidebar
C_PETAL_LL    = "#FEF4F7"   # Near-white petal — board area
C_PETAL_D     = "#E8A0B2"   # Darker petal — hover
C_ROSE        = "#C4436B"   # Deep rose — accents, primary CTA
C_ROSE_H      = "#A8335A"   # Rose hover
C_ROSE_DEEP   = "#7A1A35"   # Very dark rose

# Layout
C_APP_BG      = "#FDF5F7"
C_HEADER_BG   = "#F2AEBC"
C_SIDEBAR_BG  = "#FDE8EE"
C_PANEL_BG    = "#FEF0F3"
C_CARD_BG     = "#FFFFFF"
C_BORDER      = "#EAC4CE"
C_SEP         = "#E8BECA"

# Board
C_BOARD_BG    = "#F8EAF0"
C_CELL_BG     = "#FFF9FC"
C_CELL_FG     = "#2C1219"
C_CELL_BORDER = "#D8A9B7"
C_GIVEN_BG    = "#F2AEBC"
C_GIVEN_FG    = "#5C1428"
C_SOLVED_BG   = "#E8F5EC"
C_SOLVED_FG   = "#1A5C35"
C_STEP_BG     = "#FFF3E0"
C_STEP_FG     = "#7A4000"
C_SELECT_BG   = "#F7C9D9"
C_RELATED_BG  = "#FCE7EF"
C_INVALID_BG  = "#FFEAEA"
C_INVALID_FG  = "#B52B2B"
C_CON_FG      = "#C4436B"

# Text
C_TXT_DARK    = "#2C1219"
C_TXT_MID     = "#5C2D3D"
C_TXT_MUTED   = "#9B7080"
C_TXT_LIGHT   = "#C0A0A8"

# Semantic
C_OK          = "#2E7D52"
C_ERR         = "#C0392B"
C_WARN        = "#D67000"

# Buttons
C_PRI         = "#C4436B";  C_PRI_H  = "#A8335A";  C_PRI_F  = "#FFFFFF"
C_SEC         = "#F2AEBC";  C_SEC_H  = "#E8A0B2";  C_SEC_F  = "#5C1428"
C_GHO         = "#FDE8EE";  C_GHO_H  = "#F5C0CE";  C_GHO_F  = "#5C2D3D"
C_DNG         = "#C0392B";  C_DNG_H  = "#A93226";  C_DNG_F  = "#FFFFFF"
C_SUC         = "#2E7D52";  C_SUC_H  = "#236040";  C_SUC_F  = "#FFFFFF"
C_DIS         = "#DCC4CA";  C_DIS_F  = "#B09098"

# Stats / History
C_STAT_BG     = "#FEF0F3"
C_STAT_LBL    = "#9B7080"
C_STAT_VAL    = "#2C1219"
C_HIST_BG     = "#FDF5F7"
C_HIST_BORDER = "#EAC4CE"

# FONTS
_SYS  = platform.system()
_SANS = "SF Pro Text"  if _SYS == "Darwin"  else "Segoe UI"  if _SYS == "Windows" else "Noto Sans"
_MONO = "SF Mono"      if _SYS == "Darwin"  else "Consolas"  if _SYS == "Windows" else "Noto Mono"

F_TITLE    = (_MONO, 22, "bold")
F_SUB      = (_SANS,  9, "italic")
F_CELL     = (_MONO, 17, "bold")
F_CON      = (_MONO, 11, "bold")
F_UI       = (_SANS,  9)
F_UI_B     = (_SANS,  9, "bold")
F_SM       = (_SANS,  8)
F_SM_B     = (_SANS,  8, "bold")
F_SEC_HDR  = (_SANS,  8, "bold")
F_STAT_L   = (_SANS,  8)
F_STAT_V   = (_MONO,  9, "bold")
F_STATUS   = (_SANS,  9)
F_HIST     = (_MONO,  8)

# CONSTANTS
ALGORITHMS = [
    ("A*",                "A*"),
    ("Forward Chaining",  "Forward Chaining"),
    ("Backward Chaining", "Backward Chaining"),
    ("Backtracking",      "Backtracking"),
    ("Brute Force",       "Brute Force"),
    ("Hybrid BT+FC",      "Hybrid"),
]
SIZES        = ["4x4", "5x5", "6x6", "7x7", "8x8", "9x9"]
DIFFICULTIES = ["easy", "medium", "hard"]
HEURISTICS   = ["combined", "remaining_cells", "inequality_chains"]
PRUNINGS     = ["fc", "ac3"]
SPEEDS       = ["0.25x", "0.5x", "1x", "2x", "4x", "8x"]


# WIDGET HELPERS
def _sep(parent, orient="h", color=C_SEP, **kw):
    if orient == "h":
        return tk.Frame(parent, bg=color, height=1, **kw)
    return tk.Frame(parent, bg=color, width=1, **kw)


def _section_hdr(parent, text, bg=C_SIDEBAR_BG):
    return tk.Label(parent, text=text, font=F_SEC_HDR,
                    bg=bg, fg=C_TXT_MUTED, anchor="w")


def _btn(parent, text, command, style="secondary", enabled=True, width=None, **kw):
    """Styled, hover-aware button. style: primary|secondary|ghost|danger|success"""
    _styles = {
        "primary":   (C_PRI,  C_PRI_H,  C_PRI_F),
        "secondary": (C_SEC,  C_SEC_H,  C_SEC_F),
        "ghost":     (C_GHO,  C_GHO_H,  C_GHO_F),
        "danger":    (C_DNG,  C_DNG_H,  C_DNG_F),
        "success":   (C_SUC,  C_SUC_H,  C_SUC_F),
    }
    bg0, _, fg = _styles.get(style, _styles["secondary"])
    # Keep a single tone for each button style (no darker hover variant).
    hov = bg0
    state = "normal" if enabled else "disabled"
    if not enabled:
        bg0 = C_DIS; fg = C_DIS_F; hov = C_DIS
    kw2 = {}
    if width is not None:
        kw2["width"] = width
    b = tk.Button(parent, text=text, command=command,
                  bg=bg0, fg=fg,
                  activebackground=hov, activeforeground=fg,
                  font=F_UI, relief="flat", bd=0,
                  padx=10, pady=5,
                  cursor="hand2" if enabled else "arrow",
                  state=state, **kw2, **kw)
    if enabled:
        b.bind("<Enter>", lambda _, b=b, h=hov: b.config(bg=h))
        b.bind("<Leave>", lambda _, b=b, bg=bg0: b.config(bg=bg))
    return b


def _dropdown(parent, variable, values, width=12):
    """Styled menubutton dropdown."""
    mb = tk.Menubutton(parent, textvariable=variable,
                       bg=C_CARD_BG, fg=C_TXT_DARK,
                       activebackground=C_PETAL_L,
                       activeforeground=C_ROSE,
                       font=F_UI, relief="flat", bd=0,
                       padx=8, pady=4, cursor="hand2", width=width,
                       highlightthickness=1,
                       highlightbackground=C_BORDER)
    menu = tk.Menu(mb, tearoff=0, bg=C_CARD_BG, fg=C_TXT_DARK,
                   activebackground=C_PETAL_L,
                   activeforeground=C_ROSE, font=F_UI)
    for v in values:
        menu.add_radiobutton(label=v, variable=variable, value=v)
    mb["menu"] = menu
    mb.bind("<Enter>", lambda _: mb.config(bg=C_PETAL_L))
    mb.bind("<Leave>", lambda _: mb.config(bg=C_CARD_BG))
    return mb


def _card_frame(parent, bg=C_CARD_BG, padx=10, pady=10):
    """White card with rose border and inner padding."""
    outer = tk.Frame(parent, bg=C_BORDER, padx=1, pady=1)
    inner = tk.Frame(outer, bg=bg, padx=padx, pady=pady)
    inner.pack(fill="both", expand=True)
    return outer, inner


# MAIN APPLICATION
class FutoshikiApp(tk.Tk):

    # ─── Init ────────────────────────────────────────────────────────

    def __init__(self):
        super().__init__()
        self.title("Futoshiki")
        self.configure(bg=C_APP_BG)
        self.resizable(True, True)
        self.minsize(1050, 680)

        # ── Puzzle state ──────────────────────────────────────────────
        self.puzzle        = None
        self.initial_grid  = None
        self.cell_vars     = []   # StringVar[i][j]
        self.cell_wdgs     = []   # Label widget[i][j]
        self.cell_state    = []   # str[i][j]: given|empty|user|user_invalid|solved|step
        self.given_mask    = []   # bool[i][j]

        # ── Play mode state ───────────────────────────────────────────
        self.selected_cell = None     # (r, c) or None
        self.related_cells = set()    # set of (r, c)
        self.undo_stack    = []       # [(r, c, old_val, new_val)]
        self.redo_stack    = []       # [(r, c, old_val, new_val)]

        # ── Solver state ──────────────────────────────────────────────
        self.solving        = False
        self.stop_flag      = False
        self.history        = []
        self.replay_running = False
        self.replay_paused  = False
        self.replay_index   = 0
        self._last_solution = None   # kept for Skip-to-End and replay finish

        # ── Tk variables ──────────────────────────────────────────────
        self.mode_var      = tk.StringVar(value="play")
        self.algo_var      = tk.StringVar(value="A*")
        self.size_var      = tk.StringVar(value="4x4")
        self.diff_var      = tk.StringVar(value="easy")
        self.heuristic_var = tk.StringVar(value="combined")
        self.pruning_var   = tk.StringVar(value="fc")
        self.speed_var     = tk.StringVar(value="1x")
        self.status_var    = tk.StringVar(value="Load a puzzle to begin")
        self.time_var      = tk.StringVar(value="")
        self.file_var      = tk.StringVar(value="No puzzle loaded")

        self.algo_var.trace_add("write", lambda *_: self._on_algo_changed())
        self.mode_var.trace_add("write", lambda *_: self._on_mode_changed())

        self._build_ui()
        self.bind("<Key>", self._on_key)

    # UI CONSTRUCTION
    def _build_ui(self):
        self._build_header()
        _sep(self).pack(fill="x")
        self._build_body()
        _sep(self).pack(fill="x", side="bottom")
        self._build_status_bar()

    # ── Header ───────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self, bg=C_HEADER_BG)
        hdr.pack(fill="x")

        # Left: title block
        left = tk.Frame(hdr, bg=C_HEADER_BG, padx=20, pady=10)
        left.pack(side="left")

        tk.Label(left, text="FUTOSHIKI", font=F_TITLE,
                 bg=C_HEADER_BG, fg=C_ROSE_DEEP).pack(side="left")

        # Right: puzzle selector controls
        right = tk.Frame(hdr, bg=C_HEADER_BG, padx=20, pady=10)
        right.pack(side="right")

        tk.Label(right, text="SIZE", font=F_SM_B,
                 bg=C_HEADER_BG, fg=C_ROSE_DEEP).grid(row=0, column=0, padx=(0, 4))
        _dropdown(right, self.size_var, SIZES, width=4).grid(row=0, column=1, padx=(0, 12))

        tk.Label(right, text="DIFFICULTY", font=F_SM_B,
                 bg=C_HEADER_BG, fg=C_ROSE_DEEP).grid(row=0, column=2, padx=(0, 4))
        _dropdown(right, self.diff_var, DIFFICULTIES, width=7).grid(row=0, column=3, padx=(0, 14))

        self.new_btn  = _btn(right, "New Puzzle", self._load_random, style="secondary")
        self.new_btn.grid(row=0, column=4, padx=3)
        self.load_btn = _btn(right, "Load File", self._load_file, style="secondary")
        self.load_btn.grid(row=0, column=5, padx=3)

    # ── Body: three-column layout ────────────────────────────────────

    def _build_body(self):
        body = tk.Frame(self, bg=C_APP_BG)
        body.pack(fill="both", expand=True)

        self._build_sidebar(body)
        self._build_right_panel(body)   # build right before center so packing order works
        self._build_board_area(body)

        # Initialize conditional visibility *after* all widgets exist
        self._on_mode_changed()
        self._on_algo_changed()

    # ── Left Sidebar ─────────────────────────────────────────────────

    def _build_sidebar(self, parent):
        # Scrollable container
        container = tk.Frame(parent, bg=C_SIDEBAR_BG, width=248)
        container.pack(side="left", fill="y")
        container.pack_propagate(False)

        self._sb_canvas = tk.Canvas(container, bg=C_SIDEBAR_BG,
                                    highlightthickness=0, width=230)
        sb_scroll = tk.Scrollbar(container, orient="vertical",
                                  command=self._sb_canvas.yview)
        self._sb_canvas.configure(yscrollcommand=sb_scroll.set)

        self._sb_canvas.pack(side="left", fill="both", expand=True)
        sb_scroll.pack(side="right", fill="y")

        self._sb_frame = tk.Frame(self._sb_canvas, bg=C_SIDEBAR_BG,
                                   padx=12, pady=12)
        self._sb_frame.bind("<Configure>", lambda _:
            self._sb_canvas.configure(
                scrollregion=self._sb_canvas.bbox("all")))
        self._sb_canvas.create_window((0, 0), window=self._sb_frame, anchor="nw")

        self._sb_canvas.bind("<MouseWheel>", self._on_sidebar_scroll)
        self._sb_frame.bind("<MouseWheel>", self._on_sidebar_scroll)

        # Separator between sidebar and board
        _sep(parent, orient="v").pack(side="left", fill="y")

        self._build_mode_card(self._sb_frame)
        self._build_play_controls_card(self._sb_frame)
        self._build_algo_controls_card(self._sb_frame)

    def _on_sidebar_scroll(self, event):
        delta = event.delta
        if abs(delta) <= 3:
            self._sb_canvas.yview_scroll(-delta, "units")
        else:
            self._sb_canvas.yview_scroll(-(delta // 120), "units")

    # ── Mode card ────────────────────────────────────────────────────

    def _build_mode_card(self, parent):
        outer, inner = _card_frame(parent, bg=C_CARD_BG, padx=8, pady=8)
        outer.pack(fill="x", pady=(0, 10))

        _section_hdr(inner, "MODE", bg=C_CARD_BG).pack(fill="x", pady=(0, 6))

        toggle = tk.Frame(inner, bg=C_CARD_BG)
        toggle.pack(fill="x")

        for label, value in [("Play", "play"), ("Algorithm", "algorithm")]:
            rb = tk.Radiobutton(
                toggle, text=label, variable=self.mode_var, value=value,
                bg=C_CARD_BG, fg=C_TXT_MID,
                selectcolor=C_ROSE, activebackground=C_CARD_BG,
                activeforeground=C_ROSE, indicatoron=False,
                font=F_UI, relief="flat", bd=0,
                padx=10, pady=5, cursor="hand2",
                highlightthickness=1, highlightbackground=C_BORDER)
            rb.pack(side="left", fill="x", expand=True, padx=2)
            rb.bind("<Enter>", lambda _, r=rb: r.config(bg=C_PETAL_L))
            rb.bind("<Leave>", lambda _, r=rb: r.config(bg=C_CARD_BG))

        tk.Label(inner, text="Play: click cells and type values\nAlgorithm: auto-solve with AI",
                 font=F_SM, bg=C_CARD_BG, fg=C_TXT_LIGHT,
                 justify="left", anchor="w").pack(fill="x", pady=(6, 0))

    # ── Play controls card ────────────────────────────────────────────

    def _build_play_controls_card(self, parent):
        self._play_card_outer, inner = _card_frame(parent, bg=C_CARD_BG, padx=10, pady=10)

        _section_hdr(inner, "PLAY CONTROLS", bg=C_CARD_BG).pack(fill="x", pady=(0, 8))

        # Undo / Redo row
        ur = tk.Frame(inner, bg=C_CARD_BG)
        ur.pack(fill="x", pady=(0, 4))
        self._undo_btn = _btn(ur, "↩ Undo", self._undo, style="secondary", width=7)
        self._undo_btn.pack(side="left", padx=(0, 3))
        self._redo_btn = _btn(ur, "↪ Redo", self._redo, style="secondary", width=7)
        self._redo_btn.pack(side="left")

        _btn(inner, "Clear Cell", self._clear_selected,
             style="secondary").pack(fill="x", pady=2)

        _sep(inner, color=C_BORDER).pack(fill="x", pady=6)

        _btn(inner, "Validate Board", self._validate_board,
             style="secondary").pack(fill="x", pady=2)
        _btn(inner, "Hint", self._hint,
             style="secondary").pack(fill="x", pady=2)

        _sep(inner, color=C_BORDER).pack(fill="x", pady=6)

        _btn(inner, "Reset Board", self._reset,
             style="secondary").pack(fill="x", pady=2)

    # ── Algorithm controls card ────────────────────────────────────────
    def _build_algo_controls_card(self, parent):
        self._algo_card_outer, inner = _card_frame(parent, bg=C_CARD_BG, padx=14, pady=10)

        _section_hdr(inner, "ALGORITHM", bg=C_CARD_BG).pack(fill="x", pady=(0, 6))

        # Algorithm radio buttons
        self.algo_buttons = []
        for label, value in ALGORITHMS:
            rb = tk.Radiobutton(
                inner, text=label, variable=self.algo_var, value=value,
                bg=C_CARD_BG, fg=C_TXT_MID,
                selectcolor=C_ROSE, activebackground=C_CARD_BG,
                activeforeground=C_ROSE, indicatoron=True,
                font=F_UI, bd=0, padx=2, pady=2, cursor="hand2")
            rb.pack(anchor="w")
            self.algo_buttons.append(rb)

        # A* options
        self._astar_opts = tk.Frame(inner, bg=C_CARD_BG)
        _sep(self._astar_opts, color=C_BORDER).pack(fill="x", pady=4)
        _section_hdr(self._astar_opts, "A* OPTIONS", bg=C_CARD_BG).pack(fill="x", pady=(0, 4))

        row1 = tk.Frame(self._astar_opts, bg=C_CARD_BG)
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Heuristic", font=F_SM_B,
                 bg=C_CARD_BG, fg=C_TXT_MUTED, width=9, anchor="w").pack(side="left")
        self._heuristic_dd = _dropdown(row1, self.heuristic_var, HEURISTICS, width=14)
        self._heuristic_dd.pack(side="left")

        row2 = tk.Frame(self._astar_opts, bg=C_CARD_BG)
        row2.pack(fill="x", pady=2)
        tk.Label(row2, text="Pruning", font=F_SM_B,
                 bg=C_CARD_BG, fg=C_TXT_MUTED, width=9, anchor="w").pack(side="left")
        self._pruning_dd = _dropdown(row2, self.pruning_var, PRUNINGS, width=6)
        self._pruning_dd.pack(side="left")
        self._astar_opts.pack(fill="x", after=self.algo_buttons[-1])
        _sep(inner, color=C_BORDER).pack(fill="x", pady=8)

        # Speed
        speed_row = tk.Frame(inner, bg=C_CARD_BG)
        speed_row.pack(fill="x", pady=(0, 6))
        tk.Label(speed_row, text="Replay Speed", font=F_SM_B,
                 bg=C_CARD_BG, fg=C_TXT_MUTED).pack(side="left")
        _dropdown(speed_row, self.speed_var, SPEEDS, width=5).pack(side="right")

        # Action buttons
        self._solve_btn = _btn(inner, "Solve", self._solve, style="secondary")
        self._solve_btn.pack(fill="x", pady=2)

        self._stop_btn = _btn(inner, "Stop", self._stop_solver, style="secondary")
        # (packed on demand)

        _sep(inner, color=C_BORDER).pack(fill="x", pady=4)

        self._reset_algo_btn = _btn(inner, "Reset", self._reset, style="secondary")
        self._reset_algo_btn.pack(fill="x", pady=2)

        self._replay_btn = _btn(inner, "Replay", self._replay_history, style="secondary")
        self._replay_btn.pack(fill="x", pady=2)
        self._replay_btn.config(state="disabled")

        self._pause_btn  = _btn(inner, "Pause",  self._stop_replay,    style="secondary")
        self._resume_btn = _btn(inner, "Resume", self._resume_replay,  style="secondary")
        self._step_btn   = _btn(inner, "Step",      self._step_once,      style="secondary")
        self._skip_btn   = _btn(inner, "Skip to End", self._skip_to_end,  style="secondary")

    # ── Board area (center) ───────────────────────────────────────────

    def _build_board_area(self, parent):
        area = tk.Frame(parent, bg=C_BOARD_BG)
        area.pack(side="left", fill="both", expand=True)

        # Info bar above the board
        info_bar = tk.Frame(area, bg=C_PANEL_BG, pady=4, padx=16)
        info_bar.pack(fill="x")
        _sep(info_bar, color=C_ROSE, orient="v").pack(side="left", fill="y", padx=(0, 8))
        self._file_lbl = tk.Label(info_bar, textvariable=self.file_var,
                                   font=F_SM, bg=C_PANEL_BG, fg=C_TXT_MUTED,
                                   anchor="w")
        self._file_lbl.pack(side="left", fill="x", expand=True)

        self._mode_badge = tk.Label(info_bar, text="PLAY MODE",
                                     font=F_SM_B, bg=C_ROSE, fg="#FFFFFF",
                                     padx=8, pady=2)
        self._mode_badge.pack(side="right", padx=6, pady=2)

        _sep(area, color=C_BORDER).pack(fill="x")

        # Loading indicator
        self._loading_var = tk.StringVar(value="")
        tk.Label(area, textvariable=self._loading_var,
                 bg=C_BOARD_BG, fg=C_WARN, font=(_SANS, 10, "italic")).pack(pady=(4, 0))

        # Centering wrapper for grid
        self._board_wrapper = tk.Frame(area, bg=C_BOARD_BG)
        self._board_wrapper.pack(fill="both", expand=True)

        self._grid_frame = tk.Frame(self._board_wrapper, bg=C_BOARD_BG)

        # Placeholder
        tk.Label(self._grid_frame, text="No puzzle loaded",
                 bg=C_BOARD_BG, fg=C_TXT_LIGHT, font=(_MONO, 14)).pack(pady=80, padx=60)
        self._grid_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Cell info bar below board
        info_bot = tk.Frame(area, bg=C_PANEL_BG, pady=4, padx=16)
        info_bot.pack(fill="x", side="bottom")
        _sep(area, color=C_BORDER).pack(fill="x", side="bottom")
        self._cell_info_var = tk.StringVar(value="")
        tk.Label(info_bot, textvariable=self._cell_info_var,
                 font=F_SM, bg=C_PANEL_BG, fg=C_TXT_MUTED, anchor="w").pack(side="left")
        self._step_var = tk.StringVar(value="")
        tk.Label(info_bot, textvariable=self._step_var,
                 font=F_SM_B, bg=C_PANEL_BG, fg=C_ROSE, anchor="e").pack(side="right")

    # ── Right stats / history panel ──────────────────────────────────

    def _build_right_panel(self, parent):
        _sep(parent, orient="v").pack(side="right", fill="y")

        panel = tk.Frame(parent, bg=C_STAT_BG, width=272)
        panel.pack(side="right", fill="y")
        panel.pack_propagate(False)

        inner = tk.Frame(panel, bg=C_STAT_BG, padx=14, pady=14)
        inner.pack(fill="both", expand=True)

        # ── Statistics ───────────────────────────────────────────
        _section_hdr(inner, "STATISTICS", bg=C_STAT_BG).pack(fill="x", pady=(0, 6))
        _sep(inner, color=C_BORDER).pack(fill="x", pady=(0, 8))

        fields = [
            ("Algorithm",     "algo_disp"),
            ("Puzzle Size",   "size_disp"),
            ("Status",        "status_disp"),
            ("Time (s)",      "time_disp"),
            ("Memory (KB)",   "mem_disp"),
            ("Expansions",    "exp_disp"),
            ("Generated",     "gen_disp"),
            ("Branch Points", "bp_disp"),
            ("BT Fallbacks",  "bt_disp"),
        ]
        self.stat_vars = {}
        for label_text, key in fields:
            row = tk.Frame(inner, bg=C_STAT_BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label_text.upper(), font=F_STAT_L,
                     bg=C_STAT_BG, fg=C_STAT_LBL, anchor="w").pack(fill="x")
            var = tk.StringVar(value="\u2014")
            self.stat_vars[key] = var
            tk.Label(row, textvariable=var, font=F_STAT_V,
                     bg=C_STAT_BG, fg=C_STAT_VAL, anchor="w").pack(fill="x")
            tk.Frame(inner, bg=C_BORDER, height=1).pack(fill="x", pady=(1, 0))

        # ── Derivation History ───────────────────────────────────
        _sep(inner, color=C_BORDER).pack(fill="x", pady=(10, 6))
        _section_hdr(inner, "DERIVATION HISTORY", bg=C_STAT_BG).pack(fill="x", pady=(0, 4))

        self._history_text = scrolledtext.ScrolledText(
            inner, height=12, width=26,
            bg=C_HIST_BG, fg=C_STAT_VAL,
            font=F_HIST, relief="flat", bd=0,
            insertbackground=C_TXT_DARK,
            selectbackground=C_PETAL_D,
            highlightthickness=1, highlightbackground=C_HIST_BORDER)
        self._history_text.pack(fill="both", expand=True)
        self._history_text.config(state="disabled")

        self._history_text.tag_configure("derive",   foreground=C_OK)
        self._history_text.tag_configure("elim",     foreground=C_ERR)
        self._history_text.tag_configure("assign",   foreground=C_WARN)
        self._history_text.tag_configure("clear",    foreground=C_TXT_MUTED)
        self._history_text.tag_configure("rule",     foreground=C_TXT_LIGHT)
        self._history_text.tag_configure("heading",  foreground=C_ROSE)

    # ── Status bar ───────────────────────────────────────────────────

    def _build_status_bar(self):
        bar = tk.Frame(self, bg=C_PANEL_BG, pady=5)
        bar.pack(fill="x", side="bottom")

        _sep(bar, orient="v", color=C_ROSE).pack(side="left", fill="y")

        self._status_lbl = tk.Label(bar, textvariable=self.status_var,
                                     bg=C_PANEL_BG, fg=C_TXT_MUTED,
                                     font=F_STATUS, anchor="w", padx=10)
        self._status_lbl.pack(side="left", fill="x", expand=True)

        tk.Label(bar, textvariable=self.time_var,
                 bg=C_PANEL_BG, fg=C_ROSE, font=(_MONO, 9, "bold"),
                 anchor="e", padx=14).pack(side="right")

    # STATE MANAGEMENT
    def _on_mode_changed(self):
        mode = self.mode_var.get()
        if mode == "play":
            self._play_card_outer.pack(fill="x", pady=(0, 10))
            self._algo_card_outer.pack_forget()
            self._mode_badge.config(text="PLAY MODE", bg=C_ROSE)
        else:
            self._play_card_outer.pack_forget()
            self._algo_card_outer.pack(fill="x", pady=(0, 10))
            self._mode_badge.config(text="ALGORITHM MODE", bg=C_TXT_MID)
        self._deselect_cell()

    def _on_algo_changed(self):
        is_astar = self.algo_var.get() == "A*"
        state = "normal" if is_astar else "disabled"
        self._heuristic_dd.config(state=state)
        self._pruning_dd.config(state=state)

    def _set_status(self, msg, kind="info"):
        colors = {"info": C_TXT_MUTED, "ok": C_OK, "error": C_ERR, "warn": C_WARN}
        self.status_var.set(msg)
        self._status_lbl.config(fg=colors.get(kind, C_TXT_MUTED))

    def _reset_stats(self):
        for var in self.stat_vars.values():
            var.set("\u2014")

    def _update_stats(self, algo, size, status, stats):
        self.stat_vars["algo_disp"].set(algo)
        self.stat_vars["size_disp"].set(size)
        self.stat_vars["status_disp"].set(status)
        if not stats:
            return
        t = stats.get("time_sec")
        self.stat_vars["time_disp"].set(f"{t:.6f}" if t is not None else "\u2014")
        m = stats.get("peak_mem_kb")
        self.stat_vars["mem_disp"].set(f"{m:.1f}" if m is not None else "\u2014")
        e = stats.get("expansions")
        self.stat_vars["exp_disp"].set(str(e) if e is not None else "\u2014")
        g = stats.get("generated")
        self.stat_vars["gen_disp"].set(str(g) if g is not None else "\u2014")
        bp = stats.get("branch_points")
        self.stat_vars["bp_disp"].set(str(bp) if bp is not None else "\u2014")
        bt = stats.get("bt_fallbacks")
        self.stat_vars["bt_disp"].set(str(bt) if bt is not None else "\u2014")

    def _set_buttons_solving(self, solving):
        state = "disabled" if solving else "normal"
        for rb in self.algo_buttons:
            rb.config(state=state)
        self._reset_algo_btn.config(state=state)
        replay_state = "disabled" if (solving or not self.history) else "normal"
        self._replay_btn.config(state=replay_state)

        if solving:
            self._solve_btn.pack_forget()
            self._step_btn.pack_forget()
            self._skip_btn.pack_forget()
            self._stop_btn.pack(fill="x", pady=2, before=self._reset_algo_btn)
            self._loading_var.set("Solving\u2026 please wait")
        else:
            self._stop_btn.pack_forget()
            self._solve_btn.pack(fill="x", pady=2, before=self._reset_algo_btn)
            self._loading_var.set("")

    def _set_buttons_replay(self, state):
        """
        state: 'playing' — auto-stepping in progress
               'paused'  — paused (step-by-step manual mode)
               'idle'    — no replay / replay finished
        """
        self._pause_btn.pack_forget()
        self._resume_btn.pack_forget()
        self._replay_btn.pack_forget()
        self._step_btn.pack_forget()
        self._skip_btn.pack_forget()

        has_history = bool(self.history)

        if state == "playing":
            self._pause_btn.pack(fill="x", pady=2)
            if self._last_solution:
                self._skip_btn.pack(fill="x", pady=2)
        elif state == "paused":
            self._resume_btn.pack(fill="x", pady=2)
            self._step_btn.pack(fill="x", pady=2)
            if self._last_solution:
                self._skip_btn.pack(fill="x", pady=2)
        else:  # idle
            self._replay_btn.pack(fill="x", pady=2)
            self._replay_btn.config(state="normal" if has_history else "disabled")
            if has_history:
                self._step_btn.pack(fill="x", pady=2)
            if self._last_solution:
                self._skip_btn.pack(fill="x", pady=2)

    # GRID RENDERING
    def _render_grid(self):
        for w in self._grid_frame.winfo_children():
            w.destroy()
        self.cell_vars  = []
        self.cell_wdgs  = []
        self.cell_state = []
        self.given_mask = []

        p    = self.puzzle
        N    = p.N
        CELL = max(42, min(62, 500 // N))
        GAP  = 22

        for i in range(N):
            rv, rw, rs, rg = [], [], [], []
            for j in range(N):
                val   = p.grid[i][j]
                given = val != 0

                var = tk.StringVar(value=str(val) if val else "")
                rv.append(var)
                rg.append(given)
                rs.append("given" if given else "empty")

                lbl = tk.Label(
                    self._grid_frame,
                    textvariable=var,
                    width=2, font=F_CELL,
                    bg=C_GIVEN_BG if given else C_CELL_BG,
                    fg=C_GIVEN_FG if given else C_TXT_LIGHT,
                    relief="flat", bd=0,
                    highlightthickness=1,
                    highlightbackground=C_CELL_BORDER)
                lbl.place(x=j*(CELL+GAP), y=i*(CELL+GAP),
                          width=CELL, height=CELL)

                if not given:
                    lbl.bind("<Button-1>", lambda _, r=i, c=j: self._on_cell_click(r, c))

                # Horizontal constraint
                if j < N - 1:
                    c_val = p.h_constraints[i][j]
                    sym = "<" if c_val == 1 else (">" if c_val == -1 else "")
                    tk.Label(
                        self._grid_frame, text=sym, bg=C_BOARD_BG, fg=C_CON_FG,
                        font=F_CON
                    ).place(x=j*(CELL+GAP)+CELL,
                            y=i*(CELL+GAP)+(CELL-18)//2,
                            width=GAP, height=18)

                # Vertical constraint
                if i < N - 1:
                    c_val = p.v_constraints[i][j]
                    sym = "\u2227" if c_val == 1 else ("\u2228" if c_val == -1 else "")
                    tk.Label(
                        self._grid_frame, text=sym, bg=C_BOARD_BG, fg=C_CON_FG,
                        font=F_CON
                    ).place(x=j*(CELL+GAP)+(CELL-18)//2,
                            y=i*(CELL+GAP)+CELL,
                            width=18, height=GAP)

                rw.append(lbl)

            self.cell_vars.append(rv)
            self.cell_wdgs.append(rw)
            self.cell_state.append(rs)
            self.given_mask.append(rg)

        total_w = N * CELL + (N - 1) * GAP
        total_h = N * CELL + (N - 1) * GAP
        self._grid_frame.config(width=total_w, height=total_h)

    # ─── Cell style application ──────────────────────────────────────

    def _refresh_cell_style(self, i, j):
        """Recompute and apply background + border for cell (i,j)."""
        state = self.cell_state[i][j]
        bg_map = {
            "given":        (C_GIVEN_BG,   C_GIVEN_FG),
            "empty":        (C_CELL_BG,    C_TXT_LIGHT),
            "user":         (C_CELL_BG,    C_TXT_DARK),
            "user_invalid": (C_INVALID_BG, C_INVALID_FG),
            "solved":       (C_SOLVED_BG,  C_SOLVED_FG),
            "step":         (C_STEP_BG,    C_STEP_FG),
        }
        base_bg, base_fg = bg_map.get(state, (C_CELL_BG, C_TXT_DARK))

        is_selected = self.selected_cell == (i, j)
        is_related  = (i, j) in self.related_cells

        if is_selected:
            bg = C_SELECT_BG
            border = C_ROSE
            thickness = 2
        elif is_related and state not in ("given", "solved", "step"):
            bg = C_RELATED_BG
            border = C_PETAL_D
            thickness = 1
        else:
            bg = base_bg
            border = C_CELL_BORDER
            thickness = 1

        self.cell_wdgs[i][j].config(
            bg=bg, fg=base_fg,
            highlightbackground=border,
            highlightthickness=thickness)

    def _refresh_all_cells(self):
        if not self.puzzle:
            return
        for i in range(self.puzzle.N):
            for j in range(self.puzzle.N):
                self._refresh_cell_style(i, j)

    def _update_cell(self, i, j, val, mode="solved"):
        """Update cell value and apply the given display mode."""
        if val == 0:
            self.cell_vars[i][j].set("")
            self.cell_state[i][j] = "empty"
        else:
            self.cell_vars[i][j].set(str(val))
            if mode == "step":
                self.cell_state[i][j] = "step"
            else:
                self.cell_state[i][j] = "solved"
        self._refresh_cell_style(i, j)

    def _fill_solution(self, solution):
        N = self.puzzle.N
        for i in range(N):
            for j in range(N):
                if not self.given_mask[i][j]:
                    self._update_cell(i, j, solution.grid[i][j], "solved")
        self.update_idletasks()

    def _restore_initial_grid(self):
        if self.initial_grid:
            self.puzzle.grid = [row[:] for row in self.initial_grid]
        N = self.puzzle.N
        for i in range(N):
            for j in range(N):
                if self.given_mask[i][j]:
                    self.cell_vars[i][j].set(str(self.puzzle.grid[i][j]))
                    self.cell_state[i][j] = "given"
                else:
                    self.cell_vars[i][j].set("")
                    self.cell_state[i][j] = "empty"
        self._deselect_cell()

    # PLAY MODE — Cell Interaction
    def _on_cell_click(self, r, c):
        if self.mode_var.get() != "play":
            return
        if not self.puzzle:
            return
        if self.given_mask[r][c]:
            # Even given cells can be selected for constraint highlighting
            self._select_cell(r, c)
            return
        self._select_cell(r, c)
        self._cell_info_var.set(f"Selected: row {r+1}, col {c+1}")

    def _select_cell(self, r, c):
        prev = self.selected_cell
        prev_related = set(self.related_cells)

        self.selected_cell = (r, c)
        self.related_cells = self._get_related_cells(r, c)

        # Refresh previously selected and related cells first
        if prev:
            self._refresh_cell_style(prev[0], prev[1])
        for (pi, pj) in prev_related:
            self._refresh_cell_style(pi, pj)

        # Refresh new selection and related
        self._refresh_cell_style(r, c)
        for (ri, rj) in self.related_cells:
            self._refresh_cell_style(ri, rj)

        self._cell_info_var.set(f"Selected: row {r+1}, col {c+1}")

    def _deselect_cell(self):
        if not self.selected_cell:
            return
        old = self.selected_cell
        old_related = set(self.related_cells)
        self.selected_cell = None
        self.related_cells = set()
        if old and self.puzzle:
            self._refresh_cell_style(old[0], old[1])
            for (ri, rj) in old_related:
                if self.puzzle and ri < self.puzzle.N and rj < self.puzzle.N:
                    self._refresh_cell_style(ri, rj)
        self._cell_info_var.set("")

    def _get_related_cells(self, r, c):
        """Return cells in same row + column + constrained neighbors."""
        if not self.puzzle:
            return set()
        N = self.puzzle.N
        related = set()
        for j in range(N):
            if j != c:
                related.add((r, j))
        for i in range(N):
            if i != r:
                related.add((i, c))
        # Constraint neighbors
        if c < N - 1 and self.puzzle.h_constraints[r][c] != 0:
            related.add((r, c + 1))
        if c > 0 and self.puzzle.h_constraints[r][c - 1] != 0:
            related.add((r, c - 1))
        if r < N - 1 and self.puzzle.v_constraints[r][c] != 0:
            related.add((r + 1, c))
        if r > 0 and self.puzzle.v_constraints[r - 1][c] != 0:
            related.add((r - 1, c))
        return related

    def _on_key(self, event):
        if self.mode_var.get() != "play":
            return
        if not self.selected_cell:
            return
        r, c = self.selected_cell
        if self.given_mask[r][c]:
            return

        key = event.keysym
        if key in ("Delete", "BackSpace"):
            self._play_set_cell(r, c, 0)
            return

        # Arrow key navigation
        N = self.puzzle.N
        nr, nc = r, c
        if key == "Up"    and r > 0:   nr = r - 1
        elif key == "Down"  and r < N-1: nr = r + 1
        elif key == "Left"  and c > 0:   nc = c - 1
        elif key == "Right" and c < N-1: nc = c + 1

        if (nr, nc) != (r, c):
            self._select_cell(nr, nc)
            return

        # Digit input
        if key.isdigit():
            val = int(key)
            if 1 <= val <= self.puzzle.N:
                self._play_set_cell(r, c, val)

    def _play_set_cell(self, r, c, val):
        """Set cell value in play mode, with undo support and validation."""
        if not self.puzzle or self.given_mask[r][c]:
            return
        old_val = self.puzzle.grid[r][c]
        if old_val == val:
            return

        # Record undo
        self.undo_stack.append((r, c, old_val, val))
        self.redo_stack.clear()

        # Apply value
        self.puzzle.grid[r][c] = val

        if val == 0:
            self.cell_vars[r][c].set("")
            self.cell_state[r][c] = "empty"
        else:
            self.cell_vars[r][c].set(str(val))
            # Check validity immediately
            self.puzzle.grid[r][c] = 0  # temp unset to check
            valid = self.puzzle.is_valid_assignment(r, c, val)
            self.puzzle.grid[r][c] = val  # restore
            self.cell_state[r][c] = "user" if valid else "user_invalid"

        self._refresh_cell_style(r, c)

        # Re-validate previously invalid cells (a change might fix them)
        self._recheck_invalid_cells()

        if self.puzzle.is_filled():
            self._check_solved()

    def _recheck_invalid_cells(self):
        """Re-evaluate any user_invalid cells after a board change."""
        if not self.puzzle:
            return
        N = self.puzzle.N
        for i in range(N):
            for j in range(N):
                if self.cell_state[i][j] == "user_invalid":
                    val = self.puzzle.grid[i][j]
                    self.puzzle.grid[i][j] = 0
                    valid = self.puzzle.is_valid_assignment(i, j, val)
                    self.puzzle.grid[i][j] = val
                    if valid:
                        self.cell_state[i][j] = "user"
                        self._refresh_cell_style(i, j)

    def _undo(self):
        if not self.undo_stack:
            self._set_status("Nothing to undo", "warn")
            return
        r, c, old_val, new_val = self.undo_stack.pop()
        self.redo_stack.append((r, c, old_val, new_val))

        self.puzzle.grid[r][c] = old_val
        if old_val == 0:
            self.cell_vars[r][c].set("")
            self.cell_state[r][c] = "empty"
        else:
            self.cell_vars[r][c].set(str(old_val))
            self.puzzle.grid[r][c] = 0
            valid = self.puzzle.is_valid_assignment(r, c, old_val)
            self.puzzle.grid[r][c] = old_val
            self.cell_state[r][c] = "user" if valid else "user_invalid"
        self._refresh_cell_style(r, c)
        self._recheck_invalid_cells()
        self._set_status(f"Undone — cell ({r+1},{c+1})", "info")

    def _redo(self):
        if not self.redo_stack:
            self._set_status("Nothing to redo", "warn")
            return
        r, c, old_val, new_val = self.redo_stack.pop()
        self.undo_stack.append((r, c, old_val, new_val))

        self.puzzle.grid[r][c] = new_val
        if new_val == 0:
            self.cell_vars[r][c].set("")
            self.cell_state[r][c] = "empty"
        else:
            self.cell_vars[r][c].set(str(new_val))
            self.puzzle.grid[r][c] = 0
            valid = self.puzzle.is_valid_assignment(r, c, new_val)
            self.puzzle.grid[r][c] = new_val
            self.cell_state[r][c] = "user" if valid else "user_invalid"
        self._refresh_cell_style(r, c)
        self._recheck_invalid_cells()
        self._set_status(f"Redone — cell ({r+1},{c+1})", "info")

    def _clear_selected(self):
        if not self.selected_cell:
            self._set_status("No cell selected — click a cell first", "warn")
            return
        r, c = self.selected_cell
        if self.given_mask[r][c]:
            self._set_status("Given cells cannot be edited", "warn")
            return
        self._play_set_cell(r, c, 0)
        self._set_status(f"Cleared cell ({r+1},{c+1})", "info")

    def _validate_board(self):
        if not self.puzzle:
            self._set_status("No puzzle loaded", "warn")
            return
        N = self.puzzle.N
        invalid = []
        for i in range(N):
            for j in range(N):
                if self.cell_state[i][j] in ("user", "user_invalid"):
                    val = self.puzzle.grid[i][j]
                    if val == 0:
                        continue
                    self.puzzle.grid[i][j] = 0
                    ok = self.puzzle.is_valid_assignment(i, j, val)
                    self.puzzle.grid[i][j] = val
                    if ok:
                        self.cell_state[i][j] = "user"
                    else:
                        self.cell_state[i][j] = "user_invalid"
                        invalid.append((i, j))
                    self._refresh_cell_style(i, j)

        if invalid:
            self._set_status(f"{len(invalid)} invalid cell(s) — check highlighted cells", "error")
        elif self.puzzle.is_filled():
            self._check_solved()
        else:
            self._set_status("Board is valid so far — keep going!", "ok")

    def _hint(self):
        if not self.puzzle:
            self._set_status("No puzzle loaded", "warn")
            return
        if self.mode_var.get() != "play":
            self._set_status("Hints are available in Play mode only", "warn")
            return

        try:
            p_copy = self.puzzle.copy()
            kb = KnowledgeBase(p_copy)
            _, sol, _, _, _ = forward_chaining_solve(p_copy, kb)

            if sol:
                N = self.puzzle.N
                for i in range(N):
                    for j in range(N):
                        if (self.cell_state[i][j] == "empty" and
                                sol.grid[i][j] != 0):
                            # Scroll to and select this cell
                            self._select_cell(i, j)
                            self._cell_info_var.set(
                                f"Hint: row {i+1}, col {j+1} \u2192 {sol.grid[i][j]}")
                            self._set_status(
                                f"Hint: cell ({i+1},{j+1}) can be determined to be {sol.grid[i][j]}",
                                "info")
                            return
            self._set_status("No simple hint available — try a different strategy", "warn")
        except Exception as ex:
            self._set_status(f"Hint unavailable: {ex}", "warn")

    def _check_solved(self):
        """Check if the current board is fully and correctly solved."""
        if not self.puzzle or not self.puzzle.is_filled():
            return
        N = self.puzzle.N
        for i in range(N):
            for j in range(N):
                if self.cell_state[i][j] in ("user", "user_invalid"):
                    val = self.puzzle.grid[i][j]
                    self.puzzle.grid[i][j] = 0
                    ok = self.puzzle.is_valid_assignment(i, j, val)
                    self.puzzle.grid[i][j] = val
                    if not ok:
                        self._set_status("Puzzle filled but has errors — use Validate to find them", "error")
                        return
        self._set_status("Puzzle solved correctly! Well done!", "ok")
        self._show_success_dialog()

    # LOAD / RESET
    def _load_puzzle(self, path):
        self.puzzle       = parse_input(path)
        self.initial_grid = [row[:] for row in self.puzzle.grid]
        self.history        = []
        self.replay_index   = 0
        self.replay_running = False
        self.replay_paused  = False
        self._last_solution = None
        self.undo_stack     = []
        self.redo_stack     = []

        self._render_grid()
        self._reset_stats()
        self._set_buttons_replay("idle")
        self.stat_vars["size_disp"].set(f"{self.puzzle.N}\u00d7{self.puzzle.N}")
        self.stat_vars["status_disp"].set("Ready")
        self.time_var.set("")
        self._clear_history_display()
        self._deselect_cell()
        self._step_var.set("")

        fname = os.path.basename(path)
        self.file_var.set(
            f"{self.diff_var.get()} / {self.size_var.get()} / {fname}")

    def _load_random(self):
        diff = self.diff_var.get()
        size = self.size_var.get()
        base = os.path.dirname(os.path.abspath(__file__))
        folder = os.path.join(base, "Inputs", diff, size)

        if not os.path.exists(folder):
            messagebox.showerror("Folder Not Found",
                                 f"No puzzles found for {diff}/{size}.\n{folder}")
            return
        files = [f for f in os.listdir(folder) if f.endswith(".txt")]
        if not files:
            messagebox.showerror("No Puzzles", "No .txt puzzle files in that folder.")
            return

        path = os.path.join(folder, random.choice(files))
        try:
            self._load_puzzle(path)
            self._set_status(f"Loaded {diff}/{size} puzzle — ready!", "info")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load puzzle:\n{e}")

    def _load_file(self):
        base = os.path.dirname(os.path.abspath(__file__))
        path = filedialog.askopenfilename(
            title="Select Futoshiki puzzle file",
            initialdir=os.path.join(base, "Inputs"),
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            self._load_puzzle(path)
            self._set_status(
                f"Loaded: {os.path.basename(path)}  \u2014  "
                f"{self.puzzle.N}\u00d7{self.puzzle.N}", "info")
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not read file:\n{e}")

    def _reset(self):
        if not self.puzzle:
            return
        self.replay_running = False
        self.replay_paused  = False
        self._restore_initial_grid()
        self.history        = []
        self.replay_index   = 0
        self._last_solution = None
        self.undo_stack     = []
        self.redo_stack     = []
        self._set_buttons_replay("idle")
        self._reset_stats()
        self.stat_vars["size_disp"].set(f"{self.puzzle.N}\u00d7{self.puzzle.N}")
        self.stat_vars["status_disp"].set("Ready")
        self._set_status("Board reset", "info")
        self.time_var.set("")
        self._step_var.set("")
        self._clear_history_display()

    def _clear_history_display(self):
        ht = self._history_text
        ht.config(state="normal")
        ht.delete("1.0", tk.END)
        ht.insert(tk.END, "No history yet\n", "rule")
        ht.config(state="disabled")

    # SOLVE
    def _solve(self):
        if not self.puzzle:
            messagebox.showwarning("No Puzzle", "Please load a puzzle first.")
            return
        if self.solving:
            return

        self._reset()
        self.solving   = True
        self.stop_flag = False
        self._set_status("Solving\u2026", "info")
        self.stat_vars["status_disp"].set("Solving\u2026")
        self._set_buttons_solving(True)
        self.update_idletasks()

        if self.initial_grid:
            self.puzzle.grid = [row[:] for row in self.initial_grid]
        puzzle_copy = copy.deepcopy(self.puzzle)
        algo = self.algo_var.get()

        threading.Thread(target=self._run_solver,
                         args=(algo, puzzle_copy), daemon=True).start()

    def _stop_solver(self):
        if not self.solving:
            return
        self.stop_flag = True
        self.solving   = False
        self._set_status("Stopped by user", "warn")
        self.stat_vars["status_disp"].set("Stopped")
        self._set_buttons_solving(False)

    def _run_solver(self, algo, p):
        kb = KnowledgeBase(p)
        t0 = time.time()
        solution, stats, history = None, {}, []

        try:
            if algo == "A*":
                solution, stats, history = solve_astar(
                    p, kb,
                    heuristic=self.heuristic_var.get(),
                    pruning=self.pruning_var.get())
            elif algo == "Backtracking":
                solution, stats, history = solve_backtracking(p)
            elif algo == "Brute Force":
                solution, stats, history = brute_force(p)
            elif algo == "Backward Chaining":
                solution, stats, history = backward_chaining_solve(p, kb)
            elif algo == "Forward Chaining":
                is_complete, solution, domains, stats, history = \
                    forward_chaining_solve(p, kb)
                elapsed = time.time() - t0
                if solution is None:
                    self.after(0, self._show_fc_result,
                               "contradiction", None, elapsed, algo, stats, history)
                elif not is_complete:
                    self.after(0, self._show_fc_result,
                               "partial", solution, elapsed, algo, stats, history)
                else:
                    self.after(0, self._show_result,
                               solution, elapsed, algo, stats, history)
                self.solving = False
                self.after(0, self._set_buttons_solving, False)
                return
            elif algo == "Hybrid":
                solution, stats, history = solve_hybrid_backtracking_with_fc(p, kb)

        except Exception as e:
            if not self.stop_flag:
                self.after(0, self._set_status, f"Error: {e}", "error")
                self.after(0, self.stat_vars["status_disp"].set, "Error")
            self.solving = False
            self.after(0, self._set_buttons_solving, False)
            return

        if self.stop_flag:
            self.solving = False
            return

        elapsed = time.time() - t0
        if isinstance(stats, dict) and "time_sec" not in stats:
            stats["time_sec"] = elapsed

        self.solving = False
        self.after(0, self._show_result, solution, elapsed, algo, stats, history)
        self.after(0, self._set_buttons_solving, False)

    # RESULTS
    def _show_result(self, solution, elapsed, algo, stats, history=None):
        size_str = f"{self.puzzle.N}\u00d7{self.puzzle.N}" if self.puzzle else "\u2014"
        if solution is None:
            self._set_status("No solution found", "error")
            self._update_stats(algo, size_str, "No Solution", stats)
            messagebox.showinfo("No Solution", "This puzzle could not be solved.")
            self.time_var.set("")
            return

        self._last_solution = solution
        self.time_var.set(f"{elapsed:.4f}s")
        self._update_stats(algo, size_str, "Solved", stats)

        self.history = history or []
        self.replay_index = 0
        self._update_history_text(self.history)

        if self.history:
            # Auto-play step-by-step animation
            self._set_status(f"Solved with {algo} \u2014 animating steps\u2026", "ok")
            self._replay_history()
        else:
            # No history recorded by this algorithm — show solution directly
            self._fill_solution(solution)
            self._set_status(f"Solved with {algo}", "ok")
            self._set_buttons_replay("idle")

    def _show_fc_result(self, case, solution, elapsed, algo, stats, history):
        size_str = f"{self.puzzle.N}\u00d7{self.puzzle.N}" if self.puzzle else "\u2014"
        if case == "contradiction":
            self._set_status("Contradiction detected \u2014 no solution exists", "error")
            self._update_stats(algo, size_str, "Contradiction", stats)
            messagebox.showinfo("Contradiction",
                                "Forward Chaining found a contradiction.\n"
                                "This puzzle has no valid solution.")
            self.time_var.set("")
            self.history = history or []
            self.replay_index = 0
            self._update_history_text(self.history)
            self._set_buttons_replay("idle")
            return

        # partial case: animate what FC did manage to propagate
        self.puzzle = solution
        self.initial_grid = [row[:] for row in solution.grid]
        self._last_solution = solution
        self._update_stats(algo, size_str, "Partial", stats)
        self.time_var.set(f"{elapsed:.4f}s")
        messagebox.showinfo("Partial Solution",
                            "Forward Chaining propagated constraints\n"
                            "but could not resolve every cell.\n\n"
                            "Watch the steps, then try Backtracking\n"
                            "or Hybrid BT+FC to finish solving.")

        self.history = history or []
        self.replay_index = 0
        self._update_history_text(self.history)

        if self.history:
            self._set_status(
                "Partial result \u2014 FC did not fully solve \u2014 animating steps\u2026",
                "warn")
            self._replay_history()
        else:
            self._fill_solution(solution)
            self._set_status(
                "Partial solution \u2014 FC could not resolve all cells", "warn")
            self._set_buttons_replay("idle")

    def _show_success_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Congratulations!")
        dlg.configure(bg=C_CHERRY)
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text="\U0001f338", font=("", 40),
                 bg=C_CHERRY).pack(pady=(20, 4))
        tk.Label(dlg, text="Puzzle Solved!", font=(_MONO, 18, "bold"),
                 bg=C_CHERRY, fg=C_ROSE_DEEP).pack()
        tk.Label(dlg, text="Congratulations — all constraints satisfied!",
                 font=F_UI, bg=C_CHERRY, fg=C_ROSE_DEEP, pady=6).pack()
        _btn(dlg, "  Close  ", dlg.destroy,
             style="secondary").pack(pady=(8, 20))

    def _update_history_text(self, history):
        ht = self._history_text
        ht.config(state="normal")
        ht.delete("1.0", tk.END)

        if not history:
            ht.insert(tk.END, "No steps recorded\n", "rule")
            ht.config(state="disabled")
            return

        ht.insert(tk.END, f"{len(history)} steps recorded\n", "heading")
        ht.insert(tk.END, "\u2014" * 22 + "\n", "rule")

        for step in history:
            action = step[0]
            r, c, val = step[1], step[2], step[3]
            rule = step[4] if len(step) > 4 else ""
            if action == "derive":
                ht.insert(tk.END, f"+ Val({r},{c}) = {val}\n", "derive")
            elif action == "eliminate":
                ht.insert(tk.END, f"- ({r},{c}) \u2260 {val}", "elim")
                if rule:
                    ht.insert(tk.END, f"  [{rule}]", "rule")
                ht.insert(tk.END, "\n")
            elif action == "assign":
                ht.insert(tk.END, f"= ({r},{c}) \u2190 {val}\n", "assign")
            elif action == "clear":
                ht.insert(tk.END, f"  ({r},{c}) undo {val}\n", "clear")
            else:
                ht.insert(tk.END, f"  {action} ({r},{c}) {val}\n")

        ht.config(state="disabled")
        ht.see(tk.END)

    # REPLAY
    def _replay_history(self):
        """Start (or restart) the animated step-by-step replay."""
        if not self.history or self.replay_running:
            return
        self.replay_running = True
        self.replay_paused  = False
        self._restore_initial_grid()
        self.replay_index = 0
        self._set_buttons_replay("playing")
        self._replay_step()

    def _replay_step(self):
        """Advance one frame of the auto-replay animation."""
        if not self.replay_running:
            return
        total = len(self.history)
        if self.replay_index >= total:
            # Animation finished — normalise colours to "solved"
            self.replay_running = False
            if self._last_solution:
                self._fill_solution(self._last_solution)
            self._set_status("Step-by-step complete", "ok")
            self._set_buttons_replay("idle")
            self._step_var.set("")
            return

        self._apply_step(self.replay_index)
        self.replay_index += 1
        self._step_var.set(f"Step {self.replay_index} / {total}")

        speed = float(self.speed_var.get().replace("x", ""))
        delay = max(10, int(200 / speed))
        self.after(delay, self._replay_step)

    def _apply_step(self, idx):
        """Apply the action at history[idx] to the board display."""
        step = self.history[idx]
        action, r, c, val = step[0], step[1], step[2], step[3]
        if action in ("assign", "derive"):
            self.puzzle.grid[r][c] = val
            self._update_cell(r, c, val, "step")
        elif action == "clear":
            self.puzzle.grid[r][c] = 0
            self._update_cell(r, c, 0)

    def _stop_replay(self):
        """Pause the auto-replay (switches to manual step mode)."""
        if not self.replay_running:
            return
        self.replay_running = False
        self.replay_paused  = True
        total = len(self.history)
        self._step_var.set(f"Step {self.replay_index} / {total} — paused")
        self._set_status("Paused — use \u2192 Step to advance manually", "warn")
        self._set_buttons_replay("paused")

    def _resume_replay(self):
        """Resume auto-replay from where it was paused."""
        if not self.replay_paused:
            return
        self.replay_running = True
        self.replay_paused  = False
        self._set_status("Resuming\u2026", "info")
        self._set_buttons_replay("playing")
        self._replay_step()

    def _step_once(self):
        """Manually advance one step (works from paused or idle with history)."""
        if not self.history or self.replay_running:
            return

        # If coming from idle (history exists but replay not started)
        if not self.replay_paused:
            self._restore_initial_grid()
            self.replay_index = 0
            self.replay_paused = True
            self._set_buttons_replay("paused")

        total = len(self.history)
        if self.replay_index >= total:
            if self._last_solution:
                self._fill_solution(self._last_solution)
            self._set_status("All steps complete", "ok")
            self.replay_paused = False
            self._set_buttons_replay("idle")
            self._step_var.set("")
            return

        self._apply_step(self.replay_index)
        self.replay_index += 1
        self._step_var.set(f"Step {self.replay_index} / {total}")
        remaining = total - self.replay_index
        suffix = f"  ({remaining} remaining)" if remaining else "  — all done"
        self._set_status(
            f"Step {self.replay_index} of {total}{suffix}", "info")

    def _skip_to_end(self):
        """Stop replay and show the full solution immediately."""
        if not self._last_solution:
            self._set_status("No solution to display", "warn")
            return
        self.replay_running = False
        self.replay_paused  = False
        self.replay_index   = len(self.history)
        self._fill_solution(self._last_solution)
        self._set_status("Skipped to final solution", "ok")
        self._set_buttons_replay("idle")
        self._step_var.set("")


# ENTRY POINT
if __name__ == "__main__":
    app = FutoshikiApp()
    app.mainloop()
