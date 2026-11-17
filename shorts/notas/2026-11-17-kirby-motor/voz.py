import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Kirby nunca debió existir: era un dibujo de relleno.",
    "En 1990, Masahiro Sakurai tenía diecinueve años y trabajaba en HAL.",
    "Estaba haciendo un juego, pero el protagonista de verdad no estaba listo.",
    "Así que dibujó lo más fácil del mundo: una bolita.",
    "Ni siquiera se llamaba Kirby: en el equipo le decían Popopo.",
    "Pero pasó algo raro.",
    "¿Por qué no lo cambiaron?",
    "Sakurai probó y decidió que esa bolita le servía mejor al personaje que cualquier diseño.",
    "Así que uno de los héroes más famosos de Nintendo… sigue siendo un dibujo de relleno.",
]
PAUSAS = {0: 0.3, 4: 0.3, 5: 0.6, 6: 0.25}
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
