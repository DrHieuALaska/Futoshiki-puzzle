import copy
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import os
import random

# ------------------------------------------------
# Colors & Fonts
# ------------------------------------------------
BG          = "#0b0d14"
PANEL_BG    = "#13151f"
CELL_BG     = "#1c1f2e"
CELL_FG     = "#e8eaf6"
GIVEN_BG    = "#252a42"
GIVEN_FG    = "#90caf9"
SOLVED_FG   = "#a5d6a7"
STEP_FG     = "#ffcc80"
CON_FG      = "#ef9a9a"
BTN_BG      = "#1e2235"
BTN_FG      = "#c5cae9"
BTN_ACT     = "#2e3455"
BTN_SEL     = "#3d4a7a"
ACCENT      = "#5c6bc0"
ACCENT2     = "#7986cb"
ERR_COLOR   = "#ef5350"
OK_COLOR    = "#66bb6a"
WARN_COLOR  = "#ffb74d"
BORDER      = "#2a2f50"
STAT_BG     = "#0e1020"
STAT_LABEL  = "#7986cb"
STAT_VALUE  = "#e8eaf6"

FONT_MONO   = ("Courier New", 16, "bold")
FONT_CON    = ("Courier New", 12, "bold")
FONT_UI     = ("Segoe UI", 9)
FONT_STATUS = ("Segoe UI", 9)
FONT_STAT_L = ("Segoe UI", 8)
FONT_STAT_V = ("Courier New", 10, "bold")
FONT_TITLE  = ("Courier New", 22, "bold")

# ------------------------------------------------
# Imports 
# ------------------------------------------------
from input_output.parse_input import parse_input
from search.back_tracking import solve_backtracking
from search.forward_chaining_solve import forward_chaining_solve
from search.astar import solve_astar
from search.backward_chaining_solve import backward_chaining_solve
from search.brute_force import brute_force
from search.hybrid_backtracking_with_fc import solve_hybrid_backtracking_with_fc
from FOL.kb import KnowledgeBase

