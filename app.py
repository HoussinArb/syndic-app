import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Syndic Mobile", layout="wide")

# Connexion officielle via Service Account (Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

# Lecture des données (utilise les noms de tes onglets)
df_m = conn.read(worksheet="membres")
df_p = conn.read(worksheet="paiements")
df_d = conn.read(worksheet="depenses")

st.title("🏢 Gestion Syndic")

# Ton interface (onglets, colonnes, formulaires)
# ... Ici tu peux remettre ton code qui tourne bien sur PC ...
# Pour sauvegarder, tu utiliseras simplement :
# conn.update(worksheet="paiements", data=votre_dataframe_mis_a_jour)
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import shutil
import os
import glob


def mettre_a_jour_membre(id_membre, nom, prenom, appt, tel, email):
    conn = sqlite3.connect('syndic_v2.db')
    c = conn.cursor()
    c.execute('''UPDATE membres 
                 SET nom = ?, prenom = ?, appartement = ?, tel = ?, email = ? 
                 WHERE id = ?''', 
              (nom.upper(), prenom.capitalize(), appt.upper(), tel, email, id_membre))
    conn.commit()
    conn.close()
    st.rerun()

def obtenir_date_derniere_sauvegarde():
    liste_backups = glob.glob("backup_syndic_*.db")
    if not liste_backups:
        return "Aucune sauvegarde trouvée"
    dernier_fichier = max(liste_backups, key=os.path.getmtime)
    try:
        # Extrait la date du nom de fichier
        date_str = dernier_fichier.split('_')[-1].replace('.db', '')
        return date_str
    except:
        return "Date inconnue"


# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Syndic Mimosa Agadir", layout="wide", page_icon="🏢")

# 2. GESTION DE LA BASE DE DONNÉES
def init_db():
    conn = sqlite3.connect('syndic_v2.db')
    c = conn.cursor()
    # Table des membres
    c.execute('''CREATE TABLE IF NOT EXISTS membres 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nom TEXT, prenom TEXT, appartement TEXT, tel TEXT, email TEXT)''')
    # Table des paiements
    c.execute('''CREATE TABLE IF NOT EXISTS paiements 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  membre_id INTEGER, montant REAL, date_paiement TEXT, 
                  FOREIGN KEY(membre_id) REFERENCES membres(id))''')
    # Table des dépenses
    c.execute('''CREATE TABLE IF NOT EXISTS depenses 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  titre TEXT, montant REAL, date TEXT)''')
    conn.commit()
    conn.close()

def charger_donnees():
    conn = sqlite3.connect('syndic_v2.db')
    
    # Membres : on s'assure que les colonnes existent même si la table est vide
    df_m = pd.read_sql_query("SELECT * FROM membres", conn)
    if df_m.empty:
        df_m = pd.DataFrame(columns=['id', 'nom', 'prenom', 'appartement', 'tel', 'email'])
    
    # Paiements
    df_p = pd.read_sql_query("SELECT * FROM paiements", conn)
    if df_p.empty:
        df_p = pd.DataFrame(columns=['id', 'membre_id', 'montant', 'date_paiement'])
        
    # Dépenses
    df_d = pd.read_sql_query("SELECT * FROM depenses", conn)
    if df_d.empty:
        df_d = pd.DataFrame(columns=['id', 'titre', 'montant', 'date'])
        
    conn.close()
    return df_m, df_p, df_d

def supprimer_ligne(table, row_id):
    conn = sqlite3.connect('syndic_v2.db')
    conn.cursor().execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()
    st.rerun()

def mettre_a_jour_membre(id_membre, nom, prenom, appt, tel, email):
    conn = sqlite3.connect('syndic_v2.db')
    c = conn.cursor()
    c.execute('''UPDATE membres 
                 SET nom = ?, prenom = ?, appartement = ?, tel = ?, email = ? 
                 WHERE id = ?''', 
              (nom.upper(), prenom.capitalize(), appt.upper(), tel, email, id_membre))
    conn.commit()
    conn.close()
    st.rerun()


# Initialisation
init_db()
df_m, df_p, df_d = charger_donnees()

