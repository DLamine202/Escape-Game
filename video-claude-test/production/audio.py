"""Construit la piste audio de la pub : voix off recalée, musique et effets sonores.

Tout est synthétisé ici (numpy + ffmpeg), sans service payant.
Sortie : audio/mix.wav et timeline.json (utilisé par l'animation).
"""
import json
import subprocess
import numpy as np

SR = 44100
DUREE = 45.5
rng = np.random.default_rng(7)


def lire(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def ecrire(path, stereo):
    data = np.clip(stereo, -1, 1).astype(np.float32).T.copy()
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ac", "2", "-ar", str(SR), "-i", "-", path],
        input=data.tobytes(), check=True)


def n(t):
    return int(round(t * SR))


# ---------------------------------------------------------------- voix off
# Segments de parole détectés (ffmpeg silencedetect) dans la prise ElevenLabs.
SEGMENTS = [
    (0.00, 0.99, "Cette semaine…"),
    (1.50, 4.54, "combien d'heures avez-vous perdues, sur des choses qui vous épuisent ?"),
    (5.10, 6.88, "Et si vous pouviez simplement…"),
    (7.14, 7.71, "demander ?"),
    (8.29, 9.02, "Voici Claude."),
    (9.50, 11.10, "Vous lui parlez comme à une personne."),
    (11.47, 12.95, "Il vous répond comme un expert."),
    (13.48, 14.37, "Un mail difficile ?"),
    (14.73, 16.07, "Dix secondes, c'est réglé."),
    (16.52, 17.95, "Un contrat incompréhensible ?"),
    (18.33, 19.56, "Il vous l'explique simplement."),
    (19.99, 20.98, "Plus d'idée pour le dîner ?"),
    (21.40, 22.54, "Montrez-lui votre frigo."),
    (22.99, 24.77, "Pas besoin d'être doué en informatique."),
    (25.15, 25.88, "Vous écrivez,"),
    (26.13, 26.79, "ou vous parlez…"),
    (27.15, 27.60, "et c'est tout."),
    (28.05, 30.56, "Imaginez ce que vous ferez de tout ce temps retrouvé."),
    (31.07, 31.45, "Claude."),
    (31.77, 32.45, "Vous demandez,"),
    (32.71, 33.65, "il s'occupe du reste."),
    (34.06, 36.05, "Essayez gratuitement, dès aujourd'hui."),
]
# Blocs (premier segment, dernier segment, instant où la parole doit commencer).
BLOCS = [(0, 1, 0.6), (2, 3, 6.4), (4, 6, 10.2), (7, 8, 15.6), (9, 10, 19.7),
         (11, 12, 23.9), (13, 16, 27.9), (17, 17, 33.3), (18, 21, 37.2)]

voix_src = lire("audio/voix_brute.mp3")
voix = np.zeros(n(DUREE))
phrases = []
for a, b, cible in BLOCS:
    debut, fin = SEGMENTS[a][0], SEGMENTS[b][1]
    decal = cible - debut
    c0, c1 = max(0.0, debut - 0.10), min(len(voix_src) / SR, fin + 0.18)
    morceau = voix_src[n(c0):n(c1)].copy()
    f = n(0.02)
    morceau[:f] *= np.linspace(0, 1, f)
    morceau[-f:] *= np.linspace(1, 0, f)
    i = n(c0 + decal)
    voix[i:i + len(morceau)] += morceau
    for s in range(a, b + 1):
        d, e, txt = SEGMENTS[s]
        phrases.append({"t0": round(d + decal, 3), "t1": round(e + decal, 3), "texte": txt})

# ---------------------------------------------------------------- outils de synthèse
t = np.arange(n(DUREE)) / SR


def note(nom):
    noms = {"C": 0, "C#": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8,
            "A": 9, "Bb": 10, "B": 11}
    p, o = nom[:-1], int(nom[-1])
    return 440.0 * 2 ** ((noms[p] + 12 * (o + 1) - 69) / 12)


