"""Motor de respaldo Pixel Diario — Short 'Mario Wii termina el nivel por ti'.
Serie: El juego te ayuda en secreto. Dibuja con cairo, sin personajes, bloques, control ni diseños de Nintendo:
figuras geométricas roja y verde, plataformas genéricas, control genérico, bloque verde liso con flecha, bandera simple.
"Mario", "Wii" y "Miyamoto" solo como texto. Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["MARIO JUEGA", "POR TI"], "resalta": "POR TI"}

# paleta nueva: día de plataformas, cielo turquesa + verde pasto + amarillo sol (antes: noche azul marino + sirenas)
CIELO1 = (0.16, 0.62, 0.86)
CIELO2 = (0.55, 0.86, 0.96)
PASTO = (0.30, 0.78, 0.30)
TIERRA = (0.62, 0.40, 0.22)
TIERRA2 = (0.50, 0.31, 0.17)
SOL = (1.0, 0.84, 0.15)
ROJO = (0.94, 0.22, 0.20)
VERDE = (0.20, 0.82, 0.35)
VERDEO = (0.08, 0.55, 0.22)
BLANCO = (1, 1, 1)
TINTA = (0.05, 0.06, 0.12)
GRIS = (0.55, 0.58, 0.64)
MORADO = (0.45, 0.30, 0.85)
ORO = (1.0, 0.76, 0.10)

RESALTA = {1: ["2009."], 2: ["vida,", "otra", "más…"], 3: ["ocho", "veces", "bloque", "verde."],
           4: ["jugar", "por", "ti."], 5: ["Pero", "trampa:", "no", "cuenta", "tuyo."], 6: ["¿Por", "qué", "existe?"],
           7: ["Miyamoto", "todos", "final,", "paciencia."], 8: ["atoraste", "terminarlo", "por", "ti."]}
COLRES = {1: SOL, 2: ROJO, 3: VERDE, 4: VERDE, 5: ROJO, 6: SOL, 7: SOL, 8: SOL}


def ease(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)


def back(x):
    x = max(0, min(1, x)); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def lerp(a, b, u): return a + (b - a) * u


def linea_en(t):
    for x in L:
        if t < x["t1"] + 0.18: return x["i"]
    return len(L) - 1


def local(i, t):
    a = L[i]["t0"]; b = L[i]["t1"]
    return max(0, min(1, (t - a) / (b - a)))


def font(cr, size):
    cr.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(size)


def texto(cr, s, x, y, size, color=BLANCO, centro=True, borde=8, alpha=1.0):
    font(cr, size)
    ext = cr.text_extents(s)
    if centro: x = x - ext.x_advance / 2
    cr.move_to(x, y); cr.text_path(s)
    if borde:
        cr.set_source_rgba(*TINTA, alpha); cr.set_line_width(borde); cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.stroke_preserve()
    cr.set_source_rgba(*color, alpha); cr.fill()
    return ext.x_advance


def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0); cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi); cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); cr.close_path()


def chipb(cr, s, x, y, color, size=34, txt=TINTA):
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: píldora redonda con borde blanco
    grueso y sombra dura (antes: cinta amarilla de escena con franjas)."""
    x = max(x, 340)
    font(cr, size); tw = cr.text_extents(s).x_advance; w = tw + 70; h = size + 34
    w = min(w, W - 20 - x)
    rrect(cr, x + 6, y + 8, w, h, h / 2); cr.set_source_rgba(0, 0, 0, 0.35); cr.fill()
    rrect(cr, x, y, w, h, h / 2); cr.set_source_rgb(*color); cr.fill_preserve()
    cr.set_source_rgb(*BLANCO); cr.set_line_width(6); cr.stroke()
    z = size
    while cr.text_extents(s).x_advance > w - 50: z -= 2; font(cr, z)
    cr.set_source_rgb(*txt); cr.move_to(x + 35, y + h / 2 + z * 0.36); cr.show_text(s)


