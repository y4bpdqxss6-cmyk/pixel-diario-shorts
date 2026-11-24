"""Motor de respaldo Pixel Diario — Short 'Zelda se llama así por la esposa de un autor'.
Dibuja con cairo objetos genéricos: corona de triángulos, etiqueta colgante, cartucho sin marca, libro, sello,
reloj de arena, máquina de escribir, copas y serpentinas art déco. Sin Zelda, Link, Trifuerza, logos ni nada de la saga;
sin fotos ni dibujos de Zelda Fitzgerald. Nombres solo como texto. Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, random, subprocess, sys
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["UN NOMBRE", "PRESTADO"], "resalta": "PRESTADO"}

# paleta nueva: noche art déco (azul medianoche + dorado + crema) (antes: bosque nocturno verde musgo + amarillo + lila)
FONDO1 = (0.04, 0.05, 0.13)
FONDO2 = (0.10, 0.10, 0.26)
ORO = (1.0, 0.80, 0.30)
SOL = ORO
AMBAR = ORO
CREMA = (0.98, 0.94, 0.84)
ROSA = (1.0, 0.55, 0.62)
TURQ = (0.40, 0.88, 0.85)
ROJO = (0.92, 0.25, 0.25)
BLANCO = (1, 1, 1)
TINTA = (0.03, 0.03, 0.08)
GRIS = (0.55, 0.56, 0.62)

RESALTA = {1: ["ochenta.", "Miyamoto", "nombre."], 2: ["libro", "ilustrado"], 3: ["no", "convenció…", "pero", "sí."],
           4: ["raro:", "belleza", "eterna."], 5: ["nombre?"], 6: ["Zelda.", "Zelda", "Fitzgerald,", "gran", "Gatsby."],
           7: ["princesa", "mujer", "real."]}
COLRES = {1: ORO, 2: TURQ, 3: ROSA, 4: ORO, 5: ORO, 6: ORO, 7: ROSA}
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
    acc = 0
    if len(lineas) > 4:  # frases largas: en dos páginas de 3 líneas
        mitad = 3; prim = sum(len(p) + 1 for ln in lineas[:mitad] for p in ln)
        if vis > prim + 4: acc = prim; lineas = lineas[mitad:]
        else: lineas = lineas[:mitad]
    y = 430 if len(lineas) <= 2 else 360
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
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: listón con cola en V y doble
    filete dorado (antes: placa con esquinas cortadas y barrita lateral)."""
    x = max(x, 340)
    font(cr, size); tw = cr.text_extents(s).x_advance; w = min(tw + 100, W - 20 - x); h = size + 34; c = 22
    def forma(dx, dy):
        cr.new_path(); cr.move_to(x + dx, y + dy); cr.line_to(x + dx + w, y + dy); cr.line_to(x + dx + w - c, y + dy + h / 2)
        cr.line_to(x + dx + w, y + dy + h); cr.line_to(x + dx, y + dy + h); cr.line_to(x + dx + c, y + dy + h / 2); cr.close_path()
    forma(6, 8); cr.set_source_rgba(0, 0, 0, 0.5); cr.fill()
    forma(0, 0); cr.set_source_rgb(*color); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(4); cr.stroke()
    cr.move_to(x + c + 6, y + 7); cr.line_to(x + w - c - 6, y + 7); cr.move_to(x + c + 6, y + h - 7); cr.line_to(x + w - c - 6, y + h - 7)
    cr.set_source_rgba(*TINTA, 0.5); cr.set_line_width(2); cr.stroke()
    z = size
    while cr.text_extents(s).x_advance > w - 70: z -= 2; font(cr, z)
    cr.set_source_rgb(*txt); cr.move_to(x + 42, y + h / 2 + z * 0.36); cr.show_text(s)


