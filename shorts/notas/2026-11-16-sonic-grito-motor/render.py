"""Motor de respaldo Pixel Diario — Short 'Sonic gastó su memoria en una palabra'.
Dibuja con cairo, sin personajes, logos ni diseños reconocibles: cartucho genérico gris sin
etiqueta, monedas genéricas, iconos simples, televisor genérico, siluetas redondas genéricas
de animales y una figura blanca geométrica. "Sonic", "SEGA" y "Yuji Naka" solo como texto simple.
Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["1/8", "DEL JUEGO"], "resalta": "1/8"}

# paleta nueva: arcade de los 90, azul cobalto + magenta (antes: selva verde azulado + violeta)
BG = (0.03, 0.05, 0.18)
BG2 = (0.22, 0.03, 0.2)
AMA = (1.0, 0.85, 0.2)
ROJO = (1.0, 0.25, 0.32)
CIAN = (0.3, 0.9, 1.0)
MAG = (1.0, 0.35, 0.8)
VERDE = (0.45, 1.0, 0.55)
GRIS = (0.62, 0.63, 0.68)
BLANCO = (1, 1, 1)
OSCURO = (0.02, 0.02, 0.05)

RESALTA = {0: ["octavo"], 1: ["1991,", "oro."], 2: ["niveles,", "música", "velocidad."], 3: ["¡SE-GA!"],
           4: ["octavo", "dos", "sílabas.", "raro."], 5: ["¿Por", "qué", "tanto?", "otra", "cosa."],
           6: ["breakdance", "banda", "animales."], 7: ["tiempo", "quitó."], 8: ["hueco", "grito", "comerciales."],
           9: ["palabra…", "baile", "nunca"]}
COLRES = {1: AMA, 2: CIAN, 3: MAG, 4: ROJO, 5: AMA, 6: MAG, 7: ROJO, 8: CIAN, 9: AMA}


def ease(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)


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
        cr.set_source_rgba(*OSCURO, alpha); cr.set_line_width(borde); cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.stroke_preserve()
    cr.set_source_rgba(*color, alpha); cr.fill()
    return ext.x_advance


def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0); cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi); cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); cr.close_path()


def chipb(cr, s, x, y, color, size=34):
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: píldora rellena de color con sombra dura
    y texto oscuro (antes: contorno de color sobre relleno oscuro)."""
    x = max(x, 340)
    font(cr, size); w = cr.text_extents(s).x_advance + 56; h = size + 30
    rrect(cr, x + 8, y + 8, w, h, h / 2); cr.set_source_rgba(0, 0, 0, 0.6); cr.fill()
    rrect(cr, x, y, w, h, h / 2); cr.set_source_rgb(*color); cr.fill()
    cr.set_source_rgb(*OSCURO); cr.move_to(x + 28, y + size + 8); cr.show_text(s)


# ---------- dibujos genéricos ----------
def cartucho(cr, x, y, esc, t, rojo=1.0, rot=0.0, cajon=0.0, rebanadas=True):
    """cartucho gris genérico sin etiqueta, partido en 8 rebanadas verticales; la última se ilumina en rojo."""
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    w, h = 480, 380
    rrect(cr, -w / 2 + 10, -h / 2 + 14, w, h, 26); cr.set_source_rgba(0, 0, 0, 0.5); cr.fill()
    rrect(cr, -w / 2, -h / 2, w, h, 26); cr.set_source_rgb(*GRIS); cr.fill()
    # muescas de agarre arriba
    cr.set_source_rgb(0.5, 0.51, 0.56)
    for k in range(7): cr.rectangle(-150 + k * 48, -h / 2 + 18, 24, 34); cr.fill()
    # zona de memoria
    mx, my, mw, mh = -w / 2 + 40, -h / 2 + 80, w - 80, h - 130
    rrect(cr, mx, my, mw, mh, 12); cr.set_source_rgb(0.2, 0.22, 0.3); cr.fill()
    sw = mw / 8
    if rebanadas:
        for k in range(8):
            if k == 7:
                a = rojo * (0.75 + 0.25 * math.sin(t * 7))
                cr.save(); cr.translate(cajon * 260, 0)
                cr.rectangle(mx + k * sw + 4, my + 4, sw - 8, mh - 8)
                cr.set_source_rgba(*ROJO, max(a, 0.15) if cajon < 0.5 else 0.25); cr.fill()
                if cajon > 0:
                    cr.set_source_rgba(1, 1, 1, cajon); cr.set_line_width(6)
                    cr.rectangle(mx + k * sw + 4, my + 4, sw - 8, mh - 8); cr.stroke()
                cr.restore()
            else:
                cr.rectangle(mx + k * sw + 4, my + 4, sw - 8, mh - 8); cr.set_source_rgb(0.32, 0.4, 0.62); cr.fill()
    # contactos abajo
    cr.set_source_rgb(*AMA)
    for k in range(12): cr.rectangle(-w / 2 + 50 + k * 33, h / 2 - 34, 18, 26); cr.fill()
    cr.restore()


