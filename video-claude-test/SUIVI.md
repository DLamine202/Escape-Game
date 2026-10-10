# Pub test Claude : où on en est

## Règles du projet (demandées par l'utilisateur)
- Toujours rester sur les versions **gratuites** des applications et connecteurs, sauf abonnement déjà payé.
- Avant de produire une vidéo, **proposer d'abord** les voix, le design et le plan de montage, puis attendre la validation.
- Vidéo pour les réseaux sociaux : format vertical 9:16, sous-titres intégrés, musique douce et basse.

## Version 1 (terminée)
`livrable/pub_claude_test_9x16.mp4` : 45 s, voix ElevenLabs « Chloé », musique synthétisée.
Retours de l'utilisateur : musique trop forte et pas à son goût ; l'accroche doit nommer chaque tâche.

## Version 2 (terminée)
`livrable/pub_claude_v2_9x16.mp4` : 65 s, 1080×1920, 30 i/s.
- Voix : ElevenLabs « Chloe – Top France » (`eleven_multilingual_v2`), une seule prise (926 crédits de l'offre gratuite),
  accélérée ×1,1 sans changer la hauteur. Fichiers : `production/audio/voix_v2_brute.mp3` et `voix_v2_mots.json`
  (transcription horodatée mot par mot, ElevenLabs Scribe, gratuite).
- Audio : `production/audio2.py` recale les 36 phrases, règle les pauses (`PAUSES`, `PLAFOND`), compose le piano
  (`piano.composer`), baisse la musique sous la voix et normalise à −15 LUFS. Il écrit `timeline.json`.
- Image : `node render.js <debut> <fin> seg/pX.mp4` (rend `pub2.html` par défaut ; `PAGE=pub.html` pour la v1).
- L'API Gemini n'est plus nécessaire : la clé fournie était bloquée pour ce service (`API_KEY_SERVICE_BLOCKED`).

### Refaire la vidéo
```
cd production && python3 audio2.py
# 4 rendus en parallèle (nombre d'images = durée × 30), puis :
ffmpeg -f concat -safe 0 -i seg/liste.txt -i audio/mix_v2.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest ../livrable/pub_claude_v2_9x16.mp4
```

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
