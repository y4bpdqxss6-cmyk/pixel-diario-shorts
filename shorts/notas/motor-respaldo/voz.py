import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Cada fantasma te caza distinto.",
    "El rojo va directo a la casilla donde estás tú.",
    "El rosa no te sigue: apunta cuatro casillas delante de ti.",
    "Te quiere emboscar.",
    "El azul es el raro: calcula su objetivo usando al rojo y a ti.",
    "Por eso parece que se mueve al azar.",
    "Y el naranja te persigue… hasta que llega a ocho casillas.",
    "Ahí da la vuelta y huye a su esquina.",
    "En Japón le pusieron «el que se hace el tonto».",
    "Toru Iwatani los programó así para Pac-Man, en 1980.",
    "Y si miras hacia arriba, un error mueve el objetivo del rosa cuatro casillas a la izquierda.",
    "Así que la próxima vez que huyas, ya sabes quién te espera.",
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
    pausa = 0.18 if i < len(LINEAS) - 1 else 0.6
    partes += [a.astype(np.float32), np.zeros(int(sr * pausa), dtype=np.float32)]
    t += d + pausa
voz = np.concatenate(partes)
sf.write("voz.wav", voz, sr)
json.dump({"dur": len(voz) / sr, "lineas": tiempos}, open("tiempos.json", "w"), ensure_ascii=False, indent=1)
print(len(voz) / sr)
for x in tiempos: print(round(x["t0"], 2), round(x["t1"], 2), x["texto"])
