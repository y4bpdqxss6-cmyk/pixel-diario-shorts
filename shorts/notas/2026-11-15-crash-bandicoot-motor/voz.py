import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Crash Bandicoot 2 se vuelve más fácil cada vez que mueres.",
    "No es tu imaginación: está en el código.",
    "Mueres varias veces en el mismo tramo… y reapareces con Aku Aku, la máscara protectora.",
    "Pero si sigues fallando, una caja cercana se vuelve punto de control.",
    "Y si una roca te aplasta demasiado, empieza a ir más lenta.",
    "¿Por qué? Naughty Dog quería ayudar a quien se atora,",
    "sin cambiar nada para los expertos.",
    "Por eso nunca te lo dijo.",
    "Así que si Crash 2 te pareció fácil… quizás morías más de lo que crees.",
]
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
sr = 24000
partes, tiempos, t = [], [], 0.25
partes.append(np.zeros(int(sr * 0.25), dtype=np.float32))
for i, l in enumerate(LINEAS):
    a, sr = k.create(l, voice=VOZ, speed=VEL, lang=VOZ_LANG)
    idx = np.where(np.abs(a) > 0.01)[0]
    a = a[max(idx[0] - 200, 0): idx[-1] + 1200]
    d = len(a) / sr
    tiempos.append({"i": i, "t0": t, "t1": t + d, "texto": l})
    pausa = (1.0 if i == 4 else 0.45 if i == 7 else (0.08 if i == 5 else 0.2)) if i < len(LINEAS) - 1 else 0.6
    partes += [a.astype(np.float32), np.zeros(int(sr * pausa), dtype=np.float32)]
    t += d + pausa
voz = np.concatenate(partes)
sf.write("voz.wav", voz, sr)
json.dump({"dur": len(voz) / sr, "lineas": tiempos}, open("tiempos.json", "w"), ensure_ascii=False, indent=1)
print(len(voz) / sr)
for x in tiempos: print(round(x["t0"], 2), round(x["t1"], 2), x["texto"])
