# Moteur de recommandation e-commerce

Projet tuteuré (ISG Tunis, 2025/2026) réalisé en binôme.

Système de recommandation hybride pour une boutique e-commerce fictive, combinant trois approches : filtrage par contenu, filtrage collaboratif et recommandation temporelle.

## Fonctionnalités
- **Filtrage par contenu :** prétraitement NLP des descriptions (stemming français avec NLTK), vectorisation TF-IDF, similarité cosinus et similarité de Jaccard
- **Filtrage collaboratif :** matrice utilisateurs × produits (NumPy), similarité entre utilisateurs, prédiction de note par K plus proches voisins
- **Recommandation temporelle :** les évaluations récentes pèsent plus que les anciennes
- **Modèle hybride :** combinaison pondérée (40 % contenu, 40 % collaboratif, 20 % temps)
- **Interface web interactive (Streamlit) :** on choisit un utilisateur et une méthode, puis on obtient les recommandations avec une explication, ainsi que l'historique des notes

## Technologies
Python 3, PostgreSQL, psycopg2, NumPy, scikit-learn, NLTK, Streamlit

## Base de données (PostgreSQL)
Base `ecommerce_rec` : 20 produits, 20 utilisateurs, 60 évaluations, ainsi qu'une table `SimilariteContenu` pour les scores calculés.

## Structure du projet
- `schema.sql` : création des tables
- `data.sql` : données (produits, utilisateurs, notes)
- `1_setup_base.ipynb` : vérification de la base
- `2_contenu.ipynb` : filtrage par contenu
- `3_collaboratif.ipynb` : filtrage collaboratif et modèle hybride
- `app.py` : application Streamlit

## Lancer le projet
1. Créer la base PostgreSQL `ecommerce_rec`, puis exécuter `schema.sql` et `data.sql`
2. Remplacer `votre_mot_de_passe` par votre mot de passe PostgreSQL dans le code
3. Installer les bibliothèques : `pip install psycopg2-binary numpy scikit-learn nltk streamlit`
4. Exécuter les notebooks dans l'ordre (1, 2, puis 3). Le notebook 2 remplit la table `SimilariteContenu`
5. Lancer l'application : `streamlit run app.py`

## Auteures
Rawen Houimli et Chaima Gmati
