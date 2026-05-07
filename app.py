import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURATION
st.set_page_config(page_title="Syndic Mimosa Agadir", layout="wide", page_icon="🏢")

# Remplace par TON ID de fichier (entre /d/ et /edit)
SHEET_ID = "1HYzTP9oGbv3yDprhmPLG39XS07qdej8GTSsN0ObxIes" 
GID_MEMBRES = "0"
GID_PAIEMENTS = "469308404"
GID_DEPENSES = "108011384"

# 2. LECTURE SÉCURISÉE (Mode GID pour mobile)
def charger_gid(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    df = pd.read_csv(url)
    # Nettoyage automatique des noms de colonnes (supprime les espaces et met en minuscules)
    df.columns = [c.strip().lower() for c in df.columns]
    return df

try:
    df_membres = charger_gid(GID_MEMBRES)
    df_paiements = charger_gid(GID_PAIEMENTS)
    df_depenses = charger_gid(GID_DEPENSES)
except Exception as e:
    st.error("⚠️ Erreur de lecture. Vérifiez le SHEET_ID et que le partage est sur 'Tous les utilisateurs disposant du lien'.")
    st.stop()

# 3. CONNEXION ÉCRITURE
conn = st.connection("gsheets", type=GSheetsConnection)

def supprimer_ligne_cloud(table, row_id):
    # Pour écrire/supprimer, on passe par la connexion officielle
    df = conn.read(worksheet=table)
    df.columns = [c.strip().lower() for c in df.columns]
    df = df[df['id'] != row_id]
    conn.update(worksheet=table, data=df)
    st.rerun()

# --- INTERFACE ---
st.title("🏢 Syndic Mimosa Agadir")
cotisation_annuelle = st.number_input("Cotisation annuelle fixée (DH)", value=3000)

tab1, tab2, tab3, tab4 = st.tabs(["📥 Encaisser", "📋 État", "📉 Dépenses", "🛠 Administration"])

# --- ONGLET 3 : DÉPENSES (Version corrigée) ---
with tab3:
    st.subheader("Gestion des frais")
    with st.form("f_dep", clear_on_submit=True):
        titre_d = st.text_input("Objet (ex: Jardinier)")
        montant_d = st.number_input("Montant", min_value=0.0)
        date_d = st.date_input("Date")
        if st.form_submit_button("Enregistrer la dépense"):
            if titre_d and montant_d > 0:
                d_id = int(df_depenses['id'].max() + 1) if not df_depenses.empty and 'id' in df_depenses.columns else 1
                nouveau_f = pd.DataFrame([{"id": d_id, "titre": titre_d, "montant": montant_d, "date": str(date_d)}])
                # On s'assure que les colonnes correspondent pour l'update
                df_to_save = pd.concat([df_depenses, nouveau_f], ignore_index=True)
                conn.update(worksheet="depenses", data=df_to_save)
                st.rerun()

    st.write("**Historique des dépenses**")
    if df_depenses.empty:
        st.info("Aucune dépense enregistrée.")
    elif 'date' not in df_depenses.columns:
        st.error(f"⚠️ Colonne 'date' manquante. Colonnes actuelles : {list(df_depenses.columns)}")
    else:
        df_sorted = df_depenses.sort_values(by='date', ascending=False)
        for _, row in df_sorted.iterrows():
            with st.expander(f"📅 {row.get('date')} | {row.get('titre')} : {row.get('montant')} DH"):
                if st.button("Supprimer", key=f"del_d_{row['id']}"):
                    supprimer_ligne_cloud('depenses', row['id'])

# --- (Les autres onglets restent identiques à la version précédente) ---

# --- ONGLET 4 : ADMINISTRATION ---
with tab4:
    st.subheader("🛡️ Sécurité et Export")
    col_exp, col_info = st.columns([1, 2])
    
    with col_exp:
        if st.button("📊 Préparer Export Excel", use_container_width=True):
            with pd.ExcelWriter("syndic_export.xlsx") as writer:
                df_membres.to_excel(writer, sheet_name="Membres", index=False)
                df_paiements.to_excel(writer, sheet_name="Paiements", index=False)
                df_depenses.to_excel(writer, sheet_name="Depenses", index=False)
            with open("syndic_export.xlsx", "rb") as f:
                st.download_button("📥 Télécharger Excel", f, "syndic_complet.xlsx", use_container_width=True)

    st.divider()
    
    # Historique des paiements (Annulation)
    st.subheader("📜 Historique des encaissements")
    if not df_paiements.empty and not df_membres.empty:
        df_p_renamed = df_paiements.rename(columns={'id': 'paiement_id'})
        df_h = df_p_renamed.merge(df_membres[['id', 'appartement', 'nom']], left_on='membre_id', right_on='id')
        for _, row in df_h.sort_values('date_paiement', ascending=False).iterrows():
            with st.expander(f"💰 {row['montant']} DH - Appt {row['appartement']} ({row['nom']})"):
                if st.button("Annuler ce versement", key=f"del_p_{row['paiement_id']}"):
                    supprimer_ligne_cloud('paiements', row['paiement_id'])

    st.divider()
    
    # Correction membres
    st.subheader("👥 Correction des comptes")
    for _, row in df_membres.iterrows():
        with st.expander(f"📝 Modifier : {row['appartement']} - {row['nom']}"):
            n_nom = st.text_input("Nom", value=row['nom'], key=f"en_{row['id']}")
            n_pre = st.text_input("Prénom", value=row['prenom'], key=f"ep_{row['id']}")
            n_app = st.text_input("Appt", value=row['appartement'], key=f"ea_{row['id']}")
            n_tel = st.text_input("Tel", value=row['tel'], key=f"et_{row['id']}")
            n_em = st.text_input("Email", value=row.get('email', ''), key=f"ee_{row['id']}")
            
            c1, c2 = st.columns(2)
            if c1.button("Enregistrer", key=f"save_m_{row['id']}", type="primary"):
                mettre_a_jour_membre_cloud(row['id'], n_nom, n_pre, n_app, n_tel, n_em)
            if c2.button("Supprimer le membre", key=f"del_m_{row['id']}"):
                supprimer_ligne_cloud('membres', row['id'])
