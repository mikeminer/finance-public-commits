import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime

APP_NAME = "finance_advisor_budgeting_tool_ITA"
DATA_FILE = "finance_advisor_budgeting_tool_ITA_data.json"

DEFAULT_CATEGORIES = [
    "Affitto / Mutuo",
    "Utenze (Luce/Gas/Acqua)",
    "Internet / Telefonia",
    "Spesa alimentare",
    "Trasporti (Carburante/Mezzi)",
    "Assicurazioni",
    "Salute / Farmacia",
    "Bambini / Famiglia",
    "Casa / Manutenzione",
    "Abbonamenti ricorrenti",
    "Palestra / Fitness",
    "Ristoranti / Takeaway",
    "Intrattenimento",
    "Viaggi",
    "Risparmio / Investimenti",
    "Tasse / Imposte",
    "Regali / Donazioni",
]


# ----------------------------
# Data model
# ----------------------------

@dataclass
class FixedExpense:
    name: str
    category: str
    amount: float
    notes: str = ""


@dataclass
class BankAccount:
    bank_name: str
    account_name: str
    balance: float
    fixed_expenses: List[FixedExpense]


@dataclass
class CreditCard:
    card_name: str
    due_balance: float
    fixed_expenses: List[FixedExpense]


@dataclass
class Income:
    salary_amount: float = 0.0
    salary_account_id: Optional[str] = None


class Storage:
    def __init__(self, path: str):
        self.path = path

    def load(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save(self, data: dict) -> None:
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)


# ----------------------------
# Scrollable frame (auto-adatta)
# ----------------------------

class ScrollableFrame(ttk.Frame):
    """
    Frame scrollabile verticale.
    Usalo per pannelli lunghi (gestione conto/carta) così i pulsanti non spariscono mai.
    """
    def __init__(self, parent):
        super().__init__(parent)

        self.canvas = tk.Canvas(self, highlightthickness=0, bg="#0f1115")
        self.v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.v_scroll.set)

        self.inner = ttk.Frame(self.canvas)
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll.grid(row=0, column=1, sticky="ns")

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse wheel support (Windows)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_inner_configure(self, _evt):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, _evt):
        # Inner frame stretches to canvas width
        self.canvas.itemconfigure(self.inner_id, width=self.canvas.winfo_width())

    def _on_mousewheel(self, event):
        # Scroll only if mouse is over this canvas (avoid hijacking whole app)
        x, y = self.winfo_pointerxy()
        widget = self.winfo_containing(x, y)
        if widget is None:
            return
        # if pointer is inside canvas area
        if widget == self.canvas or str(widget).startswith(str(self.canvas)):
            delta = int(-1 * (event.delta / 120))
            self.canvas.yview_scroll(delta, "units")


# ----------------------------
# App
# ----------------------------

