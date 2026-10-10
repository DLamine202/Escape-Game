# Pub test Claude : où on en est

## Règles du projet (demandées par l'utilisateur)
- Toujours rester sur les versions **gratuites** des applications et connecteurs, sauf abonnement déjà payé.
- Avant de produire une vidéo, **proposer d'abord** les voix, le design et le plan de montage, puis attendre la validation.
- Vidéo pour les réseaux sociaux : format vertical 9:16, sous-titres intégrés, musique douce et basse.

## Préférence de l'utilisateur
Après avoir vu la version longue, l'utilisateur préfère la **version 1, plus courte (environ 45 s)** : le format long est moins captivant.
Pour les prochaines vidéos, viser 40 à 50 s.

## Version 1 (terminée, préférée)
`livrable/pub_claude_test_9x16.mp4` : 45 s, voix ElevenLabs « Chloé », musique synthétisée.
Retours de l'utilisateur : musique trop forte et pas à son goût ; l'accroche doit nommer chaque tâche.

## Version 2 (validée, en cours)
- Script validé : voir `production/script_v2.txt`.
- Musique : option B, piano composé localement (`production/piano.py`, fonction `composer`).
- Animation : `production/pub2.html` (7 scènes). Elle attend un `timeline.json` avec 36 phrases canoniques (liste ci-dessous).
- Rendu : `production/render.js` (Playwright + ffmpeg). Pour la v2, il faut le faire pointer vers `pub2.html`.

**Bloquant** : ElevenLabs renvoie « 429 trop de demandes » sur la version gratuite.
Prochaine étape : générer la voix avec **Google AI Studio (API Gemini, synthèse vocale, offre gratuite)**,
avec une clé fournie dans la variable d'environnement `GEMINI_API_KEY`. Proposer 2 ou 3 voix françaises
à l'utilisateur avant la prise finale.

## Les 36 phrases canoniques (indices utilisés par pub2.html)
0 Combien de temps perdez-vous… · 1 pour refaire votre CV ? · 2 Pour répondre à ce mail… · 3 Pour comprendre un contrat…
4 Pour aider votre enfant avec ses devoirs… · 5 sans vous souvenir de la leçon ? · 6 Et chaque soir, pour savoir quoi cuisiner ?
7 Au total… · 8 près de six heures. · 9 Chaque semaine. · 10 Et si vous pouviez simplement… · 11 demander ?
12 Voici Claude. · 13 Vous lui parlez comme à une personne. · 14 Il vous répond comme un expert.
15 Votre CV ? · 16 Il le remet à jour en quelques minutes. · 17 Ce mail ? · 18 Dix secondes, c'est réglé.
19 Le contrat ? · 20 Il vous l'explique simplement, · 21 et vous signale les points à surveiller.
22 Les devoirs ? · 23 Il réexplique la leçon, avec patience. · 24 Le dîner ? · 25 Montrez-lui votre frigo.
26 Pas besoin d'être doué en informatique. · 27 Vous écrivez, · 28 ou vous parlez… · 29 et c'est tout.
30 Ces heures-là… · 31 redeviennent les vôtres. · 32 Claude. · 33 Vous demandez, · 34 il s'occupe du reste.
35 Essayez gratuitement, dès aujourd'hui.
