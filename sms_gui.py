import sqlite3
import os
import glob
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class SMSExporterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("iPhone Message Exporter")
        self.root.geometry("560x560")
        self.root.resizable(False, False)

        # --- Section 1: Backup File ---
        tk.Label(root, text="1. iPhone Backup Location", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(15, 2))
        tk.Label(root, text="We automatically looked for your iPhone backup on this computer:", font=("Arial", 9), fg="#555").pack(anchor="w", padx=20)
        
        db_frame = tk.Frame(root)
        db_frame.pack(fill="x", padx=20, pady=5)
        
        self.db_path_entry = tk.Entry(db_frame, width=48, font=("Arial", 10))
        self.db_path_entry.pack(side="left", padx=(0, 10))
        
        browse_btn = tk.Button(db_frame, text="Browse...", command=self.browse_db, width=10)
        browse_btn.pack(side="left")

        # --- Section 2: Contact Selection ---
        tk.Label(root, text="2. Choose Conversation", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(15, 2))
        
        # Export All Toggle
        self.export_all_var = tk.BooleanVar(value=False)
        self.export_all_chk = tk.Checkbutton(
            root, text="Export every conversation on my phone (Export All)", 
            variable=self.export_all_var, font=("Arial", 10), command=self.toggle_target_state
        )
        self.export_all_chk.pack(anchor="w", padx=20, pady=(2, 5))

        tk.Label(root, text="Or select a specific person/number:", font=("Arial", 9), fg="#555").pack(anchor="w", padx=20)
        
        contact_frame = tk.Frame(root)
        contact_frame.pack(fill="x", padx=20, pady=5)

        self.contact_combo = ttk.Combobox(contact_frame, width=45, font=("Arial", 10), state="readonly")
        self.contact_combo.pack(side="left", padx=(0, 10))
        
        load_contacts_btn = tk.Button(contact_frame, text="Load Contacts", command=self.load_contacts_from_db, bg="#E0E0E0", font=("Arial", 9))
        load_contacts_btn.pack(side="left")

        # --- Section 3: Date Filters ---
        tk.Label(root, text="3. Optional Date Filter (Leave blank for all time)", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(15, 2))
        
        date_frame = tk.Frame(root)
        date_frame.pack(fill="x", padx=20, pady=5)

        start_sub = tk.Frame(date_frame)
        start_sub.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(start_sub, text="From Date (YYYY-MM-DD):", font=("Arial", 9)).pack(anchor="w")
        self.start_date_entry = tk.Entry(start_sub, width=25, font=("Arial", 10))
        self.start_date_entry.pack(anchor="w", pady=2)

        end_sub = tk.Frame(date_frame)
        end_sub.pack(side="left", fill="x", expand=True)
        tk.Label(end_sub, text="To Date (YYYY-MM-DD):", font=("Arial", 9)).pack(anchor="w")
        self.end_date_entry = tk.Entry(end_sub, width=25, font=("Arial", 10))
        self.end_date_entry.pack(anchor="w", pady=2)

        # --- Section 4: Output Filename ---
        tk.Label(root, text="4. Name Your Saved Text File", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(15, 2))
        
        self.output_entry = tk.Entry(root, width=64, font=("Arial", 10))
        self.output_entry.pack(anchor="w", padx=20, pady=5)
        self.output_entry.insert(0, "my_messages.txt")

        # --- Export Action Button ---
        export_btn = tk.Button(root, text="Export Messages to Text File", command=self.run_export, bg="#007ACC", fg="white", font=("Arial", 11, "bold"), height=2, width=38)
        export_btn.pack(pady=20)

        # Try to auto-detect sms.db on startup
        self.auto_detect_db()

    def auto_detect_db(self):
        detected_path = self.find_default_sms_db()
        if detected_path:
            self.db_path_entry.delete(0, tk.END)
            self.db_path_entry.insert(0, detected_path)
            self.load_contacts_from_db()

    def find_default_sms_db(self):
        user_profile = os.environ.get('USERPROFILE', '')
        search_paths = [
            os.path.join(user_profile, "Apple", "MobileSync", "Backup"),
            os.path.join(user_profile, "AppData", "Roaming", "Apple Computer", "MobileSync", "Backup")
        ]
        for base_path in search_paths:
            if os.path.exists(base_path):
                pattern = os.path.join(base_path, "**", "Library", "SMS", "sms.db")
                matches = glob.glob(pattern, recursive=True)
                if matches:
                    matches.sort(key=os.path.getmtime, reverse=True)
                    return matches[0]
        return ""

    def browse_db(self):
        filename = filedialog.askopenfilename(
            title="Select sms.db file",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
        )
        if filename:
            self.db_path_entry.delete(0, tk.END)
            self.db_path_entry.insert(0, filename)
            self.load_contacts_from_db()

    def load_contacts_from_db(self):
        db_path = self.db_path_entry.get().strip()
        if not db_path or not os.path.exists(db_path):
            return
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT id FROM handle WHERE id IS NOT NULL ORDER BY id ASC;")
            handles = [row[0] for row in cursor.fetchall()]
            conn.close()

            if handles:
                self.contact_combo['values'] = handles
                self.contact_combo.current(0)
        except Exception:
            pass # Fail silently if database is locked or unreadable

    def toggle_target_state(self):
        if self.export_all_var.get():
            self.contact_combo.config(state="disabled")
        else:
            self.contact_combo.config(state="readonly")

    def run_export(self):
        db_path = self.db_path_entry.get().strip()
        export_all = self.export_all_var.get()
        target = self.contact_combo.get().strip()
        start_date = self.start_date_entry.get().strip()
        end_date = self.end_date_entry.get().strip()
        output_file = self.output_entry.get().strip()

        if not db_path or not os.path.exists(db_path):
            messagebox.showerror("Missing File", "Please select or find your iPhone backup sms.db file first.")
            return
        if not export_all and not target:
            messagebox.showerror("Missing Selection", "Please select a contact from the dropdown or check 'Export All'.")
            return
        if not output_file:
            output_file = "my_messages.txt"

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            query = """
                SELECT 
                    datetime(m.date / 1000000000 + 978307200, 'unixepoch', 'localtime') as msg_date,
                    m.is_from_me,
                    COALESCE(h.id, 'Unknown') as sender,
                    m.text
                FROM message m
                JOIN chat_message_join cm ON m.ROWID = cm.message_id
                JOIN chat c ON cm.chat_id = c.ROWID
                LEFT JOIN handle h ON m.handle_id = h.ROWID
                WHERE 1=1
            """
            params = []

            if not export_all:
                query += " AND h.id = ?"
                params.append(target)

            if start_date:
                query += " AND datetime(m.date / 1000000000 + 978307200, 'unixepoch', 'localtime') >= ?"
                params.append(f"{start_date} 00:00:00")

            if end_date:
                query += " AND datetime(m.date / 1000000000 + 978307200, 'unixepoch', 'localtime') <= ?"
                params.append(f"{end_date} 23:59:59")

            query += " ORDER BY m.date ASC;"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            if not rows:
                messagebox.showwarning("No Results Found", "No messages matched your selected contact or date range.")
                conn.close()
                return

            with open(output_file, "w", encoding="utf-8") as f:
                header_info = "ALL CHATS" if export_all else target
                f.write(f"=== MESSAGE EXPORT FOR: {header_info} ===\n")
                if start_date or end_date:
                    f.write(f"Date Range: {start_date or 'Beginning'} to {end_date or 'Present'}\n")
                f.write("\n" + "="*50 + "\n\n")

                for row in rows:
                    date, is_from_me, sender, text = row
                    speaker = "Me" if is_from_me == 1 else (sender or "Them")
                    if text:
                        f.write(f"[{date}] {speaker}: {text}\n")

            conn.close()
            messagebox.showinfo("Success!", f"Successfully exported {len(rows)} messages!\n\nSaved to:\n{os.path.abspath(output_file)}")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while reading the messages:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SMSExporterApp(root)
    root.mainloop()