"""Motor de respaldo Pixel Diario — Short 'Tetris no le pagó nada a su creador'.
Dibuja con cairo, sin logos ni diseños reconocibles: piezas geométricas de 4
cuadros (tetrominós genéricos), una figura geométrica genérica y edificios
genéricos. Sin retratos. Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["CREADOR DE", "TETRIS:", "0 DÓLARES"], "resalta": "0 DÓLARES"}

# paleta: pizarra verde noche con piezas de colores (antes: noche de desierto ciruela/arena)
BG = (0.035, 0.085, 0.075)
REJ = (0.10, 0.22, 0.19)
AMA = (1.0, 0.85, 0.2)
ROJO = (1.0, 0.27, 0.27)
CIAN = (0.3, 0.9, 1.0)
VERDE = (0.4, 0.95, 0.5)
MAG = (0.85, 0.45, 1.0)
NAR = (1.0, 0.6, 0.2)
BLANCO = (1, 1, 1)
OSCURO = (0.02, 0.04, 0.035)
COLS = [CIAN, AMA, MAG, VERDE, ROJO, NAR]
PIEZAS = {"I": [(0, 0), (1, 0), (2, 0), (3, 0)], "O": [(0, 0), (1, 0), (0, 1), (1, 1)], "T": [(0, 0), (1, 0), (2, 0), (1, 1)],
          "S": [(1, 0), (2, 0), (0, 1), (1, 1)], "Z": [(0, 0), (1, 0), (1, 1), (2, 1)], "L": [(0, 0), (0, 1), (0, 2), (1, 2)]}

RESALTA = {1: ["Alexey", "Pajitnov", "Moscú,"], 2: ["mundo."], 3: ["ni", "un", "rublo."], 4: ["suyo."], 5: ["vendió.", "perdió."],
           6: ["inventado…", "¿de", "quién", "era?"], 7: ["gobierno", "soviético."], 8: ["Estado,", "Estado."],
           9: ["mil", "novecientos", "noventa", "seis", "cobrar."], 10: ["cero", "dólares."]}
COLRES = {3: ROJO, 4: CIAN, 5: ROJO, 7: ROJO, 8: ROJO, 9: VERDE}


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
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: relleno oscuro con barra de color a la izquierda."""
    x = max(x, 340)
    font(cr, size); w = cr.text_extents(s).x_advance + 64
    cr.rectangle(x, y, w, size + 30); cr.set_source_rgba(*OSCURO, 0.88); cr.fill()
    cr.rectangle(x, y, 14, size + 30); cr.set_source_rgb(*color); cr.fill()
    cr.set_source_rgb(*BLANCO); cr.move_to(x + 36, y + size + 8); cr.show_text(s)


# ---------- dibujos genéricos ----------
def celda(cr, x, y, c, col, alpha=1.0):
    cr.rectangle(x, y, c, c); cr.set_source_rgba(*col, alpha); cr.fill()
    cr.set_source_rgba(1, 1, 1, 0.35 * alpha); cr.rectangle(x, y, c, c * 0.18); cr.fill()
    cr.set_source_rgba(0, 0, 0, 0.3 * alpha); cr.rectangle(x, y + c * 0.82, c, c * 0.18); cr.fill()
    cr.set_source_rgba(*OSCURO, alpha); cr.set_line_width(3); cr.rectangle(x, y, c, c); cr.stroke()


def pieza(cr, tipo, x, y, c, col, rot=0.0, alpha=1.0, esc=1.0):
    cel = PIEZAS[tipo]
    cx = (max(p[0] for p in cel) + 1) / 2; cy = (max(p[1] for p in cel) + 1) / 2
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    for (i, j) in cel:
        celda(cr, (i - cx) * c, (j - cy) * c, c, col, alpha)
    cr.restore()


def pozo(cr, t, u):
    """pozo con piezas que caen y se apilan; x 390–690, y 850–1290"""
    X0, Y0, C = 380, 900, 26
    cr.set_source_rgba(*REJ, 0.6); cr.rectangle(X0, Y0, 260, 364); cr.fill()
    cr.set_source_rgba(1, 1, 1, 0.06); cr.set_line_width(1)
    for k in range(11): cr.move_to(X0 + k * C, Y0); cr.line_to(X0 + k * C, Y0 + 364)
    for k in range(15): cr.move_to(X0, Y0 + k * C); cr.line_to(X0 + 260, Y0 + k * C)
    cr.stroke()
    rnd = random.Random(7)
    for r in range(3):
        for k in range(10):
            if rnd.random() < 0.8: celda(cr, X0 + k * C, Y0 + 364 - (r + 1) * C, C, COLS[rnd.randrange(6)])
    cyc = (t * 0.9) % 1
    pieza(cr, "T", X0 + 130 + 26 * math.floor(math.sin(t * 2) * 2), Y0 + 20 + cyc * 250, C, MAG, rot=(math.pi / 2) * math.floor(t * 1.5))
    cr.set_source_rgb(*BLANCO); cr.set_line_width(6); cr.rectangle(X0 - 3, Y0, 266, 367); cr.stroke()


