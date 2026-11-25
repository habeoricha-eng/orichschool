# Cap Révision

Appli d'étude multilingue : import de cours, fiches, cartes mémoire, quiz, carte des concepts,
révisions espacées (SM-2) et salons d'étude partagés. Installable sur mobile (PWA).

## Lancer en local
```bash
python -m venv .venv && source .venv/bin/activate      # Windows : .venv\Scripts\activate
pip install -r requirements.txt
python make_icons.py                                    # une seule fois
mkdir -p .streamlit && echo 'GROQ_API_KEY = "ta_cle"' > .streamlit/secrets.toml
streamlit run app.py
```
Clé gratuite : console.groq.com → API Keys. Modèle modifiable avec `GROQ_MODEL`.

## Déployer gratuitement (Streamlit Community Cloud)
1. Pousse le dossier sur GitHub (ajoute `.streamlit/secrets.toml` et `data/` au `.gitignore`, mais garde `static/`).
2. share.streamlit.io → New app → choisis le dépôt, fichier `app.py`.
3. Advanced settings → Secrets : `GROQ_API_KEY = "ta_cle"`.

Render : service Web, build `pip install -r requirements.txt`,
start `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`.

## Installer sur le téléphone
Ouvre l'URL, puis « Ajouter à l'écran d'accueil » (Safari : Partager ; Chrome : menu ⋮).

## Limites à connaître
- SQLite est effacée à chaque redémarrage de l'hébergement gratuit : cours, révisions et salons
  ne sont pas durables. Pour les garder, il faut passer `core/store.py` sur Supabase (gratuit).
- Streamlit ne permet pas de service worker : pas de mode hors-ligne, l'installation repose sur le manifest.
- Le pseudo sans mot de passe suffit pour un cercle de classe, pas pour des données sensibles.