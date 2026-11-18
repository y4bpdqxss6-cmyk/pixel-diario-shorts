import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Doom te deja vivo más tiempo cuando casi no tienes vida.",
    "En 2017, unos diseñadores de juegos lo contaron en Twitter.",
    "Tu barra de vida baja parejo… hasta que llega al final.",
    "Pero ese último pedacito aguanta más golpes de los que parece.",
    "Y no es solo Doom: Assassin's Creed hace lo mismo.",
    "¿Por qué?",
    "Para que cada escape se sienta heroico, como si te salvaras por un pelo.",
    "Así que la próxima vez que sobrevivas con un pelito de vida… Doom te dejó vivo.",
]
# solo pronunciación (la pantalla muestra LINEAS tal cual; misma puntuación)
PRON = {"Doom": "Dum", "Assassin's Creed": "Asásins Crid", "Twitter": "Tuíter"}
PAUSAS = {0: 0.4, 1: 0.3, 2: 0.3, 3: 0.5, 4: 0.6, 5: 0.75}
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
