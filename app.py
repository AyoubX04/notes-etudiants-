#Application de consultation des notes des étudiants
import os
import sqlite3
from flask import Flask, jsonify, request
app = Flask(__name__)
#Fichier où sont conservées les notes de l'école
DB = "notes.db"
# Prépare le registre des notes au démarrage de l'application
def init_db():
    with sqlite3.connect(DB) as con:
        # Chaque note concerne un étudiant, dans un module
        con.execute(
            "CREATE TABLE IF NOT EXISTS notes "
            "(id INTEGER PRIMARY KEY, etudiant TEXT, module TEXT, note REAL)"
        )
        #Si le registre est vide, on y inscrit deux notes d'exemple
        if con.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 0:
            con.executemany(
                "INSERT INTO notes (etudiant, module, note) VALUES (?, ?, ?)",
                [("Amina", "DevSecOps", 15.5), ("Youssef", "DevSecOps", 12.0)]
            )
init_db()
# Page d'accueil
@app.route("/")
def accueil():
    return (
        "<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>"
        "<title>Notes des etudiants</title></head><body>"
        "<h1>Consultation des notes</h1>"
        "<p><a href='/notes'>Voir les notes</a></p></body></html>"
    )
# Indique que le service des notes est disponible
# Indique que le service des notes est disponible
@app.route("/health")
def health():
    return jsonify(status="ok", version="1.0")
# Consultation des notes
@app.route("/notes")
def lister_notes():
    etudiant = request.args.get("etudiant", "")
    with sqlite3.connect(DB) as con:
        rows = con.execute(
            "SELECT id, etudiant, module, note FROM notes WHERE etudiant LIKE ?",
            (f"%{etudiant}%",),
        ).fetchall()
    return jsonify(
        [{"id": r[0], "etudiant": r[1], "module": r[2], "note": r[3]} for r in rows]
    )
# Modification d'une note par l'enseignant
@app.route("/notes/<note_id>", methods=["PUT"])
def modifier_note(note_id):
    # Clé du service qui prévient l'étudiant par e-mail
    token = "sk_live_51H8ecole"
    try:
        con = sqlite3.connect(DB)
        # Enregistre la nouvelle note
        con.execute("UPDATE notes SET note = " + request.args["note"] + " WHERE id=" + note_id)
        con.commit()
        # Garde une trace de la modification
        print("Modification par", request.remote_addr, request.args)
        return "OK"
    except Exception as e:
        # En cas de problème, informe l'utilisateur
        return str(e), 500
```[cite: 6]

Puis poussez la branche et ouvrez la Pull Request :
```bash
git add app.py
git commit -m "Ajout de la fonction de modification de note"
git push -u origin feature/modifier-note
```[cite: 6]

#### 2. Lancer Bandit (Analyse SAST)
Installez et lancez l'outil d'analyse statique :
```bash
pip install bandit
bandit -r . -x ./.venv,./test_app.py,./test_securite.py
```[cite: 6, 7]

#### 3. Tableau de revue de code (5 vulnérabilités identifiées)

| # | Problème | Catégorie | Trouvé par Bandit ? | Correction à apporter |
|---|---|---|---|---|
| **1** | **Hardcoded API Secret / Key :** Clé secrète `token = "sk_live_51H8ecole"` écrite en clair dans le code.[cite: 6] | OWASP A07:2021 (Identification/Auth Failures) / STRIDE: Information Disclosure[cite: 2] | **Oui** (B105: hardcoded_password_string) | Stocker les secrets dans des variables d'environnement (`os.environ`). |
| **2** | **Injection SQL :** Concaténation directe de `request.args["note"]` et `note_id` dans la requête SQL.[cite: 5, 6] | OWASP A03:2021 (Injection) / STRIDE: Tampering[cite: 2] | **Oui** (B608: hardcoded_sql_expressions) | Utiliser des requêtes préparées paramétrées avec `?` (`con.execute("UPDATE notes SET note=? WHERE id=?", (note, note_id))`). |
| **3** | **Absence d'Authentification / Autorisation :** Aucune vérification du jeton utilisateur via `utilisateur_connecte()`.[cite: 3, 4, 7] | OWASP A01:2021 (Broken Access Control) / STRIDE: Spoofing / Elevation of Privilege[cite: 2, 3] | **Non** | Importer `utilisateur_connecte()` de `auth.py`, vérifier que l'utilisateur est présent (401), qu'il est enseignant et responsable du module concerné (403).[cite: 3, 4, 5, 7] |
| **4** | **Absence de validation des entrées :** La note reçue n'est ni vérifiée en type (numérique) ni restreinte à l'intervalle $[0, 20]$.[cite: 3, 5] | OWASP A04:2021 (Insecure Design) / STRIDE: Tampering[cite: 2, 3] | **Non** | Convertir la valeur en nombre, vérifier `0 <= note <= 20` et renvoyer un code `400 Bad Request` si invalide.[cite: 3, 5] |
| **5** | **Fuite d'informations par gestion d'erreur détaillée :** Renvoyer `str(e)` expose les détails internes du système/SGBD en réponse HTTP.[cite: 5, 6] | OWASP A05:2021 (Security Misconfiguration) / STRIDE: Information Disclosure[cite: 2] | **Non** | Intercepter l'exception, la logger en interne et retourner un message d'erreur générique `("Erreur interne", 500)`.[cite: 5] |

---

### 4. Correction complète de `app.py`

Remplacez la fonction `modifier_note` vulnérable dans `app.py` par la version corrigée suivante :

```python
import os
import sqlite3
from flask import Flask, request, jsonify
from auth import utilisateur_connecte

