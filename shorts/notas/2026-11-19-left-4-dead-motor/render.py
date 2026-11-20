"""Motor de respaldo Pixel Diario — Short 'Left 4 Dead te vigila mientras juegas'.
Dibuja con cairo, sin personajes, logos ni diseños reconocibles: ojo geométrico, pasillo en perspectiva, figuras
geométricas con linterna, silla de director genérica, mapa visto desde arriba con puntos. "Left 4 Dead" y "Valve"
solo como texto. Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["EL JUEGO", "TE VIGILA"], "resalta": "VIGILA"}

# paleta nueva: verde noche + rojo alarma + ámbar de linterna (antes: mar turquesa + arena + coral + lima)
FONDO1 = (0.05, 0.13, 0.10)
FONDO2 = (0.00, 0.03, 0.03)
ROJO = (0.98, 0.24, 0.24)
AMBAR = (1.0, 0.72, 0.18)
VERDE = (0.50, 1.0, 0.55)
HUESO = (0.93, 0.90, 0.80)
GRIS = (0.45, 0.50, 0.48)
MURO = (0.10, 0.20, 0.17)
BLANCO = (1, 1, 1)
TINTA = (0.02, 0.05, 0.04)
PLANO1 = (0.45, 0.06, 0.08)
PLANO2 = (0.12, 0.01, 0.03)
FIGS = (AMBAR, VERDE, (0.45, 0.75, 1.0), HUESO)

RESALTA = {1: ["2008,", "Valve", "Director."], 2: ["nervioso", "fallas", "tiros", "equipo."], 3: ["Pero", "calificarte."],
           4: ["zombis…", "botiquines", "armas"], 5: ["¿Por", "qué?"], 6: ["ninguna", "igual", "memoria."],
           7: ["te", "mira…", "Left", "4", "Dead."]}
COLRES = {1: AMBAR, 2: VERDE, 3: ROJO, 4: ROJO, 5: AMBAR, 6: VERDE, 7: ROJO}


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
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: placa oscura con marco de cinta
    de advertencia (franjas diagonales del color) y texto del color (antes: píldora de color lleno con cuadrito)."""
    x = max(x, 340)
    font(cr, size); w = cr.text_extents(s).x_advance + 60; h = size + 36
    cr.save(); cr.rectangle(x, y, w, h); cr.clip()
    cr.set_source_rgb(*color); cr.paint()
    cr.set_source_rgb(*TINTA); cr.set_line_width(9)
    for k in range(-2, int(w / 22) + 4):
        cr.move_to(x + k * 22, y + h); cr.line_to(x + k * 22 + h, y); cr.stroke()
    cr.restore()
    cr.rectangle(x + 8, y + 8, w - 16, h - 16); cr.set_source_rgb(0.03, 0.06, 0.05); cr.fill()
    cr.set_source_rgb(*color); cr.move_to(x + 30, y + size + 8); cr.show_text(s)


def tarjeta(cr, s, x, y, size, color, esc=1.0, rot=0.0, fondo=TINTA):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 70
    cr.rectangle(-w / 2 + 8, -size * 0.95 + 10, w, size * 1.5); cr.set_source_rgba(0, 0, 0, 0.5); cr.fill()
    cr.rectangle(-w / 2, -size * 0.95, w, size * 1.5); cr.set_source_rgb(*fondo); cr.fill_preserve()
    cr.set_source_rgb(*color); cr.set_line_width(5); cr.stroke()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 35, size * 0.25); cr.show_text(s)
    cr.restore()


# ---------- dibujos genéricos ----------
def pasillo(cr, t, ox=660, oy=1000):
    """pasillo oscuro en perspectiva; punto de fuga en (ox, oy)."""
    cr.set_source_rgb(*MURO)
    cr.move_to(330, 1300); cr.line_to(ox - 90, oy + 60); cr.line_to(ox + 90, oy + 60); cr.line_to(W, 1300)
    cr.line_to(W, 1700); cr.line_to(330, 1700); cr.close_path(); cr.fill()
    cr.set_source_rgba(*VERDE, 0.18); cr.set_line_width(3)
    for k in range(7):
        z = ((k / 7) + t * 0.12) % 1.0
        y = lerp(oy + 60, 1300, z ** 2)
        xl = lerp(ox - 90, 330, z ** 2); xr = lerp(ox + 90, W, z ** 2)
        cr.move_to(xl, y); cr.line_to(xr, y); cr.stroke()


