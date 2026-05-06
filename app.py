import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- CONFIGURATION ---
st.set_page_config(page_title="Syndic Mobile", layout="wide")

# Connexion via les "Secrets" (configurés sur Streamlit Cloud)
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FONCTIONS DE CHARGEMENT ---
def charger_donnees(onglet):
    # Lit l'onglet spécifié dans la Google Sheet définie dans les Secrets
    return conn.read(worksheet=onglet)

# --- CHARGEMENT ---
try:
    df_m = charger_donnees("membres")
    df_p = charger_donnees("paiements")
    df_d = charger_donnees("depenses")
except Exception as e:
    st.error("Erreur de connexion à Google Sheets. Vérifiez vos Secrets !")
    st.stop()

# --- INTERFACE ---
st.title("🏢 Syndic Mobile")

tab1, tab2, tab3 = st.tabs(["📊 État", "💰 Encaisser", "⚙️ Admin"])

with tab1:
    col1, col2 = st.columns(2)
    col1.metric("Total Recettes", f"{df_p['montant'].sum()} DH")
    col2.metric("Total Dépenses", f"{df_d['montant'].sum()} DH")

with tab2:
    st.subheader("Nouveau Paiement")
    with st.form("p_form"):
        # On prépare la liste des membres pour le menu déroulant
        choix = {f"{r['nom']} ({r['appartement']})": r['id'] for _, r in df_m.iterrows()}
        membre = st.selectbox("Copropriétaire", options=choix.keys())
        montant = st.number_input("Montant", min_value=0)
        if st.form_submit_button("Valider"):
            new_line = pd.DataFrame([{"id": len(df_p)+1, "membre_id": choix[membre], "montant": montant, "date_paiement": str(date.today())}])
            df_p_new = pd.concat([df_p, new_line], ignore_index=True)
            conn.update(worksheet="paiements", data=df_p_new)
            st.success("Enregistré !")
            st.rerun()

with tab3:
    st.write("Gestion des membres via Google Sheets directement pour l'instant.")
