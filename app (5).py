import streamlit as st
import psycopg2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime

# ==================== FONCTIONS ====================
def get_conn():
    return psycopg2.connect(
        host="localhost",
        database="ecommerce_rec",
        user="postgres",
        password="votre_mot_de_passe",
        port="5432"
    )

def get_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT IDUser, NomUser FROM Users ORDER BY IDUser")
    data = cur.fetchall()
    conn.close()
    return data

def get_produits():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT ID, NomPdt, Categorie, Prix FROM Produit ORDER BY ID")
    data = cur.fetchall()
    conn.close()
    return data

def produit_prefere(id_user):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.ID, p.NomPdt FROM Notes n
        JOIN Produit p ON n.IDProduit = p.ID
        WHERE n.IDUser = %s
        ORDER BY n.Note DESC LIMIT 1
    """, (id_user,))
    data = cur.fetchone()
    conn.close()
    return data

def get_historique_user(id_user):
    """Récupère l'historique des notes d'un utilisateur (produit, catégorie, note, date)"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.NomPdt, p.Categorie, n.Note, n.DateNote
        FROM Notes n
        JOIN Produit p ON n.IDProduit = p.ID
        WHERE n.IDUser = %s
        ORDER BY n.DateNote DESC
    """, (id_user,))
    data = cur.fetchall()
    conn.close()
    return data

def recommander_collaboratif(id_user, N=5):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT IDUser, IDProduit, Note FROM Notes")
    notes = cur.fetchall()
    cur.execute("SELECT IDUser FROM Users ORDER BY IDUser")
    users = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT ID FROM Produit ORDER BY ID")
    produits = [r[0] for r in cur.fetchall()]
    conn.close()
    u_idx = {u: i for i, u in enumerate(users)}
    p_idx = {p: i for i, p in enumerate(produits)}
    matrice = np.zeros((len(users), len(produits)))
    for u, p, n in notes:
        matrice[u_idx[u]][p_idx[p]] = n
    sim = cosine_similarity(matrice)
    u = u_idx[id_user]
    scores = []
    for id_p in produits:
        p = p_idx[id_p]
        if matrice[u][p] == 0:
            sims = [(sim[u][v], v) for v in range(len(users))
                    if v != u and matrice[v][p] > 0]
            sims.sort(reverse=True)
            top = sims[:2]
            if top:
                num = sum(s * matrice[v][p] for s, v in top)
                den = sum(abs(s) for s, v in top)
                scores.append((id_p, round(num/den, 2) if den > 0 else 0))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:N]

def recommander_contenu(id_produit, N=5):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.ID, p.NomPdt, p.Categorie, p.Prix, s.Score
        FROM SimilariteContenu s
        JOIN Produit p ON s.IDProduit2 = p.ID
        WHERE s.IDProduit1 = %s
        ORDER BY s.Score DESC LIMIT %s
    """, (id_produit, N))
    data = cur.fetchall()
    conn.close()
    return data

def recommander_recent(id_user, N=5):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT IDUser, IDProduit, Note, DateNote FROM Notes")
    notes = cur.fetchall()
    cur.execute("SELECT IDUser FROM Users ORDER BY IDUser")
    users = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT ID FROM Produit ORDER BY ID")
    produits = [r[0] for r in cur.fetchall()]
    conn.close()
    u_idx = {u: i for i, u in enumerate(users)}
    p_idx = {p: i for i, p in enumerate(produits)}
    matrice = np.zeros((len(users), len(produits)))
    for u, p, n, d in notes:
        matrice[u_idx[u]][p_idx[p]] = n
    aujourd_hui = datetime.now()
    scores = {}
    for u, p, n, d in notes:
        if u == id_user:
            continue
        jours = (aujourd_hui - datetime(d.year, d.month, d.day)).days
        poids = 1 / (1 + jours / 30)
        scores[p] = scores.get(p, 0) + n * poids
    u = u_idx[id_user]
    resultats = [(id_p, s) for id_p, s in scores.items()
                 if matrice[u][p_idx[id_p]] == 0]
    resultats.sort(key=lambda x: x[1], reverse=True)
    return resultats[:N]

def recommander_hybride(id_user, id_produit, N=5):
    r_collab = recommander_collaboratif(id_user, N)
    r_recent = recommander_recent(id_user, N)
    r_contenu = recommander_contenu(id_produit, N)
    scores = {}
    for id_p, s in r_collab:
        scores[id_p] = scores.get(id_p, 0) + 0.4 * s
    for id_p, s in r_recent:
        scores[id_p] = scores.get(id_p, 0) + 0.2 * s
    for row in r_contenu:
        scores[row[0]] = scores.get(row[0], 0) + 0.4 * row[4]
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:N]

# ==================== INTERFACE STREAMLIT ====================
st.set_page_config(page_title="Moteur de Recommandation", layout="wide", page_icon="🛒")

st.markdown("""
<div style='background: linear-gradient(90deg, #1a1a2e, #16213e);
padding: 2rem; border-radius: 12px; margin-bottom: 1rem; text-align: center;'>
<h1 style='color: white; font-size: 2.5rem; margin: 0;'>🛒 Moteur de Recommandation</h1>
<p style='color: #a0aec0; font-size: 1.1rem; margin: 0.5rem 0 0;'>
Système intelligent de recommandation E-Commerce</p>
</div>
""", unsafe_allow_html=True)

# Chargement des données communes
users = get_users()
produits = get_produits()
user_options = {f"{u[1]}": u[0] for u in users}
produit_options = {f"{p[1]} ({p[2]})": p[0] for p in produits}