def ojo(cr, cx, cy, t, abre, esc=1.0, mira=0.0):
    if abre <= 0.01: return
    cr.save(); cr.translate(cx, cy); cr.scale(esc, esc)
    w, h = 300, 150 * abre
    cr.move_to(-w, 0); cr.curve_to(-w * 0.5, -h * 1.3, w * 0.5, -h * 1.3, w, 0)
    cr.curve_to(w * 0.5, h * 1.3, -w * 0.5, h * 1.3, -w, 0); cr.close_path()
    cr.set_source_rgb(*HUESO); cr.fill_preserve()
    cr.save(); cr.clip()
    px = 70 * math.sin(t * 1.3) + mira
    cr.new_sub_path(); cr.arc(px, 0, 110, 0, 2 * math.pi); cr.set_source_rgb(*ROJO); cr.fill()
    cr.new_sub_path(); cr.arc(px, 0, 52 + 6 * math.sin(t * 5), 0, 2 * math.pi); cr.set_source_rgb(*TINTA); cr.fill()
    cr.new_sub_path(); cr.arc(px + 28, -30, 18, 0, 2 * math.pi); cr.set_source_rgb(*BLANCO); cr.fill()
    cr.restore()
    cr.move_to(-w, 0); cr.curve_to(-w * 0.5, -h * 1.3, w * 0.5, -h * 1.3, w, 0)
    cr.curve_to(w * 0.5, h * 1.3, -w * 0.5, h * 1.3, -w, 0); cr.close_path()
    cr.set_source_rgb(*TINTA); cr.set_line_width(12); cr.stroke()
    cr.restore()


