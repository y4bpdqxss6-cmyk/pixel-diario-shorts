"""Motor de respaldo Pixel Diario — Short 'Mario tiene arbustos en el cielo'.
Dibuja con cairo, sin personajes, logos ni diseños reconocibles: una pieza de píxeles INVENTADA (sin ojos) que hace de
nube y de arbusto, cartucho genérico sin marcas, suelo de pasto liso. "Super Mario Bros." y "Nintendo" solo como texto.
Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["ARBUSTOS", "EN EL CIELO"], "resalta": "ARBUSTOS"}

# paleta nueva: cielo de día pastel + verde pasto + tinta azul marino (antes: HUD nocturno carbón + rojo neón)
CIELO1 = (0.36, 0.62, 0.96)
CIELO2 = (0.74, 0.88, 1.0)
VERDE = (0.27, 0.74, 0.30)
VERDE_O = (0.10, 0.42, 0.16)
NUBE = (0.99, 0.99, 1.0)
NUBE_O = (0.55, 0.70, 0.92)
TIERRA = (0.62, 0.42, 0.26)
CORAL = (1.0, 0.42, 0.34)
AMARILLO = (1.0, 0.80, 0.18)
BLANCO = (1, 1, 1)
TINTA = (0.08, 0.10, 0.22)
PLANO1 = (0.07, 0.16, 0.36)
PLANO2 = (0.13, 0.28, 0.55)

PIEZA = [
    "....####.....###....",
    "..########.#######..",
    ".##################.",
    "####################",
    "####################",
    ".##################.",
    "..################..",
]
PIEZA_W, PIEZA_H = len(PIEZA[0]), len(PIEZA)

RESALTA = {1: ["1985,", "cartucho", "diminuto."], 2: ["nube.", "arbustos", "suelo."], 3: ["Pero", "raro:", "mismo", "dibujo."],
           4: ["color:", "blanco", "verde"], 5: ["¿Por", "qué?"], 6: ["chico", "cuatro", "colores", "misma", "pieza"],
           7: ["arbusto…", "nube."]}
COLRES = {1: AMARILLO, 2: VERDE, 3: CORAL, 4: VERDE, 5: AMARILLO, 6: AMARILLO, 7: VERDE}


def ease(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)


def back(x):  # rebote con sobrepaso
    x = max(0, min(1, x)); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def lerp(a, b, u): return a + (b - a) * u


def mezcla(c1, c2, u): return tuple(lerp(a, b, u) for a, b in zip(c1, c2))


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
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: píldora blanca con sombra y
    punto de color (antes: marco de HUD oscuro con esquinas en escuadra)."""
    x = max(x, 340)
    font(cr, size); w = cr.text_extents(s).x_advance + 96; h = size + 36
    rrect(cr, x + 6, y + 8, w, h, h / 2); cr.set_source_rgba(*TINTA, 0.35); cr.fill()
    rrect(cr, x, y, w, h, h / 2); cr.set_source_rgb(*BLANCO); cr.fill()
    cr.new_sub_path(); cr.arc(x + 36, y + h / 2, 13, 0, 2 * math.pi); cr.set_source_rgb(*color); cr.fill()
    cr.set_source_rgb(*TINTA); cr.move_to(x + 64, y + size + 10); cr.show_text(s)


