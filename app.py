import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# Configuration
st.set_page_config(page_title="Syndic Mobile", layout="wide")

# --- RÉGLAGES ---
# REMPLACE PAR TON ID RÉEL
SHEET_ID = "1_dyIcBZaX-GHZ_OApEuS77nxGsNrcgaNa7i1A7VFLAQ" 

# Fonction pour obtenir l'URL CSV (Lecture)
def get_url(gid):
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"

# Remplace les GID ci-dessous par ceux de tes onglets (visibles dans l'URL Google Sheets)
URL_MEMBRES = get_url("0") 
URL_PAIEMENTS = get_url("469308404") # <--- METS TON GID ICI
URL_DEPENSES = get_url("108011384")  # <--- METS TON GID ICI

# Connexion pour l'écriture uniquement
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    conn = None

def charger(url):
    try:
        # On ajoute un paramètre aléatoire pour éviter le cache Google
        return pd.read_csv(f"{url}&nocache={date.today()}")
    except:
        return pd.DataFrame()

# Chargement initial
df_m = charger(URL_MEMBRES)
df_p = charger(URL_PAIEMENTS)
df_d = charger(URL_DEPENSES)

st.title("🏢 Syndic Mobile")

if df_m.empty:
    st.error("Impossible de lire l'onglet 'membres'. Vérifiez le SHEET_ID et le GID.")
else:
    t1, t2, t3 = st.tabs(["📊 État", "💰 Encaisser", "💸 Dépenses"])

    with t1:
        col1, col2 = st.columns(2)
        # On s'assure que 'montant' est bien numérique
        if not df_p.empty and 'montant' in df_p.columns:
            df_p['montant'] = pd.to_numeric(df_p['montant'], errors='coerce')
            p_total = df_p['montant'].sum()
        else:
            p_total = 0
            
        if not df_d.empty and 'montant' in df_d.columns:
            df_d['montant'] = pd.to_numeric(df_d['montant'], errors='coerce')
            d_total = df_d['montant'].sum()
        else:
            d_total = 0

        col1.metric("Recettes", f"{p_total} DH")
        col2.metric("Dépenses", f"{d_total} DH")
        st.subheader("Derniers paiements")
        st.dataframe(df_p.tail(10), use_container_width=True)

    with t2:
        st.subheader("Nouveau paiement")
        if conn is not None:
            with st.form("form_p"):
                membres_list = {f"{r['nom']} ({r['appartement']})": r['id'] for _, r in df_m.iterrows()}
                choix = st.selectbox("Copropriétaire", options=membres_list.keys())
                mt = st.number_input("Montant (DH)", min_value=0, step=50)
                
                if st.form_submit_button("Enregistrer"):
                    new_p = pd.DataFrame([{
                        "id": len(df_p) + 1,
                        "membre_id": membres_list[choix],
                        "montant": mt,
                        "date_paiement": str(date.today())
                    }])
                    df_p_full = pd.concat([df_p, new_p], ignore_index=True)
                    # Tentative d'écriture
                    conn.update(worksheet="paiements", data=df_p_full)
                    st.success("✅ Enregistré !")
                    st.rerun()
        else:
            st.error("L'écriture n'est pas configurée (Vérifiez les Secrets).")

    with t3:
        st.subheader("Nouvelle dépense")
        with st.form("form_d"):
            titre = st.text_input("Objet")
            mt_d = st.number_input("Montant", min_value=0)
            if st.form_submit_button("Valider"):
                new_d = pd.DataFrame([{"id": len(df_d)+1, "titre": titre, "montant": mt_d, "date_depense": str(date.today())}])
                df_d_full = pd.concat([df_d, new_d], ignore_index=True)
                conn.update(worksheet="depenses", data=df_d_full)
                st.success("✅ Dépense enregistrée !")
                st.rerun()