def enveloppe(longueur, att, rel):
    env = np.ones(longueur)
    a, r = min(n(att), longueur // 2), min(n(rel), longueur // 2)
    env[:a] = np.linspace(0, 1, a) ** 2
    env[-r:] *= np.linspace(1, 0, r) ** 2
    return env


def nappe(freq, duree, harmoniques=6, desaccord=0.004):
    tt = np.arange(n(duree)) / SR
    s = np.zeros_like(tt)
    for d in (-desaccord, 0, desaccord):
        for h in range(1, harmoniques + 1):
            s += np.sin(2 * np.pi * freq * (1 + d) * h * tt + rng.uniform(0, 6.28)) / (h ** 1.6)
    return s / 3


def reverb(signal, duree=3.2, sec=0.35):
    ir_n = n(duree)
    ir = rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / (SR * duree / 6.5))
    ir = np.convolve(ir, np.ones(24) / 24, mode="same")  # adoucit les aigus
    ir /= np.sqrt(np.sum(ir ** 2))
    taille = 1 << int(np.ceil(np.log2(len(signal) + ir_n)))
    wet = np.fft.irfft(np.fft.rfft(signal, taille) * np.fft.rfft(ir, taille), taille)[:len(signal)]
    return sec * signal + (1 - sec) * wet * 0.6


def poser(piste, son, debut, gain=1.0):
    i = n(debut)
    j = min(len(piste), i + len(son))
    if j > i:
        piste[i:j] += son[:j - i] * gain


# ---------------------------------------------------------------- musique
musique = np.zeros(n(DUREE))
# Accroche : bourdon grave mystérieux (ré mineur) + scintillement aigu.
for f, g in ((note("D2"), 0.55), (note("A2"), 0.35), (note("F3"), 0.18)):
    s = nappe(f, 9.4, harmoniques=5) * enveloppe(n(9.4), 1.8, 1.4)
    poser(musique, s, 0.0, g)
lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.3 * np.arange(n(9)) / SR)
poser(musique, np.sin(2 * np.pi * note("A5") * np.arange(n(9)) / SR) * lfo * enveloppe(n(9), 2, 2), 0.3, 0.05)

# Révélation puis progression chaude : Fmaj9 → Cadd9 → Dm9 → Bbmaj7 (cycles de 4 s).
ACCORDS = [["F2", "C3", "A3", "E4", "G4"], ["C2", "G2", "E3", "D4", "G4"],
           ["D2", "A2", "F3", "C4", "E4"], ["Bb1", "F2", "D3", "A3", "C4"]]
debut, k = 10.2, 0
while debut < DUREE - 0.5:
    d = min(4.3, DUREE - debut)
    for i_n, nm in enumerate(ACCORDS[k % 4]):
        g = 0.45 if i_n == 0 else 0.16
        poser(musique, nappe(note(nm), d, harmoniques=4 if i_n else 6) * enveloppe(n(d), 0.9, 1.2), debut, g)
    debut += 4.0
    k += 1

# Arpège doux (cloches) qui donne l'élan, à partir des démonstrations.
def cloche(freq, d=1.4):
    tt = np.arange(n(d)) / SR
    return (np.sin(2 * np.pi * freq * tt) + 0.3 * np.sin(2 * np.pi * freq * 2.01 * tt)) * np.exp(-tt * 4.2)


