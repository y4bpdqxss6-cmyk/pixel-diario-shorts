"""Motor de respaldo Pixel Diario — Short 'The Last of Us vuelve invisible a Ellie'.
Dibuja con cairo siluetas geométricas genéricas (sin caras, sin ropa ni rasgos del juego), un muro, cajas y un
guardia genérico con cono de linterna. Sin Ellie, Joel, infectados, logos ni interfaz del juego; nombres solo como texto.
Nada de violencia. Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, random, subprocess, sys
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["ELLIE ES", "INVISIBLE"], "resalta": "INVISIBLE"}

# paleta nueva: bosque nocturno (verde musgo oscuro) + amarillo linterna + lila (antes: plano azul petróleo + naranja fuego)
FONDO1 = (0.03, 0.07, 0.06)
FONDO2 = (0.07, 0.17, 0.13)
LINTERNA = (1.0, 0.88, 0.35)
AMBAR = LINTERNA
SOL = LINTERNA
LILA = (0.74, 0.62, 1.0)
HUESO = (0.95, 0.95, 0.88)
ROJO = (0.95, 0.22, 0.22)
VERDE = (0.45, 0.90, 0.55)
AZUL = (0.55, 0.83, 0.97)
BLANCO = (1, 1, 1)
TINTA = (0.02, 0.04, 0.04)
GRIS = (0.55, 0.58, 0.58)
MUSGO = (0.22, 0.36, 0.25)
PIEDRA = (0.36, 0.38, 0.36)

RESALTA = {1: ["escondes", "enemigos."], 2: ["agachado,", "corre", "plena", "vista."], 3: ["Pero", "nadie", "existiera."],
           4: ["raro:", "solo", "descubren."], 5: ["¿Por", "qué?"], 6: ["sigilo.", "perdías", "tú."],
           7: ["Ellie", "tranquilo,", "invisible."]}
COLRES = {1: LINTERNA, 2: LILA, 3: LINTERNA, 4: LILA, 5: LINTERNA, 6: ROJO, 7: LILA}
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
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: placa con esquinas cortadas y
    barrita lateral oscura (antes: etiqueta redondeada con chincheta y borde punteado)."""
    x = max(x, 340)
    font(cr, size); tw = cr.text_extents(s).x_advance; w = min(tw + 90, W - 20 - x); h = size + 34; c = 16
    def forma(dx, dy):
        cr.new_path(); cr.move_to(x + dx + c, y + dy); cr.line_to(x + dx + w, y + dy); cr.line_to(x + dx + w, y + dy + h - c)
        cr.line_to(x + dx + w - c, y + dy + h); cr.line_to(x + dx, y + dy + h); cr.line_to(x + dx, y + dy + c); cr.close_path()
    forma(6, 8); cr.set_source_rgba(0, 0, 0, 0.5); cr.fill()
    forma(0, 0); cr.set_source_rgb(*color); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(4); cr.stroke()
    cr.rectangle(x + 14, y + 12, 10, h - 24); cr.set_source_rgb(*TINTA); cr.fill()
    z = size
    while cr.text_extents(s).x_advance > w - 60: z -= 2; font(cr, z)
    cr.set_source_rgb(*txt); cr.move_to(x + 40, y + h / 2 + z * 0.36); cr.show_text(s)


def silueta(cr, x, y, esc=1.0, agachada=0.0, alfa=1.0, color=HUESO, paso=0.0, contorno=True):
    """figura geométrica genérica (cápsula + círculo), sin cara. (x, y) = pies."""
    if alfa <= 0.01: return
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    a = max(0, min(1, agachada))
    alto = lerp(230, 150, a); incl = lerp(0, 0.35, a)
    # piernas
    for s_ in (-1, 1):
        cr.move_to(s_ * 18, -70 * (1 - 0.3 * a)); cr.line_to(s_ * 26 + 22 * math.sin(paso + (0 if s_ > 0 else math.pi)), 0)
    cr.set_line_width(24); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_source_rgba(*color, alfa); cr.stroke()
    cr.save(); cr.translate(0, -70 * (1 - 0.3 * a)); cr.rotate(incl)
    rrect(cr, -40, -(alto - 70), 80, alto - 60, 38); cr.set_source_rgba(*color, alfa); cr.fill_preserve()
    if contorno: cr.set_source_rgba(*TINTA, alfa); cr.set_line_width(6); cr.stroke()
    else: cr.new_path()
    cr.arc(0, -(alto - 70) - 38, 36, 0, 2 * math.pi); cr.set_source_rgba(*color, alfa); cr.fill_preserve()
    if contorno: cr.set_source_rgba(*TINTA, alfa); cr.set_line_width(6); cr.stroke()
    else: cr.new_path()
    cr.restore(); cr.restore()


