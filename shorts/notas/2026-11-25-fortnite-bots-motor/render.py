"""Motor de respaldo Pixel Diario — Short 'Fortnite te pone bots si juegas mal'.
Dibuja con cairo objetos genéricos: isla vista desde arriba, siluetas geométricas (cápsula + círculo), engranes,
mira circular, mapa de papel, barras, reloj, puerta, bloques y diana. Sin personajes, skins, autobús, tormenta,
armas ni logos; "Fortnite" y "Epic Games" solo como texto. Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["NO SON", "PERSONAS"], "resalta": "PERSONAS"}

# paleta nueva: "arcade nocturno" morado profundo + cian + magenta + amarillo (antes: cielo azul + verde pasto + café)
CIELO1 = (0.20, 0.08, 0.38)
CIELO2 = (0.05, 0.03, 0.14)
CIAN = (0.25, 0.90, 1.00)
MAGENTA = (1.00, 0.30, 0.70)
AMARILLO = (1.00, 0.85, 0.20)
NARANJA = (1.00, 0.55, 0.20)
VERDE = (0.45, 0.95, 0.45)
ARENA = (0.98, 0.86, 0.55)
PASTO = (0.35, 0.75, 0.40)
MAR = (0.10, 0.45, 0.80)
PAPEL = (0.96, 0.92, 0.80)
ROJO = (0.95, 0.20, 0.25)
BLANCO = (1, 1, 1)
TINTA = (0.04, 0.03, 0.10)
GRIS = (0.80, 0.80, 0.92)
SOL = AMARILLO
CORAL = MAGENTA
AZUL = MAR

RESALTA = {1: ["2019,", "Capítulo", "2."], 2: ["no", "personas…", "máquina."], 3: ["Pero", "nadie", "cuál", "es", "cuál."],
           4: ["más", "raro:", "mejor", "menos", "bots"], 5: ["¿Por", "qué?", "nuevos", "primer", "minuto"],
           6: ["construir", "apuntar."], 7: ["fácil…", "puros", "bots."]}
COLRES = {1: AMARILLO, 2: CIAN, 3: MAGENTA, 4: AMARILLO, 5: CIAN, 6: VERDE, 7: AMARILLO}
SILCOL = [CIAN, MAGENTA, AMARILLO, VERDE, NARANJA, (0.70, 0.55, 1.0)]

def ease(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)


def back(x):
    x = max(0, min(1, x)); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def rebote(x):
    x = max(0, min(1, x))
    if x < 0.5: return 4 * x * x
    x -= 0.75; return 1 - 3 * (0.0625 - x * x) if x < 0.25 else 1


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


def bloque_rect(cr, x, y, w, h, color, prof=12):
    """rectángulo 'de bloque': extrusión abajo-derecha + bisel claro arriba-izquierda (estilo nuevo de placas y chips)."""
    cr.rectangle(x + prof, y + prof, w, h); cr.set_source_rgba(0, 0, 0, 0.5); cr.fill()
    cr.rectangle(x, y, w, h); cr.set_source_rgb(*color); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()
    cr.rectangle(x + 6, y + 6, w - 12, 8); cr.set_source_rgba(1, 1, 1, 0.35); cr.fill()
    cr.rectangle(x + 6, y + h - 14, w - 12, 8); cr.set_source_rgba(0, 0, 0, 0.18); cr.fill()


def tarjeta(cr, s, x, y, size, color, esc=1.0, rot=0.0, fondo=BLANCO):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 70
    bloque_rect(cr, -w / 2, -size * 0.95, w, size * 1.5, fondo)
    font(cr, size); cr.set_source_rgb(*color); cr.move_to(-w / 2 + 35, size * 0.25); cr.show_text(s)
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
    acc = 0
    y = 440 if len(lineas) <= 2 else 380
    for ln in lineas:
        wtot = cr.text_extents(" ".join(ln)).x_advance; x = W / 2 - wtot / 2
        for p in ln:
            acc += len(p) + 1
            col = COLRES.get(i, SOL) if p in RESALTA.get(i, []) else BLANCO
            if acc > vis: col = (0.78, 0.84, 0.95)
            font(cr, size); adv = cr.text_extents(p + " ").x_advance
            cr.move_to(x, y); cr.text_path(p)
            cr.set_source_rgba(*TINTA, 1); cr.set_line_width(12); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve()
            cr.set_source_rgba(*col, 1); cr.fill()
            x += adv
        y += 90


# ---------- piezas genéricas (estilo nuevo: stickers redondeados con sombra inclinada) ----------
def sticker(cr, x, y, w, h, color, r=26, prof=12):
    rrect(cr, x + prof, y + prof, w, h, r); cr.set_source_rgba(0, 0, 0, 0.55); cr.fill()
    rrect(cr, x, y, w, h, r); cr.set_source_rgb(*color); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()


def tarjeta(cr, s, x, y, size, color, esc=1.0, rot=0.0, fondo=BLANCO):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 70
    sticker(cr, -w / 2, -size * 0.95, w, size * 1.5, fondo)
    font(cr, size); cr.set_source_rgb(*color); cr.move_to(-w / 2 + 35, size * 0.25); cr.show_text(s)
    cr.restore()


def engrane(cr, x, y, r, ang, col=GRIS):
    if r < 2: return
    n = 8
    cr.save(); cr.translate(x, y); cr.rotate(ang)
    cr.new_path()
    for k in range(n * 2):
        a0 = k * math.pi / n; rr = r if k % 2 == 0 else r * 0.74
        cr.arc(0, 0, rr, a0, a0 + math.pi / n)
    cr.close_path()
    cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(max(2, r * 0.12)); cr.stroke()
    cr.arc(0, 0, r * 0.3, 0, 2 * math.pi); cr.set_source_rgb(*TINTA); cr.fill()
    cr.restore()


def silueta(cr, x, y, esc, col, abre=0.0):
    """silueta genérica: cápsula + círculo. abre>0: se parte en dos mitades como una caja."""
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    for lado in ((-1, 1) if abre > 0 else (0,)):
        cr.save(); cr.translate(lado * 60 * abre, 0); cr.rotate(lado * 0.35 * abre)
        if abre > 0:
            cr.rectangle(-80 if lado < 0 else 0, -260, 80, 270); cr.clip()
        rrect(cr, -55, -150, 110, 150, 50); cr.set_source_rgb(*col); cr.fill_preserve()
        cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
        cr.arc(0, -195, 42, 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.stroke()
        cr.restore()
    cr.restore()


def isla(cr, cx, cy, t, esc=1.0):
    cr.save(); cr.translate(cx, cy); cr.scale(esc, esc)
    cr.save(); cr.scale(1.0, 0.62)
    for (r, col) in ((400, (0.16, 0.6, 0.9)), (360, ARENA), (320, PASTO)):
        cr.new_path()
        for k in range(41):
            a = k / 40 * 2 * math.pi
            rr = r * (1 + 0.07 * math.sin(3 * a + 1) + 0.05 * math.sin(5 * a))
            (cr.move_to if k == 0 else cr.line_to)(rr * math.cos(a), rr * math.sin(a))
        cr.close_path(); cr.set_source_rgb(*col); cr.fill()
    cr.restore()
    # árboles redondos genéricos
    for (dx, dy) in ((-220, -60), (190, 70), (40, -140), (-90, 120)):
        cr.arc(dx, dy, 34, 0, 2 * math.pi); cr.set_source_rgb(0.2, 0.55, 0.28); cr.fill()
    cr.restore()


def mira(cr, x, y, r, col=ROJO):
    cr.set_source_rgb(*col); cr.set_line_width(9)
    cr.arc(x, y, r, 0, 2 * math.pi); cr.stroke()
    for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        cr.move_to(x + dx * r * 0.55, y + dy * r * 0.55); cr.line_to(x + dx * r * 1.3, y + dy * r * 1.3)
    cr.stroke()


def reloj(cr, x, y, r, t):
    cr.arc(x + 8, y + 10, r, 0, 2 * math.pi); cr.set_source_rgba(0, 0, 0, 0.4); cr.fill()
    cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgb(*BLANCO); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(10); cr.stroke()
    a = t * 6 - math.pi / 2
    cr.move_to(x, y); cr.line_to(x + r * 0.8 * math.cos(a), y + r * 0.8 * math.sin(a))
    cr.set_source_rgb(*ROJO); cr.set_line_width(9); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()


def chipb(cr, s, x, y, color, size=34, txt=TINTA):
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: píldora con engranito girando
    a la izquierda (antes: bloque cuadrado con bisel y cubito)."""
    x = max(x, 340)
    font(cr, size); tw = cr.text_extents(s).x_advance; h = size + 34; w = min(tw + h + 50, W - 30 - x)
    sticker(cr, x, y, w, h, color, r=h / 2, prof=7)
    engrane(cr, x + h / 2 + 4, y + h / 2, h * 0.3, CHIPT * 2, TINTA if color != TINTA else BLANCO)
    z = size; font(cr, z)
    while cr.text_extents(s).x_advance > w - h - 30: z -= 2; font(cr, z)
    cr.set_source_rgb(*txt); cr.move_to(x + h + 10, y + h / 2 + z * 0.36); cr.show_text(s)


