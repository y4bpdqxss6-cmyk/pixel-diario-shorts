"""Motor de respaldo Pixel Diario — Short 'Celeste te deja saltar en el aire'.
Dibuja con cairo, sin personajes, logos ni diseños reconocibles: figura geométrica azul genérica
(no Madeline), bloques y montaña nevada genéricos. "Celeste" y "Maddy Thorson" solo como texto simple.
Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["SALTAS EN", "EL AIRE"], "resalta": "EL AIRE"}

# paleta nueva: amanecer de montaña, azul petróleo + durazno (antes: arcade azul cobalto + magenta)
CIELO1 = (0.04, 0.12, 0.2)
CIELO2 = (0.16, 0.3, 0.42)
CIELO3 = (0.93, 0.56, 0.45)
AMBAR = (1.0, 0.78, 0.25)
CORAL = (1.0, 0.45, 0.38)
TURQ = (0.3, 0.95, 0.85)
LIMA = (0.7, 1.0, 0.35)
AZUL = (0.35, 0.6, 1.0)
PIEDRA = (0.3, 0.35, 0.45)
NIEVE = (0.93, 0.96, 1.0)
BLANCO = (1, 1, 1)
OSCURO = (0.02, 0.03, 0.06)

RESALTA = {0: ["aire"], 1: ["borde…", "saltas."], 2: ["suerte:", "instante", "extra"], 3: ["Pero", "único."],
           4: ["antes", "guarda."], 5: ["esquina", "píxeles,", "empuja"], 6: ["¿Por", "qué?", "Maddy", "Thorson,"],
           7: ["trucos", "escondidos", "justo."], 8: ["imposible", "regaló", "aire."]}
COLRES = {1: TURQ, 2: AMBAR, 3: CORAL, 4: LIMA, 5: TURQ, 6: AMBAR, 7: CORAL, 8: AMBAR}


def ease(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)


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
        cr.set_source_rgba(*OSCURO, alpha); cr.set_line_width(borde); cr.set_line_join(cairo.LINE_JOIN_ROUND)
        cr.stroke_preserve()
    cr.set_source_rgba(*color, alpha); cr.fill()
    return ext.x_advance


def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0); cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi); cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); cr.close_path()


def chipb(cr, s, x, y, color, size=34):
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: etiqueta blanca rectangular con
    barra de color a la izquierda y texto oscuro (antes: píldora rellena de color con sombra dura)."""
    x = max(x, 340)
    font(cr, size); w = cr.text_extents(s).x_advance + 70; h = size + 30
    rrect(cr, x, y, w, h, 8); cr.set_source_rgba(*BLANCO, 0.95); cr.fill()
    cr.rectangle(x, y, 18, h); cr.set_source_rgb(*color); cr.fill()
    cr.set_source_rgb(*OSCURO); cr.move_to(x + 40, y + size + 8); cr.show_text(s)


def chip_serie(cr, t):
    s = "El juego te ayuda en secreto"
    font(cr, 38); w = cr.text_extents(s).x_advance + 60; x = W / 2 - w / 2; y = 170
    rrect(cr, x, y, w, 70, 35); cr.set_source_rgba(*OSCURO, 0.7); cr.fill()
    rrect(cr, x, y, w, 70, 35); cr.set_source_rgb(*AMBAR); cr.set_line_width(4); cr.stroke()
    cr.set_source_rgb(*AMBAR); cr.move_to(x + 30, y + 48); cr.show_text(s)


# ---------- dibujos genéricos ----------
def figura(cr, x, y, esc=1.0, t=0.0, estela=0.0, col=AZUL):
    """figura geométrica genérica: cuerpo redondeado azul + cabeza circular blanca con visor; y = pies"""
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    if estela > 0:
        for k in range(1, 4):
            rrect(cr, -40 - k * 34, -120, 80, 120, 30); cr.set_source_rgba(*col, 0.18 * estela / k); cr.fill()
    rrect(cr, -40, -120, 80, 120, 30); cr.set_source_rgb(*col); cr.fill()
    cr.new_sub_path(); cr.arc(0, -160, 42, 0, 2 * math.pi); cr.set_source_rgb(*NIEVE); cr.fill()
    rrect(cr, -8, -175, 44, 22, 10); cr.set_source_rgb(*OSCURO); cr.fill()
    cr.set_source_rgb(*col); cr.set_line_width(18); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    a = math.sin(t * 14) * 0.6
    cr.move_to(-18, -6); cr.line_to(-18 - 30 * math.sin(a), 30); cr.stroke()
    cr.move_to(18, -6); cr.line_to(18 + 30 * math.sin(a), 30); cr.stroke()
    cr.restore()


