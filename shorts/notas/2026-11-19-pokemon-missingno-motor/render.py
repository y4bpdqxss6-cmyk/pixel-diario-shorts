"""Motor de respaldo Pixel Diario — Short 'Pokémon Rojo tenía un error que daba objetos'.
Dibuja con cairo, sin personajes, sprites, logos ni diseños reconocibles: mochila genérica, anciano geométrico,
isla simple, bloque de glitch con rectángulos aleatorios, revista genérica. "Pokémon", "MissingNo." y "Nintendo"
solo como texto. Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["UN ERROR", "QUE REGALA"], "resalta": "REGALA"}

# paleta nueva: mar turquesa + arena + coral (antes: noche violeta + cian neón + magenta)
FONDO1 = (0.02, 0.36, 0.42)
FONDO2 = (0.01, 0.16, 0.24)
MAR = (0.10, 0.62, 0.72)
MAR_O = (0.05, 0.40, 0.52)
ARENA = (0.98, 0.84, 0.55)
CORAL = (1.0, 0.42, 0.36)
LIMA = (0.62, 0.95, 0.30)
AMARILLO = (1.0, 0.86, 0.22)
LILA = (0.72, 0.55, 1.0)
GRIS = (0.62, 0.64, 0.68)
BLANCO = (1, 1, 1)
TINTA = (0.03, 0.08, 0.12)
PLANO1 = (0.95, 0.45, 0.30)
PLANO2 = (0.65, 0.18, 0.28)
CAJAS = (CORAL, LIMA, AMARILLO, LILA, (0.35, 0.80, 1.0))

RESALTA = {1: ["viejito", "atrapar"], 2: ["isla", "costa,"], 3: ["Pero", "bloque", "píxeles", "rotos."],
           4: ["sexto", "objeto", "128", "más."], 5: ["raro."], 6: ["¿Por", "qué?", "nombre,", "Pokémon", "salvajes."],
           7: ["no", "tocarlo."], 8: ["error", "regalo", "mochila."]}
COLRES = {1: AMARILLO, 2: ARENA, 3: CORAL, 4: LIMA, 5: CORAL, 6: AMARILLO, 7: CORAL, 8: LIMA}


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
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: píldora de color lleno con
    texto oscuro y un cuadrito pixelado a la izquierda (antes: rectángulo oscuro con borde neón y barra lateral)."""
    x = max(x, 340)
    font(cr, size); w = cr.text_extents(s).x_advance + 90; h = size + 34
    rrect(cr, x + 6, y + 8, w, h, h / 2); cr.set_source_rgba(0, 0, 0, 0.35); cr.fill()
    rrect(cr, x, y, w, h, h / 2); cr.set_source_rgb(*color); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(4); cr.stroke()
    for k in range(4):
        cr.rectangle(x + 22 + (k % 2) * 12, y + h / 2 - 12 + (k // 2) * 12, 10, 10)
    cr.set_source_rgb(*TINTA); cr.fill()
    cr.set_source_rgb(*TINTA); cr.move_to(x + 60, y + size + 8); cr.show_text(s)


def tarjeta(cr, s, x, y, size, color, esc=1.0, rot=0.0, fondo=BLANCO):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 70
    rrect(cr, -w / 2 + 8, -size * 0.95 + 10, w, size * 1.5, 20); cr.set_source_rgba(0, 0, 0, 0.4); cr.fill()
    rrect(cr, -w / 2, -size * 0.95, w, size * 1.5, 20); cr.set_source_rgb(*fondo); cr.fill()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 35, size * 0.25); cr.text_path(s)
    cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke_preserve(); cr.set_source_rgb(*color); cr.fill()
    cr.restore()


def caja(cr, x, y, s, col, rot=0.0, a=1.0):
    cr.save(); cr.translate(x, y); cr.rotate(rot)
    rrect(cr, -s / 2, -s / 2, s, s, s * 0.15); cr.set_source_rgba(*col, a); cr.fill_preserve()
    cr.set_source_rgba(*TINTA, a); cr.set_line_width(5); cr.stroke()
    cr.rectangle(-s * 0.08, -s / 2, s * 0.16, s); cr.set_source_rgba(1, 1, 1, 0.55 * a); cr.fill()
    cr.restore()


# ---------- dibujos genéricos ----------
def mochila(cr, cx, cy, esc, t, abre=1.0):
    cr.save(); cr.translate(cx, cy); cr.scale(esc, esc)
    # tirantes
    cr.set_source_rgb(0.55, 0.20, 0.18); cr.set_line_width(26)
    cr.move_to(-120, -110); cr.curve_to(-200, -60, -200, 80, -150, 140); cr.stroke()
    cr.move_to(120, -110); cr.curve_to(200, -60, 200, 80, 150, 140); cr.stroke()
    rrect(cr, -170, -130, 340, 300, 70); cr.set_source_rgb(*CORAL); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(9); cr.stroke()
    rrect(cr, -100, 40, 200, 100, 26); cr.set_source_rgb(0.85, 0.32, 0.28); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
    # solapa que se abre
    cr.save(); cr.translate(0, -130); cr.rotate(-0.5 * abre)
    rrect(cr, -175, -20, 350, 110, 50); cr.set_source_rgb(0.92, 0.36, 0.32); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
    cr.restore()
    cr.restore()


def escena_a(cr, t, i):
    """imagen del inicio y del cierre: mochila de la que salen cajitas que se multiplican + contador ×1 → ×129.
    Nada en y 300–820 (el texto del gancho va encima)."""
    t0 = L[i]["t0"]
    mochila(cr, 640, 1170, 1.0 + 0.03 * math.sin(t * 7), t)
    rnd = random.Random(3)
    n = 22
    for k in range(n):
        ph = (t * 0.9 + k / n) % 1.0
        ang = rnd.uniform(-1.1, 1.1)
        v = rnd.uniform(380, 520)
        x = 640 + math.sin(ang) * v * ph * 0.9
        y = 1050 - (math.cos(ang) * v * 1.25 * ph - 420 * ph * ph)
        y = max(y, 900)
        caja(cr, x, y, 46 + 30 * ph, CAJAS[k % 5], rot=ph * 4 + k, a=min(1, (1 - ph) * 3))
    u = ease((t - t0) / 2.5)
    num = int(lerp(1, 129, u)) if i == 0 else 129
    tarjeta(cr, f"×{num}", 900, 1440, 84, LIMA, esc=1.0 + 0.06 * math.sin(t * 9), rot=0.06, fondo=TINTA)


def pueblo(cr, t, u):
    for k, (x, w, h, col) in enumerate(((420, 180, 200, CORAL), (650, 220, 260, LILA), (880, 170, 180, AMARILLO))):
        e = back(u * 3 - k * 0.2)
        if e <= 0.01: continue
        cr.save(); cr.translate(x, 1240); cr.scale(1, e)
        cr.rectangle(-w / 2, -h, w, h); cr.set_source_rgb(*col); cr.fill_preserve()
        cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
        cr.move_to(-w / 2 - 20, -h); cr.line_to(0, -h - 80); cr.line_to(w / 2 + 20, -h); cr.close_path()
        cr.set_source_rgb(*MAR_O); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.stroke()
        cr.rectangle(-25, -70, 50, 70); cr.set_source_rgb(*TINTA); cr.fill()
        cr.restore()
    cr.rectangle(340, 1240, W, 30); cr.set_source_rgb(*ARENA); cr.fill()


def anciano(cr, x, y, t, esc):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y + 6 * math.sin(t * 5)); cr.scale(esc, esc)
    rrect(cr, -60, -150, 120, 170, 30); cr.set_source_rgb(0.55, 0.45, 0.35); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
    cr.new_sub_path(); cr.arc(0, -200, 52, 0, 2 * math.pi); cr.set_source_rgb(0.98, 0.82, 0.68); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.stroke()
    cr.new_sub_path(); cr.arc(-18, -205, 6, 0, 2 * math.pi); cr.arc(18, -205, 6, 0, 2 * math.pi); cr.fill()
    cr.set_source_rgb(0.92, 0.92, 0.92); cr.move_to(-40, -185); cr.curve_to(-30, -140, 30, -140, 40, -185); cr.fill()
    cr.set_source_rgb(0.45, 0.28, 0.12); cr.set_line_width(12); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.move_to(90, -120); cr.line_to(100, 20); cr.stroke(); cr.move_to(90, -120); cr.curve_to(90, -150, 60, -150, 60, -130); cr.stroke()
    cr.restore()