def corona(cr, x, y, esc, t, brillo=0.0):
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    pts = [(-150, 0), (-150, -90), (-100, -40), (-50, -130), (0, -50), (50, -130), (100, -40), (150, -90), (150, 0)]
    cr.move_to(-140 + 8, 10)
    for px, py in pts: cr.line_to(px + 8, py + 10)
    cr.close_path(); cr.set_source_rgba(0, 0, 0, 0.45); cr.fill()
    cr.move_to(*pts[0])
    for px, py in pts[1:]: cr.line_to(px, py)
    cr.close_path(); cr.set_source_rgb(*ORO); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
    cr.rectangle(-150, -30, 300, 30); cr.set_source_rgb(0.85, 0.62, 0.18); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.stroke()
    for k, (px, py) in enumerate([(-150, -90), (-50, -130), (50, -130), (150, -90)]):
        cr.arc(px, py, 14, 0, 2 * math.pi); cr.set_source_rgb(*(ROSA if k % 2 else TURQ)); cr.fill_preserve()
        cr.set_source_rgb(*TINTA); cr.set_line_width(4); cr.stroke()
    if brillo > 0:
        for k in range(6):
            a = t * 2 + k * math.pi / 3; r = 200 + 20 * math.sin(t * 4 + k)
            sx, sy = r * math.cos(a), -60 + r * 0.6 * math.sin(a)
            cr.move_to(sx - 16, sy); cr.line_to(sx + 16, sy); cr.move_to(sx, sy - 16); cr.line_to(sx, sy + 16)
            cr.set_source_rgba(*BLANCO, brillo * (0.5 + 0.5 * math.sin(t * 6 + k))); cr.set_line_width(5); cr.stroke()
    cr.restore()


def etiqueta(cr, x, y, ang, s, esc=1.0, col=CREMA):
    """etiqueta colgante de cartón con hilo; (x, y) = punto de donde cuelga."""
    cr.save(); cr.translate(x, y); cr.rotate(ang); cr.scale(esc, esc)
    cr.move_to(0, 0); cr.line_to(0, 70); cr.set_source_rgb(*CREMA); cr.set_line_width(4); cr.stroke()
    def forma(dx, dy):
        cr.new_path(); cr.move_to(dx, 60 + dy); cr.line_to(150 + dx, 110 + dy); cr.line_to(150 + dx, 260 + dy)
        cr.line_to(-150 + dx, 260 + dy); cr.line_to(-150 + dx, 110 + dy); cr.close_path()
    forma(8, 10); cr.set_source_rgba(0, 0, 0, 0.45); cr.fill()
    forma(0, 0); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()
    cr.arc(0, 95, 12, 0, 2 * math.pi); cr.set_source_rgb(*TINTA); cr.fill()
    if s:
        font(cr, 74); w = cr.text_extents(s).x_advance
        cr.move_to(-w / 2, 215); cr.set_source_rgb(*TINTA); cr.show_text(s)
    cr.restore()


def cartucho(cr, x, y, esc, s, alfa_txt=1.0):
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    cr.move_to(-160 + 10, -200 + 12); cr.line_to(160 + 10, -200 + 12); cr.line_to(160 + 10, 200 + 12); cr.line_to(-160 + 10, 200 + 12); cr.close_path()
    cr.set_source_rgba(0, 0, 0, 0.45); cr.fill()
    cr.move_to(-160, -200); cr.line_to(130, -200); cr.line_to(160, -170); cr.line_to(160, 200); cr.line_to(-160, 200); cr.close_path()
    cr.set_source_rgb(0.62, 0.64, 0.70); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
    for k in range(5): cr.rectangle(-120 + k * 52, 160, 30, 30)
    cr.set_source_rgba(*TINTA, 0.5); cr.fill()
    rrect(cr, -120, -150, 240, 260, 14); cr.set_source_rgb(*CREMA); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
    if s: texto(cr, s, 0, 10, 110, ORO, borde=8, alpha=alfa_txt)
    cr.restore()


