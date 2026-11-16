"""Motor de respaldo Pixel Diario — Short 'Crash Bandicoot 2 te ayuda si mueres'.
Dibuja con cairo, sin personajes, logos ni diseños reconocibles: figura geométrica naranja
genérica, escudo brillante genérico (no la máscara del juego), cajas de madera genéricas,
roca genérica, consola gris genérica. Nombres solo como texto. Zona de la mascota libre
(x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["MORIR", "LO HACE", "FÁCIL"], "resalta": "FÁCIL"}

# paleta: selva al anochecer, verde azulado profundo + violeta, acentos naranja/lima (antes: noche de campamento azul acero)
BG = (0.03, 0.09, 0.08)
BG2 = (0.16, 0.06, 0.2)
HOJA = (0.05, 0.2, 0.14)
AMA = (1.0, 0.85, 0.3)
NAR = (1.0, 0.52, 0.1)
ROJO = (1.0, 0.32, 0.3)
CIAN = (0.4, 0.9, 1.0)
LIMA = (0.7, 1.0, 0.35)
VIO = (0.78, 0.55, 1.0)
MADERA = (0.72, 0.48, 0.24)
PIEDRA = (0.55, 0.52, 0.5)
BLANCO = (1, 1, 1)
OSCURO = (0.02, 0.03, 0.03)

RESALTA = {1: ["código."], 2: ["varias", "veces", "Aku", "Aku,", "protectora."], 3: ["sigues", "fallando,", "punto", "control."],
           4: ["roca", "lenta."], 5: ["¿Por", "qué?", "ayudar", "atora,"], 6: ["nada", "expertos."], 7: ["nunca"],
           8: ["fácil…", "morías"]}
COLRES = {2: CIAN, 3: LIMA, 4: AMA, 5: NAR, 6: VIO, 7: ROJO, 8: NAR}
def ease(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)


def lerp(a, b, u): return a + (b - a) * u


def linea_en(t):
    for x in L:
        if t < x["t1"] + 0.18: return x["i"]
    return len(L) - 1


def local(i, t, i2=None):
    a = L[i]["t0"]; b = L[i2 if i2 is not None else i]["t1"]
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
        cr.set_source_rgba(*OSCURO, alpha); cr.set_line_width(borde); cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.stroke_preserve()
    cr.set_source_rgba(*color, alpha); cr.fill()
    return ext.x_advance


def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0); cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi); cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); cr.close_path()


def chipb(cr, s, x, y, color, size=34):
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: contorno grueso de color sobre relleno oscuro (antes: píldora rellena)."""
    x = max(x, 340)
    font(cr, size); w = cr.text_extents(s).x_advance + 56; h = size + 30
    rrect(cr, x, y, w, h, 12); cr.set_source_rgba(*OSCURO, 0.85); cr.fill_preserve()
    cr.set_source_rgb(*color); cr.set_line_width(5); cr.stroke()
    cr.move_to(x + 28, y + size + 8); cr.show_text(s)


# ---------- dibujos genéricos ----------
def figura(cr, x, y, t, color=NAR, esc=1.0, rot=0.0, escudo=0.0):
    """figura geométrica genérica (cuerpo redondeado + cabeza circular). Pies en (x,y)."""
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    if escudo > 0:
        for k in range(3):
            r = 150 + 18 * k + 8 * math.sin(t * 6 + k)
            cr.new_sub_path(); cr.arc(0, -120, r, 0, 2 * math.pi)
            cr.set_source_rgba(*CIAN, escudo * (0.28 - 0.08 * k)); cr.fill()
        cr.new_sub_path(); cr.arc(0, -120, 150 + 8 * math.sin(t * 6), 0, 2 * math.pi)
        cr.set_source_rgba(*CIAN, escudo * 0.9); cr.set_line_width(6); cr.stroke()
    bob = 4 * math.sin(t * 4)
    cr.set_source_rgb(*color)
    rrect(cr, -42, -150 + bob, 84, 115, 30); cr.fill()
    cr.new_sub_path(); cr.arc(0, -195 + bob, 38, 0, 2 * math.pi); cr.fill()
    cr.rectangle(-34, -40, 24, 40); cr.rectangle(10, -40, 24, 40); cr.fill()
    cr.set_source_rgb(*OSCURO)
    cr.new_sub_path(); cr.arc(-12, -198 + bob, 6, 0, 2 * math.pi); cr.arc(14, -198 + bob, 6, 0, 2 * math.pi); cr.fill()
    cr.restore()


