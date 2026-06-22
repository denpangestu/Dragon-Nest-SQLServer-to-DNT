import os
import struct
import pyodbc
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

# ==========================================
# KONFIGURASI DATABASE (Sesuaikan dengan milik Anda)
# ==========================================
DB_CONFIG = {
    'server': 'DESKTOP-57UNT30',
    'database': 'DragonNest_DNT',
    'driver': '{ODBC Driver 17 for SQL Server}'
    # Username dan password tidak lagi dibutuhkan
}

def get_connection():
    conn_str = (
        f"DRIVER={DB_CONFIG['driver']};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        "Trusted_Connection=yes;"          # <--- INI KUNCI UTAMANYA
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)

class DntExporterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dragon Nest SQL to DNT Converter")
        self.root.geometry("600x750")
        self.root.resizable(False, False)
        
        self.output_folder = tk.StringVar()
        self.tables = []
        
        self.setup_ui()
        self.load_tables()

    def setup_ui(self):
        # Frame untuk List Tabel
        frame_table = ttk.LabelFrame(self.root, text="1. Pilih Tabel yang ingin di-export", padding=10)
        frame_table.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.listbox = tk.Listbox(frame_table, selectmode=tk.MULTIPLE, height=10)
        scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Frame untuk Pilih Folder
        frame_folder = ttk.LabelFrame(self.root, text="2. Pilih Lokasi Penyimpanan File .dnt", padding=10)
        frame_folder.pack(fill="x", padx=10, pady=5)
        
        ttk.Entry(frame_folder, textvariable=self.output_folder, state="readonly").pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(frame_folder, text="Browse...", command=self.browse_folder).pack(side="right")
        
        # Frame untuk Progress dan Log
        frame_log = ttk.LabelFrame(self.root, text="3. Progress & Log", padding=10)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.progress = ttk.Progressbar(frame_log, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", pady=(0, 5))
        
        self.log_text = tk.Text(frame_log, height=8, state="disabled", bg="#f0f0f0")
        self.log_text.pack(fill="both", expand=True)
        
        # Tombol Export
        self.btn_export = ttk.Button(self.root, text="MULAI EXPORT KE DNT", command=self.start_export)
        self.btn_export.pack(fill="x", padx=10, pady=10, ipady=5)

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.root.update_idletasks()

    def load_tables(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            # Ambil daftar tabel yang memiliki metadata dnt
            cursor.execute("SELECT DISTINCT table_name FROM dnt_metadata ORDER BY table_name")
            self.tables = [row.table_name for row in cursor.fetchall()]
            conn.close()
            
            for table in self.tables:
                self.listbox.insert(tk.END, table)
            self.log(f"Berhasil memuat {len(self.tables)} tabel dari database.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Gagal terhubung ke database:\n{e}")

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Pilih Folder untuk menyimpan file .dnt")
        if folder:
            self.output_folder.set(folder)

    def start_export(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Peringatan", "Pilih minimal satu tabel!")
            return
            
        if not self.output_folder.get():
            messagebox.showwarning("Peringatan", "Pilih lokasi folder penyimpanan!")
            return

        selected_tables = [self.tables[i] for i in selected_indices]
        
        # Disable tombol agar tidak diklik ganda
        self.btn_export.config(state="disabled")
        self.progress["value"] = 0
        self.progress["maximum"] = len(selected_tables)
        
        # Jalankan di thread terpisah agar UI tidak freeze
        thread = threading.Thread(target=self.export_process, args=(selected_tables,))
        thread.start()

    def export_process(self, selected_tables):
        folder = self.output_folder.get()
        success_count = 0
        
        for idx, table_name in enumerate(selected_tables):
            try:
                self.root.after(0, self.log, f"Memproses tabel: {table_name}...")
                self.export_table_to_dnt(table_name, folder)
                success_count += 1
                self.root.after(0, self.log, f"[SUCCES] {table_name} berhasil di-export.")
            except Exception as e:
                self.root.after(0, self.log, f"[ERROR] {table_name}: {str(e)}")
            
            # Update progress bar
            self.root.after(0, self.update_progress, idx + 1)

        self.root.after(0, self.log, f"\nSelesai! {success_count}/{len(selected_tables)} file berhasil dibuat.")
        self.root.after(0, lambda: self.btn_export.config(state="normal"))
        self.root.after(0, lambda: messagebox.showinfo("Selesai", "Proses export selesai!"))

    def update_progress(self, value):
        self.progress["value"] = value

    def export_table_to_dnt(self, table_name, output_folder):
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Ambil Metadata
        cursor.execute("""
            SELECT file_name, version, reversion_len, column_name, column_type 
            FROM dnt_metadata 
            WHERE table_name = ? 
            ORDER BY column_order
        """, table_name)
        metadata = cursor.fetchall()
        
        if not metadata:
            raise Exception("Metadata tidak ditemukan di tabel dnt_metadata.")
            
        file_name = metadata[0].file_name
        version = metadata[0].version
        reversion_len = metadata[0].reversion_len
        columns = [{'name': m.column_name, 'type': m.column_type} for m in metadata]
        
        # 2. Ambil Data
        cursor.execute(f"SELECT * FROM [{table_name}]")
        rows = cursor.fetchall()
        
        # 3. Tulis ke File Biner
        output_path = os.path.join(output_folder, file_name)
        with open(output_path, 'wb') as f:
            # Tulis Header
            f.write(struct.pack('<hhhi', version, reversion_len, len(columns), len(rows)))
            
            # Tulis Definisi Kolom
            for col in columns:
                name_bytes = col['name'].encode('utf-8')
                f.write(struct.pack('<h', len(name_bytes)))
                f.write(name_bytes)
                f.write(struct.pack('<B', col['type']))
                
            # Tulis Data Baris
            for row in rows:
                # row[0] adalah RowID
                f.write(struct.pack('<I', row[0])) 
                
                # Loop kolom (row[1:] adalah data kolom)
                for i, col in enumerate(columns):
                    val = row[i+1]
                    col_type = col['type']
                    
                    # Handle Null/None
                    if val is None:
                        if col_type == 1: val = ''
                        else: val = 0
                        
                    if col_type == 0: # byte
                        f.write(struct.pack('<B', int(val)))
                    elif col_type == 1: # string
                        str_bytes = str(val).encode('utf-8')
                        f.write(struct.pack('<h', len(str_bytes)))
                        f.write(str_bytes)
                    elif col_type in [2, 3]: # bool/int
                        f.write(struct.pack('<i', int(val)))
                    elif col_type in [4, 5]: # float/numeric
                        # Convert Decimal/Float ke float 32-bit
                        f.write(struct.pack('<f', float(val)))
                        
            # Tulis Footer (END)
            f.write(struct.pack('<B', 0)) # szEND = 0 (kosong)
            
        conn.close()

if __name__ == '__main__':
    root = tk.Tk()
    app = DntExporterApp(root)
    root.mainloop()