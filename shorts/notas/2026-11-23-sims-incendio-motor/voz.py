import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Los Sims existen porque a su creador se le quemó la casa.",
    "Es 1991 en Oakland, California, y Will Wright despierta oliendo a humo.",
    "Un incendio enorme baja por las colinas… y su casa no se salva.",
    "Pero lo raro no fue el incendio. Fue lo que vino después.",
    "Tuvo que comprar todo otra vez: muebles, platos, una cama, una tele.",
    "¿Y eso qué tiene que ver? Ahí pensó: reconstruir una vida, cosa por cosa, podía ser un juego. A los jefes no les gustó la idea.",
    "Pero salió en 2000. Así que cada casa que construyes en Los Sims… empezó con una casa quemada.",
]
# solo pronunciación (la pantalla muestra LINEAS tal cual; misma puntuación)
PRON = [("Will Wright", "Uil Ráit"), ("1991", "mil novecientos noventa y uno"), ("2000", "dos mil"), ("Oakland", "Óukland")]
import sys
PAUSAS = {0: 0.45, 1: 0.4, 2: 0.45, 3: 0.4, 4: float(sys.argv[1]) if len(sys.argv) > 1 else 0.6, 5: 0.5}
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
