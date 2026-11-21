"""Motor de respaldo Pixel Diario — Short 'GTA existe gracias a policías locos'.
Dibuja con cairo, sin personajes, coches reconocibles, logos ni diseños de GTA/Rockstar: ciudad genérica en cuadrícula
vista desde arriba, coches y patrullas como rectángulos genéricos con torreta roja/azul, disquete genérico, sellos.
"GTA" y "Race'n'Chase" solo como texto. Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["LA POLICÍA", "ENLOQUECIÓ"], "resalta": "ENLOQUECIÓ"}

# paleta nueva: noche azul marino + rojo/azul de sirena + amarillo neón (antes: gris niebla + rojo óxido + hueso)
FONDO1 = (0.07, 0.10, 0.22)
FONDO2 = (0.02, 0.03, 0.08)
ASFALTO = (0.16, 0.18, 0.26)
BLOQUE = (0.24, 0.30, 0.46)
BLOQUE2 = (0.30, 0.24, 0.42)
TECHO = (0.36, 0.44, 0.62)
NEON = (1.0, 0.86, 0.12)
SIRR = (1.0, 0.18, 0.22)
SIRA = (0.20, 0.55, 1.0)
VERDE = (0.25, 0.95, 0.45)
BLANCO = (1, 1, 1)
TINTA = (0.03, 0.03, 0.06)
GRIS = (0.62, 0.66, 0.76)
JUGADOR = (1.0, 0.55, 0.10)

RESALTA = {1: ["noventa,", "Race'n'Chase."], 2: ["Carreras", "policía"], 3: ["Pero", "aburrido", "trababa"],
           4: ["cancelarlo."], 5: ["Pero", "seguirte…", "embestirte."], 6: ["¿Qué", "pasó?", "error:", "rodear", "través"],
           7: ["encantó,", "todo", "juego"], 8: ["choca", "error", "saga."]}
COLRES = {1: NEON, 2: NEON, 3: SIRR, 4: SIRR, 5: NEON, 6: NEON, 7: VERDE, 8: NEON}


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


def chipb(cr, s, x, y, color, size=34):
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: cinta amarilla de escena con franjas
    diagonales en los extremos y texto negro (antes: placa de metal oxidado con remaches)."""
    x = max(x, 340)
    font(cr, size); tw = cr.text_extents(s).x_advance; w = tw + 120; h = size + 30
    cr.save(); cr.translate(x, y); cr.rotate(-0.02)
    cr.rectangle(6, 6, w, h); cr.set_source_rgba(0, 0, 0, 0.5); cr.fill()
    cr.rectangle(0, 0, w, h); cr.set_source_rgb(*color); cr.fill()
    cr.save(); cr.rectangle(0, 0, 40, h); cr.rectangle(w - 40, 0, 40, h); cr.clip()
    for k in range(-2, int(w / 18) + 4):
        cr.move_to(k * 18, h); cr.line_to(k * 18 + h, 0); cr.line_to(k * 18 + h + 9, 0); cr.line_to(k * 18 + 9, h); cr.close_path()
    cr.set_source_rgb(*TINTA); cr.fill(); cr.restore()
    cr.set_source_rgb(*TINTA); cr.move_to(60, size + 6); cr.show_text(s)
    cr.restore()


def tarjeta(cr, s, x, y, size, color, esc=1.0, rot=0.0, fondo=TINTA):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 70
    cr.rectangle(-w / 2 + 10, -size * 0.95 + 12, w, size * 1.5); cr.set_source_rgb(*color); cr.fill()
    cr.rectangle(-w / 2, -size * 0.95, w, size * 1.5); cr.set_source_rgb(*fondo); cr.fill_preserve()
    cr.set_source_rgb(*color); cr.set_line_width(6); cr.stroke()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 35, size * 0.25); cr.show_text(s)
    cr.restore()


def sello(cr, s, x, y, esc, rot, alfa=1.0, color=SIRR):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, 110); w = cr.text_extents(s).x_advance + 80
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
            col = COLRES.get(i, NEON) if p in RESALTA.get(i, []) else BLANCO
            if acc > vis: col = (0.60, 0.64, 0.78)
            font(cr, size); adv = cr.text_extents(p + " ").x_advance
            cr.move_to(x, y); cr.text_path(p)
            cr.set_source_rgba(*TINTA, 1); cr.set_line_width(12); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve()
            cr.set_source_rgba(*col, 1); cr.fill()
            x += adv
        y += 88