def moneda(cr, x, y, r, t, k):
    sx = abs(math.cos(t * 5 + k))
    cr.save(); cr.translate(x, y); cr.scale(max(sx, 0.15), 1)
    cr.new_sub_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.set_source_rgb(*AMA); cr.fill()
    cr.new_sub_path(); cr.arc(0, 0, r * 0.7, 0, 2 * math.pi); cr.set_source_rgb(0.85, 0.65, 0.1); cr.set_line_width(6); cr.stroke()
    cr.restore()


def icono_mapa(cr, x, y, s, a):
    cr.save(); cr.translate(x, y); cr.scale(s, s)
    for k, c in enumerate([(0.3, 0.75, 0.5), (0.25, 0.6, 0.45), (0.3, 0.75, 0.5)]):
        cr.move_to(-90 + k * 60, -60 + (10 if k % 2 else 0)); cr.line_to(-30 + k * 60, -60 + (0 if k % 2 else 10))
        cr.line_to(-30 + k * 60, 70 + (0 if k % 2 else 10)); cr.line_to(-90 + k * 60, 70 + (10 if k % 2 else 0)); cr.close_path()
        cr.set_source_rgba(*c, a); cr.fill()
    cr.set_source_rgba(*ROJO, a); cr.set_line_width(8)
    cr.move_to(-70, 40); cr.curve_to(-30, -40, 20, 50, 60, -30); cr.stroke()
    cr.restore()


def icono_nota(cr, x, y, s, a):
    cr.save(); cr.translate(x, y); cr.scale(s, s); cr.set_source_rgba(*MAG, a)
    cr.save(); cr.translate(-30, 50); cr.scale(1.3, 1); cr.arc(0, 0, 28, 0, 2 * math.pi); cr.restore(); cr.fill()
    cr.rectangle(2, -80, 14, 130); cr.fill()
    cr.move_to(16, -80); cr.curve_to(60, -60, 70, -20, 50, 10); cr.curve_to(55, -20, 40, -40, 16, -45); cr.close_path(); cr.fill()
    cr.restore()


def icono_rayo(cr, x, y, s, a):
    cr.save(); cr.translate(x, y); cr.scale(s, s); cr.set_source_rgba(*AMA, a)
    cr.move_to(20, -90); cr.line_to(-50, 10); cr.line_to(-5, 10); cr.line_to(-25, 90); cr.line_to(50, -15); cr.line_to(5, -15); cr.close_path(); cr.fill()
    cr.restore()


def barra_memoria(cr, x, y, w, h, lleno, col=CIAN, segs=8, rojo_seg=None, label=None):
    rrect(cr, x - 6, y - 6, w + 12, h + 12, 14); cr.set_source_rgb(*BLANCO); cr.fill()
    cr.rectangle(x, y, w, h); cr.set_source_rgb(*OSCURO); cr.fill()
    sw = w / segs
    for k in range(segs):
        f = max(0, min(1, lleno * segs - k))
        if f <= 0: continue
        c = ROJO if (rojo_seg is not None and k == rojo_seg) else col
        cr.rectangle(x + k * sw + 4, y + 4, (sw - 8) * f, h - 8); cr.set_source_rgb(*c); cr.fill()
    if label: texto(cr, label, x + w / 2, y - 26, 44, BLANCO, borde=6)


def ondas(cr, x, y, t, col=MAG, n=5, rmax=520, alpha=1.0):
    for k in range(n):
        r = ((t * 380 + k * rmax / n) % rmax)
        a = alpha * (1 - r / rmax)
        cr.new_sub_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*col, a); cr.set_line_width(14); cr.stroke()


