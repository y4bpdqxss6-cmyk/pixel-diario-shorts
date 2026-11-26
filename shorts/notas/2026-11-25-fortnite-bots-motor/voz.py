import json, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Fortnite te llena la partida de bots si juegas mal.",
    "Pasó en 2019, con el Capítulo 2.",
    "Los primeros rivales que eliminas a veces no son personas… son la máquina.",
    "Pero nadie te avisa cuál es cuál.",
    "Y eso no es lo más raro: mientras mejor juegas, menos bots te tocan.",
    "¿Por qué? Epic quería que los nuevos no perdieran en el primer minuto y dejaran el juego.",
    "Así aprenden a construir y a apuntar.",
    "Así que si tu primera victoria en Fortnite fue fácil… quizás le ganaste a puros bots.",
]
# solo pronunciación (pantalla muestra LINEAS tal cual; misma puntuación)
PRON = [("Fortnite", "Fórtnait"), ("Epic", "Épic"), ("2019", "dos mil diecinueve"), ("Capítulo 2", "Capítulo dos")]
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
