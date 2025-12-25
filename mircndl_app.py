import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --- 1. AYARLAR ---
st.set_page_config(
    page_title="MIRCNDL PRO",
    page_icon="🦅",
    layout="wide", # Tam ekran modu
    initial_sidebar_state="collapsed" # Menü kapalı
)

# --- CSS (MATRIX DARK MODE) ---
st.markdown("""
    <style>
    /* Full Siyah Arka Plan */
    .stApp { background-color: #000000; color: #00FF41; }
    
    /* Gereksiz boşlukları sil */
    .block-container { padding-top: 1rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem; }
    
    /* Arama Kutusu Stili */
    input[type="text"] {
        background-color: #111; color: #00FF41; border: 1px solid #333;
        font-size: 20px; font-weight: bold; text-transform: uppercase;
    }
    
    /* Üstteki Streamlit menüsünü gizle */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Metrik Kutuları */
    div[data-testid="stMetricValue"] { font-size: 24px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SÜPER ALGORİTMA MOTORU (TREND MAGIC) ---
def super_algoritma_hesapla(df):
    # Basit ama etkili bir SuperTrend benzeri mantık
    # 1. ATR Hesapla (Oynaklık)
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = true_range.rolling(14).mean()
    
    # 2. Üst ve Alt Bantlar
    multiplier = 3.0
    upper_band = ((df['High'] + df['Low']) / 2) + (multiplier * atr)
    lower_band = ((df['High'] + df['Low']) / 2) - (multiplier * atr)
    
    # 3. Trend Yönünü Belirle
    in_uptrend = True
    trend_data = []
    
    # Basitleştirilmiş Trend Takibi
    close = df['Close'].values
    upper = upper_band.values
    lower = lower_band.values
    
    trend = np.zeros(len(df))
    trend[0] = 1
    
    for i in range(1, len(df)):
        if close[i] > upper[i-1]:
            trend[i] = 1 # Yükseliş
        elif close[i] < lower[i-1]:
            trend[i] = -1 # Düşüş
        else:
            trend[i] = trend[i-1] # Değişim yok
            
            # Bantları sıkılaştır
            if trend[i] == 1 and lower[i] < lower[i-1]: lower[i] = lower[i-1]
            if trend[i] == -1 and upper[i] > upper[i-1]: upper[i] = upper[i-1]

    df['Trend'] = trend
    df['LowerBand'] = lower
    df['UpperBand'] = upper
    
    # Sinyal Noktaları (Oklar için)
    df['Buy_Signal'] = (df['Trend'] == 1) & (df['Trend'].shift(1) == -1)
    df['Sell_Signal'] = (df['Trend'] == -1) & (df['Trend'].shift(1) == 1)
    
    return df

# --- 3. ARAYÜZ VE GRAFİK ---

# --- ÜST BAR (ARAMA VE BİLGİ) ---
col_search, col_info = st.columns([1, 4])

with col_search:
    # Arama Kutusu (Varsayılan THYAO)
    hisse_kodu = st.text_input("HİSSE ARA (Örn: SASA, BTC-USD)", value="THYAO").upper()
    if not hisse_kodu.endswith(".IS") and not "-" in hisse_kodu and len(hisse_kodu) < 6:
        # BIST hissesi ise sonuna .IS ekleyelim (Kullanıcı yorulmasın)
        ticker_symbol = hisse_kodu + ".IS"
    else:
        ticker_symbol = hisse_kodu

# Veri Çekme
try:
    df = yf.download(ticker_symbol, period="1y", interval="1d", progress=False)
    
    if len(df) > 0:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
        
        # Algoritmayı Çalıştır
        df = super_algoritma_hesapla(df)
        son = df.iloc[-1]
        
        # Bilgi Paneli
        with col_info:
            c1, c2, c3, c4 = st.columns(4)
            delta_val = son['Close'] - df.iloc[-2]['Close']
            c1.metric("FİYAT", f"{son['Close']:.2f}", f"{delta_val:.2f}")
            
            durum = "YÜKSELİŞ TRENDİ 🚀" if son['Trend'] == 1 else "DÜŞÜŞ TRENDİ 🔻"
            renk = "normal" if son['Trend'] == 1 else "inverse"
            c2.metric("SİNYAL", durum, delta_color=renk)
            
            # Araçlar (Checkbox)
            with c3: show_ma = st.checkbox("Ortalamalar (EMA)", value=True)
            with c4: show_super = st.checkbox("Süper Algoritma", value=True)

        # --- GRAFİK ÇİZİMİ (TRADINGVIEW TARZI) ---
        fig = go.Figure()

        # 1. Mumlar
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name="Fiyat",
            increasing_line_color='#00FF41', decreasing_line_color='#FF3333'
        ))

        # 2. SÜPER ALGORİTMA (Çizgiler ve Oklar)
        if show_super:
            # Yeşil Hat (Destek)
            fig.add_trace(go.Scatter(
                x=df.index, y=df['LowerBand'], 
                mode='lines', line=dict(color='rgba(0, 255, 65, 0.4)', width=1), 
                name="Trend Desteği"
            ))
            # Kırmızı Hat (Direnç)
            fig.add_trace(go.Scatter(
                x=df.index, y=df['UpperBand'], 
                mode='lines', line=dict(color='rgba(255, 51, 51, 0.4)', width=1), 
                name="Trend Direnci"
            ))

            # AL SİNYALİ (YEŞİL OK)
            buy_signals = df[df['Buy_Signal']]
            fig.add_trace(go.Scatter(
                x=buy_signals.index, y=buy_signals['Low'] * 0.98,
                mode='markers', 
                marker=dict(symbol='triangle-up', size=15, color='#00FF41'),
                name="AL SİNYALİ"
            ))

            # SAT SİNYALİ (KIRMIZI OK)
            sell_signals = df[df['Sell_Signal']]
            fig.add_trace(go.Scatter(
                x=sell_signals.index, y=sell_signals['High'] * 1.02,
                mode='markers', 
                marker=dict(symbol='triangle-down', size=15, color='#FF3333'),
                name="SAT SİNYALİ"
            ))

        # 3. Ekstra Araçlar (EMA vb.)
        if show_ma:
            df['EMA50'] = df['Close'].ewm(span=50).mean()
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], line=dict(color='yellow', width=1), name="EMA 50"))

        # GRAFİK AYARLARI (ÇİZİM ARAÇLARI AKTİF)
        fig.update_layout(
            height=650, # Ekranı kaplasın
            template="plotly_dark",
            paper_bgcolor='black', plot_bgcolor='black',
            xaxis_rangeslider_visible=False,
            margin=dict(l=0, r=0, t=0, b=0),
            # Çizim Modu Butonları
            dragmode='pan', # Varsayılan kaydırma
            modebar=dict(
                orientation='v', # Dikey Toolbar
                bgcolor='#222',
                color='#00FF41',
                activecolor='white'
            )
        )
        
        # TRADINGVIEW GİBİ ÇİZİM ARAÇLARI EKLİYORUZ
        config = {
            'scrollZoom': True,
            'displayModeBar': True,
            'modeBarButtonsToAdd': [
                'drawline', 'drawopenpath', 'drawcircle', 'drawrect', 'eraseshape'
            ],
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }

        st.plotly_chart(fig, use_container_width=True, config=config)

    else:
        st.error("Hisse bulunamadı. Lütfen kodu doğru yazın (Örn: THYAO, GARAN).")

except Exception as e:
    st.error(f"Veri çekme hatası: {e}")