# 3. BARRE LATÉRALE : AJOUT DE MEMBRES
st.sidebar.header("👤 Nouveau Copropriétaire")
with st.sidebar.form("ajout_membre", clear_on_submit=True):
    nom = st.text_input("Nom")
    prenom = st.text_input("Prénom")
    appt = st.text_input("N° Appartement")
    tel = st.text_input("Téléphone")
    email = st.text_input("Email")
    if st.form_submit_button("Ajouter à la résidence"):
        if nom and appt:
            conn = sqlite3.connect('syndic_v2.db')
            conn.cursor().execute("INSERT INTO membres (nom, prenom, appartement, tel, email) VALUES (?,?,?,?,?)", 
                                  (nom.upper(), prenom.capitalize(), appt.upper(), tel, email))
            conn.commit()
            conn.close()
            st.rerun()
        else:
            st.sidebar.error("Nom et Appt requis !")
def sauvegarder_base():
    try:
        source = 'syndic_v2.db'
        # Crée un nom de fichier avec la date, ex: backup_syndic_2026-05-05.db
        destination = f"backup_syndic_{date.today()}.db"
        shutil.copy2(source, destination)
        return destination
    except Exception as e:
        return None
    
# 4. DASHBOARD FINANCIER
st.title("🏢 Gestion de Copropriété")
cotisation_annuelle = st.number_input("Cotisation annuelle fixée (DH)", value=3000)

total_encaisse = df_p['montant'].sum()
total_depenses = df_d['montant'].sum()
solde = total_encaisse - total_depenses

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Encaissé", f"{total_encaisse:,.2f} DH")
col2.metric("💸 Total Dépensé", f"{total_depenses:,.2f} DH")
col3.metric("🏦 Solde en Caisse", f"{solde:,.2f} DH", delta=f"{solde:,.2f}", delta_color="normal")

st.divider()

# 5. ONGLETS PRINCIPAUX
tab1, tab2, tab3, tab4 = st.tabs(["📥 Encaisser", "📋 État des Cotisations", "📉 Dépenses", "🛠 Administration"])

# --- ONGLET 1 : ENCAISSEMENT ---
with tab1:
    st.subheader("Nouveau versement")
    if not df_m.empty:
        with st.form("form_paiement", clear_on_submit=True):
            # On crée la liste pour le menu déroulant
            options = {f"Appt {row['appartement']} - {row['nom']}": row['id'] for _, row in df_m.iterrows()}
            choix = st.selectbox("Sélectionner le copropriétaire", options=options.keys())
            mt = st.number_input("Montant versé (DH)", min_value=0.0, step=50.0)
            dt = st.date_input("Date du jour")
            
            if st.form_submit_button("Valider le paiement"):
                if mt > 0:
                    conn = sqlite3.connect('syndic_v2.db')
                    conn.cursor().execute("INSERT INTO paiements (membre_id, montant, date_paiement) VALUES (?,?,?)", 
                                          (options[choix], mt, str(dt)))
                    conn.commit()
                    conn.close()
                    st.success("Paiement enregistré !")
                    st.rerun()
    else:
        st.warning("Aucun membre enregistré. Utilisez la barre latérale.")

# --- ONGLET 2 : BILAN PAR APPARTEMENT ---
with tab2:
    st.subheader("Situation des paiements")
    if not df_m.empty:
        # Calcul des sommes par membre
        groupe_p = df_p.groupby('membre_id')['montant'].sum().reset_index()
        bilan = df_m.merge(groupe_p, left_on='id', right_on='membre_id', how='left').fillna(0)
        
        bilan['Reste'] = cotisation_annuelle - bilan['montant']
        bilan['Statut'] = bilan['Reste'].apply(lambda x: "✅ OK" if x <= 0 else ("⏳ Partiel" if x < cotisation_annuelle else "❌ En attente"))
        
        st.dataframe(bilan[['appartement', 'nom', 'prenom', 'montant', 'Reste', 'Statut']], 
                     column_config={
                         "montant": "Total Versé (DH)",
                         "Reste": "Reste à payer (DH)",
                         "Statut": "État"
                     }, use_container_width=True, hide_index=True)
    else:
        st.info("La liste est vide.")

