"""Motor de respaldo Pixel Diario — Short 'Donkey Kong iba a ser un juego de Popeye'.
Dibuja con cairo, sin personajes ni diseños de Nintendo ni de Popeye: vigas rojas genéricas, barriles genéricos,
lata verde sin etiqueta, siluetas de cuadritos genéricas, contrato genérico con sellos. Los nombres solo como texto.
Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["IBA A SER", "POPEYE"], "resalta": "POPEYE"}

# paleta nueva: arcade nocturno, morado casi negro + vigas rojo neón + cian (antes: día turquesa + pasto + sol)
FONDO1 = (0.05, 0.03, 0.12)
FONDO2 = (0.20, 0.07, 0.28)
VIGA = (0.93, 0.20, 0.30)
VIGA2 = (0.62, 0.08, 0.18)
CIAN = (0.20, 0.88, 0.96)
SOL = (1.0, 0.84, 0.18)
BARRIL = (0.74, 0.44, 0.18)
BARRIL2 = (0.48, 0.26, 0.10)
VERDE = (0.22, 0.80, 0.38)
VERDEO = (0.08, 0.50, 0.22)
ROJO = (0.92, 0.16, 0.18)
BLANCO = (1, 1, 1)
TINTA = (0.05, 0.04, 0.10)
GRIS = (0.55, 0.58, 0.64)
PAPEL = (0.97, 0.95, 0.88)
MORADO = (0.55, 0.32, 0.92)
ROSA = (1.0, 0.35, 0.70)

RESALTA = {1: ["Miyamoto,", "1981,", "Popeye,", "Olivia", "Brutus."], 2: ["Pero", "gorila,", "dama,", "Jumpman."],
           3: ["Mario."], 4: ["más", "raro."], 5: ["¿Por", "qué", "cambió?", "permiso"], 6: ["siguiente", "sí", "Popeye."],
           7: ["gorila", "villano", "Popeye."]}
COLRES = {1: CIAN, 2: SOL, 3: SOL, 4: ROSA, 5: ROJO, 6: VERDE, 7: SOL}


def ease(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)


def back(x):
    x = max(0, min(1, x)); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def lerp(a, b, u): return a + (b - a) * u


def linea_en(t):
    for k, x in enumerate(L[:-1]):
        if t < L[k + 1]["t0"] - 0.02: return x["i"]
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


# ---------- piezas genéricas ----------
def chipb(cr, s, x, y, color, size=34, txt=TINTA):
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: boleto de arcade rectangular
    con muescas a los lados y doble borde (antes: píldora redonda con borde blanco)."""
    x = max(x, 340)
    font(cr, size); tw = cr.text_extents(s).x_advance; w = min(tw + 80, W - 20 - x); h = size + 34
    def forma(dx, dy):
        r = h * 0.22
        cr.new_path(); cr.move_to(x + dx, y + dy); cr.line_to(x + w + dx, y + dy)
        cr.arc_negative(x + w + dx, y + h / 2 + dy, r, -math.pi / 2, math.pi / 2)
        cr.line_to(x + w + dx, y + h + dy); cr.line_to(x + dx, y + h + dy)
        cr.arc_negative(x + dx, y + h / 2 + dy, r, math.pi / 2, -math.pi / 2); cr.close_path()
    forma(6, 8); cr.set_source_rgba(0, 0, 0, 0.45); cr.fill()
    forma(0, 0); cr.set_source_rgb(*color); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
    cr.rectangle(x + 18, y + 8, w - 36, h - 16); cr.set_line_width(2.5); cr.set_dash([8, 6]); cr.stroke(); cr.set_dash([])
    z = size
    while cr.text_extents(s).x_advance > w - 60: z -= 2; font(cr, z)
    cr.set_source_rgb(*txt); cr.move_to(x + 40, y + h / 2 + z * 0.36); cr.show_text(s)


