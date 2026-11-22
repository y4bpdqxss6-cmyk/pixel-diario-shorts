import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Mario Wii termina el nivel por ti si mueres mucho.",
    "Es New Super Mario Bros. Wii, de 2009.",
    "Pierdes una vida, otra más…",
    "y si fallas ocho veces seguidas en el mismo nivel, aparece un bloque verde.",
    "Lo golpeas, y la consola empieza a jugar por ti.",
    "Pero hay trampa: el nivel no cuenta como terminado, y lo que junta no es tuyo.",
    "¿Por qué existe?",
    "Miyamoto quería que todos llegaran al final, aunque no tuvieran la habilidad… o la paciencia.",
    "Así que si te atoraste en Mario Wii, el juego ya tenía a alguien listo para terminarlo por ti.",
]
# solo pronunciación (la pantalla muestra LINEAS tal cual; misma puntuación)
PRON = [("New Super Mario Bros.", "Niu Súper Mario Bros"), ("Wii", "Güi"), ("2009", "dos mil nueve")]
PAUSAS = {0: 0.45, 1: 0.35, 2: 0.15, 3: 0.35, 4: 0.4, 5: 0.5, 6: 0.35, 7: 0.55}
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
