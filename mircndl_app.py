import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import datetime

# --- 1. AYARLAR ---
st.set_page_config(
    page_title="MIRCNDL v8.1", 
    page_icon="🐂", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- DEV LİSTE (BIST 100 + YAN TAHTALAR) ---
BIST_DEV_LISTE = [
    "THYAO.IS", "ASELS.IS", "KCHOL.IS", "GARAN.IS", "AKBNK.IS", "ISCTR.IS", "SISE.IS", "EREGL.IS", "BIMAS.IS",
    "TUPRS.IS", "SAHOL.IS", "YKBNK.IS", "FROTO.IS", "TOASO.IS", "PGSUS.IS", "TCELL.IS", "PETKM.IS", "EKGYO.IS",
    "SASA.IS", "HEKTS.IS", "KOZAL.IS", "KRDMD.IS", "ENKAI.IS", "VESTL.IS", "TTKOM.IS", "ARCLK.IS", "SOKM.IS",
    "MGROS.IS", "KONTR.IS", "GESAN.IS", "SMRTG.IS", "EUPWR.IS", "ALFAS.IS", "ASTOR.IS", "MIATK.IS", "REEDR.IS",
    "AGROT.IS", "CVKMD.IS", "SDTTR.IS", "ONCSM.IS", "TARKM.IS", "IZENR.IS", "TATEN.IS", "PASEU.IS", "VBTYZ.IS",
    "KBORU.IS", "PEKGY.IS", "GUBRF.IS", "ODAS.IS", "ZOREN.IS", "TSKB.IS", "SKBNK.IS", "SNGYO.IS", "KLSER.IS",
    "CANTE.IS", "QUAGR.IS", "YEOTK.IS", "CWENE.IS", "PENTA.IS", "BFREN.IS", "BRSAN.IS", "CIMSA.IS", "DOAS.IS",
    "EGEEN.IS", "ENJSA.IS", "GLYHO.IS", "GWIND.IS", "ISMEN.IS", "JANTS.IS", "KCAER.IS", "KMPUR.IS", "KORDS.IS",
    "MAVI.IS", "OTKAR.IS", "OYAKC.IS", "SBCS.IS", "TAVHL.IS", "TEKFEN.IS", "VESBE.IS", "ZOREN.IS", "AKSEN.IS",
    "ALARK.IS", "ALKIM.IS", "AEFES.IS", "AYDEM.IS", "BAGFS.IS", "BERA.IS", "BIOEN.IS", "BRISA.IS", "CCOLA.IS",
    "CEMTS.IS", "DEVA.IS", "ECILC.IS", "GENIL.IS", "GOZDE.IS", "IHLAS.IS", "IPEKE.IS", "KARSN.IS", "KARTN.IS",
    "LOGO.IS", "NTHOL.IS", "NETAS.IS", "PARSN.IS", "PRKME.IS", "RTAAL.IS", "SELEC.IS", "TRGYO.IS", "TMSN.IS",
    "TURSG.IS", "ULKER.IS", "VERUS.IS", "YATAS.IS", "YYLGD.IS"
]

# --- HAFIZA ---
if 'sayfa' not in st.session_state: st.session_state.sayfa = 'anasayfa'
if 'secilen_hisse' not in st.session_state: st.session_state.secilen_hisse = None
if 'tarama_sonuclari' not in st.session_state: st.session_state.tarama_sonuclari = []

# --- CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #e0e0e0; }
    .block-container { padding-top: 1rem; }
    
    /* Kartlar */
    .scan-card {
        background-color: #161b22; padding: 15px; border-radius: 10px;
        border: 1px solid #30363d; margin-bottom: 10px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .breakout-card {
        background-color: #1a2e1a; padding: 15px; border-radius: 10px;
        border: 2px solid #00E676; margin-bottom: 10px;
        box-shadow: 0 0 10px rgba(0, 230, 118, 0.3);
        display: flex; justify-content: space-between; align-items: center;
    }
    .stButton>button { border-radius: 8px; font-weight: bold; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- FONKSİYONLAR ---
def sayfaya_git(sayfa_adi):
    st.session_state.sayfa = sayfa_adi
    st.rerun()

def hisse_sec(sembol):
    st.session_state.secilen_hisse = sembol
    st.session_state.sayfa = 'hisse_detay'
    st.rerun()

@st.cache_data(ttl=600)
def teknik_tara(strateji, hisse_listesi):
    sonuclar = []
    # İlerleme Çubuğu
    bar = st.progress(0, text="Başlıyor...")
    
    for i, sembol in enumerate(hisse_listesi):
        bar.progress((i + 1) / len(hisse_listesi), text=f"Taranıyor: {sembol}")
        try:
            # Günlük veri
            df = yf.download(sembol, period="3mo", interval="1d", progress=False)
            if len(df) < 50: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
            
            son = df.iloc[-1]
            # Breakout Hesapları
            high_20 = df['High'].rolling(20).max().shift(1).iloc[-1]
            vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
            
            # İndikatörler
            exp1 = df['Close'].ewm(span=12).mean(); exp2 = df['Close'].ewm(span=26).mean()
            macd = exp1 - exp2; signal = macd.ewm(span=9).mean()
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_val = rsi.iloc[-1]
            
            uygun = False; mesaj = ""; stil = "normal"

            if strateji == "breakout":
                # Fiyat zirveyi kırdı mı VE Hacim ortalamanın üstünde mi?
                if (son['Close'] > high_20) and (son['Volume'] > vol_avg):
                    uygun = True
                    mesaj = f"🐂 HACİMLİ KIRILIM! (Direnç: {high_20:.2f})"
                    stil = "breakout"
            
            elif strateji == "macd_rsi":
                if macd.iloc[-1] > signal.iloc[-1] and rsi_val < 70:
                    uygun = True; mesaj = f"MACD AL & RSI {rsi_val:.0f}"
            
            elif strateji == "ema_cross":
                 df['SMA50'] = df['Close'].rolling(50).mean()
                 df['SMA200'] = df['Close'].rolling(200).mean()
                 if df['SMA50'].iloc[-1] > df['SMA200'].iloc[-1]:
                     uygun = True; mesaj = "Golden Cross Trendi"

            if uygun:
                sonuclar.append({"sembol": sembol.replace(".IS", ""), "fiyat": son['Close'], "mesaj": mesaj, "stil": stil})
        except: continue
    
    bar.empty()
    return sonuclar

# --- SAYFALAR ---

# ANASAYFA
if st.session_state.sayfa == 'anasayfa':
    st.write("## 🐂 MIRCNDL v8.1 (GÜNCEL)")
    st.success("Sistem Aktif! Eğer bu yeşil yazıyı görüyorsan güncelleme başarılıdır.")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🛠️ TEKNİK TARAMA", type="primary"): sayfaya_git('teknik_menu')
    with c2:
        st.info("Piyasa Verileri: BIST GENEL (Gecikmeli)")

# TEKNİK MENÜ
elif st.session_state.sayfa == 'teknik_menu':
    c_back, c_title = st.columns([1, 4])
    with c_back:
        if st.button("⬅️"): sayfaya_git('anasayfa')
    with c_title:
        st.subheader("🛠️ Teknik Algoritmalar")
    
    # AYARLAR
    strateji = st.selectbox("Strateji", [
        ("🐂 Hacimli Kırılım (Breakout)", "breakout"),
        ("⚡ MACD + RSI", "macd_rsi"),
        ("📈 Golden Cross", "ema_cross")
    ])
    
    # HIZLI TEST KUTUSU
    hizli_test = st.checkbox("⚡ Hızlı Test Modu (Sadece ilk 10 hisseyi tara)", value=True)
    
    if st.button("🚀 TARAMAYI BAŞLAT"):
        liste = BIST_DEV_LISTE[:10] if hizli_test else BIST_DEV_LISTE
        st.session_state.tarama_sonuclari = teknik_tara(strateji[1], liste)
    
    st.write("---")
    
    if st.session_state.tarama_sonuclari:
        st.success(f"{len(st.session_state.tarama_sonuclari)} Sonuç Bulundu")
        for s in st.session_state.tarama_sonuclari:
            # Kart Stili
            css_class = "breakout-card" if s['stil'] == "breakout" else "scan-card"
            color = "#00E676" if s['stil'] == "breakout" else "#58a6ff"
            
            c_info, c_btn = st.columns([3, 1])
            with c_info:
                st.markdown(f"""
                <div class="{css_class}">
                    <div style="color:{color}; font-weight:bold; font-size:18px;">{s['sembol']}</div>
                    <div style="color:#ddd; font-size:13px;">{s['mesaj']}</div>
                    <div style="color:white; font-weight:bold;">{s['fiyat']:.2f} ₺</div>
                </div>
                """, unsafe_allow_html=True)
            with c_btn:
                if st.button("🔍", key=f"btn_{s['sembol']}"):
                    hisse_sec(s['sembol'])
    else:
        if not hizli_test: st.warning("Bu stratejiye uyan hisse bulunamadı.")

# HİSSE DETAY
elif st.session_state.sayfa == 'hisse_detay':
    sembol = st.session_state.secilen_hisse
    c_back, c_title = st.columns([1, 4])
    with c_back:
        if st.button("⬅️"): sayfaya_git('teknik_menu')
    with c_title:
        st.markdown(f"### {sembol}")
    
    try:
        df = yf.download(sembol+".IS", period="6mo", interval="1d", progress=False)
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.update_layout(template="plotly_dark", height=350, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    except:
        st.error("Grafik yüklenemedi.")