def contador(cr, s, x, y, col, t, size=130):
    sh = 6 * math.sin(t * 9)
    rrect(cr, x - 135, y - 110, 270, 170, 20); cr.set_source_rgba(*OSCURO, 0.9); cr.fill_preserve()
    cr.set_source_rgb(*col); cr.set_line_width(6); cr.stroke()
    texto(cr, s, x, y + 20 + sh * 0.3, size, col, borde=0)


def figura(cr, x, y, t, color=CIAN, esc=1.0, alpha=1.0):
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    bob = 4 * math.sin(t * 3)
    cr.set_source_rgba(*color, alpha)
    rrect(cr, -45, -150 + bob, 90, 120, 26); cr.fill()
    cr.new_sub_path(); cr.arc(0, -190 + bob, 34, 0, 2 * math.pi); cr.fill()
    cr.rectangle(-36, -40, 26, 40); cr.rectangle(10, -40, 26, 40); cr.fill()
    cr.restore()


def monitor(cr, x, y, t):
    rrect(cr, x - 210, y - 170, 420, 320, 24); cr.set_source_rgb(0.75, 0.72, 0.62); cr.fill()
    rrect(cr, x - 175, y - 140, 350, 240, 14); cr.set_source_rgb(0.02, 0.12, 0.05); cr.fill()
    cr.save(); rrect(cr, x - 175, y - 140, 350, 240, 14); cr.clip()
    for k in range(5):
        yy = y - 140 + ((t * 70 + k * 55) % 260)
        font(cr, 30); cr.set_source_rgb(0.3, 1, 0.4); cr.move_to(x - 120 + (k * 47) % 200, yy); cr.show_text("[][]")
    cr.restore()
    cr.rectangle(x - 60, y + 150, 120, 30); cr.set_source_rgb(0.6, 0.58, 0.5); cr.fill()


def cupulas(cr, alpha=0.5):
    cr.set_source_rgba(*REJ, alpha)
    for (cx, w, h) in [(180, 90, 260), (330, 70, 200), (760, 80, 230), (900, 100, 280)]:
        base = 1290
        cr.rectangle(cx - w / 2, base - h, w, h); cr.fill()
        cr.move_to(cx - w * 0.65, base - h)
        cr.curve_to(cx - w * 0.8, base - h - w * 0.8, cx, base - h - w * 0.9, cx, base - h - w * 1.4)
        cr.curve_to(cx, base - h - w * 0.9, cx + w * 0.8, base - h - w * 0.8, cx + w * 0.65, base - h); cr.close_path(); cr.fill()


def globo(cr, x, y, r, t):
    cr.new_sub_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgb(0.12, 0.35, 0.55); cr.fill()
    cr.set_source_rgba(1, 1, 1, 0.35); cr.set_line_width(3)
    for k in range(6):
        ph = (t * 0.6 + k / 6) % 1; ww = r * math.cos(ph * math.pi)
        cr.save(); cr.translate(x, y); cr.scale(max(abs(ww) / r, 0.01), 1); cr.new_sub_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.restore(); cr.stroke()
    for k in (-0.5, 0, 0.5):
        hw = r * math.sqrt(1 - k * k); cr.move_to(x - hw, y + k * r); cr.line_to(x + hw, y + k * r)
    cr.stroke()


def etiqueta(cr, s, x, y, size, color, tachado=0.0, rot=0.0, esc=1.0):
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 60
    cr.rectangle(-w / 2, -size * 0.95, w, size * 1.5); cr.set_source_rgb(*BLANCO); cr.fill()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 30, size * 0.25); cr.show_text(s)
    if tachado > 0:
        cr.set_source_rgb(*ROJO); cr.set_line_width(12)
        cr.move_to(-w / 2 + 15, 0); cr.line_to(-w / 2 + 15 + (w - 30) * tachado, -size * 0.1); cr.stroke()
    cr.restore()


def sello(cr, lineas, x, y, size, color, u):
    k = ease(u * 4); esc = 2.2 - 1.2 * k
    cr.save(); cr.translate(x, y); cr.rotate(-0.15); cr.scale(esc, esc)
    font(cr, size); w = max(cr.text_extents(s).x_advance for s in lineas) + 60
    h = size * 1.25 * len(lineas) + 30
    cr.rectangle(-w / 2, -h / 2, w, h); cr.set_source_rgba(*OSCURO, 0.92 * k); cr.fill_preserve()
    cr.set_source_rgba(*color, k); cr.set_line_width(9); cr.stroke()
    for n, s in enumerate(lineas):
        ww = cr.text_extents(s).x_advance
        cr.move_to(-ww / 2, -h / 2 + 15 + size * 1.05 + n * size * 1.25); cr.show_text(s)
    cr.restore()