def tarjeta(cr, s, x, y, size, color, esc=1.0, rot=0.0, fondo=BLANCO):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 70
    rrect(cr, -w / 2 + 10, -size * 0.95 + 12, w, size * 1.5, 22); cr.set_source_rgba(0, 0, 0, 0.35); cr.fill()
    rrect(cr, -w / 2, -size * 0.95, w, size * 1.5, 22); cr.set_source_rgb(*fondo); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 35, size * 0.25); cr.show_text(s)
    cr.restore()


def sello(cr, s, x, y, esc, rot, alfa=1.0, color=GRIS):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, 110); w = cr.text_extents(s).x_advance + 80
    rrect(cr, -w / 2, -90, w, 160, 18); cr.set_source_rgba(1, 1, 1, 0.75 * alfa); cr.fill()
    rrect(cr, -w / 2, -90, w, 160, 18); cr.set_source_rgba(*color, alfa); cr.set_line_width(14); cr.stroke()
    rrect(cr, -w / 2 + 16, -74, w - 32, 128, 10); cr.set_line_width(5); cr.stroke()
    cr.move_to(-w / 2 + 40, 28); cr.show_text(s)
    cr.restore()


def subtitulo(cr, i, t):
    s = L[i]["texto"]; pal = s.split(" ")
    u = (t - L[i]["t0"]) / (L[i]["t1"] - L[i]["t0"])
    total = sum(len(p) + 1 for p in pal); vis = u * total * 1.15
    size = 68; font(cr, size)
    lineas, act = [], []
    for p in pal:
        prueba = " ".join(act + [p])
        if cr.text_extents(prueba).x_advance > 960 and act: lineas.append(act); act = [p]
        else: act.append(p)
    lineas.append(act)
    y = 430 if len(lineas) <= 2 else 360
    acc = 0
    for ln in lineas:
        wtot = cr.text_extents(" ".join(ln)).x_advance; x = W / 2 - wtot / 2
        for p in ln:
            acc += len(p) + 1
            col = COLRES.get(i, SOL) if p in RESALTA.get(i, []) else BLANCO
            if acc > vis: col = (0.80, 0.88, 0.94)
            font(cr, size); adv = cr.text_extents(p + " ").x_advance
            cr.move_to(x, y); cr.text_path(p)
            cr.set_source_rgba(*TINTA, 1); cr.set_line_width(12); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve()
            cr.set_source_rgba(*col, 1); cr.fill()
            x += adv
        y += 88


# ---------- mundo genérico de plataformas visto de lado ----------
SUELO = 1560


def nube(cr, x, y, s):
    cr.set_source_rgba(1, 1, 1, 0.9)
    for dx, dy, r in [(-60, 10, 45), (0, -15, 60), (65, 8, 48), (20, 20, 50)]:
        cr.arc(x + dx * s, y + dy * s, r * s, 0, 2 * math.pi); cr.fill()


