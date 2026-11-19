import json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

VOZ, VOZ_LANG, VEL = "em_alex", "es-419", 1.05
LINEAS = [
    "Metal Gear Solid tiene un jefe que revisa tus partidas guardadas.",
    "Es 1998, PlayStation, y aparece Psycho Mantis.",
    "Dice que puede leer tu mente… y entonces empieza a hablar de tus otros juegos.",
    "Pero no adivina nada. Si guardaste Castlevania en la misma tarjeta, te lo dice.",
    "Y si tu control vibra, te pide dejarlo en el suelo, y lo mueve solo.",
    "¿Cómo le ganas?",
    "Cambias el control al puerto dos. Ya no puede leer tus movimientos.",
    "Así que ese jefe no leía tu mente… leía tus partidas guardadas.",
]
# solo pronunciación (la pantalla muestra LINEAS tal cual; misma puntuación)
PRON = {"Metal Gear Solid": "Métal Guír Sólid", "1998": "mil novecientos noventa y ocho",
        "PlayStation": "Pléistéishon", "Psycho Mantis": "Sáico Mántis", "Castlevania": "Cáslvania"}
PAUSAS = {0: 0.4, 1: 0.3, 2: 0.35, 3: 0.35, 4: 0.45, 5: 0.35, 6: 0.5}
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
print(len(voz) / sr)
for x in tiempos: print(round(x["t0"], 2), round(x["t1"], 2), x["texto"])
