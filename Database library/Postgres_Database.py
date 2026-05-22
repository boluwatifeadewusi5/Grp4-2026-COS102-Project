import tkinter as tk
import psycopg2
import threading
from abc import ABC, abstractmethod

class Abstractor(ABC):
    @abstractmethod
    def show_error(self, message: str):
        pass

    @abstractmethod
    def show_info(self, message: str):
        pass

class DB_GUI(Abstractor):

    def __init__(self):
        self._root = None
        self._label = None
        self._thread = threading.Thread(target=self._build_window, daemon=True)
        self._thread.start()

    def _build_window(self):
        self._root = tk.Tk()
        self._root.title("DB Status")
        self._root.geometry("420x80")
        self._root.resizable(False, False)
        self._root.configure(bg="#1e1e2e")

        self._label = tk.Label(
            self._root,
            text="Waiting for database activity...",
            bg="#1e1e2e",
            fg="#cdd6f4",
            font=("Courier", 11),
            wraplength=400,
            justify="left",
            padx=10,
            pady=20,
        )
        self._label.pack(fill="both", expand=True)
        self._root.mainloop()   # runs only inside this thread — kernel stays alive

    def _set_label(self, text: str, color: str):
        # schedule on the Tk thread; safe to call from any thread
        if self._root and self._label:
            self._root.after(0, lambda: self._label.config(text=text, fg=color))

    def show_error(self, message: str):
        print(f"[DB ERROR] {message}")
        self._set_label(f"✗  {message}", "#f38ba8")   # red

    def show_info(self, message: str):
        print(f"[DB INFO]  {message}")
        self._set_label(f"✓  {message}", "#a6e3a1")   # green


# ─────────────────────────────────────────────
#  Database layer
# ─────────────────────────────────────────────

class DATABASE(DB_GUI):

    def __init__(self, host: str, port: str, db_name: str, user: str, password: str):
        super().__init__()
        self._conn = None
        self._cursor = None

        try:
            self._conn = psycopg2.connect(
                host=host, port=port, dbname=db_name, user=user, password=password
            )
            self._cursor = self._conn.cursor()
            self.show_info("Connection successful!")
        except Exception as e:
            self.show_error(str(e))

    # ── internal helpers ──────────────────────

    def _execute(self, query: str, success_message: str = ""):
        try:
            self._cursor.execute(query)
            self._conn.commit()
            if success_message:
                self.show_info(success_message)
        except Exception as e:
            self.show_error(str(e))

    def _confirm(self, prompt: str) -> bool:
        """Simple terminal confirmation — avoids blocking Tk dialogs."""
        answer = input(f"[CONFIRM] {prompt} (y/n): ").strip().lower()
        return answer == "y"

    # ── public API ────────────────────────────

    def create_table(self, table_name: str, columns: tuple, data_types: tuple, primary_key: str = ""):
        try:
            col_defs = ",\n".join(f"{col} {dtype}" for col, dtype in zip(columns, data_types))
            query = f"CREATE TABLE {table_name} (\n{col_defs}"
            if primary_key:
                query += f",\nPRIMARY KEY ({primary_key})"
            else:
                if not self._confirm("No primary key specified. Continue?"):
                    return
            query += "\n);"
            self._execute(query, "Table created successfully.")
        except Exception as e:
            self.show_error(str(e))

    def insert(self, table_name: str, columns: tuple, values):
        try:
            col_str = ", ".join(columns)
            query = f"INSERT INTO {table_name} ({col_str}) VALUES {values};"
            self._execute(query, "Data inserted successfully.")
        except Exception as e:
            self.show_error(str(e))

    def select(self, table_name: str, columns, condition: str = ""):
        try:
            query = f"SELECT {columns} FROM {table_name}"
            if condition:
                query += f" WHERE {condition}"
            query += ";"
            self._cursor.execute(query)
            results = self._cursor.fetchall()
            self.show_info(f"Fetched {len(results)} row(s).")
            return results
        except Exception as e:
            self.show_error(str(e))

    def update(self, table_name: str, set_statement: str, condition: str = ""):
        try:
            query = f"UPDATE {table_name} SET {set_statement}"
            if condition:
                query += f" WHERE {condition}"
            query += ";"
            self._execute(query, "Table updated successfully.")
        except Exception as e:
            self.show_error(str(e))

    def delete_data(self, table_name: str, condition: str = ""):
        try:
            if not condition:
                if not self._confirm("No condition given. This will delete ALL rows. Continue?"):
                    return
                query = f"DELETE FROM {table_name};"
            else:
                query = f"DELETE FROM {table_name} WHERE {condition};"
            self._execute(query, "Data deleted successfully.")
        except Exception as e:
            self.show_error(str(e))

    def delete_table(self, table_name: str):
        try:
            self._execute(f"DROP TABLE {table_name};", "Table dropped successfully.")
        except Exception as e:
            self.show_error(str(e))

    def wipe_table(self, table_name: str):
        try:
            self._execute(f"TRUNCATE TABLE {table_name};", "Table wiped successfully.")
        except Exception as e:
            self.show_error(str(e))

    def add_column(self, table_name: str, column_definition: str):
        try:
            self._execute(f"ALTER TABLE {table_name} ADD COLUMN {column_definition};", "Column added.")
        except Exception as e:
            self.show_error(str(e))

    def remove_column(self, table_name: str, column_name: str):
        try:
            self._execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name};", "Column removed.")
        except Exception as e:
            self.show_error(str(e))

    def rename_table(self, old_name: str, new_name: str):
        try:
            self._execute(f"ALTER TABLE {old_name} RENAME TO {new_name};", "Table renamed.")
        except Exception as e:
            self.show_error(str(e))

    def rename_column(self, table_name: str, old_name: str, new_name: str):
        try:
            self._execute(
                f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name};",
                "Column renamed."
            )
        except Exception as e:
            self.show_error(str(e))

    def __del__(self):
        try:
            if self._cursor:
                self._cursor.close()
            if self._conn:
                self._conn.close()
        except Exception:
            pass

df = DATABASE(host="localhost", port="5432",db_name="test_database", user="postgres", password="Bolu4235@#$")
df.insert(table_name="students", columns=("id", "name", "age"), values="(4, 'Barnet',22),(5, 'Joseph',21)")