def tele(cr, x, y, esc, t, encendida=1.0):
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    rrect(cr, -230, -170, 460, 330, 40); cr.set_source_rgb(0.45, 0.3, 0.2); cr.fill()
    rrect(cr, -190, -135, 300, 260, 50); cr.set_source_rgb(*tuple(lerp(0.05, 0.25, encendida) for _ in range(3))); cr.fill()
    if encendida > 0:
        rnd = random.Random(int(t * 12))
        for k in range(40):
            cr.rectangle(-180 + rnd.uniform(0, 270), -125 + rnd.uniform(0, 240), 6, 3)
            cr.set_source_rgba(1, 1, 1, 0.35 * encendida); cr.fill()
    for k in range(2):
        cr.new_sub_path(); cr.arc(170, -80 + k * 80, 22, 0, 2 * math.pi); cr.set_source_rgb(0.8, 0.8, 0.8); cr.fill()
    cr.set_source_rgb(0.3, 0.3, 0.3); cr.set_line_width(8)
    cr.move_to(-40, -170); cr.line_to(-110, -270); cr.move_to(40, -170); cr.line_to(110, -270); cr.stroke()
    cr.restore()


def animal(cr, x, y, esc, t, k, col, instr):
    """silueta redonda genérica con orejas redondas y un instrumento simple"""
    cr.save(); cr.translate(x, y + 10 * math.sin(t * 8 + k)); cr.scale(esc, esc)
    cr.set_source_rgb(*col)
    rrect(cr, -55, -110, 110, 120, 45); cr.fill()
    cr.new_sub_path(); cr.arc(0, -150, 50, 0, 2 * math.pi); cr.fill()
    for dx in (-36, 36): cr.new_sub_path(); cr.arc(dx, -195, 18, 0, 2 * math.pi); cr.fill()
    cr.set_source_rgb(*OSCURO)
    for dx in (-16, 16): cr.new_sub_path(); cr.arc(dx, -155, 6, 0, 2 * math.pi); cr.fill()
    if instr == 0:  # tambor
        cr.save(); cr.translate(0, -20); cr.scale(1, 0.4); cr.arc(0, 0, 70, 0, 2 * math.pi); cr.restore()
        cr.set_source_rgb(*BLANCO); cr.fill()
    elif instr == 1:  # cuerdas
        cr.set_source_rgb(*AMA); cr.save(); cr.translate(-20, -40); cr.rotate(-0.6)
        cr.new_sub_path(); cr.arc(0, 0, 34, 0, 2 * math.pi); cr.fill(); cr.rectangle(-6, -130, 12, 110); cr.fill(); cr.restore()
    else:  # trompeta
        cr.set_source_rgb(*AMA); cr.move_to(-10, -150); cr.line_to(80, -170); cr.line_to(110, -200); cr.line_to(110, -120); cr.line_to(80, -150); cr.close_path(); cr.fill()
    cr.restore()


def bailarin(cr, x, y, t, esc=1.0):
    """figura blanca geométrica genérica girando de cabeza (breakdance)"""
    cr.save(); cr.translate(x, y); cr.scale(esc, esc); cr.rotate(math.pi + 0.3 * math.sin(t * 6))
    cr.set_source_rgb(*BLANCO)
    cr.new_sub_path(); cr.arc(0, 0, 32, 0, 2 * math.pi); cr.fill()
    rrect(cr, -28, 30, 56, 100, 24); cr.fill()
    cr.set_line_width(24); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    a = t * 9
    for s in (1, -1):
        cr.move_to(0, 120); cr.line_to(110 * math.cos(a) * s, 200 + 50 * math.sin(a) * s); cr.stroke()
        cr.move_to(0, 50); cr.line_to(-70 * s, 10); cr.stroke()
    cr.restore()


def tarjeta(cr, s, x, y, size, color, esc=1.0, rot=0.0):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 60
    rrect(cr, -w / 2, -size * 0.95, w, size * 1.5, 14); cr.set_source_rgb(*BLANCO); cr.fill()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 30, size * 0.25); cr.show_text(s)
    cr.restore()


def sello(cr, s, x, y, esc, rot=-0.2, a=1.0):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, 110); w = cr.text_extents(s).x_advance + 70
    rrect(cr, -w / 2, -110, w, 160, 16); cr.set_source_rgba(*ROJO, a); cr.set_line_width(14); cr.stroke()
    cr.set_source_rgba(*ROJO, a); cr.move_to(-w / 2 + 35, 10); cr.show_text(s)
    cr.restore()