def hoyo(cr, x, y, w):
    cr.save(); cr.translate(x, y); cr.scale(1, 0.28)
    cr.new_sub_path(); cr.arc(0, 0, w / 2, 0, 2 * math.pi); cr.set_source_rgb(0.0, 0.0, 0.0); cr.fill()
    cr.restore()
    cr.save(); cr.translate(x, y); cr.scale(1, 0.28)
    cr.new_sub_path(); cr.arc(0, 0, w / 2 + 10, 0, 2 * math.pi); cr.set_source_rgba(*LIMA, 0.6); cr.set_line_width(10); cr.stroke()
    cr.restore()


def suelo(cr, y=1290):
    cr.rectangle(0, y, W, H - y); cr.set_source_rgb(0.09, 0.16, 0.08); cr.fill()
    cr.rectangle(0, y, W, 14); cr.set_source_rgb(*tuple(c * 0.7 for c in LIMA)); cr.fill()


def vidas(cr, n, x, y, size=70, col=BLANCO):
    cr.new_sub_path(); cr.arc(x - 70, y - size * 0.35, size * 0.4, 0, 2 * math.pi); cr.set_source_rgb(*NAR); cr.fill()
    texto(cr, f"×{n}", x + 20, y, size, col, borde=8)


def calavera(cr, x, y, esc=1.0, alpha=1.0):
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    cr.new_sub_path(); cr.arc(0, 0, 60, math.pi, 2 * math.pi); cr.line_to(60, 30); cr.line_to(-60, 30); cr.close_path()
    cr.set_source_rgba(1, 1, 1, alpha); cr.fill()
    rrect(cr, -36, 20, 72, 40, 8); cr.fill()
    cr.set_source_rgba(*OSCURO, alpha)
    cr.new_sub_path(); cr.arc(-24, 0, 16, 0, 2 * math.pi); cr.arc(24, 0, 16, 0, 2 * math.pi); cr.fill()
    for dx in (-18, 0, 18): cr.rectangle(dx - 3, 40, 6, 20); cr.fill()
    cr.restore()


def caja(cr, x, y, s, rot=0.0, check=0.0, t=0.0):
    """caja de madera genérica que se convierte en caja con bandera."""
    cr.save(); cr.translate(x, y); cr.rotate(rot)
    col = tuple(lerp(a, b, check) for a, b in zip(MADERA, (0.3, 0.34, 0.4)))
    cr.rectangle(-s / 2, -s / 2, s, s); cr.set_source_rgb(*col); cr.fill()
    cr.set_source_rgb(*tuple(c * 0.6 for c in col)); cr.set_line_width(14)
    cr.rectangle(-s / 2 + 7, -s / 2 + 7, s - 14, s - 14); cr.stroke()
    cr.move_to(-s / 2 + 10, -s / 2 + 10); cr.line_to(s / 2 - 10, s / 2 - 10); cr.stroke()
    if check > 0.5:
        a = (check - 0.5) * 2
        cr.set_source_rgba(0.9, 0.9, 0.9, a); cr.rectangle(-8, -s / 2 - 150, 10, 150); cr.fill()
        ond = 10 * math.sin(t * 8)
        cr.move_to(2, -s / 2 - 150); cr.curve_to(50, -s / 2 - 160 + ond, 80, -s / 2 - 130 - ond, 120, -s / 2 - 140)
        cr.line_to(120, -s / 2 - 85); cr.curve_to(80, -s / 2 - 75 + ond, 50, -s / 2 - 105 - ond, 2, -s / 2 - 95); cr.close_path()
        cr.set_source_rgba(*LIMA, a); cr.fill()
    cr.restore()


def roca(cr, x, y, r, rot):
    cr.save(); cr.translate(x, y); cr.rotate(rot)
    cr.new_sub_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.set_source_rgb(*PIEDRA); cr.fill()
    cr.set_source_rgb(0.38, 0.36, 0.35)
    for (a, d, rr) in [(0.3, 0.5, 0.18), (2.2, 0.45, 0.22), (4.1, 0.55, 0.15), (5.3, 0.2, 0.12)]:
        cr.new_sub_path(); cr.arc(d * r * math.cos(a), d * r * math.sin(a), rr * r, 0, 2 * math.pi); cr.fill()
    cr.restore()


