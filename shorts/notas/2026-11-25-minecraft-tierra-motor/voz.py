import json, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Minecraft tiene un mundo más grande que el planeta Tierra.",
    "Cada bloque mide un metro, y el borde está lejísimos.",
    "Treinta millones de bloques del centro a la orilla, en cada dirección.",
    "Pero eso es solo una línea. Ahora piensa en todo el cuadrado.",
    "Y eso no es lo más raro: casi nadie ha llegado al borde caminando.",
    "¿Cuánto mide? Unos 3,600 millones de kilómetros cuadrados.",
    "La Tierra entera tiene 510 millones: el mapa es unas siete veces más grande.",
    "Así que la próxima vez que te pierdas… acuérdate de que es más grande que el planeta.",
]
# solo pronunciación (pantalla muestra LINEAS tal cual; misma puntuación)
PRON = [("Minecraft", "Máincraft"), ("3,600", "tres mil seiscientos"), ("510", "quinientos diez")]
PAUSAS = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
PAUSAS = {int(k): v for k, v in PAUSAS.items()}
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
    pausa = PAUSAS.get(i, 0.4) if i < len(LINEAS) - 1 else 0.6
    partes += [a.astype(np.float32), np.zeros(int(sr * pausa), dtype=np.float32)]
    t += d + pausa
voz = np.concatenate(partes)
sf.write("voz.wav", voz, sr)
json.dump({"dur": len(voz) / sr, "lineas": tiempos}, open("tiempos.json", "w"), ensure_ascii=False, indent=1)
print(len(voz) / sr, sum(len(x.split()) for x in LINEAS))
for x in tiempos: print(round(x["t0"], 2), round(x["t1"], 2), x["texto"])