def viga(cr, x0, y0, x1, y1, grosor=46):
    """viga de andamio genérica con celosía."""
    ang = math.atan2(y1 - y0, x1 - x0); ln = math.hypot(x1 - x0, y1 - y0)
    cr.save(); cr.translate(x0, y0); cr.rotate(ang)
    cr.rectangle(0, -grosor / 2 + 6, ln, grosor); cr.set_source_rgba(0, 0, 0, 0.35); cr.fill()
    cr.rectangle(0, -grosor / 2, ln, grosor); cr.set_source_rgb(*VIGA); cr.fill()
    cr.set_source_rgb(*VIGA2); cr.set_line_width(6)
    k = 0
    while k * 46 < ln:
        cr.move_to(k * 46, -grosor / 2 + 4); cr.line_to(k * 46 + 23, grosor / 2 - 4); cr.line_to(k * 46 + 46, -grosor / 2 + 4); k += 1
    cr.stroke()
    cr.rectangle(0, -grosor / 2, ln, grosor); cr.set_source_rgb(*TINTA); cr.set_line_width(4); cr.stroke()
    cr.restore()


def barril(cr, x, y, r, rot):
    cr.save(); cr.translate(x, y); cr.rotate(rot)
    cr.arc(5, 7, r, 0, 2 * math.pi); cr.set_source_rgba(0, 0, 0, 0.35); cr.fill()
    cr.arc(0, 0, r, 0, 2 * math.pi); cr.set_source_rgb(*BARRIL); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
    cr.arc(0, 0, r * 0.62, 0, 2 * math.pi); cr.set_source_rgb(*BARRIL2); cr.set_line_width(r * 0.12); cr.stroke()
    for k in range(4):
        cr.move_to(0, 0); cr.line_to(r * 0.6 * math.cos(k * math.pi / 2), r * 0.6 * math.sin(k * math.pi / 2))
    cr.set_line_width(r * 0.08); cr.stroke()
    cr.restore()


def lata(cr, x, y, esc, rot):
    """lata verde lisa, sin etiqueta ni marca. y = base."""
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    cr.rectangle(-60 + 6, -170 + 8, 120, 170); cr.set_source_rgba(0, 0, 0, 0.35); cr.fill()
    g = cairo.LinearGradient(-60, 0, 60, 0)
    g.add_color_stop_rgb(0, *VERDEO); g.add_color_stop_rgb(0.4, *VERDE); g.add_color_stop_rgb(1, *VERDEO)
    cr.rectangle(-60, -170, 120, 170); cr.set_source(g); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
    cr.save(); cr.translate(0, -170); cr.scale(1, 0.25); cr.arc(0, 0, 60, 0, 2 * math.pi); cr.restore()
    cr.set_source_rgb(0.75, 0.78, 0.8); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(4); cr.stroke()
    for yy in (-150, -20):
        cr.move_to(-60, yy); cr.line_to(60, yy)
    cr.set_source_rgba(1, 1, 1, 0.35); cr.set_line_width(4); cr.stroke()
    cr.restore()


def silueta(cr, x, y, col, esc=1.0, alfa=1.0):
    """figura de cuadritos genérica (no es ningún personaje). y = pies."""
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    px = 22
    mapa = ["..XX..", "..XX..", ".XXXX.", "X.XX.X", "..XX..", ".X..X.", ".X..X."]
    for r, fila in enumerate(mapa):
        for c, ch in enumerate(fila):
            if ch == "X":
                cr.rectangle((c - 3) * px, (r - 7) * px, px - 2, px - 2)
    cr.set_source_rgba(*col, alfa); cr.fill()
    cr.restore()


def hoja(cr, x, y, w, h, rot=0.0, corte=0.0):
    """papel cuadriculado; corte separa las dos mitades (para la escena del contrato)."""
    for lado in (0, 1):
        cr.save(); cr.translate(x + (w / 2) * lado, y)
        dx = (-1 if lado == 0 else 1) * corte * 70; cr.translate(dx, corte * 30); cr.rotate(rot + (-1 if lado == 0 else 1) * corte * 0.12)
        cr.rectangle(6, 8, w / 2, h); cr.set_source_rgba(0, 0, 0, 0.35); cr.fill()
        cr.rectangle(0, 0, w / 2, h); cr.set_source_rgb(*PAPEL); cr.fill()
        cr.set_source_rgba(0.35, 0.55, 0.85, 0.35); cr.set_line_width(2)
        for gx in range(0, int(w / 2) + 1, 30): cr.move_to(gx, 0); cr.line_to(gx, h)
        for gy in range(0, int(h) + 1, 30): cr.move_to(0, gy); cr.line_to(w / 2, gy)
        cr.stroke()
        cr.restore()