def globo(cr, s, x, y, esc):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    font(cr, 38); w = cr.text_extents(s).x_advance + 60; h = 90
    rrect(cr, -w / 2, -h / 2, w, h, 40); cr.move_to(-40, h / 2 - 2); cr.line_to(-80, h / 2 + 60); cr.line_to(10, h / 2 - 2)
    cr.set_source_rgb(*BLANCO); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
    cr.set_source_rgb(*TINTA); cr.move_to(-w / 2 + 30, 14); cr.show_text(s)
    cr.restore()


def isla(cr, t, u):
    cr.save(); cr.rectangle(330, 760, W - 330, 760); cr.clip()
    cr.set_source_rgb(*MAR); cr.paint()
    cr.set_source_rgba(1, 1, 1, 0.25); cr.set_line_width(5)
    for k in range(10):
        y = 800 + k * 75; off = (t * 60 + k * 37) % 140
        for x in range(330 - 140, W, 140):
            cr.move_to(x + off, y); cr.curve_to(x + off + 25, y - 15, x + off + 45, y - 15, x + off + 70, y); cr.stroke()
    # isla
    cr.new_sub_path(); cr.save(); cr.translate(640, 1130); cr.scale(1.0, 1.25); cr.arc(0, 0, 190, 0, 2 * math.pi); cr.restore()
    cr.set_source_rgb(*ARENA); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
    cr.new_sub_path(); cr.save(); cr.translate(620, 1120); cr.scale(1.0, 1.2); cr.arc(0, 0, 120, 0, 2 * math.pi); cr.restore()
    cr.set_source_rgb(*LIMA); cr.fill()
    # flecha que vuela (primera mitad)
    if u < 0.45:
        v = ease(u / 0.4)
        x = lerp(360, 640, v); y = lerp(800, 1100, v) - 200 * math.sin(math.pi * v)
        cr.set_source_rgb(*BLANCO); cr.set_line_width(12); cr.set_dash([22, 16])
        cr.move_to(360, 800); cr.curve_to(450, 650, 560, 800, x, y); cr.stroke(); cr.set_dash([])
        cr.new_sub_path(); cr.arc(x, y, 24, 0, 2 * math.pi); cr.set_source_rgb(*AMARILLO); cr.fill()
    else:
        v = (u - 0.45) / 0.55
        y = 1130 + 230 * math.sin(v * math.pi * 3)
        x = 860
        cr.save(); cr.translate(x, y)
        rrect(cr, -22, -60, 44, 120, 22); cr.set_source_rgb(*CORAL); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
        cr.new_sub_path(); cr.arc(0, -10, 20, 0, 2 * math.pi); cr.set_source_rgb(*AMARILLO); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.stroke()
        cr.restore()
        cr.set_source_rgb(*BLANCO); cr.set_line_width(6)
        for s in (-1, 1):
            cr.move_to(905, 1130 + s * 120); cr.line_to(905, 1130 + s * 230); cr.stroke()
            cr.move_to(890, 1130 + s * 215); cr.line_to(905, 1130 + s * 235); cr.line_to(920, 1130 + s * 215); cr.stroke()
    cr.restore()


