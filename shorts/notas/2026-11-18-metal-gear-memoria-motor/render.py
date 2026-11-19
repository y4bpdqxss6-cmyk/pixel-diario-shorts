"""Motor de respaldo Pixel Diario — Short 'Metal Gear Solid espiaba tus partidas'.
Dibuja con cairo, sin personajes, logos ni diseños reconocibles: ojo geométrico genérico, tarjeta de memoria gris
genérica, control y consola genéricos sin marcas. "Metal Gear Solid", "PlayStation", "Psycho Mantis" y "Castlevania"
solo como texto. Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["TE ESPÍA", "LA MEMORIA"], "resalta": "ESPÍA"}

# paleta nueva: noche violeta + cian neón + magenta (antes: cielo de día pastel + verde pasto + azul marino)
FONDO1 = (0.07, 0.03, 0.14)
FONDO2 = (0.22, 0.08, 0.34)
VIOLETA = (0.66, 0.36, 1.0)
CIAN = (0.25, 0.95, 1.0)
MAGENTA = (1.0, 0.30, 0.66)
AMARILLO = (1.0, 0.84, 0.25)
GRIS = (0.58, 0.60, 0.66)
GRIS_O = (0.36, 0.38, 0.44)
BLANCO = (1, 1, 1)
TINTA = (0.04, 0.02, 0.09)
PLANO1 = (0.02, 0.32, 0.38)
PLANO2 = (0.05, 0.55, 0.60)

RESALTA = {1: ["1998,", "PlayStation,", "Psycho", "Mantis."], 2: ["mente…", "otros", "juegos."],
           3: ["Pero", "adivina", "nada.", "Castlevania", "tarjeta,"], 4: ["vibra,", "suelo,", "solo."],
           5: ["¿Cómo", "ganas?"], 6: ["puerto", "dos.", "movimientos."], 7: ["mente…", "partidas", "guardadas."]}
COLRES = {1: AMARILLO, 2: VIOLETA, 3: MAGENTA, 4: CIAN, 5: AMARILLO, 6: AMARILLO, 7: CIAN}


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
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: rectángulo oscuro con borde de
    neón y barra lateral de color (antes: píldora blanca con sombra y punto de color)."""
    x = max(x, 340)
    font(cr, size); w = cr.text_extents(s).x_advance + 70; h = size + 34
    rrect(cr, x, y, w, h, 8); cr.set_source_rgba(*TINTA, 0.85); cr.fill_preserve()
    cr.set_source_rgb(*color); cr.set_line_width(4); cr.stroke()
    cr.rectangle(x + 4, y + 4, 14, h - 8); cr.set_source_rgb(*color); cr.fill()
    cr.set_source_rgb(*BLANCO); cr.move_to(x + 40, y + size + 8); cr.show_text(s)


# ---------- dibujos genéricos ----------
def tarjeta_mem(cr, cx, cy, esc, pulso=0.0):
    if esc <= 0.01: return
    cr.save(); cr.translate(cx, cy); cr.scale(esc, esc)
    w, h = 260, 320
    # glow
    cr.set_source_rgba(*VIOLETA, 0.25 * pulso); rrect(cr, -w / 2 - 24, -h / 2 - 24, w + 48, h + 48, 30); cr.fill()
    # cuerpo con esquina recortada
    cr.move_to(-w / 2, -h / 2 + 50); cr.line_to(-w / 2 + 50, -h / 2); cr.line_to(w / 2, -h / 2)
    cr.line_to(w / 2, h / 2); cr.line_to(-w / 2, h / 2); cr.close_path()
    cr.set_source_rgb(*GRIS); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
    rrect(cr, -90, -110, 180, 120, 10); cr.set_source_rgb(0.92, 0.92, 0.95); cr.fill()
    for k in range(3):
        cr.rectangle(-70, -88 + k * 30, 140 - k * 30, 12); cr.set_source_rgb(*GRIS_O); cr.fill()
    # contactos
    for k in range(7):
        cr.rectangle(-100 + k * 30, 100, 18, 40); cr.set_source_rgb(*AMARILLO); cr.fill()
    cr.restore()


