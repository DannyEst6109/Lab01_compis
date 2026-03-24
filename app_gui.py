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
        self.root.geometry("1320x800")
        self.root.minsize(1120, 700)

        self.yal_path = tk.StringVar(value="minipython.yal")
        self.input_path = tk.StringVar(value="mini_example_T.txt")

        self.current_dfa_dict: dict | None = None
        self.current_internal_dfa: dict | None = None

        self._configure_styles()
        self._build_layout()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 17, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 10), foreground="#4a4a4a")
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        style.configure("TButton", padding=6)
        style.configure("Header.TFrame", background="#f4f7fb")
        style.configure("Status.TLabel", font=("Segoe UI", 9), foreground="#333")

    def _build_layout(self) -> None:
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(14, 12))
        header.pack(fill=X)

        ttk.Label(header, text="YALex Lexer Studio", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Genera el lexer, visualiza el autómata y analiza entradas desde un solo lugar.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 8))

        top = ttk.Frame(header)
        top.pack(fill=X)

        ttk.Label(top, text="Archivo .yal").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.yal_path, width=70).grid(row=0, column=1, padx=6, sticky="we")
        ttk.Button(top, text="Buscar", command=self._pick_yal).grid(row=0, column=2, padx=4)

        ttk.Label(top, text="Archivo .txt").grid(row=1, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.input_path, width=70).grid(row=1, column=1, padx=6, sticky="we")
        ttk.Button(top, text="Buscar", command=self._pick_txt).grid(row=1, column=2, padx=4)

        self.generate_btn = ttk.Button(
            top,
            text="1) Generar lexer + AFD",
            command=self.generate_lexer_and_dfa,
            style="Primary.TButton",
        )
        self.generate_btn.grid(row=0, column=3, rowspan=2, padx=8)

        self.analyze_btn = ttk.Button(
            top,
            text="2) Analizar entrada",
            command=self.analyze_input,
            state="disabled",
            style="Primary.TButton",
        )
        self.analyze_btn.grid(row=0, column=4, rowspan=2, padx=8)

        ttk.Button(top, text="Limpiar paneles", command=self.clear_panels).grid(row=0, column=5, rowspan=2, padx=(4, 0))
        top.columnconfigure(1, weight=1)

        main = ttk.Panedwindow(self.root, orient="horizontal")
        main.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))

        left_frame = ttk.Frame(main)
        right_frame = ttk.Frame(main)
        main.add(left_frame, weight=2)
        main.add(right_frame, weight=3)

        ttk.Label(left_frame, text="Diagrama del AFD (minimizado)", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=8, pady=(6, 2))
        self.canvas = tk.Canvas(left_frame, bg="#fbfcfe", width=520, height=620, highlightthickness=1, highlightbackground="#dde4ef")
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
        cols = ("estado", "simbolo", "destino", "aceptacion", "token")
        self.trans_tree = ttk.Treeview(trans_container, columns=cols, show="headings")
        for c, title, w in (
            ("estado", "Estado", 85),
            ("simbolo", "Símbolo", 150),
            ("destino", "Destino", 85),
            ("aceptacion", "¿Acepta?", 90),
            ("token", "Token/Prioridad", 210),
        ):
            self.trans_tree.heading(c, text=title)
            self.trans_tree.column(c, width=w, anchor="center")
        scroll = ttk.Scrollbar(trans_container, orient=VERTICAL, command=self.trans_tree.yview)
        self.trans_tree.configure(yscrollcommand=scroll.set)
        self.trans_tree.tag_configure("accepting", background="#e7f7ea")
        self.trans_tree.tag_configure("normal", background="#ffffff")
        self.trans_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scroll.pack(side=RIGHT, fill=Y)

        self.status_var = tk.StringVar(value="Listo.")
        status = ttk.Label(self.root, textvariable=self.status_var, style="Status.TLabel", anchor="w", padding=(10, 5))
        status.pack(fill=X, side="bottom")

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
        self.status_var.set(msg)

    def clear_panels(self) -> None:
        self.logs_text.delete("1.0", END)
        self.tokens_text.delete("1.0", END)
        for row in self.trans_tree.get_children():
            self.trans_tree.delete(row)
        self.canvas.delete("all")
        self.status_var.set("Paneles limpiados.")

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
            self.analyze_btn.state(["!disabled"])

            self._append_log("✅ Lexer generado en thelexer.py y tokens en myToken.py")
            messagebox.showinfo("Completado", "Se generó el lexer y se dibujó el AFD.")
        except Exception as exc:
            self._append_log(f"❌ Error: {exc}")
            messagebox.showerror("Error", str(exc))

    def _fill_transition_table(self, dfa_dict: dict) -> None:
        for row in self.trans_tree.get_children():
            self.trans_tree.delete(row)

        acc = dfa_dict["accepting_states"]
        for state, mapping in sorted(dfa_dict["transitions"].items()):
            for sym, dest in sorted(mapping.items(), key=lambda x: (x[0], x[1])):
                if state in acc:
                    info = acc[state]
                    token = info["token"] if info["token"] is not None else "(skip)"
                    token_label = f"{token} (p={info['priority']})"
                    accept_label = "Sí"
                    row_tag = "accepting"
                else:
                    token_label = "-"
                    accept_label = "No"
                    row_tag = "normal"

                self.trans_tree.insert(
                    "",
                    END,
                    values=(f"S{state}", repr(sym), f"S{dest}", accept_label, token_label),
                    tags=(row_tag,),
                )

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

        self.canvas.create_text(42, 25, text="Inicio", font=("Segoe UI", 10, "bold"), fill="#223")
        sx, sy = pos[dfa_dict["initial_state"]]
        self.canvas.create_line(80, 25, sx - node_r, sy, arrow=tk.LAST, width=2, fill="#334")

        edge_labels: dict[tuple[int, int], list[str]] = {}
        for s, mapping in transitions.items():
            for symbol, d in mapping.items():
                edge_labels.setdefault((s, d), []).append(symbol)

        for (s, d), labels in edge_labels.items():
            x1, y1 = pos[s]
            x2, y2 = pos[d]

            if s == d:
                self.canvas.create_arc(
                    x1 - 35,
                    y1 - 48,
                    x1 + 35,
                    y1 + 2,
                    start=30,
                    extent=280,
                    style="arc",
                    width=2,
                    outline="#6b7280",
                )
                label = ", ".join(sorted(repr(x) for x in labels))
                self.canvas.create_text(x1, y1 - 55, text=label[:30], font=("Consolas", 8), fill="#111827")
                continue

            self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, width=1.5, fill="#6b7280")
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            label = ", ".join(sorted(repr(x) for x in labels))
            self.canvas.create_text(mx, my - 8, text=label[:28], font=("Consolas", 8), fill="#111827")

        for s in states:
            x, y = pos[s]
            fill = "#dcfce7" if s in accepting else "#ffffff"
            self.canvas.create_oval(x - node_r, y - node_r, x + node_r, y + node_r, fill=fill, outline="#1f2937", width=2)
            if s in accepting:
                self.canvas.create_oval(
                    x - node_r + 5,
                    y - node_r + 5,
                    x + node_r - 5,
                    y + node_r - 5,
                    outline="#1f2937",
                    width=1.8,
                )
            self.canvas.create_text(x, y, text=f"S{s}", font=("Segoe UI", 10, "bold"))

        self.canvas.create_rectangle(12, h - 46, 240, h - 10, fill="#ffffff", outline="#d1d5db")
        self.canvas.create_oval(20, h - 35, 40, h - 15, fill="#dcfce7", outline="#1f2937", width=2)
        self.canvas.create_text(130, h - 25, text="Estado de aceptación", font=("Segoe UI", 9), fill="#111827")

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
    LexerInadorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
