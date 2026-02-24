import streamlit as st
import sqlite3
import pandas as pd
import requests
import re
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. KONFIGURASI & REFRESH 2 MENIT (120000 ms)
st.set_page_config(page_title="Nando Gold Sultan Final", page_icon="💎", layout="wide")
st_autorefresh(interval=120000, key="nando_final_v4")

# 2. FUNGSI DATABASE (FIXED ID)
def init_db():
    conn = sqlite3.connect("riwayat_emas.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS harga_emas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT, harga REAL)''')
    conn.commit()
    conn.close()

def save_to_db(harga):
    conn = sqlite3.connect("riwayat_emas.db")
    c = conn.cursor()
    waktu_sekarang = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO harga_emas (waktu, harga) VALUES (?, ?)", (waktu_sekarang, harga))
    conn.commit()
    conn.close()

def load_data_from_db():
    try:
        conn = sqlite3.connect("riwayat_emas.db")
        # WAJIB ambil id biar gak error KeyError
        df = pd.read_sql_query("SELECT id, waktu, harga FROM harga_emas ORDER BY id DESC LIMIT 50", conn)
        conn.close()
        return df.iloc[::-1]
    except:
        return pd.DataFrame(columns=['id', 'waktu', 'harga'])

# 3. SCRAPER AKURAT (ANTAM 1G)
def get_live_price():
    try:
        url = "https://www.hargaemas.com/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        # Regex diperkuat untuk ambil harga Antam (3 jutaan)
        pattern = r'Antam.*?([23]\.[0-9]{3}\.[0-9]{3})'
        match = re.search(pattern, response.text, re.DOTALL)
        if match:
            return float(match.group(1).replace(".", ""))
        return None
    except:
        return None

# --- JALANKAN PROSES ---
init_db()
live_price = get_live_price()
if live_price:
    save_to_db(live_price)
df_history = load_data_from_db()

# 4. DASHBOARD UTAMA
st.title("💎 Nando Gold Sultan: Ultimate Dashboard")
st.write(f"🕒 Status: Live | Update Otomatis Tiap 2 Menit | {datetime.now().strftime('%H:%M:%S')} WIB")

# --- SIDEBAR: KONTROL TOTAL ---
with st.sidebar:
    st.header("💰 Dompet Sultan")
    gram_punya = st.number_input("Jumlah Emas (Gram):", min_value=0.0, value=10.0, step=0.1)
    harga_beli_avg = st.number_input("Harga Beli Rata-rata (Rp):", min_value=0, value=2900000)
    
    st.divider()
    st.header("🎯 Pengaturan Target")
    nama_mimpi = st.text_input("Mimpi Lu Apa?", value="Beli Pajero / Dana Kawin")
    target_dana = st.number_input("Target Dana (Rp):", min_value=0, value=500000000)
    
    st.divider()
    if st.button("🗑️ Reset Riwayat DB"):
        conn = sqlite3.connect("riwayat_emas.db")
        conn.execute("DELETE FROM harga_emas")
        conn.commit()
        conn.close()
        st.rerun()

# --- METRIK UTAMA ---
c1, c2, c3 = st.columns(3)
if live_price:
    c1.metric("Harga Antam 1g", f"Rp {live_price:,.0f}")
    total_aset = gram_punya * live_price
    cuan = total_aset - (gram_punya * harga_beli_avg)
    c2.metric("Total Aset Lu", f"Rp {total_aset:,.0f}")
    c3.metric("Profit/Loss Total", f"Rp {cuan:,.0f}", f"{(cuan/(gram_punya*harga_beli_avg)*100):.2f}%")

st.divider()

# --- SEKSI TARGET & PREDIKSI (KEMBALINYA FITUR HILANG) ---
col_t1, col_t2 = st.columns(2)

with col_t1:
    st.subheader(f"🚀 Goal: {nama_mimpi}")
    progres = (total_aset / target_dana) * 100 if target_dana > 0 else 0
    st.progress(min(progres/100, 1.0))
    st.write(f"Progres: **{progres:.2f}%**")
    st.caption(f"Kurang **Rp {(target_dana - total_aset):,.0f}** lagi buat nyampe target. Jangan malas, Nan! 😂")

with col_t2:
    st.subheader("🤖 AI Advisor & Prediction")
    if not df_history.empty and len(df_history) > 5:
        ma_5 = df_history['harga'].tail(5).mean()
        ma_10 = df_history['harga'].tail(10).mean()
        prediksi_besok = ma_5 + (ma_5 - ma_10)
        
        st.write(f"Estimasi Harga Besok: **Rp {prediksi_besok:,.0f}**")
        if live_price < ma_5:
            st.success("Saran AI: **Waktunya Serok!**")
        else:
            st.warning("Saran AI: **Wait & See.**")
    else:
        st.info("AI butuh data lebih banyak (minimal 10 refresh) buat bikin prediksi.")

st.divider()

# --- SEKSI ZAKAT & PAJAK ---
st.subheader("⚖️ Kewajiban & Pajak")
cz1, cz2 = st.columns(2)
with cz1:
    if gram_punya >= 85:
        st.warning(f"Zakat Mal (2.5%): **Rp {total_aset * 0.025:,.0f}**")
    else:
        st.write("✅ Belum wajib Zakat Mal.")
with cz2:
    st.info(f"Estimasi Pajak Jual (0.45%): **Rp {total_aset * 0.0045:,.0f}**")

st.divider()

# --- GRAFIK ---
st.subheader("📈 Visualisasi Riwayat Harga")
st.line_chart(df_history.set_index('waktu')['harga'], color="#FFD700")