def plataforma(cr, x0, x1, y, h=140):
    cr.rectangle(x0, y, x1 - x0, h); cr.set_source_rgb(*PIEDRA); cr.fill()
    cr.rectangle(x0, y, x1 - x0, 22); cr.set_source_rgb(*NIEVE); cr.fill()
    cr.set_source_rgba(0, 0, 0, 0.25)
    for k in range(int((x1 - x0) / 70)):
        cr.rectangle(x0 + 20 + k * 70, y + 50 + (k % 2) * 30, 30, 12); cr.fill()


def reloj_arena(cr, x, y, esc, t, a=1.0):
    cr.save(); cr.translate(x, y); cr.scale(esc, esc); cr.rotate(0.15 * math.sin(t * 4))
    cr.set_source_rgba(*NIEVE, a)
    cr.rectangle(-55, -80, 110, 14); cr.fill(); cr.rectangle(-55, 66, 110, 14); cr.fill()
    cr.move_to(-45, -66); cr.line_to(45, -66); cr.line_to(6, 0); cr.line_to(45, 66); cr.line_to(-45, 66); cr.line_to(-6, 0); cr.close_path()
    cr.set_line_width(7); cr.stroke()
    u = (t * 0.6) % 1
    cr.set_source_rgba(*AMBAR, a)
    cr.move_to(-35 * (1 - u), -60 + 55 * u); cr.line_to(35 * (1 - u), -60 + 55 * u); cr.line_to(0, -4); cr.close_path(); cr.fill()
    cr.move_to(-38 * u, 60); cr.line_to(38 * u, 60); cr.line_to(0, 60 - 50 * u); cr.close_path(); cr.fill()
    cr.rectangle(-2, -4, 4, 60); cr.fill()
    cr.restore()


def boton(cr, x, y, r, on, a=1.0):
    cr.new_sub_path(); cr.arc(x, y + 12, r, 0, 2 * math.pi); cr.set_source_rgba(0, 0, 0, 0.5 * a); cr.fill()
    cr.new_sub_path(); cr.arc(x, y + (8 if on else 0), r, 0, 2 * math.pi)
    cr.set_source_rgba(*(LIMA if on else (0.5, 0.55, 0.6)), a); cr.fill()
    texto(cr, "SALTAR", x, y + 14 + (8 if on else 0), 36, OSCURO, borde=0, alpha=a)


def bloques(cr, x, y, n, m, s=110):
    for i in range(n):
        for j in range(m):
            rrect(cr, x + i * s + 3, y + j * s + 3, s - 6, s - 6, 10); cr.set_source_rgb(*PIEDRA); cr.fill()
            cr.rectangle(x + i * s + 3, y + j * s + 3, s - 6, 14); cr.set_source_rgba(1, 1, 1, 0.15); cr.fill()


def montana(cr, cx, base, w, h, nieve=True, col=(0.35, 0.42, 0.55)):
    cr.move_to(cx - w / 2, base); cr.line_to(cx - w * 0.12, base - h * 0.72); cr.line_to(cx, base - h)
    cr.line_to(cx + w * 0.18, base - h * 0.65); cr.line_to(cx + w / 2, base); cr.close_path(); cr.set_source_rgb(*col); cr.fill()
    if nieve:
        cr.move_to(cx - w * 0.16, base - h * 0.66); cr.line_to(cx, base - h); cr.line_to(cx + w * 0.2, base - h * 0.62)
        cr.line_to(cx + w * 0.08, base - h * 0.7); cr.line_to(cx - w * 0.02, base - h * 0.6); cr.close_path()
        cr.set_source_rgb(*NIEVE); cr.fill()