def velocimetro(cr, x, y, r, v):
    cr.set_line_width(18)
    cr.set_source_rgb(0.2, 0.25, 0.25); cr.arc(x, y, r, math.pi, 2 * math.pi); cr.stroke()
    cr.set_source_rgb(*ROJO); cr.arc(x, y, r, math.pi * 1.7, 2 * math.pi); cr.stroke()
    a = math.pi + v * math.pi
    cr.set_source_rgb(*BLANCO); cr.set_line_width(10)
    cr.move_to(x, y); cr.line_to(x + (r - 20) * math.cos(a), y + (r - 20) * math.sin(a)); cr.stroke()
    cr.new_sub_path(); cr.arc(x, y, 16, 0, 2 * math.pi); cr.fill()


def consola_gris(cr, x, y, esc):
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    rrect(cr, -260, -90, 520, 180, 20); cr.set_source_rgb(0.72, 0.72, 0.74); cr.fill()
    rrect(cr, -200, -60, 400, 50, 10); cr.set_source_rgb(0.55, 0.55, 0.58); cr.fill()
    for bx in (-200, -120): cr.new_sub_path(); cr.arc(bx, 40, 22, 0, 2 * math.pi); cr.set_source_rgb(0.45, 0.45, 0.48); cr.fill()
    cr.rectangle(120, 30, 90, 16); cr.set_source_rgb(*LIMA); cr.fill()
    cr.restore()


def lluvia_codigo(cr, t, x0, x1, y0, y1, alpha=0.8):
    rnd = random.Random(8); font(cr, 30, False)
    for k in range(26):
        x = rnd.uniform(x0, x1); sp = rnd.uniform(120, 260)
        y = y0 + ((t * sp + rnd.uniform(0, 600)) % (y1 - y0))
        cr.set_source_rgba(*LIMA, alpha * rnd.uniform(0.35, 0.9))
        cr.move_to(x, y); cr.show_text(rnd.choice(["if", "0x1F", "die++", "{ }", "==", "lvl", "help()", "01"]))


def tarjeta(cr, s, x, y, size, color, esc=1.0, rot=0.0):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 60
    rrect(cr, -w / 2, -size * 0.95, w, size * 1.5, 14); cr.set_source_rgb(*BLANCO); cr.fill()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 30, size * 0.25); cr.show_text(s)
    cr.restore()


def candado(cr, x, y, esc, cerrado):
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    cr.set_source_rgb(*AMA); cr.set_line_width(34)
    sube = 70 * (1 - cerrado)
    cr.arc(0, -80 - sube, 90, math.pi, 2 * math.pi); cr.line_to(90, -40 - sube); cr.stroke()
    cr.move_to(-90, -80 - sube); cr.line_to(-90, -20); cr.stroke()
    rrect(cr, -150, -60, 300, 230, 26); cr.fill()
    cr.set_source_rgb(*OSCURO); cr.new_sub_path(); cr.arc(0, 30, 26, 0, 2 * math.pi); cr.fill(); cr.rectangle(-10, 30, 20, 70); cr.fill()
    cr.restore()


def escena_a(cr, t):
    """imagen del inicio y del cierre: figura naranja cayendo en un hoyo, contador de vidas bajando"""
    suelo(cr)
    hoyo(cr, 600, 1300, 300)
    ciclo = (t % 1.6) / 1.6
    if ciclo < 0.45:
        u = ciclo / 0.45
        figura(cr, lerp(360, 600, u), 1290 - 160 * math.sin(math.pi * min(u * 1.3, 1)), t, NAR, 0.9, rot=0.3 * u)
    else:
        u = (ciclo - 0.45) / 0.55
        cr.save(); cr.rectangle(0, 0, W, 1300); cr.clip()
        figura(cr, 600, 1290 + 420 * ease(u), t, NAR, 0.9 * (1 - 0.3 * u), rot=0.3 + 2 * u)
        cr.restore()
    n = 5 - int(t / 1.6) % 4
    vidas(cr, n, 860, 920)


