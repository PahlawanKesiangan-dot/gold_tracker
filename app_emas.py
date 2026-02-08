import streamlit as st
import sqlite3
import pandas as pd
import requests
import re
from datetime import datetime

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Gold Tracker PRO", page_icon="📈", layout="wide")

# 2. Fungsi Ambil Data dari Database
def load_data():
    try:
        conn = sqlite3.connect("riwayat_emas.db")
        # Ambil data terbaru (limit 50 untuk grafik)
        df = pd.read_sql_query("SELECT waktu, harga FROM harga_emas ORDER BY id DESC LIMIT 50", conn)
        conn.close()
        # Balik data agar urutan waktu benar (kiri ke kanan)
        return df.iloc[::-1]
    except:
        return pd.DataFrame(columns=['waktu', 'harga'])

# 3. Fungsi Scraping Harga Terbaru
def get_live_price():
    try:
        url = "https://www.hargaemas.com/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        match = re.search(r'2\.9[0-9]{2}\.[0-9]{3}', response.text)
        return match.group(0) if match else "N/A"
    except:
        return "Error"

# --- TAMPILAN WEB ---
st.title("💰 Gold Pro Dashboard")
st.markdown("---")

# Row 1: Metrik Utama
live_price = get_live_price()
df_history = load_data()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Harga Antam Saat Ini", value=f"Rp {live_price}")
with col2:
    if not df_history.empty:
        last_price = df_history['harga'].iloc[-1]
        st.metric(label="Terakhir di Database", value=f"Rp {last_price:,}".replace(",", "."))
with col3:
    st.metric(label="Status Server", value="Online ✅")

st.markdown("---")

# Row 2: Grafik Interaktif & Tabel
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("📈 Tren Pergerakan Harga")
    if not df_history.empty:
        # Streamlit line chart sangat interaktif (bisa di-zoom)
        st.line_chart(data=df_history, x='waktu', y='harga')
    else:
        st.warning("Database kosong. Jalankan aplikasi desktop untuk mengisi data.")

with right_col:
    st.subheader("📜 10 Data Terakhir")
    if not df_history.empty:
        # Menampilkan tabel data yang bersih
        st.dataframe(df_history.tail(10), use_container_width=True)

# Footer
st.sidebar.header("Navigasi")
if st.sidebar.button("Refresh Data"):
    st.rerun()

st.sidebar.info("Tips: Buka halaman ini dari HP jika laptopmu berada dalam satu jaringan WiFi yang sama!")

st.sidebar.markdown("---")
st.sidebar.subheader("📥 Download Data")

# Mengonversi dataframe ke CSV
if not df_history.empty:
    csv = df_history.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="Download as CSV",
        data=csv,
        file_name='data_emas.csv',
        mime='text/csv',
    )