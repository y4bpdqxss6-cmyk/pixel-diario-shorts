import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Max Payne se vuelve más fácil cuando juegas mal, y no avisa.",
    "Es 2001, Remedy, y el modo normal parece un juego más.",
    "Te disparan, caes, vuelves a intentar… y algo empieza a cambiar.",
    "Pero no eres tú mejorando. Los enemigos fallan más y aguantan menos.",
    "Y eso no es lo más raro: si juegas muy bien, pasa lo contrario.",
    "¿Por qué? El juego mide cómo te va en cada nivel y ajusta lo que viene: más enemigos si vas sobrado, más ayuda si te cuesta.",
    "Así que si Max Payne te pareció fácil… quizás jugabas peor de lo que crees.",
]
# solo pronunciación (la pantalla muestra LINEAS tal cual; misma puntuación)
PRON = [("Max Payne", "Max Péin"), ("2001", "dos mil uno"), ("Remedy", "Rémedi")]
import sys
PAUSAS = {0: 0.45, 1: 0.4, 2: 0.4, 3: 0.4, 4: float(sys.argv[1]) if len(sys.argv) > 1 else 0.6, 5: 0.5}
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
    pausa = PAUSAS.get(i, 0.2) if i < len(LINEAS) - 1 else 0.6
    partes += [a.astype(np.float32), np.zeros(int(sr * pausa), dtype=np.float32)]
    t += d + pausa
voz = np.concatenate(partes)
sf.write("voz.wav", voz, sr)
json.dump({"dur": len(voz) / sr, "lineas": tiempos}, open("tiempos.json", "w"), ensure_ascii=False, indent=1)
print(len(voz) / sr, sum(len(x.split()) for x in LINEAS))
for x in tiempos: print(round(x["t0"], 2), round(x["t1"], 2), x["texto"])