# ---------- ciudad genérica vista desde arriba ----------
CALLES_H = [960, 1250, 1540]
CALLES_V = [180, 520, 860]
ANCHO = 110


def ciudad(cr, t, nuevos=None):
    """cuadrícula de manzanas en y 850–1700. nuevos: escala 0..1 de manzanas extra que aparecen (escena 7)."""
    cr.rectangle(-200, 850, W + 400, 900); cr.set_source_rgb(*ASFALTO); cr.fill()
    rnd = random.Random(4)
    ys = [850] + [y + ANCHO / 2 for y in CALLES_H]
    ye = [y - ANCHO / 2 for y in CALLES_H] + [1750]
    xs = [-200] + [x + ANCHO / 2 for x in CALLES_V]
    xe = [x - ANCHO / 2 for x in CALLES_V] + [W + 200]
    n = 0
    for a, b in zip(ys, ye):
        for c, d in zip(xs, xe):
            esc = 1.0
            if nuevos is not None:
                esc = nuevos[n % len(nuevos)]
            n += 1
            if esc <= 0.01: continue
            cx, cy = (c + d) / 2, (a + b) / 2; w, h = (d - c) * esc, (b - a) * esc
            cr.rectangle(cx - w / 2, cy - h / 2, w, h); cr.set_source_rgb(*(BLOQUE if n % 2 else BLOQUE2)); cr.fill()
            # techos de edificios dentro de la manzana
            for k in range(3):
                bw = w * rnd.uniform(0.22, 0.34); bh = h * rnd.uniform(0.3, 0.42)
                bx = cx - w / 2 + 14 + k * (w - 28) / 3; by = cy - h / 2 + 14 + rnd.uniform(0, h * 0.4)
                cr.rectangle(bx, by, bw, bh); cr.set_source_rgb(*TECHO); cr.fill()
                cr.rectangle(bx + 6, by + 6, bw - 12, 6); cr.set_source_rgba(1, 1, 1, 0.12); cr.fill()
    # líneas discontinuas de las calles
    cr.set_source_rgba(*NEON, 0.55); cr.set_line_width(5); cr.set_dash([28, 26], (t * 40) % 54)
    for y in CALLES_H:
        cr.move_to(-100, y); cr.line_to(W + 100, y); cr.stroke()
    for x in CALLES_V:
        cr.move_to(x, 850); cr.line_to(x, 1750); cr.stroke()
    cr.set_dash([])


def coche(cr, x, y, ang, t, policia=False, esc=1.0, color=JUGADOR):
    """rectángulo genérico visto desde arriba; policía: blanco y negro con torreta roja/azul."""
    cr.save(); cr.translate(x, y); cr.rotate(ang); cr.scale(esc, esc)
    rrect(cr, -58 + 6, -30 + 8, 116, 60, 14); cr.set_source_rgba(0, 0, 0, 0.45); cr.fill()
    rrect(cr, -58, -30, 116, 60, 14)
    cr.set_source_rgb(*((0.95, 0.95, 0.97) if policia else color)); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
    if policia:
        cr.rectangle(-58 + 30, -30, 30, 60); cr.set_source_rgb(0.08, 0.08, 0.12); cr.fill()
    rrect(cr, 12, -22, 22, 44, 6); cr.set_source_rgb(0.15, 0.25, 0.40); cr.fill()  # parabrisas
    rrect(cr, -46, -20, 14, 40, 5); cr.set_source_rgb(0.15, 0.25, 0.40); cr.fill()
    if policia:
        on = math.sin(t * 18) > 0
        cr.rectangle(-8, -20, 12, 20); cr.set_source_rgb(*(SIRR if on else (0.4, 0.1, 0.1))); cr.fill()
        cr.rectangle(-8, 0, 12, 20); cr.set_source_rgb(*(SIRA if not on else (0.1, 0.2, 0.4))); cr.fill()
        g = cairo.RadialGradient(-2, -10 if on else 10, 2, -2, -10 if on else 10, 90)
        c = SIRR if on else SIRA
        g.add_color_stop_rgba(0, *c, 0.55); g.add_color_stop_rgba(1, *c, 0)
        cr.set_source(g); cr.arc(-2, 0, 90, 0, 2 * math.pi); cr.fill()
    cr.restore()


