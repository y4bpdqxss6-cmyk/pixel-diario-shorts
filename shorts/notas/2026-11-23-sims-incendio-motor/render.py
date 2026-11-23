"""Motor de respaldo Pixel Diario — Short 'Los Sims nacieron de una casa quemada'.
Dibuja con cairo, sin personajes, caras, logos, interfaz ni el rombo de Los Sims, y sin dibujar a Will Wright:
casitas, llamas, colinas, muebles y planos genéricos. Los nombres solo como texto.
Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, random, subprocess, sys
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["TODO EMPEZÓ", "CON FUEGO"], "resalta": "FUEGO"}

# paleta nueva: plano de arquitecto (azul petróleo) + naranja fuego + crema (antes: noir azul pizarra + ámbar + hueso)
FONDO1 = (0.04, 0.11, 0.17)
FONDO2 = (0.08, 0.24, 0.33)
FUEGO = (1.0, 0.47, 0.10)
AMBAR = (1.0, 0.80, 0.22)
SOL = AMBAR
HUESO = (0.98, 0.94, 0.85)
ROJO = (0.92, 0.18, 0.16)
VERDE = (0.35, 0.82, 0.50)
AZUL = (0.55, 0.83, 0.97)
BLANCO = (1, 1, 1)
TINTA = (0.03, 0.05, 0.08)
GRIS = (0.52, 0.55, 0.60)
CENIZA = (0.30, 0.30, 0.32)
ROSA = (0.97, 0.50, 0.55)

RESALTA = {1: ["1991", "Oakland,", "humo."], 2: ["incendio", "colinas…", "no", "salva."], 3: ["Pero", "después."],
           4: ["todo", "otra", "vez:"], 5: ["¿Y", "tiene", "ver?", "reconstruir", "juego.", "no", "gustó"],
           6: ["2000.", "quemada."]}
COLRES = {1: AZUL, 2: FUEGO, 3: AMBAR, 4: AZUL, 5: AMBAR, 6: FUEGO}

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
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: etiqueta de plano redondeada
    con chincheta y borde punteado (antes: tira de cinta adhesiva inclinada)."""
    x = max(x, 340)
    font(cr, size); tw = cr.text_extents(s).x_advance; w = min(tw + 110, W - 20 - x); h = size + 34
    rrect(cr, x + 5, y + 7, w, h, h / 2); cr.set_source_rgba(0, 0, 0, 0.5); cr.fill()
    rrect(cr, x, y, w, h, h / 2); cr.set_source_rgb(*color); cr.fill()
    rrect(cr, x + 7, y + 7, w - 14, h - 14, (h - 14) / 2); cr.set_source_rgba(*TINTA, 0.55); cr.set_line_width(3)
    cr.set_dash([10, 7]); cr.stroke(); cr.set_dash([])
    cr.arc(x + 34, y + h / 2, 11, 0, 2 * math.pi); cr.set_source_rgb(*ROJO); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(3); cr.stroke()
    z = size
    while cr.text_extents(s).x_advance > w - 85: z -= 2; font(cr, z)
    cr.set_source_rgb(*txt); cr.move_to(x + 58, y + h / 2 + z * 0.36); cr.show_text(s)


def llamas(cr, x, y, w, h, t, alfa=1.0):
    """lenguas de fuego genéricas; base en y."""
    for capa, col, esc in ((0, FUEGO, 1.0), (1, AMBAR, 0.6)):
        n = 7
        cr.new_path(); cr.move_to(x - w / 2 * esc, y)
        for k in range(n):
            x0 = x - w / 2 * esc + (k + 0.5) * w * esc / n
            hh = h * esc * (0.55 + 0.45 * abs(math.sin(t * 6 + k * 1.7 + capa)))
            cr.curve_to(x0 - w * esc / n * 0.6, y - hh * 0.4, x0 - 8, y - hh * 0.8, x0 + 6 * math.sin(t * 9 + k), y - hh)
            cr.curve_to(x0 + 8, y - hh * 0.8, x0 + w * esc / n * 0.6, y - hh * 0.4, x0 + w * esc / n * 0.5, y)
        cr.close_path(); cr.set_source_rgba(*col, alfa); cr.fill()


def humo(cr, x, y, t, n=7, alfa=0.55, esc=1.0):
    for k in range(n):
        p = ((t * 0.35 + k / n) % 1.0)
        cx = x + 50 * math.sin(p * 5 + k) * esc + 60 * p * esc; cy = y - 420 * p * esc
        r = (30 + 80 * p) * esc
        cr.arc(cx, cy, r, 0, 2 * math.pi); cr.set_source_rgba(0.55, 0.57, 0.60, alfa * (1 - p)); cr.fill()