def ojo(cr, cx, cy, esc, abre=1.0, mira=(0, 0)):
    if esc <= 0.01: return
    cr.save(); cr.translate(cx, cy); cr.scale(esc, esc)
    a = max(0.04, abre)
    cr.save(); cr.scale(1, a)
    cr.move_to(-170, 0); cr.curve_to(-90, -110, 90, -110, 170, 0); cr.curve_to(90, 110, -90, 110, -170, 0); cr.close_path()
    cr.restore()
    cr.set_source_rgb(0.95, 0.95, 1.0); cr.fill_preserve()
    cr.save(); cr.clip_preserve()
    cr.new_sub_path(); cr.arc(mira[0], mira[1], 62, 0, 2 * math.pi); cr.set_source_rgb(*VIOLETA); cr.fill()
    cr.new_sub_path(); cr.arc(mira[0], mira[1], 28, 0, 2 * math.pi); cr.set_source_rgb(*TINTA); cr.fill()
    cr.new_sub_path(); cr.arc(mira[0] - 18, mira[1] - 20, 11, 0, 2 * math.pi); cr.set_source_rgb(*BLANCO); cr.fill()
    cr.restore()
    cr.set_source_rgb(*TINTA); cr.set_line_width(10); cr.stroke()
    cr.restore()


def ondas(cr, cx, cy, t, col=VIOLETA, n=4, rmax=420):
    for k in range(n):
        r = ((t * 160 + k * rmax / n) % rmax)
        cr.new_sub_path(); cr.arc(cx, cy, r + 40, 0, 2 * math.pi)
        cr.set_source_rgba(*col, 0.55 * (1 - r / rmax)); cr.set_line_width(10); cr.stroke()


def tarjeta(cr, s, x, y, size, color, esc=1.0, rot=0.0, fondo=BLANCO):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 70
    rrect(cr, -w / 2 + 8, -size * 0.95 + 10, w, size * 1.5, 20); cr.set_source_rgba(0, 0, 0, 0.4); cr.fill()
    rrect(cr, -w / 2, -size * 0.95, w, size * 1.5, 20); cr.set_source_rgb(*fondo); cr.fill()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 35, size * 0.25); cr.text_path(s)
    cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke_preserve(); cr.set_source_rgb(*color); cr.fill()
    cr.restore()


def consola(cr, cx, cy, esc, puertos=False, cable=0.0, t=0.0):
    """caja gris genérica, sin marcas; con puertos=True se ven dos entradas '1' y '2'"""
    if esc <= 0.01: return
    cr.save(); cr.translate(cx, cy); cr.scale(esc, esc)
    rrect(cr, -260, -110, 520, 220, 24); cr.set_source_rgb(0.74, 0.75, 0.79); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
    cr.rectangle(-200, -70, 400, 16); cr.set_source_rgb(*GRIS_O); cr.fill()
    if puertos:
        for k, xx in enumerate((-110, 110)):
            rrect(cr, xx - 70, 0, 140, 70, 12); cr.set_source_rgb(*TINTA); cr.fill()
            texto(cr, str(k + 1), xx, -18, 54, CIAN if k == 1 else BLANCO, borde=6)
        # cable: salta del 1 al 2
        x = lerp(-110, 110, ease(cable)); yb = 35 - 140 * math.sin(math.pi * ease(cable))
        cr.set_source_rgb(*AMARILLO); cr.set_line_width(16); cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.move_to(x, yb + 20); cr.curve_to(x, yb + 200, -60, 260, -170, 420); cr.stroke()
        rrect(cr, x - 46, yb - 30, 92, 60, 10); cr.set_source_rgb(*AMARILLO); cr.fill_preserve()
        cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()
        if 0.85 < cable < 1.0 or (cable >= 1 and math.sin(t * 20) > 0.6):
            for k in range(8):
                ang = k * math.pi / 4
                cr.move_to(110 + 70 * math.cos(ang), 35 + 70 * math.sin(ang))
                cr.line_to(110 + 120 * math.cos(ang), 35 + 120 * math.sin(ang))
            cr.set_source_rgb(*CIAN); cr.set_line_width(8); cr.stroke()
    cr.restore()


