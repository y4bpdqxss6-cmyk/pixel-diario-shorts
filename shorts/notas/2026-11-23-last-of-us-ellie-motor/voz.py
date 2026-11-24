import json, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "The Last of Us vuelve invisible a Ellie y nunca lo notaste.",
    "Pasa cuando te escondes de los enemigos.",
    "Tú vas agachado, con cuidado… y ella corre detrás de ti, a plena vista.",
    "Pero nadie grita, nadie dispara. Es como si no existiera.",
    "Y eso no es lo más raro: solo pasa mientras no te descubren.",
    "¿Por qué?",
    "Naughty Dog no quería que tu compañera arruinara tu sigilo. Si la veían a ella, perdías tú.",
    "Así que la próxima vez que Ellie se te cruce frente a un enemigo… tranquilo, es invisible.",
]
# solo pronunciación (pantalla muestra LINEAS tal cual; misma puntuación)
PRON = [("The Last of Us", "De Last of As"), ("Naughty Dog", "Nóti Dog"), ("Ellie", "Éli")]
PAUSAS = {0: 0.45, 1: 0.45, 2: 0.5, 3: 0.6, 4: 0.8, 5: 0.5, 6: 0.55}
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
sr = 24000
partes, tiempos, t = [np.zeros(int(sr * 0.25), dtype=np.float32)], [], 0.25
for i, l in enumerate(LINEAS):
    lv = l
    for a_, b_ in PRON: lv = lv.replace(a_, b_)
    a, sr = k.create(lv, voice=VOZ, speed=VEL, lang=VOZ_LANG)
    idx = np.where(np.abs(a) > 0.01)[0]
    a = a[max(idx[0] - 200, 0): idx[-1] + 1200]
    d = len(a) / sr
    tiempos.append({"i": i, "t0": t, "t1": t + d, "texto": l})
    pausa = PAUSAS.get(i, 0.3) if i < len(LINEAS) - 1 else 0.6
    partes += [a.astype(np.float32), np.zeros(int(sr * pausa), dtype=np.float32)]
    t += d + pausa
voz = np.concatenate(partes)
sf.write("voz.wav", voz, sr)
json.dump({"dur": len(voz) / sr, "lineas": tiempos}, open("tiempos.json", "w"), ensure_ascii=False, indent=1)
print(len(voz) / sr, sum(len(x.split()) for x in LINEAS))
for x in tiempos: print(round(x["t0"], 2), round(x["t1"], 2), x["texto"])