def lineas_contrato(cr, x, y, w, corte=0.0):
    for k in range(7):
        ww = w * (0.8 if k % 3 else 0.55)
        for lado in (0, 1):
            dx = (-1 if lado == 0 else 1) * corte * 70
            a = x + 40 + dx; b = x + 40 + ww + dx
            m = x + w / 2 + dx
            if lado == 0: b = min(b, m - 6 + 0)
            else: a = max(a, m + 6)
            if b > a:
                cr.move_to(a, y + 60 + k * 44 + corte * 30); cr.line_to(b, y + 60 + k * 44 + corte * 30)
    cr.set_source_rgb(0.45, 0.45, 0.5); cr.set_line_width(8); cr.stroke()


def etiqueta(cr, s, x, y, size, col, tachado=0.0, esc=1.0):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    w = texto(cr, s, 0, 0, size, col, centro=True, borde=10)
    if tachado > 0:
        cr.move_to(-w / 2 - 10, -size * 0.32); cr.line_to(-w / 2 - 10 + (w + 20) * min(1, tachado), -size * 0.32)
        cr.set_source_rgb(*ROJO); cr.set_line_width(12); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()
    cr.restore()


def andamio(cr, t, rodar=True):
    """vigas en zigzag con un barril que baja rodando (solo y 840–1560)."""
    viga(cr, 360, 935, 1060, 985)
    viga(cr, 340, 1135, 1040, 1085)
    viga(cr, 360, 1305, 1060, 1355)
    viga(cr, -40, 1560, 1120, 1560, 60)
    if rodar:
        p = (t * 0.42) % 1.0
        if p < 0.33:
            u = p / 0.33; x = lerp(380, 1040, u); y = lerp(935, 985, u) - 56
        elif p < 0.66:
            u = (p - 0.33) / 0.33; x = lerp(1040, 360, u); y = lerp(1085, 1135, u) - 56
        else:
            u = (p - 0.66) / 0.34; x = lerp(380, 1040, u); y = lerp(1305, 1355, u) - 56
        barril(cr, x, y, 50, t * 6 * (1 if (p < 0.33 or p >= 0.66) else -1))


def escena_a(cr, t, i):
    """inicio y cierre: andamios rojos, barril rodando y la lata verde temblando. Nada en y 300–820."""
    andamio(cr, t)
    lata(cr, 900, 1530, 0.9, 0.06 * math.sin(t * 22))
    if i == 0:
        cr.save(); cr.translate(900, 1340)
        for k in range(3):
            a = -0.6 + k * 0.6 + 0.1 * math.sin(t * 9)
            cr.move_to(70 * math.sin(a), -70 * math.cos(a)); cr.line_to(100 * math.sin(a), -100 * math.cos(a))
        cr.set_source_rgb(*SOL); cr.set_line_width(8); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke(); cr.restore()


