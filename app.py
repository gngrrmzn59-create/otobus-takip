import streamlit as st
import pandas as pd
import cv2
import numpy as np
from fpdf import FPDF
from datetime import datetime
import os

# --- AYARLAR VE VERİTABANI ---
DB_FILE = "filo_veritabani.csv"
LOGOLAR = {
    "Mercedes": "https://www.car-logos.org/wp-content/uploads/2011/09/mercedes-benz.png",
    "MAN": "https://www.car-logos.org/wp-content/uploads/2011/09/man.png",
    "Otokar": "https://upload.wikimedia.org/wikipedia/tr/0/07/Otokar_logo.png",
    "Temsa": "https://upload.wikimedia.org/wikipedia/commons/4/40/Temsa_logo.png",
    "Diğer": "https://cdn-icons-png.flaticon.com/512/1995/1995471.png"
}

if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=["Plaka", "Marka", "Son_Skor", "Tarih"])
    df.to_csv(DB_FILE, index=False)

def veri_yukle():
    return pd.read_csv(DB_FILE)

def veri_kaydet(plaka, marka, skor):
    df = veri_yukle()
    yeni_satir = {"Plaka": plaka, "Marka": marka, "Son_Skor": skor, "Tarih": datetime.now().strftime("%d-%m-%Y")}
    if plaka in df["Plaka"].values:
        df.loc[df["Plaka"] == plaka, ["Son_Skor", "Tarih"]] = [skor, yeni_satir["Tarih"]]
    else:
        df = pd.concat([df, pd.DataFrame([yeni_satir])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# --- AI VE GÖRÜNTÜ İŞLEME FONKSİYONLARI ---
def hasar_isaretle(yeni_resim_bytes):
    # Byte verisini OpenCV formatına çevir
    nparr = np.frombuffer(yeni_resim_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # SİMÜLASYON: Burada fark analizi yapılır. 
    # Şimdilik görsel üzerine örnek bir hasar kutusu çiziyoruz.
    h, w, _ = img.shape
    cv2.rectangle(img, (w//3, h//3), (2*w//3, 2*h//3), (0, 0, 255), 4)
    cv2.putText(img, "HASAR TESPIT EDILDI", (w//3, h//3 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
    
    return img

def rapor_olustur(plaka, veriler):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"HASAR EKSPERTIZ RAPORU - {plaka}", ln=True, align='C')
    
    y_pos = 40
    for yon, data in veriler.items():
        img_path = f"temp_{yon}.jpg"
        cv2.imwrite(img_path, data['islenmis_img'])
        pdf.set_font("Arial", 'B', 12)
        pdf.text(10, y_pos - 5, f"{yon} CEPHE - Hasar Skoru: {data['skor']}")
        pdf.image(img_path, x=10, y=y_pos, w=90)
        y_pos += 65
        if y_pos > 230:
            pdf.add_page()
            y_pos = 30
            
    pdf.output(f"{plaka}_Rapor.pdf")
    return f"{plaka}_Rapor.pdf"

# --- STREAMLIT ARAYÜZÜ ---
st.set_page_config(page_title="Otobüs Hasar Takip", layout="wide")

# SOL PANEL (Kütüphane)
st.sidebar.title("🚌 Araç Kütüphanesi")
search = st.sidebar.text_input("Plaka Sorgula").upper()
df_filo = veri_yukle()

# Kayıtlı araçları listele
secili_arac = None
for i, row in df_filo.iterrows():
    col_l, col_p = st.sidebar.columns([1, 4])
    col_l.image(LOGOLAR.get(row['Marka'], LOGOLAR["Diğer"]), width=25)
    if col_p.button(f"{row['Plaka']}", key=row['Plaka']):
        secili_arac = row['Plaka']

# ANA EKRAN MANTIĞI
aktif_plaka = secili_arac if secili_arac else search

if aktif_plaka:
    st.header(f"🛠️ Araç Paneli: {aktif_plaka}")
    
    # Araç veritabanında yoksa marka seçtir
    if aktif_plaka not in df_filo["Plaka"].values:
        marka = st.selectbox("Bu araç yeni. Markasını seçin:", list(LOGOLAR.keys()))
        if st.button("Sisteme Tanımla"):
            veri_kaydet(aktif_plaka, marka, 0)
            st.rerun()
    else:
        marka = df_filo[df_filo["Plaka"] == aktif_plaka]["Marka"].values[0]
        
        tab1, tab2 = st.tabs(["📸 Yeni Denetim Sihirbazı", "📊 Geçmiş Veriler"])
        
        with tab1:
            yonler = ["Ön", "Arka", "Sağ", "Sol"]
            if 'adim' not in st.session_state: st.session_state.adim = 0
            if 'denetim_verileri' not in st.session_state: st.session_state.denetim_verileri = {}

            if st.session_state.adim < 4:
                su_an = yonler[st.session_state.adim]
                st.subheader(f"Adım {st.session_state.adim + 1}/4: {su_an} Cepheyi Çekiniz")
                foto = st.camera_input(f"{su_an} Fotoğrafı")
                
                if foto:
                    # AI İşleme (Doğrulama ve İşaretleme)
                    islenmis = hasar_isaretle(foto.getvalue())
                    st.image(islenmis, caption="Tespit Edilen Hasar Alanı", channels="BGR")
                    
                    if st.button("Onayla ve Devam Et"):
                        st.session_state.denetim_verileri[su_an] = {
                            'islenmis_img': islenmis,
                            'skor': 6200 # Örnek skor
                        }
                        st.session_state.adim += 1
                        st.rerun()
            else:
                st.success("Tüm açılar tamamlandı!")
                if st.button("PDF Raporu Oluştur"):
                    yol = rapor_olustur(aktif_plaka, st.session_state.denetim_verileri)
                    with open(yol, "rb") as f:
                        st.download_button("📥 Raporu İndir", f, file_name=yol)
                    # Veritabanını güncelle
                    veri_kaydet(aktif_plaka, marka, 6200)

        with tab2:
            st.write(f"**Marka:** {marka}")
            st.write(f"**Son Denetim Skoru:** {df_filo[df_filo['Plaka']==aktif_plaka]['Son_Skor'].values[0]}")
            st.write(f"**Son Denetim Tarihi:** {df_filo[df_filo['Plaka']==aktif_plaka]['Tarih'].values[0]}")
else:
    st.info("Lütfen sol taraftan bir araç seçin veya yeni bir plaka girin.")
