import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import csv
import os
import webbrowser

class PythonQueryGenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python QueryGen v0.7")
        self.root.geometry("1000x700")

        self.filename = None
        self.headers = []
        self.rows = []
        self.column_vars = {}
        self.where_column_vars = {}
        self.value_overrides = {}  # Store custom values for UPDATE

        self.setup_ui()

    def setup_ui(self):
        # Load Button
        tk.Button(self.root, text="Load CSV", command=self.load_csv).pack(pady=10)

        # Table name input
        table_frame = tk.Frame(self.root)
        table_frame.pack()
        tk.Label(table_frame, text="Table Name:").pack(side=tk.LEFT, padx=5)
        self.table_name_entry = tk.Entry(table_frame, width=40)
        self.table_name_entry.pack(side=tk.LEFT)

        # Scrollable Checkboxes Frame
        outer_frame = tk.LabelFrame(self.root, text="Select Columns to Use", padx=10, pady=10)
        outer_frame.pack(fill=tk.X, padx=10, pady=5)

        canvas = tk.Canvas(outer_frame, height=80)
        canvas.pack(side=tk.TOP, fill=tk.X, expand=True)

        h_scroll = tk.Scrollbar(outer_frame, orient=tk.HORIZONTAL, command=canvas.xview)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.configure(xscrollcommand=h_scroll.set)

        self.checkbox_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=self.checkbox_frame, anchor='nw')
        self.checkbox_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Query selection dropdown
        self.query_type = tk.StringVar(value="CREATE TABLE")
        query_options = ["CREATE TABLE", "INSERT INTO", "SELECT", "UPDATE", "DELETE"]
        query_menu = tk.OptionMenu(self.root, self.query_type, *query_options, command=self.on_query_type_change)
        query_menu.pack(pady=10)

        # WHERE Clause Frame (initially hidden)
        self.where_clause_frame_outer = tk.LabelFrame(self.root, text="Select Columns for WHERE Clause (UPDATE only)", padx=10, pady=10)

        self.where_clause_canvas = tk.Canvas(self.where_clause_frame_outer, height=60)
        self.where_clause_canvas.pack(side=tk.TOP, fill=tk.X, expand=True)

        h_scroll_where = tk.Scrollbar(self.where_clause_frame_outer, orient=tk.HORIZONTAL, command=self.where_clause_canvas.xview)
        h_scroll_where.pack(side=tk.BOTTOM, fill=tk.X)
        self.where_clause_canvas.configure(xscrollcommand=h_scroll_where.set)

        self.where_clause_inner = tk.Frame(self.where_clause_canvas)
        self.where_clause_canvas.create_window((0, 0), window=self.where_clause_inner, anchor='nw')
        self.where_clause_inner.bind("<Configure>", lambda e: self.where_clause_canvas.configure(scrollregion=self.where_clause_canvas.bbox("all")))

        self.where_clause_frame_outer.pack_forget()

        # Edit Values Button (for UPDATE queries)
        self.edit_values_button = tk.Button(self.root, text="Edit SET Values", command=self.open_value_editor)
        self.edit_values_button.pack_forget()

        # Generate SQL button
        self.generate_button = tk.Button(self.root, text="Generate SQL", command=self.generate_sql)
        self.generate_button.pack(pady=10)

        # Output textbox
        self.output = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=25)
        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Menu Bar
        self.menu_bar = tk.Menu(self.root)
        self.file = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file)
        self.file.add_separator()
        self.file.add_command(label="Exit", command=self.root.destroy)

        self.help = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=self.help)
        self.help.add_command(label="Help", command=self.open_help_dialog)
        self.help.add_command(label="About", command=self.show_about_dialog)
        self.root.config(menu=self.menu_bar)

    def on_query_type_change(self, value):
        if value == "UPDATE":
            self.where_clause_frame_outer.pack(fill=tk.X, padx=10, pady=5, before=self.generate_button)
            self.edit_values_button.pack(pady=5, before=self.generate_button)
        else:
            self.where_clause_frame_outer.pack_forget()
            self.edit_values_button.pack_forget()

    def load_csv(self):
        self.filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not self.filename:
            return

        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                self.headers = next(reader)
                self.rows = [row for row in reader if any(row)]

            base_name = os.path.splitext(os.path.basename(self.filename))[0]
            self.table_name_entry.delete(0, tk.END)
            self.table_name_entry.insert(0, base_name)

            # Clear checkboxes
            for widget in self.checkbox_frame.winfo_children():
                widget.destroy()
            for widget in self.where_clause_inner.winfo_children():
                widget.destroy()

            self.column_vars.clear()
            self.where_column_vars.clear()
            self.value_overrides.clear()

            for col in self.headers:
                var = tk.BooleanVar(value=True)
                where_var = tk.BooleanVar(value=True)
                self.column_vars[col] = var
                self.where_column_vars[col] = where_var
                tk.Checkbutton(self.checkbox_frame, text=col, variable=var).pack(side=tk.LEFT)
                tk.Checkbutton(self.where_clause_inner, text=col, variable=where_var).pack(side=tk.LEFT)

            messagebox.showinfo("CSV Loaded", f"Loaded {len(self.rows)} rows from {base_name}.csv")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read CSV: {e}")

    def open_value_editor(self):
        """Change values of selected columns for UPDATE queries"""
        selected_cols = self.get_selected_columns()
        if not selected_cols:
            messagebox.showwarning("No Columns", "Please select at least one column first.")
            return

        editor = tk.Toplevel(self.root)
        editor.title("Edit SET Values for UPDATE Query")
        editor.geometry("500x400")

        tk.Label(editor, text="Set custom values for UPDATE columns (leave blank to use CSV values)", 
                 wraplength=450, pady=10).pack()

        # Create frame
        canvas = tk.Canvas(editor)
        scrollbar = tk.Scrollbar(editor, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create fields for each column
        entries = {}
        for col in selected_cols:
            frame = tk.Frame(scrollable_frame)
            frame.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(frame, text=f"{col}:", width=20, anchor='w').pack(side=tk.LEFT)
            entry = tk.Entry(frame, width=30)
            entry.pack(side=tk.LEFT, padx=5)
            
            # Pre-fill with existing info
            if col in self.value_overrides:
                entry.insert(0, self.value_overrides[col])
            
            entries[col] = entry

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        # Buttons
        button_frame = tk.Frame(editor)
        button_frame.pack(pady=10)

        def save_values():
            for col, entry in entries.items():
                value = entry.get().strip()
                if value:
                    self.value_overrides[col] = value
                elif col in self.value_overrides:
                    del self.value_overrides[col]
            editor.destroy()
            messagebox.showinfo("Saved", "Custom values saved for UPDATE query.")

        def clear_all():
            for entry in entries.values():
                entry.delete(0, tk.END)
            self.value_overrides.clear()

        tk.Button(button_frame, text="Save", command=save_values, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Clear All", command=clear_all, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=editor.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def get_selected_columns(self):
        return [col for col, var in self.column_vars.items() if var.get()]

    def get_where_clause_columns(self):
        return [col for col, var in self.where_column_vars.items() if var.get()]

    def escape_value(self, value):
        return value.replace("'", "''")

    def generate_create_query(self, table_name, columns):
        fields = [f"{col} TEXT" for col in columns]
        return f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(fields) + "\n);"

    def generate_insert_query(self, table_name, columns):
        lines = []
        col_indexes = [self.headers.index(col) for col in columns]
        for row in self.rows:
            values = ", ".join(f"'{self.escape_value(row[i])}'" for i in col_indexes)
            lines.append(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({values});")
        return "\n".join(lines)

    def generate_select_query(self, table_name, columns):
        return f"SELECT {', '.join(columns)} FROM {table_name};"

    def generate_update_query(self, table_name, columns, where_columns):
        queries = []
        for row in self.rows:
            set_clause = ", ".join(
                f"{col} = '{self.escape_value(self.value_overrides.get(col, row[self.headers.index(col)]))}'"
                for col in columns
            )
            where_clause = " AND ".join(
                f"{col} = '{self.escape_value(row[self.headers.index(col)])}'"
                for col in where_columns
            )
            queries.append(f"UPDATE {table_name} SET {set_clause} WHERE {where_clause};")
        return "\n".join(queries)

    def generate_delete_query(self, table_name, columns):
        queries = []
        for row in self.rows:
            where_clause = " AND ".join(
                f"{col} = '{self.escape_value(row[self.headers.index(col)])}'"
                for col in columns
            )
            queries.append(f"DELETE FROM {table_name} WHERE {where_clause};")
        return "\n".join(queries)

    def generate_sql(self):
        if not self.headers or not self.rows:
            messagebox.showwarning("No Data", "Please load a CSV file first.")
            return

        selected_cols = self.get_selected_columns()
        if not selected_cols:
            messagebox.showwarning("No Columns", "Please select at least one column.")
            return

        table_name = self.table_name_entry.get().strip()
        if not table_name:
            messagebox.showwarning("Table Name", "Please enter a table name.")
            return

        query_type = self.query_type.get()
        if query_type == "CREATE TABLE":
            sql = self.generate_create_query(table_name, selected_cols)
        elif query_type == "INSERT INTO":
            sql = self.generate_insert_query(table_name, selected_cols)
        elif query_type == "SELECT":
            sql = self.generate_select_query(table_name, selected_cols)
        elif query_type == "UPDATE":
            where_cols = self.get_where_clause_columns()
            if not where_cols:
                messagebox.showwarning("No WHERE Columns", "Please select at least one column for the WHERE clause.")
                return
            sql = self.generate_update_query(table_name, selected_cols, where_cols)
        elif query_type == "DELETE":
            sql = self.generate_delete_query(table_name, selected_cols)
        else:
            sql = "-- Unsupported query type"

        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, sql)

    def show_about_dialog(self):
        messagebox.showinfo("About Python QueryGen",
                            "Version 0.7\n\n"
                            "A simple SQL Query Builder using Python's Tkinter.\n"
                            "Created by Hayden Hildreth.")

    def open_help_dialog(self):
        webbrowser.open_new_tab("https://github.com/HaydenHildreth/PyQueryGen/")
        messagebox.showinfo("Help opened",
                            "A tab with our user documentation has been\n"
                            "opened in your default browser.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PythonQueryGenApp(root)
    root.mainloop()