def escena(cr, t):
    i = linea_en(t)
    if i in (0, 7):
        escena_a(cr, t, i)
        return ("Donkey Kong · 1981", CIAN) if i == 0 else ("el villano de Popeye", SOL)
    u = local(i, t)
    if i == 1:
        e = back(u * 3)
        hoja(cr, 360, lerp(1700, 880, e), 680, 640, rot=-0.02)
        cols = [SOL, ROSA, MORADO]; noms = ["POPEYE", "OLIVIA", "BRUTUS"]
        for k in range(3):
            v = back((u - 0.25 - k * 0.15) * 5)
            if v > 0.01:
                cx = 470 + k * 230
                silueta(cr, cx, 1180, cols[k], 1.0 * v)
                etiqueta(cr, noms[k], cx, 1260, 38, cols[k], esc=v)
        tarjeta(cr, "BOCETO · 1981", 700, 900, 60, MORADO, esc=back((u - 0.05) * 4), rot=-0.04)
        return "Shigeru Miyamoto", CIAN
    if i == 2:
        filas = [("BRUTUS", "GORILA"), ("OLIVIA", "DAMA"), ("POPEYE", "JUMPMAN")]
        for k, (a, b) in enumerate(filas):
            y = 960 + k * 190
            v = (u - k * 0.3) / 0.3
            etiqueta(cr, a, 500, y, 58, BLANCO, tachado=max(0, v * 1.6))
            if v > 0.45:
                ee = back((v - 0.45) * 3)
                cr.move_to(640, y - 22); cr.line_to(700, y - 22); cr.set_source_rgb(*CIAN); cr.set_line_width(10); cr.stroke()
                cr.move_to(720, y - 22); cr.line_to(692, y - 44); cr.line_to(692, y); cr.close_path(); cr.fill()
                etiqueta(cr, b, 880, y, 58, SOL, esc=ee)
        return ("cambio de reparto"), SOL
    if i == 3:
        andamio(cr, t, rodar=False)
        fl = math.cos(math.pi * ease((u - 0.25) / 0.4))
        cr.save(); cr.translate(690, 1110); cr.scale(max(0.02, abs(fl)), 1)
        cr.arc(0, 0, 230, 0, 2 * math.pi); cr.set_source_rgb(*SOL); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(10); cr.stroke()
        cr.arc(0, 0, 195, 0, 2 * math.pi); cr.set_source_rgb(0.85, 0.62, 0.05); cr.set_line_width(6); cr.stroke()
        texto(cr, "JUMPMAN" if fl > 0 else "MARIO", 0, 28, 84 if fl > 0 else 104, BLANCO if fl > 0 else ROJO, borde=10)
        cr.restore()
        return ("Jumpman → Mario"), SOL
    if i == 4:
        # barril que rueda hacia la cámara
        vv = (t - L[4]["t0"]) / (L[5]["t0"] - L[4]["t0"])
        viga(cr, -40, 1560, 1120, 1560, 60)
        r = lerp(60, 420, ease(vv) ** 1.4)
        barril(cr, 690, 1250 - r * 0.2, r, t * 5)
        return "y eso no es todo", ROSA
    if i == 5:
        corte = ease((u - 0.45) / 0.25)
        hoja(cr, 380, 880, 620, 560, corte=corte)
        lineas_contrato(cr, 380, 880, 620, corte)
        if corte < 0.05: texto(cr, "CONTRATO", 690, 940, 52, TINTA, borde=0)
        if u < 0.4:
            texto(cr, "¿?", 690, 1300, 300 * back(u * 4) + 1, SOL, borde=16)
        else:
            v = (u - 0.4) / 0.2
            esc = lerp(2.4, 0.95, ease(v)) if v < 1 else 0.95
            sello(cr, "SIN PERMISO", 690, 1250, esc * 0.85, -0.12, min(1, v * 2), ROJO)
        return ("¿por qué?" if u < 0.4 else "sin permiso"), ROJO
    if i == 6:
        corte = 1 - ease(u / 0.3)
        hoja(cr, 380, 880, 620, 560, corte=corte)
        lineas_contrato(cr, 380, 880, 620, corte)
        if corte < 0.05: texto(cr, "CONTRATO", 690, 940, 52, TINTA, borde=0)
        tarjeta(cr, "1982", 860, 1480, 80, MORADO, esc=back(u * 4), rot=0.06)
        if u > 0.35:
            v = (u - 0.35) / 0.2
            sello(cr, "APROBADO", 690, 1250, lerp(2.4, 0.9, ease(v)) * 0.9, 0.08, min(1, v * 2), VERDEO)
        return "un año después", VERDE
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *FONDO1); g.add_color_stop_rgb(0.6, *FONDO2); g.add_color_stop_rgb(1, *FONDO1)
    cr.set_source(g); cr.paint()
    # estrellas que titilan + rejilla de neón en perspectiva abajo (fondo nuevo; antes cielo con sol y nubes)
    for k in range(60):
        x = (k * 173) % W; y = (k * 311) % 1250
        a = 0.3 + 0.5 * abs(math.sin(t * 2 + k))
        cr.rectangle(x, y, 5, 5); cr.set_source_rgba(1, 1, 1, a); cr.fill()
    cr.set_source_rgba(*ROSA, 0.25); cr.set_line_width(3)
    for k in range(-8, 9):
        cr.move_to(W / 2 + k * 40, 1250); cr.line_to(W / 2 + k * 260, H)
    off = (t * 60) % 80
    for k in range(10):
        y = 1250 + (k * 80 + off) ** 1.08 * 0.85
        cr.move_to(0, y); cr.line_to(W, y)
    cr.stroke()
    # líneas de barrido tipo pantalla
    cr.set_source_rgba(0, 0, 0, 0.12)
    for y in range(0, H, 6): cr.rectangle(0, y, W, 2)
    cr.fill()


