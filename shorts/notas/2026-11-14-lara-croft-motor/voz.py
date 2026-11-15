import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Lara Croft, la heroína de Tomb Raider, iba a ser un hombre.",
    "A mediados de los noventa, Core Design inventa un explorador de tumbas.",
    "Un hombre que esquiva trampas en pirámides.",
    "Pero de pronto el hombre desaparece y llega una mujer.",
    "Y eso no es lo más raro: no se llamaba Lara.",
    "Era Laura Cruz, una aventurera sudamericana.",
    "Pero querían un nombre inglés… y lo sacaron de la guía telefónica.",
    "Así nació Lara Croft, aristócrata británica.",
    "¿Y por qué borraron al hombre? Se parecía demasiado a Indiana Jones.",
    "Y temían una demanda.",
    "Así que, sin Indiana Jones, Lara Croft seguiría siendo un hombre.",
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