# ------------------------------------------------
# Main App
# ------------------------------------------------
class FutoshikiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Futoshiki Solver")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(820, 520)

        self.puzzle     = None
        self.cell_vars  = []
        self.cell_wdgs  = []
        self.given_mask = []
        self.solving    = False
        self.stop_flag  = False
        self.algo_var   = tk.StringVar(value="Backtracking")
        self.size_var   = tk.StringVar(value="4x4")
        self.diff_var   = tk.StringVar(value="easy")

        self._build_ui()

    # ── UI construction ──────────────────────────────────────
    def _build_ui(self):
        # ── Header bar ──────────────────────────────────────
        header = tk.Frame(self, bg=PANEL_BG)
        header.pack(fill="x")

        tk.Frame(header, bg=ACCENT, width=4).pack(side="left", fill="y")

        tk.Label(header, text="FUTOSHIKI", font=FONT_TITLE,
                 bg=PANEL_BG, fg=ACCENT2, padx=18, pady=12).pack(side="left")

        hbtn = tk.Frame(header, bg=PANEL_BG, padx=12)
        hbtn.pack(side="right")
        
        # Size selector
        self.size_menu = tk.Menubutton(hbtn, textvariable=self.size_var, bg=BTN_BG, fg=BTN_FG,
                                       activebackground=BTN_ACT, activeforeground=BTN_FG,
                                       font=FONT_UI, relief="flat", bd=0, padx=14, pady=7, cursor="hand2")
        self.size_menu.menu = tk.Menu(self.size_menu, tearoff=0, bg=PANEL_BG, fg=BTN_FG,
                                      activebackground=BTN_ACT, activeforeground=ACCENT2)
        for size in ["4x4", "5x5", "6x6", "7x7", "8x8", "9x9"]:
            self.size_menu.menu.add_radiobutton(label=size, variable=self.size_var, value=size)
        self.size_menu["menu"] = self.size_menu.menu
        self.size_menu.pack(side="left", padx=4)
        self.size_menu.bind("<Enter>", lambda e: self.size_menu.config(bg=BTN_ACT))
        self.size_menu.bind("<Leave>", lambda e: self.size_menu.config(bg=BTN_BG))

        # Difficulty selector
        self.diff_menu = tk.Menubutton(hbtn, textvariable=self.diff_var, bg=BTN_BG, fg=BTN_FG,
                                       activebackground=BTN_ACT, activeforeground=BTN_FG,
                                       font=FONT_UI, relief="flat", bd=0, padx=14, pady=7, cursor="hand2")
        self.diff_menu.menu = tk.Menu(self.diff_menu, tearoff=0, bg=PANEL_BG, fg=BTN_FG,
                                      activebackground=BTN_ACT, activeforeground=ACCENT2)
        for diff in ["easy", "medium", "hard"]:
            self.diff_menu.menu.add_radiobutton(label=diff, variable=self.diff_var, value=diff)
        self.diff_menu["menu"] = self.diff_menu.menu
        self.diff_menu.pack(side="left", padx=4)
        self.diff_menu.bind("<Enter>", lambda e: self.diff_menu.config(bg=BTN_ACT))
        self.diff_menu.bind("<Leave>", lambda e: self.diff_menu.config(bg=BTN_BG))

        self.random_btn = self._btn(hbtn, "🎲 Random Puzzle", self._load_random, accent=True)
        self.random_btn.pack(side="left", padx=4, pady=10)

        self.load_btn = self._btn(hbtn, "📁 Load File", self._load_file)
        self.load_btn.pack(side="left", padx=4, pady=10)

        self.solve_btn = self._btn(hbtn, "▶  Solve", self._solve)
        self.solve_btn.pack(side="left", padx=4, pady=10)
        
        self.stop_btn = self._btn(hbtn, "⏹ Stop", self._stop_solver)
        # Initially hidden

        self.reset_btn = self._btn(hbtn, "↺  Reset", self._reset)
        self.reset_btn.pack(side="left", padx=4, pady=10)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Algorithm selector ───────────────────────────────
        algo_bar = tk.Frame(self, bg=BG, pady=8)
        algo_bar.pack(fill="x", padx=20)

        tk.Label(algo_bar, text="ALGORITHM:", font=("Segoe UI", 8, "bold"),
                 bg=BG, fg="#555875").pack(side="left", padx=(0, 10))

        self.algo_buttons = []
        for name in ["A*", "Backtracking", "Brute Force", "Forward Chaining", "Backward Chaining", "Hybrid"]:
            rb = tk.Radiobutton(
                algo_bar, text=name, variable=self.algo_var, value=name,
                bg=BG, fg=BTN_FG, selectcolor=BTN_SEL,
                activebackground=BG, activeforeground=ACCENT2,
                font=FONT_UI, bd=0, padx=10, pady=4,
                indicatoron=False, relief="flat", cursor="hand2"
            )
            rb.pack(side="left", padx=3)
            self.algo_buttons.append(rb)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Main area: puzzle + stats ──
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)

        self.puzzle_outer = tk.Frame(main, bg=BG)
        self.puzzle_outer.pack(side="left", fill="both", expand=True, padx=24, pady=20)

        self.loading_var = tk.StringVar(value="")
        self.loading_lbl = tk.Label(self.puzzle_outer, textvariable=self.loading_var,
                                    bg=BG, fg="#ffcc80", font=("Segoe UI", 11, "italic"))
        self.loading_lbl.pack()

        self.grid_frame = tk.Frame(self.puzzle_outer, bg=BG)
        self.grid_frame.pack(anchor="nw")

        tk.Label(self.grid_frame, text="Load a puzzle file to begin",
                 bg=BG, fg="#353850", font=("Courier New", 13)).pack(pady=60, padx=40)

        self._build_stats_panel(main)

        # ── Status bar ──────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")
        status_bar = tk.Frame(self, bg=PANEL_BG, pady=5)
        status_bar.pack(fill="x", side="bottom")

        tk.Frame(status_bar, bg=ACCENT, width=3).pack(side="left", fill="y")

        self.status_var = tk.StringVar(value="No puzzle loaded")
        self.status_lbl = tk.Label(status_bar, textvariable=self.status_var,
                                   bg=PANEL_BG, fg="#90a4ae", font=FONT_STATUS,
                                   anchor="w", padx=12)
        self.status_lbl.pack(side="left", fill="x", expand=True)

        self.time_var = tk.StringVar(value="")
        tk.Label(status_bar, textvariable=self.time_var,
                 bg=PANEL_BG, fg=ACCENT2, font=("Courier New", 9, "bold"),
                 anchor="e", padx=16).pack(side="right")

    def _build_stats_panel(self, parent):
        panel = tk.Frame(parent, bg=STAT_BG, width=220)
        panel.pack(side="right", fill="y")
        panel.pack_propagate(False)

        tk.Frame(panel, bg=BORDER, width=1).pack(side="left", fill="y")

        inner = tk.Frame(panel, bg=STAT_BG, padx=16, pady=16)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text="STATISTICS", font=("Segoe UI", 8, "bold"),
                 bg=STAT_BG, fg=ACCENT, anchor="w").pack(fill="x", pady=(0, 12))

        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=(0, 12))

        stat_fields = [
            ("Algorithm",   "algo_disp"),
            ("Puzzle Size", "size_disp"),
            ("Status",      "status_disp"),
            ("Time (s)",    "time_disp"),
            ("Memory (KB)", "mem_disp"),
            ("Expansions",  "exp_disp"),
            ("Generated",   "gen_disp"),
        ]

        self.stat_vars = {}
        for label, key in stat_fields:
            row = tk.Frame(inner, bg=STAT_BG)
            row.pack(fill="x", pady=5)

            tk.Label(row, text=label.upper(), font=FONT_STAT_L,
                     bg=STAT_BG, fg=STAT_LABEL, anchor="w").pack(fill="x")

            var = tk.StringVar(value="—")
            self.stat_vars[key] = var
            tk.Label(row, textvariable=var, font=FONT_STAT_V,
                     bg=STAT_BG, fg=STAT_VALUE, anchor="w").pack(fill="x")

            tk.Frame(inner, bg="#1a1d2e", height=1).pack(fill="x", pady=(4, 0))

    def _btn(self, parent, text, cmd, accent=False):
        bg  = ACCENT   if accent else BTN_BG
        fg  = "#ffffff" if accent else BTN_FG
        abg = "#6e7dd6" if accent else BTN_ACT
        b = tk.Button(parent, text=text, command=cmd,
                      bg=bg, fg=fg, activebackground=abg,
                      activeforeground=fg, font=FONT_UI,
                      relief="flat", bd=0, padx=14, pady=7,
                      cursor="hand2")
        b.bind("<Enter>", lambda e: b.config(bg=abg))
        b.bind("<Leave>", lambda e: b.config(bg=bg))
        return b

    def _reset_stats(self):
        for key in self.stat_vars:
            self.stat_vars[key].set("—")

    def _update_stats(self, algo, size, status, stats):
        self.stat_vars["algo_disp"].set(algo)
        self.stat_vars["size_disp"].set(size)
        self.stat_vars["status_disp"].set(status)
        if stats:
            t = stats.get("time_sec")
            self.stat_vars["time_disp"].set(f"{t:.6f}" if t is not None else "—")
            m = stats.get("peak_mem_kb")
            self.stat_vars["mem_disp"].set(f"{m:.2f}" if m is not None else "—")
            e = stats.get("expansions")
            self.stat_vars["exp_disp"].set(str(e) if e is not None else "—")
            g = stats.get("generated")
            self.stat_vars["gen_disp"].set(str(g) if g is not None else "—")

    # ── Grid rendering ────────────────────────────────────────
    def _render_grid(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.cell_vars  = []
        self.cell_wdgs  = []
        self.given_mask = []

        p = self.puzzle
        N = p.N
        CELL = max(44, min(62, 460 // N))
        CON  = 20

        for i in range(N):
            row_vars, row_wdgs, row_given = [], [], []
            for j in range(N):
                val   = p.grid[i][j]
                given = val != 0

                var = tk.StringVar(value=str(val) if val else "")
                row_vars.append(var)
                row_given.append(given)

                cell = tk.Label(self.grid_frame, textvariable=var, width=2, font=FONT_MONO,
                                bg=GIVEN_BG if given else CELL_BG,
                                fg=GIVEN_FG if given else CELL_FG,
                                relief="flat", bd=0, highlightthickness=1, highlightbackground=BORDER)
                cell.place(x=j*(CELL+CON), y=i*(CELL+CON), width=CELL, height=CELL)
                row_wdgs.append(cell)

                if j < N-1:
                    c   = p.h_constraints[i][j]
                    sym = "<" if c == 1 else (">" if c == -1 else "")
                    tk.Label(self.grid_frame, text=sym, bg=BG, fg=CON_FG, font=FONT_CON).place(
                        x=j*(CELL+CON)+CELL, y=i*(CELL+CON)+(CELL-20)//2, width=CON, height=20)

                if i < N-1:
                    c   = p.v_constraints[i][j]
                    sym = "∧" if c == 1 else ("∨" if c == -1 else "")
                    tk.Label(self.grid_frame, text=sym, bg=BG, fg=CON_FG, font=FONT_CON).place(
                        x=j*(CELL+CON)+(CELL-20)//2, y=i*(CELL+CON)+CELL, width=20, height=CON)

            self.cell_vars.append(row_vars)
            self.cell_wdgs.append(row_wdgs)
            self.given_mask.append(row_given)

        total_w = N*CELL + (N-1)*CON
        total_h = N*CELL + (N-1)*CON
        self.grid_frame.config(width=total_w, height=total_h)

    # ── Actions ───────────────────────────────────────────────
    def _load_random(self):
        size = self.size_var.get()
        diff = self.diff_var.get()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        folder = os.path.join(base_dir, "Inputs", diff, size)
        
        if not os.path.exists(folder):
            messagebox.showerror("Error", f"Folder not found:\n{folder}")
            return

        files = [f for f in os.listdir(folder) if f.endswith(".txt")]
        if not files:
            messagebox.showerror("Error", "No puzzle files found.")
            return

        file = random.choice(files)
        path = os.path.join(folder, file)

        try:
            self.puzzle = parse_input(path)
            self._render_grid()
            self._set_status(f"Random: {diff}/{size}/{file}", "info")
            self.time_var.set("")
            self._reset_stats()
            self.stat_vars["size_disp"].set(f"{self.puzzle.N}×{self.puzzle.N}")
            self.stat_vars["status_disp"].set("Ready")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load puzzle:\n{e}")

    def _load_file(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        initial_dir = os.path.join(base_dir, "Inputs")
        path = filedialog.askopenfilename(
            title="Select puzzle input file",
            initialdir=initial_dir,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path: return
        try:
            self.puzzle = parse_input(path)
            self._render_grid()
            fname = path.split("/")[-1]
            self._set_status(f"Loaded: {fname}  —  {self.puzzle.N}×{self.puzzle.N} grid", "info")
            self.time_var.set("")
            self._reset_stats()
            self.stat_vars["size_disp"].set(f"{self.puzzle.N}×{self.puzzle.N}")
            self.stat_vars["status_disp"].set("Ready")
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file:\n{e}")

    def _reset(self):
        if self.puzzle is None: return
        for i in range(self.puzzle.N):
            for j in range(self.puzzle.N):
                if self.given_mask[i][j]:
                    self.cell_vars[i][j].set(str(self.puzzle.grid[i][j]))
                    self.cell_wdgs[i][j].config(bg=GIVEN_BG, fg=GIVEN_FG)
                else:
                    self.cell_vars[i][j].set("")
                    self.cell_wdgs[i][j].config(bg=CELL_BG, fg=CELL_FG)
        self._set_status("Board reset", "info")
        self.time_var.set("")
        self._reset_stats()

    def _solve(self):
        if self.puzzle is None:
            messagebox.showwarning("No Puzzle", "Please load a puzzle file first.")
            return
        if self.solving:
            return
        
        self._reset()
        self.solving = True
        self.stop_flag = False

        self._set_status("Solving…", "info")
        self.loading_var.set("⏳ Solving... Please wait")
        self.stat_vars["status_disp"].set("Solving…")
        
        # Disable buttons
        self.size_menu.config(state="disabled")
        self.diff_menu.config(state="disabled")
        self.random_btn.config(state="disabled")
        self.load_btn.config(state="disabled")
        self.reset_btn.config(state="disabled")
        for rb in self.algo_buttons:
            rb.config(state="disabled")
            
        # Toggle buttons
        self.solve_btn.pack_forget()
        self.stop_btn.pack(side="left", padx=4, pady=10)
        self.update_idletasks()

        algo_to_run = self.algo_var.get()
        puzzle_copy = copy.deepcopy(self.puzzle)

        threading.Thread(
            target=self._run_solver, 
            args=(algo_to_run, puzzle_copy), 
            daemon=True
        ).start()

    def _stop_solver(self):
        if not self.solving: return
        self.loading_var.set("")
        self.stop_flag = True
        self.solving = False
        self._set_status("Stopped by user", "warn")
        self.stat_vars["status_disp"].set("Stopped")
        self._enable_buttons()

    def _run_solver(self, algo, p):
        kb       = KnowledgeBase(p)
        t0       = time.time()
        solution = None
        stats    = {}

        try:
            if algo == "A*":
                solution, stats = solve_astar(p, kb, heuristic="ac3")
            elif algo == "Backtracking":
                solution, stats = solve_backtracking(p)
            elif algo == "Brute Force":
                solution, stats = brute_force(p)
            elif algo == "Forward Chaining":
                is_complete, solution, domains, stats = forward_chaining_solve(p, kb)
                if not is_complete: solution = None
            elif algo == "Backward Chaining":
                solution, stats = backward_chaining_solve(p, kb)
            elif algo == "Hybrid":
                solution, stats = solve_hybrid_backtracking_with_fc(p, kb)
        except Exception as e:
            if not self.stop_flag:
                self.after(0, self._set_status, f"Error: {e}", "error")
                self.after(0, self.stat_vars["status_disp"].set, "Error")
            self.solving = False
            self.after(0, self._enable_buttons)
            return

        if self.stop_flag:
            self.solving = False
            return

        elapsed = time.time() - t0
        if isinstance(stats, dict) and "time_sec" not in stats:
            stats["time_sec"] = elapsed

        self.solving = False
        self.after(0, self._show_result, solution, elapsed, algo, stats)
        self.after(0, self._enable_buttons)

    def _enable_buttons(self):
        self.loading_var.set("")
        self.size_menu.config(state="normal")
        self.diff_menu.config(state="normal")
        self.random_btn.config(state="normal")
        self.load_btn.config(state="normal")
        self.reset_btn.config(state="normal")
        for rb in self.algo_buttons:
            rb.config(state="normal")
        self.stop_btn.pack_forget()
        self.solve_btn.pack(side="left", padx=4, pady=10)

    def _update_cell(self, i, j, val, mode="solved"):
        if val == 0:
            self.cell_vars[i][j].set("")
            self.cell_wdgs[i][j].config(bg=CELL_BG, fg=CELL_FG)
        else:
            self.cell_vars[i][j].set(str(val))
            color = STEP_FG if mode == "step" else SOLVED_FG
            self.cell_wdgs[i][j].config(bg=CELL_BG, fg=color)

    def _show_result(self, solution, elapsed, algo, stats):
        size_str = f"{self.puzzle.N}×{self.puzzle.N}" if self.puzzle else "—"
        if solution is None:
            self._set_status("❌  No solution found", "error")
            self.time_var.set("")
            self._update_stats(algo, size_str, "No Solution", stats)
            messagebox.showinfo("Result", "No solution could be found for this puzzle.")
            return

        self._update_all_cells(solution)
        self._set_status(f"✅  Solution found  —  {algo}", "ok")
        self.time_var.set(f"⏱  {elapsed:.4f}s")
        self._update_stats(algo, size_str, "Solved ✓", stats)

    def _update_all_cells(self, solution):
        N = self.puzzle.N
        for i in range(N):
            for j in range(N):
                if not self.given_mask[i][j]:
                    self._update_cell(i, j, solution.grid[i][j], "solved")
        self.update_idletasks() 
    
    def _set_status(self, msg, kind="info"):
        color = {"info": "#90a4ae", "ok": OK_COLOR, "error": ERR_COLOR,
                 "warn": WARN_COLOR}.get(kind, "#90a4ae")
        self.status_var.set(msg)
        self.status_lbl.config(fg=color)

if __name__ == "__main__":
    app = FutoshikiApp()
    app.mainloop()