def gancho(cr, t):
    # entrada nueva: letrero de neón; texto completo desde el cuadro 0, con borde cian/rosa que parpadea
    # y un leve pulso de escala (antes: placas doradas/verdes con palabras que rebotan)
    ys = [600, 800]
    for k, (s, y) in enumerate(zip(GANCHO["lineas"], ys)):
        z = 175 if k == 0 else 200
        font(cr, z)
        while cr.text_extents(s).x_advance > 940: z -= 4; font(cr, z)
        wtot = cr.text_extents(s).x_advance
        esc = 1 + 0.03 * math.sin(t * 6 + k * 1.5)
        cr.save(); cr.translate(W / 2, y - z * 0.33); cr.scale(esc, esc); cr.translate(-W / 2, -(y - z * 0.33))
        x0 = W / 2 - wtot / 2
        neon = CIAN if k == 0 else ROSA
        brillo = 0.75 + 0.25 * (1 if math.sin(t * 13 + k) > -0.7 else 0.3)
        rrect(cr, x0 - 36, y - z * 0.88, wtot + 72, z * 1.12, 26); cr.set_source_rgba(0.04, 0.02, 0.10, 0.92); cr.fill()
        for lw, al in ((26, 0.18), (14, 0.35), (6, 1.0)):
            rrect(cr, x0 - 36, y - z * 0.88, wtot + 72, z * 1.12, 26); cr.set_source_rgba(*neon, al * brillo); cr.set_line_width(lw); cr.stroke()
        col = SOL if GANCHO["resalta"] in s else BLANCO
        texto(cr, s, W / 2, y, z, col, centro=True, borde=20)
        cr.restore()


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: empuje lento hacia adelante con inclinación alterna por toma (antes: paneo lateral con rebote)
    d = max(0, t - L[i]["t0"])
    zc = 1.0 + 0.07 * ease(d / 3.5)
    rot = (0.018 if i % 2 else -0.018) * ease(d / 2.0)
    cr.save()
    cr.rectangle(0, 830, W, 470); cr.rectangle(320, 1300, W - 320, 360); cr.rectangle(0, 1660, W, 40); cr.clip()
    cr.translate(690, 1220); cr.rotate(rot); cr.scale(zc, zc); cr.translate(-690, -1220)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1575, col if col else SOL, 40)
    chipb(cr, "Iba a ser otra cosa", 340, 1750, CIAN, 34)
    cr.set_source_rgba(0, 0, 0, 0.25); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*CIAN); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        dd = t - x["t0"]
        if 0 <= dd < 0.1:
            cr.set_source_rgba(1, 1, 1, 0.35 * (1 - dd / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0, 1.5] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [10.0, 12.5, 14.0, 16.5, 19.5, 21.0, 22.8, 26.5, round(L[-1]["t1"] - 0.3, 1)]
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