def chispas(cr, x, y, t, fuerza=1.0, sem=1):
    rnd = random.Random(sem + int(t * 12))
    for k in range(int(14 * fuerza)):
        a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(20, 110) * fuerza
        cr.move_to(x + math.cos(a) * r * 0.3, y + math.sin(a) * r * 0.3); cr.line_to(x + math.cos(a) * r, y + math.sin(a) * r)
        cr.set_source_rgb(*(NEON if k % 2 else BLANCO)); cr.set_line_width(5); cr.stroke()


def estrella(cr, x, y, r, col=NEON, s=None, size=60):
    cr.save(); cr.translate(x, y)
    for k in range(20):
        a = k * math.pi / 10; rr = r if k % 2 == 0 else r * 0.55
        (cr.move_to if k == 0 else cr.line_to)(math.cos(a) * rr, math.sin(a) * rr)
    cr.close_path(); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()
    cr.restore()
    if s: texto(cr, s, x, y + size * 0.35, size, SIRR, borde=8)


def escena_a(cr, t, i):
    """inicio y cierre: ciudad en cuadrícula, la patrulla zigzaguea por la calle central y choca con las esquinas.
    Nada en y 300–820 (el texto del gancho va encima)."""
    ciudad(cr, t)
    u = (t * 0.16) % 1.0
    x = lerp(360, 1000, u)
    y = 1250 + 48 * math.sin(t * 5.5)
    ang = 0.45 * math.cos(t * 5.5)
    coche(cr, x, y, ang, t, policia=True, esc=1.25)
    if abs(math.sin(t * 5.5)) > 0.96:
        chispas(cr, x + 60, y + (60 if math.sin(t * 5.5) > 0 else -60), t, 0.8)
    # coche del jugador huyendo arriba
    coche(cr, (lerp(560, 1250, u) % 1200), 960, 0, t, esc=1.0)


def disquete(cr, x, y, esc, rot):
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    rrect(cr, -150, -150, 300, 300, 18); cr.set_source_rgb(0.15, 0.17, 0.25); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
    cr.rectangle(-80, -150, 160, 100); cr.set_source_rgb(*GRIS); cr.fill()
    cr.rectangle(30, -135, 30, 70); cr.set_source_rgb(0.15, 0.17, 0.25); cr.fill()
    cr.rectangle(-110, 10, 220, 120); cr.set_source_rgb(0.96, 0.94, 0.88); cr.fill()
    for k in range(3):
        cr.move_to(-90, 45 + k * 30); cr.line_to(90, 45 + k * 30); cr.set_source_rgb(0.6, 0.6, 0.7); cr.set_line_width(3); cr.stroke()
    cr.restore()


