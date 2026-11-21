"""Motor de respaldo Pixel Diario — Short 'Silent Hill da miedo por una consola débil'.
Dibuja con cairo, sin personajes, monstruos, logos ni diseños reconocibles: calle genérica de pueblo con casas y postes,
silueta borrosa genérica, consola genérica, botón, engrane, edificios grises simples. "Silent Hill", "PlayStation" y
"Konami" solo como texto. Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["LA NIEBLA", "ESCONDE ALGO"], "resalta": "NIEBLA"}

# paleta nueva: gris niebla + rojo óxido + blanco hueso (antes: morado arcade + magenta + cian + amarillo)
FONDO1 = (0.36, 0.37, 0.39)
FONDO2 = (0.10, 0.10, 0.12)
NIEBLA = (0.80, 0.81, 0.82)
OXIDO = (0.78, 0.26, 0.14)
OXIDO2 = (0.45, 0.13, 0.08)
HUESO = (0.96, 0.92, 0.82)
AMARILLO = HUESO
ROJO = (0.92, 0.22, 0.18)
CIAN = (0.70, 0.78, 0.80)
MAGENTA = OXIDO
BLANCO = (1, 1, 1)
TINTA = (0.05, 0.05, 0.06)
GRIS = (0.55, 0.56, 0.58)
CASA = (0.22, 0.22, 0.25)
CASA2 = (0.30, 0.29, 0.31)
PLANO1 = (0.85, 0.86, 0.88)
PLANO2 = (0.62, 0.64, 0.67)

RESALTA = {1: ["1999,", "PlayStation,", "niebla."], 2: ["pasos.", "mueve…", "qué."], 3: ["Pero", "asustar."],
           4: ["raro:", "problema."], 5: ["¿Cuál?", "lejos", "golpe."], 6: ["Konami", "niebla."],
           7: ["miedo", "mostrarte."]}
COLRES = {1: OXIDO, 2: HUESO, 3: OXIDO, 4: OXIDO, 5: HUESO, 6: OXIDO, 7: OXIDO}

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


def font(cr, size, bold=True):
    cr.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
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


def chipb(cr, s, x, y, color, size=34):
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: globo de cómic blanco con borde
    grueso y sombra sólida desplazada del color (antes: placa oscura con marco de cinta de advertencia)."""
    x = max(x, 340)
    font(cr, size); w = cr.text_extents(s).x_advance + 60; h = size + 36
    rrect(cr, x + 10, y + 10, w, h, h / 2); cr.set_source_rgb(*color); cr.fill()
    rrect(cr, x, y, w, h, h / 2); cr.set_source_rgb(*BLANCO); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()
    cr.set_source_rgb(*TINTA); cr.move_to(x + 30, y + size + 8); cr.show_text(s)


def tarjeta(cr, s, x, y, size, color, esc=1.0, rot=0.0, fondo=TINTA):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 70
    cr.rectangle(-w / 2 + 10, -size * 0.95 + 12, w, size * 1.5); cr.set_source_rgb(*color); cr.fill()
    cr.rectangle(-w / 2, -size * 0.95, w, size * 1.5); cr.set_source_rgb(*fondo); cr.fill_preserve()
    cr.set_source_rgb(*color); cr.set_line_width(6); cr.stroke()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 35, size * 0.25); cr.show_text(s)
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
    y = 420 if len(lineas) <= 2 else 350
    acc = 0
    for ln in lineas:
        wtot = cr.text_extents(" ".join(ln)).x_advance; x = W / 2 - wtot / 2
        for p in ln:
            acc += len(p) + 1
            col = COLRES.get(i, AMARILLO) if p in RESALTA.get(i, []) else BLANCO
            if acc > vis: col = (0.68, 0.62, 0.74)
            font(cr, size); adv = cr.text_extents(p + " ").x_advance
            cr.move_to(x, y); cr.text_path(p)
            cr.set_source_rgba(*TINTA, 1); cr.set_line_width(12); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve()
            cr.set_source_rgba(*col, 1); cr.fill()
            x += adv
        y += 88