def tarjeta(cr, s, x, y, size, color, esc=1.0, rot=0.0):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 60
    rrect(cr, -w / 2, -size * 0.95, w, size * 1.5, 14); cr.set_source_rgb(*BLANCO); cr.fill()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 30, size * 0.25); cr.show_text(s)
    cr.restore()


def letrero(cr, x, y, flip, t):
    """letrero de madera genérico que se voltea de DIFÍCIL a JUSTO"""
    cr.set_source_rgb(0.45, 0.3, 0.18); cr.rectangle(x - 12, y, 24, 230); cr.fill()
    sx = abs(math.cos(flip * math.pi))
    cr.save(); cr.translate(x, y); cr.scale(max(sx, 0.02), 1)
    rrect(cr, -185, -90, 370, 150, 18); cr.set_source_rgb(0.62, 0.42, 0.25); cr.fill()
    s, c = ("DIFÍCIL", CORAL) if flip < 0.5 else ("JUSTO", LIMA)
    texto(cr, s, 0, 20, 80, c, borde=10)
    cr.restore()


def escena_a(cr, t, i):
    """imagen del inicio y del cierre: la figura corre, se pasa del borde, flota un instante y salta. Nada en y 300–820."""
    plataforma(cr, 330, 600, 1200)
    plataforma(cr, 840, 1180, 1200)
    per = 2.6; u = (t % per) / per
    edge = 600
    if u < 0.4:      # corre hacia el borde
        x = lerp(380, edge + 30, u / 0.4); y = 1200; est = 0.8
    elif u < 0.55:   # ya fuera del borde, flota (tiempo de coyote)
        x = edge + 30 + (u - 0.4) / 0.15 * 30; y = 1200 + 4 * math.sin(t * 30); est = 0.2
    elif u < 0.85:   # salta y aterriza al otro lado
        p = (u - 0.55) / 0.3; x = lerp(edge + 60, 930, p); y = 1200 - 280 * math.sin(math.pi * p); est = 0.6
    else:
        x = 930; y = 1200; est = 0
    # línea punteada del borde
    cr.set_source_rgba(*AMBAR, 0.9); cr.set_line_width(5); cr.set_dash([18, 14])
    cr.move_to(edge, 1000); cr.line_to(edge, 1420); cr.stroke(); cr.set_dash([])
    if 0.4 <= u < 0.55:
        texto(cr, "¡EN EL AIRE!", edge + 60, 1000, 54, TURQ, borde=8)
    figura(cr, x, y, 1.1, t, estela=est)


