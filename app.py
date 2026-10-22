import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

# ==========================================
# CONFIGURAZIONE ORARIO DI SCADENZA (MODIFICA QUI)
# ==========================================
# Imposta l'anno, mese, giorno, ora e minuto in cui l'app deve BLOCCARSI
ORARIO_SCADENZA = datetime(2026, 10, 22, 14, 0) # Esempio: 22 Ottobre 2026 alle 14:00

# Controllo immediato della scadenza
if datetime.now() > ORARIO_SCADENZA:
    st.error("❌ IL PERIODO DI PROVA È SCADUTO. L'accesso a questa applicazione è stato bloccato.")
    st.stop()

# ==========================================
# CONFIGURAZIONE PAGINA
# ==========================================
st.set_page_config(page_title="Dashboard Roulette", layout="wide")
st.title("🔥 DASHBOARD ROULETTE - MODALITÀ AGGRESSIVA")

VALORE_UNITA_BASE = 0.10
MAX_COLPI_CICLO = 5
ROSSI = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

# Inizializzazione dello Stato della Sessione
if 'bankroll_iniziale' not in st.session_state:
    st.session_state.bankroll_iniziale = 50.0
    st.session_state.bankroll = 50.0
    st.session_state.peak_bankroll = 50.0
    st.session_state.cronologia = []
    st.session_state.ciclo_attivo = False
    st.session_state.numeri_correnti = []
    st.session_state.colpo_attuale_ciclo = 0
    st.session_state.pezzi_per_numero = 2
    st.session_state.numeri_esclusi = set()

# ==========================================
# FUNZIONI DI LOGICA
# ==========================================
def estrai_numeri_da_html(contenuto_html):
    soup = BeautifulSoup(contenuto_html, 'html.parser')
    numeri = []
    elementi = soup.find_all(lambda tag: tag.has_attr('data-role') and tag['data-role'].startswith('number-'))
    for el in elementi:
        valore_str = el['data-role'].replace('number-', '').strip()
        if valore_str.isdigit():
            val = int(valore_str)
            if 0 <= val <= 36:
                numeri.append(val)
    if not numeri:
        spans = soup.find_all('span', class_='YLMNPL')
        for s in spans:
            txt = s.get_text().strip()
            if txt.isdigit() and 0 <= int(txt) <= 36:
                numeri.append(int(txt))
    return numeri[::-1]

def calcola_pezzi(bankroll_attuale, bankroll_iniziale):
    if bankroll_iniziale <= 0:
        return 2
    pezzi_base = max(2, int(bankroll_iniziale / 25.0))
    delta = (bankroll_attuale - bankroll_iniziale) / bankroll_iniziale
    if delta >= 0.40: return int(pezzi_base * 2.5)
    elif delta >= 0.20: return int(pezzi_base * 1.8)
    elif delta >= 0.10: return int(pezzi_base * 1.4)
    elif delta >= -0.05: return pezzi_base
    elif delta <= -0.10: return max(1, int(pezzi_base * 0.5))
    return pezzi_base

