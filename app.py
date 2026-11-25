# -*- coding: utf-8 -*-
"""
Orich'School — plateforme d'apprentissage intelligente et collaborative.

Installation :  pip install streamlit groq pypdf langdetect pillow
Lancement   :  python -m streamlit run app.py

Administrateur : au premier lancement, ouvre « Espace administrateur » (bas de la page d'accueil)
pour créer le compte. Option : définir ADMIN_USER / ADMIN_PASSWORD (variables d'environnement)
pour créer ce compte automatiquement. La clé Groq se saisit uniquement dans la console admin.
"""
import base64
import functools
import hashlib
import html
import io
import json
import os
import random
import re
import secrets
import shutil
import sqlite3
import time
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None
try:
    from langdetect import detect as _ld_detect
except Exception:
    _ld_detect = None
try:
    from groq import Groq
except Exception:
    Groq = None
try:
    from PIL import Image, ImageOps
except Exception:
    Image = ImageOps = None
try:
    import pytesseract
except Exception:
    pytesseract = None

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "orich_school.db")  # toujours à côté de app.py, quel que soit le dossier de lancement
DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_VISION = "qwen/qwen3.8-27b"
LANGS = {"fr": "Français", "en": "English", "it": "Italiano"}
IDX = {"fr": 0, "en": 1, "it": 2}
LANG_NAMES = {"fr": "français", "en": "English", "it": "italiano", "es": "español", "de": "Deutsch", "pt": "português",
              "nl": "Nederlands", "ar": "العربية", "ru": "русский", "zh": "中文", "ja": "日本語", "tr": "Türkçe",
              "pl": "polski", "ro": "română", "sw": "Kiswahili"}
LEVELS = ["primary", "middle", "high", "univ", "adult"]
IMG_EXT = ("png", "jpg", "jpeg", "webp")

