"""Motor de respaldo Pixel Diario — Short 'Street Fighter II no planeó sus combos'.
Dibuja con cairo, sin personajes, logos ni diseños reconocibles: dos luchadores geométricos (cuadrado azul y triángulo
rojo), máquina de arcade genérica, bola de energía genérica, lupa, llave inglesa, botón y candado. "Street Fighter II"
y "Capcom" solo como texto. Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["COMBOS", "POR ACCIDENTE"], "resalta": "ACCIDENTE"}

# paleta nueva: morado arcade + magenta neón + cian + amarillo (antes: verde noche + rojo alarma + ámbar)
FONDO1 = (0.20, 0.06, 0.32)
FONDO2 = (0.05, 0.01, 0.12)
MAGENTA = (1.0, 0.25, 0.65)
CIAN = (0.25, 0.90, 1.0)
AMARILLO = (1.0, 0.86, 0.15)
AZUL = (0.25, 0.50, 1.0)
ROJO = (1.0, 0.28, 0.25)
BLANCO = (1, 1, 1)
TINTA = (0.04, 0.01, 0.08)
GRIS = (0.55, 0.50, 0.62)
PISO = (0.30, 0.10, 0.42)
PLANO1 = (0.80, 0.08, 0.42)
PLANO2 = (0.30, 0.02, 0.18)

RESALTA = {1: ["1991", "Capcom"], 2: ["golpe,", "cubrirse."], 3: ["Pero", "raro."],
           4: ["cancelabas", "especial", "antes"], 5: ["¿Y", "arreglaron?"], 6: ["quitarlo.", "divertido", "escondido."],
           7: ["combo", "accidente."]}
COLRES = {1: AMARILLO, 2: CIAN, 3: MAGENTA, 4: AMARILLO, 5: CIAN, 6: AMARILLO, 7: MAGENTA}


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


# ---------- dibujos genéricos ----------
def piso(cr, t, y=1440):
    cr.set_source_rgb(*PISO); cr.rectangle(330, y, W - 330, 230); cr.fill()
    cr.set_source_rgba(*CIAN, 0.35); cr.set_line_width(3)
    for k in range(-6, 12):
        x = 660 + k * 120 + ((t * 60) % 120)
        cr.move_to(660 + (x - 660) * 0.4, y); cr.line_to(x, y + 230); cr.stroke()
    cr.move_to(330, y); cr.line_to(W, y); cr.set_source_rgb(*CIAN); cr.set_line_width(5); cr.stroke()


def luchador(cr, x, y, tipo, t, golpe=0.0, escudo=0.0, retro=0.0, esc=1.0):
    """tipo 'cuadro' (azul, mira a la derecha) o 'tri' (rojo, mira a la izquierda). golpe 0..1 estira el brazo."""
    cr.save(); cr.translate(x + retro, y); cr.scale(esc, esc)
    d = 1 if tipo == "cuadro" else -1
    col = AZUL if tipo == "cuadro" else ROJO
    bob = 8 * math.sin(t * 8 + (0 if d > 0 else 1.5))
    # piernas
    cr.set_source_rgb(*TINTA); cr.set_line_width(22); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.move_to(-25, -40); cr.line_to(-55, 60); cr.stroke(); cr.move_to(25, -40); cr.line_to(55, 60); cr.stroke()
    # cuerpo
    cr.save(); cr.translate(0, -150 + bob)
    if tipo == "cuadro":
        rrect(cr, -70, -80, 140, 160, 14)
    else:
        cr.move_to(0, -95); cr.line_to(85, 80); cr.line_to(-85, 80); cr.close_path()
    cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
    # cabeza (círculo con banda y ojo)
    cr.new_sub_path(); cr.arc(0, -130, 45, 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.stroke()
    cr.rectangle(-45, -150, 90, 14); cr.set_source_rgb(*BLANCO); cr.fill()
    cr.new_sub_path(); cr.arc(d * 18, -125, 8, 0, 2 * math.pi); cr.set_source_rgb(*TINTA); cr.fill()
    # brazo
    largo = 70 + 150 * golpe
    cr.set_source_rgb(*TINTA); cr.set_line_width(24)
    cr.move_to(d * 40, -20); cr.line_to(d * (40 + largo), -20 - 20 * golpe); cr.stroke()
    cr.new_sub_path(); cr.arc(d * (40 + largo), -20 - 20 * golpe, 30, 0, 2 * math.pi); cr.set_source_rgb(*AMARILLO if golpe > 0.6 else col)
    cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
    if escudo > 0.01:
        cr.set_source_rgba(*CIAN, 0.35 * escudo); cr.set_line_width(4)
        cr.new_sub_path(); cr.arc(d * 60, -40, 140 * escudo, -1.1, 1.1) if d > 0 else cr.arc(d * 60, -40, 140 * escudo, math.pi - 1.1, math.pi + 1.1)
        cr.set_line_width(22); cr.set_source_rgba(*CIAN, 0.9 * escudo); cr.stroke()
    cr.restore(); cr.restore()


def chispas(cr, x, y, t, fuerza=1.0, n=10, semilla=0):
    rnd = random.Random(semilla)
    for k in range(n):
        ang = rnd.uniform(0, 2 * math.pi); r0 = 30 + rnd.uniform(0, 40) * fuerza
        r1 = r0 + (60 + rnd.uniform(0, 80)) * fuerza * (0.7 + 0.3 * math.sin(t * 20 + k))
        cr.move_to(x + math.cos(ang) * r0, y + math.sin(ang) * r0); cr.line_to(x + math.cos(ang) * r1, y + math.sin(ang) * r1)
        cr.set_source_rgb(*(AMARILLO if k % 2 else BLANCO)); cr.set_line_width(10); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()


def estrella(cr, x, y, r, col, puntas=8, rot=0.0):
    cr.save(); cr.translate(x, y); cr.rotate(rot)
    for k in range(puntas * 2):
        rr = r if k % 2 == 0 else r * 0.5
        a = k * math.pi / puntas
        (cr.move_to if k == 0 else cr.line_to)(math.cos(a) * rr, math.sin(a) * rr)
    cr.close_path(); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
    cr.restore()


def contador(cr, x, y, n, t, esc=1.0, col=AMARILLO, size=110, estcol=MAGENTA):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(-0.08); cr.scale(esc, esc)
    estrella(cr, 0, -size * 0.35, size * 1.5, estcol, rot=t * 0.8)
    texto(cr, "COMBO", 0, -size * 0.55, size * 0.45, BLANCO, borde=10)
    texto(cr, f"×{n}", 0, size * 0.45, size, col, borde=14)
    cr.restore()


def escena_a(cr, t, i):
    """imagen del inicio y del cierre: los dos luchadores geométricos chocando, contador COMBO ×3 con chispas.
    Nada en y 300–820 (el texto del gancho va encima)."""
    piso(cr, t)
    ciclo = (t * 1.6) % 1.0
    g = ease(ciclo * 3) * (1 - ease((ciclo - 0.5) * 3))
    luchador(cr, 520, 1440, "cuadro", t, golpe=g)
    luchador(cr, 830, 1440, "tri", t, retro=30 * g)
    chispas(cr, 720, 1270, t, fuerza=0.6 + g, semilla=int(t * 6))
    contador(cr, 760, 1010, 3, t, esc=1.0 + 0.12 * max(0, math.sin(t * 10)), size=100)


def arcade(cr, x, y, esc, t, pantalla="vacia", u=0.0):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    cr.move_to(-190, 380); cr.line_to(-190, -330); cr.line_to(-150, -400); cr.line_to(150, -400); cr.line_to(190, -330)
    cr.line_to(190, 380); cr.close_path(); cr.set_source_rgb(0.15, 0.05, 0.25); cr.fill_preserve()
    cr.set_source_rgb(*MAGENTA); cr.set_line_width(8); cr.stroke()
    cr.rectangle(-150, -380, 300, 60); cr.set_source_rgb(*AMARILLO); cr.fill()
    texto(cr, "ARCADE", 0, -333, 40, TINTA, borde=0)
    cr.rectangle(-150, -290, 300, 240); cr.set_source_rgb(0.02, 0.05, 0.10); cr.fill_preserve()
    cr.set_source_rgb(*CIAN); cr.set_line_width(5); cr.stroke()
    if pantalla == "pelea":
        cr.save(); cr.rectangle(-150, -290, 300, 240); cr.clip()
        cr.translate(0, -100); cr.scale(0.32, 0.32)
        luchador(cr, -150, 250, "cuadro", t, golpe=ease(math.sin(t * 6)))
        luchador(cr, 150, 250, "tri", t)
        cr.restore()
    # panel de control
    cr.move_to(-190, -20); cr.line_to(190, -20); cr.line_to(220, 60); cr.line_to(-220, 60); cr.close_path()
    cr.set_source_rgb(0.25, 0.10, 0.38); cr.fill()
    cr.set_source_rgb(*TINTA); cr.set_line_width(12); cr.move_to(-110, 20); cr.line_to(-110, -20); cr.stroke()
    cr.new_sub_path(); cr.arc(-110, -25, 16, 0, 2 * math.pi); cr.set_source_rgb(*ROJO); cr.fill()
    for k, c in enumerate((CIAN, AMARILLO, MAGENTA)):
        cr.new_sub_path(); cr.arc(10 + k * 55, 20, 18, 0, 2 * math.pi); cr.set_source_rgb(*c); cr.fill()
    cr.restore()


def reloj_arena(cr, x, y, u):
    cr.save(); cr.translate(x, y)
    cr.move_to(-60, -90); cr.line_to(60, -90); cr.line_to(8, 0); cr.line_to(60, 90); cr.line_to(-60, 90); cr.line_to(-8, 0)
    cr.close_path(); cr.set_source_rgba(1, 1, 1, 0.15); cr.fill_preserve(); cr.set_source_rgb(*BLANCO); cr.set_line_width(6); cr.stroke()
    a = 1 - u
    cr.move_to(-50 * a, -10 - 70 * a); cr.line_to(50 * a, -10 - 70 * a); cr.line_to(0, -6); cr.close_path(); cr.set_source_rgb(*AMARILLO); cr.fill()
    cr.move_to(-55 * u, 85); cr.line_to(55 * u, 85); cr.line_to(0, 85 - 70 * u); cr.close_path(); cr.fill()
    cr.restore()


def lupa(cr, x, y, esc):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    cr.set_source_rgb(0.5, 0.3, 0.1); cr.set_line_width(40); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.move_to(110, 110); cr.line_to(230, 230); cr.stroke()
    cr.new_sub_path(); cr.arc(0, 0, 150, 0, 2 * math.pi); cr.set_source_rgba(*CIAN, 0.25); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(26); cr.stroke()
    cr.set_source_rgb(*GRIS); cr.set_line_width(12); cr.new_sub_path(); cr.arc(0, 0, 150, 0, 2 * math.pi); cr.stroke()
    cr.restore()


def bola(cr, x, y, r, t):
    g = cairo.RadialGradient(x, y, 5, x, y, r)
    g.add_color_stop_rgb(0, 1, 1, 1); g.add_color_stop_rgb(0.5, *CIAN); g.add_color_stop_rgba(1, *AZUL, 0)
    cr.set_source(g); cr.arc(x, y, r, 0, 2 * math.pi); cr.fill()
    cr.set_source_rgba(*CIAN, 0.5); cr.set_line_width(10)
    for k in range(4):
        cr.move_to(x - r - 20 - k * 40, y - 30 + k * 20); cr.line_to(x - r - 120 - k * 40, y - 30 + k * 20); cr.stroke()


def llave(cr, x, y, rot, esc=1.0):
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    cr.set_source_rgb(0.80, 0.82, 0.88)
    rrect(cr, -30, 0, 60, 330, 25); cr.fill()
    cr.new_sub_path(); cr.arc(0, -20, 85, 0, 2 * math.pi); cr.fill()
    cr.rectangle(-35, -130, 70, 110); cr.set_source_rgb(*FONDO1); cr.fill()
    cr.set_source_rgb(*TINTA); cr.set_line_width(6)
    cr.new_sub_path(); cr.arc(0, -20, 85, -1.15, math.pi + 1.15); cr.stroke()
    cr.restore()


def boton(cr, x, y, encendido, u):
    cr.save(); cr.translate(x, y)
    rrect(cr, -240, 40, 480, 120, 30); cr.set_source_rgb(0.25, 0.25, 0.28); cr.fill()
    col = ROJO if encendido else (0.35, 0.18, 0.18)
    cr.save(); cr.scale(1, 0.45); cr.new_sub_path(); cr.arc(0, 140, 200, 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill()
    cr.restore()
    rrect(cr, -200, -40, 400, 110, 50); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
    texto(cr, "BORRAR", 0, 38, 72, BLANCO if encendido else GRIS, borde=8)
    cr.restore()


def candado(cr, x, y, cierra, esc):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    cr.set_source_rgb(*TINTA); cr.set_line_width(36)
    dy = (1 - cierra) * -70
    cr.new_sub_path(); cr.arc(0, -40 + dy, 90, math.pi, 2 * math.pi); cr.stroke()
    cr.move_to(-90, -40 + dy); cr.line_to(-90, 20 + dy * 0.0); cr.stroke()
    cr.move_to(90, -40 + dy); cr.line_to(90, -40 + dy + 40 * cierra); cr.stroke()
    rrect(cr, -150, 0, 300, 230, 30); cr.set_source_rgb(*AMARILLO); cr.fill_preserve(); cr.set_line_width(10); cr.stroke()
    texto(cr, "OCULTO", 0, 135, 66, TINTA, borde=0)
    cr.restore()


def escena(cr, t):
    i = linea_en(t)
    if i in (0, 7):
        escena_a(cr, t, i)
        return ("STREET FIGHTER II", MAGENTA) if i == 0 else ("fue un accidente", MAGENTA)
    u = local(i, t)
    if i == 1:
        tarjeta(cr, "1991 · CAPCOM", 660, 690, 86, AMARILLO, esc=back(u * 4), rot=-0.04)
        arcade(cr, 680, lerp(1750, 1240, back(u * 2.5)), 1.0, t, pantalla="pelea" if u > 0.45 else "vacia")
        return ("1991", AMARILLO) if u < 0.5 else ("juego de peleas", CIAN)
    if i == 2:
        piso(cr, t)
        g = ease(u * 4) * (1 - ease((u - 0.45) * 4))
        esc_ = ease((u - 0.12) * 5)
        luchador(cr, 500, 1440, "cuadro", t, golpe=g)
        luchador(cr, 860, 1440, "tri", t, escudo=esc_)
        reloj_arena(cr, 680, 870, min(1, u * 1.6))
        if u > 0.6: tarjeta(cr, "BLOQUEADO", 690, 1100, 60, CIAN, esc=back((u - 0.6) * 5), rot=0.05)
        return "así debía ser", CIAN
    if i == 3:
        arcade(cr, 690, 1150, 0.95, t, pantalla="pelea")
        lx = lerp(1000, 700, ease(u * 2)); ly = lerp(1300, 900, ease(u * 2))
        lupa(cr, lx, ly, 0.9)
        if u > 0.55:
            s = back((u - 0.55) * 5)
            texto(cr, "!", 930, 820, 260 * max(0.01, s), MAGENTA, borde=16)
        return "algo raro", MAGENTA
    if i == 4:
        piso(cr, t)
        # cámara lenta en 3 tiempos: golpe normal → destello → especial entra antes del escudo
        g = ease(u * 5)
        luchador(cr, 470, 1440, "cuadro", t * 0.3, golpe=g if u < 0.5 else 1 - ease((u - 0.5) * 6))
        esc_ = ease((u - 0.85) * 6)
        luchador(cr, 900, 1440, "tri", t * 0.3, escudo=esc_, retro=40 * ease((u - 0.7) * 5))
        if u > 0.4:
            bx = lerp(620, 820, ease((u - 0.4) * 3))
            bola(cr, bx, 1270, 85 + 10 * math.sin(t * 15), t)
        if u > 0.7: chispas(cr, 840, 1270, t, 1.2, semilla=int(t * 8))
        tarjeta(cr, "GOLPE", 520, 800, 70, CIAN, esc=back(u * 6), rot=-0.05)
        if u > 0.38: tarjeta(cr, "+ ESPECIAL", 760, 940, 70, AMARILLO, esc=back((u - 0.38) * 6), rot=0.05)
        return ("cámara lenta" if u < 0.4 else "antes de reaccionar"), (CIAN if u < 0.4 else AMARILLO)
    if i == 5:
        arcade(cr, 620, 1260, 0.85, t, pantalla="pelea")
        rot = lerp(-0.9, -0.5, ease(u * 2))
        llave(cr, lerp(1050, 900, ease(u * 2)), 960, rot, 1.0)
        texto(cr, "¿?", 660, 880, 300 + 20 * math.sin(t * 9), CIAN, borde=16)
        return None, None
    if i == 6:
        if u < 0.35:
            boton(cr, 680, 1100, u < 0.22, u)
            if u > 0.22: texto(cr, "NO", 680, 900, 180, TINTA, borde=0)
            return "querían quitarlo", ROJO
        if u < 0.75:
            v = (u - 0.35) / 0.4
            chispas(cr, 680, 1150, t, 1.5, n=14, semilla=int(t * 6))
            for k, (n, x, y) in enumerate(((2, 480, 900), (3, 860, 1000), (4, 560, 1250), (5, 880, 1380))):
                contador(cr, x, y, n, t, esc=back(v * 4 - k * 0.7) * 0.75, col=TINTA, size=100, estcol=AMARILLO)
            return "más divertido", MAGENTA
        v = (u - 0.75) / 0.25
        candado(cr, 680, 1000, ease(v * 2.5), back(v * 4))
        return "escondido", MAGENTA
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    if i == 6:
        g.add_color_stop_rgb(0, *PLANO1); g.add_color_stop_rgb(1, *PLANO2)
        cr.set_source(g); cr.paint()
        # rayos de impacto girando
        cr.save(); cr.translate(W / 2, 1150); cr.rotate(t * 0.3)
        for k in range(16):
            a = k * math.pi / 8
            cr.move_to(0, 0); cr.line_to(math.cos(a) * 1600, math.sin(a) * 1600); cr.line_to(math.cos(a + 0.12) * 1600, math.sin(a + 0.12) * 1600)
            cr.close_path(); cr.set_source_rgba(1, 1, 1, 0.13); cr.fill()
        cr.restore()
        return
    g.add_color_stop_rgb(0, *FONDO1); g.add_color_stop_rgb(1, *FONDO2)
    cr.set_source(g); cr.paint()
    # puntos de trama (semitono) que suben (antes: niebla que se desplaza)
    for row in range(26):
        y = (row * 80 - (t * 50) % 80) + 40
        r = 4 + 8 * (y / H)
        for col in range(15):
            x = col * 80 + (40 if row % 2 else 0)
            cr.new_sub_path(); cr.arc(x, y, r, 0, 2 * math.pi)
        cr.set_source_rgba(*MAGENTA, 0.10); cr.fill()
    if i == 4:
        cr.set_source_rgba(1, 1, 1, 0.08); cr.set_line_width(6)
        rnd = random.Random(int(t * 10))
        for k in range(18):
            y = rnd.uniform(700, 1700); x = rnd.uniform(0, W)
            cr.move_to(x, y); cr.line_to(x + 300, y); cr.stroke()


def gancho(cr, t):
    # entrada nueva: cada línea "golpea" la pantalla, de grande a su tamaño con rebote y sacudida corta,
    # legible completa desde el cuadro 0 (antes: letras que parpadeaban como luz que falla)
    ys = [600, 780]
    for k, (s, y) in enumerate(zip(GANCHO["lineas"], ys)):
        z = 170
        font(cr, z)
        while cr.text_extents(s).x_advance > 990: z -= 4; font(cr, z)
        # pulso de impacto 1.0 → 1.07 → 1.0 (al cuadro 0 ya está completo y a tamaño normal)
        d = max(0, t - k * 0.12)
        esc = 1.0 + 0.07 * math.sin(min(1, d / 0.3) * math.pi)
        sh = 10 * math.sin(t * 60) * max(0, 1 - t / 0.5)
        cr.save(); cr.translate(W / 2 + sh, y - z * 0.35); cr.rotate(-0.03 if k == 0 else 0.02); cr.scale(esc, esc)
        wtot = cr.text_extents(s).x_advance; x = -wtot / 2
        ini_res = s.find(GANCHO["resalta"]) if GANCHO["resalta"] in s else 99
        if ini_res < 99:
            xa = x + cr.text_extents(s[:ini_res]).x_advance
            texto(cr, s[:ini_res], x, z * 0.35, z, BLANCO, centro=False, borde=28)
            texto(cr, s[ini_res:], xa, z * 0.35, z, AMARILLO, centro=False, borde=28)
        else:
            texto(cr, s, x, z * 0.35, z, BLANCO, centro=False, borde=28)
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


def u4(t): return local(4, t)


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: "golpe de zoom" al entrar cada escena (1.10 → 1.0 con rebote) + deslizamiento lateral lento
    # (antes: cámara en mano con temblor + acercamiento continuo)
    d = t - L[i]["t0"]
    zc = 1.0 + 0.10 * math.exp(-max(0, d) * 6) * math.cos(max(0, d) * 14)
    hx = 25 * math.sin(t * 0.6)
    cr.save()
    # nada del dibujo entra en la zona de la mascota
    cr.rectangle(0, 0, W, 1300); cr.rectangle(320, 1300, W - 320, 360); cr.rectangle(0, 1660, W, H - 1660); cr.clip()
    cr.translate(660 + hx, 1150); cr.scale(zc, zc); cr.translate(-660, -1150)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 4 and 0.28 < u4(t) < 0.42:  # destello del golpe, a pantalla completa
        cr.set_source_rgba(1, 1, 1, 0.6 * (1 - abs(u4(t) - 0.35) / 0.07)); cr.paint()
    vg = cairo.RadialGradient(W / 2, 1050, 400, W / 2, 1050, 1200)
    vg.add_color_stop_rgba(0, 0, 0, 0, 0); vg.add_color_stop_rgba(1, 0, 0, 0, 0.45)
    cr.set_source(vg); cr.paint()
    if i == 0 and t < L[0]["t1"] + 0.1:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1560, col, 40)
    chipb(cr, "Secretos de videojuegos", 360, 1760, CIAN, 34)
    cr.set_source_rgba(0, 0, 0, 0.3); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*AMARILLO); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        dd = t - x["t0"]
        if 0 <= dd < 0.10:
            cr.set_source_rgba(1, 1, 1, 0.45 * (1 - dd / 0.10)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0, 1.5] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [5.5, 8.0, 17.5, 20.5, 25.5, 27.5, 29.5, round(L[-1]["t1"] - 0.3, 1)]
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
