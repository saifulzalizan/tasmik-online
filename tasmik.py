import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pytz
import json

# Setup halaman Streamlit (Dioptimumkan untuk Telefon)
st.set_page_config(page_title="Sistem Rekod Tasmik SKBP", layout="centered")

# Pautan Skop Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def sambung_database():
    try:
        # Membaca data daripada Streamlit Secrets dengan pembersihan teks kunci
        raw_key = st.secrets["private_key"]
        
        # Memastikan simbol \n dibaca sebagai baris baru yang sah oleh Google API
        clean_key = raw_key.replace('\\n', '\n') if '\\n' in raw_key else raw_key.encode().decode('unicode_escape')
        
        info = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": clean_key,
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"]
        }
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        client = gspread.authorize(creds)
        
        # Membuka fail Google Sheets induk
        doc = client.open("Rekod Tasmik Online")
        sheet_rekod = doc.worksheet("Rekod_Tasmik")
        sheet_data = doc.worksheet("Senarai_Murid")
        
        return sheet_rekod, sheet_data
    except Exception as e:
        st.error(f"⚠️ Ralat Pangkalan Data: {e}")
        return None, None

# Panggil fungsi sambungan database
sheet_rekod, sheet_data = sambung_database()

# --- BAHAGIAN PAPARAN LOGO SK BULOH POH & TAJUK ---
url_logo_sekolah = "https://upload.wikimedia.org/wikipedia/ms/2/29/Sekolah_Kebangsaan_Buloh_Poh.jpg"

col1, col2, col3 = st.columns([1, 1.2, 1])
with col2:
    try:
        st.image(url_logo_sekolah, use_container_width=True)
    except:
        pass

st.title("📋 Sistem Rekod Tasmik Murid")
st.subheader("SK Buloh Poh")
st.write("---")

if sheet_rekod is None or sheet_data is None:
    st.warning("Gagal menyambung ke Google Sheets. Sila pastikan isi kotak Secrets telah dimasukkan mengikut format TOML yang betul.")
else:
    # --- MEMBACA DATA KELAS & NAMA DARI TAB 'Senarai_Murid' ---
    @st.cache_data(ttl=300)
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
        # --- INPUT DI LUAR BORANG ---
        pilihan_kelas = st.selectbox("📁 Kolum 1: Pilih Kelas", senarai_kelas)
        murid_dalam_kelas = sorted(peta_kelas_murid.get(pilihan_kelas, []))
        pilihan_nama = st.selectbox("👤 Kolum 2: Nama Pelajar", murid_dalam_kelas)
        
        # --- SET PILIHAN DROP-DOWN LAIN ---
        zon_masa = pytz.timezone('Asia/Kuala_Lumpur')
        hari_ini = datetime.datetime.now(zon_masa)
        senarai_tarikh = [
            hari_ini.strftime("%Y-%m-%d"),
            (hari_ini - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            (hari_ini - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
        ]
        
        senarai_minggu = [f"Minggu {i}" for i in range(1, 46)]
        senarai_bacaan = ["Iqra' 1", "Iqra' 2", "Iqra' 3", "Iqra' 4", "Iqra' 5", "Iqra' 6", "Al-Quran", "Telah Khatam"]
        senarai_muka_surat = [f"Muka Surat {i}" for i in range(1, 101)]

        # --- BORANG INPUT ---
        with st.form(key='borang_tasmik_skbp_final_v2', clear_on_submit=False):
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
                        data_baru = [
                            pilihan_kelas,   # Kolum 1
                            pilihan_nama,    # Kolum 2
                            pilihan_tarikh,  # Kolum 3
                            pilihan_minggu,  # Kolum 4
                            pilihan_tahap,   # Kolum 5
                            pilihan_ms       # Kolum 6
                        ]
                        sheet_rekod.append_row(data_baru)
                        st.success(f"🎉 Rekod bagi {pilihan_nama} ({pilihan_kelas}) berjaya disimpan!")
                        st.balloons()
                    except Exception as ralat:
                        st.error(f"❌ Gagal menyimpan data. Ralat: {ralat}")
