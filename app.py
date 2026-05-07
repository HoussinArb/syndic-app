import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURATION
st.set_page_config(page_title="Syndic Mimosa Agadir", layout="wide", page_icon="🏢")

# --- PARAMÈTRES GOOGLE SHEETS ---
# Remplace par l'ID de ton fichier (présent dans l'URL de ton navigateur)
SHEET_ID = "1HYzTP9oGbv3yDprhmPLG39XS07qdej8GTSsN0ObxIes" 
GID_MEMBRES = "0"
GID_PAIEMENTS = "469308404"
GID_DEPENSES = "108011384" 

# 2. LECTURE (Fonctionne sur PC et Mobile)
def charger_donnees_gid(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    df = pd.read_csv(url)
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

try:
    df_membres = charger_donnees_gid(GID_MEMBRES)
    df_paiements = charger_donnees_gid(GID_PAIEMENTS)
    df_depenses = charger_donnees_gid(GID_DEPENSES)
except Exception as e:
    st.error("Erreur de lecture. Vérifiez l'ID du fichier et le partage 'Lecteur'.")
    st.stop()

# Connexion pour l'écriture (Utilise tes secrets Streamlit)
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. FONCTIONS DE MISE À JOUR (Remplacent SQLite)
def mettre_a_jour_membre_cloud(id_membre, nom, prenom, appt, tel, email):
    df = conn.read(worksheet="membres")
    df.columns = [str(c).strip().lower() for c in df.columns]
    df.loc[df['id'] == id_membre, ['nom', 'prenom', 'appartement', 'tel', 'email']] = [
        nom.upper(), prenom.capitalize(), appt.upper(), tel, email
    ]
    conn.update(worksheet="membres", data=df)
    st.success("Modifications enregistrées !")
    st.rerun()

def supprimer_ligne_cloud(table, row_id):
    df = conn.read(worksheet=table)
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df[df['id'] != row_id]
    conn.update(worksheet=table, data=df)
    st.rerun()

# --- BARRE LATÉRALE : AJOUT COMPLET ---
st.sidebar.header("👤 Nouveau Copropriétaire")
with st.sidebar.form("ajout_membre", clear_on_submit=True):
    nom = st.text_input("Nom")
    prenom = st.text_input("Prénom")
    appt = st.text_input("N° Appartement")
    tel = st.text_input("Téléphone")
    email = st.text_input("Email")
    if st.form_submit_button("Ajouter à la résidence"):
        if nom and appt:
            new_id = int(df_membres['id'].max() + 1) if not df_membres.empty else 1
            new_m = pd.DataFrame([{"id": new_id, "nom": nom.upper(), "prenom": prenom.capitalize(), 
                                   "appartement": appt.upper(), "tel": tel, "email": email}])
            conn.update(worksheet="membres", data=pd.concat([df_membres, new_m], ignore_index=True))
            st.rerun()

# --- DASHBOARD ---
st.title("🏢 Syndic Mimosa Agadir")
cotisation_annuelle = st.number_input("Cotisation annuelle fixée (DH)", value=3000)

total_p = df_paiements['montant'].sum() if 'montant' in df_paiements.columns else 0
total_d = df_depenses['montant'].sum() if 'montant' in df_depenses.columns else 0
solde = total_p - total_d

c1, c2, c3 = st.columns(3)
c1.metric("💰 Encaissé", f"{total_p:,.0f} DH")
c2.metric("💸 Dépensé", f"{total_d:,.0f} DH")
c3.metric("🏦 Solde", f"{solde:,.0f} DH")

st.divider()

# --- ONGLETS ---
tab1, tab2, tab3, tab4 = st.tabs(["📥 Encaisser", "📋 État", "📉 Dépenses", "🛠 Administration"])

# ONGLET 1 : PAIEMENTS
with tab1:
    if not df_membres.empty:
        with st.form("p_form", clear_on_submit=True):
            opts = {f"{r['appartement']} - {r['nom']}": r['id'] for _, r in df_membres.iterrows()}
            choix = st.selectbox("Copropriétaire", options=opts.keys())
            mt = st.number_input("Montant", min_value=0.0)
            dt = st.date_input("Date")
            if st.form_submit_button("Valider"):
                p_id = int(df_paiements['id'].max() + 1) if not df_paiements.empty else 1
                new_p = pd.DataFrame([{"id": p_id, "membre_id": opts[choix], "montant": mt, "date_paiement": str(dt)}])
                conn.update(worksheet="paiements", data=pd.concat([df_paiements, new_p], ignore_index=True))
                st.rerun()

# ONGLET 2 : BILAN
with tab2:
    if not df_membres.empty:
        gp = df_paiements.groupby('membre_id')['montant'].sum().reset_index()
        bilan = df_membres.merge(gp, left_on='id', right_on='membre_id', how='left').fillna(0)
        bilan['reste'] = cotisation_annuelle - bilan['montant']
        st.dataframe(bilan[['appartement', 'nom', 'montant', 'reste']], use_container_width=True, hide_index=True)

# ONGLET 3 : DÉPENSES
with tab3:
    with st.form("d_form", clear_on_submit=True):
        t_d = st.text_input("Objet")
        m_d = st.number_input("Montant", min_value=0.0)
        dt_d = st.date_input("Date")
        if st.form_submit_button("Ajouter frais"):
            d_id = int(df_depenses['id'].max() + 1) if not df_depenses.empty else 1
            new_d = pd.DataFrame([{"id": d_id, "titre": t_d, "montant": m_d, "date": str(dt_d)}])
            conn.update(worksheet="depenses", data=pd.concat([df_depenses, new_d], ignore_index=True))
            st.rerun()
    for _, r in df_depenses.sort_values('date', ascending=False).iterrows():
        with st.expander(f"📅 {r['date']} | {r['titre']} : {r['montant']} DH"):
            if st.button("Supprimer", key=f"del_d_{r['id']}"):
                supprimer_ligne_cloud('depenses', r['id'])

# ONGLET 4 : ADMINISTRATION (MODIFIER / SUPPRIMER MEMBRES)
with tab4:
    st.subheader("👥 Gestion des comptes copropriétaires")
    for _, row in df_membres.iterrows():
        # ICI se trouve la correction complète (Nom, Prénom, Appt, Tel, Email)
        with st.expander(f"📝 Modifier : {row['appartement']} - {row['nom']}"):
            c_nom = st.text_input("Nom", value=row['nom'], key=f"n_{row['id']}")
            c_pre = st.text_input("Prénom", value=row['prenom'], key=f"p_{row['id']}")
            c_app = st.text_input("Appartement", value=row['appartement'], key=f"a_{row['id']}")
            c_tel = st.text_input("Téléphone", value=row['tel'], key=f"t_{row['id']}")
            c_em  = st.text_input("Email", value=row.get('email', ''), key=f"e_{row['id']}")
            
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("Sauvegarder", key=f"s_{row['id']}", type="primary"):
                mettre_a_jour_membre_cloud(row['id'], c_nom, c_pre, c_app, c_tel, c_em)
            if col_b2.button("Supprimer le membre", key=f"d_{row['id']}"):
                supprimer_ligne_cloud('membres', row['id'])