def casita(cr, x, y, esc=1.0, quemada=0.0, t=0.0):
    """casa genérica de dos aguas; (x, y) = centro de la base."""
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    q = max(0, min(1, quemada))
    pared = tuple(lerp(a, b, q) for a, b in zip(HUESO, (0.12, 0.11, 0.11)))
    techo = tuple(lerp(a, b, q) for a, b in zip((0.80, 0.30, 0.22), (0.08, 0.07, 0.07)))
    cr.rectangle(-190 + 8, -300 + 10, 380, 300); cr.set_source_rgba(0, 0, 0, 0.45); cr.fill()
    cr.rectangle(-190, -300, 380, 300); cr.set_source_rgb(*pared); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
    cr.move_to(-230, -290); cr.line_to(0, -470); cr.line_to(230, -290); cr.close_path()
    cr.set_source_rgb(*techo); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.stroke()
    cr.rectangle(-40, -150, 80, 150); cr.set_source_rgb(*tuple(lerp(a, b, q) for a, b in zip((0.45, 0.28, 0.18), (0.05, 0.05, 0.05)))); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.stroke()
    for wx in (-130, 70):
        brillo = 0.55 + 0.45 * abs(math.sin(t * 7 + wx)) if q < 0.9 else 0.0
        cr.rectangle(wx, -240, 60, 60)
        cr.set_source_rgb(*tuple(lerp(a, b, 1 - brillo) for a, b in zip(AMBAR, (0.10, 0.14, 0.2)))); cr.fill_preserve()
        cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()
    if q > 0.3:
        rnd = random.Random(5)
        for k in range(26):
            bx = rnd.uniform(-180, 180); by = rnd.uniform(-440, -10)
            if by < -300 and abs(bx) > 230 * (1 - (-by - 290) / 180): continue
            al = (q - 0.3) / 0.7 * (0.5 + 0.5 * math.sin(t * 8 + k))
            cr.arc(bx, by, rnd.uniform(4, 9), 0, 2 * math.pi); cr.set_source_rgba(*FUEGO, al); cr.fill()
    cr.restore()


def colinas(cr, t):
    cr.move_to(320, 1560); cr.curve_to(450, 1180, 620, 1150, 760, 1320); cr.curve_to(860, 1230, 980, 1160, 1080, 1260)
    cr.line_to(1080, 1600); cr.line_to(320, 1600); cr.close_path()
    cr.set_source_rgb(0.10, 0.20, 0.17); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()


def silla(cr, x, y, e):
    cr.save(); cr.translate(x, y); cr.scale(e, e)
    cr.set_source_rgb(0.75, 0.48, 0.25); cr.rectangle(-40, -120, 14, 120); cr.rectangle(-40, -50, 80, 14)
    cr.rectangle(26, -50, 14, 50); cr.fill(); cr.restore()


def plato(cr, x, y, e):
    cr.save(); cr.translate(x, y); cr.scale(e, e * 0.4)
    cr.arc(0, 0, 50, 0, 2 * math.pi); cr.set_source_rgb(*HUESO); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()
    cr.arc(0, 0, 28, 0, 2 * math.pi); cr.set_source_rgb(*AZUL); cr.set_line_width(5); cr.stroke(); cr.restore()


def cama(cr, x, y, e):
    cr.save(); cr.translate(x, y); cr.scale(e, e)
    cr.rectangle(-100, -50, 200, 40); cr.set_source_rgb(0.75, 0.48, 0.25); cr.fill()
    cr.rectangle(-100, -90, 14, 90); cr.rectangle(86, -70, 14, 70); cr.fill()
    cr.rectangle(-86, -72, 180, 24); cr.set_source_rgb(*AZUL); cr.fill()
    rrect(cr, -84, -92, 50, 22, 8); cr.set_source_rgb(*HUESO); cr.fill(); cr.restore()


def tele(cr, x, y, e, t):
    cr.save(); cr.translate(x, y); cr.scale(e, e)
    rrect(cr, -70, -110, 140, 100, 12); cr.set_source_rgb(0.2, 0.2, 0.24); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()
    cr.rectangle(-56, -98, 112, 76); cr.set_source_rgb(*AZUL); cr.fill()
    cr.set_source_rgba(1, 1, 1, 0.3); cr.rectangle(-56, -98 + (t * 120) % 76, 112, 8); cr.fill()
    cr.move_to(-30, -10); cr.line_to(-45, 0); cr.move_to(30, -10); cr.line_to(45, 0); cr.set_source_rgb(*TINTA); cr.stroke()
    cr.restore()


