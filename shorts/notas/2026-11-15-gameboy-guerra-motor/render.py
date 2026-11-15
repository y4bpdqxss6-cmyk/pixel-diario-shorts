"""Motor de respaldo Pixel Diario — Short 'Este Game Boy sobrevivió a una guerra'.
Dibuja con cairo, sin logos ni diseños reconocibles: consola portátil genérica
(azul pizarra, sin marca ni textos), figura geométrica genérica, tiendas de campaña,
vitrina genérica. Sin retratos. Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["SOBREVIVIÓ", "A UNA", "GUERRA"], "resalta": "GUERRA"}

# paleta: noche de campamento azul acero con brasas naranjas (antes: pizarra verde noche con piezas de colores)
BG = (0.04, 0.055, 0.09)
REJ = (0.12, 0.16, 0.24)
AMA = (1.0, 0.8, 0.25)
NAR = (1.0, 0.5, 0.12)
ROJO = (1.0, 0.3, 0.25)
CIAN = (0.45, 0.85, 1.0)
VERDE = (0.55, 0.95, 0.45)
ARENA = (0.78, 0.66, 0.45)
BLANCO = (1, 1, 1)
OSCURO = (0.02, 0.025, 0.04)
CONSOLA = (0.42, 0.5, 0.62)
PANT = (0.55, 0.75, 0.35)

RESALTA = {1: ["médico", "militar", "Golfo."], 2: ["incendió…", "adentro."], 3: ["negro", "derretidos."],
           4: ["no", "lo", "tiró:", "Nintendo", "nuevo."], 5: ["raro."], 6: ["Tetris", "encendieron."],
           7: ["prendió.", "start", "select", "funcionaban."], 8: ["Nueva", "York."], 9: ["dos", "mil", "veintitrés."],
           10: ["caída…", "sobrevivió", "guerra."]}
COLRES = {2: NAR, 3: NAR, 4: CIAN, 6: VERDE, 7: VERDE, 8: CIAN, 9: AMA, 10: NAR}


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
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: píldora redonda rellena de color con texto oscuro."""
    x = max(x, 340)
    font(cr, size); w = cr.text_extents(s).x_advance + 64; h = size + 30
    rrect(cr, x, y, w, h, h / 2); cr.set_source_rgb(*color); cr.fill()
    cr.set_source_rgb(*OSCURO); cr.move_to(x + 32, y + size + 8); cr.show_text(s)


# ---------- dibujos genéricos ----------
def bloques(cr, x, y, w, h, t, alpha=1.0):
    """bloques genéricos cayendo en la pantallita"""
    c = w / 8
    cr.save(); cr.rectangle(x, y, w, h); cr.clip()
    rnd = random.Random(3)
    for k in range(8):
        if rnd.random() < 0.75: cr.rectangle(x + k * c + 2, y + h - c + 2, c - 4, c - 4)
        if rnd.random() < 0.4: cr.rectangle(x + k * c + 2, y + h - 2 * c + 2, c - 4, c - 4)
    yy = y + ((t * 1.2) % 1) * (h - 2 * c)
    xx = x + 3 * c
    for (i, j) in [(0, 0), (1, 0), (2, 0), (1, 1)]:
        cr.rectangle(xx + i * c + 2, yy + j * c + 2, c - 4, c - 4)
    cr.set_source_rgba(0.12, 0.22, 0.08, alpha); cr.fill()
    cr.restore()