def control(cr, cx, cy, esc, t, vibra=0.0):
    if esc <= 0.01: return
    dx = vibra * 9 * math.sin(t * 70); dy = vibra * 6 * math.cos(t * 83)
    cr.save(); cr.translate(cx + dx, cy + dy); cr.rotate(vibra * 0.05 * math.sin(t * 50)); cr.scale(esc, esc)
    # cuerpo genérico: barra redondeada con dos asas redondas
    cr.new_sub_path(); cr.arc(-150, 30, 90, 0, 2 * math.pi)
    cr.new_sub_path(); cr.arc(150, 30, 90, 0, 2 * math.pi)
    rrect(cr, -200, -70, 400, 140, 60)
    cr.set_source_rgb(0.30, 0.30, 0.36); cr.fill()
    cr.new_sub_path(); cr.arc(-150, 0, 34, 0, 2 * math.pi); cr.set_source_rgb(0.18, 0.18, 0.22); cr.fill()
    for k, (bx, by) in enumerate(((140, -30), (180, 0), (140, 30), (100, 0))):
        cr.new_sub_path(); cr.arc(bx, by, 15, 0, 2 * math.pi)
        cr.set_source_rgb(*(CIAN, MAGENTA, AMARILLO, VIOLETA)[k]); cr.fill()
    cr.restore()
    if vibra > 0.1:
        cr.set_source_rgba(*CIAN, 0.8); cr.set_line_width(8); cr.set_line_cap(cairo.LINE_CAP_ROUND)
        for s in (-1, 1):
            for k in range(3):
                x = cx + s * (300 + k * 30); a = 40 + k * 20
                cr.move_to(x, cy - a); cr.line_to(x + s * 10, cy); cr.line_to(x, cy + a); cr.stroke()


def bloques(cr, cx, cy, u, t, resalta=-1, etiqueta=None):
    cols = (CIAN, MAGENTA, AMARILLO, VIOLETA, GRIS, CIAN, GRIS, MAGENTA)
    for k in range(8):
        r, c = divmod(k, 4)
        a = ease(u * 3 - k * 0.15)
        if a <= 0: continue
        x = cx - 230 + c * 120; y = cy + r * 120
        on = (k == resalta)
        rrect(cr, x, y, 100, 100, 12)
        cr.set_source_rgba(*(BLANCO if on and math.sin(t * 10) > -0.3 else cols[k]), a); cr.fill_preserve()
        cr.set_source_rgba(*TINTA, a); cr.set_line_width(6); cr.stroke()
    if etiqueta:
        tarjeta(cr, etiqueta, cx + 20, cy - 90, 52, MAGENTA, esc=back(etiqueta_u(t)))


_ETI = {"t": None}


def etiqueta_u(t):
    return 1.0


def globo(cr, s, x, y, esc):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    font(cr, 36); w = cr.text_extents(s).x_advance + 60; h = 90
    rrect(cr, -w / 2, -h / 2, w, h, 40); cr.move_to(-40, h / 2 - 2); cr.line_to(-90, h / 2 + 60); cr.line_to(10, h / 2 - 2)
    cr.set_source_rgb(*BLANCO); cr.fill()
    cr.set_source_rgb(*TINTA); cr.move_to(-w / 2 + 35, 15); cr.show_text(s)
    cr.restore()


