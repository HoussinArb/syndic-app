import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Syndic Mobile", layout="wide")

# --- CONNEXION À GOOGLE SHEETS ---
# URL de votre feuille (celle que vous avez copiée)
url_gsheet = "https://docs.google.com/spreadsheets/d/1HYzTP9oGbv3yDprhmPLG39XS07qdej8GTSsN0ObxIes/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

def charger_donnees(onglet):
    return conn.read(spreadsheet=url_gsheet, worksheet=onglet)

# --- CHARGEMENT DES DONNÉES ---
df_m = charger_donnees("membres")
df_p = charger_donnees("paiements")
df_d = charger_donnees("depenses")

# --- INTERFACE ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "💰 Paiements", "💸 Dépenses", "⚙️ Admin"])

with tab1:
    st.title("Tableau de Bord Syndic")
    # Calculs simples avec Pandas
    total_recu = df_p['montant'].sum()
    total_depenses = df_d['montant'].sum()
    st.metric("Solde Caisse", f"{total_recu - total_depenses} DH")

with tab2:
    st.subheader("Encaisser une cotisation")
    with st.form("ajout_paiement"):
        # On crée une liste pour le menu déroulant : "NOM (Appt)"
        liste_membres = {f"{row['nom']} ({row['appartement']})": row['id'] for _, row in df_m.iterrows()}
        membre_sel = st.selectbox("Copropriétaire", options=liste_membres.keys())
        montant = st.number_input("Montant (DH)", min_value=0)
        
        if st.form_submit_button("Enregistrer le paiement"):
            new_p = pd.DataFrame([{"id": len(df_p)+1, "membre_id": liste_membres[membre_sel], 
                                   "montant": montant, "date_paiement": str(date.today())}])
            # On ajoute la ligne au tableau existant
            df_p_updated = pd.concat([df_p, new_p], ignore_index=True)
            conn.update(spreadsheet=url_gsheet, worksheet="paiements", data=df_p_updated)
            st.success("Paiement enregistré sur le Cloud !")
            st.rerun()

# --- NOTE POUR L'ADMIN (L'AJOUT DE MEMBRE) ---
with tab4:
    st.subheader("Ajouter un Copropriétaire")
    with st.form("nouveau_membre"):
        n_nom = st.text_input("Nom")
        n_app = st.text_input("N° Appartement")
        n_em = st.text_input("Email")
        if st.form_submit_button("Créer le compte"):
            new_m = pd.DataFrame([{"id": len(df_m)+1, "nom": n_nom.upper(), 
                                   "appartement": n_app, "email": n_em}])
            df_m_updated = pd.concat([df_m, new_m], ignore_index=True)
            conn.update(spreadsheet=url_gsheet, worksheet="membres", data=df_m_updated)
            st.success("Membre ajouté !")
            st.rerun()