def chipb(cr, s, x, y, color, size=34):
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: placa de metal oxidado con
    remaches y borde rojo óxido (antes: globo de cómic blanco con sombra de color)."""
    x = max(x, 340)
    font(cr, size); w = cr.text_extents(s).x_advance + 70; h = size + 34
    cr.rectangle(x, y, w, h); cr.set_source_rgb(0.16, 0.15, 0.15); cr.fill_preserve()
    cr.set_source_rgb(*color); cr.set_line_width(6); cr.stroke()
    for rx in (x + 14, x + w - 14):
        for ry in (y + 12, y + h - 12):
            cr.new_sub_path(); cr.arc(rx, ry, 5, 0, 2 * math.pi); cr.set_source_rgb(*GRIS); cr.fill()
    cr.set_source_rgb(*HUESO); cr.move_to(x + 35, y + size + 8); cr.show_text(s)


# ---------- dibujos genéricos ----------
VX, VY = 680, 1000  # punto de fuga de la calle


def calle(cr, t, claro=0.0, pop=None):
    """calle genérica en perspectiva desde y 830 hacia abajo. pop: lista de alfas de edificios lejanos (0..1)."""
    cr.move_to(VX - 30, VY); cr.line_to(VX + 30, VY); cr.line_to(W + 200, 1700); cr.line_to(140, 1700); cr.close_path()
    cr.set_source_rgb(0.18, 0.18, 0.20); cr.fill()
    # línea central discontinua que avanza
    for k in range(10):
        u = ((k / 10) + t * 0.12) % 1.0
        y0 = VY + (1700 - VY) * u ** 2; y1 = VY + (1700 - VY) * min(1, (u + 0.04)) ** 2
        cr.move_to(VX + (690 - VX) * 0 , y0); cr.line_to(VX, y1)
        cr.set_source_rgba(*HUESO, 0.6); cr.set_line_width(4 + 18 * u); cr.stroke()
    # casas a los lados (escalan con la distancia), techo siempre por debajo de y 830
    for lado in (-1, 1):
        for k in range(5):
            u = 0.25 + k * 0.17  # 0 lejos .. 1 cerca
            x = VX + lado * (60 + 560 * u ** 1.3)
            base = VY + 700 * u ** 1.6
            w_ = 60 + 260 * u; h_ = 60 + 260 * u
            top = max(840, base - h_)
            cr.rectangle(x - w_ / 2, top, w_, base - top)
            cr.set_source_rgb(*(CASA if k % 2 else CASA2)); cr.fill()
            cr.move_to(x - w_ / 2 - 10, top); cr.line_to(x, max(835, top - 0.35 * w_)); cr.line_to(x + w_ / 2 + 10, top)
            cr.close_path(); cr.set_source_rgb(*OXIDO2); cr.fill()
            cr.rectangle(x - w_ * 0.18, top + (base - top) * 0.3, w_ * 0.16, (base - top) * 0.22)
            cr.set_source_rgba(*HUESO, 0.25 + 0.15 * math.sin(t * 2 + k)); cr.fill()
    # postes
    for k in range(4):
        u = 0.3 + k * 0.22
        x = VX + (80 + 520 * u ** 1.3); base = VY + 700 * u ** 1.6; h_ = 100 + 280 * u
        top = max(840, base - h_)
        cr.set_source_rgb(0.12, 0.10, 0.10); cr.set_line_width(4 + 10 * u)
        cr.move_to(x, base); cr.line_to(x, top); cr.stroke()
        cr.move_to(x - 40 * u - 10, top + 12); cr.line_to(x + 40 * u + 10, top + 12); cr.stroke()
    if pop:
        for k, al in enumerate(pop):
            if al <= 0.01: continue
            x = VX - 230 + k * 115; w_ = 90; h_ = 90 + (k % 3) * 25
            cr.save(); cr.translate(x, VY); cr.scale(0.6 + 0.4 * al, 0.6 + 0.4 * al)
            cr.rectangle(-w_ / 2, -h_ + 120, w_, h_); cr.set_source_rgba(0.45, 0.46, 0.50, al); cr.fill_preserve()
            cr.set_source_rgba(*TINTA, al); cr.set_line_width(4); cr.stroke()
            cr.restore()


def silueta(cr, x, y, esc, alfa, t):
    """figura humana genérica borrosa (capas con alfa), sin rasgos."""
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    for k in range(4):
        a = alfa * (0.25 if k < 3 else 0.6); g = 18 - k * 6
        cr.set_source_rgba(0.08, 0.08, 0.09, a)
        cr.new_sub_path(); cr.arc(0, -210, 34 + g, 0, 2 * math.pi); cr.fill()
        rrect(cr, -48 - g, -170 - g / 2, 96 + 2 * g, 170 + g, 30); cr.fill()
        cr.rectangle(-36 - g / 2, 0, 28 + g, 140); cr.fill(); cr.rectangle(8 - g / 2, 0, 28 + g, 140 - 20 * math.sin(t * 4)); cr.fill()
    cr.restore()


def niebla(cr, t, dens=1.0, y0=820, y1=1700, vel=1.0, semilla=3):
    if dens <= 0.01: return
    rnd = random.Random(semilla)
    for k in range(16):
        cx = (rnd.uniform(-300, W + 300) + t * vel * rnd.uniform(20, 70)) % (W + 700) - 350
        cy = rnd.uniform(y0, y1); r = rnd.uniform(200, 420)
        g = cairo.RadialGradient(cx, cy, 10, cx, cy, r)
        g.add_color_stop_rgba(0, *NIEBLA, 0.42 * dens); g.add_color_stop_rgba(1, *NIEBLA, 0)
        cr.set_source(g); cr.arc(cx, cy, r, 0, 2 * math.pi); cr.fill()


def escena_a(cr, t, i):
    """imagen del inicio y del cierre: la calle tragada por niebla, una silueta borrosa cruza al fondo.
    Nada en y 300–820 (el texto del gancho va encima)."""
    calle(cr, t)
    sx = lerp(380, 980, ((t * 0.09) % 1.0))
    silueta(cr, sx, 1130, 0.55, 0.85, t)
    niebla(cr, t, 1.0, 880, 1650, vel=1.4)


def consola(cr, x, y, esc, t):
    """consola genérica: caja oscura con ranura, luz roja y un control con cable (sin forma de ninguna marca)."""
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    rrect(cr, -260, -90, 520, 180, 24); cr.set_source_rgb(0.30, 0.30, 0.33); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
    cr.rectangle(-200, -20, 260, 18); cr.set_source_rgb(*TINTA); cr.fill()
    cr.new_sub_path(); cr.arc(190, 30, 16, 0, 2 * math.pi); cr.set_source_rgb(*ROJO if math.sin(t * 5) > 0 else OXIDO2); cr.fill()
    cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.move_to(-240, 60); cr.curve_to(-340, 160, -200, 230, -120, 240); cr.stroke()
    rrect(cr, -150, 220, 200, 80, 30); cr.set_source_rgb(0.25, 0.25, 0.28); cr.fill()
    cr.restore()


def boton(cr, x, y, u, t):
    cr.save(); cr.translate(x, y); cr.rotate(0.03 * math.sin(t * 3))
    rrect(cr, -280, -110, 560, 220, 40); cr.set_source_rgb(0.20, 0.20, 0.22); cr.fill_preserve()
    cr.set_source_rgb(*OXIDO); cr.set_line_width(10); cr.stroke()
    texto(cr, "NIEBLA =", 0, -30, 70, HUESO, borde=8)
    if u < 0.5:
        texto(cr, "MIEDO", 0, 70, 90, BLANCO, borde=8)
        if u > 0.2:
            v = ease((u - 0.2) * 4)
            cr.move_to(-160, 40); cr.line_to(-160 + 320 * v, 40 - 40 * v); cr.set_source_rgb(*ROJO); cr.set_line_width(16); cr.stroke()
    else:
        texto(cr, "¿?", 0, 78, 110 * back((u - 0.5) * 4) + 1, OXIDO, borde=10)
    cr.restore()


def engrane(cr, x, y, r, rot, col=OXIDO):
    cr.save(); cr.translate(x, y); cr.rotate(rot)
    n = 10
    for k in range(n * 2):
        a0 = k * math.pi / n; rr = r if k % 2 == 0 else r * 0.8
        cr.arc(0, 0, rr, a0, a0 + math.pi / n)
    cr.close_path(); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
    cr.new_sub_path(); cr.arc(0, 0, r * 0.3, 0, 2 * math.pi); cr.set_source_rgb(*TINTA); cr.fill()
    cr.restore()


def vision(cr, x, y, r):
    """oscuridad con un círculo de visión pequeño"""
    cr.save(); cr.rectangle(0, 820, W, 900); cr.new_sub_path(); cr.arc(x, y, r, 0, 2 * math.pi)
    cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); cr.set_source_rgba(0, 0, 0, 0.82); cr.fill(); cr.restore()


def escena(cr, t):
    i = linea_en(t)
    if i in (0, 7):
        escena_a(cr, t, i)
        return ("SILENT HILL", OXIDO) if i == 0 else ("lo que no podía mostrar", OXIDO)
    u = local(i, t)
    if i == 1:
        consola(cr, 680, lerp(1700, 1200, back(u * 2.5)), 1.0, t)
        tarjeta(cr, "1999 · PLAYSTATION", 680, 900, 74, OXIDO, esc=back(u * 4), rot=-0.03, fondo=(0.14, 0.13, 0.13))
        # la niebla entra por los lados y cubre la consola
        v = ease((u - 0.35) * 1.8)
        for lado in (-1, 1):
            cx = W / 2 + lado * lerp(900, 250, v)
            g = cairo.RadialGradient(cx, 1250, 20, cx, 1250, 520)
            g.add_color_stop_rgba(0, *NIEBLA, 0.85 * v); g.add_color_stop_rgba(1, *NIEBLA, 0)
            cr.set_source(g); cr.arc(cx, 1250, 520, 0, 2 * math.pi); cr.fill()
        return ("1999" if u < 0.5 else "pueblo con niebla"), OXIDO
    if i == 2:
        calle(cr, t * 0.5)
        niebla(cr, t, 1.1, 900, 1600, vel=0.8, semilla=9)
        for k in range(3):
            sx = 400 + k * 200 + 80 * math.sin(t * 1.3 + k * 2)
            silueta(cr, sx, 1150 + k * 30, 0.4 + 0.05 * k, 0.5 + 0.3 * math.sin(t * 2 + k), t)
        vx = 680 + 120 * math.sin(t * 0.9)
        vision(cr, vx, 1180, lerp(380, 250, u))
        if math.sin(t * 7) > -0.2: texto(cr, "?", 880, 1050, 220, HUESO, borde=12)
        return "algo se mueve", HUESO
    if i == 3:
        niebla(cr, t, 0.8, 850, 1650, vel=1.0, semilla=5)
        sh = 18 * math.sin(t * 70) * max(0, 1 - abs(u - 0.5) * 8)
        cr.save(); cr.translate(sh, 0)
        boton(cr, 680, 1150, u, t)
        cr.restore()
        return "no solo para asustar", OXIDO
    if i == 4:
        niebla(cr, t, 1.0 - 0.5 * ease((u - 0.5) * 3), 850, 1650, vel=1.0, semilla=11)
        y = lerp(700, 1150, back(u * 2.2))
        engrane(cr, 680, y, 230, t * 0.8)
        tarjeta(cr, "PROBLEMA", 680, y + 10, 72, ROJO, esc=back((u - 0.35) * 4), rot=-0.08, fondo=HUESO)
        return "nació de un problema", ROJO
    if i == 5:
        if u < 0.12:
            niebla(cr, t, 1.0, 850, 1650, semilla=11)
            texto(cr, "¿?", 680, 1300, 420 * back(u * 9) + 1, OXIDO, borde=18)
            return "¿cuál?", OXIDO
        # sin niebla: calle vacía al fondo; los edificios lejanos aparecen de golpe con "¡POP!"
        v = (u - 0.12) / 0.88
        pops = [1.0 if v > 0.12 + k * 0.13 else 0.0 for k in range(5)]
        calle(cr, t, pop=pops)
        for k in range(5):
            d = v - (0.12 + k * 0.13)
            if 0 <= d < 0.1:
                texto(cr, "¡POP!", VX - 230 + k * 115, VY - 10, 64 * back(d * 20) + 1, ROJO, borde=10)
        if v < 0.12:
            tarjeta(cr, "SIN NIEBLA", 680, 1380, 64, OXIDO, esc=back(v * 12), rot=0.03, fondo=(0.14, 0.13, 0.13))
        return ("sin niebla" if v < 0.12 else "aparecen de golpe"), ROJO
    if i == 6:
        pops = [1.0] * 5
        calle(cr, t, pop=pops)
        niebla(cr, t, ease(u * 1.6) * 1.4, 830, 1700, vel=2.0, semilla=13)
        tarjeta(cr, "KONAMI", 680, 1150, 110, OXIDO, esc=back(u * 4), rot=-0.04, fondo=(0.14, 0.13, 0.13))
        return "lo tapó con niebla", OXIDO
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    if i == 5 and local(5, t) >= 0.12:
        # plano claro sin niebla (el cambio visual más fuerte)
        g.add_color_stop_rgb(0, *PLANO1); g.add_color_stop_rgb(0.52, *PLANO2); g.add_color_stop_rgb(1, 0.25, 0.25, 0.27)
        cr.set_source(g); cr.paint()
        return
    g.add_color_stop_rgb(0, *FONDO1); g.add_color_stop_rgb(1, *FONDO2)
    cr.set_source(g); cr.paint()
    # capas de niebla que se desplazan en el fondo (antes: puntos de trama que suben)
    for k in range(5):
        y = 250 + k * 330
        xo = (t * (15 + k * 8)) % W
        for dx in (-W, 0):
            gg = cairo.LinearGradient(0, y - 120, 0, y + 120)
            gg.add_color_stop_rgba(0, *NIEBLA, 0); gg.add_color_stop_rgba(0.5, *NIEBLA, 0.07); gg.add_color_stop_rgba(1, *NIEBLA, 0)
            cr.set_source(gg); cr.rectangle(xo + dx, y - 120, W, 240); cr.fill()


def gancho(cr, t):
    # entrada nueva: el texto ya está completo y legible en el cuadro 0; respira despacio (1.0 → 1.04) y una franja
    # de niebla le pasa por detrás (antes: cada línea "golpeaba" con pulso y sacudida)
    ys = [600, 780]
    for k, (s, y) in enumerate(zip(GANCHO["lineas"], ys)):
        z = 160
        font(cr, z)
        while cr.text_extents(s).x_advance > 990: z -= 4; font(cr, z)
        esc = 1.0 + 0.04 * math.sin(t * 1.6 + k)
        cr.save(); cr.translate(W / 2, y - z * 0.35); cr.scale(esc, esc)
        wtot = cr.text_extents(s).x_advance; x = -wtot / 2
        ini_res = s.find(GANCHO["resalta"]) if GANCHO["resalta"] in s else 99
        if ini_res < 99:
            xa = x + cr.text_extents(s[:ini_res]).x_advance
            texto(cr, s[:ini_res], x, z * 0.35, z, BLANCO, centro=False, borde=28)
            texto(cr, s[ini_res:], xa, z * 0.35, z, OXIDO if False else (1.0, 0.45, 0.30), centro=False, borde=28)
        else:
            texto(cr, s, x, z * 0.35, z, BLANCO, centro=False, borde=28)
        cr.restore()


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: acercamiento lento y continuo dentro de cada escena + deriva diagonal suave
    # (antes: golpe de zoom al entrar cada escena + deslizamiento lateral)
    d = max(0, t - L[i]["t0"])
    zc = 1.0 + 0.012 * d
    hx = 18 * math.sin(t * 0.4); hy = 10 * math.cos(t * 0.3)
    cr.save()
    cr.rectangle(0, 0, W, 1300); cr.rectangle(320, 1300, W - 320, 360); cr.rectangle(0, 1660, W, H - 1660); cr.clip()
    cr.translate(680 + hx, 1150 + hy); cr.scale(zc, zc); cr.translate(-680, -1150)
    eti, col = escena(cr, t)
    cr.restore()
    vg = cairo.RadialGradient(W / 2, 1050, 400, W / 2, 1050, 1200)
    vg.add_color_stop_rgba(0, 0, 0, 0, 0); vg.add_color_stop_rgba(1, 0, 0, 0, 0.5)
    cr.set_source(vg); cr.paint()
    if i == 0 and t < L[0]["t1"] + 0.1:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1560, col, 40)
    chipb(cr, "Secretos de videojuegos", 360, 1760, GRIS, 34)
    cr.set_source_rgba(0, 0, 0, 0.3); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*OXIDO); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        dd = t - x["t0"]
        if 0 <= dd < 0.12:
            cr.set_source_rgba(*NIEBLA, 0.4 * (1 - dd / 0.12)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0, 1.5] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [5.5, 8.0, 17.5, 20.5, 22.5, 24.5, 27.5, round(L[-1]["t1"] - 0.3, 1)]
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
