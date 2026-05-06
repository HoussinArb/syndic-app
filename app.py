import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# Configuration de la page
st.set_page_config(page_title="Syndic Mobile", layout="wide")

# --- 1. CONFIGURATION (METS TES INFOS ICI) ---
SHEET_ID = "1_dyIcBZaX-GHZ_OApEuS77nxGsNrcgaNa7i1A7VFLAQ" # L'ID entre /d/ et /edit

# Remplace par tes vrais GID trouvés tout à l'heure
GID_MEMBRES = "0" 
GID_PAIEMENTS = "469308404" 
GID_DEPENSES = "108011384" 

# --- 2. FONCTIONS DE LECTURE ---
def get_csv_url(gid):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"

@st.cache_data(ttl=60) # Garde en mémoire 1 minute pour la rapidité
def charger_donnees(url):
    try:
        return pd.read_csv(url)
    except Exception as e:
        return pd.DataFrame()

# Chargement
df_m = charger_donnees(get_csv_url(GID_MEMBRES))
df_p = charger_donnees(get_csv_url(GID_PAIEMENTS))
df_d = charger_donnees(get_csv_url(GID_DEPENSES))

# --- 3. CONNEXION POUR L'ÉCRITURE ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    conn = None

st.title("🏢 Syndic Mobile")

if df_m.empty:
    st.error("⚠️ Erreur de lecture : Vérifiez l'ID et les GID.")
else:
    tab1, tab2, tab3 = st.tabs(["📊 État", "💰 Encaisser", "💸 Dépenses"])

    with tab1:
        c1, c2 = st.columns(2)
        # Calcul sécurisé des montants
        total_recettes = pd.to_numeric(df_p['montant'], errors='coerce').sum() if not df_p.empty else 0
        total_depenses = pd.to_numeric(df_d['montant'], errors='coerce').sum() if not df_d.empty else 0
        
        c1.metric("Recettes", f"{total_recettes} DH")
        c2.metric("Dépenses", f"{total_depenses} DH")
        
        st.subheader("Historique récent")
        st.dataframe(df_p.tail(10), use_container_width=True)

    with tab2:
        st.subheader("Enregistrer un paiement")
        # On vérifie si conn est disponible pour l'écriture
        if conn:
            with st.form("form_p"):
                options = {f"{r['nom']} ({r['appartement']})": r['id'] for _, r in df_m.iterrows()}
                choix = st.selectbox("Copropriétaire", options=options.keys())
                montant = st.number_input("Montant", min_value=0, step=50)
                
                if st.form_submit_button("Valider le paiement"):
                    try:
                        new_data = pd.DataFrame([{
                            "id": len(df_p) + 1,
                            "membre_id": options[choix],
                            "montant": montant,
                            "date_paiement": str(date.today())
                        }])
                        # On concatène l'ancien et le nouveau
                        updated_df = pd.concat([df_p, new_data], ignore_index=True)
                        # Tentative d'envoi vers Google
                        conn.update(worksheet="paiements", data=updated_df)
                        st.success("✅ Paiement enregistré !")
                        st.cache_data.clear() # Force la mise à jour de l'affichage
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur d'écriture : {e}")
        else:
            st.warning("⚠️ Mode lecture seule : La connexion d'écriture n'est pas active.")

    with tab3:
        st.subheader("Nouvelle dépense")
        if conn:
            with st.form("form_d"):
                objet = st.text_input("Objet")
                m_depense = st.number_input("Montant dépense", min_value=0)
                if st.form_submit_button("Enregistrer"):
                    new_dep = pd.DataFrame([{"id": len(df_d)+1, "titre": objet, "montant": m_depense, "date_depense": str(date.today())}])
                    updated_d = pd.concat([df_d, new_dep], ignore_index=True)
                    conn.update(worksheet="depenses", data=updated_d)
                    st.success("✅ Dépense enregistrée !")
                    st.cache_data.clear()
                    st.rerun()