def glitch(cr, cx, cy, t, u, ancho=420, alto=520, semilla=None):
    rnd = random.Random(semilla if semilla is not None else int(t * 12))
    e = max(0.01, back(u * 3))
    for k in range(70):
        w = rnd.choice((20, 40, 60, 80)); h = rnd.choice((20, 40, 60))
        x = cx + rnd.uniform(-ancho / 2, ancho / 2 - w) * e
        y = cy + rnd.uniform(-alto / 2, alto / 2 - h) * e
        col = rnd.choice((TINTA, BLANCO, GRIS, CORAL, LILA, (0.2, 0.2, 0.25)))
        cr.rectangle(x, y, w * e, h * e); cr.set_source_rgb(*col); cr.fill()


def lista(cr, t, u):
    x0, y0 = 380, 820
    rrect(cr, x0, y0, 600, 640, 26); cr.set_source_rgb(0.97, 0.96, 0.92); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(9); cr.stroke()
    for k in range(6):
        a = ease(u * 4 - k * 0.25)
        if a <= 0: continue
        y = y0 + 60 + k * 95
        caja(cr, x0 + 70, y + 20, 50, CAJAS[k % 5], a=a)
        cr.rectangle(x0 + 120, y + 8, 240 - k * 15, 24); cr.set_source_rgba(*GRIS, a); cr.fill()
        if k == 5:
            v = ease((u - 0.5) * 4)
            s = "×1" if v < 0.5 else "×129"
            if 0.3 < v < 1:
                cr.set_source_rgba(*LIMA, 0.5 * math.sin(math.pi * v)); rrect(cr, x0 + 20, y - 25, 560, 90, 18); cr.fill()
            texto(cr, s, x0 + 500, y + 40, 60 * (1 + 0.25 * math.sin(math.pi * v)), LIMA if v >= 0.5 else TINTA,
                  borde=8 if v >= 0.5 else 0, alpha=a)
            cr.move_to(x0 + 20, y - 25); cr.set_source_rgb(*CORAL); cr.set_line_width(6)
            rrect(cr, x0 + 18, y - 27, 564, 94, 18); cr.stroke()
        else:
            texto(cr, "×1", x0 + 500, y + 40, 52, TINTA, borde=0, alpha=a)


