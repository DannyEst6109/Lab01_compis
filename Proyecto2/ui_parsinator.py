from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from adapter import adapt_grammar
from lexer_bridge import (
    generate_lexer_from_yal,
    lexer_dfa_to_text,
    load_generated_lexer,
    tokenize_with_generated_lexer,
)
from parser_runtime import slr_parse
from primero_siguiente import compute_first, compute_follow
from slr_builder import build_parser
from yalp_parser import parse_yalp_file


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YAPar + YALex | Generador y Analizador SLR")
        self.geometry("1280x820")
        self.minsize(1080, 680)

        self.yal_path = tk.StringVar()
        self.yalp_path = tk.StringVar()
        self.input_path = tk.StringVar()
        self.generated_lexer_path = tk.StringVar()

        self.grammar = None
        self.automaton = None
        self.tables = None
        self.lexer_module = None
        self.lexer_entrypoint = "tokens"
        self.lexer_dfa = None

        self._configure_style()
        self._build_ui()

    def _configure_style(self):
        self.configure(bg="#f5f7fb")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f5f7fb")
        style.configure("Header.TFrame", background="#1f2937")
        style.configure("Title.TLabel", background="#1f2937", foreground="#ffffff", font=("Segoe UI", 17, "bold"))
        style.configure("Subtitle.TLabel", background="#1f2937", foreground="#d1d5db", font=("Segoe UI", 10))
        style.configure("TLabel", background="#f5f7fb", foreground="#111827", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 6))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 7))
        style.configure("TEntry", padding=5)
        style.configure("TNotebook", background="#f5f7fb", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10), padding=(12, 6))

    def _build_ui(self):
        header = ttk.Frame(self, style="Header.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text="Generador YAPar + YALex", style="Title.TLabel").pack(anchor="w", padx=18, pady=(14, 2))
        ttk.Label(
            header,
            text="Entrada: .yal, .yalp y texto fuente. Salida: lexer generado, AFD, LR(0), tablas SLR y traza de parsing.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", padx=18, pady=(0, 14))

        top = ttk.Frame(self)
        top.pack(fill="x", padx=14, pady=12)

        self._path_row(top, "1. Archivo .yal", self.yal_path, 0, [("YALex", "*.yal"), ("Todos", "*.*")])
        self._path_row(top, "2. Archivo .yalp", self.yalp_path, 1, [("YAPar", "*.yalp"), ("Todos", "*.*")])
        self._path_row(top, "Entrada .txt", self.input_path, 2, [("Texto", "*.txt"), ("Todos", "*.*")])
        self._readonly_row(top, "Lexer generado", self.generated_lexer_path, 3)

        actions = ttk.Frame(self)
        actions.pack(fill="x", padx=14)
        ttk.Button(actions, text="Generar lexer + parser SLR", style="Accent.TButton", command=self.build_parser_pipeline).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Ejecutar parsing", command=self.run_parsing).pack(side="left", padx=4)
        ttk.Button(actions, text="Limpiar salida", command=self._clear_output).pack(side="left", padx=4)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=14, pady=12)

        self.out = tk.Text(notebook, wrap="word")
        self.out.configure(font=("Consolas", 10), bg="#ffffff", relief="flat", padx=8, pady=8)
        notebook.add(self.out, text="Log")

        self.lex_text = tk.Text(notebook, wrap="none")
        self.lex_text.configure(font=("Consolas", 9), bg="#ffffff", relief="flat", padx=8, pady=8)
        notebook.add(self.lex_text, text="AFD lexico")

        self.table_text = tk.Text(notebook, wrap="none")
        self.table_text.configure(font=("Consolas", 9), bg="#ffffff", relief="flat", padx=8, pady=8)
        notebook.add(self.table_text, text="ACTION/GOTO")

        self.auto_text = tk.Text(notebook, wrap="none")
        self.auto_text.configure(font=("Consolas", 9), bg="#ffffff", relief="flat", padx=8, pady=8)
        notebook.add(self.auto_text, text="Automata LR(0)")

    def _path_row(self, parent, label, var, row, filetypes=None):
        ttk.Label(parent, text=label, width=18).grid(row=row, column=0, sticky="w", padx=2, pady=4)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=2, pady=2)
        ttk.Button(parent, text="...", command=lambda v=var, ft=filetypes: self._pick(v, ft)).grid(row=row, column=2, padx=2)
        parent.columnconfigure(1, weight=1)

    def _readonly_row(self, parent, label, var, row):
        ttk.Label(parent, text=label, width=18).grid(row=row, column=0, sticky="w", padx=2, pady=4)
        ttk.Entry(parent, textvariable=var, state="readonly").grid(row=row, column=1, sticky="ew", padx=2, pady=2)

    def _pick(self, var, filetypes=None):
        path = filedialog.askopenfilename(filetypes=filetypes or [("Todos", "*.*")])
        if path:
            var.set(path)

    def _append(self, msg):
        self.out.insert("end", msg + "\n")
        self.out.see("end")

    def _clear_output(self):
        self.out.delete("1.0", "end")

    def _clear_all(self):
        self.out.delete("1.0", "end")
        self.lex_text.delete("1.0", "end")
        self.table_text.delete("1.0", "end")
        self.auto_text.delete("1.0", "end")

    def build_parser_pipeline(self):
        self._clear_all()

        yal = self.yal_path.get().strip()
        if not yal or not os.path.exists(yal):
            messagebox.showerror("Error", "Seleccione un archivo .yal valido")
            return

        yalp = self.yalp_path.get().strip()
        if not yalp or not os.path.exists(yalp):
            messagebox.showerror("Error", "Seleccione un archivo .yalp valido")
            return

        try:
            self._append("Generando lexer independiente desde .yal...")
            lexer_build = generate_lexer_from_yal(yal)
            self.generated_lexer_path.set(str(lexer_build.lexer_path))
            self.lexer_module = load_generated_lexer(lexer_build.lexer_path)
            self.lexer_entrypoint = lexer_build.entrypoint
            self.lexer_dfa = lexer_build.dfa
            self.lex_text.insert("end", lexer_dfa_to_text(lexer_build.dfa))
            self._append(f"Lexer generado: {lexer_build.lexer_path}")
            self._append(f"Entrypoint del lexer: {lexer_build.entrypoint}()")

            self._append("\nLeyendo .yalp y calculando FIRST/FOLLOW...")
            raw_grammar = parse_yalp_file(yalp)
            first = compute_first(raw_grammar)
            follow = compute_follow(raw_grammar, first)
            grammar = adapt_grammar(raw_grammar, first, follow, raw_grammar.ignored)

            self._append("Construyendo automata LR(0) y tablas SLR...")
            aug, auto, tables = build_parser(grammar)
        except Exception as exc:
            messagebox.showerror("Error", str(exc))
            self._append(f"Error durante la generacion: {exc}")
            return

        self.grammar, self.automaton, self.tables = aug, auto, tables

        self._append("Parser SLR construido correctamente.")
        self._append(f"No terminales: {len(aug.non_terminals)} | Terminales: {len(aug.terminals)}")
        self._append(f"Estados LR(0): {len(auto.states)}")
        self._append(f"Conflictos SLR: {len(tables.conflicts)}")
        for conflict in tables.conflicts:
            self._append("  - " + conflict)

        self._render_lr0_automaton(auto)
        self._render_slr_tables(tables)

    def _render_lr0_automaton(self, automaton):
        for state in automaton.states:
            self.auto_text.insert("end", f"Estado {state.id}\n")
            for item in sorted(state.items, key=str):
                self.auto_text.insert("end", f"  {item}\n")
            for (src, sym), dst in sorted(automaton.transitions.items()):
                if src == state.id:
                    self.auto_text.insert("end", f"    --{sym}--> {dst}\n")
            self.auto_text.insert("end", "\n")

    def _render_slr_tables(self, tables):
        self.table_text.insert("end", "ACTION\n")
        for (state, terminal), action in sorted(tables.action.items()):
            self.table_text.insert("end", f"  ({state}, {terminal}) => {action}\n")
        self.table_text.insert("end", "\nGOTO\n")
        for (state, non_terminal), target in sorted(tables.goto.items()):
            self.table_text.insert("end", f"  ({state}, {non_terminal}) => {target}\n")

    def run_parsing(self):
        if self.grammar is None or self.tables is None:
            messagebox.showerror("Error", "Primero construye el parser SLR")
            return
        if self.lexer_module is None:
            messagebox.showerror("Error", "Primero genera el lexer desde el archivo .yal")
            return

        input_path = self.input_path.get().strip()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Error", "Seleccione un archivo de entrada valido")
            return

        with open(input_path, "r", encoding="utf-8") as f:
            text = f.read()

        self._append("\nEjecutando lexer generado...")
        lex_result = tokenize_with_generated_lexer(
            text,
            self.lexer_module,
            self.lexer_entrypoint,
            grammar_terminals=self.grammar.terminals,
        )
        for err in lex_result.errors:
            self._append(err)
        self._append(f"Tokens reconocidos: {[token for token, _ in lex_result.tokens]}")

        self._append("\nEjecutando parser SLR...")
        result = slr_parse(lex_result.tokens, self.grammar, self.tables)
        for action in result.actions:
            self._append(action)
        for err in result.errors:
            self._append(err)

        self._append("Resultado final: " + ("ACEPTADA" if result.accepted else "RECHAZADA"))


if __name__ == "__main__":
    App().mainloop()
