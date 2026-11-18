import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Super Mario Bros. esconde arbustos en el cielo y nunca los viste.",
    "Es 1985, y todo el juego tiene que caber en un cartucho diminuto.",
    "Mira una nube. Ahora baja la mirada a los arbustos del suelo.",
    "Pero aquí viene lo raro: no se parecen… son el mismo dibujo.",
    "Solo cambia el color: blanco arriba, verde abajo.",
    "¿Por qué?",
    "El cartucho era tan chico que cada dibujo contaba, y con cuatro colores distintos, la misma pieza parecía otra cosa.",
    "Así que cada vez que saltas sobre un arbusto… también estás pisando una nube.",
]
# solo pronunciación (la pantalla muestra LINEAS tal cual; misma puntuación)
PRON = {"Super Mario Bros.": "Súper Mario Bros", "1985": "mil novecientos ochenta y cinco"}
PAUSAS = {0: 0.4, 1: 0.3, 2: 0.45, 3: 0.4, 4: 0.5, 5: 0.6}
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
sr = 24000
partes, tiempos, t = [np.zeros(int(sr * 0.25), dtype=np.float32)], [], 0.25
for i, l in enumerate(LINEAS):
    lv = l
    for a_, b_ in PRON.items(): lv = lv.replace(a_, b_)
    a, sr = k.create(lv, voice=VOZ, speed=VEL, lang=VOZ_LANG)
    idx = np.where(np.abs(a) > 0.01)[0]
    a = a[max(idx[0] - 200, 0): idx[-1] + 1200]
    d = len(a) / sr
    tiempos.append({"i": i, "t0": t, "t1": t + d, "texto": l})
    pausa = PAUSAS.get(i, 0.2) if i < len(LINEAS) - 1 else 0.6
    partes += [a.astype(np.float32), np.zeros(int(sr * pausa), dtype=np.float32)]
    t += d + pausa
voz = np.concatenate(partes)
sf.write("voz.wav", voz, sr)
json.dump({"dur": len(voz) / sr, "lineas": tiempos}, open("tiempos.json", "w"), ensure_ascii=False, indent=1)
print(len(voz) / sr)
for x in tiempos: print(round(x["t0"], 2), round(x["t1"], 2), x["texto"])