def edificio(cr, x, y, col):
    cr.set_source_rgb(*col)
    cr.move_to(x - 150, y - 200); cr.line_to(x, y - 280); cr.line_to(x + 150, y - 200); cr.close_path(); cr.fill()
    cr.rectangle(x - 150, y - 200, 300, 20); cr.fill()
    for k in range(5): cr.rectangle(x - 130 + k * 58, y - 175, 28, 155); cr.fill()
    cr.rectangle(x - 160, y - 20, 320, 20); cr.fill()


def moneda(cr, x, y, r, s, rot=0.0):
    cr.save(); cr.translate(x, y); cr.scale(max(abs(math.cos(rot)), 0.08), 1)
    cr.new_sub_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.set_source_rgb(*AMA); cr.fill_preserve()
    cr.set_source_rgb(0.7, 0.5, 0.05); cr.set_line_width(5); cr.stroke()
    font(cr, r * 1.1); e = cr.text_extents(s); cr.move_to(-e.x_advance / 2, r * 0.38); cr.set_source_rgb(0.6, 0.42, 0.02); cr.show_text(s)
    cr.restore()


def flecha(cr, x1, y, x2, col, u=1.0):
    xe = lerp(x1, x2, ease(u))
    cr.set_source_rgb(*col); cr.set_line_width(10); cr.move_to(x1, y); cr.line_to(xe, y); cr.stroke()
    cr.move_to(xe + 10, y); cr.line_to(xe - 18, y - 20); cr.line_to(xe - 18, y + 20); cr.close_path(); cr.fill()


def escena(cr, t):
    i = linea_en(t)
    if t < L[1]["t0"] or i == 10:  # A y cierre en bucle: misma imagen
        pozo(cr, t, 0)
        contador(cr, "$0", 790, 1080, AMA, t, 120)
        return ("cero dólares", AMA) if i == 10 else (None, None)
    if i == 1:
        u = local(1, t)
        cupulas(cr, 0.5 + 0.4 * ease(u * 2))
        monitor(cr, 540, 1080 + 30 * (1 - ease(u * 2)), t)
        return "Moscú · años 80", CIAN
    if i == 2:
        u = local(2, t)
        globo(cr, 540, 1080, 170, t)
        rnd = random.Random(5)
        for k in range(10):
            a = rnd.uniform(0, 2 * math.pi); d = 60 + (u * 1.3 + k / 10) % 1 * 420
            pieza(cr, rnd.choice(list(PIEZAS)), 540 + d * math.cos(a), 1080 + d * 0.55 * math.sin(a), 26, COLS[k % 6], rot=t * 2 + k)
        return "conquista el mundo", VERDE
    if i == 3:
        u = local(3, t)
        figura(cr, 440, 1270, t, CIAN, 1.0)
        for k in range(6):
            mx = 600 + k * 70; my = 880 + ((t * 260 + k * 90) % 420)
            moneda(cr, mx, my, 30, "₽", t * 5 + k)
        contador(cr, "0 ₽", 440, 980, ROJO, t * (3 if u > 0.4 else 0.3), 90)
        return "ni un rublo", ROJO
    if i == 4:
        u = local(4, t)
        figura(cr, 420, 1270, t, CIAN, 0.95)
        px = lerp(540, 790, ease(u * 1.5))
        pieza(cr, "T", px, 1150, 60, MAG, rot=0.1 * math.sin(t * 3))
        etiqueta(cr, "DUEÑO: ???", 720, 960, 52, BG, rot=-0.05, esc=0.5 + 0.5 * ease(u * 3))
        return "¿no era suyo?", CIAN
    if i == 5:
        u = local(5, t)
        etiqueta(cr, "VENDIDO", 540, 980, 80, BG, tachado=ease((u - 0.1) * 3), rot=-0.04)
        if u > 0.45: etiqueta(cr, "PERDIDO", 540, 1180, 80, BG, tachado=ease((u - 0.55) * 3), rot=0.04, esc=ease((u - 0.45) * 5))
        return "ni vendido ni perdido", ROJO
    if i == 6:
        u = local(6, t)
        figura(cr, 430, 1270, t, CIAN, 1.0)
        bx, by = 430, 960 + 8 * math.sin(t * 5)
        cr.new_sub_path(); cr.arc(bx, by, 40, 0, 2 * math.pi); cr.set_source_rgb(*AMA); cr.fill()
        cr.rectangle(bx - 18, by + 38, 36, 24); cr.set_source_rgb(0.7, 0.7, 0.7); cr.fill()
        pieza(cr, "L", 560, 1180, 46, NAR, rot=0.2 * math.sin(t * 2))
        texto(cr, "?", 790, 1150, 260 + 30 * math.sin(t * 6), ROJO, borde=10)
        return "¿de quién era?", AMA
    if i == 7:
        u = local(7, t)
        pieza(cr, "T", 540, 1180, 70, MAG)
        sello(cr, ["PROPIEDAD", "DEL ESTADO"], 540, 1000, 62, ROJO, u)
        return "del gobierno soviético", ROJO
    if i == 8:
        u = local(8, t)
        figura(cr, 430, 1270, t, CIAN, 0.75)
        flecha(cr, 470, 1150, 560, BLANCO, u * 3)
        edificio(cr, 730, 1270, (0.75, 0.75, 0.72))
        texto(cr, "ESTADO", 730, 960, 50, ROJO, borde=6)
        if u > 0.45:
            k = ease((u - 0.45) * 3)
            pieza(cr, "T", 730, 880, 34, MAG, esc=k)
            flecha(cr, 560, 880, 660, BLANCO, k)
        return "trabajaba para el Estado", ROJO
    if i == 9:
        u = local(9, t)
        anio = int(lerp(1984, 1996, ease(u * 1.6)))
        texto(cr, f"{anio}", 540, 1000, 150, VERDE, borde=10)
        k = ease((u - 0.45) * 3)
        cr.set_source_rgb(*AMA); cr.set_line_width(16)
        cr.new_sub_path(); cr.arc(540, 1120 - 30 * k, 50, math.pi, 2 * math.pi); cr.stroke()
        rrect(cr, 470, 1120, 140, 110, 14); cr.fill()
        if u > 0.55:
            for n in range(5):
                mx = 300 + n * 120 + (200 if n > 1 else 0); my = 1050 + ((t * 300 + n * 70) % 240)
                moneda(cr, mx, my, 28, "$", t * 6 + n)
        return "1996: recupera los derechos", VERDE
    return None, None


