import streamlit as st
import pandas as pd
from datetime import date

# Configuration
st.set_page_config(page_title="Syndic Mobile", layout="wide")

# --- RÉGLAGE : REMPLACEZ L'ID CI-DESSOUS PAR LE VÔTRE ---
SHEET_ID = "1_dyIcBZaX-GHZ_OApEuS77nxGsNrcgaNa7i1A7VFLAQ"

# Liens directs vers les onglets au format CSV
# gid=0 est souvent l'ID de l'onglet 'membres', vérifiez l'URL de vos onglets pour les GID
URL_MEMBRES = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

st.title("🏢 Gestion Syndic (Version Directe)")

def charger_donnees():
    try:
        # On lit directement le lien CSV public
        df = pd.read_csv(URL_MEMBRES)
        return df
    except Exception as e:
        st.error(f"Impossible de lire le fichier : {e}")
        return pd.DataFrame()

df_m = charger_donnees()

if df_m.empty:
    st.warning("⚠️ Les données ne montent pas. Vérifiez que le fichier est en 'Public - Tous les utilisateurs disposant du lien'.")
    st.info(f"Tentative de lecture sur : {URL_MEMBRES}")
else:
    st.success("✅ Connexion réussie !")
    st.subheader("Liste des membres")
    st.write(df_m)
    
    # Formulaire simplifié pour tester
    with st.form("test"):
        nom = st.text_input("Ajouter un nom pour tester")
        if st.form_submit_button("Envoyer"):
            st.write("Test de bouton réussi !")