def escena_a(cr, t, i):
    """imagen del inicio y del cierre: tarjeta de memoria que late y un ojo que se abre encima y la mira.
    Nada en y 300–820 (el texto del gancho va encima)."""
    pulso = 0.5 + 0.5 * math.sin(t * 6)
    ondas(cr, 640, 1230, t, VIOLETA, 3, 330)
    tarjeta_mem(cr, 640, 1260, 1.0 + 0.04 * pulso, pulso)
    abre = 0.35 + 0.65 * ease((t - L[i]["t0"]) * 1.6) if i == 0 else 1.0
    ojo(cr, 640, 950, 0.75, abre, (12 * math.sin(t * 1.7), 30))


def escena(cr, t):
    i = linea_en(t)
    if i == 0 or i == 7:
        escena_a(cr, t, i)
        return ("METAL GEAR SOLID", MAGENTA) if i == 0 else ("partidas guardadas", CIAN)
    if i == 1:
        u = local(1, t)
        consola(cr, 640, 1300, back(u * 3))
        tarjeta(cr, "1998 · PlayStation", 600, 900, 76, AMARILLO, esc=back(u * 4), rot=-0.04)
        if u > 0.5:
            e = back((u - 0.5) * 4)
            tarjeta(cr, "PSYCHO MANTIS", 640, 1090, 90, VIOLETA, esc=e, rot=0.03, fondo=TINTA)
        return "1998", AMARILLO
    if i == 2:
        u = local(2, t)
        ondas(cr, 640, 980, t * 1.5, VIOLETA, 5, 500)
        ojo(cr, 640, 980, 0.9 + 0.05 * math.sin(t * 4), 1.0, (40 * math.sin(t * 3), 0))
        for k in range(3):
            a = ease((u - 0.35 - k * 0.15) * 5)
            if a <= 0: continue
            x = 420 + k * 220; y = 1300
            rrect(cr, x - 80, y - 80, 160, 160, 16)
            cr.set_source_rgba(*(VIOLETA if a > 0.9 else GRIS_O), a); cr.fill_preserve()
            cr.set_source_rgba(*TINTA, a); cr.set_line_width(6); cr.stroke()
            texto(cr, "?", x, y + 40, 110 * back(a), BLANCO, borde=8, alpha=a)
        return "“leo tu mente”", VIOLETA
    if i == 3:
        u = local(3, t)
        if u < 0.35:
            texto(cr, "NO ADIVINA", 560, 1000, 110 * back(u * 5), MAGENTA, borde=14)
            tarjeta_mem(cr, 640, 1300, 0.7, 0.5)
        else:
            v = (u - 0.35) / 0.65
            bloques(cr, 640, 1050, v, t, resalta=2 if v > 0.35 else -1, etiqueta="CASTLEVANIA" if v > 0.35 else None)
            if v > 0.55:
                globo(cr, "Te gusta Castlevania, ¿verdad?", 660, 1420, back((v - 0.55) * 5))
        return "lee la tarjeta", MAGENTA
    if i == 4:
        u = local(4, t)
        # piso en perspectiva (solo a la derecha de la zona de la mascota)
        cr.save(); cr.rectangle(330, 0, W, H); cr.clip()
        cr.set_source_rgba(*CIAN, 0.25); cr.set_line_width(3)
        for k in range(12):
            y = 1150 + k * k * 6
            cr.move_to(0, y); cr.line_to(W, y); cr.stroke()
        cr.restore()
        vib = ease((u - 0.45) * 4)
        y = lerp(980, 1180, ease(u * 2.2))
        control(cr, 640, y, 0.95, t, vib)
        if u > 0.6:
            texto(cr, "¡SE MUEVE SOLO!", 600, 1440, 74, CIAN, borde=10, alpha=ease((u - 0.6) * 5))
        return "control en el suelo", CIAN
    if i == 5:
        u = local(5, t)
        texto(cr, "¿?", 600, 1200, 240 + 60 * ease(u * 2) + 10 * math.sin(t * 8), AMARILLO, borde=14)
        return "¿cómo le ganas?", AMARILLO
    if i == 6:
        u = local(6, t)
        consola(cr, 640, 1020, 1.1, puertos=True, cable=ease((u - 0.1) * 2.2), t=t)
        abre = 1.0 if u < 0.6 else max(0.04, 1 - ease((u - 0.6) * 4))
        ojo(cr, 830, 1360, 0.5, abre, (25 * math.sin(t * 12), 0))
        if u > 0.75:
            texto(cr, "PUERTO 2", 760, 1560, 70, AMARILLO, borde=10, alpha=ease((u - 0.75) * 5))
        return None, None
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    if i == 6:
        g.add_color_stop_rgb(0, *PLANO1); g.add_color_stop_rgb(1, *PLANO2)
        cr.set_source(g); cr.paint()
        cr.set_source_rgba(1, 1, 1, 0.10); cr.set_line_width(2)
        off = (t * 40) % 80
        for k in range(-30, 30):
            x = k * 80 + off
            cr.move_to(x, 0); cr.line_to(x + H * 0.4, H); cr.stroke()
        return
    g.add_color_stop_rgb(0, *FONDO1); g.add_color_stop_rgb(1, *FONDO2)
    cr.set_source(g); cr.paint()
    # partículas violetas que flotan + líneas de escaneo (antes: destellos cuadrados que suben en cielo de día)
    rnd = random.Random(5)
    for k in range(30):
        x0 = rnd.uniform(0, W); sp = rnd.uniform(15, 45); r = rnd.uniform(3, 8)
        y = (rnd.uniform(0, H) - t * sp) % H
        x = x0 + 20 * math.sin(t + k)
        cr.new_sub_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgba(*VIOLETA, 0.45); cr.fill()
    cr.set_source_rgba(0, 0, 0, 0.12)
    for y in range(0, H, 8): cr.rectangle(0, y, W, 2)
    cr.fill()