def escena(cr, t):
    i = linea_en(t)
    if i in (0, 8):
        escena_a(cr, t, i)
        return ("GTA", NEON) if i == 0 else ("el error que lo salvó", NEON)
    u = local(i, t)
    if i == 1:
        ciudad(cr, t * 0.3)
        cr.rectangle(-200, 850, W + 400, 900); cr.set_source_rgba(*FONDO2, 0.6); cr.fill()
        disquete(cr, 680, lerp(1750, 1330, back(u * 3)), 0.9, 0.08 * math.sin(t * 2))
        tarjeta(cr, "RACE'N'CHASE", 680, 960, 86, NEON, esc=back((u - 0.1) * 4), rot=-0.04)
        if u > 0.55:
            v = ease((u - 0.55) * 5)
            cr.move_to(380, 950); cr.line_to(380 + 600 * v, 935); cr.set_source_rgb(*SIRR); cr.set_line_width(16); cr.stroke()
        if u > 0.75:
            texto(cr, "¿GTA?", 940, 1100, 90 * back((u - 0.75) * 6) + 1, SIRR, borde=10)
        return ("otro nombre" if u < 0.55 else "todavía no era GTA"), NEON
    if i == 2:
        ciudad(cr, t)
        x = lerp(380, 1000, u)
        coche(cr, x, 1250, 0, t, esc=1.2)
        coche(cr, x - 330, 1250, 0, t, policia=True, esc=1.2)
        # distancia segura
        cr.set_dash([16, 12]); cr.move_to(x - 260, 1180); cr.line_to(x - 70, 1180); cr.set_source_rgb(*BLANCO); cr.set_line_width(4); cr.stroke(); cr.set_dash([])
        texto(cr, "distancia segura", x - 165, 1160, 34, BLANCO, borde=6)
        return "carreras + policía", NEON
    if i == 3:
        ciudad(cr, 0)
        coche(cr, 700, 1250, 0, 0, esc=1.2); coche(cr, 400, 1250, 0, 0, policia=True, esc=1.2)
        cr.rectangle(-200, 850, W + 400, 900); cr.set_source_rgba(0, 0, 0, 0.55); cr.fill()
        # glitch: franjas desplazadas
        rnd = random.Random(int(t * 10))
        for k in range(6):
            yy = rnd.uniform(870, 1680); cr.rectangle(rnd.uniform(-60, 60), yy, W, rnd.uniform(8, 30))
            cr.set_source_rgba(*(SIRR if k % 2 else SIRA), 0.35); cr.fill()
        if u < 0.55:
            tarjeta(cr, "ZZZ… ABURRIDO", 680, 1050, 70, GRIS, esc=back(u * 6), rot=0.03)
        tarjeta(cr, "ERROR", 680 + (rnd.uniform(-8, 8) if u > 0.4 else 0), 1300, 130, SIRR, esc=back((u - 0.35) * 5), rot=-0.05)
        if u > 0.6:
            v = (u - 0.6) / 0.4
            rrect(cr, 430, 1410, 500, 40, 12); cr.set_source_rgb(*GRIS); cr.set_line_width(5); cr.stroke()
            rrect(cr, 436, 1416, max(1, 488 * v), 28, 8); cr.set_source_rgb(*NEON); cr.fill()
            texto(cr, "REINICIANDO", 680, 1505, 40, BLANCO, borde=6)
        return ("aburrido" if u < 0.4 else "se trababa"), SIRR
    if i == 4:
        ciudad(cr, t * 0.2)
        cr.rectangle(-200, 850, W + 400, 900); cr.set_source_rgba(*FONDO2, 0.55); cr.fill()
        y = lerp(880, 1180, ease(u * 1.4))
        sello(cr, "CANCELADO", 680, y, 0.95, -0.12, 1.0)
        # se detiene a centímetros de la "hoja" del juego
        rrect(cr, 430, 1360, 500, 280, 16); cr.set_source_rgb(0.95, 0.94, 0.9); cr.fill()
        texto(cr, "RACE'N'CHASE", 680, 1450, 50, TINTA, borde=0)
        for k in range(3):
            cr.rectangle(470, 1490 + k * 40, 420, 14); cr.set_source_rgb(0.75, 0.75, 0.8); cr.fill()
        n = max(1, 3 - int(u * 3))
        texto(cr, str(n), 960, 1200, 150, NEON, borde=12)
        return "casi cancelado", SIRR
    if i == 5:
        ciudad(cr, t)
        px, py = 700, 1250
        sh = 0
        if u < 0.38:
            # te siguen en fila, a distancia
            for k in range(3):
                coche(cr, px - 260 - k * 170, py, 0, t, policia=True, esc=1.05)
            coche(cr, px, py, 0, t, esc=1.1)
            return "te seguían…", NEON
        v = (u - 0.38) / 0.62
        dests = [(-1, -1), (-1, 1), (1, -1)]
        for k, (dx, dy) in enumerate(dests):
            w = ease(v * 1.6)
            x = lerp(px + dx * 380, px + dx * 70, w); y = lerp(py + dy * 330, py + dy * 50, w)
            coche(cr, x, y, math.atan2(py - y, px - x), t, policia=True, esc=1.05)
        coche(cr, px + (10 * math.sin(t * 60) if v > 0.6 else 0), py, 0.15 * math.sin(t * 9) * (v > 0.6), t, esc=1.1)
        if v > 0.6:
            chispas(cr, px - 50, py - 30, t, 1.0, 2); chispas(cr, px + 50, py - 30, t, 1.0, 5); chispas(cr, px - 40, py + 40, t, 1.0, 7)
            estrella(cr, px + 200, py - 200, 110 * back((v - 0.6) * 5) + 1, NEON, "¡PUM!" if v > 0.7 else None, 54)
        return "¡te embisten!", SIRR
    if i == 6:
        if u < 0.14:
            ciudad(cr, t * 0.2)
            cr.rectangle(-200, 850, W + 400, 900); cr.set_source_rgba(*FONDO2, 0.7); cr.fill()
            texto(cr, "¿?", 680, 1420, 440 * back(u * 9) + 1, NEON, borde=18)
            return "¿qué pasó?", NEON
        v = (u - 0.14) / 0.86
        # diagrama: plano de calle oscuro
        cr.rectangle(-200, 850, W + 400, 900); cr.set_source_rgb(0.05, 0.08, 0.18); cr.fill()
        cr.set_source_rgba(1, 1, 1, 0.06); cr.set_line_width(2)
        for k in range(0, W + 1, 60): cr.move_to(k, 850); cr.line_to(k, 1750); cr.stroke()
        for k in range(850, 1751, 60): cr.move_to(0, k); cr.line_to(W, k); cr.stroke()
        cx, cy = 680, 1230
        coche(cr, cx, cy, -math.pi / 2, t, esc=1.2)
        # ruta correcta (rodea) verde punteada
        g = ease(v * 3)
        cr.set_dash([22, 16]); cr.set_source_rgb(*VERDE); cr.set_line_width(10)
        cr.move_to(cx, 1640); cr.curve_to(cx + 330 * g, 1500, cx + 330 * g, 960, cx, 900); cr.stroke(); cr.set_dash([])
        if v > 0.1: tarjeta(cr, "RODEAR", 900, 1050, 46, VERDE, esc=back((v - 0.1) * 5), rot=0.04)
        # ruta del error (atraviesa) roja
        if v > 0.3:
            r = ease((v - 0.3) * 3)
            cr.move_to(cx - 30, 1640); cr.line_to(cx - 30, lerp(1640, cy + 60, r)); cr.set_source_rgb(*SIRR); cr.set_line_width(12); cr.stroke()
            tarjeta(cr, "ATRAVESAR", 470, 1480, 46, SIRR, esc=back((v - 0.3) * 5), rot=-0.04)
            yy = lerp(1640, cy + 95, r)
            coche(cr, cx - 30, yy, -math.pi / 2, t, policia=True, esc=1.05)
            if r >= 0.99:
                chispas(cr, cx - 20, cy + 50, t, 1.2, 3)
                estrella(cr, cx - 230, cy - 60, 90, NEON, "¡PUM!", 44)
        return ("un error" if v < 0.3 else "no sabían rodear"), NEON
    if i == 7:
        nuevos = [1.0 if k % 2 == 0 else ease((u - 0.3 - (k % 6) * 0.07) * 5) for k in range(12)]
        ciudad(cr, t, nuevos=nuevos)
        # persecución en el centro
        a = t * 2.2
        coche(cr, 680 + 160 * math.cos(a), 1250 + 90 * math.sin(a), a + math.pi / 2, t, esc=1.0)
        coche(cr, 680 + 160 * math.cos(a - 0.9), 1250 + 90 * math.sin(a - 0.9), a - 0.9 + math.pi / 2, t, policia=True, esc=1.0)
        if u < 0.45:
            v = u / 0.45
            sep = 0 if v < 0.35 else ease((v - 0.35) * 2.5) * 260
            cr.save(); cr.rectangle(0, 0, 680, H); cr.clip()
            sello(cr, "CANCELADO", 680 - sep, 1250 + sep * 0.4, 0.9, -0.12 - sep * 0.002, 1 - sep / 300)
            cr.restore(); cr.save(); cr.rectangle(680, 0, W, H); cr.clip()
            sello(cr, "CANCELADO", 680 + sep, 1250 + sep * 0.5, 0.9, -0.12 + sep * 0.002, 1 - sep / 300)
            cr.restore()
            if 0.3 < v < 0.5:
                cr.move_to(660, 1120); cr.line_to(700, 1200); cr.line_to(650, 1280); cr.line_to(710, 1380)
                cr.set_source_rgb(*BLANCO); cr.set_line_width(8); cr.stroke()
        else:
            tarjeta(cr, "TODO EL JUEGO", 680, 960, 70, VERDE, esc=back((u - 0.45) * 5), rot=-0.03)
        return ("se salvó" if u < 0.45 else "todo el juego alrededor"), VERDE
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *FONDO1); g.add_color_stop_rgb(1, *FONDO2)
    cr.set_source(g); cr.paint()
    # destellos de sirena que barren el fondo (antes: franjas de niebla)
    on = math.sin(t * 6) > 0
    c = SIRR if on else SIRA
    x = W * (0.2 if on else 0.8)
    rg = cairo.RadialGradient(x, 260, 20, x, 260, 700)
    rg.add_color_stop_rgba(0, *c, 0.22); rg.add_color_stop_rgba(1, *c, 0)
    cr.set_source(rg); cr.paint()
    # rejilla de mapa en perspectiva
    cr.set_source_rgba(1, 1, 1, 0.05); cr.set_line_width(2)
    for k in range(12):
        y = (k * 70 + t * 30) % 840
        cr.move_to(0, y); cr.line_to(W, y); cr.stroke()


