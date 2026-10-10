"""Petit synthétiseur de piano et de nappes (numpy), pour la musique de la pub v2."""
import numpy as np

SR = 44100
_rng = np.random.default_rng(11)

NOMS = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
        "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}


def hz(nom):
    p, o = nom[:-1], int(nom[-1])
    return 440.0 * 2 ** ((NOMS[p] + 12 * (o + 1) - 69) / 12)


def n(t):
    return int(round(t * SR))


def piano(freq, duree, vel=0.6):
    """Note de piano : partiels légèrement inharmoniques, deux cordes désaccordées,
    décroissance plus rapide dans les aigus, attaque de marteau feutrée."""
    tt = np.arange(n(duree + 0.6)) / SR
    B = 0.00035
    tau0 = np.interp(np.log2(freq), [np.log2(60), np.log2(1500)], [4.5, 1.1])
    s = np.zeros_like(tt)
    for k in range(1, 11):
        fk = k * freq * np.sqrt(1 + B * k * k)
        if fk > 9000:
            break
        amp = (1 / k ** 1.25) * (vel ** (0.6 + 0.25 * k))   # nuance douce = moins d'aigus
        tau = tau0 / (1 + 0.55 * (k - 1))
        env = np.exp(-tt / tau)
        for d in (-0.0004, 0.0004):
            s += amp * env * np.sin(2 * np.pi * fk * (1 + d) * tt + _rng.uniform(0, 6.28)) * 0.5
    a = n(0.004)
    s[:a] *= np.linspace(0, 1, a)
    marteau = _rng.standard_normal(n(0.012)) * np.exp(-np.arange(n(0.012)) / (SR * 0.002))
    marteau = np.convolve(marteau, np.ones(12) / 12, mode="same")
    s[:len(marteau)] += marteau * 0.04 * vel
    fin = n(duree)
    rel = len(s) - fin
    s[fin:] *= np.linspace(1, 0, rel) ** 2     # étouffoir
    return s * vel


def nappe(freq, duree, gain=1.0):
    """Nappe très douce (cordes lointaines) : peu d'harmoniques, attaque et relâche lentes."""
    tt = np.arange(n(duree)) / SR
    s = np.zeros_like(tt)
    for d in (-0.003, 0.0, 0.003):
        for h, g in ((1, 1.0), (2, 0.35), (3, 0.12)):
            s += g * np.sin(2 * np.pi * freq * (1 + d) * h * tt + _rng.uniform(0, 6.28))
    vib = 1 + 0.15 * np.sin(2 * np.pi * 0.2 * tt)
    env = np.minimum(1, tt / 1.6) * np.minimum(1, (duree - tt) / 1.4).clip(0)
    return s * env * vib * gain / 3


def reverb(signal, duree=3.8, sec=0.5):
    ir_n = n(duree)
    ir = _rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / (SR * duree / 6.0))
    ir = np.convolve(ir, np.ones(30) / 30, mode="same")
    pre = np.zeros(n(0.025))
    ir = np.concatenate([pre, ir])
    ir /= np.sqrt(np.sum(ir ** 2))
    taille = 1 << int(np.ceil(np.log2(len(signal) + len(ir))))
    wet = np.fft.irfft(np.fft.rfft(signal, taille) * np.fft.rfft(ir, taille), taille)[:len(signal)]
    return sec * signal + (1 - sec) * wet * 0.5


def poser(piste, son, debut, gain=1.0):
    i = n(debut)
    if i >= len(piste):
        return
    j = min(len(piste), i + len(son))
    piste[i:j] += son[:j - i] * gain