def fondo(cr, t):
    cr.set_source_rgb(*BG); cr.paint()
    cr.set_source_rgba(*REJ, 0.55); cr.set_line_width(2)
    off = (t * 20) % 60
    for x in range(0, W + 60, 60): cr.move_to(x, 0); cr.line_to(x, H)
    for y in range(-60, H + 60, 60): cr.move_to(0, y + off); cr.line_to(W, y + off)
    cr.stroke()
    rnd = random.Random(2)
    for k in range(9):
        x = rnd.uniform(40, 1040); sp = rnd.uniform(25, 60)
        y = (rnd.uniform(0, H) + t * sp) % (H + 200) - 100
        pieza(cr, rnd.choice(list(PIEZAS)), x, y, 22, COLS[k % 6], rot=rnd.uniform(0, 6), alpha=0.12)


def gancho(cr, t):
    # entrada nueva: las líneas caen desde arriba como piezas y rebotan (antes: deslizar por los lados); cuadro 0 completo
    ys = [450, 600, 790]; sizes = [110, 150, 160]
    for k, (s, y, z) in enumerate(zip(GANCHO["lineas"], ys, sizes)):
        u = 0.85 + 0.15 * ease((t - k * 0.08) / 0.3)
        dy = -(1 - u) * 260 + (8 * math.sin(t * 20) * (1 - ease(t / 0.6)) if t < 0.6 else 0)
        col = AMA if s == GANCHO["resalta"] else BLANCO
        texto(cr, s, W / 2, y + dy, z, col, borde=14)


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
    # cámara: zoom + leve inclinación que oscila (antes: paneo lateral); sacudida en el sello
    zc = 1.3 + 0.06 * local(i, t)
    if t < L[1]["t0"]: zc = 1.3 + 0.09 * (t / L[1]["t0"])
    rot = 0.012 * math.sin(t * 0.8); sx = 0
    if i == 7 and 0.15 < local(7, t) < 0.35: sx = 9 * math.sin(t * 70)
    cr.save(); cr.translate(540 + sx, 1100); cr.rotate(rot); cr.scale(zc, zc); cr.translate(-540, -1100)
    eti, col = escena(cr, t)
    cr.restore()
    if t < L[1]["t0"] - 0.05: gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1380, col, 40)
    chipb(cr, "número que no cuadra", 360, 1730, AMA, 30)
    cr.set_source_rgba(1, 1, 1, 0.12); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*AMA); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        d = t - x["t0"]
        if 0 <= d < 0.1:
            cr.set_source_rgba(1, 1, 0.8, 0.16 * (1 - d / 0.1)); cr.paint()
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
