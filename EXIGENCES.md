# Exigences de sécurité de l'application des notes

| # | Exigence: « Le système doit... » | Vérification | Étape du SDLC | Test |
|---|----------------------------------|--------------|---------------|------|
| 1 | Le système doit immuniser la recherche de note par nom contre les injections SQL. | Requête de test avec payload SQL. | Implémentation / Test | S1 |
| 2 | Le système doit exiger une identification valide (jeton Bearer) pour toute modification de note (renvoyer HTTP 401 si absent/invalide). | Tentative de modif sans jeton. | Implémentation / Test | S2 |
| 3 | Le système doit interdire aux étudiants de modifier les notes (renvoyer HTTP 403). | Tentative de modif avec jeton étudiant. | Implémentation / Test | S3 |
| 4 | Le système doit interdire à un enseignant de modifier les notes d'un module qu'il n'enseigne pas (renvoyer HTTP 403). | Modif avec jeton enseignant d'un autre module. | Implémentation / Test | S4 |
| 5 | Le système doit valider que la note attribuée est un nombre compris entre 0 et 20 inclus (renvoyer HTTP 400 en cas d'erreur). | Tentative avec note hors borne ou chaîne de caractères. | Implémentation / Test | S5 |
| 6 | Le système doit autoriser l'enseignant affecté au module à modifier la note de ses étudiants (renvoyer HTTP 200). | Requête valide de modif par le prof du module. | Implémentation / Test | S6 |
| 7 | Le système ne doit exposer aucun détail technique interne (ex: erreurs SQLite) en cas de défaillance (renvoyer HTTP 500 générique). | Simulation d'erreur base de données. | Implémentation / Test | S7 |
```[cite: 3, 5, 6]