CHIPT = 0.0
AREA = [(0, 850, W, 450), (320, 1300, W - 320, 360), (0, 1660, W, 40)]
POS6 = [(-230, -40), (-80, -120), (90, -90), (240, -20), (-160, 90), (150, 100)]


def escena_a(cr, t, final=False):
    """inicio y cierre: isla vista desde arriba con 6 siluetas; a 4 les aparece un engrane encima. Nada en y 300–820."""
    if not final:
        g = ease(t / 2.4)
    else:
        a = L[-1]["t0"]; b = L[-1]["t1"]
        g = ease((t - a) / max(0.1, (b - a) * 0.5))
    cx, cy = 690, 1120
    z = 1.0 + 0.10 * (t / 3.0 if not final else 0.3)
    isla(cr, cx, cy, t, 0.95 * z)
    for k, (dx, dy) in enumerate(POS6):
        x = cx + dx * z; y = cy + dy * z * 0.9 + 70
        bob = 6 * math.sin(t * 4 + k)
        silueta(cr, x, y + bob, 0.42 * z, SILCOL[k])
        if k in (0, 2, 3, 5):
            r = 30 * back(min(1, max(0, g * 1.6 - k * 0.12)))
            engrane(cr, x, y + bob - 135 * 0.42 * z - 40, r, t * 3 + k, GRIS)


