import streamlit as st
import yfinance as yf
import pandas as pd
import time

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="mircndl", page_icon="🕯️", layout="centered")

# --- TASARIM (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .signal-card { 
        background-color: #262730; 
        padding: 20px; 
        border-radius: 15px; 
        margin-bottom: 15px; 
        border-left: 5px solid #4CAF50;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .hisse-baslik { font-size: 24px; font-weight: bold; color: #fff; }
    .bilgi { font-size: 14px; color: #aaa; }
    </style>
    """, unsafe_allow_html=True)

# --- BAŞLIK ---
st.title("🕯️ mircndl")
st.caption("Bulut Tabanlı Swing Trade Asistanı")
st.divider()

# --- ARKA PLAN MOTORU (BEYİN) ---
# Verileri önbelleğe alıyoruz ki her tıkta yavaşlamasın
@st.cache_data(ttl=900)  # 15 dakikada bir veriyi tazele
def verileri_analiz_et():
    # Takip Listesi (BIST 30'dan seçmeler)
    hisseler = ["THYAO.IS", "ASELS.IS", "KCHOL.IS", "GARAN.IS", "SISE.IS", "AKBNK.IS", "TUPRS.IS", "EREGL.IS"]
    sinyaller = []

    for sembol in hisseler:
        try:
            # Veri Çek (Doğrudan Yahoo Finance'den)
            # 1 Saatlik veriyi alıp 4 Saatlik Swing mumuna çevireceğiz
            df = yf.download(sembol, period="2mo", interval="1h", progress=False, multi_level_index=False)
            
            # Sütun isimlerini düzelt (Bazen karışık gelir)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)

            # Veri boşsa geç
            if df.empty or len(df) < 50:
                continue

            # 4 Saatlik (Swing) Dönüşümü
            ozet_dict = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
            df_4h = df.resample('4h').agg(ozet_dict).dropna()

            # İndikatör Hesaplamaları
            # 1. Trend (EMA 200)
            df_4h['EMA_200'] = df_4h['Close'].ewm(span=200).mean()
            
            # 2. RSI
            delta = df_4h['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14).mean()
            rs = gain / loss
            df_4h['RSI'] = 100 - (100 / (1 + rs))

            # Son Mum Analizi
            son = df_4h.iloc[-1]
            
            # --- STRATEJİ ---
            # Trend yukarı mı? (Fiyat > EMA200)
            trend_pozitif = son['Close'] > son['EMA_200']
            
            # RSI ucuz mu? (Swing için genelde 45-50 altı iyidir)
            rsi_uygun = son['RSI'] < 60 

            # Ekranda bir şeyler görmek için kriteri biraz esnek tutuyoruz
            if trend_pozitif and rsi_uygun:
                kalite = "YÜKSEK 🔥" if son['RSI'] < 35 else "NORMAL"
                sinyaller.append({
                    "sembol": sembol.replace(".IS", ""), # .IS kısmını görselden silelim
                    "fiyat": son['Close'],
                    "hedef": son['Close'] * 1.10, # %10 Kar hedefi
                    "rsi": son['RSI'],
                    "kalite": kalite,
                    "tarih": str(son.name)
                })

        except Exception as e:
            continue
            
    return sinyaller

# --- ARAYÜZ (YÜZ) ---
if st.button("🔄 Piyasayı Tara", use_container_width=True):
    with st.spinner('Yapay zeka BIST verilerini tarıyor...'):
        time.sleep(0.5) # Animasyon hissi
        firsatlar = verileri_analiz_et()
        
        if firsatlar:
            st.success(f"Toplam {len(firsatlar)} potansiyel fırsat bulundu!")
            
            for s in firsatlar:
                renk = "green"
                ikon = "🚀"
                
                st.markdown(f"""
                <div class="signal-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="hisse-baslik">{ikon} {s['sembol']}</span>
                        <span style="background-color:#4CAF50; padding:4px 8px; border-radius:5px; font-size:12px;">{s['kalite']}</span>
                    </div>
                    <div style="margin-top:10px; display:flex; justify-content:space-between;">
                        <div class="bilgi">Giriş Fiyatı<br><strong style="color:white; font-size:18px;">{s['fiyat']:.2f} ₺</strong></div>
                        <div class="bilgi">Hedef<br><strong style="color:#4CAF50; font-size:18px;">{s['hedef']:.2f} ₺</strong></div>
                        <div class="bilgi">RSI<br><strong style="color:orange; font-size:18px;">{s['rsi']:.1f}</strong></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Şu an stratejiye (Trend + RSI) uyan hisse bulunamadı.")
            st.markdown("**Takip Listesi:** THYAO, ASELS, KCHOL, GARAN, SISE, AKBNK")

# --- ALT BİLGİ ---
st.markdown("---")
st.caption("mircndl v2.0 Cloud • API sorunu giderildi.")