def nombre_cae(cr, t, u):
    letras = "ROJO"; hexs = ["52", "4F", "4A", "4F"]
    # agua abajo (a la derecha de la zona de la mascota)
    cr.save(); cr.rectangle(330, 1240, W - 330, 300); cr.clip()
    cr.set_source_rgb(*MAR); cr.paint()
    cr.set_source_rgba(1, 1, 1, 0.35); cr.set_line_width(5)
    for k in range(4):
        y = 1270 + k * 60; off = (t * 80 + k * 50) % 140
        for x in range(190, W, 140):
            cr.move_to(x + off, y); cr.curve_to(x + off + 25, y - 15, x + off + 45, y - 15, x + off + 70, y); cr.stroke()
    cr.restore()
    for k in range(4):
        x = 440 + k * 150
        tr = ease((u - 0.25 - k * 0.05) * 4)
        cae = ease((u - 0.6 - k * 0.05) * 3.5)
        y = lerp(950, 1300, cae ** 1.6)
        if cae >= 0.999: continue
        cr.save(); cr.translate(x, y); cr.rotate(cae * (0.6 if k % 2 else -0.6))
        rrect(cr, -62, -75, 124, 150, 18); cr.set_source_rgb(*(BLANCO if tr < 0.5 else TINTA)); cr.fill_preserve()
        cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
        s = letras[k] if tr < 0.5 else hexs[k]
        texto(cr, s, 0, 35, 96 if tr < 0.5 else 70, TINTA if tr < 0.5 else LIMA, borde=0)
        cr.restore()
        if cae > 0.85:
            a = (cae - 0.85) / 0.15
            for s in (-1, 1):
                cr.new_sub_path(); cr.arc(x + s * 40 * a, 1250 - 50 * math.sin(math.pi * a), 12, 0, 2 * math.pi)
                cr.set_source_rgba(1, 1, 1, 1 - a); cr.fill()
    if u > 0.55:
        tarjeta(cr, "= Pokémon salvajes", 660, 1150 if u < 0.6 else 860, 60, AMARILLO, esc=back((u - 0.55) * 5), rot=-0.03, fondo=TINTA)


def revista(cr, t, u):
    e = max(0.01, back(u * 3))
    cr.save(); cr.translate(660, 1080); cr.rotate(-0.08); cr.scale(e, e)
    rrect(cr, -210, -280, 420, 560, 14); cr.set_source_rgb(*BLANCO); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(9); cr.stroke()
    cr.rectangle(-210, -280, 420, 120); cr.set_source_rgb(*MAR_O); cr.fill()
    texto(cr, "REVISTA", 0, -200, 64, BLANCO, borde=0)
    texto(cr, "1999", 0, -60, 110, CORAL, borde=8)
    for k in range(5):
        cr.rectangle(-160, 20 + k * 45, 320 - (k % 2) * 80, 20); cr.set_source_rgb(*GRIS); cr.fill()
    cr.restore()
    if u > 0.4:
        s = max(0.01, back((u - 0.4) * 4))
        cr.save(); cr.translate(660, 1290); cr.rotate(0.18); cr.scale(lerp(2.2, 1.0, min(1, (u - 0.4) * 5)) * s, lerp(2.2, 1.0, min(1, (u - 0.4) * 5)) * s)
        font(cr, 72); w = cr.text_extents("¡CUIDADO!").x_advance + 60
        rrect(cr, -w / 2, -66, w, 106, 16); cr.set_source_rgba(*CORAL, 0.25); cr.fill_preserve()
        cr.set_source_rgb(*CORAL); cr.set_line_width(12); cr.stroke()
        texto(cr, "¡CUIDADO!", 0, 12, 72, CORAL, borde=6)
        cr.restore()


