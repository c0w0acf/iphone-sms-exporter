import sqlite3
import os
import glob
import datetime
import threading
import time
import subprocess
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class AllInOneSMSExporter:
    def __init__(self, root):
        self.root = root
        self.root.title("iPhone Message Exporter - AIO Edition")
        self.root.geometry("600x640")
        self.root.resizable(False, False)

        self.last_detected_path = ""
        self.is_monitoring = True

        # --- Header Banner / Status ---
        self.status_frame = tk.Frame(root, bg="#007ACC", height=50)
        self.status_frame.pack(fill="x", padx=0, pady=0)
        self.status_frame.pack_propagate(False)

        self.status_label = tk.Label(
            self.status_frame, 
            text="Status: Scanning for iPhone backups...", 
            bg="#007ACC", 
            fg="white", 
            font=("Arial", 11, "bold")
        )
        self.status_label.pack(expand=True)

        # --- Step 1: Backup Control ---
        tk.Label(root, text="Step 1: Create or Locate iPhone Backup", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(15, 2))
        tk.Label(root, text="Launch Apple Devices, select a folder, or pick your database file directly:", font=("Arial", 9), fg="#555").pack(anchor="w", padx=20)
        
        launch_frame = tk.Frame(root)
        launch_frame.pack(fill="x", padx=20, pady=8)
        
        launch_btn = tk.Button(launch_frame, text="Open Apple Devices", command=self.open_apple_devices, bg="#E0E0E0", font=("Arial", 9, "bold"), width=16, height=2)
        launch_btn.pack(side="left", padx=(0, 4))

        browse_folder_btn = tk.Button(launch_frame, text="Select Folder...", command=self.browse_backup_folder, bg="#E0E0E0", font=("Arial", 9, "bold"), width=15, height=2)
        browse_folder_btn.pack(side="left", padx=(0, 4))

        browse_file_btn = tk.Button(launch_frame, text="Select .db File...", command=self.browse_database_file_directly, bg="#E0E0E0", font=("Arial", 9, "bold"), width=15, height=2)
        browse_file_btn.pack(side="left")

        # --- Step 2: Contact Selection ---
        tk.Label(root, text="Step 2: Choose Conversation", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(15, 2))
        
        self.export_all_var = tk.BooleanVar(value=False)
        self.export_all_chk = tk.Checkbutton(
            root, text="Export every conversation on my phone (Export All)", 
            variable=self.export_all_var, font=("Arial", 10), command=self.toggle_target_state
        )
        self.export_all_chk.pack(anchor="w", padx=20, pady=(2, 5))

        tk.Label(root, text="Or select a specific person/number:", font=("Arial", 9), fg="#555").pack(anchor="w", padx=20)
        
        contact_frame = tk.Frame(root)
        contact_frame.pack(fill="x", padx=20, pady=5)

        self.contact_combo = ttk.Combobox(contact_frame, width=50, font=("Arial", 10), state="readonly")
        self.contact_combo.pack(side="left", padx=(0, 10))

        # --- Step 3: Date Filters (Optional) ---
        tk.Label(root, text="Step 3: Optional Date Filter (Leave blank for all time)", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(15, 2))
        
        date_frame = tk.Frame(root)
        date_frame.pack(fill="x", padx=20, pady=5)

        start_sub = tk.Frame(date_frame)
        start_sub.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(start_sub, text="From Date (YYYY-MM-DD):", font=("Arial", 9)).pack(anchor="w")
        self.start_date_entry = tk.Entry(start_sub, width=22, font=("Arial", 10))
        self.start_date_entry.pack(anchor="w", pady=2)

        end_sub = tk.Frame(date_frame)
        end_sub.pack(side="left", fill="x", expand=True)
        tk.Label(end_sub, text="To Date (YYYY-MM-DD):", font=("Arial", 9)).pack(anchor="w")
        self.end_date_entry = tk.Entry(end_sub, width=22, font=("Arial", 10))
        self.end_date_entry.pack(anchor="w", pady=2)

        # --- Step 4: Output Filename ---
        tk.Label(root, text="Step 4: Output File Name", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(15, 2))
        
        self.output_entry = tk.Entry(root, width=64, font=("Arial", 10))
        self.output_entry.pack(anchor="w", padx=20, pady=5)
        self.output_entry.insert(0, "my_messages.txt")

        # --- Big Action Export Button ---
        export_btn = tk.Button(root, text="Export Messages to Text File", command=self.run_export, bg="#28A745", fg="white", font=("Arial", 12, "bold"), height=2, width=42)
        export_btn.pack(pady=15)

        # Start background thread to watch for backups automatically
        self.monitor_thread = threading.Thread(target=self.background_backup_watcher, daemon=True)
        self.monitor_thread.start()

    def open_apple_devices(self):
        try:
            tasklist_out = subprocess.check_output('tasklist /FI "IMAGENAME eq AppleDevices.exe"', shell=True).decode(errors='ignore')
            if "AppleDevices.exe" in tasklist_out:
                messagebox.showinfo("Already Running", "The Apple Devices app is already open and running!")
                return

            check_cmd = 'powershell -Command "Get-AppxPackage -Name *AppleDevices*"'
            pkg_output = subprocess.check_output(check_cmd, shell=True).decode(errors='ignore').strip()

            if not pkg_output:
                if messagebox.askyesno("App Not Found", "The 'Apple Devices' app is not installed on this PC.\n\nWould you like to open the Microsoft Store to install it now?"):
                    subprocess.Popen("start ms-windows-store://pdp/?ProductId=9np83lwlpz9k", shell=True)
                return

            subprocess.Popen("start apple-devices:", shell=True)
            
        except Exception as e:
            try:
                subprocess.Popen("start apple-devices:", shell=True)
            except Exception as ex:
                messagebox.showerror("Error", f"Could not launch Apple Devices app automatically:\n{str(ex)}")

    def resolve_sms_db_from_backup(self, backup_dir):
        manifest_path = os.path.join(backup_dir, "Manifest.db")
        if not os.path.exists(manifest_path):
            manifests = glob.glob(os.path.join(backup_dir, "**", "Manifest.db"), recursive=True)
            if manifests:
                manifests.sort(key=os.path.getmtime, reverse=True)
                manifest_path = manifests[0]
            else:
                return ""

        try:
            conn = sqlite3.connect(manifest_path)
            cursor = conn.cursor()
            cursor.execute("SELECT fileID FROM Files WHERE relativePath LIKE '%sms.db'")
            row = cursor.fetchone()
            conn.close()
            if row:
                file_id = row[0]
                target_file = os.path.join(os.path.dirname(manifest_path), file_id)
                if os.path.exists(target_file):
                    return target_file
        except Exception:
            pass
        return ""

    def browse_backup_folder(self):
        user_profile = os.environ.get('USERPROFILE', '')
        default_path = os.path.join(user_profile, "Apple", "MobileSync", "Backup")
        if not os.path.exists(default_path):
            default_path = user_profile

        folder_selected = filedialog.askdirectory(
            title="Select your iPhone Backup Folder",
            initialdir=default_path
        )
        
        db_path = ""
        if folder_selected:
            db_path = self.resolve_sms_db_from_backup(folder_selected)
            
            if not db_path:
                subfolders = [os.path.join(folder_selected, d) for d in os.listdir(folder_selected) if os.path.isdir(os.path.join(folder_selected, d))]
                for sub in subfolders:
                    db_path = self.resolve_sms_db_from_backup(sub)
                    if db_path:
                        break

            if not db_path:
                matches = glob.glob(os.path.join(folder_selected, "**", "sms.db"), recursive=True)
                if matches:
                    db_path = matches[0]

            if db_path and os.path.exists(db_path):
                self.last_detected_path = db_path
                self.on_backup_detected(db_path)
            else:
                messagebox.showwarning("Database Not Found", "Could not resolve a valid message database from that folder. Try using 'Select .db File...' to point directly to your database file.")

    def browse_database_file_directly(self):
        user_profile = os.environ.get('USERPROFILE', '')
        default_path = os.path.join(user_profile, "Apple", "MobileSync", "Backup")
        if not os.path.exists(default_path):
            default_path = user_profile

        filename = filedialog.askopenfilename(
            title="Select your iPhone Message Database File (*.db)",
            initialdir=default_path,
            filetypes=[("Database Files", "*.db"), ("All Files", "*.*")]
        )
        if filename:
            self.last_detected_path = filename
            self.on_backup_detected(filename)

    def find_newest_sms_db(self):
        user_profile = os.environ.get('USERPROFILE', '')
        search_paths = [
            os.path.join(user_profile, "Apple", "MobileSync", "Backup"),
            os.path.join(user_profile, "AppData", "Roaming", "Apple Computer", "MobileSync", "Backup")
        ]
        for base_path in search_paths:
            if os.path.exists(base_path):
                device_folders = [os.path.join(base_path, d) for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
                if device_folders:
                    device_folders.sort(key=os.path.getmtime, reverse=True)
                    for folder in device_folders:
                        db_path = self.resolve_sms_db_from_backup(folder)
                        if db_path:
                            return db_path
        return ""

    def background_backup_watcher(self):
        while self.is_monitoring:
            db_path = self.find_newest_sms_db()
            if db_path and db_path != self.last_detected_path:
                self.last_detected_path = db_path
                self.root.after(0, lambda: self.on_backup_detected(db_path))
            time.sleep(3)

    def on_backup_detected(self, db_path):
        mtime = os.path.getmtime(db_path)
        mod_time_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        self.status_label.config(text=f"Status: Ready! Backup loaded ({mod_time_str})")
        self.status_frame.config(bg="#28A745")
        self.status_label.config(bg="#28A745")
        
        self.load_contacts_from_db(db_path)

    def load_contacts_from_db(self, db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT id FROM handle WHERE id IS NOT NULL ORDER BY id ASC;")
            handles = [row[0] for row in cursor.fetchall()]
            conn.close()

            if handles:
                self.contact_combo['values'] = handles
                self.contact_combo.current(0)
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not read contacts from database.\nMake sure the file is a valid unencrypted chat database:\n{str(e)}")

    def toggle_target_state(self):
        if self.export_all_var.get():
            self.contact_combo.config(state="disabled")
        else:
            self.contact_combo.config(state="readonly")

    def run_export(self):
        db_path = self.last_detected_path
        if not db_path or not os.path.exists(db_path):
            messagebox.showerror("No Database Selected", "Please select your backup folder or use 'Select .db File...' to point directly to your message file.")
            return

        export_all = self.export_all_var.get()
        target = self.contact_combo.get().strip()
        start_date = self.start_date_entry.get().strip()
        end_date = self.end_date_entry.get().strip()
        output_file = self.output_entry.get().strip()

        if not export_all and not target:
            messagebox.showerror("Selection Missing", "Please select a contact from the dropdown or check 'Export All'.")
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
                query += " AND datetime(m.date / 1000000000 + 978307200, 'unixepoch', 'localtime') >= ?" 

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
    try:
        root = tk.Tk()
        app = AllInOneSMSExporter(root)
        root.mainloop()
    except Exception as e:
        error_details = traceback.format_exc()
        try:
            root_err = tk.Tk()
            root_err.withdraw()
            messagebox.showerror("Startup Error", f"The application failed to start:\n\n{error_details}")
        except Exception:
            print(error_details)
            input("Press Enter to exit...")