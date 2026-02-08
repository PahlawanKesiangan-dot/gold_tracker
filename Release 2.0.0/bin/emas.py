import tkinter as tk
from tkinter import messagebox
import requests
import re
import sqlite3
import pandas as pd
from datetime import datetime

# ==========================================
# 1. LOGIKA DATABASE
# ==========================================
def inisialisasi_db():
    conn = sqlite3.connect("riwayat_emas.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS harga_emas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            waktu TEXT,
            harga INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def simpan_ke_db(harga_angka):
    conn = sqlite3.connect("riwayat_emas.db")
    cursor = conn.cursor()
    
    # Ambil harga terakhir untuk cek duplikat
    cursor.execute("SELECT harga FROM harga_emas ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    
    # Hanya simpan jika harga berbeda atau database masih kosong
    if row is None or row[0] != harga_angka:
        waktu_skrg = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO harga_emas (waktu, harga) VALUES (?, ?)", (waktu_skrg, harga_angka))
        conn.commit()
        label_status.config(text="✅ Data Baru Disimpan", fg="green")
    else:
        label_status.config(text="ℹ️ Harga Masih Sama", fg="orange")
        
    conn.close()

def hapus_riwayat():
    tanya = messagebox.askyesno("Konfirmasi", "Hapus SEMUA riwayat permanen?")
    if tanya:
        conn = sqlite3.connect("riwayat_emas.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM harga_emas")
        conn.commit()
        conn.close()
        perbarui_tampilan_riwayat()
        label_status.config(text="🗑️ Riwayat Dikosongkan", fg="red")

# ==========================================
# 2. LOGIKA EKSPOR & FITUR
# ==========================================
def ekspor_excel():
    try:
        conn = sqlite3.connect("riwayat_emas.db")
        df = pd.read_sql_query("SELECT waktu, harga FROM harga_emas", conn)
        conn.close()

        if df.empty:
            messagebox.showwarning("Kosong", "Database masih kosong!")
            return

        nama_file = f"Laporan_Emas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        df.to_excel(nama_file, index=False)
        messagebox.showinfo("Berhasil", f"File disimpan sebagai:\n{nama_file}")
    except Exception as e:
        messagebox.showerror("Error", f"Gagal Ekspor: {e}")

def perbarui_jam():
    label_jam.config(text=f"Jam: {datetime.now().strftime('%H:%M:%S')}")
    root.after(1000, perbarui_jam)

def perbarui_tampilan_riwayat():
    listbox_riwayat.delete(0, tk.END)
    conn = sqlite3.connect("riwayat_emas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT waktu, harga FROM harga_emas ORDER BY id DESC")
    for r in cursor.fetchall():
        harga_fmt = "{:,}".format(r[1]).replace(",", ".")
        listbox_riwayat.insert(tk.END, f" {r[0]} | Rp {harga_fmt}")
    conn.close()

def ambil_harga_utama():
    label_status.config(text="🤖 Menghubungi Server...", fg="blue")
    root.update()
    try:
        url = "https://www.hargaemas.com/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        match = re.search(r'2\.9[0-9]{2}\.[0-9]{3}', response.text)
        
        if match:
            harga_teks = match.group(0)
            harga_angka = int(harga_teks.replace(".", ""))
            
            simpan_ke_db(harga_angka)
            label_harga.config(text=f"Rp {harga_teks}")
            perbarui_tampilan_riwayat()
        else:
            label_status.config(text="⚠️ Harga 2.9jt tidak terbaca", fg="orange")
    except:
        label_status.config(text="❌ Koneksi Terputus", fg="red")
    
    # Auto-update tiap 5 menit
    root.after(300000, ambil_harga_utama)

import matplotlib.pyplot as plt # Library Grafik

def tampilkan_grafik():
    try:
        # 1. Ambil data dari database
        conn = sqlite3.connect("riwayat_emas.db")
        # Kita ambil 20 data terakhir saja agar grafik tidak terlalu sesak
        df = pd.read_sql_query("SELECT waktu, harga FROM harga_emas ORDER BY id DESC LIMIT 20", conn)
        conn.close()

        if df.empty:
            messagebox.showwarning("Kosong", "Belum ada data untuk dibuat grafik!")
            return

        # 2. Balik urutan agar data lama di kiri, data baru di kanan
        df = df.iloc[::-1]

        # 3. Proses data waktu agar lebih cantik (ambil jamnya saja)
        df['waktu'] = pd.to_datetime(df['waktu']).dt.strftime('%H:%M')

        # 4. Buat Grafik
        plt.figure(figsize=(10, 5))
        plt.plot(df['waktu'], df['harga'], marker='o', linestyle='-', color='#B8860B', linewidth=2)
        
        # Tambahkan judul dan label
        plt.title("Tren Harga Emas Antam (20 Update Terakhir)", fontsize=14, fontweight='bold')
        plt.xlabel("Waktu Update", fontsize=10)
        plt.ylabel("Harga (Rp)", fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45) # Biar tulisan jam tidak tabrakan
        plt.tight_layout()

        # 5. Tampilkan jendela grafik
        plt.show()

    except Exception as e:
        messagebox.showerror("Error Grafik", f"Gagal memuat grafik: {e}")

# ==========================================
# 3. ANTARMUKA GUI (USER INTERFACE)
# ==========================================
root = tk.Tk()
root.title("Nando Gold Tracker PRO v6.5")
root.geometry("450x600")
root.resizable(False, False)
root.configure(bg="#f0f0f0")

inisialisasi_db()

# --- HEADER ---
tk.Label(root, text="HARGA EMAS ANTAM (1 GRAM)", font=("Arial", 11, "bold"), bg="#f0f0f0").pack(pady=10)
label_harga = tk.Label(root, text="Rp -,---,---", font=("Arial", 32, "bold"), fg="#B8860B", bg="#f0f0f0")
label_harga.pack()

# --- RIWAYAT SCROLLABLE ---
tk.Label(root, text="Riwayat Update (Tanpa Batas):", font=("Arial", 9, "italic"), bg="#f0f0f0").pack(pady=(20,0))
frame_list = tk.Frame(root)
frame_list.pack(pady=5)

scrollbar = tk.Scrollbar(frame_list)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

listbox_riwayat = tk.Listbox(frame_list, font=("Courier New", 10), width=45, height=10, yscrollcommand=scrollbar.set)
listbox_riwayat.pack(side=tk.LEFT)
scrollbar.config(command=listbox_riwayat.yview)

# --- TOMBOL AKSI ---
btn_frame = tk.Frame(root, bg="#f0f0f0")
btn_frame.pack(pady=20)

# Tambahkan tombol ini di bawah tombol HAPUS SEMUA
tk.Button(btn_frame, text="TAMPILKAN GRAFIK TREN", command=tampilkan_grafik, 
          bg="#8e44ad", fg="white", width=38, font=("Arial", 9, "bold")).grid(row=2, column=0, columnspan=2, pady=5)
tk.Button(btn_frame, text="UPDATE MANUAL", command=ambil_harga_utama, bg="#27ae60", fg="white", width=18, font=("Arial", 9, "bold")).grid(row=0, column=0, padx=5, pady=5)
tk.Button(btn_frame, text="EKSPOR EXCEL", command=ekspor_excel, bg="#2980b9", fg="white", width=18, font=("Arial", 9, "bold")).grid(row=0, column=1, padx=5, pady=5)
tk.Button(btn_frame, text="HAPUS SEMUA", command=hapus_riwayat, bg="#c0392b", fg="white", width=38, font=("Arial", 9, "bold")).grid(row=1, column=0, columnspan=2, pady=5)

# --- STATUS BAR ---
status_frame = tk.Frame(root, relief="sunken", bd=1)
status_frame.pack(side="bottom", fill="x")

label_status = tk.Label(status_frame, text="Sistem Siap", font=("Arial", 8, "italic"))
label_status.pack(side="left", padx=5)

label_jam = tk.Label(status_frame, text="Jam: --:--:--", font=("Courier New", 9, "bold"))
label_jam.pack(side="right", padx=5)

# --- JALANKAN ---
perbarui_jam()
perbarui_tampilan_riwayat()
root.after(1000, ambil_harga_utama)

root.mainloop()