import streamlit as st
import yfinance as yf
import pandas as pd
import time

# --- MARKA AYARLARI (mircndl) ---
st.set_page_config(
    page_title="mircndl",  # Tarayıcı sekmesinde yazacak isim
    page_icon="🕯️",        # Uygulama ikonu (Mum)
    layout="centered"
)

# --- TASARIM (DARK CANDLE THEME) ---
st.markdown("""
    <style>
    /* Ana Arka Plan */
    .stApp { 
        background-color: #0E1117; 
        color: white; 
    }
    
    /* Sinyal Kartı Tasarımı */
    .signal-card { 
        background-color: #1E1E1E; 
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 15px; 
        border-left: 6px solid #4CAF50; /* Yeşil Mum Çizgisi */
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    
    /* Metin Stilleri */
    .hisse-baslik { font-size: 26px; font-weight: bold; color: #fff; letter-spacing: 1px; }
    .kalite-badge { background-color: #2E7D32; color: white; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;}
    .bilgi-baslik { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
    .bilgi-deger { font-size: 20px; font-weight: bold; color: #eee; }
    
    /* Buton Stili */
    div.stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px;
        font-weight: bold;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #45a049;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ÜST KISIM (HEADER) ---
st.title("🕯️ mircndl") 
st.caption("Mirkan & Candle • Algoritmik Swing Analizi") # Senin İmzan
st.divider()

# --- ARKA PLAN MOTORU (BEYİN) ---
@st.cache_data(ttl=900)
def verileri_analiz_et():
    # Takip Listesi
    hisseler = ["THYAO.IS", "ASELS.IS", "KCHOL.IS", "GARAN.IS", "SISE.IS", "AKBNK.IS", "TUPRS.IS", "EREGL.IS", "BIMAS.IS", "FROTO.IS"]
    sinyaller = []

    for sembol in hisseler:
        try:
            # Veri Çek (Yahoo Finance)
            df = yf.download(sembol, period="3mo", interval="1h", progress=False, multi_level_index=False)
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)

            if df.empty or len(df) < 50: continue

            # Swing Dönüşümü (4 Saatlik)
            ozet = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
            df_4h = df.resample('4h').agg(ozet).dropna()

            # İndikatörler
            df_4h['EMA_200'] = df_4h['Close'].ewm(span=200).mean()
            
            delta = df_4h['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14).mean()
            rs = gain / loss
            df_4h['RSI'] = 100 - (100 / (1 + rs))

            son = df_4h.iloc[-1]
            
            # Strateji
            trend_pozitif = son['Close'] > son['EMA_200']
            rsi_uygun = son['RSI'] < 55 # Swing için biraz gevşettik

            if trend_pozitif and rsi_uygun:
                kalite = "GÜÇLÜ AL 🔥" if son['RSI'] < 35 else "AL SİNYALİ"
                sinyaller.append({
                    "sembol": sembol.replace(".IS", ""),
                    "fiyat": son['Close'],
                    "hedef": son['Close'] * 1.08, # %8 Hedef
                    "rsi": son['RSI'],
                    "kalite": kalite
                })

        except:
            continue
            
    return sinyaller

# --- ARAYÜZ (GÖVDE) ---
if st.button("PİYASAYI TARA", use_container_width=True):
    with st.spinner('mircndl algoritmaları çalışıyor...'):
        time.sleep(0.8)
        firsatlar = verileri_analiz_et()
        
        if firsatlar:
            st.success(f"Analiz Tamamlandı: {len(firsatlar)} Mum Formasyonu Bulundu")
            
            for s in firsatlar:
                st.markdown(f"""
                <div class="signal-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                        <span class="hisse-baslik">{s['sembol']}</span>
                        <span class="kalite-badge">{s['kalite']}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between;">
                        <div>
                            <div class="bilgi-baslik">GÜNCEL FİYAT</div>
                            <div class="bilgi-deger">{s['fiyat']:.2f} ₺</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="bilgi-baslik">HEDEF</div>
                            <div class="bilgi-deger" style="color:#4CAF50;">{s['hedef']:.2f} ₺</div>
                        </div>
                    </div>
                    <div style="margin-top:10px; padding-top:10px; border-top:1px solid #333; display:flex; justify-content:space-between; align-items:center;">
                         <span style="font-size:12px; color:#666;">RSI Göstergesi</span>
                         <span style="color:orange; font-weight:bold;">{s['rsi']:.1f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Şu an stratejiye uygun mum yapısı oluşmadı.")
            st.caption("Takip Listesi: BIST 30 (THYAO, ASELS, KCHOL...)")