def escena(cr, t):
    i = linea_en(t)
    if i == 0 or i == 8:
        escena_a(cr, t, i)
        return ("Celeste · 2018", TURQ) if i == 0 else ("un regalo en el aire", AMBAR)
    if i == 1:
        u = local(1, t)
        plataforma(cr, 200, 560, 1220)
        cr.set_source_rgba(*AMBAR, 1); cr.set_line_width(6); cr.set_dash([18, 14])
        cr.move_to(560, 880); cr.line_to(560, 1420); cr.stroke(); cr.set_dash([])
        texto(cr, "BORDE", 560, 860, 50, AMBAR, borde=8)
        x = lerp(420, 700, ease(u * 1.3)); y = 1220 - (260 * math.sin(math.pi * ease((u - 0.7) * 3.3)) if u > 0.7 else 0)
        figura(cr, x, y, 1.0, t * 0.3, estela=0.5)
        if u > 0.45:
            texto(cr, "CÁMARA LENTA", 820, 1000, 48, BLANCO, borde=6, alpha=ease((u - 0.45) * 5))
        return "ya fuera del borde", AMBAR
    if i == 2:
        u = local(2, t)
        plataforma(cr, 200, 520, 1240)
        figura(cr, 650, 1240 + 6 * math.sin(t * 25), 1.0, 0)
        reloj_arena(cr, 650, 930, 0.9 + 0.1 * ease(u * 4), t, ease(u * 5))
        texto(cr, "+1 instante", 650, 1380, 66, AMBAR, borde=12, alpha=ease((u - 0.25) * 6))
        return "tiempo de coyote", AMBAR
    if i == 3:
        u = local(3, t)
        nombres = ["COYOTE", "?", "?"]
        for k in range(3):
            e = ease((u - k * 0.15) * 4)
            if e < 0.01: continue
            x = 380 + k * 240; y = 1100
            cr.save(); cr.translate(x, y); cr.scale(e, e); cr.rotate(0.06 * math.sin(t * 5 + k))
            rrect(cr, -100, -140, 200, 280, 20); cr.set_source_rgb(*(TURQ if k == 0 else CIELO2)); cr.fill()
            rrect(cr, -100, -140, 200, 280, 20); cr.set_source_rgb(*BLANCO); cr.set_line_width(6); cr.stroke()
            texto(cr, nombres[k], 0, 20, 48 if k == 0 else 120, OSCURO if k == 0 else CORAL, borde=0 if k == 0 else 8)
            cr.restore()
        return "hay más trucos", CORAL
    if i == 4:
        u = local(4, t)
        plataforma(cr, 340, 1000, 1260)
        p = min(u / 0.65, 1.0)
        if u < 0.65: fy = lerp(880, 1260, p * p)
        else:
            q = (u - 0.65) / 0.35; fy = 1260 - 300 * math.sin(math.pi * min(q, 1))
        figura(cr, 640, fy, 0.9, t)
        on = 0.35 < u < 0.7
        boton(cr, 880, 960, 70, on)
        if on:
            for k in range(3):
                pp = ((t * 2 + k / 3) % 1)
                cr.new_sub_path(); cr.arc(lerp(880, 650, pp), lerp(1000, 1250, pp), 14, 0, 2 * math.pi)
                cr.set_source_rgba(*LIMA, 1 - pp); cr.fill()
            texto(cr, "GUARDADO", 880, 1120, 46, LIMA, borde=6)
        return "búfer de salto", LIMA
    if i == 5:
        u = local(5, t)
        bloques(cr, 340, 820, 2, 1, 120)
        bloques(cr, 700, 820, 3, 1, 120)
        # la figura sube, roza la esquina y se desliza a un lado
        p = ease(u * 1.4)
        fx = 575 + (65 * ease((u - 0.35) * 4) if u > 0.35 else 0)
        fy = lerp(1380, 1110, p) if u < 0.35 else lerp(1110, 760, ease((u - 0.5) * 3))
        figura(cr, fx, fy + 200, 0.75, t)
        if 0.25 < u < 0.6:
            cr.new_sub_path(); cr.arc(580, 940, 40 + 10 * math.sin(t * 20), 0, 2 * math.pi)
            cr.set_source_rgba(*CORAL, 0.8); cr.set_line_width(8); cr.stroke()
        if u > 0.35:
            a = ease((u - 0.35) * 4)
            cr.set_source_rgba(*TURQ, a); cr.set_line_width(12)
            cr.move_to(480, 1000); cr.line_to(620, 1000); cr.stroke()
            cr.move_to(640, 1000); cr.line_to(605, 972); cr.line_to(605, 1028); cr.close_path(); cr.fill()
            texto(cr, "unos píxeles", 860, 1060, 52, TURQ, borde=8, alpha=a)
        return "corrección de esquinas", TURQ
    if i == 6:
        u = local(6, t)
        montana(cr, 540, 1420, 900, 520)
        texto(cr, "¿?", 540, 1080, 220 + 20 * math.sin(t * 6), AMBAR, borde=14)
        tarjeta(cr, "MADDY THORSON", 640, 1300, 56, CIELO1, esc=ease((u - 0.25) * 4), rot=-0.03)
        return "la creadora lo contó", AMBAR
    if i == 7:
        u = local(7, t)
        # el cambio visual más fuerte: amanecer de golpe + letrero que se voltea + lista que se enciende
        cr.rectangle(-1000, -1000, W + 2000, H + 2000); cr.set_source_rgba(*CIELO3, 0.35 * ease(u * 3)); cr.fill()
        montana(cr, 780, 1420, 760, 560, col=(0.4, 0.38, 0.5))
        letrero(cr, 830, 1010, ease((u - 0.15) * 2.5), t)
        for k, s in enumerate(["COYOTE", "BÚFER", "ESQUINAS"]):
            on = u > 0.35 + k * 0.15
            y = 900 + k * 110
            rrect(cr, 340, y - 55, 280, 80, 14); cr.set_source_rgba(*(LIMA if on else (0.4, 0.45, 0.5)), 0.95); cr.fill()
            texto(cr, ("✓ " if on else "") + s, 480, y, 40, OSCURO, borde=0)
        return "difícil pero justo", LIMA
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *CIELO1); g.add_color_stop_rgb(0.55, *CIELO2); g.add_color_stop_rgb(1, *CIELO3)
    cr.set_source(g); cr.paint()
    # montañas lejanas con paralaje + nieve que cae (antes: rejilla de neón + estrellas de píxel)
    off = (t * 12) % 600
    for k in range(-1, 4):
        montana(cr, k * 600 - off + 200, 1700, 700, 420, nieve=True, col=(0.12, 0.2, 0.3))
    off2 = (t * 28) % 500
    for k in range(-1, 4):
        montana(cr, k * 500 - off2 + 100, 1920, 600, 360, nieve=False, col=(0.08, 0.14, 0.22))
    rnd = random.Random(9)
    for k in range(60):
        x0 = rnd.uniform(0, W); sp = rnd.uniform(60, 160); r = rnd.choice([3, 4, 6])
        y = (rnd.uniform(0, H) + t * sp) % H; x = x0 + 30 * math.sin(t * 1.2 + k)
        cr.new_sub_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.55); cr.fill()