def libro(cr, x, y, esc, apertura, t, dibujos=1.0):
    """libro genérico; apertura 0 = cerrado, 1 = abierto con dibujos de líneas simples."""
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    a = ease(apertura)
    cr.rectangle(-300 * a - 10 + 10, -200 + 12, 600 * a + 20 if a > 0.05 else 300, 400); cr.set_source_rgba(0, 0, 0, 0.45); cr.fill()
    if a < 0.05:
        rrect(cr, -150, -200, 300, 400, 10); cr.set_source_rgb(0.55, 0.20, 0.30); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
        rrect(cr, -110, -150, 220, 300, 6); cr.set_source_rgb(*ORO); cr.set_line_width(5); cr.stroke()
    else:
        for s_ in (-1, 1):
            cr.move_to(0, -200); cr.line_to(s_ * 300 * a, -190); cr.line_to(s_ * 300 * a, 200); cr.line_to(0, 210); cr.close_path()
            cr.set_source_rgb(*CREMA); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()
        if dibujos > 0 and a > 0.8:
            cr.set_source_rgba(*TINTA, dibujos); cr.set_line_width(5)
            # castillo de líneas (página izquierda)
            cr.move_to(-250, 120); cr.line_to(-250, 0); cr.line_to(-220, 0); cr.line_to(-220, -30); cr.line_to(-190, -30); cr.line_to(-190, 0)
            cr.line_to(-110, 0); cr.line_to(-110, -30); cr.line_to(-80, -30); cr.line_to(-80, 0); cr.line_to(-50, 0); cr.line_to(-50, 120)
            cr.move_to(-170, 120); cr.line_to(-170, 70); cr.arc(-150, 70, 20, math.pi, 0); cr.line_to(-130, 120); cr.stroke()
            # espada genérica (página derecha)
            sw = 0.1 * math.sin(t * 3)
            cr.save(); cr.translate(150, 20); cr.rotate(sw)
            cr.move_to(0, -150); cr.line_to(16, -120); cr.line_to(16, 60); cr.line_to(-16, 60); cr.line_to(-16, -120); cr.close_path(); cr.stroke()
            cr.move_to(-60, 60); cr.line_to(60, 60); cr.move_to(0, 60); cr.line_to(0, 130); cr.stroke(); cr.restore()
    cr.restore()


def reloj_arena(cr, x, y, esc, t):
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    for yy in (-150, 150):
        rrect(cr, -110, yy - 15, 220, 30, 8); cr.set_source_rgb(0.55, 0.36, 0.20); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
    cr.move_to(-85, -135); cr.curve_to(-85, -40, -12, -20, -12, 0); cr.curve_to(-12, 20, -85, 40, -85, 135)
    cr.line_to(85, 135); cr.curve_to(85, 40, 12, 20, 12, 0); cr.curve_to(12, -20, 85, -40, 85, -135); cr.close_path()
    cr.set_source_rgba(0.75, 0.88, 1.0, 0.35); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
    # arena arriba que nunca baja: se mantiene llena y el hilito cae sin vaciarla
    cr.move_to(-70, -110); cr.line_to(70, -110); cr.line_to(14, -20); cr.line_to(-14, -20); cr.close_path(); cr.set_source_rgb(*ORO); cr.fill()
    cr.move_to(-60, 130); cr.line_to(60, 130); cr.line_to(0, 95); cr.close_path(); cr.fill()
    for k in range(6):
        p = (t * 2.5 + k / 6) % 1
        cr.arc(0, -10 + p * 110, 3, 0, 2 * math.pi); cr.fill()
    cr.restore()


def maquina(cr, x, y, esc, s, t):
    """máquina de escribir genérica que teclea s."""
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    # hoja
    rrect(cr, -170, -330, 340, 260, 6); cr.set_source_rgb(*CREMA); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
    if s:
        font(cr, 80); cr.set_source_rgb(*TINTA); w = cr.text_extents(s).x_advance; cr.move_to(-w / 2 if len(s) > 4 else -120, -170); cr.show_text(s)
    # cuerpo
    cr.move_to(-260 + 10, -80 + 12); cr.line_to(260 + 10, -80 + 12); cr.line_to(300 + 10, 120 + 12); cr.line_to(-300 + 10, 120 + 12); cr.close_path()
    cr.set_source_rgba(0, 0, 0, 0.45); cr.fill()
    rrect(cr, -230, -110, 460, 50, 20); cr.set_source_rgb(0.20, 0.22, 0.30); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()
    cr.move_to(-260, -70); cr.line_to(260, -70); cr.line_to(300, 120); cr.line_to(-300, 120); cr.close_path()
    cr.set_source_rgb(0.15, 0.32, 0.30); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.stroke()
    for fila in range(3):
        for k in range(8 - fila):
            kx = -210 + fila * 25 + k * 58; ky = -20 + fila * 45
            pres = 4 if (int(t * 10) + k * 3 + fila) % 7 == 0 else 0
            cr.arc(kx, ky + pres, 18, 0, 2 * math.pi); cr.set_source_rgb(*CREMA); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(3); cr.stroke()
    cr.restore()