# ───────────────────────────── Traductions (fr, en, it) ─────────────────────────────
TR = {
    "tagline": ("Apprendre mieux, ensemble.", "Learn better, together.", "Imparare meglio, insieme."),
    "start": ("Commencer", "Get started", "Inizia"),
    "login": ("Se connecter", "Sign in", "Accedi"),
    "register": ("Créer un compte", "Create an account", "Crea un account"),
    "back": ("Retour", "Back", "Indietro"),
    "name": ("Nom d'utilisateur", "Username", "Nome utente"),
    "password": ("Mot de passe", "Password", "Password"),
    "pwd_short": ("Le mot de passe doit contenir au moins 6 caractères.", "The password needs at least 6 characters.", "La password deve avere almeno 6 caratteri."),
    "bad_login": ("Identifiants incorrects.", "Wrong credentials.", "Credenziali errate."),
    "name_taken": ("Ce nom est déjà utilisé.", "This name is already taken.", "Questo nome è già in uso."),
    "fill": ("Renseigne tous les champs.", "Fill in every field.", "Compila tutti i campi."),
    "blocked": ("Ton accès a été suspendu. Contacte l'administrateur.", "Your access has been suspended. Contact the administrator.", "Il tuo accesso è stato sospeso. Contatta l'amministratore."),
    "logout": ("Se déconnecter", "Sign out", "Esci"),
    "home": ("Accueil", "Home", "Home"),
    "docs": ("Mes cours", "My courses", "I miei corsi"),
    "studio": ("Studio", "Studio", "Studio"),
    "review": ("Révision", "Review", "Ripasso"),
    "rooms": ("Salons", "Rooms", "Aule"),
    "settings": ("Réglages", "Settings", "Impostazioni"),
    "hello": ("Bonjour", "Hello", "Ciao"),
    "level": ("Classe / niveau d'études", "Class / study level", "Classe / livello di studi"),
    "st_docs": ("Cours", "Courses", "Corsi"),
    "st_cards": ("Cartes", "Cards", "Carte"),
    "st_due": ("À réviser", "Due today", "Da ripassare"),
    "st_avg": ("Score moyen", "Average score", "Punteggio medio"),
    "qa_scan": ("Ajouter un cours", "Add a course", "Aggiungi un corso"),
    "qa_review": ("Réviser maintenant", "Review now", "Ripassa ora"),
    "qa_rooms": ("Mes salons", "My rooms", "Le mie aule"),
    "recent": ("Mes cours récents", "My recent courses", "I miei corsi recenti"),
    "study": ("Étudier", "Study", "Studia"),
    "add_course": ("Ajouter un cours", "Add a course", "Aggiungi un corso"),
    "tab_photo": ("📷 Photo", "📷 Photo", "📷 Foto"),
    "tab_files": ("📁 Fichiers et captures", "📁 Files and screenshots", "📁 File e screenshot"),
    "tab_text": ("✏️ Texte", "✏️ Text", "✏️ Testo"),
    "cam_hint": ("Cadre bien la page avec une bonne lumière. Tu peux ajouter plusieurs pages, y compris manuscrites.",
                 "Frame the page in good light. You can add several pages, handwritten ones included.",
                 "Inquadra bene la pagina con buona luce. Puoi aggiungere più pagine, anche scritte a mano."),
    "cam_label": ("Prendre une photo du cours", "Take a photo of the course", "Scatta una foto del corso"),
    "add_page": ("Ajouter cette page", "Add this page", "Aggiungi questa pagina"),
    "pages_n": ("{n} page(s) prête(s)", "{n} page(s) ready", "{n} pagina/e pronta/e"),
    "clear_pages": ("Tout effacer", "Clear all", "Cancella tutto"),
    "extract": ("Lire le texte du cours", "Read the course text", "Leggi il testo del corso"),
    "upload": ("Choisis des fichiers (PDF, TXT, MD, images)", "Choose files (PDF, TXT, MD, images)", "Scegli i file (PDF, TXT, MD, immagini)"),
    "drop": ("Glisse tes fichiers ici", "Drop your files here", "Trascina qui i tuoi file"),
    "browse": ("Parcourir", "Browse", "Sfoglia"),
    "paste": ("Colle ton texte ici", "Paste your text here", "Incolla qui il testo"),
    "title": ("Titre", "Title", "Titolo"),
    "subject": ("Matière (facultatif)", "Subject (optional)", "Materia (facoltativa)"),
    "check_text": ("Vérifie le texte lu et corrige-le si besoin", "Check the text and fix it if needed", "Controlla il testo letto e correggilo se serve"),
    "save": ("Enregistrer", "Save", "Salva"),
    "cancel": ("Annuler", "Cancel", "Annulla"),
    "saved": ("Enregistré.", "Saved.", "Salvato."),
    "empty_docs": ("Aucun cours pour le moment. Ajoute ta première photo, un PDF ou un texte.", "No course yet. Add your first photo, PDF or text.", "Nessun corso. Aggiungi la prima foto, un PDF o un testo."),
    "delete": ("Supprimer", "Delete", "Elimina"),
    "detected": ("Langue du cours", "Course language", "Lingua del corso"),
    "chars": ("caractères", "characters", "caratteri"),
    "reading": ("Lecture en cours…", "Reading…", "Lettura in corso…"),
    "read_err": ("Lecture impossible :", "Cannot read:", "Lettura impossibile:"),
    "ocr_fail": ("La lecture de l'image a échoué. Réessaie avec une photo plus nette.", "Reading the image failed. Try again with a sharper photo.", "Lettura dell'immagine non riuscita. Riprova con una foto più nitida."),
    "ocr_unavailable": ("La lecture des images n'est pas disponible pour le moment.", "Image reading is not available right now.", "La lettura delle immagini non è al momento disponibile."),
    "no_text": ("Aucun texte détecté sur cette image.", "No text detected on this image.", "Nessun testo rilevato nell'immagine."),
    "pdf_scanned": ("Ce PDF ne contient pas de texte : prends-le plutôt en photo.", "This PDF has no text: take a photo of it instead.", "Questo PDF non contiene testo: fotografalo."),
    "my_courses": ("Mes cours", "My courses", "I miei corsi"),
    "choose_doc": ("Choisis un cours", "Pick a course", "Scegli un corso"),
    "summary": ("Fiche de synthèse", "Study summary", "Scheda di sintesi"),
    "flashcards": ("Flashcards", "Flashcards", "Flashcard"),
    "quiz": ("Quiz", "Quiz", "Quiz"),
    "generate": ("Générer", "Generate", "Genera"),
    "count": ("Nombre d'éléments", "Number of items", "Numero di elementi"),
    "generating": ("Génération en cours…", "Generating…", "Generazione in corso…"),
    "no_summary": ("Pas encore de fiche pour ce cours.", "No summary for this course yet.", "Nessuna scheda per questo corso."),
    "no_cards": ("Pas encore de flashcards.", "No flashcards yet.", "Nessuna flashcard."),
    "no_quiz": ("Pas encore de quiz.", "No quiz yet.", "Nessun quiz."),
    "lvl_info": ("Expliqué pour : {lvl} · rédigé en {lang}", "Explained for: {lvl} · written in {lang}", "Spiegato per: {lvl} · scritto in {lang}"),
    "error_ai": ("L'IA n'a pas répondu, version simplifiée utilisée.", "The AI did not answer, simplified version used.", "L'IA non ha risposto, versione semplificata usata."),
    "flip": ("Retourner", "Flip", "Gira"),
    "prev": ("Précédent", "Previous", "Indietro"),
    "next": ("Suivant", "Next", "Avanti"),
    "front": ("Question", "Question", "Domanda"),
    "back_side": ("Réponse", "Answer", "Risposta"),
    "correct": ("Bonne réponse !", "Correct!", "Risposta esatta!"),
    "wrong": ("Mauvaise réponse. Réponse attendue :", "Wrong. Expected answer:", "Sbagliato. Risposta attesa:"),
    "score": ("Score", "Score", "Punteggio"),
    "save_score": ("Enregistrer mon score", "Save my score", "Salva il punteggio"),
    "new_attempt": ("Nouvelle tentative", "New attempt", "Nuovo tentativo"),
    "show_answer": ("Montrer la réponse", "Show answer", "Mostra la risposta"),
    "again": ("À revoir", "Again", "Da rivedere"),
    "hard": ("Difficile", "Hard", "Difficile"),
    "good": ("Bien", "Good", "Bene"),
    "easy": ("Facile", "Easy", "Facile"),
    "done": ("Plus rien à réviser aujourd'hui. Bravo !", "Nothing left to review today. Well done!", "Niente da ripassare oggi. Bravo!"),
    "left": ("restantes", "left", "rimaste"),
    "create_room": ("Créer un salon d'étude", "Create a study room", "Crea un'aula di studio"),
    "room_name": ("Nom du salon", "Room name", "Nome dell'aula"),
    "room_subject": ("Matière", "Subject", "Materia"),
    "room_level": ("Classe / niveau", "Class / level", "Classe / livello"),
    "join_room": ("Rejoindre avec un code", "Join with a code", "Unisciti con un codice"),
    "code": ("Code d'invitation", "Invitation code", "Codice d'invito"),
    "join": ("Rejoindre", "Join", "Unisciti"),
    "my_rooms": ("Mes salons", "My rooms", "Le mie aule"),
    "no_rooms": ("Tu n'as encore rejoint aucun salon. Crée-en un pour ta classe ou rejoins-en un avec un code.",
                 "You haven't joined any room yet. Create one for your class or join with a code.",
                 "Non fai ancora parte di nessuna aula. Creane una per la tua classe o unisciti con un codice."),
    "send": ("Envoyer", "Send", "Invia"),
    "message": ("Écris un message à la classe", "Write a message to the class", "Scrivi un messaggio alla classe"),
    "members": ("Membres", "Members", "Membri"),
    "bad_code": ("Code introuvable.", "Code not found.", "Codice non trovato."),
    "leave": ("Quitter le salon", "Leave the room", "Lascia l'aula"),
    "delete_room": ("Supprimer le salon", "Delete the room", "Elimina l'aula"),
    "tab_chat": ("💬 Discussion", "💬 Chat", "💬 Chat"),
    "tab_shared": ("📚 Cours partagés", "📚 Shared courses", "📚 Corsi condivisi"),
    "tab_members": ("👥 Membres", "👥 Members", "👥 Membri"),
    "share_course": ("Partager un de mes cours", "Share one of my courses", "Condividi uno dei miei corsi"),
    "share": ("Partager", "Share", "Condividi"),
    "shared_by": ("partagé par {name}", "shared by {name}", "condiviso da {name}"),
    "add_mine": ("Ajouter à mes cours", "Add to my courses", "Aggiungi ai miei corsi"),
    "no_shared": ("Aucun cours partagé dans ce salon.", "No shared course in this room.", "Nessun corso condiviso in questa aula."),
    "no_msg": ("Aucun message. Lance la discussion.", "No messages yet. Start the discussion.", "Nessun messaggio. Avvia la discussione."),
    "room_live": ("Discussion en direct", "Live discussion", "Discussione in diretta"),
    "profile": ("Profil", "Profile", "Profilo"),
    "ui_lang": ("Langue de l'interface", "Interface language", "Lingua dell'interfaccia"),
    "new_pwd": ("Nouveau mot de passe", "New password", "Nuova password"),
    "update_pwd": ("Changer le mot de passe", "Change password", "Cambia password"),
    "pwd_ok": ("Mot de passe mis à jour.", "Password updated.", "Password aggiornata."),
    "export": ("Exporter mes cartes (JSON)", "Export my cards (JSON)", "Esporta le mie carte (JSON)"),
    "danger": ("Zone sensible", "Sensitive area", "Area sensibile"),
    "delete_acc": ("Supprimer mon compte", "Delete my account", "Elimina il mio account"),
    "confirm_del": ("Je confirme la suppression définitive de mon compte et de mes données.", "I confirm the permanent deletion of my account and data.", "Confermo l'eliminazione definitiva del mio account e dei miei dati."),
    "lvl_primary": ("Primaire", "Primary school", "Scuola primaria"),
    "lvl_middle": ("Collège (6e à 3e)", "Middle school", "Scuola media"),
    "lvl_high": ("Lycée", "High school", "Scuola superiore"),
    "lvl_univ": ("Université", "University", "Università"),
    "lvl_adult": ("Autodidacte", "Self-learner", "Autodidatta"),
    # Page d'accueil publique
    "hero_title": ("Photographie ton cours. Orich'School s'occupe du reste.", "Snap your lesson. Orich'School does the rest.", "Fotografa la lezione. Orich'School fa il resto."),
    "hero_sub": ("Importe un PDF, une photo, une capture d'écran ou même une page écrite à la main. Tu reçois une fiche de synthèse, des flashcards, un quiz par niveaux et un tuteur IA qui répond uniquement à partir de ton cours, dans la langue du cours.",
                 "Import a PDF, a photo, a screenshot or even a handwritten page. You get a study summary, flashcards, a quiz in levels and an AI tutor that answers only from your course, in the course's language.",
                 "Importa un PDF, una foto, uno screenshot o anche una pagina scritta a mano. Ricevi una scheda di sintesi, flashcard, un quiz a livelli e un tutor IA che risponde solo in base al tuo corso, nella lingua del corso."),
    "demo_cap": ("Exemple de flashcard", "Flashcard example", "Esempio di flashcard"),
    "demo_q": ("Que produit la photosynthèse ?", "What does photosynthesis produce?", "Che cosa produce la fotosintesi?"),
    "demo_a": ("Du glucose et du dioxygène, grâce à l'énergie de la lumière.", "Glucose and oxygen, using the energy of light.", "Glucosio e ossigeno, grazie all'energia della luce."),
    "feat_title": ("Ce que tu peux faire", "What you can do", "Cosa puoi fare"),
    "f1t": ("Scanne ou importe", "Scan or import", "Scansiona o importa"),
    "f1d": ("Appareil photo du téléphone, captures d'écran, PDF, texte ou écriture manuscrite.", "Phone camera, screenshots, PDFs, text or handwriting.", "Fotocamera del telefono, screenshot, PDF, testo o scrittura a mano."),
    "f2t": ("Ta langue de cours, détectée seule", "Your course language, detected for you", "La lingua del corso, rilevata da sola"),
    "f2d": ("Fiche, cartes et quiz sont écrits dans la langue du cours, pas celle de l'interface.", "Summary, cards and quiz are written in the course's language, not the interface's.", "Scheda, carte e quiz sono scritti nella lingua del corso, non in quella dell'interfaccia."),
    "f3t": ("Un tuteur IA pour ton cours", "An AI tutor for your course", "Un tutor IA per il tuo corso"),
    "f3d": ("Discute à l'écrit ou à la voix : il répond uniquement à partir de ton cours.", "Chat in writing or by voice: it answers only from your course.", "Chatta per iscritto o a voce: risponde solo in base al tuo corso."),
    "f4t": ("Fiches, cartes et quiz", "Summaries, cards and quizzes", "Schede, carte e quiz"),
    "f4d": ("Synthèse claire, flashcards recto/verso et quiz par niveaux qui balaie tout le cours.", "A clear summary, two-sided flashcards and a leveled quiz that covers the whole course.", "Sintesi chiara, flashcard fronte/retro e quiz a livelli che copre tutto il corso."),
    "f5t": ("Révisions au bon moment", "Reviews at the right time", "Ripassi al momento giusto"),
    "f5d": ("L'algorithme SM-2 te représente chaque carte juste avant que tu l'oublies.", "The SM-2 algorithm shows each card again just before you forget it.", "L'algoritmo SM-2 ti ripropone ogni carta poco prima che la dimentichi."),
    "f6t": ("Salons d'étude", "Study rooms", "Aule di studio"),
    "f6d": ("Un salon par matière et par classe : cours partagés et discussion en direct.", "One room per subject and class: shared courses and live chat.", "Un'aula per materia e classe: corsi condivisi e chat in diretta."),
    "how_title": ("Comment ça marche", "How it works", "Come funziona"),
    "s1t": ("Ajoute ton cours", "Add your course", "Aggiungi il corso"),
    "s1d": ("Photo, capture, fichier ou texte.", "Photo, screenshot, file or text.", "Foto, screenshot, file o testo."),
    "s2t": ("Génère ton support", "Generate your material", "Genera il materiale"),
    "s2d": ("Fiche, flashcards et quiz en quelques secondes.", "Summary, flashcards and quiz in seconds.", "Scheda, flashcard e quiz in pochi secondi."),
    "s3t": ("Révise et partage", "Review and share", "Ripassa e condividi"),
    "s3d": ("Reviens quand les cartes sont dues, ou étudie avec ta classe.", "Come back when cards are due, or study with your class.", "Torna quando le carte sono in scadenza, o studia con la classe."),
    "who_title": ("Pour tous les niveaux", "For every level", "Per ogni livello"),
    "who_sub": ("Chaque élève rejoint sa classe, mais le travail porte toujours sur le contenu de son cours.", "Every student joins their class, but the work always focuses on the content of their course.", "Ogni studente entra nella propria classe, ma il lavoro riguarda sempre il contenuto del suo corso."),
    "cta_final": ("Prêt pour ton prochain cours ?", "Ready for your next course?", "Pronto per il prossimo corso?"),
    "admin_link": ("Espace administrateur", "Administrator area", "Area amministratore"),
    # Administration
    "admin_setup_title": ("Première configuration", "First setup", "Prima configurazione"),
    "admin_setup_hint": ("Crée le compte administrateur de la plateforme.", "Create the platform administrator account.", "Crea l'account amministratore della piattaforma."),
    "confirm_pwd": ("Confirmer le mot de passe", "Confirm password", "Conferma password"),
    "pwd_mismatch": ("Les mots de passe ne correspondent pas.", "Passwords do not match.", "Le password non coincidono."),
    "create_admin": ("Créer le compte administrateur", "Create administrator account", "Crea l'account amministratore"),
    "admin_console": ("Console d'administration", "Administration console", "Console di amministrazione"),
    "ad_live": ("Temps réel", "Live", "In diretta"),
    "ad_users": ("Utilisateurs", "Users", "Utenti"),
    "ad_rooms": ("Salons", "Rooms", "Aule"),
    "ad_ai": ("Intelligence artificielle", "Artificial intelligence", "Intelligenza artificiale"),
    "ad_account": ("Mon compte", "My account", "Il mio account"),
    "m_users": ("Utilisateurs", "Users", "Utenti"),
    "m_online": ("En ligne", "Online", "Online"),
    "m_docs": ("Cours", "Courses", "Corsi"),
    "m_cards": ("Cartes", "Cards", "Carte"),
    "m_msgs": ("Messages aujourd'hui", "Messages today", "Messaggi oggi"),
    "feed_title": ("Activité en direct", "Live activity", "Attività in diretta"),
    "no_activity": ("Aucune activité pour le moment.", "No activity yet.", "Nessuna attività."),
    "chart_title": ("Activité des 7 derniers jours", "Activity over the last 7 days", "Attività degli ultimi 7 giorni"),
    "search": ("Rechercher un utilisateur", "Search a user", "Cerca un utente"),
    "col_name": ("Nom", "Name", "Nome"),
    "col_level": ("Niveau", "Level", "Livello"),
    "col_status": ("Statut", "Status", "Stato"),
    "col_seen": ("Dernière activité", "Last seen", "Ultima attività"),
    "col_created": ("Inscrit le", "Joined", "Iscritto il"),
    "col_docs": ("Cours", "Courses", "Corsi"),
    "col_cards": ("Cartes", "Cards", "Carte"),
    "st_active": ("Actif", "Active", "Attivo"),
    "st_blocked": ("Bloqué", "Blocked", "Bloccato"),
    "select_users": ("Sélectionner des utilisateurs", "Select users", "Seleziona utenti"),
    "block": ("Bloquer l'accès", "Block access", "Blocca l'accesso"),
    "unblock": ("Rétablir l'accès", "Restore access", "Ripristina l'accesso"),
    "del_sel": ("Supprimer définitivement", "Delete permanently", "Elimina definitivamente"),
    "confirm_bulk": ("Je confirme : suppression irréversible des comptes et données sélectionnés.", "I confirm: irreversible deletion of the selected accounts and data.", "Confermo: eliminazione irreversibile degli account e dei dati selezionati."),
    "done_n": ("{n} utilisateur(s) mis à jour.", "{n} user(s) updated.", "{n} utente/i aggiornato/i."),
    "no_users": ("Aucun utilisateur.", "No users.", "Nessun utente."),
    "owner": ("Créateur", "Owner", "Creatore"),
    "key_set": ("Clé configurée (se termine par {tail})", "Key configured (ends with {tail})", "Chiave configurata (termina con {tail})"),
    "key_none": ("Aucune clé configurée : l'application fonctionne en version simplifiée.", "No key configured: the app runs in simplified mode.", "Nessuna chiave: l'app funziona in versione semplificata."),
    "key_new": ("Nouvelle clé API Groq", "New Groq API key", "Nuova chiave API Groq"),
    "key_hint": ("Laisse vide pour conserver la clé actuelle. Cette clé n'est visible par aucun utilisateur.", "Leave empty to keep the current key. No user can see this key.", "Lascia vuoto per mantenere la chiave attuale. Nessun utente può vederla."),
    "model_text": ("Modèle de texte", "Text model", "Modello di testo"),
    "model_vision": ("Modèle de lecture d'images", "Image reading model", "Modello di lettura immagini"),
    "test_ai": ("Tester la connexion", "Test connection", "Testa la connessione"),
    "test_ok": ("Connexion réussie.", "Connection successful.", "Connessione riuscita."),
    "test_fail": ("Échec de la connexion :", "Connection failed:", "Connessione non riuscita:"),
    "remove_key": ("Supprimer la clé", "Remove the key", "Rimuovi la chiave"),
    "ev_register": ("a créé son compte", "created an account", "ha creato l'account"),
    "ev_login": ("s'est connecté", "signed in", "ha effettuato l'accesso"),
    "ev_doc": ("a ajouté un cours", "added a course", "ha aggiunto un corso"),
    "ev_scan": ("a scanné un cours", "scanned a course", "ha scansionato un corso"),
    "ev_summary": ("a généré une fiche", "generated a summary", "ha generato una scheda"),
    "ev_cards": ("a généré des flashcards", "generated flashcards", "ha generato flashcard"),
    "ev_quiz": ("a généré un quiz", "generated a quiz", "ha generato un quiz"),
    "ev_score": ("a terminé un quiz", "finished a quiz", "ha completato un quiz"),
    "ev_review": ("a révisé une carte", "reviewed a card", "ha ripassato una carta"),
    "ev_room": ("a créé un salon", "created a room", "ha creato un'aula"),
    "ev_join": ("a rejoint un salon", "joined a room", "è entrato in un'aula"),
    "ev_msg": ("a écrit dans un salon", "posted in a room", "ha scritto in un'aula"),
    "tutor": ("Tuteur IA", "AI tutor", "Tutor IA"),
    "tutor_hint": ("Pose tes questions sur ce cours : le tuteur répond uniquement à partir de son contenu.", "Ask questions about this course: the tutor answers only from its content.", "Fai domande su questo corso: il tutor risponde solo in base al suo contenuto."),
    "tutor_empty": ("Aucun message pour ce cours. Pose ta première question, à l'écrit ou à la voix.", "No messages for this course yet. Ask your first question, written or spoken.", "Nessun messaggio per questo corso. Fai la prima domanda, scritta o a voce."),
    "tutor_ask": ("Pose une question sur ce cours", "Ask a question about this course", "Fai una domanda su questo corso"),
    "tq1": ("Explique-moi ce cours simplement.", "Explain this course to me simply.", "Spiegami questo corso in modo semplice."),
    "tq2": ("Quels sont les points à retenir ?", "What are the key points to remember?", "Quali sono i punti da ricordare?"),
    "tq3": ("Pose-moi une question pour me tester.", "Ask me a question to test me.", "Fammi una domanda per mettermi alla prova."),
    "thinking": ("Un instant…", "One moment…", "Un momento…"),
    "mic": ("Parle au tuteur (micro)", "Talk to the tutor (microphone)", "Parla al tutor (microfono)"),
    "listen": ("Écouter la réponse", "Listen to the answer", "Ascolta la risposta"),
    "stop": ("Arrêter", "Stop", "Ferma"),
    "auto_voice": ("Lire les réponses à voix haute", "Read answers aloud", "Leggi le risposte ad alta voce"),
    "clear_chat": ("Effacer la discussion", "Clear the chat", "Cancella la chat"),
    "ai_off": ("L'assistant IA n'est pas encore activé. Demande à l'administrateur de l'activer.", "The AI assistant is not enabled yet. Ask the administrator to enable it.", "L'assistente IA non è ancora attivo. Chiedi all'amministratore di attivarlo."),
    "cards_added": ("{n} flashcards ajoutées.", "{n} flashcards added.", "{n} flashcard aggiunte."),
    "quiz_total": ("{n} questions couvrent tout le cours.", "{n} questions cover the whole course.", "{n} domande coprono tutto il corso."),
    "level_n": ("Niveau {n}", "Level {n}", "Livello {n}"),
    "lvl_name_1": ("Bases", "Basics", "Basi"),
    "lvl_name_2": ("Compréhension", "Understanding", "Comprensione"),
    "lvl_name_3": ("Pièges et raisonnement", "Traps and reasoning", "Trabocchetti e ragionamento"),
    "quiz_hint": ("Choisis une réponse par question. Tu peux la changer autant que tu veux avant de valider.", "Pick one answer per question. You can change it as often as you like before submitting.", "Scegli una risposta per domanda. Puoi cambiarla quante volte vuoi prima di confermare."),
    "validate": ("Valider mes réponses", "Submit my answers", "Conferma le risposte"),
    "passed": ("Niveau réussi ! Tu peux passer au suivant.", "Level passed! You can move on to the next one.", "Livello superato! Puoi passare al successivo."),
    "failed": ("Pas encore : il faut au moins 70 % pour réussir. Revois le cours et réessaie.", "Not yet: you need at least 70% to pass. Review the course and try again.", "Non ancora: serve almeno il 70%. Ripassa il corso e riprova."),
    "correction": ("Voir la correction", "See the correction", "Vedi la correzione"),
    "your_answer": ("Ta réponse", "Your answer", "La tua risposta"),
    "right_answer": ("Bonne réponse", "Right answer", "Risposta esatta"),
   "unanswered": ("sans réponse", "unanswered", "senza risposta"),
    "next_level": ("Passer au niveau suivant", "Go to the next level", "Passa al livello successivo"),
    "retry_level": ("Réessayer ce niveau", "Retry this level", "Riprova questo livello"),
    "restart_quiz": ("Recommencer au niveau 1", "Restart at level 1", "Ricomincia dal livello 1"),
    "all_done": ("🏆 Bravo, tu as maîtrisé tout le cours !", "🏆 Well done, you have mastered the whole course!", "🏆 Bravo, hai padroneggiato tutto il corso!"),
    "cam_native": ("Ou ouvre l'appareil photo du téléphone, ou choisis des images déjà prises.", "Or open the phone's camera, or pick photos you already took.", "Oppure apri la fotocamera del telefono o scegli immagini già scattate."),
    "level_hint": ("Sert uniquement à te classer dans la bonne classe. Cela ne change jamais les résumés ni les réponses de l'IA.", "Only used to place you in the right class. It never changes summaries or AI answers.", "Serve solo a inserirti nella classe giusta. Non cambia mai riassunti o risposte dell'IA."),
    "ai_last_error": ("Dernière erreur de l'IA", "Last AI error", "Ultimo errore IA"),
    "ev_tutor": ("a discuté avec le tuteur IA", "chatted with the AI tutor", "ha chiacchierato con il tutor IA"),
    "ev_ai_error": ("erreur IA", "AI error", "errore IA"),
    "too_many": ("Trop de tentatives. Réessaie dans 15 minutes.", "Too many attempts. Try again in 15 minutes.", "Troppi tentativi. Riprova tra 15 minuti."),
    "reg_limit": ("Trop d'inscriptions en peu de temps. Réessaie plus tard.", "Too many sign-ups in a short time. Try again later.", "Troppe iscrizioni in poco tempo. Riprova più tardi."),
    "ai_quota": ("Tu as atteint la limite d'utilisation de l'IA pour cette heure. Réessaie un peu plus tard.", "You reached the AI usage limit for this hour. Try again a bit later.", "Hai raggiunto il limite di utilizzo dell'IA per quest'ora. Riprova più tardi."),
    "cur_pwd": ("Mot de passe actuel", "Current password", "Password attuale"),
    "admin_pwd_short": ("Le mot de passe administrateur doit contenir au moins 12 caractères.", "The administrator password needs at least 12 characters.", "La password amministratore deve avere almeno 12 caratteri."),
    "admin_pwd_managed": ("Le mot de passe administrateur est géré dans les secrets de l'application.", "The administrator password is managed in the app secrets.", "La password amministratore è gestita nei segreti dell'app."),
    "key_from_secrets": ("La clé est fournie par les secrets de l'application (recommandé).", "The key comes from the app secrets (recommended).", "La chiave proviene dai segreti dell'app (consigliato)."),
    "key_need_secret": ("Aucune clé détectée. Ajoute GROQ_API_KEY dans les secrets de l'application (jamais dans le code), puis redémarre l'app.", "No key detected. Add GROQ_API_KEY to the app secrets (never in the code), then restart the app.", "Nessuna chiave rilevata. Aggiungi GROQ_API_KEY nei segreti dell'app (mai nel codice), poi riavvia l'app."),
    "auto_model": ("automatique", "automatic", "automatico"),
    "models_hint": ("Laisse vide : l'application choisit seule un modèle actif et bascule sur un autre si celui-ci tombe en panne ou est retiré.", "Leave empty: the app picks an active model by itself and switches to another one if it fails or is retired.", "Lascia vuoto: l'app sceglie da sola un modello attivo e passa a un altro se si ferma o viene ritirato."),
    "test_models": ("Tester tous les modèles", "Test all models", "Testa tutti i modelli"),
    "refresh_models": ("Actualiser la liste", "Refresh the list", "Aggiorna l'elenco"),
    "txt_kind": ("texte", "text", "testo"),
    "img_kind": ("image", "image", "immagine"),
}