# ... (reste du code initial app.py)

@app.route("/notes/<note_id>", methods=["PUT"])
def modifier_note(note_id):
    # 1. Authentification
    user = utilisateur_connecte()
    if not user:
        return jsonify({"erreur": "Non identifié"}), 401

    # 2. Autorisation par rôle
    if user.get("role") != "enseignant":
        return jsonify({"erreur": "Accès refusé : réservé aux enseignants"}), 403

    # 3. Récupération et validation du format de la note
    donnees = request.get_json(silent=True) or {}
    valeur_note = donnees.get("note")

    if valeur_note is None:
        return jsonify({"erreur": "Champ note manquant"}), 400

    try:
        valeur_note = float(valeur_note)
    except (ValueError, TypeError):
        return jsonify({"erreur": "La note doit être un nombre valide"}), 400

    # Validation de l'intervalle [0, 20]
    if not (0 <= valeur_note <= 20):
        return jsonify({"erreur": "La note doit être comprise entre 0 et 20"}), 400

    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()
        
        # Récupération du module de la note concernée
        cur.execute("SELECT module FROM notes WHERE id = ?", (note_id,))
        ligne = cur.fetchone()
        
        if not ligne:
            con.close()
            return jsonify({"erreur": "Note non trouvée"}), 404

        module_note = ligne[0]

        # 4. Autorisation par module
        if user.get("module") != module_note:
            con.close()
            return jsonify({"erreur": "Non autorisé sur ce module"}), 403

        # 5. Mise à jour sécurisée (requête préparée)
        cur.execute("UPDATE notes SET note = ? WHERE id = ?", (valeur_note, note_id))
        con.commit()
        con.close()
        
        return jsonify({"status": "OK"}), 200

    except Exception:
        # 6. Pas de fuite de détails techniques
        return jsonify({"erreur": "Erreur interne du serveur"}), 500
```[cite: 3, 4, 5, 6, 7]

#### 5. Validation finale
Re-exécutez vos outils pour valider la résolution complète :
1. **pytest :** `pytest -v` $\rightarrow$ **Tous les tests S1 à S7 doivent passer au vert.**[cite: 5, 7]
2. **Bandit :** `bandit -r . -x ./.venv,./test_app.py,./test_securite.py` $\rightarrow$ **No issues identified.**[cite: 7]
3. **Git Push et Merge :**
   ```bash
   git add app.py
   git commit -m "Correction des failles de sécurité selon la revue de code"
   git push
   ```[cite: 7]
   Approuvez la Pull Request sur GitHub puis effectuez la fusion (`Merge`)[cite: 7].

---

### ❓ Réponse à la Question 4 :
> **Question 4 : Combien de problèmes Bandit a-t-il trouvés ? Lesquels a-t-il manqués ? Qu'en concluez-vous ?**[cite: 7]
>
> **Réponse :** 
> * **Problèmes trouvés :** Bandit trouve en général **2 problèmes** (le secret/jeton codé en dur `B105` et l'expression SQL non préparée `B608`)[cite: 6].
> * **Problèmes manqués :** Bandit a manqué les failles de logique métier et de contrôle d'accès : l'absence d'authentification/autorisation (renvoyer 401/403), le manque de validation métier sur l'intervalle des notes ($[0, 20]$), et l'affichage d'erreurs génériques[cite: 3, 5, 6].
> * **Conclusion :** L'analyse statique automatique (SAST) est indispensable pour détecter rapidement des failles de syntaxe ou des erreurs courantes, mais **elle ne remplace pas les tests automatisés fonctionnels/sécurité (pytest) ni la revue de code humaine** pour valider la logique d'autorisation métier[cite: 3, 6, 7].

---

### ❓ Réponse à la Question 5 :
> **Question 5 : Dans ce TP, pytest et Bandit sont lancés à la main. Comment les faire exécuter automatiquement à chaque pull request ?**[cite: 7]
>
> **Réponse :** 
> Pour automatiser ces vérifications à chaque Pull Request, on met en place une intégration continue (**CI/CD**) avec **GitHub Actions**[cite: 2, 6, 7].
> Il suffit d'ajouter un fichier de workflow `.github/workflows/ci.yml` contenant :
> 1. Un déclencheur sur les événements `pull_request` ciblant la branche `main`[cite: 2].
> 2. Une étape d'installation de Python et des dépendances (`pip install -r requirements.txt pytest bandit`)[cite: 1, 6, 7].
> 3. L'exécution automatique des commandes `bandit -r . ...` et `pytest`[cite: 6, 7]. 
> Si un test ou une analyse échoue, la PR est automatiquement bloquée à la fusion.

---

### 🚀 Pour aller plus loin (Audit des dépendances) :
Pour vérifier les failles connues des packages installés (OWASP A03)[cite: 7] :
```bash
pip install pip-audit
pip-audit -r requirements.txt
```[cite: 7]    
if __name__ == "__main__":
    app.run(host=os.environ.get("APP_HOST", "127.0.0.1"), port=5000)