# --- ONGLET 3 : DÉPENSES ---
with tab3:
    c_form, c_list = st.columns([1, 2])
    with c_form:
        st.write("**Ajouter un frais**")
        with st.form("f_dep", clear_on_submit=True):
            titre_d = st.text_input("Objet (ex: Jardinier)")
            montant_d = st.number_input("Montant", min_value=0.0)
            date_d = st.date_input("Date", key="dt_dep")
            if st.form_submit_button("Enregistrer"):
                if titre_d and montant_d > 0:
                    conn = sqlite3.connect('syndic_v2.db')
                    conn.cursor().execute("INSERT INTO depenses (titre, montant, date) VALUES (?,?,?)", 
                                          (titre_d, montant_d, str(date_d)))
                    conn.commit()
                    conn.close()
                    st.rerun()
    with c_list:
        st.write("**Historique des dépenses**")
        if not df_d.empty:
            for _, row in df_d.iterrows():
                col_info, col_del = st.columns([3, 1])
                col_info.write(f"📅 {row['date']} | **{row['titre']}** : {row['montant']} DH")
                if col_del.button("Supprimer", key=f"del_d_{row['id']}"):
                    supprimer_ligne('depenses', row['id'])


# --- TAB 4 : ADMINISTRATION & COMPTES ---
with tab4:
    # 1. Section Sécurité (Haut de l'onglet)
    st.subheader("🛡️ Sécurité et Sauvegarde")
    col_save, col_info_s = st.columns([1, 2])
    
    with col_save:
        if st.button("💾 Créer une sauvegarde maintenant", use_container_width=True):
            fichier_save = sauvegarder_base() # Utilise votre fonction existante
            if fichier_save:
                st.success(f"Sauvegarde créée : {fichier_save}")
                st.rerun()
        
        with open("syndic_v2.db", "rb") as f:
            st.download_button(
                label="📥 Télécharger pour Clé USB",
                data=f,
                file_name=f"syndic_backup_{date.today()}.db",
                mime="application/x-sqlite3",
                use_container_width=True
            )

    with col_info_s:
        date_save = obtenir_date_derniere_sauvegarde()
        if date_save == str(date.today()):
            st.success(f"✅ Vos données sont à jour (Sauvegarde : {date_save})")
        else:
            st.warning(f"⚠️ Dernière sauvegarde : {date_save}")

    st.divider()

    # 2. Section Modification des membres
    st.subheader("👥 Correction des comptes copropriétaires")
    if not df_m.empty:
        for _, row in df_m.iterrows():
            with st.expander(f"📝 Modifier : {row['appartement']} - {row['nom']} {row['prenom']}"):
                c_nom, c_pre = st.columns(2)
                n_nom = c_nom.text_input("Nom", value=row['nom'], key=f"edit_n_{row['id']}")
                n_pre = c_pre.text_input("Prénom", value=row['prenom'], key=f"edit_p_{row['id']}")
                
                c_app, c_tel, c_em = st.columns(3)
                n_app = c_app.text_input("N° Appt", value=row['appartement'], key=f"edit_a_{row['id']}")
                n_tel = c_tel.text_input("Tel", value=row['tel'], key=f"edit_t_{row['id']}")
                n_em = c_em.text_input("Email", value=row.get('email', ''), key=f"edit_e_{row['id']}")
                
                btn_c1, btn_c2 = st.columns([1, 4])
                if btn_c1.button("Enregistrer", key=f"save_m_{row['id']}", type="primary"):
                    mettre_a_jour_membre(row['id'], n_nom, n_pre, n_app, n_tel, n_em)
                
                if btn_c2.button("Supprimer le membre", key=f"del_m_{row['id']}"):
                    supprimer_ligne('membres', row['id'])
    else:
        st.info("Aucun membre enregistré.")

    st.divider()
    
    # 3. Section Annulation Paiements (Historique)
    st.subheader("📜 Historique des encaissements")
    if not df_p.empty and not df_m.empty:
        df_p_renamed = df_p.rename(columns={'id': 'paiement_id'})
        df_h = df_p_renamed.merge(df_m[['id', 'appartement', 'nom']], left_on='membre_id', right_on='id')
        for _, row in df_h.iterrows():
            ch1, ch2, ch3 = st.columns([3, 1, 1])
            ch1.write(f"Appt {row['appartement']} - {row['nom']} ({row['date_paiement']})")
            ch2.write(f"**{row['montant']} DH**")
            if ch3.button("Annuler", key=f"del_p_{row['paiement_id']}"):
                supprimer_ligne('paiements', row['paiement_id'])
