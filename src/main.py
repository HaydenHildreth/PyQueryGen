import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import csv
import os
import webbrowser

class PythonQueryGenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python QueryGen")
        self.root.geometry("1000x700")

        self.filename = None
        self.headers = []
        self.rows = []
        self.column_vars = {}

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

        # Create an inner frame to hold checkboxes
        self.checkbox_frame = tk.Frame(canvas)
        self.checkbox_window = canvas.create_window((0, 0), window=self.checkbox_frame, anchor='nw')

        # Update scrollregion when contents change
        def update_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.checkbox_frame.bind("<Configure>", update_scrollregion)

        # Query selection
        self.query_type = tk.StringVar(value="CREATE TABLE")
        query_options = ["CREATE TABLE", "INSERT INTO", "SELECT", "UPDATE", "DELETE"]
        tk.OptionMenu(self.root, self.query_type, *query_options).pack(pady=10)

        # Generate
        tk.Button(self.root, text="Generate SQL", command=self.generate_sql).pack(pady=10)

        # Query output
        self.output = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=25)
        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Menu Bar
        self.menu_bar = tk.Menu(root)
        
        # File section of Menu Bar
        self.file = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file)
        self.file.add_separator()
        self.file.add_command(label="Exit", command=root.destroy)
        
        # Help and About section of Menu Bar
        self.help = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=self.help)
        self.help.add_command(label="Help", command=self.open_help_dialog)
        self.help.add_command(label="About", command=self.show_about_dialog)

        # Display Menu Bar
        root.config(menu=self.menu_bar)

    def load_csv(self):
        self.filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not self.filename:
            return

        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                self.headers = next(reader)
                self.rows = [row for row in reader if any(row)]

            # This sets table name equal to .CSV name
            base_name = os.path.splitext(os.path.basename(self.filename))[0]
            self.table_name_entry.delete(0, tk.END)
            self.table_name_entry.insert(0, base_name)

            # Clear checkboxes
            for widget in self.checkbox_frame.winfo_children():
                widget.destroy()

            # Create new checkboxes
            self.column_vars.clear()
            for col in self.headers:
                var = tk.BooleanVar(value=True)
                self.column_vars[col] = var
                tk.Checkbutton(self.checkbox_frame, text=col, variable=var).pack(side=tk.LEFT)

            messagebox.showinfo("CSV Loaded", f"Loaded {len(self.rows)} rows from {base_name}.csv")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read CSV: {e}")

    def get_selected_columns(self):
        return [col for col, var in self.column_vars.items() if var.get()]

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

    def generate_update_query(self, table_name, columns):
        col_indexes = [self.headers.index(col) for col in columns]
        queries = []
        for i, row in enumerate(self.rows):
            set_clause = ", ".join(
                f"{col} = '{self.escape_value(row[self.headers.index(col)])}'"
                for col in columns
            )
            where_clause = " AND ".join(
                f"{col} = '{self.escape_value(row[self.headers.index(col)])}'"
                for col in columns
            )
            queries.append(f"UPDATE {table_name} SET {set_clause} WHERE {where_clause};")
        return "\n".join(queries)

    def generate_delete_query(self, table_name, columns):
        queries = []
        for i, row in enumerate(self.rows):
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
            sql = self.generate_update_query(table_name, selected_cols)
        elif query_type == "DELETE":
            sql = self.generate_delete_query(table_name, selected_cols)
        else:
            sql = "-- Unsupported query type"

        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, sql)

    # About box popup
    def show_about_dialog(self):
        messagebox.showinfo("About Python QueryGen",
                            "Version 0.5\n\n"
                            "A simple SQL Query Builder using Python's Tkinter.\n"
                            "Created by Hayden Hildreth.")
                            
    # Help box popup
    def open_help_dialog(self):
        self.help_link = 'https://github.com/HaydenHildreth/PyQueryGen/'
        webbrowser.open_new_tab(self.help_link)
        messagebox.showinfo("Help opened",
                            "A tab with our user documentation has been\n"
                            "opened in your default browser.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PythonQueryGenApp(root)
    root.mainloop()
