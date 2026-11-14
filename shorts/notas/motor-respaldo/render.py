"""Motor de respaldo Pixel Diario — Short 'Cada fantasma te caza distinto'.
Dibuja con cairo, sin personajes reconocibles: el jugador es un rombo blanco y
los perseguidores son cuadros de color. Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["Cada fantasma", "te caza", "distinto."], "resalta": "distinto."}

# paleta: noche azul tinta con muros lila (antes: verde azulado/coral)
BG = (0.043, 0.063, 0.15)
MURO = (0.30, 0.20, 0.62)
AMARI = (1.0, 0.84, 0.25)
COL = {"rojo": (1.0, 0.27, 0.3), "rosa": (1.0, 0.55, 0.85), "azul": (0.25, 0.9, 1.0), "naranja": (1.0, 0.62, 0.2)}
BLANCO = (1, 1, 1)

TILE, COLS, ROWS = 44, 22, 10
BX, BY = 56, 850  # tablero x 56–1024, y 850–1290
MUROS = [(3, 2, 3, 1), (9, 2, 4, 1), (17, 2, 2, 1), (3, 7, 2, 1), (8, 8, 3, 1), (15, 7, 4, 1), (12, 0, 1, 1), (12, 9, 1, 1)]

RESALTA = {1: ["rojo", "directo"], 2: ["rosa", "cuatro", "casillas"], 3: ["emboscar."], 4: ["azul", "rojo"], 5: ["azar."],
           6: ["naranja", "ocho", "casillas."], 7: ["huye"], 8: ["tonto»."], 9: ["Toru", "Iwatani", "1980."],
           10: ["error", "izquierda."], 11: ["espera."]}
COLRES = {1: COL["rojo"], 2: COL["rosa"], 3: COL["rosa"], 4: COL["azul"], 6: COL["naranja"], 7: COL["naranja"], 8: COL["naranja"]}


def ease(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)


def lerp(a, b, u): return a + (b - a) * u


def lp(p, q, u): return (lerp(p[0], q[0], u), lerp(p[1], q[1], u))


def tile_xy(c):
    return BX + (c[0] + 0.5) * TILE, BY + (c[1] + 0.5) * TILE


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


def texto(cr, s, x, y, size, color=BLANCO, centro=True, borde=8):
    font(cr, size)
    ext = cr.text_extents(s)
    if centro: x = x - ext.x_advance / 2
    cr.move_to(x, y); cr.text_path(s)
    cr.set_source_rgb(0.02, 0.03, 0.08); cr.set_line_width(borde); cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.stroke_preserve(); cr.set_source_rgb(*color); cr.fill()
    return ext.x_advance


def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0); cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi); cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); cr.close_path()


def chipb(cr, s, x, y, color, size=34):
    """chip de abajo; nunca entra en la zona de la mascota (x<=310)."""
    x = max(x, 340)
    font(cr, size); w = cr.text_extents(s).x_advance + 44
    rrect(cr, x, y, w, size + 30, (size + 30) / 2); cr.set_source_rgb(*color); cr.fill()
    cr.set_source_rgb(0.04, 0.05, 0.12); cr.move_to(x + 22, y + size + 8); cr.show_text(s)


def tablero(cr, t):
    rrect(cr, BX - 8, BY - 8, COLS * TILE + 16, ROWS * TILE + 16, 18)
    cr.set_source_rgb(0.07, 0.09, 0.22); cr.fill()
    cr.set_source_rgba(1, 1, 1, 0.06); cr.set_line_width(1)
    for c in range(COLS + 1):
        cr.move_to(BX + c * TILE, BY); cr.line_to(BX + c * TILE, BY + ROWS * TILE)
    for r in range(ROWS + 1):
        cr.move_to(BX, BY + r * TILE); cr.line_to(BX + COLS * TILE, BY + r * TILE)
    cr.stroke()
    for (c, r, w, h) in MUROS:
        rrect(cr, BX + c * TILE + 4, BY + r * TILE + 4, w * TILE - 8, h * TILE - 8, 8)
        cr.set_source_rgb(*MURO); cr.fill()


def jugador(cr, c, t, dirc=(1, 0)):
    x, y = tile_xy(c); s = 20 + 2 * math.sin(t * 10)
    cr.save(); cr.translate(x, y)
    cr.move_to(0, -s); cr.line_to(s, 0); cr.line_to(0, s); cr.line_to(-s, 0); cr.close_path()
    cr.set_source_rgb(*BLANCO); cr.fill()
    # flechita de dirección
    cr.set_source_rgb(*AMARI); cr.set_line_width(5)
    cr.move_to(dirc[0] * 24, dirc[1] * 24); cr.line_to(dirc[0] * 36, dirc[1] * 36); cr.stroke()
    cr.restore()


def bloque(cr, c, color, t, alpha=1.0, wob=0):
    x, y = tile_xy(c); s = 19
    cr.save(); cr.translate(x, y); cr.rotate(wob)
    rrect(cr, -s, -s, 2 * s, 2 * s, 7); cr.set_source_rgba(*color, alpha); cr.fill()
    cr.set_source_rgba(0.04, 0.05, 0.12, alpha); cr.rectangle(-8, -5, 5, 5); cr.rectangle(3, -5, 5, 5); cr.fill()
    cr.restore()


def mira(cr, c, color, t):
    x, y = tile_xy(c); r = 22 + 4 * math.sin(t * 8)
    cr.set_source_rgb(*color); cr.set_line_width(5)
    cr.arc(x, y, r, 0, 2 * math.pi); cr.stroke()
    for a in range(4):
        dx, dy = math.cos(a * math.pi / 2), math.sin(a * math.pi / 2)
        cr.move_to(x + dx * (r - 8), y + dy * (r - 8)); cr.line_to(x + dx * (r + 10), y + dy * (r + 10))
    cr.stroke()


def raya(cr, a, b, color, u=1.0, dash=True):
    x1, y1 = tile_xy(a); x2, y2 = tile_xy(b)
    cr.set_source_rgb(*color); cr.set_line_width(5)
    if dash: cr.set_dash([14, 10])
    cr.move_to(x1, y1); cr.line_to(lerp(x1, x2, u), lerp(y1, y2, u)); cr.stroke(); cr.set_dash([])


def subtitulo(cr, i, t):
    s = L[i]["texto"]; pal = s.split(" ")
    u = (t - L[i]["t0"]) / (L[i]["t1"] - L[i]["t0"])
    total = sum(len(p) + 1 for p in pal); vis = u * total * 1.15
    size = 72; font(cr, size)
    lineas, act = [], []
    for p in pal:
        prueba = " ".join(act + [p])
        if cr.text_extents(prueba).x_advance > 960 and act: lineas.append(act); act = [p]
        else: act.append(p)
    lineas.append(act)
    y = 400 if len(lineas) <= 2 else 370
    acc = 0
    for ln in lineas:
        wtot = cr.text_extents(" ".join(ln)).x_advance; x = W / 2 - wtot / 2
        for p in ln:
            acc += len(p) + 1
            col = COLRES.get(i, AMARI) if p.strip(",:") in RESALTA.get(i, []) or p in RESALTA.get(i, []) else BLANCO
            a = 1.0 if acc <= vis else 0.28
            font(cr, size); adv = cr.text_extents(p + " ").x_advance
            cr.move_to(x, y); cr.text_path(p)
            cr.set_source_rgba(0.02, 0.03, 0.08, a); cr.set_line_width(9); cr.stroke_preserve()
            cr.set_source_rgba(*col, a); cr.fill()
            x += adv
        y += 92


def gancho(cr, t):
    # desde el fotograma 0, en letras gigantes, zona y 300–820
    pop = 1.0 if t > 0.25 else 0.9 + 0.1 * ease(t / 0.25)
    cr.save(); cr.translate(W / 2, 560); cr.scale(pop, pop); cr.translate(-W / 2, -560)
    ys = [440, 600, 790]; sizes = [128, 128, 172]
    for s, y, z in zip(GANCHO["lineas"], ys, sizes):
        col = AMARI if s == GANCHO["resalta"] else BLANCO
        texto(cr, s, W / 2, y, z, col, borde=14)
    cr.restore()


def escena(cr, t):
    i = linea_en(t)
    if t < L[1]["t0"]:  # A: el objeto principal ya moviéndose
        u = t / L[1]["t0"]
        P = (lerp(6, 10, u), 5)
        jugador(cr, P, t)
        for nombre, ini in zip(COL, [(20, 1), (1, 1), (20, 8), (1, 8)]):
            bloque(cr, lp(ini, P, 0.12 + 0.25 * u), COL[nombre], t)
        return None, None
    if i == 1:
        u = local(1, t); P = (lerp(10, 13, u), 5); R = lp((2, 1), P, 0.15 + 0.6 * ease(u))
        for nombre, c in [("rosa", (1, 8)), ("azul", (20, 8)), ("naranja", (20, 1))]: bloque(cr, c, COL[nombre], t, 0.25)
        raya(cr, R, P, COL["rojo"], ease(u * 2)); mira(cr, P, COL["rojo"], t)
        jugador(cr, P, t); bloque(cr, R, COL["rojo"], t)
        return "ROJO · persigue", COL["rojo"]
    if i in (2, 3):
        u = local(2, t, 3); P = (lerp(6, 9, u), 5); tgt = (P[0] + 4, 5)
        n = min(4, int(u * 9))
        for k in range(1, n + 1):
            x, y = tile_xy((P[0] + k, 5)); rrect(cr, x - 18, y - 18, 36, 36, 6)
            cr.set_source_rgba(*COL["rosa"], 0.25); cr.fill()
            font(cr, 24); cr.set_source_rgb(*COL["rosa"]); cr.move_to(x - 7, y - 24); cr.show_text(str(k))
        Pk = lp((19, 8), (tgt[0], tgt[1]), ease((u - 0.35) / 0.6))
        if n >= 4: mira(cr, tgt, COL["rosa"], t); raya(cr, Pk, tgt, COL["rosa"])
        jugador(cr, P, t); bloque(cr, Pk, COL["rosa"], t)
        bloque(cr, (3, 1), COL["rojo"], t, 0.3)
        return "ROSA · embosca", COL["rosa"]
    if i in (4, 5):
        u = local(4, t, 5); P = (lerp(9, 11, u), 6); R = (6, 3)
        A = (P[0] + 2, 6); B = (2 * A[0] - R[0], 2 * A[1] - R[1])
        B = (min(B[0], 21), min(B[1], 9))
        jugador(cr, P, t); bloque(cr, R, COL["rojo"], t)
        x, y = tile_xy(A); cr.arc(x, y, 9, 0, 2 * math.pi); cr.set_source_rgb(*AMARI); cr.fill()
        raya(cr, R, A, COL["rojo"], ease(u * 3))
        if u > 0.25: raya(cr, A, B, COL["azul"], ease((u - 0.25) * 3)); mira(cr, B, COL["azul"], t)
        if i == 4:
            Bl = (3, 8)
        else:
            v = local(5, t); Bl = lp((3, 8), B, ease(v))
            Bl = (Bl[0] + 1.3 * math.sin(t * 9), Bl[1] + 1.0 * math.cos(t * 7))
        bloque(cr, Bl, COL["azul"], t)
        return "AZUL · usa al rojo", COL["azul"]
    if i in (6, 7):
        P = (11, 5); jugador(cr, P, t, (0, 1))
        x, y = tile_xy(P); cr.save(); cr.rectangle(BX, BY, COLS * TILE, ROWS * TILE); cr.clip()
        cr.set_dash([16, 12]); cr.set_line_width(5); cr.set_source_rgba(*COL["naranja"], 0.8)
        cr.arc(x, y, 8 * TILE * ease(local(6, t) * 2.5), 0, 2 * math.pi); cr.stroke(); cr.set_dash([]); cr.restore()
        if i == 6:
            u = local(6, t); O = lp((21, 0.3), (18.5, 2.5), ease(u))
            raya(cr, O, P, COL["naranja"])
        else:
            u = local(7, t); O = lp((18.5, 2.5), (0, 9), ease(u)); mira(cr, (0, 9), COL["naranja"], t)
        font(cr, 30); cr.set_source_rgb(*COL["naranja"]); cr.move_to(x + 8 * TILE * 0.7, y - 8 * TILE * 0.72 + 30)
        bloque(cr, O, COL["naranja"], t)
        return "NARANJA · 8 casillas", COL["naranja"]
    if i == 8:
        u = local(8, t)
        cr.set_source_rgba(*BG, 0.7); cr.rectangle(BX - 20, BY - 20, COLS * TILE + 40, ROWS * TILE + 40); cr.fill()
        bloque(cr, (10.5, 1.4), COL["naranja"], t, 1, 0.3 * math.sin(t * 6))
        e = ease(u * 3)
        cr.save(); cr.translate(W / 2, 1110); cr.scale(e, e); cr.translate(-W / 2, -1110)
        texto(cr, "OTOBOKE", W / 2, 1120, 120, COL["naranja"], borde=12)
        cr.restore()
        if u > 0.35: texto(cr, "«el que se hace el tonto»", W / 2, 1210, 46, BLANCO)
        return "NARANJA · japonés", COL["naranja"]
    if i == 9:
        u = local(9, t); z = 1 - 0.18 * ease(u)
        cr.save(); cr.translate(540, 1060); cr.scale(z, z); cr.translate(-540, -1060)
        P = (11, 5); jugador(cr, P, t)
        for k, nombre in enumerate(COL):
            a = t * 1.4 + k * math.pi / 2; bloque(cr, (11 + 6 * math.cos(a), 4.5 + 3.4 * math.sin(a)), COL[nombre], t)
        cr.restore()
        anio = int(lerp(1970, 1980, ease(u * 1.6)))
        rrect(cr, 340, 1300, 600, 150, 26); cr.set_source_rgba(0.07, 0.09, 0.22, 0.95); cr.fill()
        texto(cr, "TORU IWATANI", 640, 1360, 50, BLANCO); texto(cr, str(anio), 640, 1430, 62, AMARI)
        return None, None
    if i == 10:
        u = local(10, t); P = (13, 8); jugador(cr, P, t, (0, -1))
        esp = (13, 4); real = (9, 4)
        n = min(4, int(u * 10))
        for k in range(1, n + 1):
            x, y = tile_xy((13, 8 - k)); rrect(cr, x - 18, y - 18, 36, 36, 6); cr.set_source_rgba(*COL["rosa"], 0.22); cr.fill()
        if u < 0.45: mira(cr, esp, COL["rosa"], t)
        else:
            x, y = tile_xy(esp); cr.set_source_rgba(1, 1, 1, 0.35); cr.set_line_width(4)
            cr.arc(x, y, 22, 0, 2 * math.pi); cr.stroke()
            v = ease((u - 0.45) / 0.3); g = lp(esp, real, v)
            raya(cr, esp, g, (1, 0.3, 0.3)); mira(cr, g, COL["rosa"], t)
        bloque(cr, lp((2, 1), (8, 3), ease(u)), COL["rosa"], t)
        if u > 0.62:
            k = ease((u - 0.62) * 6); cr.save(); cr.translate(850, 1190); cr.rotate(-0.15); cr.scale(2 - k, 2 - k)
            rrect(cr, -150, -50, 300, 100, 14); cr.set_source_rgb(1, 0.2, 0.25); cr.fill()
            texto(cr, "ERROR", 0, 26, 70, BLANCO, borde=0); cr.restore()
        return "BUG · mirar arriba", (1, 0.35, 0.4)
    # final: todos convergen
    u = local(11, t); P = (11, 5); jugador(cr, P, t)
    for nombre, ini, fin in zip(COL, [(21, 0), (0, 0), (21, 9), (0, 9)], [(12, 4), (10, 4), (12, 6), (10, 6)]):
        bloque(cr, lp(ini, fin, ease(u * 1.3)), COL[nombre], t)
    return "¿quién te espera?", AMARI


def fondo(cr, t):
    cr.set_source_rgb(*BG); cr.paint()
    # puntitos que suben (cambio sutil constante)
    rnd = random.Random(7)
    for k in range(70):
        x = rnd.uniform(0, W); y = (rnd.uniform(0, H) - t * rnd.uniform(15, 50)) % H
        cr.set_source_rgba(0.6, 0.55, 1, rnd.uniform(0.08, 0.25)); cr.arc(x, y, rnd.uniform(1.5, 3.5), 0, 2 * math.pi); cr.fill()


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    fondo(cr, t)
    i = linea_en(t)
    # cámara: leve acercamiento por escena + temblor en ERROR
    zc = 1 + 0.035 * local(i, t); sx = sy = 0
    if i == 10 and local(10, t) > 0.62: sx = 6 * math.sin(t * 60) * max(0, 1 - (local(10, t) - 0.62) * 6)
    cr.save(); cr.translate(540 + sx, 1060 + sy); cr.scale(zc, zc); cr.translate(-540, -1060)
    tablero(cr, t)
    etiqueta, col = escena(cr, t)
    cr.restore()
    if t < L[1]["t0"] - 0.05: gancho(cr, t)
    else: subtitulo(cr, i, t)
    if etiqueta: chipb(cr, etiqueta, 360, 1340, col, 42)
    chipb(cr, "secretos de juegos", 360, 1730, (0.75, 0.7, 1.0), 32)
    # barra de progreso
    cr.set_source_rgba(1, 1, 1, 0.15); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*AMARI); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    # destello de corte
    for x in L[1:]:
        d = t - x["t0"]
        if 0 <= d < 0.1 and x["i"] in (1, 2, 4, 6, 8, 9, 10, 11):
            cr.set_source_rgba(1, 1, 1, 0.18 * (1 - d / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        for t in [0, 1.2, 3.5, 7.5, 12, 15, 18, 21, 23.5, 27, 30, 32.5, 36]:
            cuadro(t).write_to_png(f"prueba/t{t:05.1f}.png")
    else:
        n = int(DUR * FPS)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-i", "mezcla.wav", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
                              "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", "short.mp4"], stdin=subprocess.PIPE)
        for f in range(n):
            p.stdin.write(bytes(cuadro(f / FPS).get_data()))
        p.stdin.close(); p.wait()
