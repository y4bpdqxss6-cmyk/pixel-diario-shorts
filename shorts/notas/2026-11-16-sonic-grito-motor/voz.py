import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Sonic gastó casi un octavo de su cartucho en una sola palabra.",
    "En 1991, cada pedacito de memoria valía oro.",
    "Ahí debían caber niveles, música y velocidad.",
    "Pero al prender la consola, lo primero que oyes es: ¡SE-GA!",
    "Casi un octavo del juego en dos sílabas. Y eso no es lo más raro.",
    "¿Por qué tanto? Ese espacio era para otra cosa.",
    "Una prueba de sonido: Sonic bailando breakdance con una banda de animales.",
    "No hubo tiempo y se quitó.",
    "Yuji Naka llenó el hueco con el grito de los comerciales.",
    "Así que esa palabra… ocupa el lugar de un baile que Sonic nunca hizo.",
]
PAUSAS = {3: 0.45, 4: 1.25, 6: 0.25, 7: 0.35}
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
sr = 24000
partes, tiempos, t = [np.zeros(int(sr * 0.25), dtype=np.float32)], [], 0.25
for i, l in enumerate(LINEAS):
    a, sr = k.create(l, voice=VOZ, speed=VEL, lang=VOZ_LANG)
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
