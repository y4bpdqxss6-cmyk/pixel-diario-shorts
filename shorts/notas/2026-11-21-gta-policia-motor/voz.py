import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "GTA existe porque la policía del juego se volvió loca.",
    "A mediados de los noventa, el juego ni siquiera se llamaba así: era Race'n'Chase.",
    "Carreras ilegales en una ciudad, y la policía persiguiéndote.",
    "Pero era aburrido y se trababa todo el tiempo.",
    "La editora estuvo a punto de cancelarlo.",
    "Pero un día, en una prueba, las patrullas dejaron de seguirte… y empezaron a embestirte.",
    "¿Qué pasó? Un error: no sabían rodear tu coche, así que intentaban pasar a través de él.",
    "Al equipo le encantó, y construyó todo el juego alrededor.",
    "Así que si una patrulla te choca en GTA… está repitiendo el error que salvó a la saga.",
]
# solo pronunciación (la pantalla muestra LINEAS tal cual; misma puntuación)
PRON = {"GTA": "Ge Te A", "Race'n'Chase": "Réis an Chéis"}
PAUSAS = {0: 0.45, 1: 0.35, 2: 0.2, 3: 0.4, 4: 0.55, 5: 0.5, 6: 0.3, 7: 0.55}
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
print(len(voz) / sr, sum(len(x.split()) for x in LINEAS))
for x in tiempos: print(round(x["t0"], 2), round(x["t1"], 2), x["texto"])
