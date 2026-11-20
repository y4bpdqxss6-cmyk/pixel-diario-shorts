import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Left 4 Dead te está vigilando mientras juegas, y no lo notas.",
    "Salió en 2008, y Valve escondió algo dentro: el Director.",
    "Mira qué tan nervioso estás, qué tanto fallas tus tiros y si ayudas a tu equipo.",
    "Pero no es para calificarte.",
    "Con eso decide dónde salen los zombis… y qué botiquines y armas encuentras.",
    "¿Por qué?",
    "Para que ninguna partida sea igual y nunca puedas aprenderte el mapa de memoria.",
    "Así que la próxima vez que sientas que alguien te mira… es Left 4 Dead.",
]
# solo pronunciación (la pantalla muestra LINEAS tal cual; misma puntuación)
PRON = {"Left 4 Dead": "Left For Ded", "2008": "dos mil ocho", "Valve": "Valv"}
PAUSAS = {0: 0.55, 1: 0.45, 2: 0.45, 3: 0.45, 4: 0.6, 5: 0.35, 6: 0.45}
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