def escena_a(cr, t):
    """imagen del inicio y del cierre: cartucho genérico en 8 rebanadas, una en rojo; gira y late desde el cuadro 0"""
    cartucho(cr, 540, 1080, 1.0 + 0.04 * math.sin(t * 5), t, rot=0.06 * math.sin(t * 2.2))
    texto(cr, "1 PALABRA", 540, 1390, 64, ROJO, borde=10, alpha=0.6 + 0.4 * math.sin(t * 6) ** 2)


def escena(cr, t):
    i = linea_en(t)
    if i == 0 or i == 9:
        escena_a(cr, t)
        return ("Sonic · 1991", CIAN) if i == 0 else ("1 palabra = 1 baile", MAG)
    if i == 1:
        u = local(1, t)
        cartucho(cr, 540, 1150, 0.8, t, rojo=0.0)
        for k in range(9):
            yy = 860 + ((t * 500 + k * 130) % 360)
            moneda(cr, 340 + (k * 97) % 400, yy, 34, t, k)
        tarjeta(cr, "1991", 540, 930, 110, (0.15, 0.2, 0.5), esc=ease(u * 4), rot=-0.05)
        return "memoria = oro", AMA
    if i == 2:
        u = local(2, t)
        cartucho(cr, 540, 1120, 0.6, t, rojo=0.0, rebanadas=False)
        for k, fn in enumerate((icono_mapa, icono_nota, icono_rayo)):
            e = ease((u - k * 0.22) * 4)
            if e > 0:
                fn(cr, lerp(260 + k * 280, 360 + k * 180, ease((u - 0.75) * 4)), lerp(860, 1000, ease((u - 0.75) * 4)), 0.9, e)
        barra_memoria(cr, 340, 1310, 400, 56, 0.3 + 0.62 * ease(u * 1.3), CIAN, label="MEMORIA")
        return "niveles + música + velocidad", CIAN
    if i == 3:
        u = local(3, t)
        tele(cr, 540, 1120, 0.95, t, encendida=ease((u - 0.1) * 3))
        if u > 0.6:
            e = ease((u - 0.6) * 4)
            ondas(cr, 540, 1080, t, MAG, alpha=e)
            texto(cr, "SE-GA", 540, 1130, 80 + 120 * e, BLANCO, borde=14)
        return "lo primero que oyes", MAG
    if i == 4:
        u = local(4, t)
        ondas(cr, 540, 1060, t * 0.6, MAG, n=3, rmax=450, alpha=0.4)
        barra_memoria(cr, 160, 1000, 760, 140, 1.0, (0.32, 0.4, 0.62), rojo_seg=7)
        e = ease(u * 3)
        texto(cr, "SE-GA", 160 + 760 * 15 / 16, 1090, 30 * e + 1, BLANCO, borde=5)
        texto(cr, "1/8", 540, 1290, 120 + 15 * math.sin(t * 9), ROJO, borde=12)
        return "2 sílabas = 1/8", ROJO
    if i == 5:
        u = local(5, t)
        cartucho(cr, 470, 1120, 0.85, t, cajon=ease((u - 0.1) * 3))
        texto(cr, "¿?", 820, 960, 160 + 15 * math.sin(t * 7), AMA, borde=12)
        return "ese espacio era para…", AMA
    if i == 6:
        u = local(6, t)
        # el cambio visual más fuerte: luces de disco giratorias + banda genérica
        for k in range(6):
            a = t * 1.5 + k * math.pi / 3
            cr.move_to(540, 860)
            cr.line_to(540 + 900 * math.cos(a - 0.12), 860 + 900 * math.sin(a - 0.12))
            cr.line_to(540 + 900 * math.cos(a + 0.12), 860 + 900 * math.sin(a + 0.12)); cr.close_path()
            cr.set_source_rgba(*([MAG, CIAN, AMA][k % 3]), 0.18); cr.fill()
        cr.new_sub_path(); cr.arc(540, 870, 50, 0, 2 * math.pi); cr.set_source_rgb(0.85, 0.85, 0.9); cr.fill()
        cr.rectangle(0, 1290, W, 40); cr.set_source_rgb(0.25, 0.1, 0.3); cr.fill()
        for k, (x, col) in enumerate([(380, (0.95, 0.6, 0.3)), (700, (0.6, 0.85, 0.4)), (900, (0.9, 0.5, 0.6))]):
            if u > 0.15 + k * 0.1: animal(cr, x, 1290, 0.8, t, k, col, k)
        bailarin(cr, 560, 1060, t, 0.9)
        return "prueba de sonido", MAG
    if i == 7:
        u = local(7, t)
        apag = ease((u - 0.3) * 3)
        for k, (x, col) in enumerate([(380, (0.95, 0.6, 0.3)), (700, (0.6, 0.85, 0.4)), (900, (0.9, 0.5, 0.6))]):
            animal(cr, x, 1290, 0.8, 0, k, tuple(c * (1 - 0.7 * apag) for c in col), k)
        bailarin(cr, 560, 1060, 0, 0.9)
        cr.rectangle(-300, 500, W + 600, 1200); cr.set_source_rgba(0, 0, 0, 0.45 * apag); cr.fill()
        sello(cr, "CANCELADO", 540, 1110, 1.6 - 0.6 * ease(u * 4), a=ease(u * 4))
        return "sin tiempo → fuera", ROJO
    if i == 8:
        u = local(8, t)
        tele(cr, 330, 1080, 0.6, t, 1.0)
        cartucho(cr, 790, 1110, 0.55, t, cajon=1 - ease((u - 0.3) * 2.5))
        for k in range(3):
            p = ((t * 0.9 + k / 3) % 1)
            x = lerp(470, 900, p); y = 1050 - 120 * math.sin(math.pi * p)
            texto(cr, "SE-GA", x, y, 50, MAG, borde=8, alpha=1 - p * 0.6)
        tarjeta(cr, "YUJI NAKA", 540, 1330, 58, (0.15, 0.2, 0.5), esc=ease(u * 4))
        return "el grito de la tele", CIAN
    return None, None


