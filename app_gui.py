"""Interfaz gráfica para el generador y simulador de analizadores léxicos YALex."""

from __future__ import annotations

import importlib.util
import io
import math
import os
from contextlib import redirect_stdout
from tkinter import BOTH, END, LEFT, RIGHT, VERTICAL, X, Y, filedialog, messagebox, ttk
import tkinter as tk

from LexerGenerator import build_dfa_dict, build_lexer
from ParserYal import YALexParser
from lexer_generator import generate_lexer, generate_token_module


class LexerInadorGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Lexer-inador GUI · YALex")
        self.root.geometry("1250x760")

        self.yal_path = tk.StringVar(value="minipython.yal")
        self.input_path = tk.StringVar(value="mini_example_T.txt")

        self.current_dfa_dict: dict | None = None
        self.current_internal_dfa: dict | None = None

        self._build_layout()

    def _build_layout(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=X)

        ttk.Label(top, text="Archivo .yal").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.yal_path, width=70).grid(row=0, column=1, padx=6, sticky="we")
        ttk.Button(top, text="Buscar", command=self._pick_yal).grid(row=0, column=2, padx=4)

        ttk.Label(top, text="Archivo .txt").grid(row=1, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.input_path, width=70).grid(row=1, column=1, padx=6, sticky="we")
        ttk.Button(top, text="Buscar", command=self._pick_txt).grid(row=1, column=2, padx=4)

        ttk.Button(top, text="1) Generar lexer + AFD", command=self.generate_lexer_and_dfa).grid(row=0, column=3, rowspan=2, padx=8)
        ttk.Button(top, text="2) Analizar entrada", command=self.analyze_input).grid(row=0, column=4, rowspan=2, padx=8)
        top.columnconfigure(1, weight=1)

        main = ttk.Panedwindow(self.root, orient="horizontal")
        main.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))

        left_frame = ttk.Frame(main)
        right_frame = ttk.Frame(main)
        main.add(left_frame, weight=2)
        main.add(right_frame, weight=3)

        ttk.Label(left_frame, text="Diagrama del AFD (minimizado)").pack(anchor="w", padx=5, pady=(5, 2))
        self.canvas = tk.Canvas(left_frame, bg="#f8f8f8", width=520, height=660)
        self.canvas.pack(fill=BOTH, expand=True, padx=5, pady=5)

        panel = ttk.Notebook(right_frame)
        panel.pack(fill=BOTH, expand=True)

        tokens_tab = ttk.Frame(panel)
        log_tab = ttk.Frame(panel)
        trans_tab = ttk.Frame(panel)

        panel.add(tokens_tab, text="Tokens")
        panel.add(log_tab, text="Logs")
        panel.add(trans_tab, text="Transiciones")

        self.tokens_text = tk.Text(tokens_tab, wrap="word")
        self.tokens_text.pack(fill=BOTH, expand=True)

        self.logs_text = tk.Text(log_tab, wrap="word")
        self.logs_text.pack(fill=BOTH, expand=True)

        trans_container = ttk.Frame(trans_tab)
        trans_container.pack(fill=BOTH, expand=True)
        cols = ("estado", "simbolo", "destino")
        self.trans_tree = ttk.Treeview(trans_container, columns=cols, show="headings")
        for c, title, w in (("estado", "Estado", 100), ("simbolo", "Símbolo", 140), ("destino", "Destino", 100)):
            self.trans_tree.heading(c, text=title)
            self.trans_tree.column(c, width=w, anchor="center")
        scroll = ttk.Scrollbar(trans_container, orient=VERTICAL, command=self.trans_tree.yview)
        self.trans_tree.configure(yscrollcommand=scroll.set)
        self.trans_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scroll.pack(side=RIGHT, fill=Y)

    def _pick_yal(self) -> None:
        file_path = filedialog.askopenfilename(title="Selecciona archivo YAL", filetypes=[("YALex", "*.yal"), ("Todos", "*.*")])
        if file_path:
            self.yal_path.set(file_path)

    def _pick_txt(self) -> None:
        file_path = filedialog.askopenfilename(title="Selecciona archivo de entrada", filetypes=[("Text", "*.txt"), ("Todos", "*.*")])
        if file_path:
            self.input_path.set(file_path)

    def _append_log(self, msg: str) -> None:
        self.logs_text.insert(END, msg + "\n")
        self.logs_text.see(END)

    def generate_lexer_and_dfa(self) -> None:
        yal_file = self.yal_path.get().strip()
        if not yal_file or not os.path.exists(yal_file):
            messagebox.showerror("Error", "No se encontró el archivo .yal seleccionado.")
            return

        self.logs_text.delete("1.0", END)
        self.tokens_text.delete("1.0", END)
        self._append_log(f"▶ Parseando {yal_file}")

        try:
            parser = YALexParser().parse(yal_file)
            rules = parser.get_all_rules()

            self.current_dfa_dict = build_dfa_dict(rules, parser=parser, minimize=True, verbose=True)
            self.current_internal_dfa = build_lexer(rules, minimize=True, verbose=False)

            generate_token_module(self.current_dfa_dict, "myToken.py")
            generate_lexer(self.current_dfa_dict, output_path="thelexer.py")

            self._fill_transition_table(self.current_dfa_dict)
            self._draw_dfa(self.current_dfa_dict)

            self._append_log("✅ Lexer generado en thelexer.py y tokens en myToken.py")
            messagebox.showinfo("Completado", "Se generó el lexer y se dibujó el AFD.")
        except Exception as exc:
            self._append_log(f"❌ Error: {exc}")
            messagebox.showerror("Error", str(exc))

    def _fill_transition_table(self, dfa_dict: dict) -> None:
        for row in self.trans_tree.get_children():
            self.trans_tree.delete(row)

        for state, mapping in sorted(dfa_dict["transitions"].items()):
            for sym, dest in sorted(mapping.items(), key=lambda x: (x[0], x[1])):
                self.trans_tree.insert("", END, values=(f"S{state}", repr(sym), f"S{dest}"))

    def _draw_dfa(self, dfa_dict: dict) -> None:
        self.canvas.delete("all")

        transitions = dfa_dict["transitions"]
        accepting = set(dfa_dict["accepting_states"].keys())
        states = sorted(transitions.keys())

        if not states:
            return

        w = max(680, self.canvas.winfo_width())
        h = max(600, self.canvas.winfo_height())
        cx, cy = w / 2, h / 2
        radius = min(w, h) * 0.35

        pos: dict[int, tuple[float, float]] = {}
        n = len(states)
        for i, s in enumerate(states):
            angle = 2 * math.pi * i / n - math.pi / 2
            pos[s] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))

        node_r = 24

        self.canvas.create_text(36, 25, text="Inicio", font=("Arial", 10, "bold"))
        sx, sy = pos[dfa_dict["initial_state"]]
        self.canvas.create_line(70, 25, sx - node_r, sy, arrow=tk.LAST, width=2)

        edge_labels: dict[tuple[int, int], list[str]] = {}
        for s, mapping in transitions.items():
            for symbol, d in mapping.items():
                edge_labels.setdefault((s, d), []).append(symbol)

        for (s, d), labels in edge_labels.items():
            x1, y1 = pos[s]
            x2, y2 = pos[d]

            if s == d:
                self.canvas.create_arc(x1 - 35, y1 - 48, x1 + 35, y1 + 2, start=30, extent=280, style="arc", width=2)
                label = ", ".join(sorted(repr(x) for x in labels))
                self.canvas.create_text(x1, y1 - 55, text=label[:30], font=("Arial", 8))
                continue

            self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, width=1.5, fill="#555")
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            label = ", ".join(sorted(repr(x) for x in labels))
            self.canvas.create_text(mx, my - 8, text=label[:28], font=("Arial", 8), fill="#222")

        for s in states:
            x, y = pos[s]
            fill = "#d9f2d9" if s in accepting else "#ffffff"
            self.canvas.create_oval(x - node_r, y - node_r, x + node_r, y + node_r, fill=fill, outline="#1f1f1f", width=2)
            if s in accepting:
                self.canvas.create_oval(x - node_r + 5, y - node_r + 5, x + node_r - 5, y + node_r - 5, outline="#1f1f1f", width=1.8)
            self.canvas.create_text(x, y, text=f"S{s}", font=("Arial", 10, "bold"))

    def analyze_input(self) -> None:
        txt_file = self.input_path.get().strip()
        if not txt_file or not os.path.exists(txt_file):
            messagebox.showerror("Error", "No se encontró el archivo .txt seleccionado.")
            return

        if self.current_dfa_dict is None:
            messagebox.showwarning("Atención", "Primero genera el lexer con el archivo .yal.")
            return

        with open(txt_file, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            spec = importlib.util.spec_from_file_location("thelexer_runtime", "thelexer.py")
            if spec is None or spec.loader is None:
                raise RuntimeError("No fue posible cargar thelexer.py")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            entrypoint = self.current_dfa_dict["entrypoint"]
            lexer_fn = getattr(module, entrypoint)

            buf = io.StringIO()
            with redirect_stdout(buf):
                tokens = lexer_fn(content)
            console = buf.getvalue()

            self.tokens_text.delete("1.0", END)
            self.tokens_text.insert(END, f"Archivo: {txt_file}\n\n")
            self.tokens_text.insert(END, "Tokens reconocidos:\n")
            for i, tok in enumerate(tokens, start=1):
                self.tokens_text.insert(END, f"{i:>3}. {tok}\n")

            self._append_log(f"▶ Entrada analizada: {txt_file}")
            if console.strip():
                self._append_log("Salida de acciones/errores:")
                self._append_log(console.rstrip())
            self._append_log(f"✅ Total de tokens reconocidos: {len(tokens)}")
        except Exception as exc:
            self._append_log(f"❌ Error al ejecutar thelexer.py: {exc}")
            messagebox.showerror("Error", str(exc))


def main() -> None:
    root = tk.Tk()
    ttk.Style().theme_use("clam")
    LexerInadorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