def chica_invisible(cr, x, y, esc, t, nivel):
    """silueta baja; nivel 0 = sólida, 1 = transparente con contorno punteado y destellos."""
    al = lerp(1.0, 0.18 + 0.12 * abs(math.sin(t * 5)), nivel)
    silueta(cr, x, y, esc, 0.0, al, LILA, paso=t * 9 if nivel < 2 else 0)
    if nivel > 0.3:
        cr.save(); cr.translate(x, y); cr.scale(esc, esc)
        cr.set_dash([12, 9]); cr.set_line_width(5); cr.set_source_rgba(*LILA, nivel)
        rrect(cr, -48, -190, 96, 170, 44); cr.stroke(); cr.arc(0, -228, 42, 0, 2 * math.pi); cr.stroke(); cr.set_dash([])
        for k in range(5):
            p = (t * 0.9 + k / 5) % 1
            sx = 70 * math.sin(k * 2.3 + t); sy = -40 - 220 * p
            cr.move_to(sx - 9, sy); cr.line_to(sx + 9, sy); cr.move_to(sx, sy - 9); cr.line_to(sx, sy + 9)
            cr.set_source_rgba(*BLANCO, nivel * (1 - p)); cr.set_line_width(4); cr.stroke()
        cr.restore()


def guardia(cr, x, y, esc, ang, t, alcance=520, alerta=0.0, apertura=0.32):
    """figura genérica con linterna; el cono sale hacia 'ang' (radianes)."""
    hx, hy = x - 40 * esc * math.copysign(1, math.cos(ang)) * -1, y - 150 * esc
    g = cairo.RadialGradient(hx, hy, 10, hx, hy, alcance)
    col = tuple(lerp(a, b, alerta) for a, b in zip(LINTERNA, ROJO))
    g.add_color_stop_rgba(0, *col, 0.55); g.add_color_stop_rgba(1, *col, 0.0)
    cr.move_to(hx, hy); cr.arc(hx, hy, alcance, ang - apertura, ang + apertura); cr.close_path()
    cr.set_source(g); cr.fill()
    silueta(cr, x, y, esc, 0.0, 1.0, PIEDRA)
    cr.save(); cr.translate(hx, hy); cr.rotate(ang)
    rrect(cr, -10, -12, 46, 24, 6); cr.set_source_rgb(*GRIS); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(4); cr.stroke()
    cr.restore()
    return hx, hy