# Sidebar - Paramètres globaux
with st.sidebar:
    st.markdown("### ⚙️ Paramètres")
    st.markdown("---")
    sel_user = st.selectbox("👤 Choisir un utilisateur", list(user_options.keys()))
    sel_user_id = user_options[sel_user]
    pref = produit_prefere(sel_user_id)
    if pref:
        st.info(f"❤️ Produit préféré : **{pref[1]}**")
        sel_produit_id = pref[0]
    else:
        sel_produit = st.selectbox("🛍️ Produit préféré", list(produit_options.keys()))
        sel_produit_id = produit_options[sel_produit]
    st.markdown("---")
    mode = st.radio("🔀 Méthode", ["Collaboratif","Contenu","Time-Aware","Hybride"])
    N = st.slider("📊 Nombre de recommandations", 1, 10, 5)
    st.markdown("---")
    bouton = st.button("🚀 Lancer la recommandation", use_container_width=True)

# Affichage des métriques (résumé utilisateur)
col1, col2, col3 = st.columns(3)
col1.metric("👤 Utilisateur", sel_user)
col2.metric("❤️ Produit préféré", pref[1] if pref else "Non défini")
col3.metric("🔀 Méthode", mode)
st.markdown("---")

# ==================== ONGLETS ====================
onglet_reco, onglet_histo = st.tabs(["🎯 Recommandations", "📜 Historique utilisateur"])

# ---- ONGLET 1 : RECOMMANDATIONS ----
with onglet_reco:
    if bouton:
        conn = get_conn()
        cur = conn.cursor()
        st.markdown(f"## 🎯 Recommandations pour **{sel_user}**")

        if mode == "Collaboratif":
            st.markdown("### 🤝 Filtrage Collaboratif")
            st.markdown("*Basé sur les préférences d'utilisateurs similaires*")
            recs = recommander_collaboratif(sel_user_id, N)
            if recs:
                for i, (id_p, score) in enumerate(recs, 1):
                    cur.execute("SELECT NomPdt, Categorie, Prix FROM Produit WHERE ID=%s", (id_p,))
                    row = cur.fetchone()
                    if row:
                        st.success(f"**#{i} — {row[0]}**\n\n📦 Catégorie: {row[1]} | 💰 Prix: {row[2]}€")
                        st.caption("👥 Recommandé car des utilisateurs similaires ont aimé ce produit")
            else:
                st.warning("Pas assez de données pour cet utilisateur")

        elif mode == "Contenu":
            st.markdown("### 📋 Filtrage par Contenu")
            st.markdown("*Basé sur la similarité des descriptions de produits*")
            recs = recommander_contenu(sel_produit_id, N)
            if recs:
                for i, row in enumerate(recs, 1):
                    st.success(f"**#{i} — {row[1]}**\n\n📦 Catégorie: {row[2]} | 💰 Prix: {row[3]}€")
                    st.caption("📌 Recommandé car similaire à votre produit préféré")
            else:
                st.warning("Lancez d'abord le notebook 2_contenu.ipynb !")

        elif mode == "Time-Aware":
            st.markdown("### ⏰ Recommandation Time-Aware")
            st.markdown("*Basé sur les tendances et préférences récentes*")
            recs = recommander_recent(sel_user_id, N)
            if recs:
                for i, (id_p, score) in enumerate(recs, 1):
                    cur.execute("SELECT NomPdt, Categorie, Prix FROM Produit WHERE ID=%s", (id_p,))
                    row = cur.fetchone()
                    if row:
                        st.success(f"**#{i} — {row[0]}**\n\n📦 Catégorie: {row[1]} | 💰 Prix: {row[2]}€")
                        st.caption("⏰ Recommandé car tendance récente ou populaire en ce moment")
            else:
                st.warning("Pas assez de données temporelles")

        else:  # Hybride
            st.markdown("### 🔀 Modèle Hybride")
            st.markdown("*Combinaison : 40% Contenu + 40% Collaboratif + 20% Temps*")
            recs = recommander_hybride(sel_user_id, sel_produit_id, N)
            if recs:
                for i, (id_p, score) in enumerate(recs, 1):
                    cur.execute("SELECT NomPdt, Categorie, Prix FROM Produit WHERE ID=%s", (id_p,))
                    row = cur.fetchone()
                    if row:
                        st.success(f"**#{i} — {row[0]}**\n\n📦 Catégorie: {row[1]} | 💰 Prix: {row[2]}€")
                        st.caption("🔀 Recommandé par combinaison : contenu + collaboratif + tendances récentes")
            else:
                st.warning("Pas assez de données")

        conn.close()
        st.markdown("---")
        st.info(f"✅ Méthode: **{mode}** | Utilisateur: **{sel_user}** | Produit préféré: **{pref[1] if pref else 'Non défini'}**")

# ---- ONGLET 2 : HISTORIQUE ----
with onglet_histo:
    st.markdown(f"## 📜 Historique des notes de **{sel_user}**")
    historique = get_historique_user(sel_user_id)
    if historique:
        st.markdown(f"**{len(historique)} produits notés :**")
        for row in historique:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{row[0]}** — {row[1]}")
                    st.caption(f"📅 Noté le {row[3]}")
                with col2:
                    etoiles = "⭐" * int(row[2])
                    st.markdown(f"### {etoiles}")
    else:
        st.info("Aucune note enregistrée pour cet utilisateur")