def copa(cr, x, y, esc, ang=0.0):
    cr.save(); cr.translate(x, y); cr.rotate(ang); cr.scale(esc, esc)
    cr.move_to(-70, -160); cr.curve_to(-70, -90, 70, -90, 70, -160); cr.close_path()
    cr.set_source_rgba(*ORO, 0.9); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
    cr.move_to(0, -108); cr.line_to(0, -10); cr.move_to(-45, 0); cr.line_to(45, 0); cr.set_source_rgb(*CREMA); cr.set_line_width(8); cr.stroke()
    for k in range(4):
        cr.arc(-30 + k * 20, -170 - (k % 2) * 25, 6, 0, 2 * math.pi); cr.set_source_rgba(*BLANCO, 0.8); cr.fill()
    cr.restore()


def serpentinas(cr, t, u):
    for k in range(9):
        x0 = 360 + k * 80; ph = k * 1.3
        cr.move_to(x0, 830 - 40 + 900 * ((t * 0.15 + k * 0.11) % 1) * 0 )
        y0 = 850 + ((t * 120 + k * 97) % 650)
        cr.move_to(x0, y0)
        for j in range(1, 7): cr.line_to(x0 + 22 * math.sin(ph + j * 1.2 + t * 3), y0 + j * 14)
        cr.set_source_rgba(*((ORO, ROSA, TURQ)[k % 3]), 0.9 * u); cr.set_line_width(7); cr.stroke()


def escena_a(cr, t, final=False):
    """inicio y cierre: corona que flota y etiqueta colgante que se balancea y escribe ZELDA. Nada en y 300–820."""
    yb = 1430 + 10 * math.sin(t * 2.2)
    corona(cr, 690, yb, 1.15, t, 0.6)
    n = 5 if final else int(max(0, min(5, (t - 0.2) * 5)))
    etiqueta(cr, 690, 900, 0.18 * math.sin(t * 2.6), "ZELDA"[:n], 1.0)