def escena(cr, t):
    i = linea_en(t)
    u = local(i, t)
    if i == 0:
        escena_a(cr, t)
        return "Fortnite", CIAN
    if i == 1:
        # mapa de papel con rutas punteadas; tarjeta que cae con rebote
        cr.save(); cr.translate(690, 1110); cr.rotate(-0.06)
        sticker(cr, -330, -210, 660, 420, PAPEL, r=10)
        cr.set_source_rgba(0.55, 0.45, 0.3, 0.6); cr.set_line_width(6); cr.set_dash([18, 14])
        cr.move_to(-270, 150); cr.curve_to(-120, -60, 60, 160, 260, -140); cr.stroke(); cr.set_dash([])
        cr.set_source_rgb(*ROJO); cr.set_line_width(10)
        cr.move_to(225, -175); cr.line_to(295, -105); cr.move_to(295, -175); cr.line_to(225, -105); cr.stroke()
        cr.restore()
        y = lerp(860, 1110, rebote(min(1, u * 2.2)))
        tarjeta(cr, "2019 · CAPÍTULO 2", 690, y, 70, TINTA, rot=0.04, fondo=AMARILLO)
        return "2019", AMARILLO
    if i == 2:
        x, y = 690, 1240
        abre = ease((u - 0.5) * 3) if u > 0.5 else 0
        if abre > 0:
            for k in range(3):
                engrane(cr, x - 40 + k * 40, y - 60 - 70 * k * 0.6, 34 * abre, t * 4 * (1 if k % 2 else -1), GRIS)
            cr.rectangle(x - 35, y - 210, 70, 50); cr.set_source_rgb(*VERDE); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
        silueta(cr, x, y, 1.0, MAGENTA, abre)
        mx = lerp(950, x, ease(u * 2.2)); my = lerp(920, y - 120, ease(u * 2.2))
        mira(cr, mx, my, 70)
        if u > 0.62: tarjeta(cr, "MÁQUINA", 860, 980, 54, TINTA, esc=back((u - 0.62) * 5), rot=0.08, fondo=CIAN)
        return ("¿un rival?" if u < 0.5 else "no es una persona"), CIAN
    if i == 3:
        xs = [440, 590, 740, 890, 1040 - 40]
        for k in range(5):
            fase = t * 5 + k * 1.3
            x = xs[k] + 55 * math.sin(fase) * min(1, u * 3)
            silueta(cr, x, 1250, 0.6, SILCOL[k])
            texto(cr, "?", x, 1250 - 205 * 0.6 - 30 + 8 * math.sin(fase * 1.5), 90, AMARILLO, borde=10)
        return "¿cuál es cuál?", MAGENTA
    if i == 4:
        # barra HABILIDAD que sube y contador BOTS que baja
        v = ease(u * 1.3)
        texto(cr, "HABILIDAD", 520, 945, 46, GRIS, borde=7)
        sticker(cr, 400, 970, 240, 300, (0.12, 0.08, 0.25), r=16, prof=8)
        hh = 230 * v
        rrect(cr, 418, 1255 - hh, 204, max(4, hh), 10); cr.set_source_rgb(*VERDE); cr.fill()
        texto(cr, "↑", 520, 1250 - hh - 10, 80, VERDE, borde=8) if v > 0.1 else None
        n = int(round(lerp(70, 5, v)))
        texto(cr, "BOTS", 850, 945, 46, GRIS, borde=7)
        tarjeta(cr, f"{n:02d}", 850, 1140, 150, MAGENTA if n > 20 else VERDE, fondo=TINTA)
        engrane(cr, 850, 1250, 34, t * 3, GRIS)
        return ("mejor juegas" if u < 0.5 else "menos bots"), AMARILLO
    if i == 5:
        if u < 0.22:
            texto(cr, "¿?", 690, 1290, 380 * back(u * 7) + 1, CIAN, borde=16)
            return "¿por qué?", CIAN
        if u < 0.62:
            v = (u - 0.22) / 0.4
            reloj(cr, 520, 1050, 110 * back(v * 4) + 1, t)
            texto(cr, "0:59", 520, 1230, 64, AMARILLO, borde=9)
            # puerta SALIR tachada
            sticker(cr, 800, 920, 190, 300, (0.35, 0.25, 0.55), r=8, prof=8)
            texto(cr, "SALIR", 895, 900, 44, BLANCO, borde=7)
            silueta(cr, lerp(700, 860, ease(v * 1.5)), 1210, 0.5, CIAN)
            if v > 0.55:
                cr.set_source_rgb(*ROJO); cr.set_line_width(22); cr.set_line_cap(cairo.LINE_CAP_ROUND)
                w = ease((v - 0.55) * 4)
                cr.move_to(780, 900); cr.line_to(780 + 230 * w, 900 + 340 * w); cr.stroke()
            return "el primer minuto", AMARILLO
        v = (u - 0.62) / 0.38
        tarjeta(cr, "EPIC GAMES", 690, 1000, 90, BLANCO, esc=back(v * 4), rot=-0.04, fondo=TINTA)
        for k in range(3):
            silueta(cr, 520 + k * 170, 1280, 0.42, SILCOL[k] if v > 0.3 else GRIS)
        return "que no se fueran", CIAN
    if i == 6:
        # bloques que se apilan como rampa + diana
        n = min(6, int(u * 9) + 1)
        for k in range(n):
            col_, fila = [(0, 0), (1, 0), (2, 0), (1, 1), (2, 1), (2, 2)][k]
            x = 400 + col_ * 110; y = 1180 - fila * 110
            sticker(cr, x, y, 100, 100, NARANJA if (k % 2) else AMARILLO, r=8, prof=6)
        cx, cy = 900, 1060
        rr = 130 * back(min(1, u * 3))
        for k, col in enumerate((ROJO, BLANCO, ROJO, BLANCO)):
            cr.arc(cx, cy, max(1, rr * (1 - k * 0.24)), 0, 2 * math.pi); cr.set_source_rgb(*col); cr.fill()
        cr.arc(cx, cy, max(1, rr), 0, 2 * math.pi); cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()
        if u > 0.5: mira(cr, cx, cy, 50, CIAN)
        return ("construir" if u < 0.5 else "apuntar"), VERDE
    if i == 7:
        escena_a(cr, t, final=True)
        return ("tu primera victoria…" if u < 0.45 else "puros bots"), CIAN
    return None, None