class FinanceAdvisorBudgetingToolITA(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} — Finanze domestiche")
        self.geometry("1200x720")
        self.minsize(980, 600)

        self.storage = Storage(DATA_FILE)
        self.accounts: Dict[str, BankAccount] = {}
        self.cards: Dict[str, CreditCard] = {}
        self.income = Income()

        self.categories: List[str] = list(DEFAULT_CATEGORIES)
        self._delete_category_combos: List[ttk.Combobox] = []

        self.last_saved_at: Optional[str] = None
        self.selected_account_id: Optional[str] = None
        self.selected_card_id: Optional[str] = None

        self._setup_theme()
        self._build_ui()
        self._load_state()
        self._refresh_all()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ----------------------------
    # Theme
    # ----------------------------
    def _setup_theme(self):
        self.configure(bg="#0f1115")
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(".", font=("Segoe UI", 10))
        style.configure("TFrame", background="#0f1115")
        style.configure("TLabel", background="#0f1115", foreground="#e6e6e6")
        style.configure("TLabelframe", background="#0f1115", foreground="#e6e6e6")
        style.configure("TLabelframe.Label", background="#0f1115", foreground="#e6e6e6")
        style.configure("TButton", background="#1b1f2a", foreground="#e6e6e6", padding=8)
        style.map("TButton", background=[("active", "#262b38")], foreground=[("active", "#ffffff")])
        style.configure("TEntry", fieldbackground="#141824", foreground="#e6e6e6")
        style.configure("TCombobox", fieldbackground="#141824", foreground="#e6e6e6")
        style.map("TCombobox", fieldbackground=[("readonly", "#141824")], foreground=[("readonly", "#e6e6e6")])

        style.configure(
            "Treeview",
            background="#121522",
            fieldbackground="#121522",
            foreground="#e6e6e6",
            rowheight=26,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background="#1b1f2a",
            foreground="#e6e6e6",
            relief="flat",
        )
        style.map("Treeview.Heading", background=[("active", "#262b38")])

        style.configure("TNotebook", background="#0f1115", borderwidth=0)
        style.configure("TNotebook.Tab", background="#1b1f2a", foreground="#e6e6e6", padding=(14, 8))
        style.map("TNotebook.Tab", background=[("selected", "#262b38"), ("active", "#262b38")])

    # ----------------------------
    # Core calculations
    # ----------------------------
    def account_monthly_expenses(self, acc: BankAccount) -> float:
        return sum(e.amount for e in acc.fixed_expenses)

    def card_monthly_expenses(self, card: CreditCard) -> float:
        return sum(e.amount for e in card.fixed_expenses)

    def total_monthly_expenses(self) -> float:
        return (
            sum(self.account_monthly_expenses(a) for a in self.accounts.values())
            + sum(self.card_monthly_expenses(c) for c in self.cards.values())
        )

    def account_effective_balance(self, acc: BankAccount) -> float:
        return acc.balance - self.account_monthly_expenses(acc)

    # ----------------------------
    # UI build
    # ----------------------------
    def _build_ui(self):
        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=14, pady=14)

        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 10))

        ttk.Label(header, text=APP_NAME, font=("Segoe UI", 18, "bold")).pack(side="left")
        self.status_var = tk.StringVar(value="Pronto.")
        ttk.Label(header, textvariable=self.status_var, foreground="#9aa4b2").pack(side="left", padx=(14, 0))
        ttk.Button(header, text="💾 Salva ora", command=self.save_state).pack(side="right")

        self.nb = ttk.Notebook(root)
        self.nb.pack(fill="both", expand=True)

        self.tab_dashboard = ttk.Frame(self.nb)
        self.tab_accounts = ttk.Frame(self.nb)
        self.tab_cards = ttk.Frame(self.nb)
        self.tab_income = ttk.Frame(self.nb)

        self.nb.add(self.tab_dashboard, text="Dashboard")
        self.nb.add(self.tab_accounts, text="Banche & Conti")
        self.nb.add(self.tab_cards, text="Carte di Credito")
        self.nb.add(self.tab_income, text="Stipendio mensile")

        self._build_dashboard_tab()
        self._build_accounts_tab()
        self._build_cards_tab()
        self._build_income_tab()

    def _build_dashboard_tab(self):
        wrap = ttk.Frame(self.tab_dashboard)
        wrap.pack(fill="both", expand=True, padx=12, pady=12)

        top = ttk.Frame(wrap)
        top.pack(fill="x", pady=(0, 10))

        self.last_saved_var = tk.StringVar(value="Ultimo salvataggio: —")
        ttk.Label(top, textvariable=self.last_saved_var, foreground="#9aa4b2").pack(side="left")

        kpi_row = ttk.Frame(wrap)
        kpi_row.pack(fill="x", pady=(0, 12))

        self.kpi_cash = tk.StringVar(value="€ 0,00")
        self.kpi_debt = tk.StringVar(value="€ 0,00")
        self.kpi_net = tk.StringVar(value="€ 0,00")
        self.kpi_salary = tk.StringVar(value="€ 0,00")
        self.kpi_monthly = tk.StringVar(value="€ 0,00")

        def kpi_card(parent, label, var):
            f = ttk.Labelframe(parent, text=label)
            f.pack(side="left", fill="x", expand=True, padx=6)
            ttk.Label(f, textvariable=var, font=("Segoe UI", 16, "bold")).pack(padx=10, pady=14, anchor="w")

        kpi_card(kpi_row, "Liquidità (Conti - Spese mensili conti)", self.kpi_cash)
        kpi_card(kpi_row, "Debiti (Carte)", self.kpi_debt)
        kpi_card(kpi_row, "Netto", self.kpi_net)
        kpi_card(kpi_row, "Stipendio mensile", self.kpi_salary)
        kpi_card(kpi_row, "Spese mensili (Conti + Carte)", self.kpi_monthly)

        bottom = ttk.Frame(wrap)
        bottom.pack(fill="both", expand=True)

        left = ttk.Labelframe(bottom, text="Conti (lordo / spese mensili / effettivo)")
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right = ttk.Labelframe(bottom, text="Carte")
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))

        self.tree_dash_accounts = ttk.Treeview(
            left,
            columns=("bank", "account", "gross", "monthly", "effective"),
            show="headings",
        )
        for c, t, w in [
            ("bank", "Banca", 170),
            ("account", "Conto", 170),
            ("gross", "Saldo lordo", 120),
            ("monthly", "Spese mensili", 130),
            ("effective", "Saldo effettivo", 130),
        ]:
            self.tree_dash_accounts.heading(c, text=t)
            self.tree_dash_accounts.column(c, width=w, anchor="w")
        self.tree_dash_accounts.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree_dash_cards = ttk.Treeview(right, columns=("name", "due"), show="headings")
        self.tree_dash_cards.heading("name", text="Carta")
        self.tree_dash_cards.heading("due", text="Saldo da pagare")
        self.tree_dash_cards.column("name", width=320, anchor="w")
        self.tree_dash_cards.column("due", width=160, anchor="w")
        self.tree_dash_cards.pack(fill="both", expand=True, padx=8, pady=8)

    # ----------------------------
    # Category bar
    # ----------------------------
    def _category_bar(self, parent, on_changed_callback):
        bar = ttk.Frame(parent)
        bar.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 6))
        bar.columnconfigure(1, weight=1)

        ttk.Label(bar, text="Nuova categoria").grid(row=0, column=0, sticky="w")
        ent_new = ttk.Entry(bar)
        ent_new.grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(
            bar, text="➕ Aggiungi",
            command=lambda e=ent_new: self.add_category(e, on_changed_callback)
        ).grid(row=0, column=2, sticky="ew")

        ttk.Label(bar, text="Elimina categoria").grid(row=1, column=0, sticky="w", pady=(8, 0))
        cmb_del = ttk.Combobox(bar, state="readonly", values=self.categories)
        cmb_del.grid(row=1, column=1, sticky="ew", padx=8, pady=(8, 0))
        ttk.Button(
            bar, text="🗑️ Elimina",
            command=lambda c=cmb_del: self.delete_category(c.get(), on_changed_callback)
        ).grid(row=1, column=2, sticky="ew", pady=(8, 0))

        self._delete_category_combos.append(cmb_del)
        if self.categories:
            cmb_del.set(self.categories[0])

        ent_new.bind("<Return>", lambda _e: self.add_category(ent_new, on_changed_callback))
        return bar

    def add_category(self, entry_widget: ttk.Entry, on_changed_callback):
        raw = entry_widget.get().strip()
        if not raw:
            messagebox.showwarning(APP_NAME, "Scrivi il nome della categoria.")
            return
        name = " ".join(raw.split())
        if name.lower() in [c.lower() for c in self.categories]:
            messagebox.showinfo(APP_NAME, "Categoria già presente.")
            return
        self.categories.append(name)
        self._normalize_categories_order()
        entry_widget.delete(0, tk.END)
        self.set_status(f"Categoria aggiunta: {name}")
        on_changed_callback()
        self.save_state()

    def delete_category(self, category_name: str, on_changed_callback):
        cat = (category_name or "").strip()
        if not cat:
            messagebox.showwarning(APP_NAME, "Seleziona una categoria da eliminare.")
            return
        if cat not in self.categories:
            messagebox.showwarning(APP_NAME, "Categoria non trovata.")
            return
        if len(self.categories) <= 1:
            messagebox.showwarning(APP_NAME, "Non puoi eliminare l’ultima categoria rimasta.")
            return

        used_in = []
        for acc_id, acc in self.accounts.items():
            if any(e.category == cat for e in acc.fixed_expenses):
                used_in.append(f"Conto {acc_id} ({acc.bank_name}/{acc.account_name})")
        for card_id, card in self.cards.items():
            if any(e.category == cat for e in card.fixed_expenses):
                used_in.append(f"Carta {card_id} ({card.card_name})")

        if used_in:
            messagebox.showwarning(
                APP_NAME,
                "Non puoi eliminare questa categoria perché è usata in:\n\n- "
                + "\n- ".join(used_in)
                + "\n\nPrima sposta quelle spese su un’altra categoria."
            )
            return

        if not messagebox.askyesno(APP_NAME, f"Eliminare la categoria '{cat}'?"):
            return

        self.categories = [c for c in self.categories if c != cat]
        self._normalize_categories_order()
        self.set_status(f"Categoria eliminata: {cat}")
        on_changed_callback()
        self.save_state()

    def _normalize_categories_order(self):
        lower_map = {c.lower(): c for c in self.categories}
        base_exact: List[str] = []
        for d in DEFAULT_CATEGORIES:
            if d.lower() in lower_map:
                base_exact.append(lower_map[d.lower()])
        rest = [c for c in self.categories if c.lower() not in {b.lower() for b in base_exact}]
        self.categories = base_exact + sorted(rest, key=lambda x: x.lower())

    def _refresh_category_sources(self):
        if hasattr(self, "cmb_acc_exp_cat"):
            self.cmb_acc_exp_cat.configure(values=self.categories)
            if self.categories and self.cmb_acc_exp_cat.get() not in self.categories:
                self.cmb_acc_exp_cat.set(self.categories[0])

        if hasattr(self, "cmb_card_exp_cat"):
            self.cmb_card_exp_cat.configure(values=self.categories)
            if self.categories and self.cmb_card_exp_cat.get() not in self.categories:
                self.cmb_card_exp_cat.set(self.categories[0])

        for cmb in getattr(self, "_delete_category_combos", []):
            try:
                cur = cmb.get()
                cmb.configure(values=self.categories)
                if self.categories:
                    if cur not in self.categories:
                        cmb.set(self.categories[0])
                else:
                    cmb.set("")
            except tk.TclError:
                pass

    # ----------------------------
    # Selection helpers
    # ----------------------------
    def _get_selected_account_id(self) -> Optional[str]:
        sel = self.tree_accounts.selection() if hasattr(self, "tree_accounts") else ()
        if sel:
            return sel[0]
        focus = self.tree_accounts.focus() if hasattr(self, "tree_accounts") else ""
        if focus:
            return focus
        return self.selected_account_id

    def _get_selected_card_id(self) -> Optional[str]:
        sel = self.tree_cards.selection() if hasattr(self, "tree_cards") else ()
        if sel:
            return sel[0]
        focus = self.tree_cards.focus() if hasattr(self, "tree_cards") else ""
        if focus:
            return focus
        return self.selected_card_id

    # ----------------------------
    # Accounts tab
    # ----------------------------
    def _build_accounts_tab(self):
        wrap = ttk.Frame(self.tab_accounts)
        wrap.pack(fill="both", expand=True, padx=12, pady=12)

        left = ttk.Labelframe(wrap, text="Elenco conti (saldo effettivo)")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # ✅ Pannello destro scrollabile: qui non sparisce più nulla
        right_outer = ttk.Labelframe(wrap, text="Gestione conto selezionato")
        right_outer.pack(side="left", fill="both", expand=True, padx=(8, 0))

        right_scroll = ScrollableFrame(right_outer)
        right_scroll.pack(fill="both", expand=True)
        right = right_scroll.inner

        # left tree
        self.tree_accounts = ttk.Treeview(
            left,
            columns=("bank", "account", "gross", "monthly", "effective"),
            show="headings",
            selectmode="browse",
        )
        for c, t, w in [
            ("bank", "Banca", 160),
            ("account", "Conto", 170),
            ("gross", "Lordo", 110),
            ("monthly", "Spese", 110),
            ("effective", "Effettivo", 120),
        ]:
            self.tree_accounts.heading(c, text=t)
            self.tree_accounts.column(c, width=w, anchor="w")
        self.tree_accounts.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree_accounts.bind("<<TreeviewSelect>>", self._on_account_select)

        form = ttk.Frame(left)
        form.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Label(form, text="Banca").grid(row=0, column=0, sticky="w")
        ttk.Label(form, text="Nome conto").grid(row=0, column=1, sticky="w")
        ttk.Label(form, text="Saldo lordo").grid(row=0, column=2, sticky="w")
        self.ent_bank = ttk.Entry(form)
        self.ent_account = ttk.Entry(form)
        self.ent_balance = ttk.Entry(form)
        self.ent_bank.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        self.ent_account.grid(row=1, column=1, sticky="ew", padx=(0, 6))
        self.ent_balance.grid(row=1, column=2, sticky="ew")
        form.columnconfigure(0, weight=2)
        form.columnconfigure(1, weight=2)
        form.columnconfigure(2, weight=1)

        btns = ttk.Frame(left)
        btns.pack(fill="x", padx=8, pady=(0, 10))
        ttk.Button(btns, text="➕ Aggiungi conto", command=self.add_account).pack(side="left")
        ttk.Button(btns, text="🗑️ Elimina selezionato", command=self.delete_selected_account).pack(side="left", padx=8)

        # right content
        self.lbl_acc_title = ttk.Label(right, text="Seleziona un conto a sinistra.", font=("Segoe UI", 12, "bold"))
        self.lbl_acc_title.pack(anchor="w", padx=10, pady=(10, 6))
        self.lbl_acc_summary = ttk.Label(right, text="", foreground="#9aa4b2")
        self.lbl_acc_summary.pack(anchor="w", padx=10, pady=(0, 10))

        bal_frame = ttk.Frame(right)
        bal_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Label(bal_frame, text="Aggiorna saldo lordo:").pack(side="left")
        self.ent_update_acc_balance = ttk.Entry(bal_frame, width=14)
        self.ent_update_acc_balance.pack(side="left", padx=8)
        ttk.Button(bal_frame, text="✔ Aggiorna", command=self.update_account_balance).pack(side="left")

        exp_frame = ttk.Labelframe(right, text="Spese mensili del conto (es: SDD)")
        exp_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # ✅ Grid layout dentro exp_frame: pulsanti NON vengono spinti fuori
        exp_frame.columnconfigure(0, weight=1)
        exp_frame.rowconfigure(1, weight=1)  # tree row elastica

        self._category_bar(exp_frame, self._refresh_category_sources)

        self.tree_acc_exp = ttk.Treeview(
            exp_frame,
            columns=("name", "category", "amount", "notes"),
            show="headings",
            selectmode="browse",
            height=10
        )
        for c, t, w in [
            ("name", "Voce", 200),
            ("category", "Categoria", 210),
            ("amount", "Importo", 110),
            ("notes", "Note", 260),
        ]:
            self.tree_acc_exp.heading(c, text=t)
            self.tree_acc_exp.column(c, width=w, anchor="w")

        # scrollbar tree spese conto
        acc_exp_scroll = ttk.Scrollbar(exp_frame, orient="vertical", command=self.tree_acc_exp.yview)
        self.tree_acc_exp.configure(yscrollcommand=acc_exp_scroll.set)

        self.tree_acc_exp.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=(0, 6))
        acc_exp_scroll.grid(row=1, column=1, sticky="ns", pady=(0, 6))

        # ✅ pulsanti sempre visibili
        exp_btns = ttk.Frame(exp_frame)
        exp_btns.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        ttk.Button(exp_btns, text="➕ Aggiungi spesa mensile", command=self.add_account_expense).pack(side="left")
        ttk.Button(exp_btns, text="🗑️ Rimuovi spesa selezionata", command=self.delete_selected_account_expense).pack(side="left", padx=8)

        exp_form = ttk.Frame(exp_frame)
        exp_form.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 10))
        exp_form.columnconfigure(0, weight=2)
        exp_form.columnconfigure(1, weight=2)
        exp_form.columnconfigure(2, weight=1)
        exp_form.columnconfigure(3, weight=3)

        ttk.Label(exp_form, text="Voce").grid(row=0, column=0, sticky="w")
        ttk.Label(exp_form, text="Categoria").grid(row=0, column=1, sticky="w")
        ttk.Label(exp_form, text="Importo").grid(row=0, column=2, sticky="w")
        ttk.Label(exp_form, text="Note").grid(row=0, column=3, sticky="w")

        self.ent_acc_exp_name = ttk.Entry(exp_form)
        self.cmb_acc_exp_cat = ttk.Combobox(exp_form, state="readonly", values=self.categories)
        self.ent_acc_exp_amount = ttk.Entry(exp_form, width=10)
        self.ent_acc_exp_notes = ttk.Entry(exp_form)

        self.ent_acc_exp_name.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        self.cmb_acc_exp_cat.grid(row=1, column=1, sticky="ew", padx=(0, 6))
        self.ent_acc_exp_amount.grid(row=1, column=2, sticky="ew", padx=(0, 6))
        self.ent_acc_exp_notes.grid(row=1, column=3, sticky="ew")

        if self.categories:
            self.cmb_acc_exp_cat.set(self.categories[0])

    # ----------------------------
    # Cards tab
    # ----------------------------
    def _build_cards_tab(self):
        wrap = ttk.Frame(self.tab_cards)
        wrap.pack(fill="both", expand=True, padx=12, pady=12)

        left = ttk.Labelframe(wrap, text="Elenco carte")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # ✅ pannello destro scrollabile
        right_outer = ttk.Labelframe(wrap, text="Gestione carta selezionata")
        right_outer.pack(side="left", fill="both", expand=True, padx=(8, 0))

        right_scroll = ScrollableFrame(right_outer)
        right_scroll.pack(fill="both", expand=True)
        right = right_scroll.inner

        self.tree_cards = ttk.Treeview(left, columns=("name", "due"), show="headings", selectmode="browse")
        self.tree_cards.heading("name", text="Carta")
        self.tree_cards.heading("due", text="Saldo da pagare")
        self.tree_cards.column("name", width=320, anchor="w")
        self.tree_cards.column("due", width=140, anchor="w")
        self.tree_cards.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree_cards.bind("<<TreeviewSelect>>", self._on_card_select)

        form = ttk.Frame(left)
        form.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Label(form, text="Nome carta").grid(row=0, column=0, sticky="w")
        ttk.Label(form, text="Saldo da pagare").grid(row=0, column=1, sticky="w")
        self.ent_card_name = ttk.Entry(form)
        self.ent_card_due = ttk.Entry(form)
        self.ent_card_name.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        self.ent_card_due.grid(row=1, column=1, sticky="ew")
        form.columnconfigure(0, weight=3)
        form.columnconfigure(1, weight=1)

        btns = ttk.Frame(left)
        btns.pack(fill="x", padx=8, pady=(0, 10))
        ttk.Button(btns, text="➕ Aggiungi carta", command=self.add_card).pack(side="left")
        ttk.Button(btns, text="🗑️ Elimina selezionata", command=self.delete_selected_card).pack(side="left", padx=8)

        self.lbl_card_title = ttk.Label(right, text="Seleziona una carta a sinistra.", font=("Segoe UI", 12, "bold"))
        self.lbl_card_title.pack(anchor="w", padx=10, pady=(10, 6))

        due_frame = ttk.Frame(right)
        due_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Label(due_frame, text="Aggiorna saldo da pagare:").pack(side="left")
        self.ent_update_card_due = ttk.Entry(due_frame, width=14)
        self.ent_update_card_due.pack(side="left", padx=8)
        ttk.Button(due_frame, text="✔ Aggiorna", command=self.update_card_due).pack(side="left")

        exp_frame = ttk.Labelframe(right, text="Spese mensili della carta (mappate)")
        exp_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        exp_frame.columnconfigure(0, weight=1)
        exp_frame.rowconfigure(1, weight=1)

        self._category_bar(exp_frame, self._refresh_category_sources)

        self.tree_card_exp = ttk.Treeview(
            exp_frame,
            columns=("name", "category", "amount", "notes"),
            show="headings",
            selectmode="browse",
            height=10
        )
        for c, t, w in [
            ("name", "Voce", 200),
            ("category", "Categoria", 210),
            ("amount", "Importo", 110),
            ("notes", "Note", 260),
        ]:
            self.tree_card_exp.heading(c, text=t)
            self.tree_card_exp.column(c, width=w, anchor="w")

        card_exp_scroll = ttk.Scrollbar(exp_frame, orient="vertical", command=self.tree_card_exp.yview)
        self.tree_card_exp.configure(yscrollcommand=card_exp_scroll.set)

        self.tree_card_exp.grid(row=1, column=0, sticky="nsew", padx=(8, 0), pady=(0, 6))
        card_exp_scroll.grid(row=1, column=1, sticky="ns", pady=(0, 6))

        exp_btns = ttk.Frame(exp_frame)
        exp_btns.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        ttk.Button(exp_btns, text="➕ Aggiungi spesa mensile", command=self.add_card_expense).pack(side="left")
        ttk.Button(exp_btns, text="🗑️ Rimuovi spesa selezionata", command=self.delete_selected_card_expense).pack(side="left", padx=8)

        exp_form = ttk.Frame(exp_frame)
        exp_form.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 10))
        exp_form.columnconfigure(0, weight=2)
        exp_form.columnconfigure(1, weight=2)
        exp_form.columnconfigure(2, weight=1)
        exp_form.columnconfigure(3, weight=3)

        ttk.Label(exp_form, text="Voce").grid(row=0, column=0, sticky="w")
        ttk.Label(exp_form, text="Categoria").grid(row=0, column=1, sticky="w")
        ttk.Label(exp_form, text="Importo").grid(row=0, column=2, sticky="w")
        ttk.Label(exp_form, text="Note").grid(row=0, column=3, sticky="w")

        self.ent_card_exp_name = ttk.Entry(exp_form)
        self.cmb_card_exp_cat = ttk.Combobox(exp_form, state="readonly", values=self.categories)
        self.ent_card_exp_amount = ttk.Entry(exp_form, width=10)
        self.ent_card_exp_notes = ttk.Entry(exp_form)

        self.ent_card_exp_name.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        self.cmb_card_exp_cat.grid(row=1, column=1, sticky="ew", padx=(0, 6))
        self.ent_card_exp_amount.grid(row=1, column=2, sticky="ew", padx=(0, 6))
        self.ent_card_exp_notes.grid(row=1, column=3, sticky="ew")

        if self.categories:
            self.cmb_card_exp_cat.set(self.categories[0])

    # ----------------------------
    # Income tab
    # ----------------------------
    def _build_income_tab(self):
        wrap = ttk.Frame(self.tab_income)
        wrap.pack(fill="both", expand=True, padx=12, pady=12)

        box = ttk.Labelframe(wrap, text="Stipendio mensile")
        box.pack(fill="x", padx=6, pady=6)

        row = ttk.Frame(box)
        row.pack(fill="x", padx=10, pady=10)

        ttk.Label(row, text="Importo stipendio mensile (€)").grid(row=0, column=0, sticky="w")
        ttk.Label(row, text="Accredita su conto").grid(row=0, column=1, sticky="w")

        self.ent_salary = ttk.Entry(row)
        self.cmb_salary_account = ttk.Combobox(row, state="readonly", values=[])
        self.ent_salary.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self.cmb_salary_account.grid(row=1, column=1, sticky="ew")

        row.columnconfigure(0, weight=1)
        row.columnconfigure(1, weight=2)

        btns = ttk.Frame(box)
        btns.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btns, text="✔ Salva stipendio mensile", command=self.save_income).pack(side="left")

    # ----------------------------
    # Helpers
    # ----------------------------
    def _fmt_eur(self, x: float) -> str:
        return f"€ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _safe_float(self, s: str) -> Optional[float]:
        if s is None:
            return None
        s = s.strip().replace("€", "").replace(" ", "")
        s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None

    def _make_id(self, prefix: str, existing: Dict[str, object]) -> str:
        i = 1
        while True:
            candidate = f"{prefix}{i:04d}"
            if candidate not in existing:
                return candidate
            i += 1

    def set_status(self, text: str):
        self.status_var.set(text)

    def _format_saved_label(self):
        if not self.last_saved_at:
            return "Ultimo salvataggio: —"
        try:
            dt = datetime.fromisoformat(self.last_saved_at)
            return "Ultimo salvataggio: " + dt.strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            return f"Ultimo salvataggio: {self.last_saved_at}"

    # ----------------------------
    # CRUD: Accounts / Cards / Income
    # ----------------------------
    def add_account(self):
        bank = self.ent_bank.get().strip()
        name = self.ent_account.get().strip()
        bal = self._safe_float(self.ent_balance.get())
        if not bank or not name or bal is None:
            messagebox.showwarning(APP_NAME, "Inserisci Banca, Nome conto e un Saldo lordo valido.")
            return
        acc_id = self._make_id("ACC", self.accounts)
        self.accounts[acc_id] = BankAccount(bank, name, bal, fixed_expenses=[])
        self.ent_bank.delete(0, tk.END)
        self.ent_account.delete(0, tk.END)
        self.ent_balance.delete(0, tk.END)
        self.selected_account_id = acc_id
        self.set_status("Conto aggiunto.")
        self._refresh_all()
        self._select_account_in_tree(acc_id)
        self.save_state()

    def delete_selected_account(self):
        acc_id = self._get_selected_account_id()
        if not acc_id or acc_id not in self.accounts:
            messagebox.showwarning(APP_NAME, "Seleziona un conto da eliminare.")
            return
        if messagebox.askyesno(APP_NAME, "Eliminare il conto selezionato?"):
            del self.accounts[acc_id]
            if self.selected_account_id == acc_id:
                self.selected_account_id = None
            if self.income.salary_account_id == acc_id:
                self.income.salary_account_id = None
            self.set_status("Conto eliminato.")
            self._refresh_all()
            self.save_state()

    def update_account_balance(self):
        acc_id = self._get_selected_account_id()
        if not acc_id or acc_id not in self.accounts:
            messagebox.showwarning(APP_NAME, "Seleziona un conto.")
            return
        new_bal = self._safe_float(self.ent_update_acc_balance.get())
        if new_bal is None:
            messagebox.showwarning(APP_NAME, "Inserisci un saldo lordo valido.")
            return
        self.accounts[acc_id].balance = new_bal
        self.ent_update_acc_balance.delete(0, tk.END)
        self.set_status("Saldo lordo aggiornato.")
        self._refresh_all()
        self._select_account_in_tree(acc_id)
        self.save_state()

    def add_account_expense(self):
        acc_id = self._get_selected_account_id()
        if not acc_id or acc_id not in self.accounts:
            messagebox.showwarning(APP_NAME, "Seleziona prima un conto (clicca una riga).")
            return
        name = self.ent_acc_exp_name.get().strip()
        category = self.cmb_acc_exp_cat.get().strip()
        amount = self._safe_float(self.ent_acc_exp_amount.get())
        notes = self.ent_acc_exp_notes.get().strip()
        if not name or not category or amount is None:
            messagebox.showwarning(APP_NAME, "Inserisci Voce, Categoria e Importo valido.")
            return
        self.accounts[acc_id].fixed_expenses.append(FixedExpense(name, category, amount, notes))
        self.ent_acc_exp_name.delete(0, tk.END)
        self.ent_acc_exp_amount.delete(0, tk.END)
        self.ent_acc_exp_notes.delete(0, tk.END)
        self.set_status("Spesa conto aggiunta.")
        self._refresh_all()
        self._select_account_in_tree(acc_id)
        self.save_state()

    def delete_selected_account_expense(self):
        acc_id = self._get_selected_account_id()
        if not acc_id or acc_id not in self.accounts:
            messagebox.showwarning(APP_NAME, "Seleziona un conto.")
            return
        sel = self.tree_acc_exp.selection()
        if not sel:
            messagebox.showwarning(APP_NAME, "Seleziona una spesa da rimuovere.")
            return
        idx = int(sel[0].replace("EXP", ""))
        exps = self.accounts[acc_id].fixed_expenses
        if 0 <= idx < len(exps) and messagebox.askyesno(APP_NAME, "Rimuovere la spesa selezionata?"):
            exps.pop(idx)
            self.set_status("Spesa conto rimossa.")
            self._refresh_all()
            self._select_account_in_tree(acc_id)
            self.save_state()

    def add_card(self):
        name = self.ent_card_name.get().strip()
        due = self._safe_float(self.ent_card_due.get())
        if not name or due is None:
            messagebox.showwarning(APP_NAME, "Inserisci Nome carta e un Saldo da pagare valido.")
            return
        card_id = self._make_id("CRD", self.cards)
        self.cards[card_id] = CreditCard(name, due, fixed_expenses=[])
        self.ent_card_name.delete(0, tk.END)
        self.ent_card_due.delete(0, tk.END)
        self.selected_card_id = card_id
        self.set_status("Carta aggiunta.")
        self._refresh_all()
        self._select_card_in_tree(card_id)
        self.save_state()

    def delete_selected_card(self):
        card_id = self._get_selected_card_id()
        if not card_id or card_id not in self.cards:
            messagebox.showwarning(APP_NAME, "Seleziona una carta da eliminare.")
            return
        if messagebox.askyesno(APP_NAME, "Eliminare la carta selezionata?"):
            del self.cards[card_id]
            if self.selected_card_id == card_id:
                self.selected_card_id = None
            self.set_status("Carta eliminata.")
            self._refresh_all()
            self.save_state()

    def update_card_due(self):
        card_id = self._get_selected_card_id()
        if not card_id or card_id not in self.cards:
            messagebox.showwarning(APP_NAME, "Seleziona una carta.")
            return
        new_due = self._safe_float(self.ent_update_card_due.get())
        if new_due is None:
            messagebox.showwarning(APP_NAME, "Inserisci un saldo valido.")
            return
        self.cards[card_id].due_balance = new_due
        self.ent_update_card_due.delete(0, tk.END)
        self.set_status("Saldo carta aggiornato.")
        self._refresh_all()
        self._select_card_in_tree(card_id)
        self.save_state()

    def add_card_expense(self):
        card_id = self._get_selected_card_id()
        if not card_id or card_id not in self.cards:
            messagebox.showwarning(APP_NAME, "Seleziona prima una carta (clicca una riga).")
            return
        name = self.ent_card_exp_name.get().strip()
        category = self.cmb_card_exp_cat.get().strip()
        amount = self._safe_float(self.ent_card_exp_amount.get())
        notes = self.ent_card_exp_notes.get().strip()
        if not name or not category or amount is None:
            messagebox.showwarning(APP_NAME, "Inserisci Voce, Categoria e Importo valido.")
            return
        self.cards[card_id].fixed_expenses.append(FixedExpense(name, category, amount, notes))
        self.ent_card_exp_name.delete(0, tk.END)
        self.ent_card_exp_amount.delete(0, tk.END)
        self.ent_card_exp_notes.delete(0, tk.END)
        self.set_status("Spesa carta aggiunta.")
        self._refresh_all()
        self._select_card_in_tree(card_id)
        self.save_state()

    def delete_selected_card_expense(self):
        card_id = self._get_selected_card_id()
        if not card_id or card_id not in self.cards:
            messagebox.showwarning(APP_NAME, "Seleziona una carta.")
            return
        sel = self.tree_card_exp.selection()
        if not sel:
            messagebox.showwarning(APP_NAME, "Seleziona una spesa da rimuovere.")
            return
        idx = int(sel[0].replace("EXP", ""))
        exps = self.cards[card_id].fixed_expenses
        if 0 <= idx < len(exps) and messagebox.askyesno(APP_NAME, "Rimuovere la spesa selezionata?"):
            exps.pop(idx)
            self.set_status("Spesa carta rimossa.")
            self._refresh_all()
            self._select_card_in_tree(card_id)
            self.save_state()

    def save_income(self):
        sal = self._safe_float(self.ent_salary.get())
        if sal is None:
            messagebox.showwarning(APP_NAME, "Inserisci un importo stipendio valido.")
            return
        selected = self.cmb_salary_account.get().strip()
        acc_id = None
        if selected:
            acc_id = selected.split(" — ")[0].strip()
            if acc_id not in self.accounts:
                acc_id = None
        self.income.salary_amount = sal
        self.income.salary_account_id = acc_id
        self.set_status("Stipendio mensile salvato.")
        self._refresh_all()
        self.save_state()

    # ----------------------------
    # Tree selection / refresh
    # ----------------------------
    def _select_account_in_tree(self, acc_id: str):
        try:
            if self.tree_accounts.exists(acc_id):
                self.tree_accounts.selection_set(acc_id)
                self.tree_accounts.focus(acc_id)
                self.tree_accounts.see(acc_id)
        except Exception:
            pass

    def _select_card_in_tree(self, card_id: str):
        try:
            if self.tree_cards.exists(card_id):
                self.tree_cards.selection_set(card_id)
                self.tree_cards.focus(card_id)
                self.tree_cards.see(card_id)
        except Exception:
            pass

    def _on_account_select(self, _evt=None):
        self.selected_account_id = self._get_selected_account_id()
        self._refresh_account_panel()

    def _on_card_select(self, _evt=None):
        self.selected_card_id = self._get_selected_card_id()
        self._refresh_card_panel()

    def _refresh_all(self):
        self._refresh_accounts_tree()
        self._refresh_cards_tree()
        self._refresh_dashboard()
        self._refresh_account_panel()
        self._refresh_card_panel()
        self._refresh_income_combo()
        self._refresh_category_sources()

    def _refresh_accounts_tree(self):
        for i in self.tree_accounts.get_children():
            self.tree_accounts.delete(i)
        for acc_id, a in self.accounts.items():
            monthly = self.account_monthly_expenses(a)
            eff = self.account_effective_balance(a)
            self.tree_accounts.insert(
                "", "end", iid=acc_id,
                values=(a.bank_name, a.account_name, self._fmt_eur(a.balance), self._fmt_eur(monthly), self._fmt_eur(eff))
            )
        if self.selected_account_id:
            self._select_account_in_tree(self.selected_account_id)

    def _refresh_cards_tree(self):
        for i in self.tree_cards.get_children():
            self.tree_cards.delete(i)
        for card_id, c in self.cards.items():
            self.tree_cards.insert("", "end", iid=card_id, values=(c.card_name, self._fmt_eur(c.due_balance)))
        if self.selected_card_id:
            self._select_card_in_tree(self.selected_card_id)

    def _refresh_dashboard(self):
        total_monthly = self.total_monthly_expenses()
        cash_effective = sum(self.account_effective_balance(a) for a in self.accounts.values())
        debt = sum(c.due_balance for c in self.cards.values())
        net = cash_effective - debt

        self.kpi_cash.set(self._fmt_eur(cash_effective))
        self.kpi_debt.set(self._fmt_eur(debt))
        self.kpi_net.set(self._fmt_eur(net))
        self.kpi_salary.set(self._fmt_eur(self.income.salary_amount))
        self.kpi_monthly.set(self._fmt_eur(total_monthly))
        self.last_saved_var.set(self._format_saved_label())

        for t in [self.tree_dash_accounts, self.tree_dash_cards]:
            for i in t.get_children():
                t.delete(i)

        for a in self.accounts.values():
            monthly = self.account_monthly_expenses(a)
            eff = self.account_effective_balance(a)
            self.tree_dash_accounts.insert(
                "", "end",
                values=(a.bank_name, a.account_name, self._fmt_eur(a.balance), self._fmt_eur(monthly), self._fmt_eur(eff))
            )

        for c in self.cards.values():
            self.tree_dash_cards.insert("", "end", values=(c.card_name, self._fmt_eur(c.due_balance)))

    def _refresh_account_panel(self):
        acc_id = self._get_selected_account_id()
        if not acc_id or acc_id not in self.accounts:
            self.lbl_acc_title.configure(text="Seleziona un conto a sinistra.")
            self.lbl_acc_summary.configure(text="")
            for i in self.tree_acc_exp.get_children():
                self.tree_acc_exp.delete(i)
            return

        a = self.accounts[acc_id]
        monthly = self.account_monthly_expenses(a)
        eff = self.account_effective_balance(a)
        self.lbl_acc_title.configure(text=f"{acc_id} — {a.bank_name} / {a.account_name}")
        self.lbl_acc_summary.configure(
            text=f"Saldo lordo: {self._fmt_eur(a.balance)}   |   Spese mensili: {self._fmt_eur(monthly)}   |   Saldo effettivo: {self._fmt_eur(eff)}"
        )
        for i in self.tree_acc_exp.get_children():
            self.tree_acc_exp.delete(i)
        for idx, exp in enumerate(a.fixed_expenses):
            self.tree_acc_exp.insert("", "end", iid=f"EXP{idx}", values=(exp.name, exp.category, self._fmt_eur(exp.amount), exp.notes or ""))

    def _refresh_card_panel(self):
        card_id = self._get_selected_card_id()
        if not card_id or card_id not in self.cards:
            self.lbl_card_title.configure(text="Seleziona una carta a sinistra.")
            for i in self.tree_card_exp.get_children():
                self.tree_card_exp.delete(i)
            return

        c = self.cards[card_id]
        self.lbl_card_title.configure(text=f"{card_id} — {c.card_name}")
        for i in self.tree_card_exp.get_children():
            self.tree_card_exp.delete(i)
        for idx, exp in enumerate(c.fixed_expenses):
            self.tree_card_exp.insert("", "end", iid=f"EXP{idx}", values=(exp.name, exp.category, self._fmt_eur(exp.amount), exp.notes or ""))

    def _refresh_income_combo(self):
        items = [f"{acc_id} — {a.bank_name} / {a.account_name}" for acc_id, a in self.accounts.items()]
        self.cmb_salary_account.configure(values=items)

        if self.income.salary_account_id and self.income.salary_account_id in self.accounts:
            a = self.accounts[self.income.salary_account_id]
            self.cmb_salary_account.set(f"{self.income.salary_account_id} — {a.bank_name} / {a.account_name}")
        else:
            self.cmb_salary_account.set("")

        self.ent_salary.delete(0, tk.END)
        self.ent_salary.insert(0, f"{self.income.salary_amount:.2f}".replace(".", ","))

    # ----------------------------
    # Persistence
    # ----------------------------
    def _serialize(self) -> dict:
        return {
            "app": APP_NAME,
            "meta": {"last_saved_at": self.last_saved_at},
            "categories": self.categories,
            "accounts": {
                acc_id: {
                    "bank_name": a.bank_name,
                    "account_name": a.account_name,
                    "balance": a.balance,
                    "fixed_expenses": [asdict(e) for e in a.fixed_expenses],
                }
                for acc_id, a in self.accounts.items()
            },
            "cards": {
                card_id: {
                    "card_name": c.card_name,
                    "due_balance": c.due_balance,
                    "fixed_expenses": [asdict(e) for e in c.fixed_expenses],
                }
                for card_id, c in self.cards.items()
            },
            "income": asdict(self.income),
        }

    def _load_state(self):
        raw = self.storage.load()
        if not raw:
            return
        try:
            self.last_saved_at = raw.get("meta", {}).get("last_saved_at")

            loaded_cats = raw.get("categories")
            if isinstance(loaded_cats, list) and loaded_cats:
                self.categories = loaded_cats
            else:
                self.categories = list(DEFAULT_CATEGORIES)

            lower = [c.lower() for c in self.categories]
            for d in DEFAULT_CATEGORIES:
                if d.lower() not in lower:
                    self.categories.append(d)
            self._normalize_categories_order()

            self.accounts.clear()
            for acc_id, obj in raw.get("accounts", {}).items():
                exps = [FixedExpense(**e) for e in obj.get("fixed_expenses", [])]
                self.accounts[acc_id] = BankAccount(
                    bank_name=obj.get("bank_name", ""),
                    account_name=obj.get("account_name", ""),
                    balance=float(obj.get("balance", 0.0)),
                    fixed_expenses=exps,
                )

            self.cards.clear()
            for card_id, obj in raw.get("cards", {}).items():
                exps = [FixedExpense(**e) for e in obj.get("fixed_expenses", [])]
                self.cards[card_id] = CreditCard(
                    card_name=obj.get("card_name", ""),
                    due_balance=float(obj.get("due_balance", 0.0)),
                    fixed_expenses=exps,
                )

            inc = raw.get("income", {})
            self.income = Income(
                salary_amount=float(inc.get("salary_amount", 0.0)),
                salary_account_id=inc.get("salary_account_id"),
            )

            self.set_status("Dati caricati.")
        except Exception:
            messagebox.showwarning(APP_NAME, "Errore nel caricamento dati. Avvio vuoto.")
            self.accounts.clear()
            self.cards.clear()
            self.income = Income()
            self.categories = list(DEFAULT_CATEGORIES)
            self.last_saved_at = None

    def save_state(self):
        try:
            self.last_saved_at = datetime.now().isoformat(timespec="seconds")
            self.storage.save(self._serialize())
            self.set_status("Salvato.")
            self.last_saved_var.set(self._format_saved_label())
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Impossibile salvare i dati:\n{e}")

    def on_close(self):
        self.save_state()
        self.destroy()


if __name__ == "__main__":
    FinanceAdvisorBudgetingToolITA().mainloop()