# ---------- dibujos genéricos ----------
def pieza(cr, cx, cy, px, fill, edge, alpha=1.0):
    """la pieza de píxeles inventada; (cx, cy) = centro abajo"""
    x0 = cx - PIEZA_W * px / 2; y0 = cy - PIEZA_H * px
    for r, fila in enumerate(PIEZA):
        for c, ch in enumerate(fila):
            if ch != "#": continue
            borde = any(not (0 <= r + dr < PIEZA_H and 0 <= c + dc < PIEZA_W and PIEZA[r + dr][c + dc] == "#")
                        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            col = edge if borde else fill
            cr.rectangle(x0 + c * px, y0 + r * px, px + 0.6, px + 0.6)
            cr.set_source_rgba(*col, alpha); cr.fill()
    # brillo interior (mismo en las dos)
    for (r, c) in ((2, 4), (2, 5), (3, 13), (3, 14), (2, 15)):
        cr.rectangle(x0 + c * px, y0 + r * px, px, px)
        cr.set_source_rgba(*mezcla(fill, BLANCO, 0.45), alpha); cr.fill()


def nube(cr, cx, cy, px, a=1.0): pieza(cr, cx, cy, px, NUBE, NUBE_O, a)


def arbusto(cr, cx, cy, px, a=1.0): pieza(cr, cx, cy, px, VERDE, VERDE_O, a)


def suelo(cr, y, scroll=0.0):
    cr.rectangle(-400, y, W + 800, H - y + 400); cr.set_source_rgb(*TIERRA); cr.fill()
    cr.rectangle(-400, y, W + 800, 46); cr.set_source_rgb(*VERDE); cr.fill()
    cr.set_source_rgba(*VERDE_O, 0.8)
    for k in range(-10, 40):
        x = (k * 46 - scroll) % (W + 460) - 230
        cr.rectangle(x, y + 46, 23, 12); cr.fill()
    cr.set_source_rgba(0, 0, 0, 0.12)
    for k in range(-6, 30):
        x = (k * 120 - scroll * 0.9) % (W + 480) - 240
        cr.rectangle(x, y + 120 + (k % 3) * 70, 34, 16); cr.fill()


def cartucho(cr, cx, cy, esc):
    if esc <= 0.01: return
    cr.save(); cr.translate(cx, cy); cr.scale(esc, esc)
    rrect(cr, -150, -190, 300, 380, 22); cr.set_source_rgb(0.55, 0.57, 0.62); cr.fill()
    rrect(cr, -150, -190, 300, 380, 22); cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
    rrect(cr, -110, -150, 220, 200, 12); cr.set_source_rgb(0.95, 0.93, 0.86); cr.fill()
    for k in range(5):
        cr.rectangle(-110, 90 + k * 18, 220, 8); cr.set_source_rgb(0.42, 0.44, 0.5); cr.fill()
    # mini pieza en la etiqueta (sin marca)
    nube(cr, 0, 0, 9)
    cr.restore()


def tarjeta(cr, s, x, y, size, color, esc=1.0, rot=0.0):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 70
    rrect(cr, -w / 2 + 8, -size * 0.95 + 10, w, size * 1.5, 24); cr.set_source_rgba(*TINTA, 0.35); cr.fill()
    rrect(cr, -w / 2, -size * 0.95, w, size * 1.5, 24); cr.set_source_rgb(*BLANCO); cr.fill()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 35, size * 0.25); cr.text_path(s)
    cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke_preserve(); cr.set_source_rgb(*color); cr.fill()
    cr.restore()


def flecha(cr, x, y0, y1, u, col=CORAL):
    if u <= 0: return
    ye = lerp(y0, y1, ease(u))
    cr.set_source_rgb(*col); cr.set_line_width(14); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_dash([2, 30]); cr.move_to(x, y0); cr.line_to(x, ye); cr.stroke(); cr.set_dash([])
    if u > 0.6:
        cr.move_to(x - 30, ye - 34); cr.line_to(x, ye + 4); cr.line_to(x + 30, ye - 34); cr.stroke()


def escena_a(cr, t, i):
    """imagen del inicio y del cierre: cielo con nubes que se deslizan (una parpadea en verde) y arbustos en el suelo.
    Nada en y 300–820 (el texto del gancho va encima)."""
    scroll = t * 90
    for k, (y, px, sp) in enumerate(((1040, 20, 1.0), (1220, 14, 0.7), (960, 12, 0.5))):
        x = (k * 420 + 900 - scroll * sp) % 1400 - 160
        verde = (k == 0) and (math.sin(t * 3.2) > 0.75)
        if verde: arbusto(cr, x, y, px)
        else: nube(cr, x, y, px)
    suelo(cr, 1420, scroll * 1.6)
    for k in range(3):
        x = (k * 520 + 600 - scroll * 1.6) % 1560 - 240
        if x > 500:
            arbusto(cr, x, 1420, 18)


