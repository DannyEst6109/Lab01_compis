from __future__ import annotations

import importlib.util
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from adapter import adapt_grammar
from parser_runtime import slr_parse, tokenize_input
from primero_siguiente import compute_first, compute_follow
from slr_builder import build_parser
from yalp_parser import parse_yalp_file


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YAPar + YALex | Generador y Analizador SLR")
        self.geometry("1200x760")

        self.yalp_path = tk.StringVar()
        self.lexer_path = tk.StringVar()
        self.input_path = tk.StringVar()

        self.grammar = None
        self.automaton = None
        self.tables = None

        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=8)

        self._path_row(top, "Archivo .yalp", self.yalp_path, 0)
        self._path_row(top, "Lexer .py", self.lexer_path, 1)
        self._path_row(top, "Entrada .txt", self.input_path, 2)

        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=8)
        ttk.Button(actions, text="1) Construir Gramática+SLR", command=self.build_parser_pipeline).pack(side="left", padx=4)
        ttk.Button(actions, text="2) Ejecutar Parsing", command=self.run_parsing).pack(side="left", padx=4)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.out = tk.Text(notebook, wrap="word")
        self.out.configure(font=("Consolas", 10))
        notebook.add(self.out, text="Log")

        self.table_text = tk.Text(notebook, wrap="none")
        self.table_text.configure(font=("Consolas", 9))
        notebook.add(self.table_text, text="ACTION/GOTO")

        self.auto_text = tk.Text(notebook, wrap="none")
        self.auto_text.configure(font=("Consolas", 9))
        notebook.add(self.auto_text, text="Autómata LR(0)")

    def _path_row(self, parent, label, var, row):
        ttk.Label(parent, text=label, width=14).grid(row=row, column=0, sticky="w", padx=2, pady=2)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=2, pady=2)
        ttk.Button(parent, text="...", command=lambda v=var: self._pick(v)).grid(row=row, column=2, padx=2)
        parent.columnconfigure(1, weight=1)

    def _pick(self, var):
        path = filedialog.askopenfilename()
        if path:
            var.set(path)

    def _append(self, msg):
        self.out.insert("end", msg + "\n")
        self.out.see("end")

    def build_parser_pipeline(self):
        self.out.delete("1.0", "end")
        self.table_text.delete("1.0", "end")
        self.auto_text.delete("1.0", "end")

        yalp = self.yalp_path.get().strip()
        if not yalp or not os.path.exists(yalp):
            messagebox.showerror("Error", "Seleccione un archivo .yalp válido")
            return

        g = parse_yalp_file(yalp)
        first = compute_first(g)
        follow = compute_follow(g, first)
        g2 = adapt_grammar(g, first, follow, g.ignored)

        aug, auto, tables = build_parser(g2)
        self.grammar, self.automaton, self.tables = aug, auto, tables

        self._append("Parser SLR construido correctamente.")
        self._append(f"No terminales: {len(aug.non_terminals)} | Terminales: {len(aug.terminals)}")
        self._append(f"Estados LR(0): {len(auto.states)}")
        self._append(f"Conflictos SLR: {len(tables.conflicts)}")
        for c in tables.conflicts:
            self._append("  - " + c)

        for state in auto.states:
            self.auto_text.insert("end", f"Estado {state.id}\n")
            for item in sorted(state.items, key=str):
                self.auto_text.insert("end", f"  {item}\n")
            for (src, sym), dst in sorted(auto.transitions.items()):
                if src == state.id:
                    self.auto_text.insert("end", f"    --{sym}--> {dst}\n")
            self.auto_text.insert("end", "\n")

        self.table_text.insert("end", "ACTION\n")
        for (s, t), act in sorted(tables.action.items()):
            self.table_text.insert("end", f"  ({s}, {t}) => {act}\n")
        self.table_text.insert("end", "\nGOTO\n")
        for (s, nt), st in sorted(tables.goto.items()):
            self.table_text.insert("end", f"  ({s}, {nt}) => {st}\n")

    def run_parsing(self):
        if self.grammar is None or self.tables is None:
            messagebox.showerror("Error", "Primero construye el parser SLR")
            return

        inp = self.input_path.get().strip()
        if not inp or not os.path.exists(inp):
            messagebox.showerror("Error", "Seleccione un archivo de entrada válido")
            return

        with open(inp, "r", encoding="utf-8") as f:
            text = f.read()

        lexer_mod = None
        lexer_file = self.lexer_path.get().strip()
        if lexer_file:
            spec = importlib.util.spec_from_file_location("external_lexer", lexer_file)
            if spec and spec.loader:
                lexer_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(lexer_mod)

        token_stream, lex_errors = tokenize_input(text, lexer_mod)
        for err in lex_errors:
            self._append(err)
        self._append(f"Tokens reconocidos: {[t for t, _ in token_stream]}")

        result = slr_parse(token_stream, self.grammar, self.tables)
        for action in result.actions:
            self._append(action)
        for err in result.errors:
            self._append(err)

        self._append("Resultado final: " + ("ACEPTADA" if result.accepted else "RECHAZADA"))


if __name__ == "__main__":
    App().mainloop()
