import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# Configuration de la page
st.set_page_config(page_title="Syndic Mobile", layout="wide", page_icon="🏢")

# 1. Connexion à Google Sheets
# Cette ligne utilise les informations de tes "Secrets"
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. Fonction de chargement avec gestion d'erreur précise
def charger_donnees(nom_onglet):
    try:
        # On force la lecture de l'onglet spécifique
        # ttl=0 permet d'éviter de lire de vieilles données en cache
        data = conn.read(worksheet=nom_onglet, ttl=0)
        return data
    except Exception as e:
        # Si ça rate, on affiche l'erreur exacte pour comprendre pourquoi
        st.error(f"⚠️ Erreur sur l'onglet '{nom_onglet}' : {e}")
        return pd.DataFrame()

# 3. Chargement des données au démarrage
df_m = charger_donnees("membres")
df_p = charger_donnees("paiements")
df_d = charger_donnees("depenses")

# --- INTERFACE UTILISATEUR ---
st.title("🏢 Gestion Syndic Mobile")

# On vérifie si l'onglet membres a bien été lu et n'est pas vide
if df_m.empty:
    st.warning("La liste des membres est vide ou inaccessible. Vérifiez vos colonnes (id, nom, appartement) et le partage du fichier.")
else:
    tab1, tab2, tab3 = st.tabs(["📊 État Global", "💰 Encaisser", "💸 Dépenses"])

    # ONGLET 1 : RÉSUMÉ
    with tab1:
        col1, col2 = st.columns(2)
        
        # Calcul des totaux si les colonnes existent
        recettes = df_p['montant'].sum() if not df_p.empty and 'montant' in df_p.columns else 0
        depenses = df_d['montant'].sum() if not df_d.empty and 'montant' in df_d.columns else 0
        
        col1.metric("Total Recettes", f"{recettes} DH")
        col2.metric("Total Dépenses", f"{depenses} DH")
        
        st.divider()
        st.subheader("Historique des paiements")
        if not df_p.empty:
            st.dataframe(df_p.tail(10), use_container_width=True)
        else:
            st.info("Aucun paiement enregistré pour le moment.")

    # ONGLET 2 : FORMULAIRE DE PAIEMENT
    with tab2:
        st.subheader("Enregistrer un nouveau paiement")
        with st.form("form_paiement"):
            # On crée une liste pour le menu déroulant
            options_membres = {f"{r['nom']} (Appt {r['appartement']})": r['id'] for _, r in df_m.iterrows()}
            choix = st.selectbox("Choisir le copropriétaire", options=options_membres.keys())
            montant_p = st.number_input("Montant versé (DH)", min_value=0, step=50)
            
            if st.form_submit_button("Confirmer le paiement"):
                # Création de la nouvelle ligne
                nouveau_p = pd.DataFrame([{
                    "id": len(df_p) + 1,
                    "membre_id": options_membres[choix],
                    "montant": montant_p,
                    "date_paiement": str(date.today())
                }])
                # Fusion et mise à jour de la feuille Google
                df_p_maj = pd.concat([df_p, nouveau_p], ignore_index=True)
                conn.update(worksheet="paiements", data=df_p_maj)
                st.success("✅ Paiement enregistré dans Google Sheets !")
                st.rerun()

    # ONGLET 3 : FORMULAIRE DE DÉPENSE
    with tab3:
        st.subheader("Ajouter une dépense du syndic")
        with st.form("form_depense"):
            titre_d = st.text_input("Objet de la dépense (ex: Électricité, Ménage)")
            montant_d = st.number_input("Montant payé (DH)", min_value=0)
            
            if st.form_submit_button("Enregistrer la dépense"):
                nouvelle_d = pd.DataFrame([{
                    "id": len(df_d) + 1,
                    "titre": titre_d,
                    "montant": montant_d,
                    "date_depense": str(date.today())
                }])
                df_d_maj = pd.concat([df_d, nouvelle_d], ignore_index=True)
                conn.update(worksheet="depenses", data=df_d_maj)
                st.success("✅ Dépense enregistrée !")
                st.rerun()