def escena(cr, t):
    i = linea_en(t)
    u = local(i, t)
    if i == 0:
        escena_a(cr, t)
        return "Zelda", ORO
    if i == 1:
        tarjeta(cr, "MIYAMOTO", 690, 960, 70, TINTA, esc=back(u * 4), rot=-0.03, fondo=ORO)
        s = "???" if int(t * 3) % 2 == 0 else ""
        cartucho(cr, 690, 1340, max(0.02, 0.95 * back(min(1, u * 3 + 0.3))), s)
        if u > 0.6: tarjeta(cr, "SIN NOMBRE", 820, 1150, 46, TINTA, esc=back((u - 0.6) * 5), rot=0.06, fondo=ROSA)
        return ("mediados de los 80" if u < 0.5 else "juego sin nombre"), ORO
    if i == 2:
        libro(cr, 690, 1250, 0.95, min(1, u * 2.2), t)
        if u > 0.65: tarjeta(cr, "UN LIBRO", 690, 960, 64, TINTA, esc=back((u - 0.65) * 5), rot=0.03, fondo=TURQ)
        return ("idea de publicidad" if u < 0.5 else "libro ilustrado"), TURQ
    if i == 3:
        libro(cr, 690, 1250, 0.95, 1.0, t, dibujos=1 - ease(u * 2))
        if u > 0.12: sello(cr, "NO", 690, 1200, back((u - 0.12) * 5) * 1.0, -0.15, 1.0, ROJO)
        if u > 0.55:
            v = ease((u - 0.55) / 0.3)
            yy = lerp(1150, 940, v)
            cr.arc(690, yy, 90 + 20 * math.sin(t * 6), 0, 2 * math.pi)
            g = cairo.RadialGradient(690, yy, 5, 690, yy, 110); g.add_color_stop_rgba(0, *ORO, 0.7); g.add_color_stop_rgba(1, *ORO, 0)
            cr.set_source(g); cr.fill()
            texto(cr, "★", 690, yy + 30, 90, ORO, borde=6)
        return ("el libro, no" if u < 0.55 else "pero algo sí"), (ROJO if u < 0.55 else ORO)
    if i == 4:
        corona(cr, 560, 1250, 0.8, t, 1.0)
        reloj_arena(cr, 900, 1330, max(0.02, 0.75 * back(min(1, u * 3))), t)
        if u > 0.45: tarjeta(cr, "BELLEZA ETERNA", 690, 960, 58, TINTA, esc=back((u - 0.45) * 5), rot=-0.03, fondo=ORO)
        return "princesa eterna", ORO
    if i == 5:
        texto(cr, "¿?", 690, 1350, 340 * back(u * 3) + 1, ORO, borde=16)
        return "¿de dónde salió?", ORO
    if i == 6:
        if u < 0.38:
            v = u / 0.38
            maquina(cr, 690, 1430, 0.9, "ZELDA"[:int(v * 7)], t)
            return "un autor famoso…", CREMA
        serpentinas(cr, t, ease((u - 0.38) / 0.1))
        # luz dorada de fiesta: abanico art déco
        for k in range(9):
            a = math.pi + k * math.pi / 8
            cr.move_to(690, 1560); cr.arc(690, 1560, 650, a, a + math.pi / 16); cr.close_path()
            cr.set_source_rgba(*ORO, 0.10 + 0.05 * math.sin(t * 3 + k)); cr.fill()
        copa(cr, 470, 1560, 1.0, -0.12 + 0.05 * math.sin(t * 2))
        copa(cr, 910, 1560, 1.0, 0.12 - 0.05 * math.sin(t * 2))
        tarjeta(cr, "ZELDA FITZGERALD", 690, 1000, 62, TINTA, esc=back((u - 0.38) * 5), rot=-0.03, fondo=CREMA)
        if u > 0.68:
            tarjeta(cr, "EL GRAN GATSBY", 690, 1210, 62, TINTA, esc=back((u - 0.68) * 5), rot=0.04, fondo=ORO)
            return "su esposo escribió…", ORO
        return "una mujer real", ROSA
    if i == 7:
        escena_a(cr, t, final=True)
        if 0.2 < u < 0.85:
            v = min(ease((u - 0.2) * 5), 1 - ease((u - 0.7) / 0.15))
            tarjeta(cr, "MUJER REAL", 900, 1250, 44, TINTA, esc=v, rot=0.08, fondo=ROSA)
        return ("la princesa más famosa" if u < 0.5 else "nombre de una mujer real"), ROSA
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *FONDO1); g.add_color_stop_rgb(0.6, *FONDO2); g.add_color_stop_rgb(1, *FONDO1)
    cr.set_source(g); cr.paint()
    # fondo nuevo: abanicos art déco que giran muy despacio + confeti dorado que cae (antes: ruinas con enredaderas y luciérnagas)
    for cx, cy, r0 in ((540, 1950, 1200), (0, 300, 600), (1080, 300, 600)):
        for k in range(14):
            a = k * math.pi / 7 + t * 0.05
            cr.move_to(cx, cy); cr.arc(cx, cy, r0, a, a + math.pi / 14); cr.close_path()
            cr.set_source_rgba(*ORO, 0.035); cr.fill()
        for rr in (r0 * 0.4, r0 * 0.7):
            cr.arc(cx, cy, rr, 0, 2 * math.pi); cr.set_source_rgba(*ORO, 0.08); cr.set_line_width(3); cr.stroke()
    for k in range(34):
        p = (t * 0.07 + k * 0.131) % 1.0
        x = (k * 197) % W + 30 * math.sin(t * 1.1 + k); y = -50 + p * (H + 100)
        cr.save(); cr.translate(x, y); cr.rotate(t * 2 + k)
        cr.rectangle(-6, -3, 12, 6); cr.set_source_rgba(*((ORO, CREMA, ROSA)[k % 3]), 0.45); cr.fill(); cr.restore()


