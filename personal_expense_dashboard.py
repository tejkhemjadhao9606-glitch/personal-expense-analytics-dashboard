import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import mysql.connector
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ---------------- DATABASE SETTINGS ----------------

DB = {
    "host": "localhost",
    "user": "root",
    "password": "tejas1741",
    "database": "personal_expense_db"
}


# ---------------- COLORS ----------------

NAVY = "#24476B"
BLUE = "#2878E8"
GREEN = "#2EAD59"
RED = "#F26470"
PURPLE = "#8257E5"
ORANGE = "#FF8A34"
BG = "#F3F7FC"
WHITE = "#FFFFFF"
TEXT = "#15365C"
BORDER = "#D7E4F5"


# ---------------- DATABASE ----------------

def connect_database():
    con = mysql.connector.connect(
        host=DB["host"],
        user=DB["user"],
        password=DB["password"]
    )

    cur = con.cursor()
    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS {DB['database']}"
    )
    cur.close()
    con.close()

    con = mysql.connector.connect(**DB)
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            expense_date DATE NOT NULL,
            category VARCHAR(50) NOT NULL,
            description VARCHAR(100),
            amount DECIMAL(10,2) NOT NULL,
            payment_mode VARCHAR(30) NOT NULL
        )
    """)

    con.commit()
    cur.close()
    con.close()


def query_db(sql, values=None, fetch=False):
    con = mysql.connector.connect(**DB)
    cur = con.cursor()

    try:
        cur.execute(sql, values or ())
        result = cur.fetchall() if fetch else None
        con.commit()
        return result
    finally:
        cur.close()
        con.close()


def money(amount):
    return f"₹ {float(amount or 0):,.2f}"


# ---------------- DASHBOARD ----------------

class ExpenseDashboard:

    def __init__(self, root):
        self.root = root
        self.root.title("Personal Expense Analytics Dashboard")
        self.root.configure(bg=BG)

        try:
            self.root.state("zoomed")
        except tk.TclError:
            self.root.geometry("1280x800")

        self.root.minsize(950, 600)
        self.chart_canvases = []

        self.setup_style()
        self.build_header()
        self.build_main()
        self.refresh_data()

    # ---------------- STYLE ----------------

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            font=("Segoe UI", 8),
            rowheight=23,
            background=WHITE,
            foreground=TEXT
        )

        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 8, "bold"),
            background="#E7F0FC",
            foreground=TEXT
        )

        style.configure("TCombobox", padding=2)

    # ---------------- HEADER ----------------

    def build_header(self):
        header = tk.Frame(self.root, bg=NAVY, height=75)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="◉  Personal Expense Analytics Dashboard",
            bg=NAVY,
            fg=WHITE,
            font=("Segoe UI", 19, "bold")
        ).pack(anchor="w", padx=18, pady=(8, 0))

        tk.Label(
            header,
            text="Track  •  Analyze  •  Plan Better",
            bg=NAVY,
            fg="#D8E7FA",
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=22)

        self.date_label = tk.Label(
            header,
            text="DATE RANGE",
            bg=NAVY,
            fg=WHITE,
            font=("Segoe UI", 9)
        )
        self.date_label.place(relx=0.98, rely=0.5, anchor="e")

    # ---------------- MAIN LAYOUT ----------------

    def build_main(self):
        self.body = tk.Frame(self.root, bg=BG)
        self.body.pack(fill="both", expand=True, padx=7, pady=7)

        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(0, minsize=180)
        self.body.grid_columnconfigure(1, weight=1)

        self.sidebar = tk.Frame(
            self.body,
            bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=8,
            pady=6
        )
        self.sidebar.grid(
            row=0, column=0, sticky="nsew", padx=(0, 5)
        )

        self.dashboard = tk.Frame(self.body, bg=BG)
        self.dashboard.grid(
            row=0, column=1, sticky="nsew", padx=(5, 0)
        )

        # Three dashboard rows: KPIs, charts, table/insights
        self.dashboard.grid_rowconfigure(0, weight=1)
        self.dashboard.grid_rowconfigure(1, weight=4)
        self.dashboard.grid_rowconfigure(2, weight=2)
        self.dashboard.grid_columnconfigure(0, weight=1)

        self.build_sidebar()
        self.build_dashboard()

    def button(self, parent, text, color, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=WHITE,
            activebackground=color,
            activeforeground=WHITE,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 8, "bold"),
            pady=5
        )

    def entry(self, parent, label, default=""):
        tk.Label(
            parent,
            text=label,
            bg=WHITE,
            fg=TEXT,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", pady=(4, 1))

        item = tk.Entry(
            parent,
            font=("Segoe UI", 9),
            relief="solid",
            bd=1
        )
        item.pack(fill="x", ipady=2)

        if default:
            item.insert(0, default)

        return item

    # ---------------- SIDEBAR ----------------

    def build_sidebar(self):
        s = self.sidebar

        tk.Label(
            s, text="▦  FILTERS",
            bg=WHITE, fg=TEXT,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(s, text="Month", bg=WHITE, fg=TEXT).pack(anchor="w")

        self.month = tk.StringVar(value="All Months")
        self.month_box = ttk.Combobox(
            s, textvariable=self.month,
            values=["All Months"], state="readonly"
        )
        self.month_box.pack(fill="x", pady=(1, 4))
        self.month_box.bind(
            "<<ComboboxSelected>>",
            lambda event: self.refresh_data()
        )

        tk.Label(s, text="Category", bg=WHITE, fg=TEXT).pack(anchor="w")

        self.category = tk.StringVar(value="All")
        self.category_box = ttk.Combobox(
            s, textvariable=self.category,
            values=["All"], state="readonly"
        )
        self.category_box.pack(fill="x", pady=(1, 4))
        self.category_box.bind(
            "<<ComboboxSelected>>",
            lambda event: self.refresh_data()
        )

        tk.Label(
            s, text="Payment Mode", bg=WHITE, fg=TEXT
        ).pack(anchor="w")

        self.payment = tk.StringVar(value="All")
        self.payment_box = ttk.Combobox(
            s, textvariable=self.payment,
            values=["All"], state="readonly"
        )
        self.payment_box.pack(fill="x", pady=(1, 4))
        self.payment_box.bind(
            "<<ComboboxSelected>>",
            lambda event: self.refresh_data()
        )

        self.button(
            s, "↻ Reset Filters", NAVY, self.reset_filters
        ).pack(fill="x", pady=3)

        ttk.Separator(s).pack(fill="x", pady=5)

        tk.Label(
            s, text="MANAGE EXPENSES",
            bg=WHITE, fg=TEXT,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=3)

        self.button(
            s, "+ Add Expense", GREEN, self.add_expense
        ).pack(fill="x", pady=2)

        self.button(
            s, "Update Selected", BLUE, self.update_expense
        ).pack(fill="x", pady=2)

        self.button(
            s, "Delete Selected", RED, self.delete_expense
        ).pack(fill="x", pady=2)

        self.button(
            s, "Refresh Data", PURPLE, self.refresh_data
        ).pack(fill="x", pady=2)

        ttk.Separator(s).pack(fill="x", pady=5)

        tk.Label(
            s, text="ADD / EDIT EXPENSE",
            bg=WHITE, fg=TEXT,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=2)

        self.date_entry = self.entry(
            s, "Date (YYYY-MM-DD)",
            datetime.today().strftime("%Y-%m-%d")
        )

        self.category_entry = self.entry(s, "Category")
        self.description_entry = self.entry(s, "Description")
        self.amount_entry = self.entry(s, "Amount (₹)")

        tk.Label(
            s, text="Payment Mode",
            bg=WHITE, fg=TEXT
        ).pack(anchor="w", pady=(4, 1))

        self.payment_entry = tk.StringVar(value="Cash")

        ttk.Combobox(
            s,
            textvariable=self.payment_entry,
            values=["Cash", "UPI", "Card", "Net Banking", "Other"],
            state="readonly"
        ).pack(fill="x")

        self.button(
            s, "Clear Form", "#6B7F95", self.clear_form
        ).pack(fill="x", pady=4)

    # ---------------- DASHBOARD CONTENT ----------------

    def build_dashboard(self):
        d = self.dashboard

        # KPI cards
        self.kpi_frame = tk.Frame(d, bg=BG)
        self.kpi_frame.grid(row=0, column=0, sticky="nsew")

        for i in range(4):
            self.kpi_frame.grid_columnconfigure(
                i, weight=1, uniform="cards"
            )

        self.kpis = []

        cards = [
            ("TOTAL EXPENSES", BLUE),
            ("AVERAGE / TRANSACTION", GREEN),
            ("HIGHEST EXPENSE", RED),
            ("TOP CATEGORY", PURPLE)
        ]

        for i, (title, color) in enumerate(cards):
            card = tk.Frame(
                self.kpi_frame,
                bg=WHITE,
                highlightbackground=BORDER,
                highlightthickness=1,
                padx=7, pady=5
            )
            card.grid(
                row=0, column=i,
                sticky="nsew", padx=3, pady=2
            )

            tk.Label(
                card, text=title,
                bg=WHITE, fg=TEXT,
                font=("Segoe UI", 8, "bold")
            ).pack(anchor="w")

            value = tk.Label(
                card, text="₹ 0.00",
                bg=WHITE, fg=color,
                font=("Segoe UI", 12, "bold")
            )
            value.pack(anchor="w", pady=2)

            sub = tk.Label(
                card, text="",
                bg=WHITE, fg="#67809E",
                font=("Segoe UI", 7)
            )
            sub.pack(anchor="w")

            self.kpis.append((value, sub))

        # Four charts in two columns
        self.chart_area = tk.Frame(d, bg=BG)
        self.chart_area.grid(
            row=1, column=0, sticky="nsew", pady=3
        )

        self.chart_area.grid_rowconfigure(0, weight=1)
        self.chart_area.grid_rowconfigure(1, weight=1)
        self.chart_area.grid_columnconfigure(0, weight=1)
        self.chart_area.grid_columnconfigure(1, weight=1)

        titles = [
            "Category-wise Spending",
            "Daily Expense Trend",
            "Expenses by Category",
            "Payment Mode Analysis"
        ]

        self.chart_frames = []

        for i, title in enumerate(titles):
            frame = tk.Frame(
                self.chart_area,
                bg=WHITE,
                highlightbackground=BORDER,
                highlightthickness=1
            )
            frame.grid(
                row=i // 2, column=i % 2,
                sticky="nsew", padx=3, pady=3
            )

            tk.Label(
                frame, text=title,
                bg=WHITE, fg=TEXT,
                font=("Segoe UI", 9, "bold")
            ).pack(anchor="w", padx=7, pady=(4, 0))

            self.chart_frames.append(frame)

        # Bottom row: table and insights only
        # Monthly Comparison has been removed.
        bottom = tk.Frame(d, bg=BG)
        bottom.grid(row=2, column=0, sticky="nsew")

        bottom.grid_columnconfigure(0, weight=7)
        bottom.grid_columnconfigure(1, weight=3)
        bottom.grid_rowconfigure(0, weight=1)

        table_frame = self.panel(bottom, "Top 5 Expenses")
        table_frame.grid(
            row=0, column=0, sticky="nsew", padx=3, pady=2
        )

        holder = tk.Frame(table_frame, bg=WHITE)
        holder.pack(fill="both", expand=True, padx=3, pady=2)

        columns = (
            "id", "date", "category",
            "description", "amount", "payment"
        )

        self.tree = ttk.Treeview(
            holder, columns=columns,
            show="headings", height=4
        )

        headings = [
            ("id", "#", 30),
            ("date", "Date", 85),
            ("category", "Category", 90),
            ("description", "Description", 100),
            ("amount", "Amount (₹)", 75),
            ("payment", "Mode", 65)
        ]

        for key, label, width in headings:
            self.tree.heading(key, text=label)
            self.tree.column(
                key, width=width,
                minwidth=25, anchor="center",
                stretch=True
            )

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.load_selected)

        insight_frame = self.panel(bottom, "Expense Insights")
        insight_frame.grid(
            row=0, column=1, sticky="nsew", padx=3, pady=2
        )

        self.insights = tk.Label(
            insight_frame,
            text="Add expenses to view insights.",
            bg=WHITE, fg=TEXT,
            font=("Segoe UI", 9),
            justify="left",
            anchor="nw",
            wraplength=220
        )
        self.insights.pack(
            fill="both", expand=True, padx=7, pady=7
        )

    def panel(self, parent, title):
        frame = tk.Frame(
            parent, bg=WHITE,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        tk.Label(
            frame, text=title,
            bg=WHITE, fg=TEXT,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=6, pady=3)

        return frame

    # ---------------- FORM FUNCTIONS ----------------

    def clear_form(self):
        for item in (
            self.date_entry,
            self.category_entry,
            self.description_entry,
            self.amount_entry
        ):
            item.delete(0, tk.END)

        self.date_entry.insert(
            0, datetime.today().strftime("%Y-%m-%d")
        )
        self.payment_entry.set("Cash")

    def get_form(self):
        date_text = self.date_entry.get().strip()
        category = self.category_entry.get().strip()
        description = self.description_entry.get().strip()
        amount_text = self.amount_entry.get().strip()
        payment = self.payment_entry.get().strip()

        if not date_text or not category or not amount_text:
            messagebox.showwarning(
                "Missing Information",
                "Enter date, category and amount."
            )
            return None

        try:
            expense_date = datetime.strptime(
                date_text, "%Y-%m-%d"
            ).date()

            amount = float(amount_text)

            if amount <= 0:
                raise ValueError

        except ValueError:
            messagebox.showwarning(
                "Invalid Input",
                "Use YYYY-MM-DD for date and enter a positive amount."
            )
            return None

        return (
            expense_date, category,
            description, amount, payment
        )

    def add_expense(self):
        data = self.get_form()
        if not data:
            return

        try:
            query_db("""
                INSERT INTO expenses
                (expense_date, category, description, amount, payment_mode)
                VALUES (%s, %s, %s, %s, %s)
            """, data)

            self.clear_form()
            self.refresh_data()

            messagebox.showinfo(
                "Success", "Expense added successfully."
            )

        except mysql.connector.Error as error:
            messagebox.showerror("Database Error", str(error))

    def update_expense(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select Expense",
                "Select an expense from the table."
            )
            return

        data = self.get_form()
        if not data:
            return

        expense_id = self.tree.item(
            selected[0], "values"
        )[0]

        try:
            query_db("""
                UPDATE expenses
                SET expense_date=%s, category=%s,
                    description=%s, amount=%s, payment_mode=%s
                WHERE id=%s
            """, data + (expense_id,))

            self.clear_form()
            self.refresh_data()

            messagebox.showinfo(
                "Success", "Expense updated successfully."
            )

        except mysql.connector.Error as error:
            messagebox.showerror("Database Error", str(error))

    def delete_expense(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select Expense",
                "Select an expense from the table."
            )
            return

        expense_id = self.tree.item(
            selected[0], "values"
        )[0]

        if messagebox.askyesno(
            "Confirm Delete",
            f"Delete expense #{expense_id}?"
        ):
            try:
                query_db(
                    "DELETE FROM expenses WHERE id=%s",
                    (expense_id,)
                )

                self.clear_form()
                self.refresh_data()

            except mysql.connector.Error as error:
                messagebox.showerror("Database Error", str(error))

    def load_selected(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(
            selected[0], "values"
        )

        self.clear_form()

        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, str(values[1]))

        self.category_entry.insert(0, str(values[2]))
        self.description_entry.insert(0, str(values[3]))
        self.amount_entry.insert(0, str(values[4]))
        self.payment_entry.set(str(values[5]))

    # ---------------- FILTERS ----------------

    def reset_filters(self):
        self.month.set("All Months")
        self.category.set("All")
        self.payment.set("All")
        self.refresh_data()

    # ---------------- REFRESH DATA ----------------

    def refresh_data(self):
        try:
            rows = query_db("""
                SELECT id, expense_date, category,
                       description, amount, payment_mode
                FROM expenses
                ORDER BY expense_date DESC, id DESC
            """, fetch=True)

        except mysql.connector.Error as error:
            messagebox.showerror(
                "Database Error",
                "Check MySQL and your database settings.\n\n"
                + str(error)
            )
            return

        months = sorted(
            {str(r[1])[:7] for r in rows},
            reverse=True
        )
        categories = sorted({r[2] for r in rows})
        payments = sorted({r[5] for r in rows})

        self.month_box["values"] = ["All Months"] + months
        self.category_box["values"] = ["All"] + categories
        self.payment_box["values"] = ["All"] + payments

        if self.month.get() not in self.month_box["values"]:
            self.month.set("All Months")

        if self.category.get() not in self.category_box["values"]:
            self.category.set("All")

        if self.payment.get() not in self.payment_box["values"]:
            self.payment.set("All")

        filtered = []

        for row in rows:
            if (
                self.month.get() != "All Months"
                and str(row[1])[:7] != self.month.get()
            ):
                continue

            if (
                self.category.get() != "All"
                and row[2] != self.category.get()
            ):
                continue

            if (
                self.payment.get() != "All"
                and row[5] != self.payment.get()
            ):
                continue

            filtered.append(row)

        self.update_table(filtered)
        self.update_kpis(filtered)
        self.update_charts(filtered)
        self.update_insights(filtered)

        if filtered:
            dates = [str(r[1]) for r in filtered]
            self.date_label.config(
                text=f"DATE RANGE\n{min(dates)}  →  {max(dates)}"
            )
        else:
            self.date_label.config(text="DATE RANGE\nNo expenses")

    # ---------------- TABLE ----------------

    def update_table(self, rows):
        self.tree.delete(*self.tree.get_children())

        top = sorted(
            rows,
            key=lambda r: float(r[4]),
            reverse=True
        )[:5]

        for row in top:
            self.tree.insert(
                "", "end",
                values=(
                    row[0], row[1], row[2],
                    row[3] or "",
                    f"{float(row[4]):.2f}",
                    row[5]
                )
            )

    # ---------------- KPI CARDS ----------------

    def update_kpis(self, rows):
        total = sum(float(r[4]) for r in rows)
        count = len(rows)
        average = total / count if count else 0

        highest = max(
            rows,
            key=lambda r: float(r[4]),
            default=None
        )

        categories = {}

        for row in rows:
            categories[row[2]] = (
                categories.get(row[2], 0) + float(row[4])
            )

        top_category = (
            max(categories, key=categories.get)
            if categories else "—"
        )

        share = (
            categories.get(top_category, 0) / total * 100
            if total else 0
        )

        self.kpis[0][0].config(text=money(total))
        self.kpis[0][1].config(text=f"{count} transactions")

        self.kpis[1][0].config(text=money(average))
        self.kpis[1][1].config(text="Per transaction")

        self.kpis[2][0].config(
            text=money(highest[4]) if highest else money(0)
        )
        self.kpis[2][1].config(
            text=highest[2] if highest else "No expenses"
        )

        self.kpis[3][0].config(text=top_category)
        self.kpis[3][1].config(
            text=f"{share:.1f}% of spending"
        )

    # ---------------- CHART HELPERS ----------------

    def clear_charts(self):
        for canvas in self.chart_canvases:
            canvas.get_tk_widget().destroy()

        self.chart_canvases = []

    def draw_chart(self, parent, fig):
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both", expand=True,
            padx=3, pady=2
        )

        self.chart_canvases.append(canvas)

    def make_figure(self):
        # Larger figure so the pie charts fill their panels
        return Figure(
            figsize=(5.2, 2.2),
            dpi=90,
            facecolor=WHITE
        )

    # ---------------- CHARTS ----------------

    def update_charts(self, rows):
        self.clear_charts()

        category_totals = {}
        daily_totals = {}
        payment_totals = {}

        for row in rows:
            date = str(row[1])
            category = row[2]
            amount = float(row[4])
            payment = row[5]

            category_totals[category] = (
                category_totals.get(category, 0) + amount
            )

            daily_totals[date] = (
                daily_totals.get(date, 0) + amount
            )

            payment_totals[payment] = (
                payment_totals.get(payment, 0) + amount
            )

        # 1. Larger category pie chart
        fig = self.make_figure()
        ax = fig.add_subplot(111)

        if category_totals:
            labels = list(category_totals.keys())
            amounts = list(category_totals.values())

            wedges, _, _ = ax.pie(
                amounts,
                labels=None,
                autopct="%1.1f%%",
                startangle=90,
                pctdistance=0.70,
                radius=1.12,
                textprops={"fontsize": 9, "weight": "bold"},
                wedgeprops={
                    "edgecolor": WHITE,
                    "linewidth": 1.5
                }
            )

            ax.legend(
                wedges,
                [
                    f"{name}: ₹{amount:,.0f}"
                    for name, amount in zip(labels, amounts)
                ],
                loc="center left",
                bbox_to_anchor=(0.98, 0.5),
                fontsize=8,
                frameon=False,
                borderaxespad=0
            )

        else:
            ax.text(
                0.5, 0.5, "No expense data",
                ha="center", va="center"
            )

        ax.set_aspect("equal")
        fig.subplots_adjust(
            left=0.03, right=0.96,
            top=0.95, bottom=0.03
        )

        self.draw_chart(self.chart_frames[0], fig)

        # 2. Daily expense trend
        fig = self.make_figure()
        ax = fig.add_subplot(111)

        if daily_totals:
            days = sorted(daily_totals)
            amounts = [daily_totals[d] for d in days]

            ax.plot(
                days, amounts,
                marker="o",
                markersize=5,
                linewidth=2,
                color=BLUE
            )

            ax.set_ylabel("Amount (₹)", fontsize=8)
            ax.tick_params(axis="both", labelsize=8)
            ax.tick_params(axis="x", labelrotation=15)
            ax.grid(axis="y", alpha=0.25)
        else:
            ax.text(
                0.5, 0.5, "No expense data",
                ha="center", va="center"
            )

        fig.tight_layout()
        self.draw_chart(self.chart_frames[1], fig)

        # 3. Category bar chart
        fig = self.make_figure()
        ax = fig.add_subplot(111)

        if category_totals:
            names = list(category_totals.keys())
            amounts = list(category_totals.values())

            colors = [
                BLUE, ORANGE, GREEN,
                PURPLE, RED
            ]

            ax.bar(
                names,
                amounts,
                color=[
                    colors[i % len(colors)]
                    for i in range(len(names))
                ],
                width=0.65
            )

            ax.set_ylabel("Amount (₹)", fontsize=8)
            ax.tick_params(axis="both", labelsize=8)
            ax.tick_params(axis="x", labelrotation=15)
            ax.grid(axis="y", alpha=0.25)
            ax.set_axisbelow(True)
        else:
            ax.text(
                0.5, 0.5, "No expense data",
                ha="center", va="center"
            )

        fig.tight_layout()
        self.draw_chart(self.chart_frames[2], fig)

        # 4. Larger payment mode doughnut chart
        fig = self.make_figure()
        ax = fig.add_subplot(111)

        if payment_totals:
            labels = list(payment_totals.keys())
            amounts = list(payment_totals.values())
            total = sum(amounts)

            wedges, _, _ = ax.pie(
                amounts,
                labels=None,
                autopct="%1.1f%%",
                startangle=90,
                pctdistance=0.78,
                radius=1.12,
                wedgeprops={
                    "width": 0.42,
                    "edgecolor": WHITE,
                    "linewidth": 1.5
                },
                textprops={"fontsize": 9, "weight": "bold"}
            )

            ax.text(
                0, 0,
                f"Total\n₹{total:,.0f}",
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold",
                color=NAVY
            )

            ax.legend(
                wedges,
                [
                    f"{name}: ₹{amount:,.0f}"
                    for name, amount in zip(labels, amounts)
                ],
                loc="center left",
                bbox_to_anchor=(0.98, 0.5),
                fontsize=8,
                frameon=False,
                borderaxespad=0
            )

        else:
            ax.text(
                0.5, 0.5, "No expense data",
                ha="center", va="center"
            )

        ax.set_aspect("equal")
        fig.subplots_adjust(
            left=0.03, right=0.96,
            top=0.95, bottom=0.03
        )

        self.draw_chart(self.chart_frames[3], fig)

    # ---------------- EXPENSE INSIGHTS ----------------

    def update_insights(self, rows):
        if not rows:
            self.insights.config(
                text="Add expenses to view insights."
            )
            return

        total = sum(float(r[4]) for r in rows)
        category_totals = {}
        payment_totals = {}

        for row in rows:
            category_totals[row[2]] = (
                category_totals.get(row[2], 0) + float(row[4])
            )

            payment_totals[row[5]] = (
                payment_totals.get(row[5], 0) + float(row[4])
            )

        top_category = max(
            category_totals, key=category_totals.get
        )

        top_payment = max(
            payment_totals, key=payment_totals.get
        )

        category_percent = (
            category_totals[top_category] / total * 100
        )

        payment_percent = (
            payment_totals[top_payment] / total * 100
        )

        self.insights.config(
            text=(
                f"Total Spending\n{money(total)}\n\n"
                f"Top Category\n{top_category} "
                f"({category_percent:.1f}%)\n\n"
                f"Top Payment Mode\n{top_payment} "
                f"({payment_percent:.1f}%)\n\n"
                f"Transactions\n{len(rows)}"
            )
        )


# ---------------- START APPLICATION ----------------

if __name__ == "__main__":
    try:
        connect_database()

    except mysql.connector.Error as error:
        temp = tk.Tk()
        temp.withdraw()

        messagebox.showerror(
            "MySQL Error",
            "Check that MySQL is running and your password is correct.\n\n"
            + str(error),
            parent=temp
        )

        temp.destroy()
        raise SystemExit

    root = tk.Tk()
    app = ExpenseDashboard(root)
    root.mainloop()