def consola(cr, x, y, t, esc=1.0, quemada=0.0, encendida=0.0, derrite=0.0, cartucho=None):
    """consola portátil genérica (azul pizarra, sin marca). Centro (x,y), alto ~520*esc."""
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    if cartucho is not None:  # cartucho genérico entrando por arriba
        cy = lerp(-420, -300, ease(cartucho))
        rrect(cr, -110, cy - 60, 220, 140, 10); cr.set_source_rgb(0.3, 0.3, 0.34); cr.fill()
        rrect(cr, -80, cy - 40, 160, 70, 6); cr.set_source_rgb(0.85, 0.85, 0.8); cr.fill()
    rrect(cr, -190, -260, 380, 520, 34)
    base = tuple(lerp(c, 0.08, quemada) for c in CONSOLA)
    cr.set_source_rgb(*base); cr.fill_preserve()
    cr.set_source_rgba(0.85, 0.9, 1.0, 0.75); cr.set_line_width(7); cr.stroke()
    if quemada > 0:  # manchas de quemado
        rnd = random.Random(11)
        for k in range(14):
            cr.new_sub_path(); cr.arc(rnd.uniform(-170, 170), rnd.uniform(-240, 240), rnd.uniform(20, 60), 0, 2 * math.pi)
            cr.set_source_rgba(0.02, 0.02, 0.02, 0.55 * quemada); cr.fill()
    # pantalla
    rrect(cr, -150, -220, 300, 240, 18); cr.set_source_rgb(0.15, 0.17, 0.2); cr.fill()
    on = encendida
    cr.rectangle(-115, -195, 230, 190)
    cr.set_source_rgb(*tuple(lerp(0.08, c, on) for c in PANT)); cr.fill()
    if on > 0.05: bloques(cr, -115, -195, 230, 190, t, on)
    # cruceta y dos botones redondos (genéricos)
    bc = (0.12, 0.12, 0.14) if quemada < 0.5 else (0.05, 0.05, 0.05)
    cr.set_source_rgb(*bc)
    dy = derrite * 18
    cr.rectangle(-140, 80, 90, 30); cr.rectangle(-110, 50, 30, 90); cr.fill()
    if derrite > 0:
        for (dx, w) in [(-120, 14), (-95, 10), (-70, 12)]:
            rrect(cr, dx, 100, w, 20 + dy * (1 + (dx % 3)), w / 2); cr.fill()
    for (bx, by) in [(70, 110), (130, 80)]:
        cr.new_sub_path(); cr.save(); cr.translate(bx, by); cr.scale(1, 1 + derrite * 0.5); cr.arc(0, 0, 26, 0, 2 * math.pi); cr.restore()
        cr.set_source_rgb(*((0.55, 0.15, 0.3) if quemada < 0.5 else (0.1, 0.04, 0.05))); cr.fill()
    # dos botoncitos alargados
    for bx in (-50, 20):
        rrect(cr, bx, 180, 50, 16, 8)
        lit = on > 0.5 and (math.sin(t * 6 + bx) > 0)
        cr.set_source_rgb(*(VERDE if lit else (0.2, 0.2, 0.22))); cr.fill()
    cr.restore()


def humo(cr, x, y, t, n=8, alpha=0.35):
    rnd = random.Random(21)
    for k in range(n):
        ph = (t * 0.35 + k / n) % 1
        xx = x + rnd.uniform(-90, 90) + 40 * math.sin(t + k)
        yy = y - ph * 330
        cr.new_sub_path(); cr.arc(xx, yy, 30 + ph * 60, 0, 2 * math.pi)
        cr.set_source_rgba(0.5, 0.5, 0.55, alpha * (1 - ph)); cr.fill()


def llamas(cr, x, y, w, t, alto=1.0):
    for k in range(9):
        fx = x - w / 2 + k * w / 8
        h = (90 + 50 * math.sin(t * 9 + k * 1.7)) * alto
        for col, s in [(ROJO, 1.0), (NAR, 0.72), (AMA, 0.42)]:
            cr.move_to(fx - 30 * s, y); cr.curve_to(fx - 30 * s, y - h * s * 0.6, fx + 8 * math.sin(t * 7 + k), y - h * s * 0.8,
                                                fx + 5 * math.sin(t * 7 + k), y - h * s)
            cr.curve_to(fx + 10, y - h * s * 0.6, fx + 30 * s, y - h * s * 0.4, fx + 30 * s, y); cr.close_path()
            cr.set_source_rgba(*col, 0.9); cr.fill()


def brasas(cr, t, y0=1350, n=22):
    rnd = random.Random(5)
    for k in range(n):
        x = rnd.uniform(60, 1020); sp = rnd.uniform(60, 140)
        y = y0 - ((t * sp + rnd.uniform(0, 900)) % 900)
        cr.new_sub_path(); cr.arc(x + 12 * math.sin(t * 2 + k), y, rnd.uniform(3, 7), 0, 2 * math.pi)
        cr.set_source_rgba(*NAR, 0.7); cr.fill()


def dunas(cr, alpha=0.9):
    cr.set_source_rgba(*tuple(c * 0.55 for c in ARENA), alpha)
    cr.move_to(0, 1300); cr.curve_to(250, 1220, 450, 1330, 700, 1250); cr.curve_to(850, 1210, 980, 1260, 1080, 1240)
    cr.line_to(1080, 2000); cr.line_to(0, 2000); cr.close_path(); cr.fill()