def gancho(cr, t):
    # entrada nueva: dos líneas sobre marco art déco con esquinas escalonadas; "PRESTADO" en dorado con un brillo
    # que la barre de lado a lado. Completo y legible desde el cuadro 0 (antes: placas oscuras con parpadeo lila)
    ys = [610, 800]
    for k, (s, y) in enumerate(zip(GANCHO["lineas"], ys)):
        z = 165 if k == 0 else 185
        font(cr, z)
        while cr.text_extents(s).x_advance > 900: z -= 4; font(cr, z)
        wtot = cr.text_extents(s).x_advance
        x0 = W / 2 - wtot / 2
        bob = 4 * math.sin(t * 2.0 + k)
        rrect(cr, x0 - 40 + 10, y - z * 0.9 + 12 + bob, wtot + 80, z * 1.15, 8); cr.set_source_rgba(0, 0, 0, 0.55); cr.fill()
        rrect(cr, x0 - 40, y - z * 0.9 + bob, wtot + 80, z * 1.15, 8)
        cr.set_source_rgb(*(CREMA if k == 0 else TINTA)); cr.fill_preserve()
        cr.set_source_rgb(*ORO); cr.set_line_width(8); cr.stroke()
        for sx in (-1, 1):  # esquinas escalonadas
            for sy in (-1, 1):
                cx = W / 2 + sx * (wtot / 2 + 40); cy = y - z * 0.9 + bob + (0 if sy < 0 else z * 1.15)
                cr.rectangle(cx - 14, cy - 14, 28, 28); cr.set_source_rgb(*ORO); cr.fill()
        if k == 0:
            texto(cr, s, W / 2, y + bob, z, TINTA, centro=True, borde=0)
        else:
            font(cr, z); cr.move_to(x0, y + bob); cr.text_path(s)
            gx = x0 - 300 + ((t * 420) % (wtot + 600))
            gr = cairo.LinearGradient(gx - 120, 0, gx + 120, 0)
            gr.add_color_stop_rgb(0, *ORO); gr.add_color_stop_rgb(0.5, 1, 0.98, 0.85); gr.add_color_stop_rgb(1, *ORO)
            cr.set_source(gr); cr.fill()


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: inclinación vertical lenta (de abajo hacia arriba) en cada toma (antes: paneo lateral)
    d = max(0, t - L[i]["t0"]) if i else t
    py = -30 + 60 * ease(d / 5.0)
    cr.save()
    cr.rectangle(0, 830, W, 470); cr.rectangle(320, 1300, W - 320, 360); cr.rectangle(0, 1660, W, 40); cr.clip()
    cr.translate(0, py); cr.translate(690, 1200); cr.scale(1.03, 1.03); cr.translate(-690, -1200)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0 or t > L[-1]["t1"] - 0.35:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1570, col if col else AMBAR, 40)
    chipb(cr, "Secretos de videojuegos", 340, 1745, ORO, 34)
    cr.set_source_rgba(0, 0, 0, 0.25); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*ORO); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        dd = t - x["t0"]
        if 0 <= dd < 0.1:
            cr.set_source_rgba(1, 1, 1, 0.30 * (1 - dd / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0, 1.5] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [1.0, 6.5, 10.0, 15.5, 19.5, 25.0, 28.0, 30.5, 34.0, 36.0, round(L[-1]["t1"] - 0.2, 1)]
        for t in ts:
            cuadro(t).write_to_png(f"prueba/t{t:05.1f}.png")
    elif modo == "hoja":
        from PIL import Image
        import glob
        fs = sorted(glob.glob("prueba/*.png")); ims = [Image.open(f).resize((270, 480)) for f in fs]
        cols = 8; rows = (len(ims) + cols - 1) // cols
        hoja = Image.new("RGB", (cols * 270, rows * 480))
        for k, im in enumerate(ims): hoja.paste(im, ((k % cols) * 270, (k // cols) * 480))
        hoja.save(sys.argv[2] if len(sys.argv) > 2 else "hoja.jpg", quality=85)
    else:
        n = int(DUR * FPS)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-i", "mezcla.wav", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
                              "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", "short.mp4"], stdin=subprocess.PIPE)
        for f in range(n):
            p.stdin.write(bytes(cuadro(f / FPS).get_data()))
        p.stdin.close(); p.wait()