def gancho(cr, t):
    # entrada nueva: aparece grande y se encoge a su lugar con un leve rebote (antes: caía desde arriba); cuadro 0 ya legible
    ys = [590, 790]; sizes = [150, 175]
    for k, (s, y, z) in enumerate(zip(GANCHO["lineas"], ys, sizes)):
        u = max(0, min(1, (t - k * 0.06) / 0.45))
        esc = 1.0 + 0.08 * (1 - ease(u)) - 0.05 * math.sin(u * math.pi) * (1 - u)
        col = AMBAR if s == GANCHO["resalta"] else BLANCO
        cr.save(); cr.translate(W / 2, y); cr.scale(esc, esc)
        texto(cr, s, 0, 0, z, col, borde=20)
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
    y = 420 if len(lineas) <= 2 else 380
    acc = 0
    for ln in lineas:
        wtot = cr.text_extents(" ".join(ln)).x_advance; x = W / 2 - wtot / 2
        for p in ln:
            acc += len(p) + 1
            col = COLRES.get(i, AMBAR) if p in RESALTA.get(i, []) else BLANCO
            a = 1.0 if acc <= vis else 0.28
            font(cr, size); adv = cr.text_extents(p + " ").x_advance
            cr.move_to(x, y); cr.text_path(p)
            cr.set_source_rgba(*OSCURO, a); cr.set_line_width(9); cr.stroke_preserve()
            cr.set_source_rgba(*col, a); cr.fill()
            x += adv
        y += 90


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: deriva vertical suave + vaivén lateral (antes: empuje hacia adentro + inclinación)
    dy = -40 * math.sin(t * 0.7); dx = 25 * math.sin(t * 0.45)
    zc = 1.0 + (0.08 * ease(t / L[0]["t1"]) if i == 0 else 0.04)
    cr.save(); cr.translate(540 + dx, 1100 + dy); cr.scale(zc, zc); cr.translate(-540, -1100)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0 and t < L[0]["t1"] + 0.1:
        gancho(cr, t); chip_serie(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1480, col, 40)
    chipb(cr, "El juego te ayuda en secreto", 360, 1740, AMBAR, 28)
    cr.set_source_rgba(1, 1, 1, 0.12); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*TURQ); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        d = t - x["t0"]
        if 0 <= d < 0.1:
            cr.set_source_rgba(1, 1, 1, 0.14 * (1 - d / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [round(L[-1]["t1"] - 0.3, 1)]
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