def t(key, **kw):
    lang = st.session_state.get("lang", "fr")
    v = TR.get(key)
    s = v[IDX.get(lang, 0)] if v else key
    return s.format(**kw) if kw else s


# ───────────────────────────── Base de données ─────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT UNIQUE, pwd TEXT, lang TEXT DEFAULT 'fr',
    level TEXT DEFAULT 'adult', created TEXT, role TEXT DEFAULT 'user', status TEXT DEFAULT 'active', last_seen TEXT);
CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, lang TEXT, content TEXT,
    created TEXT, subject TEXT DEFAULT '', source TEXT DEFAULT 'text');
CREATE TABLE IF NOT EXISTS summaries(id INTEGER PRIMARY KEY, user_id INTEGER, doc_id INTEGER, content TEXT, created TEXT);
CREATE TABLE IF NOT EXISTS cards(id INTEGER PRIMARY KEY, user_id INTEGER, doc_id INTEGER, front TEXT, back TEXT,
    ef REAL DEFAULT 2.5, interval INTEGER DEFAULT 0, reps INTEGER DEFAULT 0, due TEXT);
CREATE TABLE IF NOT EXISTS quizzes(id INTEGER PRIMARY KEY, user_id INTEGER, doc_id INTEGER, data TEXT, created TEXT);
CREATE TABLE IF NOT EXISTS scores(id INTEGER PRIMARY KEY, user_id INTEGER, doc_id INTEGER, score INTEGER, total INTEGER, created TEXT);
CREATE TABLE IF NOT EXISTS rooms(id INTEGER PRIMARY KEY, name TEXT, code TEXT UNIQUE, owner_id INTEGER, created TEXT,
    subject TEXT DEFAULT '', level TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS room_members(room_id INTEGER, user_id INTEGER, PRIMARY KEY(room_id, user_id));
CREATE TABLE IF NOT EXISTS room_docs(id INTEGER PRIMARY KEY, room_id INTEGER, title TEXT, lang TEXT, content TEXT,
    subject TEXT, shared_by INTEGER, ts TEXT);
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, room_id INTEGER, user_id INTEGER, content TEXT, ts TEXT);
CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS login_attempts(k TEXT PRIMARY KEY, n INTEGER DEFAULT 0, locked_until TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS ai_chats(id INTEGER PRIMARY KEY, user_id INTEGER, doc_id INTEGER, role TEXT, content TEXT, ts TEXT);
CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY, user_id INTEGER, action TEXT, detail TEXT, ts TEXT);
"""
MIGRATIONS = {
    "users": {"role": "TEXT DEFAULT 'user'", "status": "TEXT DEFAULT 'active'", "last_seen": "TEXT"},
    "documents": {"subject": "TEXT DEFAULT ''", "source": "TEXT DEFAULT 'text'"},
    "rooms": {"subject": "TEXT DEFAULT ''", "level": "TEXT DEFAULT ''"},
}


def secret(name, default=""):
    """Lit un secret (variable d'environnement ou secrets Streamlit). Les secrets ne sont jamais écrits dans le code."""
    val = os.getenv(name)
    if not val:
        try:
            val = st.secrets.get(name)
        except Exception:
            val = None
    return str(val) if val else default


@functools.lru_cache(maxsize=1)
def use_pg():
    """PostgreSQL (base partagée par tous les élèves) si DATABASE_URL est défini, sinon SQLite local."""
    return bool(secret("DATABASE_URL"))


ID_TABLES = {"users", "documents", "summaries", "cards", "quizzes", "scores", "rooms", "room_docs", "messages", "activity", "ai_chats"}


def _clean_pg_dsn(raw_url: str) -> str:
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
    url = (raw_url or "").strip().strip('"').strip("'")
    parts = urlsplit(url)
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() != "pgbouncer"
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


import threading

_POOL_LOCK = threading.Lock()


@st.cache_resource
def pg_pool():
    import psycopg2.extras
    import psycopg2.pool
    dsn = _clean_pg_dsn(secret("DATABASE_URL"))
    return psycopg2.pool.ThreadedConnectionPool(
        1,
        10,
        dsn=dsn,
        cursor_factory=psycopg2.extras.RealDictCursor,
        connect_timeout=10,
    )


def to_pg(sql):
    sql = sql.replace("?", "%s")
    m = re.match(r"\s*INSERT OR IGNORE INTO (.*)", sql, re.S | re.I)
    return f"INSERT INTO {m.group(1)} ON CONFLICT DO NOTHING" if m else sql


def _run_pg(sql, args, one, write):
    import psycopg2
    sql = to_pg(sql)
    tbl = re.match(r"\s*INSERT INTO (\w+)", sql, re.I)
    returning = bool(tbl and tbl.group(1).lower() in ID_TABLES and "RETURNING" not in sql.upper())
    if returning:
        sql += " RETURNING id"
    pool = pg_pool()
    for attempt in (1, 2):
        conn = None
        broken = False
        try:
            with _POOL_LOCK:
                conn = pool.getconn()
            with conn.cursor() as cur:
                cur.execute(sql, args)
                if write:
                    conn.commit()
                    return cur.fetchone()["id"] if returning else None
                rows = cur.fetchall()
            conn.commit()
            return (rows[0] if rows else None) if one else rows
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            broken = True
            if attempt == 2:
                raise
        except Exception:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    broken = True
            raise
        finally:
            if conn is not None:
                with _POOL_LOCK:
                    try:
                        pool.putconn(conn, close=broken)
                    except Exception:
                        pass

def run(sql, args=(), one=False, write=False):
    if use_pg():
        return _run_pg(sql, args, one, write)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, args)
        if write:
            conn.commit()
            return cur.lastrowid
        rows = cur.fetchall()
        return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()


