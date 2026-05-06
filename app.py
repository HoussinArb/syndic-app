import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# 1. Configuration de la page
st.set_page_config(page_title="Syndic Mobile", layout="wide", page_icon="🏢")

# 2. Connexion à Google Sheets (utilise les configurations des Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Fonction pour charger les données proprement
def charger_donnees(nom_onglet):
    try:
        return conn.read(worksheet=nom_onglet)
    except Exception as e:
        st.error(f"Impossible de lire l'onglet '{nom_onglet}'. Vérifiez le nom dans Google Sheets.")
        return pd.DataFrame()

# 4. Chargement des données
df_m = charger_donnees("membres")
df_p = charger_donnees("paiements")
df_d = charger_donnees("depenses")

# --- INTERFACE UTILISATEUR ---
st.title("🏢 Gestion Syndic")

if df_m.empty:
    st.warning("La liste des membres est vide ou inaccessible.")
else:
    tab1, tab2, tab3 = st.tabs(["📊 État Global", "💰 Encaisser", "💸 Dépenses"])

    # --- ONGLET 1 : DASHBOARD ---
    with tab1:
        col1, col2, col3 = st.columns(3)
        recettes = df_p['montant'].sum() if not df_p.empty else 0
        depenses = df_d['montant'].sum() if not df_d.empty else 0
        
        col1.metric("Total Recettes", f"{recettes} DH")
        col2.metric("Total Dépenses", f"{depenses} DH")
        col3.metric("Solde en Caisse", f"{recettes - depenses} DH", delta_color="normal")

    # --- ONGLET 2 : PAIEMENTS ---
    with tab2:
        st.subheader("Enregistrer une cotisation")
        with st.form("form_paiement"):
            # Création d'une liste déroulante : Nom du membre (Appartement)
            options_membres = {f"{r['nom']} - Appt {r['appartement']}": r['id'] for _, r in df_m.iterrows()}
            choix = st.selectbox("Choisir le copropriétaire", options=options_membres.keys())
            montant_saisie = st.number_input("Montant versé (DH)", min_value=0, step=50)
            
            if st.form_submit_button("Valider le paiement"):
                new_row = pd.DataFrame([{
                    "id": len(df_p) + 1,
                    "membre_id": options_membres[choix],
                    "montant": montant_saisie,
                    "date_paiement": str(date.today())
                }])
                df_p_updated = pd.concat([df_p, new_row], ignore_index=True)
                conn.update(worksheet="paiements", data=df_p_updated)
                st.success(f"Paiement de {montant_saisie} DH enregistré !")
                st.rerun()

    # --- ONGLET 3 : DEPENSES ---
    with tab3:
        st.subheader("Ajouter une dépense")
        with st.form("form_depense"):
            titre = st.text_input("Objet de la dépense")
            montant_d = st.number_input("Montant (DH)", min_value=0)
            cat = st.selectbox("Catégorie", ["Entretien", "Électricité", "Eau", "Réparation", "Autre"])
            
            if st.form_submit_button("Enregistrer la dépense"):
                new_dep = pd.DataFrame([{
                    "id": len(df_d) + 1,
                    "titre": titre,
                    "montant": montant_d,
                    "date_depense": str(date.today()),
                    "categorie": cat
                }])
                df_d_updated = pd.concat([df_d, new_dep], ignore_index=True)
                conn.update(worksheet="depenses", data=df_d_updated)
                st.success("Dépense enregistrée !")
                st.rerun()