def muro(cr, x, y, w, h):
    cr.rectangle(x + 8, y + 10, w, h); cr.set_source_rgba(0, 0, 0, 0.45); cr.fill()
    cr.rectangle(x, y, w, h); cr.set_source_rgb(*PIEDRA); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()
    cr.set_line_width(3); cr.set_source_rgba(*TINTA, 0.6)
    for r in range(int(h // 40)):
        yy = y + 40 * (r + 1)
        if yy < y + h: cr.move_to(x, yy); cr.line_to(x + w, yy)
        off = 0 if r % 2 else 45
        for xx in range(int(x + off), int(x + w), 90): cr.move_to(xx, y + 40 * r); cr.line_to(xx, min(y + 40 * (r + 1), y + h))
    cr.stroke()
    for k in range(6):  # musgo
        cr.arc(x + 30 + k * w / 6, y + 4, 16 + 6 * (k % 2), math.pi, 2 * math.pi); cr.set_source_rgb(*MUSGO); cr.fill()


def caja(cr, x, y, s):
    cr.rectangle(x - s / 2 + 6, y - s + 8, s, s); cr.set_source_rgba(0, 0, 0, 0.45); cr.fill()
    cr.rectangle(x - s / 2, y - s, s, s); cr.set_source_rgb(0.55, 0.40, 0.24); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
    cr.move_to(x - s / 2, y - s); cr.line_to(x + s / 2, y); cr.move_to(x + s / 2, y - s); cr.line_to(x - s / 2, y); cr.stroke()


def suelo(cr, y=1520):
    cr.rectangle(0, y, W, 200); cr.set_source_rgb(0.10, 0.14, 0.12); cr.fill()
    cr.move_to(0, y); cr.line_to(W, y); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()


def interruptor(cr, x, y, on, t):
    rrect(cr, x - 200, y - 70, 400, 140, 70); cr.set_source_rgb(*(LILA if on else ROJO)); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
    bx = x + (110 if on else -110)
    cr.arc(bx, y, 56, 0, 2 * math.pi); cr.set_source_rgb(*HUESO); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.stroke()
    texto(cr, "SIGILO" if on else "COMBATE", x + (-55 if on else 55), y + 18, 46 if on else 40, TINTA, borde=0)


def escena_a(cr, t, extra=0.0):
    """inicio y cierre: muro, dos siluetas agachadas detrás y la baja volviéndose transparente; cono de linterna
    barriendo desde la derecha. Nada en y 300–820 (el recorte empieza en 830)."""
    suelo(cr)
    ang = math.pi + 0.25 * math.sin(t * 1.3) - 0.05
    guardia(cr, 990, 1520, 0.85, ang, t, 640)
    silueta(cr, 470, 1520, 1.35, 0.85, 1.0, HUESO)
    chica_invisible(cr, 650, 1520, 1.15, t, 0.5 + 0.5 * abs(math.sin(t * 1.7)) if extra == 0 else 1.0)
    muro(cr, 360, 1420, 440, 100)


def escena(cr, t):
    i = linea_en(t)
    u = local(i, t)
    if i == 0:
        escena_a(cr, t)
        return "The Last of Us", LILA
    if i == 1:
        # pasillo en perspectiva con guardia que barre la linterna
        cr.move_to(330, 1520); cr.line_to(560, 1050); cr.line_to(820, 1050); cr.line_to(1080, 1520); cr.close_path()
        cr.set_source_rgb(0.09, 0.13, 0.11); cr.fill()
        for k in range(5):
            yy = 1050 + (470) * (k / 5) ** 1.4
            cr.move_to(330 + (560 - 330) * (1 - (yy - 1050) / 470), yy); cr.line_to(1080 - (1080 - 820) * (1 - (yy - 1050) / 470), yy)
        cr.set_source_rgba(*MUSGO, 0.8); cr.set_line_width(3); cr.stroke()
        ang = math.pi / 2 + 0.55 * math.sin(t * 2.2)
        guardia(cr, 690, 1150, 0.6, ang, t, 480, apertura=0.28)
        caja(cr, 450, 1500, 120); caja(cr, 960, 1500, 140)
        tarjeta(cr, "PS3 · 2013", 690, 940, 66, TINTA, esc=back(u * 4), rot=-0.03, fondo=LINTERNA)
        return "te escondes", LINTERNA
    if i == 2:
        suelo(cr)
        ang = math.pi + 0.15 * math.sin(t * 1.5)
        hx, hy = guardia(cr, 1000, 1520, 0.8, ang, t, 660)
        for cx in (420, 620, 820): caja(cr, cx, 1520, 130)
        # la alta salta de caja en caja, agachada
        k = min(2, int(u * 3)); fr = (u * 3) % 1
        bx = lerp(370 + k * 200, 370 + (k + 1) * 200, ease(min(1, fr * 2.5))) if k < 2 else 770
        silueta(cr, min(bx, 770), 1520, 1.0, 0.9, 1.0, HUESO, paso=t * 6)
        # la baja corre por el centro, dentro del cono
        rx = lerp(380, 760, ease(u))
        chica_invisible(cr, rx, 1340, 0.8, t, 0.0)
        if u > 0.45: tarjeta(cr, "A PLENA VISTA", 690, 960, 58, TINTA, esc=back((u - 0.45) * 5), rot=0.03, fondo=LILA)
        return ("vas agachado" if u < 0.45 else "ella corre"), (HUESO if u < 0.45 else LILA)
    if i == 3:
        suelo(cr)
        ang = math.pi + 0.18 - 0.36 * ease(u)
        guardia(cr, 1000, 1520, 0.8, ang, t, 660)
        chica_invisible(cr, 640, 1520, 0.9, t, 0.0)
        # signo de pregunta sobre el guardia que se apaga
        al = 1 - ease((u - 0.3) / 0.3)
        if al > 0: texto(cr, "?", 1000, 1210, 120, LINTERNA, borde=10, alpha=al)
        if u > 0.5: tarjeta(cr, "0 ALERTAS", 690, 980, 90, VERDE, esc=back((u - 0.5) * 4), rot=-0.04, fondo=TINTA)
        return ("nadie grita" if u < 0.5 else "como si no existiera"), LINTERNA
    if i == 4:
        on = u < 0.6
        interruptor(cr, 690, 1000, on, t)
        suelo(cr)
        chica_invisible(cr, 690, 1520, 1.0, t, 1.0 if on else 0.0)
        if not on:
            for k in range(8):
                a_ = k * math.pi / 4
                cr.move_to(690 + 140 * math.cos(a_), 1380 + 140 * math.sin(a_)); cr.line_to(690 + 190 * math.cos(a_), 1380 + 190 * math.sin(a_))
            cr.set_source_rgba(*ROJO, 0.9 * (1 - ease((u - 0.6) / 0.4))); cr.set_line_width(8); cr.stroke()
        return ("solo en sigilo" if on else "si te descubren, se acaba"), (LILA if on else ROJO)
    if i == 5:
        texto(cr, "¿?", 690, 1350, 340 * back(u * 3) + 1, LINTERNA, borde=16)
        return "¿por qué?", LINTERNA
    if i == 6:
        # pantalla dividida: arriba ASÍ NO, abajo ASÍ SÍ
        cr.rectangle(0, 830, W, 440); cr.set_source_rgba(*ROJO, 0.10 + 0.10 * (u > 0.15) * abs(math.sin(t * 8))); cr.fill()
        texto(cr, "ASÍ NO", 180, 920, 54, ROJO, borde=7)
        cr.move_to(420, 1240); cr.line_to(1080, 1240); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
        guardia(cr, 1000, 1240, 0.55, math.pi, t, 430, alerta=ease(u * 4))
        silueta(cr, 520, 1240, 0.7, 0.85, 1.0, HUESO)
        silueta(cr, 700, 1240, 0.6, 0.0, 1.0, LILA)
        if u > 0.12:
            texto(cr, "!", 1000, 1080, 110, ROJO, borde=9)
        if u > 0.3: sello(cr, "PERDISTE", 690, 1080, back((u - 0.3) * 5) * 0.75, -0.12, 1.0, ROJO)
        if u > 0.5:
            v = ease((u - 0.5) / 0.15)
            cr.rectangle(320, 1280, W - 320, 270); cr.set_source_rgba(*VERDE, 0.14 * v); cr.fill()
            texto(cr, "ASÍ SÍ", 450, 1345, 50, VERDE, borde=7, alpha=v)
            cr.move_to(320, 1535); cr.line_to(1080, 1535); cr.set_source_rgba(*TINTA, v); cr.set_line_width(5); cr.stroke()
            guardia(cr, 1010, 1535, 0.55, math.pi, t, 430)
            silueta(cr, lerp(420, 620, ease((u - 0.5) * 2)), 1535, 0.7, 0.85, v, HUESO, paso=t * 6)
            chica_invisible(cr, lerp(540, 780, ease((u - 0.5) * 2)), 1535, 0.6, t, 1.0)
        if u > 0.75: tarjeta(cr, "NAUGHTY DOG", 760, 1350, 46, TINTA, esc=back((u - 0.75) * 6), rot=0.03, fondo=LINTERNA)
        return ("si la veían a ella…" if u < 0.5 else "así no pierdes"), (ROJO if u < 0.5 else VERDE)
    if i == 7:
        escena_a(cr, t, 1.0 if u > 0.55 else 0.0)
        if 0.25 < u < 0.6:
            texto(cr, "!", 990, 1260, 90, LINTERNA, borde=8, alpha=1 - ease((u - 0.45) / 0.15))
        return ("frente a un enemigo" if u < 0.55 else "tranquilo, es invisible"), LILA
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *FONDO1); g.add_color_stop_rgb(0.6, *FONDO2); g.add_color_stop_rgb(1, *FONDO1)
    cr.set_source(g); cr.paint()
    # fondo nuevo: edificios en ruinas con enredaderas que se desplazan despacio + esporas/luciérnagas que flotan
    # (antes: cuadrícula de plano y chispas)
    off = (t * 12) % 360
    for capa, (col, base, alt) in enumerate((((0.05, 0.11, 0.09), 1100, 520), ((0.07, 0.15, 0.12), 1250, 380))):
        for k in range(-1, 5):
            x = k * 360 - off * (0.5 + capa * 0.5)
            h_ = alt * (0.6 + 0.4 * ((k * 7 + capa * 3) % 5) / 4)
            cr.move_to(x, base); cr.line_to(x, base - h_); cr.line_to(x + 120, base - h_ + 40); cr.line_to(x + 200, base - h_ + 10)
            cr.line_to(x + 260, base - h_ * 0.7); cr.line_to(x + 260, base); cr.close_path()
            cr.set_source_rgb(*col); cr.fill()
            cr.move_to(x + 60, base - h_ + 10)
            for j in range(8): cr.line_to(x + 60 + 14 * math.sin(j + t), base - h_ + 10 + j * h_ / 8)
            cr.set_source_rgba(*MUSGO, 0.6); cr.set_line_width(5); cr.stroke()
    for k in range(30):
        p = (t * 0.06 + k * 0.137) % 1.0
        x = (k * 211) % W + 40 * math.sin(t * 0.8 + k); y = H - p * (H + 100)
        cr.arc(x, y, 3 + (k % 3), 0, 2 * math.pi)
        cr.set_source_rgba(*LINTERNA, 0.45 * (0.5 + 0.5 * math.sin(t * 3 + k)) * (1 - p)); cr.fill()


def gancho(cr, t):
    # entrada nueva: dos líneas en placas oscuras; "INVISIBLE" en lila parpadea entre sólido y contorno, como si
    # desapareciera. Completo y legible desde el cuadro 0 (antes: cartel crema flotando con brillo de fuego)
    ys = [610, 800]
    for k, (s, y) in enumerate(zip(GANCHO["lineas"], ys)):
        z = 170 if k == 0 else 175
        font(cr, z)
        while cr.text_extents(s).x_advance > 900: z -= 4; font(cr, z)
        wtot = cr.text_extents(s).x_advance
        dx = (6 * math.sin(t * 2.4)) if k == 1 else 0
        x0 = W / 2 - wtot / 2
        rrect(cr, x0 - 40 + 10, y - z * 0.9 + 12, wtot + 80, z * 1.15, 18); cr.set_source_rgba(0, 0, 0, 0.55); cr.fill()
        rrect(cr, x0 - 40, y - z * 0.9, wtot + 80, z * 1.15, 18)
        cr.set_source_rgb(*(HUESO if k == 0 else TINTA)); cr.fill_preserve()
        cr.set_source_rgb(*LILA); cr.set_line_width(8); cr.stroke()
        if k == 0:
            texto(cr, s, W / 2, y, z, TINTA, centro=True, borde=0)
        else:
            al = 0.72 + 0.28 * math.cos(t * 4.5)
            font(cr, z); cr.move_to(x0 + dx, y); cr.text_path(s)
            cr.set_source_rgba(*LILA, al); cr.fill_preserve()
            cr.set_source_rgb(*BLANCO); cr.set_line_width(4); cr.set_dash([14, 8]); cr.stroke(); cr.set_dash([])


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: paneo lateral lento (de derecha a izquierda) en cada toma (antes: empuje hacia adentro)
    d = max(0, t - L[i]["t0"]) if i else t
    px = 40 - 70 * ease(d / 5.0)
    cr.save()
    cr.rectangle(0, 830, W, 470); cr.rectangle(320, 1300, W - 320, 360); cr.rectangle(0, 1660, W, 40); cr.clip()
    cr.translate(px, 0); cr.translate(690, 1200); cr.scale(1.03, 1.03); cr.translate(-690, -1200)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0 or t > L[-1]["t1"] - 0.35:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1570, col if col else AMBAR, 40)
    chipb(cr, "El juego te ayuda en secreto", 340, 1745, LINTERNA, 34)
    cr.set_source_rgba(0, 0, 0, 0.25); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*LILA); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        dd = t - x["t0"]
        if 0 <= dd < 0.1:
            cr.set_source_rgba(1, 1, 1, 0.30 * (1 - dd / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0, 1.5] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [7.0, 9.5, 11.5, 13.5, 15.5, 17.5, 21.0, 22.5, 24.5, 27.0, 29.5, round(L[-1]["t1"] - 0.2, 1)]
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