def hash_pwd(pwd, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", pwd.encode(), bytes.fromhex(salt), 150_000).hex()
    return f"{salt}${digest}"


def check_pwd(pwd, stored):
    return secrets.compare_digest(hash_pwd(pwd, stored.split("$")[0]), stored)


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today():
    return date.today().isoformat()


def pg_schema():
    out = []
    for stmt in SCHEMA.split(";"):
        stmt = stmt.strip()
        if stmt:
            out.append(stmt.replace("INTEGER PRIMARY KEY", "SERIAL PRIMARY KEY").replace(" REAL", " DOUBLE PRECISION"))
    return out


def bootstrap_admin():
    """Le compte administrateur est créé uniquement depuis les secrets (jamais depuis le site)."""
    pw = secret("ADMIN_PASSWORD")
    if not pw:
        return
    name = secret("ADMIN_USER", "admin")
    run("UPDATE users SET role='user' WHERE role='admin' AND name!=?", (name,), write=True)  # un seul administrateur : toi
    row = run("SELECT id,pwd,role FROM users WHERE name=?", (name,), one=True)
    if not row:
        run("INSERT INTO users(name,pwd,role,created,status) VALUES(?,?,?,?,?)", (name, hash_pwd(pw), "admin", now(), "active"), write=True)
    elif row["role"] != "admin" or not check_pwd(pw, row["pwd"]):
        run("UPDATE users SET role='admin', status='active', pwd=? WHERE id=?", (hash_pwd(pw), row["id"]), write=True)


@st.cache_resource
def init_db():
    if use_pg():
        for stmt in pg_schema():
            run(stmt, write=True)
        for table, cols in MIGRATIONS.items():
            for col, ddl in cols.items():
                run(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {ddl}", write=True)
    else:
        old = os.path.join(os.getcwd(), "orich_school.db")  # récupère une base créée par erreur dans un autre dossier
        if not os.path.exists(DB_PATH) and os.path.exists(old):
            shutil.copy(old, DB_PATH)
        conn = sqlite3.connect(DB_PATH)
        conn.executescript(SCHEMA)
        for table, cols in MIGRATIONS.items():
            have = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
            for col, ddl in cols.items():
                if col not in have:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
        conn.commit()
        conn.close()
    bootstrap_admin()
    return True


def get_setting(k, default=""):
    r = run("SELECT v FROM settings WHERE k=?", (k,), one=True)
    return r["v"] if r and r["v"] else default


def set_setting(k, v):
    run("INSERT INTO settings(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, v), write=True)


def log(uid, action, detail=""):
    run("INSERT INTO activity(user_id,action,detail,ts) VALUES(?,?,?,?)", (uid, action, detail[:120], now()), write=True)


def delete_room(rid):
    for tb in ("messages", "room_members", "room_docs"):
        run(f"DELETE FROM {tb} WHERE room_id=?", (rid,), write=True)
    run("DELETE FROM rooms WHERE id=?", (rid,), write=True)


def delete_user(uid):
    for r in run("SELECT id FROM rooms WHERE owner_id=?", (uid,)):
        delete_room(r["id"])
    for tb in ("documents", "summaries", "cards", "quizzes", "scores", "messages", "room_members", "activity", "ai_chats"):
        run(f"DELETE FROM {tb} WHERE user_id=?", (uid,), write=True)
    run("DELETE FROM room_docs WHERE shared_by=?", (uid,), write=True)
    run("DELETE FROM users WHERE id=? AND role!='admin'", (uid,), write=True)


def current_user():
    uid = st.session_state.get("uid")
    u = run("SELECT * FROM users WHERE id=?", (uid,), one=True) if uid else None
    if uid and (not u or u["status"] == "blocked"):
        blocked = bool(u)
        st.session_state.clear()
        if blocked:
            st.session_state.flash_err = "blocked"
        return None
    return u

def level_of(u):
    return u["level"] if u["level"] in LEVELS else "adult"

def flash(msg):
    st.session_state["flash"] = msg


# ───────────────────────────── Langue du cours & documents ─────────────────────────────
STOP = {
    "fr": {"le", "la", "les", "des", "une", "est", "que", "pour", "dans", "avec", "pas", "sur", "qui", "sont", "du", "et"},
    "en": {"the", "and", "of", "to", "is", "in", "that", "for", "with", "are", "this", "was", "on", "as", "it"},
    "it": {"il", "lo", "gli", "che", "di", "per", "con", "non", "una", "sono", "del", "della", "nel", "e"},
    "es": {"el", "los", "las", "de", "que", "y", "en", "un", "una", "por", "con", "para", "es"},
    "de": {"der", "die", "das", "und", "ist", "nicht", "ein", "eine", "mit", "für", "von", "zu", "den"},
}


def detect_lang(text):
    sample = text[:4000]
    if _ld_detect:
        try:
            return _ld_detect(sample).split("-")[0]
        except Exception:
            pass
    words = re.findall(r"[a-zàâçéèêëîïôûùüòìäöß']+", sample.lower())
    scores = {k: sum(w in v for w in words) for k, v in STOP.items()}
    return max(scores, key=scores.get) if any(scores.values()) else "fr"


def clean_text(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def parse_file(f):
    name, raw = f.name.lower(), f.getvalue()
    if name.endswith(".pdf"):
        if PdfReader is None:
            raise RuntimeError("pypdf")
        txt = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(raw)).pages)
        if len(txt.strip()) < 20:
            raise ValueError(t("pdf_scanned"))
        return txt
    for enc in ("utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def save_doc(uid, title, subject, text, source="text"):
    text = clean_text(text)
    if not text:
        return None
    did = run("INSERT INTO documents(user_id,title,lang,content,created,subject,source) VALUES(?,?,?,?,?,?,?)",
              (uid, (title or text[:40]).strip()[:120], detect_lang(text), text, now(), (subject or "").strip()[:60], source), write=True)
    log(uid, "scan" if source == "scan" else "doc", title or text[:40])
    return did


# ───────────────────────────── IA : Groq (texte, vision, voix) ─────────────────────────────
class AIError(Exception):
    """Codes : « off » (IA non configurée), « quota » (limite horaire), « fail » (échec des appels)."""


def ai_msg(e):
    return {"off": t("ai_off"), "quota": t("ai_quota")}.get(str(e), t("error_ai"))


# ── Clé API : fournie uniquement par les secrets de l'hébergeur (jamais dans le code ni dans la base) ──
def api_key():
    return secret("GROQ_API_KEY")


def ai_available():
    return bool(Groq and api_key())


# ── Modèles : choix automatique + bascule si l'un tombe en panne ou est retiré ──
KNOWN_DEAD = {"llama-3.3-70b-versatile", "llama-3.1-8b-instant", "meta-llama/llama-4-scout-17b-16e-instruct",
              "meta-llama/llama-4-maverick-17b-128e-instruct", "qwen/qwen3-32b", "moonshotai/kimi-k2-instruct",
              "moonshotai/kimi-k2-instruct-0905", "deepseek-r1-distill-llama-70b"}
TEXT_PREF = ["openai/gpt-oss-120b", "qwen/qwen3.6-27b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]
VISION_PREF = ["qwen/qwen3.8-27b", "qwen/qwen3.6-27b"]
NOT_CHAT = ("whisper", "guard", "tts", "orpheus", "embed", "safeguard")
_BAD = {}  # modèle -> moment où Groq a répondu « introuvable / retiré »


def list_models():
    """Modèles réellement disponibles pour la clé (liste mise en cache 1 h)."""
    try:
        c = json.loads(get_setting("models_cache") or "null")
        if c and time.time() - c["ts"] < 3600:
            return c["ids"]
    except Exception:
        pass
    try:
        ids = [m.id for m in Groq(api_key=api_key()).models.list().data if not any(x in m.id.lower() for x in NOT_CHAT)]
        set_setting("models_cache", json.dumps({"ts": time.time(), "ids": ids}))
        return ids
    except Exception:
        return []


def model_chain(vision=False):
    avail = list_models()
    chain = []
    for m in [get_setting("vision_model" if vision else "model"), *(VISION_PREF if vision else TEXT_PREF)]:
        if m and m not in KNOWN_DEAD and m not in chain and (not avail or m in avail):
            chain.append(m)
    hints = ("vision", "qwen", "muse", "-vl")
    for m in avail:
        if m not in chain and m not in KNOWN_DEAD and (not vision or any(h in m.lower() for h in hints)):
            chain.append(m)
    alive = [m for m in chain if time.time() - _BAD.get(m, 0) > 3600]
    return (alive or chain)[:5] or (VISION_PREF if vision else TEXT_PREF)


AI_HOURLY_LIMIT = 150


def check_quota():
    """Limite l'usage de l'IA par élève et par heure pour protéger la clé."""
    uid = st.session_state.get("uid")
    if not uid or st.session_state.get("is_admin"):
        return
    since = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    n = run("SELECT COUNT(*) c FROM activity WHERE user_id=? AND action='ai_call' AND ts>=?", (uid, since), one=True)["c"]
    if n >= AI_HOURLY_LIMIT:
        raise AIError("quota")


def _clean(out):
    return re.sub(r"<think>.*?</think>", "", out, flags=re.S).strip()


def _parse_json(out):
    out = re.sub(r"^```(?:json)?|```$", "", _clean(out).strip(), flags=re.M).strip()
    try:
        return json.loads(out)
    except ValueError:
        return json.loads(out[out.index("{"): out.rindex("}") + 1])


def groq_chat(messages, as_json=False, temperature=0.3, max_tokens=None, vision=False):
    """Essaie les modèles dans l'ordre ; l'erreur technique reste visible de l'administrateur seulement."""
    if not ai_available():
        raise AIError("off")
    check_quota()
    client = Groq(api_key=api_key())
    max_tokens = max_tokens or (8000 if as_json else 3000)
    last = None
    for model in model_chain(vision):
        for json_mode in ([True, False] if as_json else [False]):
            try:
                kw = dict(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
                if json_mode:
                    kw["response_format"] = {"type": "json_object"}
                out = client.chat.completions.create(**kw).choices[0].message.content or ""
                log(st.session_state.get("uid"), "ai_call", model)
                return _parse_json(out) if as_json else _clean(out)
            except Exception as e:
                last, msg = e, str(e).lower()
                if "401" in msg or "invalid_api_key" in msg or "invalid api key" in msg:
                    set_setting("last_ai_error", f"{now()} — clé refusée : {str(e)[:200]}")
                    raise AIError("fail")
                if json_mode and ("response_format" in msg or "json" in msg):
                    continue  # ce modèle n'a pas le mode JSON : même modèle, sans ce mode
                if any(x in msg for x in ("decommission", "not found", "does not exist", "model_not_found", "no longer supported", "404")):
                    _BAD[model] = time.time()
                elif "429" in msg or "rate" in msg:
                    time.sleep(1.5)
                break  # modèle suivant
    set_setting("last_ai_error", f"{now()} — {str(last)[:300]}")
    log(st.session_state.get("uid"), "ai_error", str(last)[:100])
    raise AIError("fail")


def ask_groq(system, prompt, **kw):
    return groq_chat([{"role": "system", "content": system}, {"role": "user", "content": prompt}], **kw)


def test_models():
    """Teste chaque modèle de la chaîne (texte puis image). Renvoie [(modèle, est_image, ok, détail)]."""
    out = []
    if not ai_available():
        return out
    client = Groq(api_key=api_key())
    for vision in (False, True):
        for m in model_chain(vision):
            try:
                content = "Réponds OK."
                if vision and Image:
                    buf = io.BytesIO()
                    Image.new("RGB", (160, 60), "white").save(buf, "JPEG")
                    content = [{"type": "text", "text": "Réponds OK."},
                               {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()}}]
                client.chat.completions.create(model=m, messages=[{"role": "user", "content": content}], max_tokens=200)
                out.append((m, vision, True, ""))
            except Exception as e:
                out.append((m, vision, False, str(e)[:160]))
    return out


def transcribe(raw):
    """Voix → texte (Whisper sur Groq)."""
    if not ai_available():
        raise AIError("off")
    check_quota()
    try:
        r = Groq(api_key=api_key()).audio.transcriptions.create(
            file=("voice.wav", raw), model=get_setting("stt_model", "whisper-large-v3-turbo"))
        return (getattr(r, "text", None) or str(r)).strip()
    except Exception as e:
        set_setting("last_ai_error", f"{now()} — voix : {str(e)[:300]}")
        raise AIError("fail")


def prepare_image(raw):
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    img.thumbnail((1800, 1800))
    out = io.BytesIO()
    img.save(out, "JPEG", quality=85)
    return out.getvalue()


def ocr_image(raw):
    """Lit un cours en photo, capture ou manuscrit (modèle de vision, sinon Tesseract si installé)."""
    data = prepare_image(raw) if Image else raw
    if ai_available():
        b64 = base64.b64encode(data).decode()
        return groq_chat([{"role": "user", "content": [
            {"type": "text", "text": "Transcris fidèlement tout le texte de cette image de cours, y compris l'écriture manuscrite, "
                                     "les titres, listes, formules et tableaux (en texte). Conserve la langue d'origine sans traduire. "
                                     "Réponds uniquement avec la transcription."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}],
            vision=True, temperature=0, max_tokens=4000)
    if pytesseract and Image:
        img = Image.open(io.BytesIO(data))
        try:
            return pytesseract.image_to_string(img, lang="fra+eng+ita")
        except Exception:
            return pytesseract.image_to_string(img)
    raise RuntimeError(t("ocr_unavailable"))


SYS = ("Tu es un tuteur rigoureux. Tu travailles UNIQUEMENT à partir du texte du cours fourni : tu n'ajoutes aucune "
       "information extérieure et tu ne déformes pas le contenu du cours.")


def lname(lang):
    return LANG_NAMES.get(lang, lang)


def chunk_text(text, size=6000):
    """Découpe un cours en passages pour que TOUT le contenu soit traité, même s'il est long."""
    chunks, cur = [], ""
    for p in re.split(r"\n\s*\n", text):
        p = p.strip()
        if not p:
            continue
        while len(p) > size:
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(p[:size])
            p = p[size:]
        if cur and len(cur) + len(p) + 2 > size:
            chunks.append(cur)
            cur = ""
        cur += p + "\n\n"
    if cur.strip():
        chunks.append(cur)
    return chunks or [text]


def _per_chunk(chunks, builder, progress):
    """Appelle l'IA sur chaque passage ; ignore un passage en échec, sauf si tout échoue."""
    results, fails = [], 0
    for i, c in enumerate(chunks):
        if progress:
            progress(i / len(chunks))
        try:
            results.append(builder(c, i))
        except AIError as e:
            if str(e) == "off":
                raise
            fails += 1
    if progress:
        progress(1.0)
    if not results:
        raise AIError("fail")
    return results


def gen_summary(text, lang, progress=None):
    base = f"Écris ENTIÈREMENT en {lname(lang)} (la langue du cours). "
    chunks = chunk_text(text, 9000)
    ask = "Fais la fiche de synthèse du cours en Markdown : un titre, les idées clés, les définitions, les exemples du cours, puis une section « À retenir ». N'oublie aucune notion importante."
    if len(chunks) == 1:
        if progress:
            progress(0.3)
        return ask_groq(SYS, f"{base}{ask}\n\nCOURS :\n{chunks[0]}", temperature=0.2)
    notes = _per_chunk(chunks, lambda c, i: ask_groq(
        SYS, f"{base}Voici la partie {i + 1}/{len(chunks)} d'un cours. Résume-la fidèlement en notes structurées, sans omettre aucune notion importante.\n\nPARTIE :\n{c}",
        temperature=0.2), lambda f: progress(f * 0.85) if progress else None)
    return ask_groq(SYS, f"{base}Voici les notes de toutes les parties du cours, dans l'ordre. {ask}\n\nNOTES :\n" + "\n\n".join(notes), temperature=0.2)


def _json_items(data, key):
    return data.get(key, []) if isinstance(data, dict) else []


def gen_cards(text, lang, progress=None):
    def build(c, i):
        data = ask_groq(SYS, f"Crée des flashcards ENTIÈREMENT en {lname(lang)} à partir de ce passage de cours. Fais UNE carte par notion importante "
                             "(définition, idée, date, formule, exemple, cause, conséquence) : couvre TOUT le passage, sans nombre fixé et sans doublon. "
                             'Réponds en JSON strict : {"cards":[{"front":"question","back":"réponse concise"}]}\n\nPASSAGE :\n' + c, as_json=True)
        return _json_items(data, "cards")
    cards, seen = [], set()
    for batch in _per_chunk(chunk_text(text, 6000), build, progress):
        for c in batch:
            if isinstance(c, dict) and c.get("front") and c.get("back"):
                key = str(c["front"]).strip().lower()
                if key not in seen:
                    seen.add(key)
                    cards.append({"front": str(c["front"]).strip(), "back": str(c["back"]).strip()})
    if not cards:
        raise AIError("fail")
    return cards


def gen_quiz(text, lang, progress=None):
    def build(c, i):
        data = ask_groq(SYS, f"Crée un quiz ENTIÈREMENT en {lname(lang)} qui couvre TOUS les points importants de ce passage de cours, sans nombre fixé "
                             "(une à plusieurs questions par notion). Chaque question a 4 options dont une seule correcte, et un niveau : "
                             "1 = rappel direct, 2 = compréhension ou application, 3 = piège ou raisonnement (options très plausibles, nuances, formulations trompeuses). "
                             "Répartis environ 50 % de niveau 1, 30 % de niveau 2 et 20 % de niveau 3. Les questions doivent se comprendre seules "
                             "(n'écris jamais « selon le passage »). Réponds en JSON strict : "
                             '{"questions":[{"q":"...","options":["a","b","c","d"],"answer":0,"level":1,"explanation":"..."}]}\n\nPASSAGE :\n' + c,
                       as_json=True, temperature=0.4)
        return _json_items(data, "questions")
    out, seen = [], set()
    for batch in _per_chunk(chunk_text(text, 6000), build, progress):
        for q in batch:
            try:
                opts = [str(o) for o in q["options"]]
                ans = int(q["answer"])
                key = str(q["q"]).strip().lower()
                if len(opts) < 2 or not 0 <= ans < len(opts) or key in seen:
                    continue
                good = opts[ans]
                random.shuffle(opts)
                lvl = int(q.get("level", 1))
                out.append({"q": str(q["q"]).strip(), "options": opts, "answer": opts.index(good),
                            "level": lvl if lvl in (1, 2, 3) else 1, "explanation": str(q.get("explanation", ""))})
                seen.add(key)
            except Exception:
                continue
    if not out:
        raise AIError("fail")
    return out


def relevant_context(text, question, max_chars=9000):
    """Choisit les passages du cours les plus liés à la question (le tuteur reste centré sur le cours)."""
    if len(text) <= max_chars:
        return text
    chunks = chunk_text(text, 1500)
    words = {w for w in re.findall(r"\w{4,}", question.lower())}
    scored = sorted(range(len(chunks)), key=lambda i: -len(words & set(re.findall(r"\w{4,}", chunks[i].lower()))))
    picked, total = {0}, len(chunks[0])
    for i in scored:
        if i not in picked and total + len(chunks[i]) <= max_chars:
            picked.add(i)
            total += len(chunks[i])
    return "\n\n".join(chunks[i] for i in sorted(picked))


def tutor_reply(d, history, question):
    system = (f"Tu es le tuteur IA d'Orich'School. Tu aides l'élève UNIQUEMENT sur le cours « {d['title']} » fourni ci-dessous. "
              f"Réponds dans la langue dans laquelle l'élève t'écrit ; à défaut, en {lname(d['lang'])}. "
              "Appuie-toi exclusivement sur le contenu du cours : si l'information n'y figure pas, dis-le simplement et propose une question liée au cours. "
              "Sois clair, concis et pédagogue, donne des exemples tirés du cours et vérifie parfois la compréhension par une petite question.\n\n"
              "COURS :\n" + relevant_context(d["content"], question))
    return groq_chat([{"role": "system", "content": system}, *history[-8:], {"role": "user", "content": question}],
                     temperature=0.3, max_tokens=1200)


TTS_LANG = {"fr": "fr-FR", "en": "en-US", "it": "it-IT", "es": "es-ES", "de": "de-DE", "pt": "pt-PT", "nl": "nl-NL",
            "ar": "ar-SA", "ru": "ru-RU", "zh": "zh-CN", "ja": "ja-JP", "tr": "tr-TR", "pl": "pl-PL", "ro": "ro-RO", "sw": "sw-KE"}


# ───────────────────────────── Répétition espacée (SM-2) ─────────────────────────────
def sm2(ef, interval, reps, quality):
    """quality de 0 à 5. Retourne (facilité, intervalle en jours, répétitions)."""
    if quality < 3:
        reps, interval = 0, 1
    else:
        interval = 1 if reps == 0 else 6 if reps == 1 else max(1, round(interval * ef))
        reps += 1
    ef = max(1.3, ef + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    return ef, interval, reps


def rate_card(card, quality):
    ef, interval, reps = sm2(card["ef"], card["interval"], card["reps"], quality)
    due = (date.today() + timedelta(days=interval)).isoformat()
    run("UPDATE cards SET ef=?, interval=?, reps=?, due=? WHERE id=?", (ef, interval, reps, due, card["id"]), write=True)


# ───────────────────────────── Style : glassmorphism sombre ─────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@400;500&display=swap');
:root{--ink:#080b16;--field:#12162b;--violet:#8b6cff;--cyan:#38e1ff;--rose:#ff6fb5;--text:#e9ecff;--muted:#98a0c8;
--glass:rgba(255,255,255,.06);--edge:rgba(139,108,255,.35);color-scheme:dark}
html,body,[class*="css"],.stApp{font-family:'Inter',system-ui,sans-serif;color:var(--text);color-scheme:dark}
.stApp{background:radial-gradient(900px 520px at 8% -10%,rgba(139,108,255,.30),transparent 60%),
radial-gradient(800px 520px at 100% 0%,rgba(56,225,255,.16),transparent 60%),
radial-gradient(700px 500px at 50% 110%,rgba(255,111,181,.10),transparent 60%),var(--ink)}
h1,h2,h3,h4{font-family:'Sora',sans-serif!important;letter-spacing:-.015em;color:var(--text)!important}
#MainMenu,footer,header[data-testid="stHeader"]{visibility:hidden;height:0}
.block-container{padding:1.2rem 1rem 5rem;max-width:1100px}
section[data-testid="stSidebar"]{background:rgba(10,14,30,.85);backdrop-filter:blur(18px);border-right:1px solid var(--edge)}
/* textes : toujours clairs sur fond sombre */
.stApp label,.stApp label p,[data-testid="stWidgetLabel"] p,[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li,
[data-testid="stRadio"] p,[data-testid="stCheckbox"] p,[data-testid="stToggle"] p,.stApp summary p{color:var(--text)!important}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:var(--muted)!important}
/* champs de saisie : fond sombre, texte blanc (corrige le blanc sur blanc) */
div[data-baseweb="input"],div[data-baseweb="base-input"],div[data-baseweb="textarea"],div[data-baseweb="select"]>div,
[data-testid="stNumberInput"] div[data-baseweb="input"]{background:var(--field)!important;border:1px solid var(--edge)!important;border-radius:12px!important}
div[data-baseweb="input"]:focus-within,div[data-baseweb="textarea"]:focus-within,div[data-baseweb="select"]>div:focus-within{border-color:var(--cyan)!important;box-shadow:0 0 0 1px var(--cyan)!important}
input,textarea,[data-baseweb="select"] *{color:#fff!important;-webkit-text-fill-color:#fff!important;caret-color:var(--cyan)!important}
input,textarea{background:transparent!important}
::placeholder{color:#8a92bd!important;-webkit-text-fill-color:#8a92bd!important;opacity:1!important}
div[data-baseweb="popover"] ul,div[data-baseweb="popover"] [role="listbox"],div[data-baseweb="menu"]{background:var(--field)!important;border:1px solid var(--edge);border-radius:12px}
div[data-baseweb="popover"] li,div[data-baseweb="popover"] li *{color:var(--text)!important;-webkit-text-fill-color:var(--text)!important;background:transparent!important}
div[data-baseweb="popover"] li:hover,div[data-baseweb="popover"] li[aria-selected="true"]{background:rgba(139,108,255,.28)!important}
[data-testid="stChatInput"],[data-testid="stChatInput"]>div{background:var(--field)!important;border:1px solid var(--edge)!important;border-radius:16px!important}
[data-testid="stChatInput"] textarea{color:#fff!important}
[data-testid="stChatMessage"]{background:var(--glass);border:1px solid var(--edge);border-radius:16px;padding:.7rem .9rem}
[data-testid="stExpander"]{background:var(--glass);border:1px solid var(--edge)!important;border-radius:14px}
[data-testid="stAudioInput"],[data-testid="stCameraInput"]{background:var(--glass);border:1px solid var(--edge);border-radius:16px;padding:.4rem}
[data-testid="stDataFrame"]{border:1px solid var(--edge);border-radius:12px}
/* cartes verre */
.glass{background:var(--glass);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);border:1px solid var(--edge);
border-radius:20px;padding:1.1rem 1.3rem;margin-bottom:1rem;box-shadow:0 0 28px rgba(139,108,255,.14),inset 0 1px 0 rgba(255,255,255,.08)}
.stat b{display:block;font:700 2rem 'Sora',sans-serif;color:var(--cyan)}.stat span{color:var(--muted);font-size:.9rem}
.brand{font:800 1.45rem 'Sora',sans-serif;background:linear-gradient(90deg,var(--violet),var(--cyan));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.pill{display:inline-block;padding:.15rem .7rem;border-radius:99px;border:1px solid var(--edge);color:var(--cyan);font-size:.8rem;margin:.1rem .25rem .1rem 0}
.muted{color:var(--muted)}
/* accueil public */
.hero{display:grid;grid-template-columns:1.15fr .85fr;gap:2.4rem;align-items:center;padding:2.2rem 0 1rem}
.hero h1{font-size:clamp(2rem,5.2vw,3.5rem);line-height:1.08;margin:0 0 1rem;font-weight:800}
.lead{font-size:1.1rem;line-height:1.65;color:var(--muted);max-width:56ch}
.demo{position:relative;padding:.5rem}.demo .cap{color:var(--muted);font-size:.85rem;margin-bottom:.6rem}
.mini{border:1px solid var(--edge);border-radius:22px;padding:1.4rem 1.5rem;font-size:1.15rem;line-height:1.45;background:linear-gradient(145deg,rgba(139,108,255,.22),rgba(56,225,255,.08));box-shadow:0 0 40px rgba(139,108,255,.28)}
.mini.back{margin:-.5rem 0 0 1.6rem;font-size:1rem;background:linear-gradient(145deg,rgba(56,225,255,.2),rgba(255,111,181,.12));border-color:rgba(56,225,255,.5)}
.sec{font:700 1.5rem 'Sora',sans-serif;margin:2.4rem 0 1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:1rem}
.fcard{background:var(--glass);backdrop-filter:blur(18px);border:1px solid var(--edge);border-radius:20px;padding:1.2rem 1.3rem;box-shadow:0 0 24px rgba(139,108,255,.12)}
.fcard .ico{font-size:1.6rem}.fcard h4{margin:.5rem 0 .3rem;font-size:1.05rem}.fcard p{margin:0;color:var(--muted)!important;line-height:1.55;font-size:.95rem}
.step b{font:800 2rem 'Sora',sans-serif;color:var(--violet)}
.chips{display:flex;flex-wrap:wrap;gap:.5rem;margin-top:.8rem}
.chip{padding:.45rem 1rem;border-radius:99px;border:1px solid var(--edge);background:var(--glass)}
/* cartes & chat de salon */
.flash{min-height:200px;display:flex;align-items:center;justify-content:center;text-align:center;font-size:1.25rem;line-height:1.5;
background:linear-gradient(145deg,rgba(139,108,255,.18),rgba(56,225,255,.08));border:1px solid var(--edge);border-radius:24px;padding:2rem;box-shadow:0 0 40px rgba(139,108,255,.25)}
.flash.back{background:linear-gradient(145deg,rgba(56,225,255,.2),rgba(255,111,181,.1));border-color:rgba(56,225,255,.5)}
.bubble{background:var(--glass);border:1px solid rgba(255,255,255,.1);border-radius:16px;padding:.55rem .85rem;margin:.35rem 0;max-width:88%}
.bubble.me{margin-left:auto;border-color:var(--edge);background:rgba(139,108,255,.2)}.bubble small{color:var(--muted)}
/* admin */
.live{display:inline-flex;align-items:center;gap:.5rem;color:var(--cyan)}
.live::before{content:"";width:9px;height:9px;border-radius:50%;background:#3dffa0;box-shadow:0 0 10px #3dffa0;animation:pulse 1.6s infinite}
@keyframes pulse{50%{opacity:.35}}
.feed-row{padding:.45rem 0;border-bottom:1px solid rgba(255,255,255,.07);font-size:.93rem}
.feed-row span{color:var(--muted);margin-right:.6rem;font-variant-numeric:tabular-nums}.feed-row em{color:var(--muted);margin-left:.4rem}
/* boutons */
.stButton>button,.stDownloadButton>button,div[data-testid="stFormSubmitButton"]>button{border-radius:14px;border:1px solid var(--edge);
background:linear-gradient(135deg,rgba(139,108,255,.35),rgba(56,225,255,.2));color:var(--text);font-weight:600;transition:box-shadow .2s,transform .1s}
.stButton>button p,.stDownloadButton>button p,div[data-testid="stFormSubmitButton"]>button p{color:inherit!important}
.stButton>button[kind="primary"],div[data-testid="stFormSubmitButton"]>button[kind="primaryFormSubmit"]{background:linear-gradient(135deg,#7f5cff,#2ec8f0);border-color:transparent;color:#05070f}
.stButton>button:hover{box-shadow:0 0 18px rgba(139,108,255,.55);border-color:var(--cyan);color:#fff}
.stButton>button[kind="primary"]:hover{color:#05070f}.stButton>button:active{transform:scale(.98)}
[data-testid="stFileUploaderDropzone"]{background:var(--glass);border:1px dashed var(--edge);border-radius:18px}
.stTabs [data-baseweb="tab-list"]{gap:.4rem;flex-wrap:wrap}.stTabs [data-baseweb="tab"]{background:var(--glass);border-radius:12px;padding:.4rem 1rem}
.stTabs [aria-selected="true"]{border:1px solid var(--cyan)}
@media (max-width:820px){.hero{grid-template-columns:1fr;gap:1.2rem;padding-top:1rem}}
@media (max-width:640px){.block-container{padding:.8rem .6rem 5rem}.flash{min-height:160px;font-size:1.05rem;padding:1.2rem}
.stat b{font-size:1.5rem}.bubble{max-width:96%}div[data-testid="stHorizontalBlock"]{flex-wrap:wrap;gap:.5rem}
div[data-testid="stHorizontalBlock"]>div{min-width:calc(50% - .5rem)!important}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
"""


def uploader_css():
    """Traduit les textes internes du sélecteur de fichiers dans la langue de l'interface."""
    return (f'<style>[data-testid="stFileUploaderDropzoneInstructions"]>div>span{{font-size:0!important}}'
            f'[data-testid="stFileUploaderDropzoneInstructions"]>div>span::before{{content:"{t("drop")}";font-size:1rem;color:#e9ecff}}'
            f'[data-testid="stFileUploaderDropzone"] button{{font-size:0!important}}'
            f'[data-testid="stFileUploaderDropzone"] button::after{{content:"{t("browse")}";font-size:.9rem}}</style>')


def glass(content):
    st.markdown(f'<div class="glass">{content}</div>', unsafe_allow_html=True)


# ───────────────────────────── Langue de l'interface ─────────────────────────────
def on_lang(key):
    st.session_state.lang = st.session_state[key]
    uid = st.session_state.get("uid")
    if uid:
        run("UPDATE users SET lang=? WHERE id=?", (st.session_state.lang, uid), write=True)


def lang_picker(key, label=True):
    st.session_state[key] = st.session_state.get("lang", "fr")
    st.selectbox(t("ui_lang") if label else "🌐", list(LANGS), format_func=LANGS.get, key=key, on_change=on_lang,
                 args=(key,), label_visibility="visible" if label else "collapsed")


def goto(view, mode=None):
    st.session_state.view = view
    if mode:
        st.session_state.auth_mode = mode


def go_page(page):
    st.session_state.nav = page


def open_studio(doc_id):
    st.session_state.nav = "studio"
    st.session_state.studio_doc = doc_id


# ───────────────────────────── Pages publiques ─────────────────────────────
def page_landing():
    c1, c2, c3 = st.columns([3, 2, 2])
    c1.markdown("<span class='brand'>Orich'School</span>", unsafe_allow_html=True)
    with c2:
        lang_picker("lang_landing", label=False)
    c3.button(t("login"), key="top_login", on_click=goto, args=("auth", "login"), use_container_width=True)

    st.markdown(f"""
    <div class="hero">
      <div><h1>{t('hero_title')}</h1><p class="lead">{t('hero_sub')}</p></div>
      <div class="demo"><div class="cap">{t('demo_cap')}</div>
        <div class="mini">{t('demo_q')}</div><div class="mini back">{t('demo_a')}</div></div>
    </div>""", unsafe_allow_html=True)
    b1, b2, _ = st.columns([2, 2, 3])
    b1.button(t("start"), key="hero_start", type="primary", on_click=goto, args=("auth", "register"), use_container_width=True)
    b2.button(t("login"), key="hero_login", on_click=goto, args=("auth", "login"), use_container_width=True)

    feats = [("📷", "f1"), ("🌍", "f2"), ("🎓", "f3"), ("✨", "f4"), ("🔁", "f5"), ("👥", "f6")]
    cards = "".join(f"<div class='fcard'><div class='ico'>{i}</div><h4>{t(k + 't')}</h4><p>{t(k + 'd')}</p></div>" for i, k in feats)
    st.markdown(f"<div class='sec'>{t('feat_title')}</div><div class='grid'>{cards}</div>", unsafe_allow_html=True)

    steps = "".join(f"<div class='fcard step'><b>{n}</b><h4>{t(f's{n}t')}</h4><p>{t(f's{n}d')}</p></div>" for n in (1, 2, 3))
    st.markdown(f"<div class='sec'>{t('how_title')}</div><div class='grid'>{steps}</div>", unsafe_allow_html=True)

    chips = "".join(f"<span class='chip'>{t('lvl_' + k)}</span>" for k in LEVELS)
    st.markdown(f"<div class='sec'>{t('who_title')}</div><div class='glass'><p class='lead' style='margin:0'>{t('who_sub')}</p>"
                f"<div class='chips'>{chips}</div></div>", unsafe_allow_html=True)

    st.markdown(f"<div class='sec' style='text-align:center'>{t('cta_final')}</div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    mid.button(t("start"), key="final_start", type="primary", on_click=goto, args=("auth", "register"), use_container_width=True)


MAX_FAILS, LOCK_MINUTES = 5, 15
_DUMMY = []


def is_locked(key):
    r = run("SELECT locked_until FROM login_attempts WHERE k=?", (key,), one=True)
    return bool(r and r["locked_until"] and r["locked_until"] > now())


def register_fail(key, limit=MAX_FAILS):
    r = run("SELECT n FROM login_attempts WHERE k=?", (key,), one=True)
    n = (r["n"] if r else 0) + 1
    until = (datetime.now() + timedelta(minutes=LOCK_MINUTES)).strftime("%Y-%m-%d %H:%M:%S") if n >= limit else ""
    run("INSERT INTO login_attempts(k,n,locked_until) VALUES(?,?,?) ON CONFLICT(k) DO UPDATE SET n=excluded.n, locked_until=excluded.locked_until",
        (key, 0 if until else n, until), write=True)


def clear_fails(key):
    run("DELETE FROM login_attempts WHERE k=?", (key,), write=True)


def dummy_check(pwd):
    """Même durée de calcul que pour un vrai compte : on ne révèle pas si un nom existe."""
    if not _DUMMY:
        _DUMMY.append(hash_pwd("dummy"))
    check_pwd(pwd, _DUMMY[0])


def page_auth():
    st.button("← " + t("back"), key="auth_back", on_click=goto, args=("landing",))
    st.markdown("<div style='text-align:center'><span class='brand' style='font-size:2.3rem'>Orich'School</span>"
                f"<p class='muted'>{t('tagline')}</p></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        lang_picker("lang_auth", label=False)
        if st.session_state.get("flash_err") == "blocked":
            st.error(t("blocked"))
        mode = st.radio("mode", ["login", "register"], format_func=t, horizontal=True, key="auth_mode", label_visibility="collapsed")
        if mode == "login":
            with st.form("login"):
                n, p = st.text_input(t("name"), max_chars=60), st.text_input(t("password"), type="password", max_chars=128)
                if st.form_submit_button(t("login"), use_container_width=True, type="primary"):
                    name = n.strip()
                    key = "u:" + name.lower()
                    if is_locked(key):
                        st.error(t("too_many"))
                    else:
                        u = run("SELECT * FROM users WHERE name=?", (name,), one=True)
                        if not u:
                            dummy_check(p)
                        if not u or u["role"] == "admin" or not check_pwd(p, u["pwd"]):
                            register_fail(key)
                            st.error(t("bad_login"))
                        elif u["status"] == "blocked":
                            st.error(t("blocked"))
                        else:
                            clear_fails(key)
                            st.session_state.update(uid=u["id"], lang=u["lang"] if u["lang"] in LANGS else "fr")
                            st.session_state.pop("flash_err", None)
                            log(u["id"], "login")
                            st.rerun()
        else:
            with st.form("register"):
                n = st.text_input(t("name"), key="reg_name", max_chars=40)
                p = st.text_input(t("password"), type="password", key="reg_pwd", max_chars=128)
                lv = st.selectbox(t("level"), LEVELS, format_func=lambda k: t("lvl_" + k), index=1)
                st.caption(t("level_hint"))
                if st.form_submit_button(t("register"), use_container_width=True, type="primary"):
                    since = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
                    if not n.strip():
                        st.error(t("fill"))
                    elif len(p) < 6:
                        st.error(t("pwd_short"))
                    elif run("SELECT COUNT(*) c FROM activity WHERE action='register' AND ts>=?", (since,), one=True)["c"] >= 30:
                        st.error(t("reg_limit"))
                    elif n.strip().lower() == secret("ADMIN_USER", "admin").lower() or run("SELECT id FROM users WHERE name=?", (n.strip(),), one=True):
                        st.error(t("name_taken"))
                    else:
                        uid = run("INSERT INTO users(name,pwd,lang,level,created) VALUES(?,?,?,?,?)",
                                  (n.strip(), hash_pwd(p), st.session_state.get("lang", "fr"), lv, now()), write=True)
                        st.session_state.uid = uid
                        log(uid, "register")
                        st.rerun()


def admin_url_ok():
    """L'espace administrateur n'est joignable que via une adresse secrète (?admin=<ADMIN_URL_KEY>)."""
    got = st.query_params.get("admin", "")
    return bool(got) and secrets.compare_digest(str(got), secret("ADMIN_URL_KEY", "1"))


def leave_admin_page():
    st.query_params.clear()
    st.session_state.view = "landing"


def page_admin_login():
    st.button("← " + t("back"), key="adm_back", on_click=leave_admin_page)
    st.markdown("<div style='text-align:center'><span class='brand' style='font-size:2rem'>Orich'School</span></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        lang_picker("lang_adm", label=False)
        st.markdown(f"#### {t('admin_link')}")
        with st.form("admin_login"):
            n, p = st.text_input(t("name"), max_chars=60), st.text_input(t("password"), type="password", max_chars=128)
            if st.form_submit_button(t("login"), use_container_width=True, type="primary"):
                key = "a:" + n.strip().lower()
                if is_locked(key) or is_locked("a:*"):
                    st.error(t("too_many"))
                else:
                    u = run("SELECT * FROM users WHERE name=? AND role='admin'", (n.strip(),), one=True)
                    if not u:
                        dummy_check(p)
                    if u and check_pwd(p, u["pwd"]):
                        clear_fails(key)
                        st.session_state.update(uid=u["id"], lang=u["lang"] if u["lang"] in LANGS else "fr", admin_last=time.time())
                        st.rerun()
                    register_fail(key)
                    register_fail("a:*", limit=20)
                    st.error(t("bad_login"))


# ───────────────────────────── Pages apprenant ─────────────────────────────
def page_home(u):
    uid = u["id"]
    st.markdown(f"## {t('hello')} {html.escape(u['name'])} 👋")
    st.markdown(f"<span class='pill'>{t('level')} : {t('lvl_' + level_of(u))}</span>", unsafe_allow_html=True)
    nd = run("SELECT COUNT(*) c FROM documents WHERE user_id=?", (uid,), one=True)["c"]
    nc = run("SELECT COUNT(*) c FROM cards WHERE user_id=?", (uid,), one=True)["c"]
    due = run("SELECT COUNT(*) c FROM cards WHERE user_id=? AND due<=?", (uid, today()), one=True)["c"]
    sc = run("SELECT AVG(100.0*score/total) a FROM scores WHERE user_id=? AND total>0", (uid,), one=True)["a"]
    for col, (val, label) in zip(st.columns(4), [(nd, t("st_docs")), (nc, t("st_cards")), (due, t("st_due")),
                                                (f"{sc:.0f}%" if sc is not None else "–", t("st_avg"))]):
        with col:
            glass(f"<div class='stat'><b>{val}</b><span>{label}</span></div>")
    a, b, c, e = st.columns(4)
    a.button("📷 " + t("qa_scan"), key="qa1", type="primary", on_click=go_page, args=("docs",), use_container_width=True)
    b.button("🤖 " + t("tutor"), key="qa4", on_click=go_page, args=("tutor",), use_container_width=True)
    c.button("🔁 " + t("qa_review"), key="qa2", on_click=go_page, args=("review",), use_container_width=True)
    e.button("👥 " + t("qa_rooms"), key="qa3", on_click=go_page, args=("rooms",), use_container_width=True)
    rows = run("SELECT d.id,d.title,d.subject,d.lang,(SELECT COUNT(*) FROM cards c WHERE c.doc_id=d.id) n FROM documents d "
               "WHERE d.user_id=? ORDER BY d.id DESC LIMIT 5", (uid,))
    st.markdown(f"#### {t('recent')}")
    if not rows:
        st.info(t("empty_docs"))
    for r in rows:
        c1, c2 = st.columns([4, 1])
        with c1:
            sub = f"<span class='pill'>{html.escape(r['subject'])}</span>" if r["subject"] else ""
            glass(f"<b>{html.escape(r['title'])}</b><br>{sub}<span class='pill'>{lname(r['lang'])}</span>"
                  f"<span class='muted'>{r['n']} {t('st_cards').lower()}</span>")
        c2.button(t("study"), key=f"h_st{r['id']}", on_click=open_studio, args=(r["id"],), use_container_width=True)


def run_extract(u, images, source="scan"):
    texts = []
    with st.spinner(t("reading")):
        try:
            for raw in images:
                texts.append(ocr_image(raw))
        except AIError as e:
            st.error(ai_msg(e))
            return
        except RuntimeError as e:
            st.error(str(e))
            return
        except Exception:
            st.error(t("ocr_fail"))
            return
    text = clean_text("\n\n".join(x for x in texts if x))
    if not text:
        st.warning(t("no_text"))
        return
    st.session_state.draft = {"text": text, "title": f"{datetime.now():%d/%m %H:%M}", "subject": "", "source": source}
    st.session_state.scan_pages = []
    st.rerun()


def draft_review(u):
    d = st.session_state.get("draft")
    if not d:
        return
    st.markdown(f"#### ✅ {t('check_text')}")
    with st.form("draft_form"):
        title = st.text_input(t("title"), value=d["title"])
        subject = st.text_input(t("subject"), value=d["subject"])
        text = st.text_area("text", value=d["text"], height=280, label_visibility="collapsed")
        c1, c2 = st.columns(2)
        ok = c1.form_submit_button(t("save"), use_container_width=True, type="primary")
        cancel = c2.form_submit_button(t("cancel"), use_container_width=True)
    if ok:
        save_doc(u["id"], title, subject, text, d["source"])
        st.session_state.pop("draft")
        flash(t("saved"))
        st.rerun()
    if cancel:
        st.session_state.pop("draft")
        st.rerun()


def tab_photo(u):
    st.caption(t("cam_hint"))
    pages = st.session_state.setdefault("scan_pages", [])
    n = st.session_state.setdefault("cam_n", 0)
    shot = st.camera_input(t("cam_label"), key=f"cam_{n}")
    if shot is not None and st.button(t("add_page"), key="add_page", type="primary", use_container_width=True):
        pages.append(shot.getvalue())
        st.session_state.cam_n = n + 1
        st.rerun()
    if pages:
        st.caption(t("pages_n", n=len(pages)))
        st.image(pages, width=90)
        c1, c2 = st.columns(2)
        if c1.button(t("extract"), key="extract_cam", type="primary", use_container_width=True):
            run_extract(u, pages)
        if c2.button(t("clear_pages"), key="clear_cam", use_container_width=True):
            st.session_state.scan_pages = []
            st.rerun()
    st.divider()
    st.caption(t("cam_native"))
    nat_n = st.session_state.setdefault("nat_n", 0)
    nat = st.file_uploader(t("cam_native"), type=list(IMG_EXT), accept_multiple_files=True, key=f"nat_{nat_n}", label_visibility="collapsed")
    if nat and st.button(t("extract"), key="extract_nat", type="primary", use_container_width=True):
        st.session_state.nat_n = nat_n + 1
        run_extract(u, [f.getvalue() for f in nat])


def tab_files(u):
    up_n = st.session_state.setdefault("up_n", 0)
    files = st.file_uploader(t("upload"), type=["pdf", "txt", "md", "markdown", *IMG_EXT], accept_multiple_files=True, key=f"up_{up_n}")
    if files and st.button(t("save"), key="save_files", type="primary", use_container_width=True):
        images, saved = [], 0
        for f in files:
            if f.name.lower().rsplit(".", 1)[-1] in IMG_EXT:
                images.append(f.getvalue())
                continue
            try:
                if save_doc(u["id"], f.name, "", parse_file(f), "file"):
                    saved += 1
            except Exception as e:
                st.error(f"{f.name} — {t('read_err')} {e if isinstance(e, ValueError) else ''}")
        st.session_state.up_n = up_n + 1
        if images:
            run_extract(u, images, "scan")
        elif saved:
            flash(t("saved"))
            st.rerun()


def tab_text(u):
    with st.form("paste_form", clear_on_submit=True):
        title = st.text_input(t("title"))
        subject = st.text_input(t("subject"))
        body = st.text_area(t("paste"), height=180)
        if st.form_submit_button(t("save"), use_container_width=True, type="primary") and body.strip():
            save_doc(u["id"], title, subject, body, "text")
            flash(t("saved"))
            st.rerun()


def page_docs(u):
    st.markdown(f"## {t('docs')}")
    draft_review(u)
    if not st.session_state.get("draft"):
        st.markdown(f"#### {t('add_course')}")
        t1, t2, t3 = st.tabs([t("tab_photo"), t("tab_files"), t("tab_text")])
        with t1:
            tab_photo(u)
        with t2:
            tab_files(u)
        with t3:
            tab_text(u)
    docs = run("SELECT id,title,subject,lang,source,LENGTH(content) n FROM documents WHERE user_id=? ORDER BY id DESC", (u["id"],))
    st.markdown(f"#### {t('my_courses')}")
    if not docs:
        st.info(t("empty_docs"))
    for d in docs:
        c1, c2, c3 = st.columns([4, 1, 1])
        with c1:
            sub = f"<span class='pill'>{html.escape(d['subject'])}</span>" if d["subject"] else ""
            icon = "📷" if d["source"] == "scan" else "📄"
            glass(f"{icon} <b>{html.escape(d['title'])}</b><br>{sub}<span class='pill'>{t('detected')} : {lname(d['lang'])}</span>"
                  f"<span class='muted'>{d['n']} {t('chars')}</span>")
        c2.button(t("study"), key=f"d_st{d['id']}", on_click=open_studio, args=(d["id"],), use_container_width=True)
        if c3.button(t("delete"), key=f"del{d['id']}", use_container_width=True):
            for tb in ("summaries", "cards", "quizzes", "scores", "ai_chats"):
                run(f"DELETE FROM {tb} WHERE doc_id=?", (d["id"],), write=True)
            run("DELETE FROM documents WHERE id=?", (d["id"],), write=True)
            st.rerun()


def run_ai(fn, *args):
    """Lance une génération IA et affiche un message clair (sans détail technique) en cas de problème."""
    try:
        return fn(*args)
    except AIError as e:
        st.error(ai_msg(e))
    return None


def progress_cb():
    bar = st.progress(0.0, text=t("generating"))
    return lambda f: bar.progress(min(max(f, 0.0), 1.0), text=t("generating"))


def tab_summary(u, d):
    last = run("SELECT * FROM summaries WHERE doc_id=? ORDER BY id DESC", (d["id"],), one=True)
    if st.button(t("generate"), key="gen_sum", type="primary", use_container_width=True):
        content = run_ai(gen_summary, d["content"], d["lang"], progress_cb())
        if content:
            run("INSERT INTO summaries(user_id,doc_id,content,created) VALUES(?,?,?,?)", (u["id"], d["id"], content, now()), write=True)
            log(u["id"], "summary", d["title"])
            st.rerun()
    if last:
        glass("")
        st.markdown(last["content"])
        st.download_button("⬇ .md", last["content"], file_name=f"{d['title']}.md")
    else:
        st.info(t("no_summary"))


def tab_cards(u, d):
    if st.button(t("generate"), key="gen_cards", type="primary", use_container_width=True):
        cards = run_ai(gen_cards, d["content"], d["lang"], progress_cb())
        if cards:
            have = {r["front"].strip().lower() for r in run("SELECT front FROM cards WHERE doc_id=? AND user_id=?", (d["id"], u["id"]))}
            added = 0
            for c in cards:
                if c["front"].lower() not in have:
                    run("INSERT INTO cards(user_id,doc_id,front,back,due) VALUES(?,?,?,?,?)",
                        (u["id"], d["id"], c["front"], c["back"], today()), write=True)
                    added += 1
            log(u["id"], "cards", d["title"])
            flash(t("cards_added", n=added))
            st.rerun()
    cards = run("SELECT * FROM cards WHERE doc_id=? AND user_id=? ORDER BY id", (d["id"], u["id"]))
    if not cards:
        st.info(t("no_cards"))
        return
    ik, fk = f"ci_{d['id']}", f"cf_{d['id']}"
    st.session_state.setdefault(ik, 0)
    st.session_state.setdefault(fk, False)
    i = st.session_state[ik] % len(cards)
    c = cards[i]
    flipped = st.session_state[fk]
    st.caption(f"{i + 1}/{len(cards)} · {t('back_side') if flipped else t('front')}")
    st.markdown(f"<div class='flash {'back' if flipped else ''}'>{html.escape(c['back'] if flipped else c['front'])}</div>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns(3)
    if b1.button(t("prev"), key="c_prev", use_container_width=True):
        st.session_state[ik], st.session_state[fk] = i - 1, False
        st.rerun()
    if b2.button(t("flip"), key="c_flip", type="primary", use_container_width=True):
        st.session_state[fk] = not flipped
        st.rerun()
    if b3.button(t("next"), key="c_next", use_container_width=True):
        st.session_state[ik], st.session_state[fk] = i + 1, False
        st.rerun()


PASS_RATE = 0.7


def tab_quiz(u, d):
    if st.button(t("generate"), key="gen_quiz", type="primary", use_container_width=True):
        qs = run_ai(gen_quiz, d["content"], d["lang"], progress_cb())
        if qs:
            run("INSERT INTO quizzes(user_id,doc_id,data,created) VALUES(?,?,?,?)",
                (u["id"], d["id"], json.dumps(qs, ensure_ascii=False), now()), write=True)
            log(u["id"], "quiz", d["title"])
            st.rerun()
    qz = run("SELECT * FROM quizzes WHERE doc_id=? AND user_id=? ORDER BY id DESC", (d["id"], u["id"]), one=True)
    if not qz:
        st.info(t("no_quiz"))
        return
    qid, questions = qz["id"], json.loads(qz["data"])
    by_level = {n: [q for q in questions if q.get("level", 1) == n] for n in (1, 2, 3)}
    levels = [n for n in (1, 2, 3) if by_level[n]]
    if not levels:
        st.info(t("no_quiz"))
        return
    st.caption(t("quiz_total", n=len(questions)))
    cur = st.session_state.get(f"ql_{qid}", levels[0])
    if cur not in levels:
        cur = levels[0]
    st.progress((levels.index(cur) + 1) / len(levels), text=f"{t('level_n', n=cur)} · {t('lvl_name_' + str(cur))}")
    attempt = st.session_state.get(f"qt_{qid}_{cur}", 0)
    qs = list(by_level[cur])
    random.Random(f"{qid}-{cur}-{attempt}").shuffle(qs)
    res = st.session_state.get(f"qr_{qid}_{cur}_{attempt}")

    if res is None:  # session de questions : on peut changer de réponse jusqu'à la validation
        st.caption(t("quiz_hint"))
        with st.form(f"qf_{qid}_{cur}_{attempt}"):
            picks = []
            for i, q in enumerate(qs):
                st.markdown(f"**{i + 1}. {q['q']}**")
                picks.append(st.radio(f"q{i}", q["options"], index=None, key=f"qa_{qid}_{cur}_{attempt}_{i}", label_visibility="collapsed"))
            sent = st.form_submit_button(t("validate"), use_container_width=True, type="primary")
        if sent:
            score = sum(1 for q, p in zip(qs, picks) if p is not None and q["options"].index(p) == q["answer"])
            st.session_state[f"qr_{qid}_{cur}_{attempt}"] = {"score": score, "picks": picks}
            run("INSERT INTO scores(user_id,doc_id,score,total,created) VALUES(?,?,?,?,?)", (u["id"], d["id"], score, len(qs), now()), write=True)
            log(u["id"], "score", f"{t('level_n', n=cur)} · {score}/{len(qs)}")
            st.rerun()
        return

    score, total = res["score"], len(qs)
    passed = score / total >= PASS_RATE
    glass(f"<b>{t('score')} : {score}/{total}</b> · {round(100 * score / total)} %")
    (st.success if passed else st.warning)(t("passed") if passed else t("failed"))
    with st.expander(t("correction")):
        for i, (q, p) in enumerate(zip(qs, res["picks"])):
            good = p is not None and q["options"].index(p) == q["answer"]
            st.markdown(f"{'✅' if good else '❌'} **{i + 1}. {q['q']}**")
            st.caption(f"{t('your_answer')} : {p if p is not None else t('unanswered')} · {t('right_answer')} : {q['options'][q['answer']]}")
            if q.get("explanation"):
                st.caption(q["explanation"])
    nxt = next((n for n in levels if n > cur), None)
    if passed and not nxt:
        st.success(t("all_done"))
        if not st.session_state.get(f"bal_{qid}"):
            st.session_state[f"bal_{qid}"] = True
            st.balloons()
    c1, c2, c3 = st.columns(3)
    if passed and nxt and c1.button(t("next_level"), key="q_next", type="primary", use_container_width=True):
        st.session_state[f"ql_{qid}"] = nxt
        st.rerun()
    if c2.button(t("retry_level"), key="q_retry", use_container_width=True):
        st.session_state[f"qt_{qid}_{cur}"] = attempt + 1
        st.rerun()
    if cur != levels[0] and c3.button(t("restart_quiz"), key="q_restart", use_container_width=True):
        st.session_state[f"ql_{qid}"] = levels[0]
        st.rerun()


def page_studio(u):
    st.markdown(f"## {t('studio')}")
    docs = run("SELECT * FROM documents WHERE user_id=? ORDER BY id DESC", (u["id"],))
    if not docs:
        st.info(t("empty_docs"))
        return
    by_id = {d["id"]: d for d in docs}
    if st.session_state.get("studio_doc") not in by_id:
        st.session_state.pop("studio_doc", None)
    sel = st.selectbox(t("choose_doc"), list(by_id), format_func=lambda i: by_id[i]["title"], key="studio_doc")
    d = by_id[sel]
    st.markdown(f"<span class='pill'>{t('detected')} : {lname(d['lang'])}</span>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs([f"📝 {t('summary')}", f"🃏 {t('flashcards')}", f"🎯 {t('quiz')}"])
    with t1:
        tab_summary(u, d)
    with t2:
        tab_cards(u, d)
    with t3:
        tab_quiz(u, d)


# ───────────────────────────── Tuteur IA (écrit et voix) ─────────────────────────────
def speak_widget(text, lang, auto=False):
    """Bouton de lecture à voix haute (synthèse vocale du navigateur, dans la langue du cours)."""
    import streamlit.components.v1 as components
    payload = json.dumps(re.sub(r"[*_`#>|]", "", text)[:2500]).replace("</", "<\\/")
    listen, stop = json.dumps("🔊 " + t("listen")), json.dumps("⏹ " + t("stop"))
    auto_js = "setTimeout(play, 300);" if auto else ""
    components.html(f"""
<button id="b" style="background:rgba(139,108,255,.25);color:#e9ecff;border:1px solid rgba(139,108,255,.5);border-radius:12px;padding:.45rem 1rem;font:600 14px system-ui;cursor:pointer"></button>
<script>
const T={payload}, L={json.dumps(TTS_LANG.get(lang, "fr-FR"))}, LISTEN={listen}, STOP={stop};
const b=document.getElementById('b'); let on=false; b.textContent=LISTEN;
function stopAll(){{speechSynthesis.cancel(); on=false; b.textContent=LISTEN;}}
function play(){{try{{speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance(T); u.lang=L; u.onend=stopAll; u.onerror=stopAll; speechSynthesis.speak(u); on=true; b.textContent=STOP;}}catch(e){{}}}}
b.onclick=()=>on?stopAll():play();
{auto_js}
</script>""", height=52)


def set_quick(text):
    st.session_state.quick = text


def page_tutor(u):
    st.markdown(f"## 🤖 {t('tutor')}")
    docs = run("SELECT id,title,lang,content FROM documents WHERE user_id=? ORDER BY id DESC", (u["id"],))
    if not docs:
        st.info(t("empty_docs"))
        return
    by_id = {d["id"]: d for d in docs}
    if st.session_state.get("tutor_doc") not in by_id:
        st.session_state.pop("tutor_doc", None)
    d = by_id[st.selectbox(t("choose_doc"), list(by_id), format_func=lambda i: by_id[i]["title"], key="tutor_doc")]
    st.caption(t("tutor_hint"))
    hist = run("SELECT role,content FROM ai_chats WHERE user_id=? AND doc_id=? ORDER BY id", (u["id"], d["id"]))
    with st.container(height=420, border=True):
        if not hist:
            st.caption(t("tutor_empty"))
        for m in hist:
            with st.chat_message("user" if m["role"] == "user" else "assistant"):
                st.markdown(m["content"])
    auto = bool(st.session_state.pop("speak_new", False) and st.session_state.get("auto_voice"))
    if hist and hist[-1]["role"] == "assistant":
        speak_widget(hist[-1]["content"], d["lang"], auto)

    cols = st.columns(3)
    for col, k in zip(cols, ("tq1", "tq2", "tq3")):
        col.button(t(k), key=k, on_click=set_quick, args=(t(k),), use_container_width=True)
    o1, o2 = st.columns(2)
    o1.toggle(t("auto_voice"), key="auto_voice")
    if o2.button(t("clear_chat"), key="clr_chat", use_container_width=True):
        run("DELETE FROM ai_chats WHERE user_id=? AND doc_id=?", (u["id"], d["id"]), write=True)
        st.rerun()

    prompt = st.session_state.pop("quick", None)
    if hasattr(st, "audio_input"):
        n = st.session_state.setdefault("mic_n", 0)
        audio = st.audio_input(t("mic"), key=f"mic_{n}")
        if audio is not None:
            st.session_state.mic_n = n + 1
            with st.spinner(t("thinking")):
                try:
                    prompt = transcribe(audio.getvalue())
                except AIError as e:
                    st.error(ai_msg(e))
    prompt = st.chat_input(t("tutor_ask")) or prompt
    if prompt:
        history = [{"role": m["role"], "content": m["content"]} for m in hist]
        with st.spinner(t("thinking")):
            try:
                answer = tutor_reply(d, history, prompt)
            except AIError as e:
                st.error(ai_msg(e))
                return
        for role, content in (("user", prompt), ("assistant", answer)):
            run("INSERT INTO ai_chats(user_id,doc_id,role,content,ts) VALUES(?,?,?,?,?)", (u["id"], d["id"], role, content, now()), write=True)
        log(u["id"], "tutor", d["title"])
        st.session_state.speak_new = True
        st.rerun()


def page_review(u):
    st.markdown(f"## {t('review')}")
    due = run("SELECT * FROM cards WHERE user_id=? AND due<=? ORDER BY due, id", (u["id"], today()))
    if not due:
        glass(f"✨ {t('done')}")
        return
    card = due[0]
    st.caption(f"{len(due)} {t('left')}")
    shown = st.session_state.get("rv_show", False)
    st.markdown(f"<div class='flash {'back' if shown else ''}'>{html.escape(card['back'] if shown else card['front'])}</div>", unsafe_allow_html=True)
    if not shown:
        if st.button(t("show_answer"), key="rv_reveal", type="primary", use_container_width=True):
            st.session_state.rv_show = True
            st.rerun()
        return
    for col, (label, q) in zip(st.columns(4), [(t("again"), 1), (t("hard"), 3), (t("good"), 4), (t("easy"), 5)]):
        if col.button(label, key=f"g{q}", use_container_width=True):
            rate_card(card, q)
            log(u["id"], "review")
            st.session_state.rv_show = False
            st.rerun()


# ───────────────────────────── Salons d'étude ─────────────────────────────
def message_bubble(m, uid):
    me = "me" if m["user_id"] == uid else ""
    return f"<div class='bubble {me}'><small>{html.escape(m['name'])} · {m['ts'][11:16]}</small><br>{html.escape(m['content'])}</div>"


@st.fragment(run_every=3)
def chat_feed(rid, uid):
    run("UPDATE users SET last_seen=? WHERE id=?", (now(), uid), write=True)
    msgs = run("SELECT m.user_id,m.content,m.ts,u.name FROM messages m JOIN users u ON u.id=m.user_id "
               "WHERE m.room_id=? ORDER BY m.id DESC LIMIT 80", (rid,))
    with st.container(height=420, border=True):
        if not msgs:
            st.caption(t("no_msg"))
        for m in reversed(msgs):
            st.markdown(message_bubble(m, uid), unsafe_allow_html=True)


def page_rooms(u):
    st.markdown(f"## {t('rooms')}")
    c1, c2 = st.columns(2)
    with c1, st.expander(f"➕ {t('create_room')}"):
        with st.form("new_room", clear_on_submit=True):
            name = st.text_input(t("room_name"))
            subj = st.text_input(t("room_subject"))
            lv = st.selectbox(t("room_level"), LEVELS, format_func=lambda k: t("lvl_" + k), index=LEVELS.index(level_of(u)))
            if st.form_submit_button(t("create_room"), use_container_width=True, type="primary") and name.strip():
                code = secrets.token_hex(3).upper()
                rid = run("INSERT INTO rooms(name,code,owner_id,created,subject,level) VALUES(?,?,?,?,?,?)",
                          (name.strip(), code, u["id"], now(), subj.strip(), lv), write=True)
                run("INSERT OR IGNORE INTO room_members VALUES(?,?)", (rid, u["id"]), write=True)
                log(u["id"], "room", name.strip())
                st.session_state.room = rid
                st.rerun()
    with c2, st.expander(f"🔑 {t('join_room')}"):
        with st.form("join_room", clear_on_submit=True):
            code = st.text_input(t("code"))
            if st.form_submit_button(t("join"), use_container_width=True):
                r = run("SELECT * FROM rooms WHERE code=?", (code.strip().upper(),), one=True)
                if r:
                    run("INSERT OR IGNORE INTO room_members VALUES(?,?)", (r["id"], u["id"]), write=True)
                    log(u["id"], "join", r["name"])
                    st.session_state.room = r["id"]
                    st.rerun()
                st.error(t("bad_code"))
    rooms = run("SELECT r.* FROM rooms r JOIN room_members m ON m.room_id=r.id WHERE m.user_id=? ORDER BY r.id DESC", (u["id"],))
    if not rooms:
        st.info(t("no_rooms"))
        return
    by_id = {r["id"]: r for r in rooms}
    ids = list(by_id)
    cur = st.session_state.get("room")
    rid = st.selectbox(t("my_rooms"), ids, index=ids.index(cur) if cur in ids else 0, format_func=lambda i: by_id[i]["name"])
    st.session_state.room = rid
    room = by_id[rid]
    tags = "".join(f"<span class='pill'>{html.escape(x)}</span>" for x in [room["subject"], t("lvl_" + room["level"]) if room["level"] in LEVELS else ""] if x)
    glass(f"<b>{html.escape(room['name'])}</b><br>{tags}<span class='pill'>{t('code')} : {room['code']}</span>")
    tc, ts, tm = st.tabs([t("tab_chat"), t("tab_shared"), t("tab_members")])
    with tc:
        st.markdown(f"<span class='live'>{t('room_live')}</span>", unsafe_allow_html=True)
        chat_feed(rid, u["id"])
        with st.form(f"send_{rid}", clear_on_submit=True):
            msg = st.text_input(t("message"), label_visibility="collapsed", placeholder=t("message"))
            if st.form_submit_button(t("send"), use_container_width=True, type="primary") and msg.strip():
                run("INSERT INTO messages(room_id,user_id,content,ts) VALUES(?,?,?,?)", (rid, u["id"], msg.strip()[:1000], now()), write=True)
                log(u["id"], "msg", room["name"])
                st.rerun()
    with ts:
        mine = run("SELECT id,title,subject,lang,content FROM documents WHERE user_id=? ORDER BY id DESC", (u["id"],))
        if mine:
            by_doc = {d["id"]: d for d in mine}
            sid = st.selectbox(t("share_course"), list(by_doc), format_func=lambda i: by_doc[i]["title"], key=f"sh_{rid}")
            if st.button(t("share"), key=f"share_{rid}", type="primary"):
                d = by_doc[sid]
                run("INSERT INTO room_docs(room_id,title,lang,content,subject,shared_by,ts) VALUES(?,?,?,?,?,?,?)",
                    (rid, d["title"], d["lang"], d["content"], d["subject"], u["id"], now()), write=True)
                st.rerun()
        shared = run("SELECT r.*,u.name FROM room_docs r JOIN users u ON u.id=r.shared_by WHERE r.room_id=? ORDER BY r.id DESC", (rid,))
        if not shared:
            st.info(t("no_shared"))
        for s in shared:
            a, b = st.columns([4, 1])
            with a:
                glass(f"📚 <b>{html.escape(s['title'])}</b><br><span class='pill'>{lname(s['lang'])}</span>"
                      f"<span class='muted'>{t('shared_by', name=html.escape(s['name']))}</span>")
            if b.button(t("add_mine"), key=f"adopt{s['id']}", use_container_width=True):
                save_doc(u["id"], s["title"], s["subject"], s["content"], "file")
                flash(t("saved"))
                st.rerun()
    with tm:
        members = run("SELECT u.name FROM room_members m JOIN users u ON u.id=m.user_id WHERE m.room_id=?", (rid,))
        st.markdown("".join(f"<span class='pill'>{html.escape(m['name'])}</span>" for m in members), unsafe_allow_html=True)
        if room["owner_id"] == u["id"]:
            if st.button(t("delete_room"), key="del_room"):
                delete_room(rid)
                st.session_state.pop("room", None)
                st.rerun()
        elif st.button(t("leave"), key="leave_room"):
            run("DELETE FROM room_members WHERE room_id=? AND user_id=?", (rid, u["id"]), write=True)
            st.session_state.pop("room", None)
            st.rerun()


def page_settings(u):
    st.markdown(f"## {t('settings')}")
    st.markdown(f"#### {t('profile')}")
    glass(f"<b>{html.escape(u['name'])}</b>")
    lang_picker("lang_settings")
    lv = st.selectbox(t("level"), LEVELS, format_func=lambda k: t("lvl_" + k), index=LEVELS.index(level_of(u)), key="set_level")
    st.caption(t("level_hint"))
    if lv != level_of(u):
        run("UPDATE users SET level=? WHERE id=?", (lv, u["id"]), write=True)
        st.rerun()
    with st.form("pwd", clear_on_submit=True):
        new = st.text_input(t("new_pwd"), type="password")
        if st.form_submit_button(t("update_pwd"), use_container_width=True):
            if len(new) < 6:
                st.error(t("pwd_short"))
            else:
                run("UPDATE users SET pwd=? WHERE id=?", (hash_pwd(new), u["id"]), write=True)
                st.success(t("pwd_ok"))
    cards = run("SELECT front,back,ef,interval,reps,due FROM cards WHERE user_id=?", (u["id"],))
    st.download_button(t("export"), json.dumps([dict(c) for c in cards], ensure_ascii=False, indent=2),
                       file_name="orich_cards.json", mime="application/json")
    st.markdown(f"#### {t('danger')}")
    ok = st.checkbox(t("confirm_del"), key="conf_del")
    if st.button(t("delete_acc"), key="del_acc", disabled=not ok):
        delete_user(u["id"])
        st.session_state.clear()
        st.rerun()


# ───────────────────────────── Console administrateur ─────────────────────────────
EV_ICON = {"register": "🆕", "login": "🔑", "doc": "📄", "scan": "📷", "summary": "📝", "cards": "🃏", "quiz": "🎯",
           "score": "🏆", "review": "🔁", "room": "🏫", "join": "🚪", "msg": "💬", "tutor": "🤖", "ai_error": "⚠️"}


@st.fragment(run_every=3)
def admin_live():
    if time.time() - st.session_state.get("admin_last", time.time()) > 1800:
        st.rerun()
    online_since = (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    q = lambda sql, a=(): run(sql, a, one=True)["c"]
    metrics = [(q("SELECT COUNT(*) c FROM users WHERE role!='admin'"), t("m_users")),
               (q("SELECT COUNT(*) c FROM users WHERE role!='admin' AND last_seen>=?", (online_since,)), t("m_online")),
               (q("SELECT COUNT(*) c FROM documents"), t("m_docs")),
               (q("SELECT COUNT(*) c FROM cards"), t("m_cards")),
               (q("SELECT COUNT(*) c FROM messages WHERE ts>=?", (today(),)), t("m_msgs"))]
    for col, (v, label) in zip(st.columns(5), metrics):
        with col:
            glass(f"<div class='stat'><b>{v}</b><span>{label}</span></div>")
    st.markdown(f"<span class='live'>{t('feed_title')}</span>", unsafe_allow_html=True)
    rows = run("SELECT a.action,a.detail,a.ts,u.name FROM activity a LEFT JOIN users u ON u.id=a.user_id WHERE a.action!='ai_call' ORDER BY a.id DESC LIMIT 40")
    with st.container(height=340, border=True):
        if not rows:
            st.caption(t("no_activity"))
        for r in rows:
            ev = t("ev_" + r["action"]) if ("ev_" + r["action"]) in TR else r["action"]
            det = f"<em>{html.escape(r['detail'])}</em>" if r["detail"] else ""
            st.markdown(f"<div class='feed-row'><span>{r['ts'][5:16]}</span>{EV_ICON.get(r['action'], '•')} "
                        f"<b>{html.escape(r['name'] or '?')}</b> {ev}{det}</div>", unsafe_allow_html=True)
    days = [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    counts = {r["d"]: r["n"] for r in run("SELECT substr(ts,1,10) d, COUNT(*) n FROM activity WHERE ts>=? AND action!='ai_call' GROUP BY d", (days[0],))}
    st.caption(t("chart_title"))
    st.bar_chart(pd.DataFrame({"events": [counts.get(d, 0) for d in days]}, index=[d[5:] for d in days]))


def admin_users():
    search = st.text_input(t("search"), key="adm_search").strip().lower()
    rows = run("SELECT u.id,u.name,u.level,u.status,u.created,u.last_seen,"
               "(SELECT COUNT(*) FROM documents d WHERE d.user_id=u.id) docs,(SELECT COUNT(*) FROM cards c WHERE c.user_id=u.id) cards "
               "FROM users u WHERE u.role!='admin' ORDER BY u.id DESC")
    rows = [r for r in rows if search in r["name"].lower()]
    if not rows:
        st.info(t("no_users"))
        return
    st.dataframe([{t("col_name"): r["name"], t("col_level"): t("lvl_" + r["level"]) if r["level"] in LEVELS else r["level"],
                   t("col_status"): t("st_blocked") if r["status"] == "blocked" else t("st_active"),
                   t("col_seen"): r["last_seen"] or "–", t("col_created"): (r["created"] or "")[:10],
                   t("col_docs"): r["docs"], t("col_cards"): r["cards"]} for r in rows], use_container_width=True, hide_index=True)
    by_id = {r["id"]: r for r in rows}
    picked = st.multiselect(t("select_users"), list(by_id), format_func=lambda i: f"{by_id[i]['name']} ({t('st_blocked') if by_id[i]['status'] == 'blocked' else t('st_active')})")
    c1, c2 = st.columns(2)
    if c1.button("🚫 " + t("block"), key="blk", disabled=not picked, use_container_width=True):
        for i in picked:
            run("UPDATE users SET status='blocked' WHERE id=? AND role!='admin'", (i,), write=True)
        flash(t("done_n", n=len(picked)))
        st.rerun()
    if c2.button("✅ " + t("unblock"), key="unblk", disabled=not picked, use_container_width=True):
        for i in picked:
            run("UPDATE users SET status='active' WHERE id=?", (i,), write=True)
        flash(t("done_n", n=len(picked)))
        st.rerun()
    ok = st.checkbox(t("confirm_bulk"), key="bulk_ok")
    if st.button("🗑️ " + t("del_sel"), key="bulk_del", disabled=not (picked and ok)):
        for i in picked:
            delete_user(i)
        flash(t("done_n", n=len(picked)))
        st.rerun()


def admin_rooms():
    rows = run("SELECT r.id,r.name,r.subject,r.code,u.name owner,(SELECT COUNT(*) FROM room_members m WHERE m.room_id=r.id) members,"
               "(SELECT COUNT(*) FROM messages g WHERE g.room_id=r.id) msgs FROM rooms r LEFT JOIN users u ON u.id=r.owner_id ORDER BY r.id DESC")
    if not rows:
        st.info(t("no_rooms"))
    for r in rows:
        a, b = st.columns([4, 1])
        with a:
            glass(f"<b>{html.escape(r['name'])}</b> <span class='pill'>{html.escape(r['subject'] or '-')}</span><br>"
                  f"<span class='muted'>{t('owner')} : {html.escape(r['owner'] or '?')} · {t('members')} : {r['members']} · 💬 {r['msgs']} · {r['code']}</span>")
        if b.button(t("delete"), key=f"adm_room{r['id']}", use_container_width=True):
            delete_room(r["id"])
            st.rerun()


def admin_ai():
    key = api_key()
    if key:
        st.markdown(f"<span class='pill'>{t('key_set', tail=key[-4:])}</span>", unsafe_allow_html=True)
        st.caption(t("key_from_secrets"))
    else:
        st.warning(t("key_need_secret"))
    with st.form("ai_form"):
        model = st.text_input(t("model_text"), value=get_setting("model"), placeholder=t("auto_model"))
        vision = st.text_input(t("model_vision"), value=get_setting("vision_model"), placeholder=t("auto_model"))
        st.caption(t("models_hint"))
        if st.form_submit_button(t("save"), use_container_width=True, type="primary"):
            set_setting("model", model.strip())
            set_setting("vision_model", vision.strip())
            set_setting("models_cache", "")
            flash(t("saved"))
            st.rerun()
    c1, c2 = st.columns(2)
    if c1.button(t("test_models"), key="test_ai", type="primary", use_container_width=True):
        with st.spinner(t("generating")):
            results = test_models()
        if not results:
            st.error(t("key_none"))
        for m, is_img, ok, detail in results:
            kind = t("img_kind") if is_img else t("txt_kind")
            st.markdown(f"{'✅' if ok else '❌'} `{m}` · {kind}" + (f" — {detail}" if detail else ""))
    if c2.button(t("refresh_models"), key="refresh_models", use_container_width=True):
        set_setting("models_cache", "")
        st.rerun()
    err = get_setting("last_ai_error")
    if err:
        st.caption(f"{t('ai_last_error')} : {err}")


def admin_account(u):
    if secret("ADMIN_PASSWORD"):
        st.info(t("admin_pwd_managed"))
        return
    with st.form("adm_pwd", clear_on_submit=True):
        cur = st.text_input(t("cur_pwd"), type="password")
        p1 = st.text_input(t("new_pwd"), type="password")
        p2 = st.text_input(t("confirm_pwd"), type="password")
        if st.form_submit_button(t("update_pwd"), use_container_width=True):
            row = run("SELECT pwd FROM users WHERE id=?", (u["id"],), one=True)
            if not check_pwd(cur, row["pwd"]):
                st.error(t("bad_login"))
            elif len(p1) < 12:
                st.error(t("admin_pwd_short"))
            elif p1 != p2:
                st.error(t("pwd_mismatch"))
            else:
                run("UPDATE users SET pwd=? WHERE id=?", (hash_pwd(p1), u["id"]), write=True)
                st.success(t("pwd_ok"))


def page_admin(u):
    st.markdown(f"## 🛡️ {t('admin_console')}")
    tl, tu, tr, ta, tc = st.tabs([t("ad_live"), t("ad_users"), t("ad_rooms"), t("ad_ai"), t("ad_account")])
    with tl:
        admin_live()
    with tu:
        admin_users()
    with tr:
        admin_rooms()
    with ta:
        admin_ai()
    with tc:
        admin_account(u)


# ───────────────────────────── Point d'entrée ─────────────────────────────
THEME_CONFIG = """[theme]
base = "dark"
primaryColor = "#8b6cff"
backgroundColor = "#080b16"
secondaryBackgroundColor = "#12162b"
textColor = "#e9ecff"
font = "sans serif"

[browser]
gatherUsageStats = false
"""


def ensure_theme_config():
    """Crée .streamlit/config.toml (thème sombre) au premier lancement ; actif après un redémarrage."""
    try:
        path = os.path.join(".streamlit", "config.toml")
        if not os.path.exists(path):
            os.makedirs(".streamlit", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(THEME_CONFIG)
    except Exception:
        pass


ADMIN_IDLE_SECONDS = 1800


def main():
    st.set_page_config(page_title="Orich'School", page_icon="🎓", layout="wide", initial_sidebar_state="auto")
    init_db()
    ensure_theme_config()
    st.session_state.setdefault("lang", "fr")
    st.markdown(CSS + uploader_css(), unsafe_allow_html=True)
    u = current_user()
    if not u:
        if admin_url_ok():
            page_admin_login()
        else:
            {"landing": page_landing, "auth": page_auth}.get(st.session_state.get("view", "landing"), page_landing)()
        return
    run("UPDATE users SET last_seen=? WHERE id=?", (now(), u["id"]), write=True)
    if st.session_state.get("flash"):
        st.success(st.session_state.pop("flash"))

    if u["role"] == "admin":
        if time.time() - st.session_state.get("admin_last", time.time()) > ADMIN_IDLE_SECONDS:
            st.session_state.clear()  # session administrateur expirée après 30 min d'inactivité
            st.rerun()
        st.session_state.admin_last = time.time()
        st.session_state.is_admin = True
        with st.sidebar:
            st.markdown("<span class='brand'>Orich'School</span>", unsafe_allow_html=True)
            st.caption(f"🛡️ {u['name']}")
            lang_picker("lang_side")
            if st.button(t("logout"), key="logout", use_container_width=True):
                st.session_state.clear()
                st.rerun()
        page_admin(u)
        return

    pages = {"home": ("🏠", page_home), "docs": ("📚", page_docs), "studio": ("✨", page_studio), "tutor": ("🤖", page_tutor),
             "review": ("🔁", page_review), "rooms": ("👥", page_rooms), "settings": ("⚙️", page_settings)}
    with st.sidebar:
        st.markdown("<span class='brand'>Orich'School</span>", unsafe_allow_html=True)
        page = st.radio("nav", list(pages), format_func=lambda k: f"{pages[k][0]}  {t(k)}", key="nav", label_visibility="collapsed")
        st.divider()
        lang_picker("lang_side")
        st.caption(u["name"])
        if st.button(t("logout"), key="logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    pages[page][1](u)


if __name__ == "__main__":
    main()