ARP = {0: ["F4", "A4", "C5", "E5"], 1: ["E4", "G4", "C5", "D5"], 2: ["D4", "F4", "A4", "C5"], 3: ["D4", "F4", "Bb4", "C5"]}
pas = 60 / 96 / 2
tt0 = 15.3
while tt0 < 44.0:
    k = int((tt0 - 10.2) // 4.0) % 4
    idx = int(round((tt0 - 15.3) / pas))
    if not (32.6 < tt0 < 33.3):
        vel = 0.10 if idx % 4 == 0 else 0.065
        if tt0 > 37.0:
            vel *= 0.8
        poser(musique, cloche(note(ARP[k][idx % 4])), tt0, vel)
    tt0 += pas

# Silence (presque) total au moment de la rupture « demander ? ».
courbe = np.interp(t, [0, 6.0, 7.0, 8.7, 9.9, 10.2, 44.3, DUREE],
                   [1, 1, 0.55, 0.10, 0.10, 1.0, 1.0, 0.0])
musique *= courbe
musique = reverb(musique, duree=3.5, sec=0.45)

# ---------------------------------------------------------------- effets sonores
sfx = np.zeros(n(DUREE))


def bruit_filtre(d, lo, hi):
    x = rng.standard_normal(n(d))
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    X[(fr < lo) | (fr > hi)] = 0
    return np.fft.irfft(X, len(x))


def whoosh(d=0.7):
    x = bruit_filtre(d, 300, 5000)
    env = np.sin(np.linspace(0, np.pi, len(x))) ** 3
    return x * env / np.max(np.abs(x * env))


def tic(f=2400, d=0.025):
    tt = np.arange(n(d)) / SR
    return np.sin(2 * np.pi * f * tt) * np.exp(-tt * 260)


def touche():
    x = bruit_filtre(0.03, 1500, 7000)
    return x * np.exp(-np.arange(len(x)) / (SR * 0.006)) / (np.max(np.abs(x)) + 1e-9)


def pop(f0=900, f1=520, d=0.09):
    tt = np.arange(n(d)) / SR
    f = np.linspace(f0, f1, len(tt))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 38)


def impact(d=2.5):
    tt = np.arange(n(d)) / SR
    return np.sin(2 * np.pi * 52 * tt * (1 - 0.15 * tt / d)) * np.exp(-tt * 2.2)


# Horloge qui s'accélère pendant l'accroche.
tt0, intervalle = 0.3, 0.5
while tt0 < 6.0:
    poser(sfx, tic(2600 if int(tt0 / intervalle) % 2 else 2000), tt0, 0.09)
    tt0 += intervalle
    intervalle = max(0.17, intervalle * 0.93)
for c in (0.25, 0.75, 1.25, 1.75, 2.25):           # cartes qui tombent
    poser(sfx, pop(500, 300, 0.12), c, 0.10)
poser(sfx, whoosh(0.9), 5.75, 0.10)                 # bascule vers la lumière
poser(sfx, impact(), 10.15, 0.55)                   # révélation de Claude
poser(sfx, whoosh(0.6), 14.85, 0.10)                # entrée dans le téléphone
for debut_demo in (15.35, 19.45, 23.65):            # frappe + bulles
    for i in range(14):
        poser(sfx, touche(), debut_demo + i * 0.055 + rng.uniform(0, 0.02), 0.05)
    poser(sfx, pop(), debut_demo + 0.95, 0.12)
    poser(sfx, pop(700, 980, 0.08), debut_demo + 1.6, 0.08)
poser(sfx, whoosh(0.6), 27.5, 0.10)
poser(sfx, whoosh(0.7), 32.85, 0.12)
poser(sfx, whoosh(0.8), 36.75, 0.13)
poser(sfx, impact(3.0), 37.15, 0.35)
poser(sfx, pop(880, 1320, 0.12), 40.0, 0.10)        # bouton « Essayer »
sfx = reverb(sfx, duree=1.6, sec=0.7)

# ---------------------------------------------------------------- mixage
def norm(x, crete):
    return x / (np.max(np.abs(x)) + 1e-9) * crete


voix = norm(voix, 0.9)
musique = norm(musique, 0.22)
sfx = norm(sfx, 0.24)

# Ducking : la musique baisse quand la voix parle.
env_v = np.convolve(np.abs(voix), np.ones(n(0.25)) / n(0.25), mode="same")
duck = 1 - 0.45 * np.clip(env_v / (np.percentile(env_v, 95) + 1e-9), 0, 1)
musique *= duck

g = musique + sfx
stereo = np.vstack([voix + g * 0.96, voix + np.roll(g, 22)])   # léger élargissement
fondu = n(0.4)
stereo[:, -fondu:] *= np.linspace(1, 0, fondu)
ecrire("audio/mix_brut.wav", stereo)
ecrire("audio/musique_seule.wav", np.vstack([musique + sfx, musique + sfx]))

json.dump({"duree": DUREE, "phrases": phrases}, open("timeline.json", "w"), ensure_ascii=False, indent=1)
print("ok", len(phrases), "phrases")
