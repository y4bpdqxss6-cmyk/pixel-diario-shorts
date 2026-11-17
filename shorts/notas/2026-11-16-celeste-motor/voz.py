import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Celeste te deja saltar en el aire y nunca lo notaste.",
    "Corres, te pasas del borde… y aun así saltas.",
    "No es suerte: el juego te da un instante extra después de caer.",
    "Pero no es lo único.",
    "Si aprietas saltar un poquito antes de tocar el suelo, el juego lo guarda.",
    "Y si tu cabeza choca con una esquina por unos píxeles, te empuja para que pases.",
    "¿Por qué? Su creadora, Maddy Thorson, lo contó:",
    "son trucos escondidos para que un juego tan difícil se sienta justo.",
    "Así que ese salto imposible del que presumiste… Celeste te lo regaló en el aire.",
]
import sys
PAUSAS = {2: 0.35, 5: 0.6, 6: 0.15, 7: 0.45}
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