def fondo(cr, t):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *BG2); g.add_color_stop_rgb(0.5, *BG); g.add_color_stop_rgb(1, 0.01, 0.02, 0.1)
    cr.set_source(g); cr.paint()
    # rejilla de neón en perspectiva que avanza + estrellas de píxel (antes: hojas de selva y luciérnagas)
    cr.set_line_width(3)
    hz = 1450
    for k in range(-10, 11):
        cr.move_to(540 + k * 40, hz); cr.line_to(540 + k * 260, H)
        cr.set_source_rgba(*MAG, 0.35); cr.stroke()
    for k in range(8):
        p = ((k + t * 1.2) % 8) / 8
        y = hz + (H - hz) * p * p
        cr.move_to(0, y); cr.line_to(W, y); cr.set_source_rgba(*MAG, 0.15 + 0.35 * p); cr.stroke()
    rnd = random.Random(5)
    for k in range(30):
        x = rnd.uniform(20, 1060); y = rnd.uniform(60, 1400)
        a = 0.25 + 0.35 * math.sin(t * 3 + k * 1.3)
        s = rnd.choice([6, 8, 10])
        cr.rectangle(x, y, s, s); cr.set_source_rgba(*CIAN, max(a, 0)); cr.fill()


def gancho(cr, t):
    # entrada nueva: cae desde arriba con rebote (antes: deslizando desde la izquierda); cuadro 0 ya legible
    ys = [560, 760]; sizes = [260, 130]
    for k, (s, y, z) in enumerate(zip(GANCHO["lineas"], ys, sizes)):
        u = (t - k * 0.05) / 0.5
        dy = 0 if u >= 1 else (-40 * (1 - ease(max(u, 0))) + 18 * abs(math.sin(max(u, 0) * math.pi * 2)) * (1 - max(u, 0)))
        col = ROJO if s == GANCHO["resalta"] else BLANCO
        texto(cr, s, W / 2, y + dy, z, col, borde=18)


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
    # cámara nueva: empuje hacia adentro + leve inclinación que oscila (antes: paneo lateral + zoom hacia afuera)
    zc = 1.0 + 0.12 * ease(local(i, t))
    if i == 0: zc = 1.0 + 0.15 * ease(t / L[0]["t1"])
    rot = 0.015 * math.sin(t * 0.9); sx = sy = 0
    if i == 3 and local(3, t) > 0.6: sx = 12 * math.sin(t * 61); sy = 10 * math.cos(t * 53)
    cr.save(); cr.translate(540 + sx, 1100 + sy); cr.rotate(rot); cr.scale(zc, zc); cr.translate(-540, -1100)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0 and t < L[0]["t1"] + 0.1: gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1480, col, 40)
    chipb(cr, "Secretos de videojuegos", 360, 1740, AMA, 28)
    cr.set_source_rgba(1, 1, 1, 0.12); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*MAG); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        d = t - x["t0"]
        if 0 <= d < 0.1:
            cr.set_source_rgba(1, 0.8, 1, 0.16 * (1 - d / 0.1)); cr.paint()
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
