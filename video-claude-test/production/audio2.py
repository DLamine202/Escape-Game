"""Piste audio de la pub v2 : voix off ElevenLabs recalée + piano composé localement.

Entrées : audio/voix_v2_brute.mp3 (prise unique) et audio/voix_v2_mots.json (transcription
horodatée mot par mot). Sorties : audio/mix_v2.wav et timeline.json (36 phrases canoniques
utilisées par pub2.html).
"""
import json
import re
import subprocess
import numpy as np
from piano import composer, SR, n

PHRASES = [
    "Combien de temps perdez-vous…", "pour refaire votre CV ?", "Pour répondre à ce mail que vous repoussez depuis trois jours ?",
    "Pour comprendre un contrat de quatorze pages ?", "Pour aider votre enfant avec ses devoirs…", "sans vous souvenir de la leçon ?",
    "Et chaque soir, pour savoir quoi cuisiner ?", "Au total…", "près de six heures.", "Chaque semaine.",
    "Et si vous pouviez simplement…", "demander ?", "Voici Claude.", "Vous lui parlez comme à une personne.",
    "Il vous répond comme un expert.", "Votre CV ?", "Il le remet à jour en quelques minutes.", "Ce mail ?",
    "Dix secondes, c'est réglé.", "Le contrat ?", "Il vous l'explique simplement,", "et vous signale les points à surveiller.",
    "Les devoirs ?", "Il réexplique la leçon, avec patience.", "Le dîner ?", "Montrez-lui votre frigo.",
    "Pas besoin d'être doué en informatique.", "Vous écrivez,", "ou vous parlez…", "et c'est tout.",
    "Ces heures-là…", "redeviennent les vôtres.", "Claude.", "Vous demandez,", "il s'occupe du reste.",
    "Essayez gratuitement, dès aujourd'hui.",
]
# Silence imposé AVANT certaines phrases (secondes) ; ailleurs, la pause d'origine plafonnée.
PAUSES = {7: 0.4, 10: 0.7, 12: 1.1, 15: 0.6, 17: 0.75, 19: 0.75, 22: 0.75, 24: 0.75,
          26: 0.5, 30: 0.6, 32: 0.7, 35: 0.3}
PLAFOND = 0.3
DEBUT, QUEUE = 0.4, 3.0
TEMPO = 1.1   # la prise est un peu lente pour une pub : accélération sans changer la hauteur


def lire(path, filtre="anull"):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af", filtre, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def ecrire(path, stereo):
    data = np.clip(stereo, -1, 1).astype(np.float32).T.copy()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", path],
                   input=data.tobytes(), check=True)


def est_mot(s):
    return re.search(r"\w", s) is not None


# ---------------------------------------------------------------- phrases → mots
mots = [w for w in json.load(open("audio/voix_v2_mots.json"))["words"] if w["type"] == "word" and est_mot(w["text"])]
bornes, i = [], 0
for ph in PHRASES:
    k = sum(est_mot(t) for t in ph.split())
    bloc = mots[i:i + k]
    attendu = [t for t in ph.split() if est_mot(t)]
    assert [b["text"].strip(",.…?") for b in bloc] == [a.strip(",.…?") for a in attendu], (ph, [b["text"] for b in bloc])
    bornes.append((bloc[0]["start"] / TEMPO, bloc[-1]["end"] / TEMPO))
    i += k
assert i == len(mots)

# ---------------------------------------------------------------- recalage de la voix
src = lire("audio/voix_v2_brute.mp3", f"atempo={TEMPO}")
duree_src = len(src) / SR
morceaux, phrases, t = [], [], DEBUT
for j, (s, e) in enumerate(bornes):
    avant = s - bornes[j - 1][1] if j else s
    apres = bornes[j + 1][0] - e if j + 1 < len(bornes) else duree_src - e
    pre, post = min(0.06, avant / 2), min(0.16, apres / 2)
    if j:
        t += PAUSES.get(j, min(avant, PLAFOND))
    morceau = src[n(s - pre):n(min(duree_src, e + post))].copy()
    f = n(0.015)
    morceau[:f] *= np.linspace(0, 1, f)
    morceau[-f:] *= np.linspace(1, 0, f)
    morceaux.append((t - pre, morceau))
    phrases.append({"t0": round(t, 3), "t1": round(t + e - s, 3), "texte": PHRASES[j]})
    t += e - s
DUREE = round(t + QUEUE, 2)

voix = np.zeros(n(DUREE))
for debut, m in morceaux:
    a = n(debut)
    voix[a:a + len(m)] += m[:len(voix) - a]

# ---------------------------------------------------------------- musique et mixage
P = phrases
musique = composer(DUREE, rupture=P[10]["t0"] - 0.3, revelation=P[12]["t0"] - 0.05,
                   benefice=P[30]["t0"] - 0.2, cta=P[32]["t0"] - 0.1)


def norm(x, crete):
    return x / (np.max(np.abs(x)) + 1e-9) * crete


voix = norm(voix, 0.9)
musique = norm(musique, 0.16)
# Ducking doux : la musique s'efface un peu sous la voix.
env = np.convolve(np.abs(voix), np.ones(n(0.3)) / n(0.3), mode="same")
musique *= 1 - 0.4 * np.clip(env / (np.percentile(env, 95) + 1e-9), 0, 1)

stereo = np.vstack([voix + musique, voix + np.roll(musique, 25)])
ecrire("audio/mix_v2_brut.wav", stereo)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "audio/mix_v2_brut.wav",
                "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-ar", str(SR), "audio/mix_v2.wav"], check=True)

json.dump({"duree": DUREE, "phrases": phrases}, open("timeline.json", "w"), ensure_ascii=False, indent=1)
print("ok", len(phrases), "phrases, durée", DUREE, "s")