def fondo(cr, t, i):
    # fondo nuevo: noche arcade con sol de franjas en el horizonte y piso de rejilla en perspectiva que avanza
    # (antes: cielo de día con nubes cuadradas, colinas escalonadas y rejilla isométrica)
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *CIELO2); g.add_color_stop_rgb(0.55, *CIELO1); g.add_color_stop_rgb(1, *CIELO2)
    cr.set_source(g); cr.paint()
    for k in range(40):
        x = (k * 263) % W; y = (k * 151) % 820 + 40
        a = 0.3 + 0.3 * math.sin(t * 2 + k)
        cr.arc(x, y, 3, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, a); cr.fill()
    hy = 1560
    cr.save(); cr.arc(W / 2, hy, 260, math.pi, 2 * math.pi); cr.clip()
    sg = cairo.LinearGradient(0, hy - 260, 0, hy); sg.add_color_stop_rgb(0, *AMARILLO); sg.add_color_stop_rgb(1, *MAGENTA)
    cr.set_source(sg); cr.paint()
    for k in range(6):
        yy = hy - 30 - k * 34; cr.rectangle(0, yy, W, 6 + k * 1.5)
    cr.set_source_rgb(*CIELO1); cr.fill()
    cr.restore()
    cr.rectangle(0, hy, W, H - hy); cr.set_source_rgb(*CIELO2); cr.fill()
    cr.set_source_rgba(*MAGENTA, 0.55); cr.set_line_width(3)
    for k in range(-12, 13):
        cr.move_to(W / 2 + k * 40, hy); cr.line_to(W / 2 + k * 260, H)
    off = (t * 0.8) % 1.0
    for k in range(10):
        p = ((k + off) / 10) ** 2
        yy = hy + p * (H - hy); cr.move_to(0, yy); cr.line_to(W, yy)
    cr.stroke()


