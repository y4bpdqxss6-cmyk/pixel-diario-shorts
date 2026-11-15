import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Este Game Boy se quemó en una guerra y siguió prendiendo.",
    "Era de un médico militar en la guerra del Golfo.",
    "Su tienda de campaña se incendió… con el Game Boy adentro.",
    "El frente quedó negro y los botones, derretidos.",
    "Pero él no lo tiró: se lo mandó a Nintendo para pedir uno nuevo.",
    "Y aquí viene lo raro.",
    "Los técnicos le metieron un Tetris y lo encendieron.",
    "Y prendió. Hasta start y select funcionaban.",
    "Nintendo lo puso años en su tienda de Nueva York.",
    "Ahí estuvo, con Tetris prendido, hasta dos mil veintitrés.",
    "Tu control no aguanta una caída… y este Game Boy sobrevivió a una guerra.",
]
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
sr = 24000
partes, tiempos, t = [], [], 0.25
partes.append(np.zeros(int(sr * 0.25), dtype=np.float32))
for i, l in enumerate(LINEAS):
    a, sr = k.create(l.replace("«", "").replace("»", ""), voice=VOZ, speed=VEL, lang=VOZ_LANG)
    # recorta silencios
    idx = np.where(np.abs(a) > 0.01)[0]
    a = a[max(idx[0] - 200, 0): idx[-1] + 1200]
    d = len(a) / sr
    tiempos.append({"i": i, "t0": t, "t1": t + d, "texto": l})
    pausa = (0.45 if i in (4, 5) else 0.18) if i < len(LINEAS) - 1 else 0.6
    partes += [a.astype(np.float32), np.zeros(int(sr * pausa), dtype=np.float32)]
    t += d + pausa
voz = np.concatenate(partes)
sf.write("voz.wav", voz, sr)
json.dump({"dur": len(voz) / sr, "lineas": tiempos}, open("tiempos.json", "w"), ensure_ascii=False, indent=1)
print(len(voz) / sr)
for x in tiempos: print(round(x["t0"], 2), round(x["t1"], 2), x["texto"])
