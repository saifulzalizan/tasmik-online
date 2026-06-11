import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz
import json

# Setup halaman Streamlit
st.set_page_config(page_title="Rekod Tasmik Murid", layout="centered")

# Pautan Skop Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def sambung_database():
    try:
        # Mengambil data string JSON terus dari Streamlit Secrets (Lebih Selamat)
        creds_str = st.secrets["gspread_creds"]
        
        # Menukar teks string kepada format Python dictionary (JSON)
        info = json.loads(creds_str)
            
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        client = gspread.authorize(creds)
        
        # Membuka Google Sheets bernama 'Rekod Tasmik Online'
        sheet = client.open("Rekod Tasmik Online").worksheet("Rekod_Tasmik")
        return sheet
    except Exception as e:
        st.error(f"⚠️ Ralat Sistem Google Cloud: {e}")
        return None

# Panggil fungsi sambungan database
sheet = sambung_database()

st.title("📋 Sistem Rekod Tasmik Murid")
st.write("Sila isi maklumat bacaan murid di bawah. Data akan disimpan terus ke Google Sheets.")

if sheet is None:
    st.warning("Sambungan ke pangkalan data gagal. Sila semak tetapan Streamlit Secrets anda.")
else:
    # --- Borang Input Murid ---
    with st.form(key='borang_tasmik', clear_on_submit=True):
        nama_murid = st.text_input("Nama Murid:")
        
        pilihan_bacaan = st.selectbox("Jenis Bacaan:", ["Al-Quran", "Iqra'"])
        
        # Input Surah/Iqra & Ayat/Halaman berdasarkan pilihan jenis bacaan
        if pilihan_bacaan == "Al-Quran":
            surah_bacaan = st.text_input("Nama Surah:", placeholder="Contoh: Al-Baqarah")
            ayat_bacaan = st.text_input("Ayat Ke:", placeholder="Contoh: 1-10")
        else:
            surah_bacaan = st.selectbox("Iqra' Jilid:", ["Iqra' 1", "Iqra' 2", "Iqra' 3", "Iqra' 4", "Iqra' 5", "Iqra' 6"])
            ayat_bacaan = st.text_input("Muka Surat:", placeholder="Contoh: 15")
            
        status_bacaan = st.radio("Status Kelancaran:", ["Lancar (Boleh Alih)", "Kurang Lancar (Ulang)"])
        catatan = st.text_area("Catatan Tambahan (Jika ada):", placeholder="Contoh: Jaga hukum dengung")
        
        butang_hantar = st.form_submit_button(label="💾 Simpan Rekod Ke Google Sheets")

    # --- Proses Simpan Data Selesai Klik Butang ---
    if butang_hantar:
        if nama_murid == "" or surah_bacaan == "" or ayat_bacaan == "":
            st.error("⚠️ Sila pastikan Nama Murid, Surah/Iqra' dan Ayat/Muka Surat telah diisi!")
        else:
            with st.spinner("Sedang menyimpan data..."):
                try:
                    # Set zon masa peranti kepada Asia/Kuala_Lumpur
                    zon_masa = pytz.timezone('Asia/Kuala_Lumpur')
                    masa_sekarang = datetime.datetime.now(zon_masa).strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Susun data mengikut turutan kolum di Google Sheets
                    data_baru = [masa_sekarang, nama_murid, pilihan_bacaan, surah_bacaan, ayat_bacaan, status_bacaan, catatan]
                    
                    # Masukkan data ke baris paling bawah di Google Sheets
                    sheet.append_row(data_baru)
                    
                    st.success(f"🎉 Rekod tasmik bagi {nama_murid} telah berjaya disimpan!")
                    st.balloons()
                except Exception as ralat:
                    st.error(f"❌ Gagal menyimpan data. Ralat: {ralat}")
