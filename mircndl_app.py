import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time
import datetime

# --- 1. AYARLAR & CSS ---
st.set_page_config(
    page_title="MIRCNDL", 
    page_icon="📊", 
    layout="wide", 
    initial_sidebar_state="collapsed" # Menü kapalı başlasın
)

# --- HAFIZA (SESSION STATE) ---
# Sayfa yenilense bile verilerin kaybolmaması için burası kritik
if 'sayfa' not in st.session_state: st.session_state.sayfa = 'anasayfa'
if 'secilen_hisse' not in st.session_state: st.session_state.secilen_hisse = None
if 'tarama_sonuclari' not in st.session_state: st.session_state.tarama_sonuclari = [] # Tarama sonucu hafızası
if 'kullanici_notlari' not in st.session_state: st.session_state.kullanici_notlari = {}
if 'trade_gecmisi' not in st.session_state: st.session_state.trade_gecmisi = {}

# --- CSS TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #e0e0e0; }
    
    /* Gereksiz boşlukları sil */
    .block-container { padding-top: 1rem; padding-bottom: 5rem; }
    
    /* Haber Kartı */
    .news-card {
        background-color: #1a1c24; padding: 12px; border-radius: 8px;
        border-left: 3px solid #FFD700; margin-bottom: 8px; font-size: 13px;
    }
    
    /* Tarama Kartı */
    .scan-card {
        background-color: #161b22; padding: 15px; border-radius: 10px;
        border: 1px solid #30363d; margin-bottom: 10px;
        display: flex; justify-content: space-between; align-items: center;
    }
    
    /* Özel Butonlar */
    .stButton>button { 
        border-radius: 8px; font-weight: bold; border: none; 
        transition: 0.3s;
    }
    
    /* Geri Dön Butonu Stili */
    .back-btn { background-color: #333; color: white; }
    
    </style>
    """, unsafe_allow_html=True)

# --- 2. FONKSİYONLAR ---

def sayfaya_git(sayfa_adi):
    st.session_state.sayfa = sayfa_adi
    st.rerun() # Sayfayı anında yenile ve yönlendir

def hisse_sec(sembol):
    st.session_state.secilen_hisse = sembol
    st.session_state.sayfa = 'hisse_detay'
    st.rerun()

def not_kaydet():
    sembol = st.session_state.secilen_hisse
    key = f"not_input_{sembol}"
    if key in st.session_state and st.session_state[key]:
        not_icerik = st.session_state[key]
        if sembol not in st.session_state.kullanici_notlari:
            st.session_state.kullanici_notlari[sembol] = []
        st.session_state.kullanici_notlari[sembol].append(f"{datetime.datetime.now().strftime('%d/%m %H:%M')} - {not_icerik}")
        st.toast("Not Kaydedildi! 💾")

def teknik_tara(strateji):
    hisseler = ["THYAO.IS", "ASELS.IS", "KCHOL.IS", "GARAN.IS", "AKBNK.IS", "SISE.IS", 
                "EREGL.IS", "SASA.IS", "HEKTS.IS", "ASTOR.IS", "MIATK.IS", "REEDR.IS", "TUPRS.IS"]
    sonuclar = []
    
    progress_bar = st.progress(0)
    
    for i, sembol in enumerate(hisseler):
        progress_bar.progress((i + 1) / len(hisseler))
        try:
            df = yf.download(sembol, period="6mo", interval="1d", progress=False)
            if len(df) < 50: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
            
            # Hesaplamalar
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['SMA200'] = df['Close'].rolling(200).mean()
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            exp1 = df['Close'].ewm(span=12).mean(); exp2 = df['Close'].ewm(span=26).mean()
            macd = exp1 - exp2; signal = macd.ewm(span=9).mean()
            
            son = df.iloc[-1]
            uygun = False
            mesaj = ""

            if strateji == "macd_rsi":
                if macd.iloc[-1] > signal.iloc[-1] and son['RSI'] < 70:
                    uygun = True; mesaj = f"MACD AL & RSI {son['RSI']:.0f}"
            elif strateji == "ema_cross":
                if son['SMA50'] > son['SMA200']:
                    uygun = True; mesaj = "Golden Cross Trendi"
            elif strateji == "satis":
                if son['RSI'] > 75 or (macd.iloc[-1] < signal.iloc[-1]):
                    uygun = True; mesaj = "Satış Bölgesi / Şişkinlik"

            if uygun:
                sonuclar.append({"sembol": sembol.replace(".IS", ""), "fiyat": son['Close'], "mesaj": mesaj})
        except: continue
    
    progress_bar.empty()
    return sonuclar

def hisse_bilgi_getir(sembol):
    try:
        ticker = yf.Ticker(sembol + ".IS")
        return ticker.info
    except: return {}

# --- 3. SAYFA YÖNETİMİ ---

# --- ANASAYFA ---
if st.session_state.sayfa == 'anasayfa':
    
    # Başlık ve Logo
    col_logo, col_baslik = st.columns([1, 8])
    with col_logo: st.write("## 🕯️")
    with col_baslik: st.write("## MIRCNDL")
    
    st.write("---")
    
    # Haberler
    st.caption("📢 PİYASA ÖZETİ")
    st.markdown('<div class="news-card">🌍 <b>Global:</b> Fed faiz kararı bekleniyor, Ons Altın dirençte.</div>', unsafe_allow_html=True)
    st.markdown('<div class="news-card">🇹🇷 <b>BIST:</b> Endeks 9000 üzerinde tutunmaya çalışıyor. Bankalar hareketli.</div>', unsafe_allow_html=True)
    
    st.write("")
    st.write("")
    
    # Ana Menü Butonları (Sidebar Yerine Buradan Yönetiyoruz)
    st.caption("🚀 HIZLI ERİŞİM")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🛠️ TEKNİK ANALİZ", type="primary", use_container_width=True):
            sayfaya_git('teknik_menu')
    with c2:
        if st.button("🏢 TEMEL ANALİZ", use_container_width=True):
            st.toast("Yakında eklenecek...")
            
    st.info("👆 Analiz türünü seçerek başla.")


# --- TEKNİK ANALİZ MENÜSÜ ---
elif st.session_state.sayfa == 'teknik_menu':
    
    # Üst Bar: Geri Dön ve Başlık
    c_back, c_title = st.columns([1, 4])
    with c_back:
        if st.button("⬅️", help="Anasayfaya Dön"): sayfaya_git('anasayfa')
    with c_title:
        st.subheader("🛠️ Teknik Tarama")
    
    # Filtreler (Sol menü yerine yukarıya aldık, daha rahat)
    st.markdown("##### Strateji Seçimi")
    strateji = st.selectbox("", [
        ("⚡ MACD + RSI Kombinasyonu", "macd_rsi"),
        ("📈 Golden Cross (EMA)", "ema_cross"),
        ("🔻 Satış Sinyalleri", "satis")
    ], label_visibility="collapsed")
    
    # Tarama Butonu
    if st.button("🚀 TARAMAYI BAŞLAT", type="primary", use_container_width=True):
        st.session_state.tarama_sonuclari = teknik_tara(strateji[1])
    
    st.write("---")
    
    # Sonuçları Göster (Hafızadan okuyoruz)
    if st.session_state.tarama_sonuclari:
        st.success(f"{len(st.session_state.tarama_sonuclari)} Hisse Bulundu")
        
        for s in st.session_state.tarama_sonuclari:
            # Kart Yapısı
            col_info, col_btn = st.columns([3, 1])
            
            with col_info:
                st.markdown(f"""
                <div style="font-weight:bold; font-size:18px; color:#4CAF50">{s['sembol']}</div>
                <div style="font-size:12px; color:#aaa">{s['mesaj']}</div>
                <div style="font-weight:bold;">{s['fiyat']:.2f} ₺</div>
                """, unsafe_allow_html=True)
            
            with col_btn:
                # İşte burası! Artık tıklayınca çalışacak.
                if st.button("🔍 İncele", key=f"btn_{s['sembol']}"):
                    hisse_sec(s['sembol'])
            
            st.markdown("<hr style='margin:5px 0; border-color:#333'>", unsafe_allow_html=True)
            
    elif st.session_state.tarama_sonuclari == [] and st.button("Temizle"): 
        pass # Boş durum


# --- HİSSE DETAY SAYFASI ---
elif st.session_state.sayfa == 'hisse_detay':
    
    sembol = st.session_state.secilen_hisse
    
    # Üst Bar
    c_back, c_title = st.columns([1, 4])
    with c_back:
        if st.button("⬅️", help="Listeye Dön"): sayfaya_git('teknik_menu')
    with c_title:
        st.markdown(f"### 🏢 {sembol} Analiz Kartı")

    # Veriler
    bilgi = hisse_bilgi_getir(sembol)
    
    # 1. Puan ve Fiyat
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Fiyat", f"{bilgi.get('currentPrice', 0)} ₺")
    with col2:
        st.metric("MIRCNDL Puanı", "82/100", delta="Güçlü")
        
    # 2. Grafik
    st.markdown("#### 📈 Canlı Grafik")
    df_chart = yf.download(sembol+".IS", period="3mo", interval="1d", progress=False)
    fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'])])
    fig.update_layout(height=300, margin=dict(t=10,b=0,l=0,r=0), template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # 3. Not ve Trade
    st.write("---")
    tab1, tab2 = st.tabs(["📝 Notlar", "💰 Geçmiş İşlemler"])
    
    with tab1:
        st.text_area("Hisse hakkında not al:", key=f"not_input_{sembol}")
        if st.button("💾 Notu Kaydet"):
            not_kaydet()
        
        # Kayıtlı notları göster
        if sembol in st.session_state.kullanici_notlari:
            st.info("📋 Kayıtlı Notlar:")
            for notum in st.session_state.kullanici_notlari[sembol]:
                st.write(f"- {notum}")

    with tab2:
        c1, c2 = st.columns(2)
        alis = c1.number_input("Alış Fiyatı", key="alis")
        satis = c2.number_input("Satış Fiyatı", key="satis")
        if st.button("İşlem Ekle"):
            # Buraya işlem ekleme mantığı gelir
            st.success(f"{sembol} işlemi eklendi: {alis} -> {satis}")
