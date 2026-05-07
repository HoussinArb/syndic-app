import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURATION ET PARAMÈTRES
# ==========================================
st.set_page_config(page_title="Syndic Mimosa Agadir", layout="wide", page_icon="🏢")

# --- MODIFIE CES 3 VALEURS ---
SHEET_ID = "1HYzTP9oGbv3yDprhmPLG39XS07qdej8GTSsN0ObxIes" 
GID_MEMBRES = "0"
GID_PAIEMENTS = "469308404"
GID_DEPENSES = "108011384" 
# -----------------------------

# ==========================================
# 2. LECTURE DES DONNÉES (MODE HYBRIDE GID)
# ==========================================
def charger_gid(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    df = pd.read_csv(url)
    # Nettoyage : enlève les espaces et force les minuscules pour les colonnes
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

try:
    df_membres = charger_gid(GID_MEMBRES)
    df_paiements = charger_gid(GID_PAIEMENTS)
    df_depenses = charger_gid(GID_DEPENSES)
except Exception as e:
    st.error("⚠️ Problème de lecture. Vérifiez l'ID du fichier et les GIDs.")
    st.stop()

# Connexion pour l'écriture (via Secrets Streamlit)
conn = st.connection("gsheets", type=GSheetsConnection)

# ==========================================
# 3. FONCTIONS D'ÉCRITURE CLOUD
# ==========================================
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

# ==========================================
# 4. DASHBOARD PRINCIPAL
# ==========================================
st.title("🏢 Syndic Mimosa Agadir")
cotisation_annuelle = st.number_input("Cotisation annuelle fixée (DH)", value=3000)

# Calculs rapides
total_encaisse = df_paiements['montant'].sum() if 'montant' in df_paiements.columns else 0
total_depenses = df_depenses['montant'].sum() if 'montant' in df_depenses.columns else 0
solde = total_encaisse - total_depenses

c1, c2, c3 = st.columns(3)
c1.metric("💰 Encaissé", f"{total_encaisse:,.0f} DH")
c2.metric("💸 Dépensé", f"{total_depenses:,.0f} DH")
c3.metric("🏦 Solde", f"{solde:,.0f} DH")

st.divider()

# ==========================================
# 5. SYSTÈME D'ONGLETS
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📥 Encaisser", "📋 État", "📉 Dépenses", "🛠 Administration"])

# --- ONGLET 1 : ENCAISSEMENT ---
with tab1:
    st.subheader("Nouveau versement")
    if not df_membres.empty:
        with st.form("f_paiement", clear_on_submit=True):
            options = {f"Appt {row['appartement']} - {row['nom']}": row['id'] for _, row in df_membres.iterrows()}
            choix = st.selectbox("Copropriétaire", options=options.keys())
            mt = st.number_input("Montant (DH)", min_value=0.0, step=50.0)
            dt = st.date_input("Date")
            if st.form_submit_button("Valider"):
                if mt > 0:
                    p_id = int(df_paiements['id'].max() + 1) if not df_paiements.empty else 1
                    nouveau_p = pd.DataFrame([{"id": p_id, "membre_id": options[choix], "montant": mt, "date_paiement": str(dt)}])
                    conn.update(worksheet="paiements", data=pd.concat([df_paiements, nouveau_p], ignore_index=True))
                    st.rerun()

# --- ONGLET 2 : BILAN ---
with tab2:
    st.subheader("Situation des paiements")
    if not df_membres.empty:
        groupe_p = df_paiements.groupby('membre_id')['montant'].sum().reset_index()
        bilan = df_membres.merge(groupe_p, left_on='id', right_on='membre_id', how='left').fillna(0)
        bilan['reste'] = cotisation_annuelle - bilan['montant']
        bilan['statut'] = bilan['reste'].apply(lambda x: "✅ OK" if x <= 0 else ("⏳ Partiel" if x < cotisation_annuelle else "❌ En attente"))
        st.dataframe(bilan[['appartement', 'nom', 'montant', 'reste', 'statut']], use_container_width=True, hide_index=True)

# --- ONGLET 3 : DÉPENSES ---
with tab3:
    st.subheader("Gestion des frais")
    with st.form("f_dep", clear_on_submit=True):
        titre_d = st.text_input("Objet (ex: Jardinier)")
        montant_d = st.number_input("Montant", min_value=0.0)
        date_d = st.date_input("Date")
        if st.form_submit_button("Ajouter dépense"):
            if titre_d and montant_d > 0:
                d_id = int(df_depenses['id'].max() + 1) if not df_depenses.empty else 1
                nouveau_d = pd.DataFrame([{"id": d_id, "titre": titre_d, "montant": montant_d, "date": str(date_d)}])
                conn.update(worksheet="depenses", data=pd.concat([df_depenses, nouveau_d], ignore_index=True))
                st.rerun()
    
    st.write("**Historique des dépenses**")
    if 'date' in df_depenses.columns and not df_depenses.empty:
        for _, row in df_depenses.sort_values('date', ascending=False).iterrows():
            with st.expander(f"📅 {row['date']} | {row['titre']} : {row['montant']} DH"):
                if st.button("Supprimer", key=f"del_d_{row['id']}"):
                    supprimer_ligne_cloud('depenses', row['id'])
    else:
        st.info("Aucune dépense affichable.")

# --- ONGLET 4 : ADMINISTRATION ---
with tab4:
    st.subheader("🛠 Administration")
    if st.button("📊 Générer Export Excel"):
        with pd.ExcelWriter("export_syndic.xlsx") as writer:
            df_membres.to_excel(writer, sheet_name="Membres", index=False)
            df_paiements.to_excel(writer, sheet_name="Paiements", index=False)
            df_depenses.to_excel(writer, sheet_name="Depenses", index=False)
        with open("export_syndic.xlsx", "rb") as f:
            st.download_button("📥 Télécharger Excel", f, "syndic_complet.xlsx")

    st.divider()
    st.write("**Correction des membres**")
    for _, row in df_membres.iterrows():
        with st.expander(f"📝 {row['appartement']} - {row['nom']}"):
            n_nom = st.text_input("Nom", value=row['nom'], key=f"en_{row['id']}")
            n_pre = st.text_input("Prénom", value=row['prenom'], key=f"ep_{row['id']}")
            n_app = st.text_input("Appt", value=row['appartement'], key=f"ea_{row['id']}")
            n_tel = st.text_input("Tel", value=row['tel'], key=f"et_{row['id']}")
            n_em = st.text_input("Email", value=row.get('email', ''), key=f"ee_{row['id']}")
            
            c1, c2 = st.columns(2)
            if c1.button("Sauvegarder", key=f"sm_{row['id']}", type="primary"):
                mettre_a_jour_membre_cloud(row['id'], n_nom, n_pre, n_app, n_tel, n_em)
            if c2.button("Supprimer", key=f"dm_{row['id']}"):
                supprimer_ligne_cloud('membres', row['id'])

# Barre latérale pour l'ajout rapide
st.sidebar.header("👤 Nouveau Membre")
with st.sidebar.form("side_add"):
    s_nom = st.text_input("Nom")
    s_app = st.text_input("Appartement")
    if st.form_submit_button("Ajouter"):
        if s_nom and s_app:
            new_id = int(df_membres['id'].max() + 1) if not df_membres.empty else 1
            new_m = pd.DataFrame([{"id": new_id, "nom": s_nom.upper(), "appartement": s_app.upper(), "prenom": "", "tel": "", "email": ""}])
            conn.update(worksheet="membres", data=pd.concat([df_membres, new_m], ignore_index=True))
            st.rerun()
