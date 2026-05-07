import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Vos GIDs qui fonctionnent
GID_MEMBRES = "0"
GID_PAIEMENTS = "469308404"
GID_DEPENSES = "108011384" # À récupérer dans votre barre d'adresse

# 2. Fonction de lecture sécurisée (celle qui a fonctionné)
def charger_csv(gid):
    url = f"https://docs.google.com/spreadsheets/d/1HYzTP9oGbv3yDprhmPLG39XS07qdej8GTSsN0ObxIes/export?format=csv&gid={gid}"
    return pd.read_csv(url)

# 3. On charge les données pour l'affichage
df_m = charger_csv(GID_MEMBRES)
df_p = charger_csv(GID_PAIEMENTS)

# 4. Connexion pour l'écriture (comme sur PC)
conn = st.connection("gsheets", type=GSheetsConnection)

# --- VOTRE CODE PC POUR L'INTERFACE ICI ---
st.title("🏢 Syndic Mobile")
st.write("Liste des membres :", df_m)

# Quand vous voudrez enregistrer un paiement (bouton Valider) :
# Utilisez conn.update(worksheet="paiements", data=votre_df_modifié)