def tienda(cr, x, y, w, col=(0.42, 0.45, 0.3)):
    cr.set_source_rgb(*col)
    cr.move_to(x - w / 2, y); cr.line_to(x, y - w * 0.6); cr.line_to(x + w / 2, y); cr.close_path(); cr.fill()
    cr.set_source_rgb(*tuple(c * 0.5 for c in col))
    cr.move_to(x - w * 0.12, y); cr.line_to(x, y - w * 0.3); cr.line_to(x + w * 0.12, y); cr.close_path(); cr.fill()


def figura(cr, x, y, t, color=CIAN, esc=1.0):
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    bob = 4 * math.sin(t * 3)
    cr.set_source_rgb(*color)
    rrect(cr, -45, -150 + bob, 90, 120, 26); cr.fill()
    cr.new_sub_path(); cr.arc(0, -190 + bob, 34, 0, 2 * math.pi); cr.fill()
    cr.rectangle(-36, -40, 26, 40); cr.rectangle(10, -40, 26, 40); cr.fill()
    # brazalete de médico: maletín blanco con cruz verde (no la cruz roja)
    rrect(cr, 40, -90 + bob, 70, 52, 8); cr.set_source_rgb(*BLANCO); cr.fill()
    cr.set_source_rgb(0.2, 0.7, 0.35); cr.rectangle(68, -82 + bob, 14, 36); cr.rectangle(57, -71 + bob, 36, 14); cr.fill()
    cr.restore()


def caja_envio(cr, x, y, esc=1.0, rot=0.0):
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    cr.rectangle(-110, -80, 220, 160); cr.set_source_rgb(0.72, 0.55, 0.33); cr.fill()
    cr.rectangle(-18, -80, 36, 160); cr.set_source_rgb(0.85, 0.75, 0.55); cr.fill()
    cr.restore()


def tarjeta(cr, s, x, y, size, color, esc=1.0, rot=0.0):
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 60
    rrect(cr, -w / 2, -size * 0.95, w, size * 1.5, 14); cr.set_source_rgb(*BLANCO); cr.fill()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 30, size * 0.25); cr.show_text(s)
    cr.restore()


def flecha(cr, x1, y1, x2, y2, col, u=1.0):
    xe = lerp(x1, x2, ease(u)); ye = lerp(y1, y2, ease(u))
    cr.set_source_rgb(*col); cr.set_line_width(12); cr.move_to(x1, y1); cr.line_to(xe, ye); cr.stroke()
    a = math.atan2(y2 - y1, x2 - x1)
    cr.move_to(xe + 14 * math.cos(a), ye + 14 * math.sin(a))
    cr.line_to(xe - 26 * math.cos(a) + 22 * math.sin(a), ye - 26 * math.sin(a) - 22 * math.cos(a))
    cr.line_to(xe - 26 * math.cos(a) - 22 * math.sin(a), ye - 26 * math.sin(a) + 22 * math.cos(a)); cr.close_path(); cr.fill()


def vitrina(cr, x, y, t):
    # haz de luz
    cr.move_to(x - 60, 860); cr.line_to(x + 60, 860); cr.line_to(x + 260, y + 160); cr.line_to(x - 260, y + 160); cr.close_path()
    cr.set_source_rgba(1, 0.95, 0.7, 0.10 + 0.03 * math.sin(t * 3)); cr.fill()
    cr.rectangle(x - 170, y + 160, 340, 140); cr.set_source_rgb(0.25, 0.27, 0.32); cr.fill()
    cr.rectangle(x - 200, y + 150, 400, 20); cr.set_source_rgb(0.35, 0.37, 0.42); cr.fill()
    cr.rectangle(x - 190, y - 230, 380, 380); cr.set_source_rgba(0.7, 0.9, 1.0, 0.10); cr.fill_preserve()
    cr.set_source_rgba(0.8, 0.95, 1, 0.6); cr.set_line_width(4); cr.stroke()
    cr.set_source_rgba(1, 1, 1, 0.25); cr.set_line_width(8)
    cr.move_to(x - 150, y - 190); cr.line_to(x - 90, y - 250 + 60); cr.stroke()


