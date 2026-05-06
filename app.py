import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# Configuration
st.set_page_config(page_title="Syndic Mobile", layout="wide")

# --- RÉGLAGES ---
# Remplace par ton ID réel
SHEET_ID = "1_dyIcBZaX-GHZ_OApEuS77nxGsNrcgaNa7i1A7VFLAQ"

# Fonction pour obtenir l'URL CSV de chaque onglet
def get_url(gid):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"

# IDs des onglets (GID) - À vérifier dans ton navigateur
URL_MEMBRES = get_url("0")           # Souvent 0
URL_PAIEMENTS = get_url("469308404")   # Remplace par le GID de l'onglet paiements
URL_DEPENSES = get_url("108011384")    # Remplace par le GID de l'onglet depenses

# Connexion pour l'écriture (update)
conn = st.connection("gsheets", type=GSheetsConnection)

def charger(url):
    try:
        return pd.read_csv(url)
    except:
        return pd.DataFrame()

# Chargement
df_m = charger(URL_MEMBRES)
df_p = charger(URL_PAIEMENTS)
df_d = charger(URL_DEPENSES)

st.title("🏢 Syndic Mobile - Opérationnel")

if df_m.empty:
    st.error("Problème de lecture des membres.")
else:
    t1, t2, t3 = st.tabs(["📊 État", "💰 Encaisser", "💸 Dépenses"])

    with t1:
        col1, col2 = st.columns(2)
        p_total = df_p['montant'].sum() if not df_p.empty else 0
        d_total = df_d['montant'].sum() if not df_d.empty else 0
        col1.metric("Recettes", f"{p_total} DH")
        col2.metric("Dépenses", f"{d_total} DH")
        st.dataframe(df_p.tail(5), use_container_width=True)

    with t2:
        with st.form("p"):
            membres_list = {f"{r['nom']} ({r['appartement']})": r['id'] for _, r in df_m.iterrows()}
            choix = st.selectbox("Membre", options=membres_list.keys())
            mt = st.number_input("Montant", min_value=0)
            if st.form_submit_button("Valider"):
                new_row = pd.DataFrame([{"id": len(df_p)+1, "membre_id": membres_list[choix], "montant": mt, "date_paiement": str(date.today())}])
                df_p = pd.concat([df_p, new_row], ignore_index=True)
                conn.update(worksheet="paiements", data=df_p)
                st.success("Payé !")
                st.rerun()
