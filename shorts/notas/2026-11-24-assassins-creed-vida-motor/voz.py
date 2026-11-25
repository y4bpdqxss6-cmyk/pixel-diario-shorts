import json, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Assassin's Creed te enseña menos vida de la que tienes.",
    "Lo contó una diseñadora en 2017, en un hilo de Twitter.",
    "Te pegan, la barra baja, y quedas con un pedacito rojo.",
    "Pero ese pedacito no es lo que parece: aguanta más golpes que el resto.",
    "Y no es el único: Doom hace lo mismo.",
    "¿Por qué? Para que sientas que sobreviviste de milagro.",
    "Si la barra dice quince por ciento… puede quedarte el doble.",
    "Así que esa última rayita roja… es la parte de tu vida que más miente.",
]
# solo pronunciación (pantalla muestra LINEAS tal cual; misma puntuación)
PRON = [("Assassin's Creed", "Asásins Crid"), ("2017", "dos mil diecisiete"), ("Doom", "Dum"), ("Twitter", "Tuíter")]
PAUSAS = {0: 0.55, 1: 0.5, 2: 0.6, 3: 0.9, 4: 1.25, 5: 0.5, 6: 0.6}
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
