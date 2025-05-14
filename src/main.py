import tkinter as tk
from tkinter import ttk, StringVar, BooleanVar, Listbox, Scrollbar, VERTICAL, HORIZONTAL, messagebox
import sqlite3

class SQLQueryBuilder:
    def __init__(self, root):
        self.root = root
        self.root.title("SQL Query Builder")
        
        # --- Initialize Data ---
        self.tables = []
        self.columns = {}
        self.selected_table = StringVar()
        self.selected_columns = []
        self.where_conditions = []
        self.order_by_columns = []
        self.order_by_direction = StringVar()  # "ASC" or "DESC"
        self.limit_value = StringVar()
        self.offset_value = StringVar()
        self.available_columns = []

        # --- Database Connection ---
        self.conn = None  # Will hold the database connection
        self.cursor = None # Will hold the cursor
        self.db_file = StringVar()  # Stores the database file path
        self.create_connection_frame()

        # --- Query Building Frames ---
        self.from_frame = ttk.Frame(root)
        self.select_frame = ttk.Frame(root)
        self.where_frame = ttk.Frame(root)
        self.orderby_frame = ttk.Frame(root)
        self.limit_offset_frame = ttk.Frame(root)  # New frame for LIMIT and OFFSET
        self.create_from_frame()
        self.create_select_frame()
        self.create_where_frame()
        self.create_orderby_frame()
        self.create_limit_offset_frame() # Initialize the Limit/Offset frame
        self.query_display_frame = ttk.Frame(root)
        self.create_query_display_frame()

        # --- Status Bar ---
        self.status_bar = tk.Label(root, text="Not Connected to Database", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Menu Bar ---
        self.menu_bar = tk.Menu(root)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Connect to Database", command=self.connect_to_database)
        self.file_menu.add_command(label="Execute Query", command=self.execute_query)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=root.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="About", command=self.show_about_dialog)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

        root.config(menu=self.menu_bar)

        # --- Layout ---
        self.connection_frame.pack(pady=10)
        self.from_frame.pack(pady=10, fill=tk.X)
        self.select_frame.pack(pady=10, fill=tk.X)
        self.where_frame.pack(pady=10, fill=tk.X)
        self.orderby_frame.pack(pady=10, fill=tk.X)
        self.limit_offset_frame.pack(pady=10, fill=tk.X) # Pack the Limit/Offset frame
        self.query_display_frame.pack(pady=10, fill=tk.X)

    def create_connection_frame(self):
        self.connection_frame = ttk.Frame(self.root)
        ttk.Label(self.connection_frame, text="Database File:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(self.connection_frame, textvariable=self.db_file, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.connection_frame, text="Connect", command=self.connect_to_database).grid(row=0, column=2, padx=5, pady=5)

    def create_from_frame(self):
        ttk.Label(self.from_frame, text="FROM Table:").pack(side=tk.LEFT, padx=5)
        self.table_combo = ttk.Combobox(self.from_frame, textvariable=self.selected_table, values=self.tables, state="disabled")
        self.table_combo.pack(side=tk.LEFT, padx=5)
        self.table_combo.bind("<<ComboboxSelected>>", self.populate_columns)

    def create_select_frame(self):
        ttk.Label(self.select_frame, text="SELECT Columns:").pack(side=tk.LEFT, padx=5)

        self.select_listbox = Listbox(self.select_frame, selectmode=tk.MULTIPLE, width=40, height=5)
        self.select_listbox.pack(side=tk.LEFT, padx=5, fill=tk.BOTH)

        # Scrollbar for the select listbox
        select_scrollbar = Scrollbar(self.select_frame, orient=VERTICAL, command=self.select_listbox.yview)
        select_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.select_listbox.config(yscrollcommand=select_scrollbar.set)

        # Buttons to add/remove columns
        select_button_frame = ttk.Frame(self.select_frame)
        ttk.Button(select_button_frame, text="Add", command=self.add_selected_columns).pack(side=tk.TOP, padx=5, pady=2)
        ttk.Button(select_button_frame, text="Remove", command=self.remove_selected_columns).pack(side=tk.TOP, padx=5, pady=2)
        select_button_frame.pack(side=tk.LEFT)

    def create_where_frame(self):
        ttk.Label(self.where_frame, text="WHERE Conditions:").pack(side=tk.LEFT, padx=5)

        self.where_listbox = Listbox(self.where_frame, width=50, height=5)
        self.where_listbox.pack(side=tk.LEFT, padx=5, fill=tk.BOTH)

        # Scrollbar for the where listbox
        where_scrollbar = Scrollbar(self.where_frame, orient=VERTICAL, command=self.where_listbox.yview)
        where_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.where_listbox.config(yscrollcommand=where_scrollbar.set)

        self.where_entry = ttk.Entry(self.where_frame, width=30)
        self.where_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(self.where_frame, text="Add Condition", command=self.add_where_condition).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.where_frame, text="Remove Condition", command=self.remove_where_condition).pack(side=tk.LEFT, padx=5)

    def create_orderby_frame(self):
        ttk.Label(self.orderby_frame, text="ORDER BY:").pack(side=tk.LEFT, padx=5)

        self.orderby_listbox = Listbox(self.orderby_frame, selectmode=tk.MULTIPLE, width=40, height=5)
        self.orderby_listbox.pack(side=tk.LEFT, padx=5, fill=tk.BOTH)

        # Scrollbar for the orderby listbox
        orderby_scrollbar = Scrollbar(self.orderby_frame, orient=VERTICAL, command=self.orderby_listbox.yview)
        orderby_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.orderby_listbox.config(yscrollcommand=orderby_scrollbar.set)

        self.order_by_direction.set("ASC")  # Default to ascending
        self.asc_radio = ttk.Radiobutton(self.orderby_frame, text="ASC", variable=self.order_by_direction, value="ASC")
        self.desc_radio = ttk.Radiobutton(self.orderby_frame, text="DESC", variable=self.order_by_direction, value="DESC")
        self.asc_radio.pack(side=tk.LEFT, padx=5)
        self.desc_radio.pack(side=tk.LEFT, padx=5)

        # Add/Remove buttons for Order By
        order_button_frame = ttk.Frame(self.orderby_frame)
        ttk.Button(order_button_frame, text="Add", command=self.add_order_by_columns).pack(side=tk.TOP, padx=5, pady=2)
        ttk.Button(order_button_frame, text="Remove", command=self.remove_order_by_columns).pack(side=tk.TOP, padx=5, pady=2)
        order_button_frame.pack(side=tk.LEFT)

    def create_limit_offset_frame(self):
        ttk.Label(self.limit_offset_frame, text="LIMIT").pack(side=tk.LEFT, padx=5)
        ttk.Entry(self.limit_offset_frame, textvariable=self.limit_value, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Label(self.limit_offset_frame, text="OFFSET").pack(side=tk.LEFT, padx=5)
        ttk.Entry(self.limit_offset_frame, textvariable=self.offset_value, width=10).pack(side=tk.LEFT, padx=5)

    def create_query_display_frame(self):
        ttk.Label(self.query_display_frame, text="Generated Query:").pack(side=tk.TOP, padx=5)
        self.query_text = tk.Text(self.query_display_frame, height=5, width=80)
        self.query_text.pack(side=tk.LEFT, padx=5, fill=tk.BOTH)
        query_scrollbar = Scrollbar(self.query_display_frame, orient=VERTICAL, command=self.query_text.yview)
        query_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.query_text.config(yscrollcommand=query_scrollbar.set)

    def connect_to_database(self):
        db_file = self.db_file.get()
        if not db_file:
            messagebox.showerror("Error", "Please enter a database file path.")
            self.status_bar.config(text="No Database Selected")
            return

        try:
            self.conn = sqlite3.connect(db_file)
            self.cursor = self.conn.cursor()
            self.status_bar.config(text=f"Connected to {db_file}")
            self.populate_tables()  # Populate the table list
        except sqlite3.Error as e:
            messagebox.showerror("Connection Error", f"Error connecting to database: {e}")
            self.status_bar.config(text="Connection Failed")
            self.conn = None
            self.cursor = None

    def populate_tables(self):
        if self.cursor:
            try:
                self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                self.tables = [row[0] for row in self.cursor.fetchall()]
                self.table_combo['values'] = self.tables
                self.table_combo['state'] = 'readonly' # Enable the combobox
                if self.tables:
                  self.selected_table.set(self.tables[0])  # Set a default table
                  self.populate_columns()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Error fetching tables: {e}")
        else:
            messagebox.showerror("Error", "Not connected to a database.")

    def populate_columns(self, event=None):
        table_name = self.selected_table.get()
        if self.cursor and table_name:
            try:
                self.cursor.execute(f"PRAGMA table_info({table_name})")
                self.available_columns = [row[1] for row in self.cursor.fetchall()]
                self.columns = self.available_columns
                self.select_listbox.delete(0, tk.END)  # Clear previous columns
                self.orderby_listbox.delete(0, tk.END)
                for col in self.columns:
                    self.select_listbox.insert(tk.END, col)
                    self.orderby_listbox.insert(tk.END, col)
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Error fetching columns: {e}")
        elif not self.cursor:
             messagebox.showerror("Error", "Not connected to a database.")

    def add_selected_columns(self):
        selected_indices = self.select_listbox.curselection()
        for i in selected_indices:
            col = self.columns[i]
            if col not in self.selected_columns:
                self.selected_columns.append(col)
        self.update_query_display()

    def remove_selected_columns(self):
        selected_indices = self.select_listbox.curselection()
        # Iterate in reverse order to avoid index issues when removing elements
        for i in sorted(selected_indices, reverse=True):
            col = self.columns[i]
            if col in self.selected_columns:
                self.selected_columns.remove(col)
        self.update_query_display()

    def add_where_condition(self):
        condition = self.where_entry.get()
        if condition:
            self.where_conditions.append(condition)
            self.where_listbox.insert(tk.END, condition)
            self.where_entry.delete(0, tk.END)
            self.update_query_display()

    def remove_where_condition(self):
        selected_index = self.where_listbox.curselection()
        if selected_index:
            condition = self.where_listbox.get(selected_index[0])  # Get the condition string
            self.where_conditions.remove(condition)  # Remove it from the list
            self.where_listbox.delete(selected_index[0])
            self.update_query_display()

    def add_order_by_columns(self):
        selected_indices = self.orderby_listbox.curselection()
        for i in selected_indices:
            col = self.columns[i]
            if col not in self.order_by_columns:
                self.order_by_columns.append(col)
        self.update_query_display()

    def remove_order_by_columns(self):
        selected_indices = self.orderby_listbox.curselection()
         # Iterate in reverse order to avoid index issues when removing elements
        for i in sorted(selected_indices, reverse=True):
            col = self.columns[i]
            if col in self.order_by_columns:
                self.order_by_columns.remove(col)
        self.update_query_display()

    def build_query(self):
        query = "SELECT "
        if self.selected_columns:
            query += ", ".join(self.selected_columns)
        else:
            query += "*"  # Default to all columns if none selected

        if self.selected_table.get():
            query += f" FROM {self.selected_table.get()}"
        else:
            return "SELECT * FROM ;" # Return a minimal query, but it will error.

        if self.where_conditions:
            query += " WHERE " + " AND ".join(self.where_conditions)

        if self.order_by_columns:
            query += f" ORDER BY " + ", ".join(self.order_by_columns) + f" {self.order_by_direction.get()}"

        if self.limit_value.get():
            query += f" LIMIT {self.limit_value.get()}"
        if self.offset_value.get():
            query += f" OFFSET {self.offset_value.get()}"

        query += ";"
        return query

    def update_query_display(self):
        query = self.build_query()
        self.query_text.delete("1.0", tk.END)
        self.query_text.insert(tk.END, query)

    def execute_query(self):
        if not self.cursor:
            messagebox.showerror("Error", "Not connected to a database.")
            return

        query = self.build_query()
        try:
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            if results:
                # Display results in a new window
                self.display_results(results)
            else:
                messagebox.showinfo("Success", "Query executed successfully. No results returned.")

        except sqlite3.Error as e:
            messagebox.showerror("Query Error", f"Error executing query: {e}")

    def display_results(self, results):
        results_window = tk.Toplevel(self.root)
        results_window.title("Query Results")

        # Determine number of columns
        num_cols = len(results[0]) if results else 0

        # Get column names (if possible - depends on the query)
        column_names = [description[0] for description in self.cursor.description] if self.cursor.description else [f"Column {i+1}" for i in range(num_cols)]

        # Create Treeview widget to display results
        tree = ttk.Treeview(results_window, cols=column_names, show="headings")

        # Define column headings
        for col in column_names:
            tree.heading(col, text=col)
            tree.column(col, width=100)  # Adjust width as needed

        # Insert data into the Treeview
        for row in results:
            tree.insert("", tk.END, values=row)

        tree.pack(expand=True, fill=tk.BOTH)

    def show_about_dialog(self):
        messagebox.showinfo("About SQL Query Builder",
                            "Version 0.1\n\n"
                            "A simple SQL Query Builder using Tkinter.\n"
                            "Created by Hayden Hildreth.")

    def close_connection(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            self.status_bar.config(text="Disconnected")
            messagebox.showinfo("Disconnected", "Successfully disconnected from the database.")

if __name__ == "__main__":
    root = tk.Tk()
    app = SQLQueryBuilder(root)
    root.protocol("WM_DELETE_WINDOW", app.close_connection) # Close DB connection on exit
    root.mainloop()
