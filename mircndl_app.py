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
        progress