def plataforma(cr, x, y, w, h=60):
    cr.rectangle(x, y, w, h); cr.set_source_rgb(*TIERRA); cr.fill()
    for k in range(int(w // 60) + 1):
        cr.rectangle(x + k * 60 + 8, y + 26, 40, 8); cr.set_source_rgb(*TIERRA2); cr.fill()
    rrect(cr, x - 6, y - 18, w + 12, 30, 12); cr.set_source_rgb(*PASTO); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(4); cr.stroke()


def suelo(cr, t, hueco=None):
    """suelo de pasto en y SUELO; hueco=(x0,x1) deja un hoyo."""
    tramos = [(-200, W + 200)] if not hueco else [(-200, hueco[0]), (hueco[1], W + 200)]
    for a, b in tramos:
        plataforma(cr, a, SUELO, b - a, 300)


def figura(cr, x, y, t, color=ROJO, esc=1.0, rot=0.0, salto=0.0, ojos=True):
    """cuadrado genérico con ojos (personaje geométrico). y = pies."""
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc * (1 + 0.08 * salto), esc * (1 - 0.08 * salto))
    rrect(cr, -45 + 6, -96 + 8, 90, 90, 18); cr.set_source_rgba(0, 0, 0, 0.3); cr.fill()
    rrect(cr, -45, -96, 90, 90, 18); cr.set_source_rgb(*color); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()
    if ojos:
        for ox in (-14, 14):
            cr.arc(ox + 6, -60, 11, 0, 2 * math.pi); cr.set_source_rgb(1, 1, 1); cr.fill()
            cr.arc(ox + 9, -60, 5, 0, 2 * math.pi); cr.set_source_rgb(*TINTA); cr.fill()
    cr.restore()


def control(cr, x, y, esc, rot, t, solo=True):
    """control genérico: rectángulo redondo con cruz y dos botones; si solo=True los botones se presionan solos."""
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    rrect(cr, -170 + 8, -85 + 10, 340, 170, 70); cr.set_source_rgba(0, 0, 0, 0.3); cr.fill()
    rrect(cr, -170, -85, 340, 170, 70); cr.set_source_rgb(0.93, 0.93, 0.96); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
    cr.rectangle(-115, -15, 90, 30); cr.rectangle(-85, -45, 30, 90); cr.set_source_rgb(0.25, 0.27, 0.32); cr.fill()
    for k, (bx, by) in enumerate([(70, 15), (115, -25)]):
        p = solo and (math.sin(t * 9 + k * 2.2) > 0.3)
        cr.arc(bx, by + (5 if p else 0), 24, 0, 2 * math.pi); cr.set_source_rgb(*((0.9, 0.3, 0.3) if p else (0.45, 0.47, 0.55))); cr.fill()
    cr.restore()


def bloque(cr, x, y, esc=1.0, rot=0.0):
    """bloque verde liso con flecha blanca (no es el bloque del juego)."""
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    rrect(cr, -70 + 7, -70 + 9, 140, 140, 20); cr.set_source_rgba(0, 0, 0, 0.3); cr.fill()
    rrect(cr, -70, -70, 140, 140, 20); cr.set_source_rgb(*VERDE); cr.fill_preserve()
    cr.set_source_rgb(*VERDEO); cr.set_line_width(8); cr.stroke()
    cr.move_to(-35, -10); cr.line_to(10, -10); cr.line_to(10, -38); cr.line_to(45, 0); cr.line_to(10, 38); cr.line_to(10, 10)
    cr.line_to(-35, 10); cr.close_path(); cr.set_source_rgb(1, 1, 1); cr.fill()
    cr.restore()


def calavera(cr, x, y, r, col=BLANCO):
    cr.new_sub_path(); cr.arc(x, y, r, math.pi, 2 * math.pi); cr.line_to(x + r, y + r * 0.5); cr.line_to(x + r * 0.5, y + r * 0.9)
    cr.line_to(x - r * 0.5, y + r * 0.9); cr.line_to(x - r, y + r * 0.5); cr.close_path()
    cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(4); cr.stroke()
    for ox in (-0.38, 0.38):
        cr.arc(x + ox * r, y + r * 0.05, r * 0.25, 0, 2 * math.pi); cr.set_source_rgb(*TINTA); cr.fill()


def moneda(cr, x, y, t, alfa=1.0):
    w = abs(math.cos(t * 4 + x * 0.01)) * 34 + 6
    cr.save(); cr.translate(x, y); cr.scale(w / 40, 1)
    cr.arc(0, 0, 40, 0, 2 * math.pi); cr.set_source_rgba(*ORO, alfa); cr.fill_preserve()
    cr.set_source_rgba(*TINTA, alfa); cr.set_line_width(5); cr.stroke()
    cr.restore()


def bandera(cr, x, y, t):
    cr.rectangle(x - 8, y - 520, 16, 520); cr.set_source_rgb(0.85, 0.87, 0.9); cr.fill()
    cr.arc(x, y - 530, 22, 0, 2 * math.pi); cr.set_source_rgb(*SOL); cr.fill()
    ond = 14 * math.sin(t * 6)
    cr.move_to(x, y - 500); cr.curve_to(x + 80, y - 500 + ond, x + 120, y - 480 - ond, x + 170, y - 470)
    cr.line_to(x, y - 390); cr.close_path(); cr.set_source_rgb(*VERDE); cr.fill()


def tele(cr, x, y, esc):
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    rrect(cr, -260, -180, 520, 340, 30); cr.set_source_rgb(0.18, 0.18, 0.22); cr.fill()
    rrect(cr, -230, -155, 460, 290, 18); cr.set_source_rgb(0.08, 0.30, 0.45); cr.fill()
    cr.rectangle(-60, 160, 120, 30); cr.set_source_rgb(0.18, 0.18, 0.22); cr.fill()
    cr.restore()


def escena_a(cr, t, i):
    """inicio y cierre: la figura roja salta sola de plataforma en plataforma, el control genérico aprieta
    botones solo. Nada en y 300–820 (el texto del gancho va encima)."""
    off = (t * 120) % 360
    for k in range(-1, 5):
        plataforma(cr, 340 + k * 360 - off, 1320 - (k % 2) * 140, 220)
    suelo(cr, t)
    # salto automático entre plataformas
    p = (t * 120 / 360) % 1.0
    x = 560
    k0 = int(t * 120 / 360)
    yb = 1320 - (k0 % 2) * 140 - 18
    yn = 1320 - ((k0 + 1) % 2) * 140 - 18
    y = lerp(yb, yn, p) - 260 * math.sin(math.pi * p)
    figura(cr, x, y, t, ROJO, 1.1, rot=0.5 * math.sin(math.pi * p) * (1 if p < 0.5 else -0.3))
    control(cr, 860, 1010, 0.75, 0.12 * math.sin(t * 7), t)
    texto(cr, "SOLO", 860, 1145, 40, SOL, borde=7)


def escena(cr, t):
    i = linea_en(t)
    if i in (0, 8):
        escena_a(cr, t, i)
        return ("Mario Wii", SOL) if i == 0 else ("listo para terminarlo", SOL)
    u = local(i, t)
    if i == 1:
        suelo(cr, t)
        tele(cr, 690, lerp(1700, 1220, back(u * 3)), 1.0)
        tarjeta(cr, "WII · 2009", 690, 1230, 90, MORADO, esc=back((u - 0.15) * 4), rot=-0.04)
        figura(cr, 1000, SUELO - 18, t, ROJO, 0.8, salto=abs(math.sin(t * 6)))
        return "New Super Mario Bros. Wii", SOL
    if i == 2:
        suelo(cr, t, hueco=(620, 820))
        # cae en el hoyo dos veces
        v = (u * 2) % 1.0
        x = lerp(420, 720, min(1, v * 1.6))
        y = SUELO - 18 if v < 0.55 else SUELO - 18 + (v - 0.55) * 900
        figura(cr, x, y, t, ROJO, 1.0, rot=(v - 0.55) * 3 if v > 0.55 else 0)
        n = 2 if u < 0.5 else 3
        tarjeta(cr, f"VIDAS: {5 - (1 if u < 0.5 else 2)}", 760, 1020, 70, ROJO, esc=1.0, rot=0.03)
        for k in range(2 if u >= 0.5 else 1):
            calavera(cr, 760 + (k - 0.5 * (u >= 0.5)) * 110, 1160, 42)
        return "una vida… otra más", ROJO
    if i == 3:
        suelo(cr, t)
        cnt = min(8, 1 + int(u * 1.5 * 8))
        texto(cr, f"{cnt}/8", 690, 1080, 150, ROJO if cnt < 8 else SOL, borde=14)
        for k in range(8):
            cx = 400 + (k % 4) * 125; cy = 1180 + (k // 4) * 115
            calavera(cr, cx, cy, 40, BLANCO if k < cnt else (0.7, 0.75, 0.8))
        if u > 0.68:
            v = (u - 0.68) / 0.32
            bloque(cr, 900, lerp(860, 1250, back(v * 1.6)), 1.0, 0.1 * (1 - v))
            if v > 0.5: texto(cr, "¡NUEVO!", 900, 1380, 46, VERDE, borde=8)
        return ("8 veces seguidas" if u < 0.68 else "bloque verde"), VERDE
    if i == 4:
        suelo(cr, t)
        if u < 0.35:
            v = u / 0.35
            bloque(cr, 690, 1200 - (30 if v > 0.6 else 0), 1.0)
            figura(cr, 690, SUELO - 18 - 220 * math.sin(math.pi * min(1, v * 1.2)), t, ROJO, 1.0)
        else:
            v = (u - 0.35) / 0.65
            bloque(cr, 690, 1200, 0.8)
            # aparece la figura verde y avanza sola
            figura(cr, lerp(500, 980, v), SUELO - 18 - abs(math.sin(t * 7)) * 60, t, VERDE, 1.0, salto=abs(math.sin(t * 7)))
            control(cr, 640, 1010, 0.55, 0, t, solo=False)
            tarjeta(cr, "PILOTO AUTOMÁTICO", 690, 880, 52, VERDEO, esc=back(v * 4), rot=-0.03)
        return "la consola juega", VERDE
    if i == 5:
        suelo(cr, t)
        bandera(cr, 900, SUELO - 18, t)
        figura(cr, lerp(500, 820, ease(u * 2)), SUELO - 18, t, VERDE, 0.95)
        alf = 1 - ease((u - 0.45) * 3)
        for k in range(4):
            moneda(cr, 420 + k * 95, 1150 + 20 * math.sin(t * 3 + k), t, max(0.15, alf))
        if u > 0.25:
            sello(cr, "NO CUENTA", 690, 1290, back((u - 0.25) * 4) * 0.9, -0.1, 1.0, GRIS)
        return ("hay trampa" if u < 0.25 else "no cuenta"), ROJO
    if i == 6:
        suelo(cr, t)
        texto(cr, "¿?", 690, 1450, 460 * back(u * 3) + 1, SOL, borde=18)
        return "¿por qué?", SOL
    if i == 7:
        # camino largo con mucha gente geométrica avanzando; las que caen reciben una flecha que las empuja a la meta
        suelo(cr, t, hueco=(560, 700))
        bandera(cr, 1010, SUELO - 18, t)
        cols = [ROJO, VERDE, MORADO, (1.0, 0.55, 0.15), (0.2, 0.5, 0.95)]
        for k in range(6):
            ph = (t * 0.25 + k / 6) % 1.0
            x = lerp(330, 1000, ph)
            col = cols[k % 5]
            if k % 3 == 1 and 560 < x < 700:
                # cae un poco, la flecha la levanta
                y = SUELO - 18 + 60 * math.sin(math.pi * (x - 560) / 140)
                figura(cr, x, y, t, col, 0.6)
                cr.move_to(x - 25, y + 60); cr.line_to(x + 25, y + 60); cr.line_to(x, y + 10); cr.close_path()
                cr.set_source_rgb(*SOL); cr.fill()
            else:
                y = SUELO - 18 - abs(math.sin(t * 6 + k)) * 25
                figura(cr, x, y, t, col, 0.6)
        tarjeta(cr, "MIYAMOTO", 690, 960, 80, MORADO, esc=back(u * 5), rot=-0.03)
        if u > 0.45:
            tarjeta(cr, "TODOS AL FINAL", 690, 1130, 56, VERDEO, esc=back((u - 0.45) * 5), rot=0.03)
        return "que todos lleguen", SOL
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *CIELO1); g.add_color_stop_rgb(0.75, *CIELO2); g.add_color_stop_rgb(1, *CIELO2)
    cr.set_source(g); cr.paint()
    # sol con rayos girando
    cr.save(); cr.translate(930, 170); cr.rotate(t * 0.4)
    for k in range(12):
        cr.move_to(0, 0); cr.arc(0, 0, 260, k * math.pi / 6, k * math.pi / 6 + 0.13); cr.close_path()
        cr.set_source_rgba(1, 1, 1, 0.12); cr.fill()
    cr.restore()
    cr.arc(930, 170, 70, 0, 2 * math.pi); cr.set_source_rgb(*SOL); cr.fill()
    # nubes que pasan (fondo nuevo: cielo diurno con nubes, antes destellos de sirena)
    for k, (yy, s, v) in enumerate([(250, 0.9, 25), (520, 0.7, 40), (980, 0.8, 18), (1180, 0.6, 30)]):
        x = (k * 330 - t * v) % (W + 400) - 200
        nube(cr, x, yy, s)


def gancho(cr, t):
    # entrada nueva: texto completo desde el cuadro 0 sobre placas doradas; cada palabra rebota como si saltara
    # sola, con desfase (antes: placas rojo/azul de sirena con vaivén)
    ys = [600, 790]
    for k, (s, y) in enumerate(zip(GANCHO["lineas"], ys)):
        z = 170
        font(cr, z)
        while cr.text_extents(s).x_advance > 960: z -= 4; font(cr, z)
        wtot = cr.text_extents(s).x_advance
        x0 = W / 2 - wtot / 2
        rrect(cr, x0 - 34 + 8, y - z * 0.9 + 10, wtot + 68, z * 1.15, 30); cr.set_source_rgba(0, 0, 0, 0.35); cr.fill()
        rrect(cr, x0 - 34, y - z * 0.9, wtot + 68, z * 1.15, 30)
        cr.set_source_rgb(*(ORO if k == 0 else VERDEO)); cr.fill_preserve()
        cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
        x = x0
        for j, p in enumerate(s.split(" ")):
            font(cr, z)
            dy = -14 * abs(math.sin(t * 5 + j * 1.3 + k))
            col = SOL if GANCHO["resalta"] in s else BLANCO
            texto(cr, p, x, y + dy, z, col, centro=False, borde=24)
            font(cr, z); x += cr.text_extents(p + " ").x_advance


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: paneo lateral de juego de plataformas (deriva horizontal) con rebote vertical leve
    # al cambiar de toma (antes: cenital con giro)
    d = max(0, t - L[i]["t0"])
    zc = 1.0 + 0.05 * ease(d / 2.5)
    px = 30 * math.sin(t * 0.5)
    py = -18 * math.exp(-d * 6) * math.cos(d * 25)
    cr.save()
    cr.rectangle(0, 830, W, 470); cr.rectangle(320, 1300, W - 320, 360); cr.rectangle(0, 1660, W, 40); cr.clip()
    cr.translate(690 + px, 1250 + py); cr.scale(zc, zc); cr.translate(-690, -1250)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0 and t < L[0]["t1"] + 0.1:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1560, col if col else SOL, 40)
    chipb(cr, "El juego te ayuda en secreto", 340, 1745, VERDE, 34)
    cr.set_source_rgba(0, 0, 0, 0.25); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*SOL); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        dd = t - x["t0"]
        if 0 <= dd < 0.1:
            cr.set_source_rgba(1, 1, 1, 0.35 * (1 - dd / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0, 1.5] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [10.0, 12.0, 14.5, 18.5, 24.0, 26.5, round(L[-1]["t1"] - 0.3, 1)]
        for t in ts:
            cuadro(t).write_to_png(f"prueba/t{t:05.1f}.png")
    else:
        n = int(DUR * FPS)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-i", "mezcla.wav", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
                              "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", "short.mp4"], stdin=subprocess.PIPE)
        for f in range(n):
            p.stdin.write(bytes(cuadro(f / FPS).get_data()))
        p.stdin.close(); p.wait()