def escena(cr, t):
    i = linea_en(t)
    if t < L[1]["t0"] or i == 8:
        escena_a(cr, t)
        return ("Crash Bandicoot 2", NAR) if i == 0 else ("¿morías más?", NAR)
    if i == 1:
        u = local(1, t)
        lluvia_codigo(cr, t, 120, 980, 860, 1290)
        consola_gris(cr, 540, 1160 + 10 * math.sin(t * 3), 0.9 + 0.1 * ease(u))
        tarjeta(cr, "PlayStation · 1997", 540, 960, 56, (0.15, 0.2, 0.3), esc=ease(u * 3), rot=-0.03)
        return "está en el código", LIMA
    if i == 2:
        u = local(2, t)
        suelo(cr)
        for k in range(3):
            a = ease((u - k * 0.12) * 5) * (1 - ease((u - 0.5) * 6))
            if a > 0: calavera(cr, 330 + k * 210, 1000, 0.9 * a + 0.1, a)
        if u > 0.5:
            e = ease((u - 0.5) * 3)
            figura(cr, 540, 1290, t, NAR, 0.95, escudo=e)
            texto(cr, "AKU AKU", 540, 940, 90 * e + 1, CIAN, borde=10)
        return "3 vidas perdidas → escudo", CIAN
    if i == 3:
        u = local(3, t)
        suelo(cr)
        c = ease((u - 0.35) * 3)
        caja(cr, 540, 1180, 220 * (1 + 0.12 * math.sin(math.pi * c)), rot=c * 2 * math.pi, check=c, t=t)
        figura(cr, 260 + 30 * math.sin(t * 2), 1290, t, NAR, 0.75)
        if c > 0.9:
            texto(cr, "CHECKPOINT", 540, 930, 84, LIMA, borde=10)
            cr.set_source_rgba(1, 1, 0.8, 0.5 * (1 - ease((u - 0.68) * 5))); cr.new_sub_path(); cr.arc(540, 1180, 260, 0, 2 * math.pi); cr.fill()
        return "caja → punto de control", LIMA
    if i == 4:
        u = local(4, t)
        suelo(cr)
        lenta = ease((u - 0.4) * 2.5)
        vel = 1.0 - 0.65 * lenta
        x = 1250 - ((t * 420 * vel) % 1500)
        roca(cr, x, 1150, 140, -t * 3 * vel)
        figura(cr, 300, 1290, t, NAR, 0.75)
        velocimetro(cr, 760, 1000, 110, 0.9 - 0.6 * lenta)
        if lenta > 0.2:
            cr.set_source_rgba(*VIO, 0.12 * lenta); cr.rectangle(0, 860, W, 440); cr.fill()
        return "roca más lenta", AMA
    if i == 5:
        u = local(5, t)
        texto(cr, "¿?", 540, 1140, 300 + 25 * math.sin(t * 7), NAR, borde=12)
        tarjeta(cr, "NAUGHTY DOG", 540, 1260, 60, (0.15, 0.2, 0.3), esc=ease((u - 0.3) * 3))
        return "el porqué", NAR
    if i == 6:
        u = local(6, t)
        off = 600 * (1 - ease(u * 3))
        cr.rectangle(0 - off, 860, W / 2 - 6, 440); cr.set_source_rgba(*ROJO, 0.18); cr.fill()
        cr.rectangle(W / 2 + 6 + off, 860, W / 2 - 6, 440); cr.set_source_rgba(*LIMA, 0.18); cr.fill()
        cr.set_source_rgb(*BLANCO); cr.rectangle(W / 2 - 4, 860, 8, 440); cr.fill()
        figura(cr, 270 - off, 1260, t, NAR, 0.7, escudo=1.0)
        figura(cr, 810 + off, 1260, t, NAR, 0.7)
        texto(cr, "SE ATORA", 270 - off, 930, 54, ROJO, borde=8)
        texto(cr, "EXPERTO", 810 + off, 930, 54, LIMA, borde=8)
        return "mismo nivel, otra ayuda", VIO
    if i == 7:
        u = local(7, t)
        cr.rectangle(0, 860, W / 2 - 6, 440); cr.set_source_rgba(*ROJO, 0.12); cr.fill()
        cr.rectangle(W / 2 + 6, 860, W / 2 - 6, 440); cr.set_source_rgba(*LIMA, 0.12); cr.fill()
        candado(cr, 540, 1120, 0.6 + 0.35 * ease(u * 3), ease((u - 0.35) * 4))
        if u > 0.55: texto(cr, "SECRETO", 540, 930, 90, AMA, borde=10)
        return "nunca te lo dijo", ROJO
    return None, None