def gancho(cr, t):
    # entrada nueva: cada línea llega desde grande (zoom hacia atrás) con parpadeo de interferencia;
    # en el cuadro 0 ya está a escala ~1.15 y legible (antes: subía desde abajo con rebote)
    ys = [600, 790]; sizes = [150, 128]
    for k, (s, y, z) in enumerate(zip(GANCHO["lineas"], ys, sizes)):
        u = ease((t - k * 0.06) / 0.4)
        e = lerp(1.18, 1.0, u)
        cr.save(); cr.translate(W / 2, y); cr.scale(e, e)
        if t < 0.5 and int(t * 30) % 4 == 1:
            texto(cr, s, -8, 0, z, CIAN, borde=0, alpha=0.6)
        palabras = s.split(" "); font(cr, z)
        wtot = cr.text_extents(s).x_advance; x = -wtot / 2
        for p in palabras:
            col = MAGENTA if p == GANCHO["resalta"] else BLANCO
            adv = cr.text_extents(p + " ").x_advance
            texto(cr, p, x, 0, z, col, centro=False, borde=26)
            x += adv
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
            if acc > vis: col = (0.70, 0.68, 0.78)
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
    # cámara nueva: balanceo de giro lento + empuje continuo dentro de cada escena; temblor solo cuando vibra el control
    # (antes: inclinación vertical lenta + respiración de escala)
    zc = 1.0 + 0.05 * local(i, t)
    rot = 0.012 * math.sin(t * 0.9)
    sx = sy = 0
    if i == 4 and local(4, t) > 0.45:
        sx = 6 * math.sin(t * 61); sy = 5 * math.cos(t * 47)
    cr.save(); cr.translate(660 + sx, 1150 + sy); cr.rotate(rot); cr.scale(zc, zc); cr.translate(-660, -1150)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0 and t < L[0]["t1"] + 0.1:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1560, col, 40)
    chipb(cr, "El juego te engaña", 360, 1760, VIOLETA, 34)
    cr.set_source_rgba(0, 0, 0, 0.3); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*CIAN); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        d = t - x["t0"]
        if 0 <= d < 0.1:
            cr.set_source_rgba(*VIOLETA, 0.18 * (1 - d / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0, 1.5] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [16.8, 21.0, 27.0, round(L[-1]["t1"] - 0.3, 1)]
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