def figura(cr, x, y, col, t, k, luz=True):
    paso = math.sin(t * 7 + k)
    if luz:
        g = cairo.RadialGradient(x + 20, y - 60, 10, x + 20, y - 260, 260)
        g.add_color_stop_rgba(0, *AMBAR, 0.45); g.add_color_stop_rgba(1, *AMBAR, 0)
        cr.move_to(x + 18, y - 60); cr.line_to(x - 70, y - 320); cr.line_to(x + 110, y - 320); cr.close_path()
        cr.set_source(g); cr.fill()
    cr.set_source_rgb(*TINTA); cr.set_line_width(14); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.move_to(x - 10, y); cr.line_to(x - 18 - 12 * paso, y + 50); cr.stroke()
    cr.move_to(x + 10, y); cr.line_to(x + 18 + 12 * paso, y + 50); cr.stroke()
    rrect(cr, -28 + x, y - 80, 56, 85, 18); cr.set_source_rgb(*col); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
    cr.new_sub_path(); cr.arc(x, y - 105, 24, 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.stroke()


def escena_a(cr, t, i):
    """imagen del inicio y del cierre: ojo gigante que se abre sobre un pasillo con cuatro figuras con linterna.
    Nada en y 300–820 (el texto del gancho va encima)."""
    t0 = L[i]["t0"]
    pasillo(cr, t)
    abre = 0.35 + 0.65 * ease((t - t0 + 0.2) / 1.2)
    # parpadeo del ojo cada ~2.6 s
    ph = (t % 2.6)
    if 2.35 < ph < 2.6: abre *= abs(math.cos((ph - 2.35) / 0.25 * math.pi))
    ojo(cr, 660, 1040, t, abre, esc=1.0 + 0.04 * math.sin(t * 2))
    for k in range(4):
        x = 470 + k * 140 + 10 * math.sin(t * 2 + k)
        figura(cr, x, 1480 - (k % 2) * 30, FIGS[k], t, k)


def silla(cr, x, y, esc, rot=0.0):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    cr.set_source_rgb(0.55, 0.36, 0.18); cr.set_line_width(16); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.move_to(-110, -40); cr.line_to(110, 200); cr.stroke(); cr.move_to(110, -40); cr.line_to(-110, 200); cr.stroke()
    cr.move_to(-120, -260); cr.line_to(-120, -40); cr.stroke(); cr.move_to(120, -260); cr.line_to(120, -40); cr.stroke()
    cr.rectangle(-130, -60, 260, 34); cr.set_source_rgb(*TINTA); cr.fill()
    cr.rectangle(-130, -250, 260, 110); cr.set_source_rgb(*TINTA); cr.fill_preserve()
    cr.set_source_rgb(*AMBAR); cr.set_line_width(5); cr.stroke()
    texto(cr, "DIRECTOR", 0, -178, 42, AMBAR, borde=0)
    cr.restore()


def medidor(cr, x, y, icono, etiqueta, nivel, col, t, a):
    if a <= 0.01: return
    cr.save(); cr.translate(x + (1 - a) * 300, y)
    rrect(cr, 0, -70, 620, 150, 20); cr.set_source_rgba(0.03, 0.07, 0.06, 0.95); cr.fill_preserve()
    cr.set_source_rgb(*col); cr.set_line_width(5); cr.stroke()
    cr.save(); cr.translate(80, 5)
    if icono == "corazon":
        s = 1 + 0.15 * max(0, math.sin(t * 12))
        cr.scale(s, s)
        cr.move_to(0, 40); cr.curve_to(-70, -10, -40, -70, 0, -30); cr.curve_to(40, -70, 70, -10, 0, 40)
        cr.set_source_rgb(*col); cr.fill()
    elif icono == "diana":
        for r, c in ((50, BLANCO), (34, col), (18, BLANCO), (6, col)):
            cr.new_sub_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.set_source_rgb(*c); cr.fill()
        cr.set_source_rgb(*ROJO); cr.set_line_width(7)
        for dx, dy in ((48, -42), (-52, 30)):
            cr.move_to(dx - 10, dy - 10); cr.line_to(dx + 10, dy + 10); cr.stroke()
            cr.move_to(dx + 10, dy - 10); cr.line_to(dx - 10, dy + 10); cr.stroke()
    else:
        for s_ in (-1, 1):
            rrect(cr, s_ * 22 - 22, -40, 44, 80, 18); cr.set_source_rgb(*col); cr.fill_preserve()
            cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
        cr.set_source_rgb(*BLANCO); cr.set_line_width(5)
        for k in range(3):
            ang = -math.pi / 2 + (k - 1) * 0.6
            cr.move_to(math.cos(ang) * 55, math.sin(ang) * 55); cr.line_to(math.cos(ang) * 75, math.sin(ang) * 75); cr.stroke()
    cr.restore()
    texto(cr, etiqueta, 160, -10, 46, BLANCO, centro=False, borde=0)
    rrect(cr, 160, 22, 420, 30, 15); cr.set_source_rgb(0.15, 0.2, 0.18); cr.fill()
    rrect(cr, 160, 22, max(30, 420 * nivel), 30, 15); cr.set_source_rgb(*col); cr.fill()
    cr.restore()


def hoja(cr, t, u):
    e = max(0.01, back(u * 4))
    cr.save(); cr.translate(660, 1080); cr.rotate(0.05); cr.scale(e, e)
    cr.rectangle(-200, -260, 400, 520); cr.set_source_rgb(*HUESO); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
    texto(cr, "CALIFICACIÓN", 0, -190, 40, TINTA, borde=0)
    for k in range(4):
        cr.rectangle(-150, -140 + k * 40, 300 - (k % 2) * 90, 14); cr.set_source_rgb(*GRIS); cr.fill()
    texto(cr, "10", 0, 160, 190, (0.1, 0.45, 0.2), borde=0)
    v = ease((u - 0.35) * 3)
    if v > 0:
        cr.set_source_rgb(*ROJO); cr.set_line_width(28); cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.move_to(-170, -230); cr.line_to(lerp(-170, 170, min(1, v * 2)), lerp(-230, 230, min(1, v * 2))); cr.stroke()
        if v > 0.5:
            w2 = (v - 0.5) * 2
            cr.move_to(170, -230); cr.line_to(lerp(170, -170, w2), lerp(-230, 230, w2)); cr.stroke()
    cr.restore()


def mapa_base(cr, x0, y0, w, h, esc=1.0):
    cr.save(); cr.translate(x0 + w / 2, y0 + h / 2); cr.scale(esc, esc); cr.translate(-w / 2, -h / 2)
    cr.rectangle(0, 0, w, h); cr.set_source_rgb(0.06, 0.12, 0.10); cr.fill_preserve()
    cr.set_source_rgb(*VERDE); cr.set_line_width(4); cr.stroke()
    cr.set_source_rgb(0.18, 0.30, 0.26); cr.set_line_width(w * 0.07)
    cr.move_to(w * 0.1, h * 0.85); cr.line_to(w * 0.1, h * 0.5); cr.line_to(w * 0.6, h * 0.5); cr.line_to(w * 0.6, h * 0.15)
    cr.line_to(w * 0.9, h * 0.15); cr.stroke()
    cr.move_to(w * 0.6, h * 0.5); cr.line_to(w * 0.9, h * 0.5); cr.line_to(w * 0.9, h * 0.85); cr.line_to(w * 0.35, h * 0.85); cr.stroke()
    return w, h


def cruz(cr, x, y, s, a=1.0):
    cr.rectangle(x - s / 2, y - s / 2, s, s); cr.set_source_rgba(*BLANCO, a); cr.fill()
    cr.rectangle(x - s * 0.1, y - s * 0.35, s * 0.2, s * 0.7); cr.rectangle(x - s * 0.35, y - s * 0.1, s * 0.7, s * 0.2)
    cr.set_source_rgba(*ROJO, a); cr.fill()


def arma(cr, x, y, s, a=1.0):
    cr.rectangle(x - s * 0.6, y - s * 0.12, s * 1.2, s * 0.24); cr.rectangle(x + s * 0.15, y, s * 0.2, s * 0.45)
    cr.set_source_rgba(*AMBAR, a); cr.fill()


def puntos_mapa(cr, w, h, semilla, u, t, objetos=True, n=7):
    rnd = random.Random(semilla)
    camino = [(0.1, 0.8), (0.1, 0.6), (0.3, 0.5), (0.5, 0.5), (0.6, 0.3), (0.75, 0.15), (0.9, 0.3), (0.9, 0.7), (0.6, 0.85), (0.4, 0.85)]
    for k in range(n):
        px, py = rnd.choice(camino); px += rnd.uniform(-0.04, 0.04); py += rnd.uniform(-0.04, 0.04)
        a = ease(u * 5 - k * 0.3)
        cr.new_sub_path(); cr.arc(px * w, py * h, w * 0.035 * (1 + 0.2 * math.sin(t * 8 + k)), 0, 2 * math.pi)
        cr.set_source_rgba(*ROJO, a); cr.fill()
    if objetos:
        for k in range(3):
            px, py = rnd.choice(camino)
            a = ease(u * 5 - 1 - k * 0.3)
            if k % 2 == 0: cruz(cr, px * w, py * h, w * 0.08, a)
            else: arma(cr, px * w, py * h, w * 0.1, a)


def mapa_grande(cr, t, u):
    w, h = mapa_base(cr, 360, 820, 600, 640, esc=max(0.01, back(u * 4)))
    if u < 0.5:
        # zombis que se mueven de lugar
        sem = 0 if u < 0.25 else 1
        puntos_mapa(cr, w, h, sem, 1.0, t, objetos=False, n=8)
    else:
        sem = 2 + int((u - 0.5) * 8)
        puntos_mapa(cr, w, h, sem, 1.0, t, objetos=True, n=5)
    cr.restore()


def tres_mapas(cr, t, u):
    for k in range(3):
        a = back(u * 4 - k * 0.6)
        if a <= 0.01: continue
        x0 = 345 + k * 240; y0 = 900
        w, h = mapa_base(cr, x0, y0, 220, 380, esc=a)
        puntos_mapa(cr, w, h, 10 + k * 7, 1.0, t, objetos=True, n=5)
        cr.restore()
    if u > 0.6:
        s = max(0.01, back((u - 0.6) * 5))
        z = lerp(2.0, 1.0, min(1, (u - 0.6) * 6))
        cr.save(); cr.translate(700, 1390); cr.rotate(-0.1); cr.scale(s * z, s * z)
        font(cr, 74); w = cr.text_extents("NUNCA IGUAL").x_advance + 60
        cr.rectangle(-w / 2, -70, w, 110); cr.set_source_rgba(*ROJO, 0.25); cr.fill_preserve()
        cr.set_source_rgb(*ROJO); cr.set_line_width(12); cr.stroke()
        texto(cr, "NUNCA IGUAL", 0, 12, 74, ROJO, borde=6)
        cr.restore()


def escena(cr, t):
    i = linea_en(t)
    if i in (0, 7):
        escena_a(cr, t, i)
        return ("LEFT 4 DEAD", ROJO) if i == 0 else ("alguien te mira", ROJO)
    u = local(i, t)
    if i == 1:
        pasillo(cr, t)
        tarjeta(cr, "2008 · VALVE", 660, 740, 80, AMBAR, esc=back(u * 4), rot=-0.04)
        if u > 0.3:
            v = ease((u - 0.3) * 3)
            silla(cr, 680, lerp(1060, 1300, v), 0.9, rot=(1 - v) * 0.5)
        return "el Director", AMBAR
    if i == 2:
        medidor(cr, 370, 900, "corazon", "NERVIOS", 0.3 + 0.6 * ease(u * 3), ROJO, t, ease(u * 5))
        medidor(cr, 370, 1100, "diana", "PUNTERÍA", 0.7 - 0.4 * ease((u - 0.33) * 3), AMBAR, t, ease((u - 0.3) * 5))
        medidor(cr, 370, 1300, "manos", "EQUIPO", 0.2 + 0.6 * ease((u - 0.66) * 3), VERDE, t, ease((u - 0.62) * 5))
        return "te está midiendo", VERDE
    if i == 3:
        hoja(cr, t, u)
        return "no es examen", ROJO
    if i == 4:
        mapa_grande(cr, t, u)
        return ("zombis" if u < 0.5 else "botiquines y armas"), (ROJO if u < 0.5 else AMBAR)
    if i == 5:
        ojo(cr, 660, 1300, t, 0.6, esc=0.5)
        texto(cr, "¿?", 660, 1180, 380 + 20 * math.sin(t * 9), AMBAR, borde=16)
        return None, None
    if i == 6:
        tres_mapas(cr, t, u)
        return "cada partida", VERDE
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    if i == 6:
        g.add_color_stop_rgb(0, *PLANO1); g.add_color_stop_rgb(1, *PLANO2)
        cr.set_source(g); cr.paint()
        cr.set_source_rgba(1, 1, 1, 0.07); cr.set_line_width(3)
        off = (t * 40) % 80
        for k in range(-30, 30):
            cr.move_to(k * 80 + off, 0); cr.line_to(k * 80 + off + H * 0.4, H); cr.stroke()
        return
    g.add_color_stop_rgb(0, *FONDO1); g.add_color_stop_rgb(1, *FONDO2)
    cr.set_source(g); cr.paint()
    # niebla: manchas suaves que se desplazan (antes: cuadritos pixelados que bajan)
    rnd = random.Random(4)
    for k in range(9):
        x = (rnd.uniform(0, W) + t * rnd.uniform(15, 40)) % (W + 400) - 200
        y = rnd.uniform(600, 1800); r = rnd.uniform(160, 300)
        gr = cairo.RadialGradient(x, y, 0, x, y, r)
        gr.add_color_stop_rgba(0, 0.6, 0.8, 0.7, 0.07); gr.add_color_stop_rgba(1, 0.6, 0.8, 0.7, 0)
        cr.set_source(gr); cr.arc(x, y, r, 0, 2 * math.pi); cr.fill()


def gancho(cr, t):
    # entrada nueva: las letras "se prenden" como luz que falla (parpadeo por letra, siempre legible desde el cuadro 0)
    # y el texto baja un poco (antes: las líneas entraban deslizándose desde los lados)
    ys = [620, 800]; sizes = [150, 150]
    for k, (s, y, z) in enumerate(zip(GANCHO["lineas"], ys, sizes)):
        dy = (1 - ease((t + 0.2) / 0.5)) * -40
        font(cr, z); wtot = cr.text_extents(s).x_advance; x = W / 2 - wtot / 2
        resalta = s.endswith(GANCHO["resalta"]); ini_res = len(s) - len(GANCHO["resalta"]) if resalta else 99
        for j, ch in enumerate(s):
            font(cr, z); adv = cr.text_extents(ch).x_advance if ch != " " else cr.text_extents(" ").x_advance
            if ch != " ":
                fl = 1.0
                f = (t * 9 + j * 1.7 + k * 3.1)
                if t > 0.15 and math.sin(f) > 0.93 and t < 2.6: fl = 0.45
                col = ROJO if j >= ini_res else BLANCO
                texto(cr, ch, x, y + dy, z, col, centro=False, borde=26, alpha=1.0)
                if fl < 1:
                    texto(cr, ch, x, y + dy, z, (0.3, 0.3, 0.3), centro=False, borde=0, alpha=1 - fl)
            x += adv


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
            col = COLRES.get(i, AMBAR) if p in RESALTA.get(i, []) else BLANCO
            if acc > vis: col = (0.62, 0.70, 0.66)
            font(cr, size); adv = cr.text_extents(p + " ").x_advance
            cr.move_to(x, y); cr.text_path(p)
            cr.set_source_rgba(*TINTA, 1); cr.set_line_width(12); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve()
            cr.set_source_rgba(*col, 1); cr.fill()
            x += adv
        y += 88


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: "cámara en mano" (temblor suave de varias senoides) + acercamiento continuo dentro de cada escena
    # (antes: paneo horizontal + golpe de zoom en cada tiempo)
    u = local(i, t)
    zc = 1.0 + 0.05 * u
    hx = 6 * math.sin(t * 1.7) + 3 * math.sin(t * 4.3); hy = 5 * math.cos(t * 1.3) + 3 * math.sin(t * 3.1)
    rot = 0.004 * math.sin(t * 0.9)
    cr.save(); cr.translate(660 + hx, 1100 + hy); cr.rotate(rot); cr.scale(zc, zc); cr.translate(-660, -1100)
    cr.restore(); cr.save()
    # nada del dibujo entra en la zona de la mascota
    cr.rectangle(0, 0, W, 1300); cr.rectangle(320, 1300, W - 320, 360); cr.rectangle(0, 1660, W, H - 1660); cr.clip()
    cr.translate(660 + hx, 1100 + hy); cr.rotate(rot); cr.scale(zc, zc); cr.translate(-660, -1100)
    eti, col = escena(cr, t)
    cr.restore()
    # viñeta tipo linterna
    vg = cairo.RadialGradient(W / 2, 1050, 300, W / 2, 1050, 1150)
    vg.add_color_stop_rgba(0, 0, 0, 0, 0); vg.add_color_stop_rgba(1, 0, 0, 0, 0.55)
    cr.set_source(vg); cr.paint()
    if i == 0 and t < L[0]["t1"] + 0.1:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1560, col, 40)
    chipb(cr, "El juego te ayuda en secreto", 360, 1760, AMBAR, 34)
    cr.set_source_rgba(0, 0, 0, 0.3); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*ROJO); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        d = t - x["t0"]
        if 0 <= d < 0.12:
            cr.set_source_rgba(0, 0, 0, 0.5 * (1 - d / 0.12)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0, 1.5] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [9.0, 11.5, 16.0, 18.5, 22.0, 24.5, round(L[-1]["t1"] - 0.3, 1)]
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
