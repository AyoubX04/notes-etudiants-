import os
import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)

# Fichier où sont conservées les notes de l'école
DB = "notes.db"

# Prépare le registre des notes au démarrage de l'application
def init_db():
    with sqlite3.connect(DB) as con:
        # Chaque note concerne un étudiant, dans un module
        con.execute(
            "CREATE TABLE IF NOT EXISTS notes "
            "(id INTEGER PRIMARY KEY, etudiant TEXT, module TEXT, note REAL)"
        )
        # Si le registre est vide, on y inscrit deux notes d'exemple
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

# Modification d'une note par l'enseignant (version vulnérable)
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

if __name__ == "__main__":
    app.run(host=os.environ.get("APP_HOST", "127.0.0.1"), port=5000)