def gancho(cr, t):
    # entrada nueva: dos stickers inclinados que llegan deslizándose desde los lados con giro y se quedan oscilando;
    # legibles completos desde el cuadro 0 (empiezan ya dentro de pantalla) (antes: placas tipo bloque con rebote)
    ys = [620, 810]
    for k, (s, y) in enumerate(zip(GANCHO["lineas"], ys)):
        z = 150 if k == 0 else 200
        font(cr, z)
        while cr.text_extents(s).x_advance > 820: z -= 4; font(cr, z)
        wtot = cr.text_extents(s).x_advance
        ent = 1 - ease(t / 0.45) if t < 1 else 0
        dx = (-1 if k == 0 else 1) * 25 * ent
        rot = (-0.06 if k == 0 else 0.04) + 0.015 * math.sin(t * 3 + k)
        cr.save(); cr.translate(W / 2 + dx, y - z * 0.33); cr.rotate(rot)
        sticker(cr, -wtot / 2 - 40, -z * 0.62, wtot + 80, z * 1.15, AMARILLO if k == 0 else TINTA, r=30, prof=16)
        font(cr, z); cr.move_to(-wtot / 2, z * 0.36); cr.text_path(s)
        cr.set_source_rgb(*(TINTA if k == 0 else MAGENTA)); cr.fill()
        cr.restore()


def cuadro(t):
    global CHIPT
    CHIPT = t
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: acercamiento lento continuo + pequeño golpe de zoom en cada cambio de frase (antes: paneo lateral)
    golpe = 0
    for x in L[1:]:
        dd = t - x["t0"]
        if 0 <= dd < 0.3: golpe = 0.05 * (1 - dd / 0.3)
    z = 1.0 + 0.03 * ((t % 6) / 6) + golpe
    cr.save()
    for r in AREA: cr.rectangle(*r)
    cr.clip()
    cr.translate(690, 1150); cr.scale(z, z); cr.translate(-690, -1150)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0 or t > L[-1]["t1"] - 0.35:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1570, col if col else AMARILLO, 40, TINTA)
    chipb(cr, "El juego te ayuda en secreto", 340, 1745, BLANCO, 34)
    cr.set_source_rgba(0, 0, 0, 0.3); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*CIAN); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0, 1.5, 3.0] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [5.8, 8.0, 10.0, 12.0, 14.2, 17.5, 20.0, 21.5, 23.0, 25.0, 27.8, round(L[-1]["t1"] - 0.2, 1)]
        for t in sorted(set(ts)):
            cuadro(t).write_to_png(f"prueba/t{t:05.1f}.png")
    elif modo == "hoja":
        from PIL import Image
        import glob
        fs = sorted(glob.glob(sys.argv[3] + "/*.png" if len(sys.argv) > 3 else "prueba/*.png")); ims = [Image.open(f).resize((270, 480)) for f in fs]
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