def plano(cr, u, t):
    """plano de casa visto desde arriba que se arma cuarto por cuarto (u 0..1)."""
    cuartos = [(420, 900, 300, 260, "SALA"), (720, 900, 260, 260, "COCINA"), (420, 1160, 300, 280, "CUARTO"), (720, 1160, 260, 280, "BAÑO")]
    cr.rectangle(400, 880, 600, 580); cr.set_source_rgba(*AZUL, 0.12); cr.fill()
    for k, (x, y, w, h, et) in enumerate(cuartos):
        p = ease((u - k * 0.2) / 0.25)
        if p <= 0: continue
        per = 2 * (w + h) * p
        cr.new_path(); cr.move_to(x, y)
        pts = [(x + w, y), (x + w, y + h), (x, y + h), (x, y)]; prev = (x, y); rest = per
        for q in pts:
            seg = abs(q[0] - prev[0]) + abs(q[1] - prev[1])
            if rest >= seg: cr.line_to(*q); rest -= seg; prev = q
            else:
                f_ = rest / seg; cr.line_to(prev[0] + (q[0] - prev[0]) * f_, prev[1] + (q[1] - prev[1]) * f_); break
        cr.set_source_rgb(*HUESO); cr.set_line_width(10); cr.stroke()
        if p > 0.8:
            texto(cr, et, x + w / 2, y + h / 2 + 15, 44, AZUL, borde=6, alpha=(p - 0.8) * 5)


def escena_a(cr, t, d):
    """inicio y cierre: casita con llamas que suben y humo. Nada en y 300–820 (el recorte empieza en 830)."""
    casita(cr, 690, 1440, 1.0, 0.0, t)
    humo(cr, 640, 1000, t, 8, 0.5)
    llamas(cr, 690, 1000, 360, 190 + 40 * math.sin(t * 2), t)
    llamas(cr, 520, 1210, 120, 120, t + 1)
    llamas(cr, 860, 1230, 110, 110, t + 2)