def edificios(cr, alpha=0.6):
    cr.set_source_rgba(*REJ, alpha)
    for (bx, w, h) in [(60, 120, 420), (190, 90, 560), (300, 110, 360), (800, 100, 500), (920, 140, 620), (1030, 90, 380)]:
        cr.rectangle(bx - w / 2, 1300 - h, w, h); cr.fill()
    cr.set_source_rgba(1, 0.9, 0.5, alpha * 0.4)
    rnd = random.Random(9)
    for k in range(60):
        cr.rectangle(rnd.choice([30, 160, 270, 780, 880, 1000]) + rnd.uniform(0, 60), rnd.uniform(800, 1280), 10, 14); cr.fill()


def explosion(cr, x, y, u):
    if u <= 0 or u >= 1: return
    r = 40 + 380 * ease(u)
    cr.new_sub_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*AMA, 0.5 * (1 - u)); cr.fill()
    cr.new_sub_path(); cr.arc(x, y, r * 0.6, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 0.9, 0.6 * (1 - u)); cr.fill()


def escena_a(cr, t):
    """imagen del inicio y del cierre: consola quemada, humo, brasas, pantalla con bloques"""
    llamas(cr, 540, 1300, 520, t, 0.55)
    consola(cr, 540, 1100 + 6 * math.sin(t * 2.5), t, 0.72, quemada=0.85, encendida=0.85 + 0.15 * math.sin(t * 8), derrite=0.6)
    pass  # sin humo: la franja y 300–820 queda solo para el gancho


def escena(cr, t):
    i = linea_en(t)
    if t < L[1]["t0"] or i == 10:
        escena_a(cr, t)
        return ("sobrevivió a una guerra", NAR) if i == 10 else (None, None)
    if i == 1:
        u = local(1, t)
        dunas(cr)
        tienda(cr, 260, 1260, 220); tienda(cr, 840, 1250, 260); tienda(cr, 640, 1225, 150)
        figura(cr, lerp(380, 520, ease(u)), 1300, t, CIAN, 0.95)
        return "Guerra del Golfo · 1990-91", ARENA
    if i == 2:
        u = local(2, t)
        dunas(cr)
        tienda(cr, 540, 1270, 420)
        llamas(cr, 540, 1275, 420, t, 0.4 + 1.2 * ease(u * 2))
        humo(cr, 540, 1000, t, 9, 0.4)
        return "tienda en llamas", NAR
    if i == 3:
        u = local(3, t)
        consola(cr, 540, 1090, t, 0.78 + 0.05 * u, quemada=ease(u * 2), derrite=ease(u * 1.5))
        humo(cr, 540, 900, t, 6, 0.3)
        return "frente negro, botones derretidos", NAR
    if i == 4:
        u = local(4, t)
        k = ease(u * 2)
        consola(cr, lerp(330, 760, ease((u - 0.35) * 2)), 1120 - 30 * math.sin(math.pi * ease((u - 0.35) * 2)), t,
                0.38 * (1 - 0.3 * ease((u - 0.35) * 2)), quemada=0.85, derrite=0.6)
        caja_envio(cr, 760, 1180, 0.9 + 0.1 * k)
        tarjeta(cr, "NINTENDO", 760, 960, 54, (0.2, 0.25, 0.4), esc=ease(u * 3), rot=0.04)
        return "¿me dan uno nuevo?", CIAN
    if i == 5:
        u = local(5, t)
        texto(cr, "?", 540, 1230, 330 + 30 * math.sin(t * 7), AMA, borde=12)
        rnd = random.Random(4)
        for k in range(10):
            a = k * math.pi / 5 + t; d = 210 + 30 * math.sin(t * 5 + k)
            cr.new_sub_path(); cr.arc(540 + d * math.cos(a), 1120 + d * 0.8 * math.sin(a), 10, 0, 2 * math.pi)
            cr.set_source_rgb(*NAR); cr.fill()
        return "lo raro", AMA
    if i == 6:
        u = local(6, t)
        consola(cr, 540, 1150, t, 0.66, quemada=0.85, derrite=0.6, cartucho=ease(u * 1.6),
                encendida=0.15 * ease((u - 0.8) * 5))
        return "cartucho de Tetris", VERDE
    if i == 7:
        u = local(7, t)
        consola(cr, 540, 1130, t, 0.74 + 0.04 * math.sin(t * 4), quemada=0.85, derrite=0.6, encendida=ease(u * 4))
        if u > 0.05:
            texto(cr, "¡PRENDIÓ!", 540, 920 + 10 * math.sin(t * 6), 100 * ease(u * 5) + 1, VERDE, borde=10)
        return "start y select: OK", VERDE
    if i == 8:
        u = local(8, t)
        edificios(cr, 0.7)
        vitrina(cr, 540, 1080, t)
        consola(cr, 540, 1060 + 6 * math.sin(t * 2), t, 0.42, quemada=0.85, derrite=0.6, encendida=1.0)
        tarjeta(cr, "NUEVA YORK", 540, 820, 44, (0.2, 0.25, 0.4), esc=ease(u * 3))
        return "en exhibición", CIAN
    if i == 9:
        u = local(9, t)
        anio = 2023
        texto(cr, f"{anio}", 540, 900, 150, AMA, borde=10)
        x = lerp(540, 820, ease((u - 0.55) * 2.5))
        vitrina(cr, x, 1230, t) if u < 0.55 else None
        consola(cr, x, 1220, t, 0.34, quemada=0.85, derrite=0.6, encendida=1.0 - 0.6 * ease((u - 0.6) * 3))
        if u > 0.5: flecha(cr, 400, 1330, 700, 1330, BLANCO, (u - 0.5) * 3)
        return "fuera de exhibición", AMA
    return None, None