def escena(cr, t):
    i = linea_en(t)
    if i == 0 or i == 7:
        escena_a(cr, t, i)
        return ("SUPER MARIO BROS.", CORAL) if i == 0 else ("pisando una nube", VERDE)
    if i == 1:
        u = local(1, t)
        tarjeta(cr, "1985", 600, 880, 120 + 6 * math.sin(t * 5), CORAL, esc=back(u * 4), rot=-0.04)
        esc = lerp(1.7, 0.75, ease((u - 0.25) * 1.6)) * back(u * 3)
        cartucho(cr, 620, 1230, esc)
        if u > 0.6:
            texto(cr, "¡DIMINUTO!", 640, 1490 - 40 * ease((u - 0.6) * 4), 70, AMARILLO, borde=10, alpha=ease((u - 0.6) * 4))
        return None, None
    if i == 2:
        u = local(2, t)
        # la cámara baja de la nube al arbusto
        dy = -lerp(-150, 330, ease((u - 0.2) * 1.6))
        cr.save(); cr.translate(0, dy)
        nube(cr, 640, 980, 22)
        flecha(cr, 640, 1020, 1480, (u - 0.35) * 2.2)
        suelo(cr, 1680, t * 20)
        arbusto(cr, 640, 1680, 22)
        cr.restore()
        return ("nube → arbusto", CORAL) if u > 0.45 else ("mira una nube", CORAL)
    if i == 3:
        u = local(3, t)
        bajar = ease((u - 0.1) * 1.8)
        suelo(cr, 1380, 0)
        arbusto(cr, 640, 1380, 22)
        nube(cr, 640, lerp(1000, 1380, bajar), 22, a=lerp(1, 0.55, bajar))
        if bajar > 0.98:
            d = (u - 0.66)
            if d < 0.12:
                cr.rectangle(-500, -500, W + 1000, H + 1000); cr.set_source_rgba(1, 1, 1, 0.6 * (1 - d / 0.12)); cr.fill()
            e = max(0.02, back((u - 0.66) * 4))
            cr.save(); cr.translate(560, 1020); cr.rotate(-0.05); cr.scale(e, e)
            texto(cr, "MISMO DIBUJO", 0, 0, 104, CORAL, borde=14); cr.restore()
        return "píxel por píxel", CORAL
    if i == 4:
        u = local(4, t)
        fase = (u * 4) % 2 < 1
        suelo(cr, 1420, t * 30) if not fase else None
        y = 1330 if fase else 1420
        if fase: nube(cr, 640, lerp(1300, 1250, ease((u * 4) % 1)), 24)
        else: arbusto(cr, 640, 1420, 24)
        texto(cr, "CIELO" if fase else "SUELO", 560, 960, 120, NUBE if fase else VERDE, borde=14)
        return ("blanco = nube", NUBE_O) if fase else ("verde = arbusto", VERDE)
    if i == 5:
        u = local(5, t)
        texto(cr, "¿?", 580, 1180, 240 + 60 * ease(u * 2) + 10 * math.sin(t * 8), AMARILLO, borde=14)
        cr.save(); cr.translate(620, 1420); cr.rotate(0.12 * math.sin(t * 9))
        pieza(cr, 0, 0, 18, mezcla(NUBE, VERDE, 0.5 + 0.5 * math.sin(t * 6)), TINTA); cr.restore()
        return "¿por qué?", AMARILLO
    if i == 6:
        u = local(6, t)
        # cambio visual más fuerte: plano azul de memoria, barra casi llena que se libera, paleta de 4 colores que gira
        # barra
        lleno = 0.96 if u < 0.38 else lerp(0.96, 0.55, ease((u - 0.38) * 3))
        texto(cr, "MEMORIA", 540, 900, 64, BLANCO, borde=8)
        rrect(cr, 180, 930, 720, 80, 18); cr.set_source_rgba(0, 0, 0, 0.45); cr.fill()
        col = CORAL if lleno > 0.8 else VERDE
        rrect(cr, 190, 940, 700 * lleno, 60, 12); cr.set_source_rgb(*col); cr.fill()
        texto(cr, f"{int(lleno * 100)}%", 540, 990, 50, BLANCO, borde=6)
        # paleta de 4 cuadritos que gira
        if u > 0.45:
            a = ease((u - 0.45) * 4)
            cr.save(); cr.translate(870, 1200); cr.rotate(t * 1.6); cr.scale(a, a)
            for k, c in enumerate((NUBE, VERDE, AMARILLO, CORAL)):
                ang = k * math.pi / 2
                cr.rectangle(110 * math.cos(ang) - 34, 110 * math.sin(ang) - 34, 68, 68)
                cr.set_source_rgb(*c); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
            cr.restore()
        # la misma pieza cambia: nube, arbusto, nube...
        m = 0.5 + 0.5 * math.sin(max(0, u - 0.45) * 22)
        pieza(cr, 520 if u > 0.45 else 600, 1360, 18, mezcla(NUBE, VERDE, m), mezcla(NUBE_O, VERDE_O, m))
        if u > 0.75:
            texto(cr, "1 PIEZA = 2 COSAS", 540, 1500 - 30 * ease((u - 0.75) * 5), 64, AMARILLO, borde=10,
                  alpha=ease((u - 0.75) * 5))
        return None, None
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    if i == 6:
        g.add_color_stop_rgb(0, *PLANO1); g.add_color_stop_rgb(1, *PLANO2)
        cr.set_source(g); cr.paint()
        cr.set_source_rgba(1, 1, 1, 0.08); cr.set_line_width(2)
        off = (t * 30) % 60
        for x in range(-60, W + 60, 60): cr.move_to(x + off, 0); cr.line_to(x + off, H); cr.stroke()
        for y in range(-60, H + 60, 60): cr.move_to(0, y + off); cr.line_to(W, y + off); cr.stroke()
        return
    g.add_color_stop_rgb(0, *CIELO1); g.add_color_stop_rgb(1, *CIELO2)
    cr.set_source(g); cr.paint()
    # destellos cuadrados que suben (antes: suelo de rejilla en perspectiva + líneas de escaneo)
    rnd = random.Random(9)
    for k in range(26):
        x0 = rnd.uniform(0, W); sp = rnd.uniform(20, 60); s = rnd.choice((6, 8, 10))
        y = (rnd.uniform(0, H) - t * sp) % H
        cr.rectangle(x0, y, s, s); cr.set_source_rgba(1, 1, 1, 0.35); cr.fill()


