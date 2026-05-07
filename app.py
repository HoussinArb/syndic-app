import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. CONFIGURATION ET CONNEXION
# ==========================================
st.set_page_config(page_title="Syndic Mimosa Agadir", layout="wide", page_icon="🏢")

# Connexion native à Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def charger_donnees():
    # Lecture des 3 onglets indispensables
    df_m = conn.read(worksheet="membres")
    df_p = conn.read(worksheet="paiements")
    df_d = conn.read(worksheet="depenses")
    return df_m, df_p, df_d

# Initialisation des DataFrames
df_membres, df_paiements, df_depenses = charger_donnees()

# ==========================================
# 2. FONCTIONS DE GESTION (CLOUD)
# ==========================================
def mettre_a_jour_membre_cloud(id_membre, nom, prenom, appt, tel, email):
    df = conn.read(worksheet="membres")
    df.loc[df['id'] == id_membre, ['nom', 'prenom', 'appartement', 'tel', 'email']] = [
        nom.upper(), prenom.capitalize(), appt.upper(), tel, email
    ]
    conn.update(worksheet="membres", data=df)
    st.success("Modifications enregistrées !")
    st.rerun()

def supprimer_ligne_cloud(table, row_id):
    df = conn.read(worksheet=table)
    df = df[df['id'] != row_id]
    conn.update(worksheet=table, data=df)
    st.rerun()

# ==========================================
# 3. BARRE LATÉRALE : AJOUT DE MEMBRES
# ==========================================
st.sidebar.header("👤 Nouveau Copropriétaire")
with st.sidebar.form("ajout_membre", clear_on_submit=True):
    nom = st.text_input("Nom")
    prenom = st.text_input("Prénom")
    appt = st.text_input("N° Appartement")
    tel = st.text_input("Téléphone")
    email = st.text_input("Email")
    
    if st.form_submit_button("Ajouter à la résidence"):
        if nom and appt:
            # Calcul de l'ID suivant (émulation auto-increment)
            next_id = int(df_membres['id'].max() + 1) if not df_membres.empty else 1
            nouveau = pd.DataFrame([{
                "id": next_id, "nom": nom.upper(), "prenom": prenom.capitalize(), 
                "appartement": appt.upper(), "tel": tel, "email": email
            }])
            df_m_maj = pd.concat([df_membres, nouveau], ignore_index=True)
            conn.update(worksheet="membres", data=df_m_maj)
            st.sidebar.success("Membre ajouté !")
            st.rerun()
        else:
            st.sidebar.error("Nom et Appt requis !")

# ==========================================
# 4. DASHBOARD FINANCIER
# ==========================================
st.title("🏢 Syndic Mimosa Agadir")
cotisation_annuelle = st.number_input("Cotisation annuelle fixée (DH)", value=3000)

total_encaisse = df_paiements['montant'].sum()
total_depenses = df_depenses['montant'].sum()
solde = total_encaisse - total_depenses

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Encaissé", f"{total_encaisse:,.2f} DH")
col2.metric("💸 Total Dépensé", f"{total_depenses:,.2f} DH")
col3.metric("🏦 Solde en Caisse", f"{solde:,.2f} DH")

st.divider()

# ==========================================
# 5. ONGLETS PRINCIPAUX
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📥 Encaisser", "📋 État des Cotisations", "📉 Dépenses", "🛠 Administration"])

# --- ONGLET 1 : ENCAISSEMENT ---
with tab1:
    st.subheader("Nouveau versement")
    if not df_membres.empty:
        with st.form("form_paiement", clear_on_submit=True):
            options = {f"Appt {row['appartement']} - {row['nom']}": row['id'] for _, row in df_membres.iterrows()}
            choix = st.selectbox("Sélectionner le copropriétaire", options=options.keys())
            mt = st.number_input("Montant versé (DH)", min_value=0.0, step=50.0)
            dt = st.date_input("Date du jour")
            
            if st.form_submit_button("Valider le paiement"):
                if mt > 0:
                    p_id = int(df_paiements['id'].max() + 1) if not df_paiements.empty else 1
                    nouveau_p = pd.DataFrame([{
                        "id": p_id, "membre_id": options[choix], 
                        "montant": mt, "date_paiement": str(dt)
                    }])
                    conn.update(worksheet="paiements", data=pd.concat([df_paiements, nouveau_p], ignore_index=True))
                    st.success("Paiement enregistré dans le Cloud !")
                    st.rerun()
    else:
        st.warning("Aucun membre enregistré.")

# --- ONGLET 2 : BILAN PAR APPARTEMENT ---
with tab2:
    st.subheader("Situation des paiements")
    if not df_membres.empty:
        groupe_p = df_paiements.groupby('membre_id')['montant'].sum().reset_index()
        bilan = df_membres.merge(groupe_p, left_on='id', right_on='membre_id', how='left').fillna(0)
        bilan['Reste'] = cotisation_annuelle - bilan['montant']
        bilan['Statut'] = bilan['Reste'].apply(lambda x: "✅ OK" if x <= 0 else ("⏳ Partiel" if x < cotisation_annuelle else "❌ En attente"))
        
        st.dataframe(bilan[['appartement', 'nom', 'montant', 'Reste', 'Statut']], 
                     column_config={"montant": "Payé (DH)", "Reste": "Reste (DH)"},
                     use_container_width=True, hide_index=True)

# --- ONGLET 3 : DÉPENSES ---
with tab3:
    st.subheader("Gestion des frais")
    with st.form("f_dep", clear_on_submit=True):
        titre_d = st.text_input("Objet (ex: Jardinier)")
        montant_d = st.number_input("Montant", min_value=0.0)
        date_d = st.date_input("Date")
        if st.form_submit_button("Enregistrer la dépense"):
            if titre_d and montant_d > 0:
                d_id = int(df_depenses['id'].max() + 1) if not df_depenses.empty else 1
                nouveau_f = pd.DataFrame([{"id": d_id, "titre": titre_d, "montant": montant_d, "date": str(date_d)}])
                conn.update(worksheet="depenses", data=pd.concat([df_depenses, nouveau_f], ignore_index=True))
                st.rerun()

    st.write("**Historique des dépenses**")
    for _, row in df_depenses.sort_values(by='date', ascending=False).iterrows():
        with st.expander(f"📅 {row['date']} | {row['titre']} : {row['montant']} DH"):
            if st.button("Supprimer", key=f"del_d_{row['id']}"):
                supprimer_ligne_cloud('depenses', row['id'])

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
