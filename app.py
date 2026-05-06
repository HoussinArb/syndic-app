import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# Configuration de la page
st.set_page_config(page_title="Syndic Mobile", layout="wide", page_icon="🏢")

# Connexion à Google Sheets
# --- REMPLACE LA LIGNE 11 PAR CELLE-CI ---
# On utilise directement le lien CSV (remplace TON_ID par ton vrai ID)
URL_MEMBRES = "https://docs.google.com/spreadsheets/d/1HYzTP9oGbv3yDprhmPLG39XS07qdej8GTSsN0ObxIes/gviz/tq?tqx=out:csv&sheet=membres"

def charger_donnees_test():
    try:
        return pd.read_csv(URL_MEMBRES)
    except Exception as e:
        st.error(f"Erreur de lecture directe : {e}")
        return pd.DataFrame()

df_m = charger_donnees_test()
# ... garde le reste du code identique ...

# Fonction de chargement sécurisée
def charger_donnees(nom_onglet):
    try:
        # On lit l'onglet avec ttl=0 pour avoir les données en temps réel
        data = conn.read(worksheet=nom_onglet, ttl=0)
        return data
    except Exception as e:
        st.error(f"Erreur sur l'onglet '{nom_onglet}' : {e}")
        return pd.DataFrame()

# Chargement des 3 onglets
df_m = charger_donnees("membres")
df_p = charger_donnees("paiements")
df_d = charger_donnees("depenses")

# --- INTERFACE ---
st.title("🏢 Gestion Syndic Mobile")

# Vérification si les données membres sont chargées
if df_m.empty:
    st.warning("⚠️ Impossible de charger la liste des membres. Vérifiez l'ID dans les Secrets et le nom de l'onglet.")
else:
    tab1, tab2, tab3 = st.tabs(["📊 État", "💰 Encaisser", "💸 Dépenses"])

    with tab1:
        col1, col2 = st.columns(2)
        total_p = df_p['montant'].sum() if not df_p.empty else 0
        total_d = df_d['montant'].sum() if not df_d.empty else 0
        col1.metric("Recettes", f"{total_p} DH")
        col2.metric("Dépenses", f"{total_d} DH")
        st.divider()
        st.subheader("Derniers paiements")
        st.dataframe(df_p.tail(5), use_container_width=True)

    with tab2:
        st.subheader("Enregistrer un paiement")
        with st.form("form_p"):
            # Liste déroulante des membres
            liste_membres = {f"{r['nom']} (Appt {r['appartement']})": r['id'] for _, r in df_m.iterrows()}
            membre_choisi = st.selectbox("Copropriétaire", options=liste_membres.keys())
            montant = st.number_input("Montant (DH)", min_value=0, step=50)
            
            if st.form_submit_button("Valider"):
                new_p = pd.DataFrame([{
                    "id": len(df_p) + 1,
                    "membre_id": liste_membres[membre_choisi],
                    "montant": montant,
                    "date_paiement": str(date.today())
                }])
                df_p_ext = pd.concat([df_p, new_p], ignore_index=True)
                conn.update(worksheet="paiements", data=df_p_ext)
                st.success("Paiement enregistré !")
                st.rerun()

    with tab3:
        st.subheader("Nouvelle dépense")
        with st.form("form_d"):
            objet = st.text_input("Objet")
            m_depense = st.number_input("Montant", min_value=0)
            if st.form_submit_button("Enregistrer"):
                new_d = pd.DataFrame([{
                    "id": len(df_d) + 1,
                    "titre": objet,
                    "montant": m_depense,
                    "date_depense": str(date.today())
                }])
                df_d_ext = pd.concat([df_d, new_d], ignore_index=True)
                conn.update(worksheet="depenses", data=df_d_ext)
                st.success("Dépense enregistrée !")
                st.rerun()