def escena(cr, t):
    i = linea_en(t)
    u = local(i, t)
    if i == 0:
        escena_a(cr, t, t)
        return "Los Sims", FUEGO
    if i == 1:
        # ventana de noche con humo que entra y líneas de olor
        cr.rectangle(470, 1000, 440, 380); cr.set_source_rgb(0.04, 0.06, 0.14); cr.fill()
        cr.arc(820, 1080, 40, 0, 2 * math.pi); cr.set_source_rgb(*HUESO); cr.fill()
        cr.set_source_rgb(0.55, 0.38, 0.22); cr.set_line_width(22)
        cr.rectangle(470, 1000, 440, 380); cr.stroke(); cr.move_to(690, 1000); cr.line_to(690, 1380); cr.stroke()
        cr.move_to(470, 1190); cr.line_to(910, 1190); cr.stroke()
        if u > 0.25: humo(cr, 600, 1380, t, 7, 0.6 * ease((u - 0.25) * 3), 0.8)
        if u > 0.5:
            for k in range(3):
                x = 520 + k * 140; yy = 1520 - 60 * ((t * 0.8 + k * 0.3) % 1)
                cr.move_to(x, yy)
                for j in range(6): cr.line_to(x + 18 * math.sin(j * 1.6 + t * 4), yy - j * 22)
                cr.set_source_rgba(*GRIS, 0.9); cr.set_line_width(7); cr.stroke()
        tarjeta(cr, "1991 · OAKLAND", 690, 930, 66, FUEGO, esc=back(u * 4), rot=-0.03, fondo=HUESO)
        return "huele a humo", GRIS
    if i == 2:
        colinas(cr, t)
        fx = lerp(330, 1000, ease(u / 0.75))
        cr.save(); cr.rectangle(320, 830, fx - 320, 800); cr.clip()
        cr.move_to(320, 1560); cr.curve_to(450, 1180, 620, 1150, 760, 1320); cr.curve_to(860, 1230, 980, 1160, 1080, 1260)
        cr.line_to(1080, 1600); cr.line_to(320, 1600); cr.close_path(); cr.set_source_rgb(0.12, 0.10, 0.09); cr.fill()
        cr.restore()
        hy = 1560 - (fx - 320) * 0.5 if fx < 560 else 1240 + 40 * math.sin(fx / 90)
        llamas(cr, fx, hy + 20, 170, 150, t)
        humo(cr, fx - 30, hy - 80, t, 6, 0.5)
        casita(cr, 900, 1330, 0.42, ease((u - 0.6) / 0.3), t)
        if u > 0.75: llamas(cr, 900, 1150, 140, 90 * (1 - ease((u - 0.75) / 0.25)) + 1, t)
        return ("baja por las colinas" if u < 0.6 else "su casa no se salva"), FUEGO
    if i == 3:
        rnd = random.Random(11)
        pts = []
        font(cr, 520); cr.move_to(540, 1420); cr.text_path("?"); fl = cr.copy_path_flat(); cr.new_path()
        for tipo, xy in fl:
            if xy: pts.append((xy[0], xy[1]))
        pts = pts[::max(1, len(pts) // 60)]
        c = ease(u / 0.6)
        for k, (px, py) in enumerate(pts):
            sx = rnd.uniform(360, 1040); sy = rnd.uniform(860, 1560)
            x = lerp(sx, px, c) + 6 * math.sin(t * 5 + k); y = lerp(sy, py, c) + 6 * math.cos(t * 4 + k)
            cr.arc(x, y, 12, 0, 2 * math.pi); cr.set_source_rgb(*(CENIZA if u < 0.7 else AMBAR)); cr.fill()
        if u > 0.55:
            texto(cr, "?", 540 + cr.text_extents("?").x_advance / 2 if False else 690, 1420, 520, AMBAR, borde=14, alpha=0.85 * ease((u - 0.55) / 0.25))
        if u > 0.7:
            cr.set_source_rgba(*HUESO, 0.12 * ease((u - 0.7) / 0.3)); cr.paint()
        return "lo que vino después", AMBAR
    if i == 4:
        cr.rectangle(370, 940, 480, 560); cr.set_source_rgba(*HUESO, 0.10); cr.fill()
        cr.move_to(370, 1500); cr.line_to(370, 940); cr.line_to(610, 830); cr.line_to(850, 940); cr.line_to(850, 1500)
        cr.set_source_rgb(*HUESO); cr.set_line_width(9); cr.stroke()
        cosas = [(lambda e: silla(cr, 450, 1490, e)), (lambda e: plato(cr, 610, 1200, e)),
                 (lambda e: cama(cr, 700, 1490, e)), (lambda e: tele(cr, 520, 1080, e, t))]
        etqs = ["muebles", "platos", "una cama", "una tele"]
        for k, fn in enumerate(cosas):
            p = (u - 0.08 - k * 0.2) * 5
            if p <= 0: continue
            dy = -300 * (1 - ease(min(1, p)))
            cr.save(); cr.translate(0, dy); fn(1.0); cr.restore()
        # ticket de compras que se alarga
        n = sum(1 for k in range(4) if u > 0.08 + k * 0.2)
        hh = 120 + n * 70
        cr.rectangle(875, 900, 170, hh); cr.set_source_rgb(*HUESO); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(4); cr.stroke()
        texto(cr, "COMPRAR", 960, 950, 30, TINTA, borde=0)
        for k in range(n):
            texto(cr, "✓ " + etqs[k], 885, 1015 + k * 70, 26, ROJO, centro=False, borde=0)
        return "todo otra vez", AZUL
    if i == 5:
        if u < 0.14:
            texto(cr, "¿?", 690, 1300, 320 * back(u * 9) + 1, AMBAR, borde=16)
            return "¿qué tiene que ver?", AMBAR
        if u < 0.74:
            v = (u - 0.14) / 0.6
            plano(cr, v, t)
            return "reconstruir una vida = un juego", AMBAR
        plano(cr, 1.0, t)
        sello(cr, "NO", 700, 1180, back((u - 0.74) * 6) * 1.5, -0.2, 1.0, ROJO)
        return "a los jefes no les gustó", ROJO
    if i == 6:
        if u < 0.25:
            plano(cr, 1.0, t)
            tarjeta(cr, "2000", 700, 1180, 150, FUEGO, esc=back(u * 8), rot=0.04, fondo=HUESO)
            return "salió en 2000", VERDE
        escena_a(cr, t, t)
        return "empezó con una casa quemada", FUEGO
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *FONDO1); g.add_color_stop_rgb(0.6, *FONDO2); g.add_color_stop_rgb(1, *FONDO1)
    cr.set_source(g); cr.paint()
    # fondo nuevo: cuadrícula de plano de arquitecto que se desliza + chispas que suben (antes: edificios noir y lluvia)
    off = (t * 18) % 60
    cr.set_source_rgba(*AZUL, 0.10); cr.set_line_width(1.5)
    for x in range(0, W + 60, 60):
        cr.move_to(x - off, 0); cr.line_to(x - off, H)
    for y in range(0, H + 60, 60):
        cr.move_to(0, y + off); cr.line_to(W, y + off)
    cr.stroke()
    cr.set_source_rgba(*AZUL, 0.18); cr.set_line_width(3)
    for x in range(0, W + 240, 240):
        cr.move_to(x - off * 4 % 240, 0); cr.line_to(x - off * 4 % 240, H)
    cr.stroke()
    for k in range(28):
        p = (t * 0.12 + k * 0.137) % 1.0
        x = (k * 211) % W + 25 * math.sin(t + k); y = H - p * (H + 100)
        cr.arc(x, y, 3 + (k % 3), 0, 2 * math.pi); cr.set_source_rgba(*FUEGO, 0.35 * (1 - p)); cr.fill()


def gancho(cr, t):
    # entrada nueva: cartel de plano (crema y petróleo) que flota suave, con "FUEGO" en naranja y un brillo que
    # titila debajo; texto completo desde el cuadro 0 (antes: expediente con sacudida de "retroceso")
    ys = [600, 790]
    for k, (s, y) in enumerate(zip(GANCHO["lineas"], ys)):
        z = 160 if k == 0 else 185
        font(cr, z)
        while cr.text_extents(s).x_advance > 900: z -= 4; font(cr, z)
        wtot = cr.text_extents(s).x_advance
        bob = 8 * math.sin(t * 3 + k * 1.4)
        cr.save(); cr.translate(0, bob)
        x0 = W / 2 - wtot / 2
        rrect(cr, x0 - 40 + 10, y - z * 0.9 + 12, wtot + 80, z * 1.15, 26); cr.set_source_rgba(0, 0, 0, 0.5); cr.fill()
        rrect(cr, x0 - 40, y - z * 0.9, wtot + 80, z * 1.15, 26)
        cr.set_source_rgb(*(HUESO if k == 0 else TINTA)); cr.fill_preserve()
        cr.set_source_rgb(*FUEGO); cr.set_line_width(8); cr.stroke()
        if k == 0: texto(cr, s, W / 2, y, z, TINTA, centro=True, borde=0)
        else:
            font(cr, z); w1 = cr.text_extents("CON ").x_advance; w2 = cr.text_extents("FUEGO").x_advance
            gl = cairo.RadialGradient(x0 + w1 + w2 / 2, y - z * 0.3, 10, x0 + w1 + w2 / 2, y - z * 0.3, w2 * 0.7)
            gl.add_color_stop_rgba(0, *FUEGO, 0.35 + 0.15 * math.sin(t * 11)); gl.add_color_stop_rgba(1, *FUEGO, 0)
            cr.set_source(gl); cr.rectangle(x0 + w1 - 20, y - z * 0.9, w2 + 40, z * 1.15); cr.fill()
            texto(cr, "CON ", x0, y, z, HUESO, centro=False, borde=0)
            texto(cr, "FUEGO", x0 + w1, y, z, FUEGO, centro=False, borde=0)
        cr.restore()


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: empuje lento hacia adentro en cada toma, sin vaivén (antes: cámara en mano con descenso)
    d = max(0, t - L[i]["t0"]) if i else t
    zc = 1.0 + 0.07 * ease(d / 4.0)
    cr.save()
    cr.rectangle(0, 830, W, 470); cr.rectangle(320, 1300, W - 320, 360); cr.rectangle(0, 1660, W, 40); cr.clip()
    cr.translate(690, 1200); cr.scale(zc, zc); cr.translate(-690, -1200)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0 or t > L[-1]["t1"] - 0.35:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1570, col if col else AMBAR, 40)
    chipb(cr, "Secretos de videojuegos", 340, 1745, AZUL, 34)
    cr.set_source_rgba(0, 0, 0, 0.25); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*FUEGO); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        dd = t - x["t0"]
        if 0 <= dd < 0.1:
            cr.set_source_rgba(1, 1, 1, 0.35 * (1 - dd / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0, 1.5] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [5.0, 11.0, 12.8, 15.0, 18.0, 20.5, 22.2, 25.0, 28.4, 29.8, round(L[-1]["t1"] - 0.2, 1)]
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