def fondo(cr, t):
    cr.set_source_rgb(*BG); cr.paint()
    # estrellas que titilan + gradiente cálido abajo (antes: cuadrícula verde)
    rnd = random.Random(2)
    for k in range(70):
        x = rnd.uniform(0, W); y = rnd.uniform(0, H * 0.85); a = 0.25 + 0.25 * math.sin(t * rnd.uniform(1, 3) + k)
        cr.rectangle(x, y, 3, 3); cr.set_source_rgba(1, 1, 1, a); cr.fill()
    g = cairo.LinearGradient(0, H * 0.55, 0, H)
    g.add_color_stop_rgba(0, 0.3, 0.12, 0.05, 0); g.add_color_stop_rgba(1, 0.35, 0.13, 0.04, 0.55)
    cr.set_source(g); cr.rectangle(0, 0, W, H); cr.fill()


def gancho(cr, t):
    # entrada nueva: cada línea llega desde grande (x2) y se asienta con un golpe (antes: caer desde arriba); cuadro 0 completo y legible
    ys = [460, 600, 800]; sizes = [112, 96, 180]
    for k, (s, y, z) in enumerate(zip(GANCHO["lineas"], ys, sizes)):
        u = ease((t - k * 0.07) / 0.35)
        esc = 1.0 + 0.08 * (1 - u)
        col = NAR if s == GANCHO["resalta"] else BLANCO
        cr.save(); cr.translate(W / 2, y - z * 0.35); cr.scale(esc, esc); cr.translate(-W / 2, -(y - z * 0.35))
        texto(cr, s, W / 2, y, z, col, borde=16)
        cr.restore()


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
    brasas(cr, t)
    i = linea_en(t)
    # cámara: empuje lento hacia adentro con deriva vertical (antes: zoom + inclinación); sacudida en el incendio y en "¡PRENDIÓ!"
    zc = 1.22 + 0.10 * local(i, t)
    if t < L[1]["t0"]: zc = 1.38 - 0.08 * ease(t / L[1]["t0"])
    dy = 14 * math.sin(t * 0.9); sx = 0
    if i == 2 and 0.3 < local(2, t) < 0.5: sx = 10 * math.sin(t * 70)
    if i == 7 and 0.0 < local(7, t) < 0.2: sx = 12 * math.sin(t * 80)
    cr.save(); cr.translate(540 + sx, 1100 + dy); cr.scale(zc, zc); cr.translate(-540, -1100)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 7: explosion(cr, 540, 1080, local(7, t) * 4)
    if t < L[1]["t0"] - 0.05: gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1420, col, 38)
    chipb(cr, "objeto con historia", 360, 1740, AMA, 28)
    cr.set_source_rgba(1, 1, 1, 0.12); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*NAR); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        d = t - x["t0"]
        if 0 <= d < 0.1:
            cr.set_source_rgba(1, 0.9, 0.8, 0.16 * (1 - d / 0.1)); cr.paint()
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
