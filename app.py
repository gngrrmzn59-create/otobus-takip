import streamlit as st
import cv2
import numpy as np
import os
from datetime import datetime, timedelta
from fpdf import FPDF

st.set_page_config(page_title="Otobüs Hasar Takip", layout="centered")
st.title("🚌 Otobüs Hasar Denetim Sistemi")

# Dosya saklama alanı
if not os.path.exists("data"):
    os.makedirs("data")

plaka = st.text_input("Araç Plakası Girin:").upper()

if plaka:
    img_file = st.camera_input("Aracın Fotoğrafını Çek")
    if img_file:
        bugun = datetime.now().strftime("%Y-%m-%d")
        yeni_yol = f"data/{plaka}_{bugun}.jpg"
        
        with open(yeni_yol, "wb") as f:
            f.write(img_file.getbuffer())
        
        st.success(f"{plaka} için {bugun} tarihli kayıt alındı.")

        # Dünkü fotoğrafı bul ve kıyasla
        dun = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        eski_yol = f"data/{plaka}_{dun}.jpg"

        if os.path.exists(eski_yol):
            img1 = cv2.imread(eski_yol)
            img2 = cv2.imread(yeni_yol)
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
            
            g1 = cv2.GaussianBlur(cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY), (21, 21), 0)
            g2 = cv2.GaussianBlur(cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY), (21, 21), 0)
            
            fark = cv2.absdiff(g1, g2)
            _, esik = cv2.threshold(fark, 35, 255, cv2.THRESH_BINARY)
            
            if np.sum(esik) > 5000:
                st.warning("⚠️ Yeni bir değişim algılandı!")
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt=f"PLAKA: {plaka} | TARIH: {bugun} | DURUM: DEGISIM VAR", ln=True)
                pdf.output("rapor.pdf")
                with open("rapor.pdf", "rb") as f:
                    st.download_button("📥 Raporu İndir", f, file_name=f"{plaka}_rapor.pdf")
            else:
                st.success("✅ Önemli bir fark bulunamadı.")
        else:
            st.info("Kıyaslama için sistemde dünkü kayıt bulunamadı.")
