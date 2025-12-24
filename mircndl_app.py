import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time
import datetime

# --- 1. AYARLAR & CSS ---
st.set_page_config(page_title="MIRCNDL", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# Hafıza (Session State) Başlatma - Sayfalar arası geçiş ve notlar için
if 'sayfa' not in st.session_state: st.session_state.sayfa = 'anasayfa'
if 'secilen_hisse' not in st.session_state: st.session_state.secilen_hisse = None
if 'kullanici_notlari' not in st.session_state: st.session_state.kullanici_notlari = {}
if 'trade_gecmisi' not in st.session_state: st.session_state.trade_gecmisi = {}

# Özel Tasarım (CSS) - Boşlukları alma ve Şıklık
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #e0e0e0; }
    
    /* Üst Boşlukları Yok Et */
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    
    /* Haber Kartları */
    .news-card {
        background-color: #1a1c24; padding: 15px; border-radius: 10px;
        border-left: 4px solid #FBC02D; margin-bottom: 10px; font-size: 14px;
    }
    
    /* Tarama Sonuç Kartı (Sade) */
    .scan-card {
        background-color: #161b22; padding: 12px; border-radius: 8px;
        border: 1px solid #30363d; margin-bottom: 8px; cursor: pointer;
        display: flex; justify-content: space-between; align-items: center;
        transition: 0.3s;
    }
    .scan-card:hover { border-color: #58a6ff; background-color: #21262d; }
    
    /* Puan Kartı */
    .score-box {
        font-size: 24px; font-weight: bold; padding: 10px; 
        border-radius: 8px; text-align: center; color: white;
    }
    
    /* Butonlar */
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FONKSİYONLAR ---

def sayfaya_git(sayfa_adi):
    st.session_state.sayfa = sayfa_adi

def hisse_sec(sembol):
    st.session_state.secilen_hisse = sembol
    st.session_state.sayfa = 'hisse_detay'

def not_kaydet():
    sembol = st.session_state.secilen_hisse
    not_icerik = st.session_state[f"not_input_{sembol}"]
    if sembol not in st.session_state.kullanici_notlari:
        st.session_state.kullanici_notlari[sembol] = []
    st.session_state.kullanici_notlari[sembol].append(f"{datetime.datetime.now().strftime('%d-%m %H:%M')} - {not_icerik}")

def trade_kaydet(alis, satis):
    sembol = st.session_state.secilen_hisse
    if sembol not in st.session_state.trade_gecmisi:
        st.session_state.trade_gecmisi[sembol] = []
    st.session_state.trade_gecmisi[sembol].append({"alis": alis, "satis": satis})

@st.cache_data(ttl=600)
def teknik_tara(strateji):
    # Hız için kısıtlı liste
    hisseler = ["THYAO.IS", "ASELS.IS", "KCHOL.IS", "GARAN.IS", "AKBNK.IS", "SISE.IS", 
                "EREGL.IS", "SASA.IS", "HEKTS.IS", "ASTOR.IS", "MIATK.IS", "REEDR.IS"]
    sonuclar = []
    
    for sembol in hisseler:
        try:
            df = yf.download(sembol, period="6mo", interval="1d", progress=False)
            if len(df) < 50: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
            
            # İndikatörler
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

            if strateji == "macd_rsi_kombin": # MACD AL + RSI Makul
                if macd.iloc[-1] > signal.iloc[-1] and son['RSI'] < 70:
                    uygun = True; mesaj = f"MACD Kesişimi & RSI {son['RSI']:.0f}"
            elif strateji == "ema_tarama": # Golden Cross
                if son['SMA50'] > son['SMA200']:
                    uygun = True; mesaj = "Golden Cross (50 > 200)"
            elif strateji == "satis_sinyali":
                if son['RSI'] > 75 or (macd.iloc[-1] < signal.iloc[-1]):
                    uygun = True; mesaj = "Aşırı Alım veya MACD Sat"

            if uygun:
                sonuclar.append({"sembol": sembol.replace(".IS", ""), "fiyat": son['Close'], "mesaj": mesaj})
        except: continue
    return sonuclar

def hisse_temel_getir(sembol):
    try:
        ticker = yf.Ticker(sembol + ".IS")
        info = ticker.info
        return info
    except: return None

# --- 3. ANA UYGULAMA MANTIĞI ---

# HEADER (Her sayfada sabit)
c1, c2 = st.columns([1, 10])
with c1: st.markdown("## 📊") # Mum İkonu
with c2: st.markdown("## MIRCNDL")

# --- SAYFA: ANASAYFA ---
if st.session_state.sayfa == 'anasayfa':
    
    # 1. Haberler (Hap Bilgi)
    st.markdown("### 📰 Hap Haberler")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="news-card">🌍 <b>Küresel:</b> Fed faiz kararı bekleniyor, piyasalar temkinli. Altın ons bazında hareketli.</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="news-card">🇹🇷 <b>Yurt İçi:</b> BIST 100 endeksi 9000 puan üzerinde tutunmaya çalışıyor. Bankacılık sektörü öncü.</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="news-card">⚡ <b>Enerji:</b> Yenilenebilir enerji teşvikleri açıklandı. ASTOR ve YEOTK hareketlenebilir.</div>', unsafe_allow_html=True)
    
    st.divider()

    # 2. Sidebar (Ana Menü)
    with st.sidebar:
        st.title("Menü")
        if st.button("🛠️ Teknik Analiz"): sayfaya_git('teknik_menu')
        if st.button("🏢 Temel Analiz"): st.toast("Yakında eklenecek...")
        st.info("Sürüm: v7.0 Super App")

    st.info("👈 Menüden analiz türünü seçerek başla.")


# --- SAYFA: TEKNİK ANALİZ MENÜSÜ ---
elif st.session_state.sayfa == 'teknik_menu':
    
    # Geri Butonu
    if st.button("⬅️ Geri Dön", key="back_home"): sayfaya_git('anasayfa')
    
    st.markdown("### 🛠️ Teknik Analiz Merkezi")
    
    # Sidebar Değişimi
    with st.sidebar:
        st.header("Teknik Filtreler")
        secim = st.radio("Strateji Seç:", [
            ("⚡ MACD + RSI Kombin", "macd_rsi_kombin"),
            ("📈 EMA Golden Cross", "ema_tarama"),
            ("🔻 Satış Verenler", "satis_sinyali")
        ])
        if st.button("🔙 Ana Menü"): sayfaya_git('anasayfa')

    # Tarama Ekranı
    st.write(f"Seçilen Strateji: **{secim[0]}**")
    
    if st.button("🚀 TARAMAYI BAŞLAT", type="primary"):
        with st.spinner("Piyasa taranıyor... Roketler ateşlendi! 🚀"):
            time.sleep(1) # Animasyon efekti
            sonuclar = teknik_tara(secim[1])
            
            if sonuclar:
                st.success(f"{len(sonuclar)} Hisse Bulundu")
                for s in sonuclar:
                    # Tıklanabilir Kartlar (Buton hilesi ile)
                    col_a, col_b = st.columns([5, 1])
                    with col_a:
                        st.markdown(f"""
                        <div class="scan-card">
                            <span style="font-weight:bold; font-size:18px; color:#58a6ff">{s['sembol']}</span>
                            <span style="color:#aaa">{s['mesaj']}</span>
                            <span style="font-weight:bold; color:white">{s['fiyat']:.2f} ₺</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_b:
                        # Butona basınca detaya git
                        if st.button("İncele", key=f"btn_{s['sembol']}"):
                            hisse_sec(s['sembol'])
            else:
                st.warning("Bu stratejiye uygun hisse bulunamadı.")


# --- SAYFA: HİSSE DETAY (SUPER EKRAN) ---
elif st.session_state.sayfa == 'hisse_detay':
    
    sembol = st.session_state.secilen_hisse
    
    # Üst Bar (Geri ve Başlık)
    c1, c2 = st.columns([1, 6])
    with c1:
        if st.button("⬅️ Listeye Dön"): sayfaya_git('teknik_menu')
    with c2:
        st.markdown(f"## 🏢 {sembol} - Detaylı Analiz Kartı")
    
    # Veri Çekme
    with st.spinner("Hisse röntgeni çekiliyor..."):
        bilgi = hisse_temel_getir(sembol)
        
        if bilgi:
            # 1. Kısım: Temel Skor ve Fiyat
            col1, col2, col3, col4 = st.columns(4)
            puan = 75 # Yapay zeka puanı (Örnek)
            renk = "#00C853" if puan > 70 else "#FFAB00"
            
            with col1:
                st.markdown("### MIRCNDL Puanı")
                st.markdown(f'<div class="score-box" style="background-color:{renk}">{puan}/100</div>', unsafe_allow_html=True)
            with col2:
                st.metric("Fiyat", f"{bilgi.get('currentPrice',0)} ₺")
            with col3:
                st.metric("F/K", f"{bilgi.get('trailingPE',0):.2f}")
            with col4:
                st.metric("Pazar", "Yıldız Pazar") # Örnek
            
            st.divider()
            
            # 2. Kısım: Grafik ve Benzerlik
            g1, g2 = st.columns([2, 1])
            with g1:
                st.markdown("#### 📈 Teknik Görünüm")
                # Basit bir mum grafiği
                df = yf.download(sembol+".IS", period="3mo", interval="1d", progress=False)
                fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
                fig.update_layout(height=300, margin=dict(t=0,b=0,l=0,r=0), xaxis_rangeslider_visible=False, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            
            with g2:
                st.markdown("#### 🤖 Yapay Zeka Yorumu")
                st.info("Benzerlik Analizi: Bu hisse, 2023 Mayıs ayındaki TOASO hareketine %85 benzerlik gösteriyor. O dönem %12 yükseliş gelmişti.")
                
                st.markdown("#### 📊 İndikatör Durumu")
                st.write("RSI: **Nötr (55)**")
                st.write("MACD: **AL Bölgesinde**")
                st.write("Hacim: **Ortalama Üzeri**")

            st.divider()
            
            # 3. Kısım: KİŞİSEL TRADE GÜNLÜĞÜ (Hafıza)
            st.markdown("### 📒 Kişisel Notlar & Trade Geçmişi")
            
            n1, n2 = st.columns(2)
            
            with n1:
                st.subheader("📝 Not Al")
                st.text_area("Hisseyle ilgili düşüncelerin:", key=f"not_input_{sembol}")
                if st.button("Notu Kaydet"):
                    not_kaydet()
                    st.success("Kaydedildi!")
                
                # Eski notları göster
                if sembol in st.session_state.kullanici_notlari:
                    st.write("---")
                    for notum in st.session_state.kullanici_notlari[sembol]:
                        st.caption(notum)

            with n2:
                st.subheader("💰 Trade Geçmişi")
                c_al, c_sat = st.columns(2)
                alis = c_al.number_input("Alış Fiyatı", min_value=0.0)
                satis = c_sat.number_input("Satış Fiyatı", min_value=0.0)
                
                if st.button("İşlemi Ekle"):
                    trade_kaydet(alis, satis)
                    st.success("Portföye işlendi!")
                
                if sembol in st.session_state.trade_gecmisi:
                    st.write("---")
                    for islem in st.session_state.trade_gecmisi[sembol]:
                        kar_zarar = islem['satis'] - islem['alis']
                        renk_t = "green" if kar_zarar > 0 else "red"
                        st.markdown(f"Alış: {islem['alis']} - Satış: {islem['satis']} | **K/Z: :{renk_t}[{kar_zarar:.2f}]**")

        else:
            st.error("Veri alınamadı.")