def fondo(cr, t):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *BG2); g.add_color_stop_rgb(0.55, *BG); g.add_color_stop_rgb(1, 0.02, 0.06, 0.05)
    cr.set_source(g); cr.paint()
    # hojas de selva a los lados que se mecen + luciérnagas (antes: estrellas y brasas)
    for lado in (0, 1):
        for k in range(5):
            cr.save()
            bx = 0 if lado == 0 else W; by = 250 + k * 330
            cr.translate(bx, by); cr.rotate((0.5 if lado == 0 else math.pi - 0.5) + 0.06 * math.sin(t * 1.3 + k))
            cr.move_to(0, 0); cr.curve_to(80, -70, 220, -60, 300, 0); cr.curve_to(220, 60, 80, 70, 0, 0)
            cr.set_source_rgba(*HOJA, 0.9); cr.fill(); cr.restore()
    rnd = random.Random(3)
    for k in range(26):
        x = rnd.uniform(40, 1040) + 30 * math.sin(t * 0.7 + k); y = rnd.uniform(100, 1800) + 20 * math.cos(t * 0.9 + k)
        a = 0.3 + 0.3 * math.sin(t * 2 + k * 1.7)
        cr.new_sub_path(); cr.arc(x, y, 4, 0, 2 * math.pi); cr.set_source_rgba(*LIMA, a); cr.fill()


def gancho(cr, t):
    # entrada nueva: cada línea entra deslizándose desde la izquierda con rebote (antes: desde grande y se asienta); cuadro 0 legible
    ys = [470, 625, 830]; sizes = [150, 100, 180]
    for k, (s, y, z) in enumerate(zip(GANCHO["lineas"], ys, sizes)):
        u = (t - k * 0.06) / 0.4
        dx = 0 if u >= 1 else (-50 * (1 - ease(max(u, 0))) + 20 * math.sin(max(u, 0) * math.pi))
        col = NAR if s == GANCHO["resalta"] else BLANCO
        texto(cr, s, W / 2 + dx, y, z, col, borde=16)


def subtitulo(cr, i, t):
    s = L[i]["texto"]; pal = s.split(" ")
    u = (t - L[i]["t0"]) / (L[i]["t1"] - L[i]["t0"])
    total = sum(len(p) + 1 for p in pal); vis = u * total * 1.15
    size = 70; font(cr, size)
    lineas, act = [], []
    for p in pal:
        prueba = " ".join(act + [p])
        if cr.text_extents(prueba).x_advance > 960 and act: lineas.append(act); act = [p]
        else: act.append(p)
    lineas.append(act)
    y = 420 if len(lineas) <= 2 else 380
    acc = 0
    for ln in lineas:
        wtot = cr.text_extents(" ".join(ln)).x_advance; x = W / 2 - wtot / 2
        for p in ln:
            acc += len(p) + 1
            col = COLRES.get(i, AMA) if p in RESALTA.get(i, []) else BLANCO
            a = 1.0 if acc <= vis else 0.28
            font(cr, size); adv = cr.text_extents(p + " ").x_advance
            cr.move_to(x, y); cr.text_path(p)
            cr.set_source_rgba(*OSCURO, a); cr.set_line_width(9); cr.stroke_preserve()
            cr.set_source_rgba(*col, a); cr.fill()
            x += adv
        y += 90


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    fondo(cr, t)
    i = linea_en(t)
    # cámara nueva: paneo lateral suave + zoom hacia afuera en cada escena (antes: empuje hacia adentro con deriva vertical)
    zc = 1.30 - 0.10 * ease(local(i, t))
    if t < L[1]["t0"]: zc = 1.18 + 0.12 * ease(t / L[1]["t0"])
    px = 22 * math.sin(t * 0.8); sx = 0
    if i == 3 and 0.55 < local(3, t) < 0.7: sx = 10 * math.sin(t * 70)
    cr.save(); cr.translate(540 + px + sx, 1100); cr.scale(zc, zc); cr.translate(-540, -1100)
    eti, col = escena(cr, t)
    cr.restore()
    if t < L[1]["t0"] - 0.05: gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1420, col, 38)
    chipb(cr, "El juego te ayuda en secreto", 360, 1740, AMA, 28)
    cr.set_source_rgba(1, 1, 1, 0.12); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*LIMA); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        d = t - x["t0"]
        if 0 <= d < 0.1:
            cr.set_source_rgba(0.9, 1, 0.8, 0.16 * (1 - d / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [round(L[-1]["t1"] - 0.3, 1)]
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