def composer(duree, rupture, revelation, benefice, cta):
    """Musique de la pub. Les repères (en secondes) calent les sections sur la voix."""
    m = np.zeros(n(duree))
    pad = np.zeros(n(duree))
    temps = 60 / 84
    mesure = 4 * temps

    # 1. Accroche — ré mineur, clairsemé, mystérieux.
    HOOK = [("D2", ["D4", "E4", "A4", "F4"]), ("Bb1", ["D4", "F4", "A4", "C5"]),
            ("G1", ["D4", "Bb4", "F4", "A4"]), ("A1", ["E4", "G4", "D5", "C#5"])]
    t, k = 0.15, 0
    while t < rupture - 0.8:
        basse, haut = HOOK[k % 4]
        poser(m, piano(hz(basse), mesure, 0.42), t)
        poser(m, piano(hz(basse) * 2, mesure, 0.25), t)
        for i, nm in enumerate(haut):
            poser(m, piano(hz(nm), mesure - i * temps, 0.30 if i else 0.36), t + (i + 0.5) * temps)
        poser(pad, nappe(hz(basse) * 4, mesure + 0.6, 0.5), t)
        t += mesure
        k += 1

    # 2. Rupture — une seule note qui reste suspendue.
    poser(m, piano(hz("A5"), 2.5, 0.28), rupture + 0.2)
    poser(m, piano(hz("E5"), 2.5, 0.20), rupture + 0.2 + temps * 1.5)

    # 3. Révélation → démonstrations → rassurer — fa majeur, arpèges fluides.
    PROG = [("F2", ["F3", "C4", "E4", "A4"]), ("E2", ["C4", "G4", "C5", "E4"]),
            ("D2", ["A3", "D4", "F4", "C5"]), ("Bb1", ["F3", "D4", "A4", "C5"])]
    poser(m, piano(hz("F2"), 3, 0.5), revelation)
    for i, nm in enumerate(["C4", "F4", "A4", "E5"]):           # accord égrené
        poser(m, piano(hz(nm), 3, 0.38), revelation + 0.06 * i)
    t, k = revelation + mesure, 0
    while t < benefice - 0.3:
        basse, notes = PROG[k % 4]
        prog_v = min(1.0, 0.75 + 0.03 * k)
        poser(m, piano(hz(basse), mesure, 0.42 * prog_v), t)
        motif = [0, 1, 2, 3, 2, 1, 2, 3]
        for i, j in enumerate(motif):
            v = (0.30 if i % 2 == 0 else 0.22) * prog_v
            poser(m, piano(hz(notes[j]), temps * 1.6, v), t + i * temps / 2)
        poser(pad, nappe(hz(basse) * 4, mesure + 0.6, 0.45), t)
        t += mesure
        k += 1

    # 4. Bénéfice — montée lumineuse vers la résolution.
    for i, (basse, accord) in enumerate([("Bb1", ["D4", "F4", "Bb4", "C5"]), ("C2", ["E4", "G4", "C5", "D5"])]):
        tt = benefice + i * mesure * 0.75
        poser(m, piano(hz(basse), mesure, 0.45), tt)
        for j, nm in enumerate(accord):
            poser(m, piano(hz(nm), mesure, 0.32), tt + j * 0.09)
        poser(pad, nappe(hz(basse) * 4, mesure, 0.55), tt)

    # 5. Appel à l'action — Fa majeur 9, puis petit motif qui s'éteint.
    poser(m, piano(hz("F1"), 6, 0.5), cta)
    poser(m, piano(hz("F2"), 6, 0.4), cta)
    for j, nm in enumerate(["A3", "E4", "G4", "C5", "A5"]):
        poser(m, piano(hz(nm), 6, 0.34), cta + j * 0.07)
    for j, nm in enumerate(["C5", "A4", "G4", "F4"]):
        poser(m, piano(hz(nm), 3, 0.26), cta + 2.4 + j * temps)
    poser(pad, nappe(hz("F3"), duree - cta, 0.5), cta)
    poser(pad, nappe(hz("C4"), duree - cta, 0.35), cta)

    mix = reverb(m + pad * 0.35, duree=3.8, sec=0.55)
    f = n(1.2)
    mix[-f:] *= np.linspace(1, 0, f)
    return mix