def gancho(cr, t):
    # entrada nueva: el texto completo está desde el cuadro 0 con un destello rojo/azul de sirena que alterna detrás
    # de cada línea y un leve vaivén horizontal (antes: respiraba despacio con niebla detrás)
    ys = [600, 790]
    for k, (s, y) in enumerate(zip(GANCHO["lineas"], ys)):
        z = 175
        font(cr, z)
        while cr.text_extents(s).x_advance > 990: z -= 4; font(cr, z)
        on = (math.sin(t * 8) > 0) ^ (k == 1)
        cr.save(); cr.translate(W / 2 + 10 * math.sin(t * 3 + k * 2), y - z * 0.35)
        wtot = cr.text_extents(s).x_advance; x = -wtot / 2
        rrect(cr, x - 30, -z * 0.55, wtot + 60, z * 1.1, 26)
        cr.set_source_rgba(*(SIRR if on else SIRA), 0.85); cr.fill()
        if GANCHO["resalta"] in s:
            texto(cr, s, x, z * 0.35, z, NEON, centro=False, borde=26)
        else:
            texto(cr, s, x, z * 0.35, z, BLANCO, centro=False, borde=26)
        cr.restore()


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: paneo cenital que sigue la acción con un pequeño giro (antes: acercamiento lento + deriva)
    d = max(0, t - L[i]["t0"])
    zc = 1.0 + 0.04 * ease(d / 2.0)
    rot = 0.012 * math.sin(t * 0.7)
    sh = 0
    if i == 5 and local(5, t) > 0.38 + 0.62 * 0.6: sh = 12 * math.sin(t * 70)
    cr.save()
    cr.rectangle(0, 830, W, 470); cr.rectangle(320, 1300, W - 320, 360); cr.rectangle(0, 1660, W, 40); cr.clip()
    cr.translate(680 + sh, 1250); cr.rotate(rot); cr.scale(zc, zc); cr.translate(-680, -1250)
    eti, col = escena(cr, t)
    cr.restore()
    # borde superior de la "ventana" de la ciudad
    cr.set_source_rgba(*NEON, 0.8); cr.rectangle(0, 826, W, 6); cr.fill()
    vg = cairo.RadialGradient(W / 2, 1050, 450, W / 2, 1050, 1250)
    vg.add_color_stop_rgba(0, 0, 0, 0, 0); vg.add_color_stop_rgba(1, 0, 0, 0, 0.45)
    cr.set_source(vg); cr.paint()
    if i == 0 and t < L[0]["t1"] + 0.1:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1560, NEON if col != VERDE else VERDE, 40)
    chipb(cr, "Secretos de videojuegos", 360, 1760, GRIS, 34)
    cr.set_source_rgba(0, 0, 0, 0.3); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*NEON); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        dd = t - x["t0"]
        if 0 <= dd < 0.1:
            cr.set_source_rgba(1, 1, 1, 0.35 * (1 - dd / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0, 1.5] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [6.0, 13.0, 19.5, 22.0, 24.2, 26.0, 27.8, 29.5, round(L[-1]["t1"] - 0.3, 1)]
        for t in ts:
            cuadro(t).write_to_png(f"prueba/t{t:05.1f}.png")
    elif modo == "hoja":
        pass
    else:
        n = int(DUR * FPS)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-i", "mezcla.wav", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
                              "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", "short.mp4"], stdin=subprocess.PIPE)
        for f in range(n):
            p.stdin.write(bytes(cuadro(f / FPS).get_data()))
        p.stdin.close(); p.wait()
