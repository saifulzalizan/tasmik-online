import streamlit as st
import datetime
import pytz
import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials

# 1. Konfigurasi Fail Semak Keselamatan Google Sheets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def sambung_database():
    try:
        # Kod Automatik: Minta Python cari jalan pintas folder semasa fail tasmik.py ini berada
        folder_semasa = os.path.dirname(os.path.abspath(__file__))
        path_credentials = os.path.join(folder_semasa, "credentials.json")
        
        # Sila semak jika fail wujud menggunakan nama alternatif jika cubaan pertama gagal
        if not os.path.exists(path_credentials):
            path_credentials = os.path.join(folder_semasa, "credentials.json.json")

        # Membaca fail credentials menggunakan path mutlak
        creds = ServiceAccountCredentials.from_json_keyfile_name(path_credentials, scope)
        client = gspread.authorize(creds)
        
        # Membuka Google Sheets bernama 'Rekod Tasmik Online'
        sheet = client.open("Rekod Tasmik Online").worksheet("Rekod_Tasmik")
        return sheet
    except Exception as e:
        # Menampilkan ralat sebenar daripada sistem Google untuk tujuan 'debugging'
        st.error(f"⚠️ Ralat Sistem Google: {e}")
        return None

# Panggil fungsi sambungan database
db_sheet = sambung_database()

# 2. Tetapan Paparan Aplikasi (Mobile-Friendly)
st.set_page_config(page_title="Sistem Tasmik Online", layout="centered")
st.title("📖 Rekod Tasmik Murid")
st.write("Sistem Perekodan Google Sheets Secara Live")
st.markdown("---")

# Zon Waktu Malaysia untuk simpanan masa yang tepat
kl_tz = pytz.timezone("Asia/Kuala_Lumpur")
waktu_sekarang = datetime.datetime.now(kl_tz)

# 3. Borang Input Guru
kolum1, kolum2 = st.columns(2)
with kolum1:
    kelas = st.selectbox("Kelas", ["1B", "1A", "2B"])
with kolum2:
    minggu = st.number_input("Minggu Ke-", min_value=1, max_value=52, value=3)

# Senarai Murid Statik
senarai_murid = {
    "1B": ["Daud", "Fatima", "Ali", "Zubair"],
    "1A": ["Aisha", "Omar", "Khadijah"],
    "2B": ["Muaz", "Hamzah", "Bilal"]
}

nama_pelajar = st.selectbox("Nama Pelajar", senarai_murid.get(kelas, []))

st.markdown("### Kemas Kini Bacaan Baru")

iqra = st.selectbox("Peringkat Bacaan", ["Iqra' 1", "Iqra' 2", "Iqra' 3", "Iqra' 4", "Iqra' 5", "Iqra' 6", "Al-Quran"])
muka_surat = st.number_input("Muka Surat", min_value=1, max_value=604, value=1)
sesi = st.radio("Sesi Bacaan", ["Tasmik Kelas", "Kelas Tambahan", "Ujian"], horizontal=True)

# Tarikh lalai hari ini mengikut zon masa Malaysia
tarikh_pilihan = st.date_input("Tarikh Rekod", waktu_sekarang.date())

st.markdown("---")

# 4. Proses Simpan Data Bila Butang Ditekan
if st.button("💾 Simpan Rekod Ke Google Sheets", use_container_width=True):
    if db_sheet is not None:
        with st.spinner("Sedang menyimpan data secara online..."):
            try:
                # Sediakan susunan data mengikut ketetapan kolum Google Sheets
                data_baru = [
                    str(tarikh_pilihan),
                    int(minggu),
                    kelas,
                    nama_pelajar,
                    iqra,
                    int(muka_surat),
                    sesi,
                    waktu_sekarang.strftime("%Y-%m-%d %H:%M:%S") # Masa kemas kini tepat
                ]
                
                # Masukkan data ke baris paling bawah dalam Google Sheets
                db_sheet.append_row(data_baru)
                
                st.success(f"🎉 Rekod bagi {nama_pelajar} (Kelas {kelas}) berjaya disimpan!")
                st.balloons()
                
            except Exception as error:
                st.error(f"Ralat semasa menghantar data: {error}")
    else:
        st.warning("Sambungan gagal. Sila semak mesej ralat kuning/merah di bahagian atas skrin untuk melihat puncanya.")