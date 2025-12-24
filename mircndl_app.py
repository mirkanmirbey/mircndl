import streamlit as st
import requests
import pandas as pd
import time

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="mircndl",
    page_icon="🕯️",
    layout="centered" # Mobilde uygulama gibi görünmesi için ortaladık
)

# --- TASARIM (CSS) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: white;
    }
    div[data-testid="stMetricValue"] {
        font-size: 20px;
    }
    .signal-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        border-left: 5px solid #4CAF50;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BAŞLIK ---
st.title("🕯️ mircndl")
st.caption("Yapay Zeka Destekli Swing Trade Asistanı")
st.divider()

# --- VERİ ÇEKME FONKSİYONU ---
def get_signals():
    try:
        # Backend API adresimiz
        response = requests.get("http://127.0.0.1:8000/sinyaller")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Sunucu hatası!")
            return None
    except:
        st.error("Bağlantı kurulamadı. Backend (API) açık mı?")
        return None

# --- BUTON VE YENİLEME ---
if st.button("🔄 Piyasayı Tara"):
    with st.spinner('Grafikler analiz ediliyor...'):
        time.sleep(1) # Efekt olsun diye :)
        data = get_signals()
        
        if data and data['bulunan_sinyaller']:
            st.success(f"{len(data['bulunan_sinyaller'])} Fırsat Bulundu!")
            
            for sinyal in data['bulunan_sinyaller']:
                # Yön Rengi Belirleme
                renk = "green" if "AL" in sinyal['yon'] else "red"
                ikon = "🚀" if "AL" in sinyal['yon'] else "🔻"
                
                # KART GÖRÜNÜMÜ
                st.markdown(f"""
                <div class="signal-card" style="border-left-color: {renk};">
                    <h3>{ikon} {sinyal['sembol']}</h3>
                    <p><b>Yön:</b> {sinyal['yon']} | <b>Kalite:</b> {sinyal['kalite']}</p>
                    <div style="display: flex; justify-content: space-between;">
                        <div>Giriş: <b>{sinyal['fiyat']:.2f} ₺</b></div>
                        <div>Hedef: <b>{sinyal['hedef']:.2f} ₺</b></div>
                    </div>
                    <hr style="margin: 10px 0; border-color: #444;">
                    <small style="color: #aaa;">Analiz Tarihi: {sinyal['tarih']}</small>
                </div>
                """, unsafe_allow_html=True)
                
        elif data:
            st.info("Currently, no high-quality swing signals found.")
            st.markdown("---")
            st.write("🔍 **Takip Edilen Hisseler:** THYAO, ASELS, KCHOL, GARAN, SISE")
            
else:
    st.info("Güncel sinyalleri görmek için tarama yapın.")

# --- ALT BİLGİ ---
st.markdown("---")
st.caption("mircndl v1.0 • Designed by Architect")