def gancho(cr, t):
    # entrada nueva: cada línea sube desde abajo y rebota con sobrepaso (antes: caía desde arriba con temblor);
    # en el cuadro 0 ya está a escala ~0.9 y legible
    ys = [590, 790]; sizes = [140, 125]
    for k, (s, y, z) in enumerate(zip(GANCHO["lineas"], ys, sizes)):
        u = 0.55 + (t - k * 0.05) / 0.45
        e = back(u)
        col = VERDE if s == GANCHO["resalta"] else BLANCO
        cr.save(); cr.translate(W / 2, y + (1 - min(1, u)) * 60); cr.scale(e, e)
        texto(cr, s, 0, 0, z, col, borde=26)
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
    y = 420 if len(lineas) <= 2 else 360
    acc = 0
    for ln in lineas:
        wtot = cr.text_extents(" ".join(ln)).x_advance; x = W / 2 - wtot / 2
        for p in ln:
            acc += len(p) + 1
            col = COLRES.get(i, AMARILLO) if p in RESALTA.get(i, []) else BLANCO
            if acc > vis: col = (0.80, 0.82, 0.88)
            font(cr, size); adv = cr.text_extents(p + " ").x_advance
            cr.move_to(x, y); cr.text_path(p)
            cr.set_source_rgba(*TINTA, 1); cr.set_line_width(12); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve()
            cr.set_source_rgba(*col, 1); cr.fill()
            x += adv
        y += 90


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: inclinación vertical lenta (sube y baja) + respiración de escala; sin giro ni temblor
    # (antes: deriva lateral + empuje al cambiar de escena + temblor)
    zc = 1.0 + 0.025 * math.sin(t * 1.3)
    dy = 22 * math.sin(t * 0.8)
    cr.save(); cr.translate(680, 1150 + dy); cr.scale(zc, zc); cr.translate(-680, -1150)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0 and t < L[0]["t1"] + 0.1:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1500, col, 40)
    chipb(cr, "Secreto de diseño", 360, 1760, AMARILLO, 34)
    cr.set_source_rgba(0, 0, 0, 0.15); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*VERDE); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        d = t - x["t0"]
        if 0 <= d < 0.1:
            cr.set_source_rgba(1, 1, 1, 0.14 * (1 - d / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0, 1.5] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [16.5, 26.5, round(L[-1]["t1"] - 0.3, 1)]
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