def elabora_tiro(nuovo_numero, quantita_numeri):
    st.session_state.cronologia.append(nuovo_numero)
    crono = st.session_state.cronologia

    if st.session_state.ciclo_attivo:
        pezzi = st.session_state.pezzi_per_numero
        costo_fiches = pezzi * VALORE_UNITA_BASE
        spesa = quantita_numeri * costo_fiches
        st.session_state.bankroll -= spesa
        st.session_state.colpo_attuale_ciclo += 1

        if nuovo_numero in st.session_state.numeri_correnti:
            vincita = (costo_fiches * 35) + costo_fiches
            st.session_state.bankroll += vincita
            st.session_state.ciclo_attivo = False
            st.session_state.numeri_esclusi = set(st.session_state.numeri_correnti)
            st.session_state.pezzi_per_numero = calcola_pezzi(st.session_state.bankroll, st.session_state.bankroll_iniziale)
        else:
            if st.session_state.colpo_attuale_ciclo >= MAX_COLPI_CICLO or st.session_state.bankroll < (quantita_numeri * VALORE_UNITA_BASE):
                st.session_state.ciclo_attivo = False
                st.session_state.numeri_esclusi = set(st.session_state.numeri_correnti)
                st.session_state.pezzi_per_numero = calcola_pezzi(st.session_state.bankroll, st.session_state.bankroll_iniziale)

    costo_prossimo = quantita_numeri * st.session_state.pezzi_per_numero * VALORE_UNITA_BASE
    if not st.session_state.ciclo_attivo and st.session_state.bankroll >= costo_prossimo:
        if len(crono) >= 5:
            ultimi_dati = pd.Series(crono[-120:])
            frequenze = ultimi_dati.value_counts()
            scelti = [num for num in frequenze.index if num not in st.session_state.numeri_esclusi][:quantita_numeri]
            if len(scelti) < quantita_numeri:
                for n in range(37):
                    if n not in scelti and n not in st.session_state.numeri_esclusi:
                        scelti.append(n)
                    if len(scelti) == quanti_numeri: break
        else:
            scelti = list(range(quantita_numeri))
        scelti.sort()
        st.session_state.numeri_correnti = scelti
        st.session_state.ciclo_attivo = True
        st.session_state.colpo_attuale_ciclo = 0

    if st.session_state.bankroll > st.session_state.peak_bankroll:
        st.session_state.peak_bankroll = st.session_state.bankroll

# ==========================================
# INTERFACCIA UTENTE
# ==========================================
st.sidebar.header("1. Setup Iniziale")
html_input = st.sidebar.text_area("Incolla codice HTML dei numeri:")
saldo_input = st.sidebar.number_input("Saldo Iniziale (€)", value=50.0, step=5.0)
quanti_input = st.sidebar.selectbox("Numeri Previsione", options=list(range(1, 9)), index=2)

if st.sidebar.button("Carica HTML & Inizia"):
    st.session_state.bankroll_iniziale = saldo_input
    st.session_state.bankroll = saldo_input
    st.session_state.peak_bankroll = saldo_input
    st.session_state.pezzi_per_numero = calcola_pezzi(saldo_input, saldo_input)
    st.session_state.ciclo_attivo = False
    if html_input.strip():
        st.session_state.cronologia = estrai_numeri_da_html(html_input)
        st.sidebar.success(f"Estratti {len(st.session_state.cronologia)} numeri!")
    else:
        st.session_state.cronologia = []

st.header("2. Tappeto Roulette")
cols = st.columns(13)

# Bottone Zero
if cols[0].button("0", key="num_0", use_container_width=True):
    elabora_tiro(0, quanti_input)

# Bottoni 1-36
riga1 = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36]
riga2 = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35]
riga3 = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]

for idx, col in enumerate(cols[1:], start=0):
    with col:
        if st.button(str(riga1[idx]), key=f"num_{riga1[idx]}", use_container_width=True):
            elabora_tiro(riga1[idx], quanti_input)
        if st.button(str(riga2[idx]), key=f"num_{riga2[idx]}", use_container_width=True):
            elabora_tiro(riga2[idx], quanti_input)
        if st.button(str(riga3[idx]), key=f"num_{riga3[idx]}", use_container_width=True):
            elabora_tiro(riga3[idx], quanti_input)

# DASHBOARD RISULTATI
st.markdown("---")
col_a, col_b, col_c = st.columns(3)
col_a.metric("Cassa Attuale", f"{st.session_state.bankroll:.2f} €")
col_b.metric("Picco Massimo", f"{st.session_state.peak_bankroll:.2f} €")
col_c.metric("Profitto/Perdita", f"{st.session_state.bankroll - st.session_state.bankroll_iniziale:+.2f} €")

if st.session_state.ciclo_attivo:
    st.success(f"🎯 NUMERI DA PUNTARE: {', '.join(map(str, st.session_state.numeri_correnti))}")
