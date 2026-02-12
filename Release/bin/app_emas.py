import streamlit as st
import sqlite3
import pandas as pd
import requests
import re
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="Nando Gold Pro", page_icon="💰", layout="wide")

# (BAGIAN CSS BERMASALAH SUDAH DIHAPUS AGAR WARNA OTOMATIS NORMAL)

# 2. FUNGSI DATA
def load_data_from_db():
    try:
        conn = sqlite3.connect("riwayat_emas.db")
        df = pd.read_sql_query("SELECT waktu, harga FROM harga_emas ORDER BY id DESC LIMIT 50", conn)
        conn.close()
        return df.iloc[::-1]
    except:
        return pd.DataFrame(columns=['waktu', 'harga'])

def get_live_price():
    try:
        url = "https://www.hargaemas.com/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        match = re.search(r'2\.9[0-9]{2}\.[0-9]{3}', response.text)
        return match.group(0) if match else "N/A"
    except:
        return "Error"

# 3. TAMPILAN DASHBOARD
st.title("💰 Nando Gold Pro Dashboard")
st.write(f"Update: {datetime.now().strftime('%H:%M:%S')}")
st.divider()

# Ambil data
live_price_str = get_live_price()
df_history = load_data_from_db()

# --- METRIK UTAMA ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Harga Web Sekarang", f"Rp {live_price_str}")
with col2:
    if not df_history.empty:
        last_price = df_history['harga'].iloc[-1]
        st.metric("Harga Terakhir di DB", f"Rp {last_price:,}".replace(",", "."))
with col3:
    st.metric("Status Sistem", "Online ✅")

st.divider()

# --- ANALISIS CERDAS ---
if not df_history.empty:
    rata_rata = df_history['harga'].mean()
    harga_terakhir = df_history['harga'].iloc[-1]
    
    st.subheader("💡 Analisis Rekomendasi")
    c1, c2 = st.columns(2)
    c1.info(f"**Harga Rata-rata Riwayat:** Rp {rata_rata:,.0f}".replace(",", "."))
    
    if harga_terakhir < rata_rata:
        c2.success("✅ **Saran:** Harga di bawah rata-rata. Bagus untuk **BELI**.")
    else:
        c2.warning("⚠️ **Saran:** Harga di atas rata-rata. Lebih baik **TUNGGU**.")

st.divider()

# --- GRAFIK & TABEL ---
left_col, right_col = st.columns([2, 1])
with left_col:
    st.subheader("📈 Tren Harga")
    if not df_history.empty:
        st.line_chart(data=df_history, x='waktu', y='harga')
with right_col:
    st.subheader("📜 Riwayat")
    if not df_history.empty:
        st.dataframe(df_history.sort_values(by='waktu', ascending=False), use_container_width=True)

# --- SIDEBAR ---
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

if not df_history.empty:
    csv = df_history.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 Download CSV", data=csv, file_name='data_emas.csv')