def escena(cr, t):
    i = linea_en(t)
    if i in (0, 8):
        escena_a(cr, t, i)
        return ("POKÉMON ROJO Y AZUL", CORAL) if i == 0 else ("un regalo", LIMA)
    u = local(i, t)
    if i == 1:
        pueblo(cr, t, u)
        anciano(cr, 760, 1230, t, back(u * 3 - 0.4))
        if u > 0.35: globo(cr, "¿Quieres ver cómo se atrapa?", 640, 850, back((u - 0.35) * 5))
        return "el viejito", AMARILLO
    if i == 2:
        isla(cr, t, u)
        return "la costa de la isla", ARENA
    if i == 3:
        glitch(cr, 660, 1080, t, u)
        if u > 0.5: tarjeta(cr, "MISSINGNO.", 660, 860, 84, CORAL, esc=back((u - 0.5) * 5), rot=-0.05, fondo=TINTA)
        return "píxeles rotos", CORAL
    if i == 4:
        lista(cr, t, u)
        return "+128 objetos", LIMA
    if i == 5:
        glitch(cr, 660, 1050, t, 1.0, 560, 400, semilla=int(t * 6))
        tarjeta(cr, "+128", 660, 1080, 170 + 12 * math.sin(t * 9), LIMA, esc=back(u * 4), rot=0.05 * math.sin(t * 3), fondo=TINTA)
        return None, None
    if i == 6:
        nombre_cae(cr, t, u)
        return "tu nombre", AMARILLO
    if i == 7:
        revista(cr, t, u)
        return "Nintendo, 1999", CORAL
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    if i == 6:
        g.add_color_stop_rgb(0, *PLANO1); g.add_color_stop_rgb(1, *PLANO2)
        cr.set_source(g); cr.paint()
        cr.set_source_rgba(1, 1, 1, 0.10)
        off = (t * 50) % 60
        for y in range(-60, H, 60):
            for x in range(0, W, 60):
                if ((x + y) // 60) % 2 == 0: cr.rectangle(x, y + off, 30, 30)
        cr.fill()
        return
    g.add_color_stop_rgb(0, *FONDO1); g.add_color_stop_rgb(1, *FONDO2)
    cr.set_source(g); cr.paint()
    # cuadritos pixelados que bajan como lluvia lenta (antes: partículas violetas que flotan + líneas de escaneo)
    rnd = random.Random(9)
    for k in range(34):
        x = rnd.uniform(0, W); sp = rnd.uniform(20, 60); s = rnd.choice((8, 12, 16))
        y = (rnd.uniform(0, H) + t * sp) % H
        cr.rectangle(x, y, s, s); cr.set_source_rgba(*ARENA, 0.22); cr.fill()


def gancho(cr, t):
    # entrada nueva: la línea 1 entra deslizándose desde la izquierda y la 2 desde la derecha, con rebote;
    # en el cuadro 0 ya están casi en su lugar y legibles (antes: llegaban desde grande con parpadeo)
    ys = [610, 790]; sizes = [150, 132]
    for k, (s, y, z) in enumerate(zip(GANCHO["lineas"], ys, sizes)):
        u = back((t + 0.25 - k * 0.05) / 0.45)
        dx = (1 - u) * (-320 if k == 0 else 320)
        cr.save(); cr.translate(W / 2 + dx, y)
        palabras = s.split(" "); font(cr, z)
        wtot = cr.text_extents(s).x_advance; x = -wtot / 2
        for p in palabras:
            col = LIMA if p == GANCHO["resalta"] else BLANCO
            adv = cr.text_extents(p + " ").x_advance
            texto(cr, p, x, 0, z, col, centro=False, borde=26)
            x += adv
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
            if acc > vis: col = (0.72, 0.80, 0.82)
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
    # cámara nueva: paneo horizontal lento + pequeño golpe de zoom en cada tiempo de la música (118 bpm)
    # (antes: balanceo de giro + empuje continuo por escena)
    beat = 60 / 118
    fb = (t % beat) / beat
    zc = 1.0 + 0.018 * math.exp(-fb * 6)
    px = 14 * math.sin(t * 0.7)
    sx = sy = 0
    if i in (3, 5):
        sx = 5 * math.sin(t * 61); sy = 4 * math.cos(t * 47)
    cr.save(); cr.translate(660 + px + sx, 1150 + sy); cr.scale(zc, zc); cr.translate(-660, -1150)
    # nada del dibujo entra en la zona de la mascota
    cr.rectangle(0, 0, W, 1300); cr.rectangle(320, 1300, W - 320, 360); cr.rectangle(0, 1660, W, H - 1660); cr.clip()
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0 and t < L[0]["t1"] + 0.1:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1560, col, 40)
    chipb(cr, "Errores geniales", 360, 1760, ARENA, 34)
    cr.set_source_rgba(0, 0, 0, 0.3); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*LIMA); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        d = t - x["t0"]
        if 0 <= d < 0.1:
            cr.set_source_rgba(1, 1, 1, 0.16 * (1 - d / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0, 1.5] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [19.5, 25.0, 27.5, round(L[-1]["t1"] - 0.3, 1)]
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
