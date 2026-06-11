import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz
import json

# Setup halaman Streamlit
st.set_page_config(page_title="Sistem Rekod Tasmik", layout="centered")

# Pautan Skop Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def sambung_database():
    try:
        # Mengambil kunci keselamatan dari Streamlit Secrets
        creds_str = st.secrets["gspread_creds"]
        info = json.loads(creds_str)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        client = gspread.authorize(creds)
        
        # Membuka fail Google Sheets induk
        doc = client.open("Rekod Tasmik Online")
        
        # Tab 1: Tempat simpan rekod tasmik
        sheet_rekod = doc.worksheet("Rekod_Tasmik")
        
        # Tab 2: Sumber data (Kelas & Nama)
        sheet_data = doc.worksheet("Senarai_Murid")
        
        return sheet_rekod, sheet_data
    except Exception as e:
        st.error(f"⚠️ Ralat Pangkalan Data: {e}")
        return None, None

# Panggil fungsi sambungan database
sheet_rekod, sheet_data = sambung_database()

st.title("📋 Sistem Rekod Tasmik Murid")
st.write("Sila isi rekod bacaan murid menggunakan pilihan drop-down di bawah.")

if sheet_rekod is None or sheet_data is None:
    st.warning("Gagal menyambung ke Google Sheets. Sila semak tetapan Secrets atau nama tab Sheets anda.")
else:
    # --- MEMBACA DATA KELAS & NAMA DARI TAB 'Senarai_Murid' ---
    @st.cache_data(ttl=600)
    def ambil_data_murid():
        try:
            semua_baris = sheet_data.get_all_records()
            peta_kelas_murid = {}
            for baris in semua_baris:
                kelas = str(baris.get('Kelas', '')).strip()
                nama = str(baris.get('Nama', '')).strip()
                if kelas and nama:
                    if kelas not in peta_kelas_murid:
                        peta_kelas_murid[kelas] = []
                    peta_kelas_murid[kelas].append(nama)
            return peta_kelas_murid, sorted(list(peta_kelas_murid.keys()))
        except Exception as e:
            st.error(f"Gagal membaca data murid: {e}")
            return {}, []

    peta_kelas_murid, senarai_kelas = ambil_data_murid()

    if not senarai_kelas:
        st.error("⚠️ Tiada data kelas ditemui di dalam tab 'Senarai_Murid'!")
    else:
        # --- PENAPIS KELAS (DI LUAR BORANG) ---
        pilihan_kelas = st.selectbox("📁 Kolum 1: Pilih Kelas", senarai_kelas)
        murid_dalam_kelas = sorted(peta_kelas_murid.get(pilihan_kelas, []))

        # --- SET PILIHAN DROP-DOWN SEPERTI KEHENDAK ANDA ---
        
        # Drop-down Tarikh: Menyediakan tarikh hari ini, semalam, dan kelmarin
        zon_masa = pytz.timezone('Asia/Kuala_Lumpur')
        hari_ini = datetime.datetime.now(zon_masa)
        senarai_tarikh = [
            hari_ini.strftime("%Y-%m-%d"),
            (hari_ini - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            (hari_ini - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        ]
        
        # Drop-down Minggu: Minggu 1 hingga Minggu 45
        senarai_minggu = [f"Minggu {i}" for i in range(1, 46)]
        
        # Drop-down Tahap Bacaan
        senarai_bacaan = ["Iqra' 1", "Iqra' 2", "Iqra' 3", "Iqra' 4", "Iqra' 5", "Iqra' 6", "Al-Quran", "Telah Khatam"]
        
        # Drop-down Muka Surat: Nombor 1 hingga 100 (Boleh ditambah jika perlu)
        senarai_muka_surat = [f"Muka Surat {i}" for i in range(1, 101)]

        # --- BORANG INPUT UTAMA ---
        with st.form(key='borang_tasmik_baru', clear_on_submit=True):
            
            pilihan_nama = st.selectbox("👤 Kolum 2: Nama Pelajar", murid_dalam_kelas)
            
            pilihan_tarikh = st.selectbox("📅 Kolum 3: Tarikh Bacaan", senarai_tarikh)
            
            pilihan_minggu = st.selectbox("📆 Kolum 4: Minggu", senarai_minggu)
            
            pilihan_tahap = st.selectbox("📖 Kolum 5: Pilihan Bacaan", senarai_bacaan)
            
            pilihan_ms = st.selectbox("📄 Kolum 6: Muka Surat Bacaan", senarai_muka_surat)
            
            butang_simpan = st.form_submit_button(label="💾 Simpan Rekod")

        # --- PROSES SIMPAN DATA KE GOOGLE SHEETS ---
        if butang_simpan:
            if not pilihan_nama:
                st.error("⚠️ Sila pastikan nama pelajar telah dipilih!")
            else:
                with st.spinner("Sedang menyimpan ke Google Sheets..."):
                    try:
                        # Susun data TEPAT mengikut turutan kolum kehendak anda
                        data_baru = [
                            pilihan_kelas,   # Kolum 1
                            pilihan_nama,    # Kolum 2
                            pilihan_tarikh,  # Kolum 3
                            pilihan_minggu,  # Kolum 4
                            pilihan_tahap,   # Kolum 5
                            pilihan_ms       # Kolum 6
                        ]
                        
                        # Simpan ke tab Rekod_Tasmik
                        sheet_rekod.append_row(data_baru)
                        
                        st.success(f"🎉 Rekod bagi {pilihan_nama} ({pilihan_kelas}) susunan baharu berjaya disimpan!")
                        st.balloons()
                    except Exception as ralat:
                        st.error(f"❌ Gagal menyimpan data. Ralat: {ralat}")
