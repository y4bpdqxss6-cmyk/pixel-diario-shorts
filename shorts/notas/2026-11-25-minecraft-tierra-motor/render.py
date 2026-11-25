"""Motor de respaldo Pixel Diario — Short 'Minecraft es más grande que la Tierra'.
Dibuja con cairo objetos genéricos: cubo verde y café liso (sin textura oficial), globo terráqueo simple, flechas,
contador, regla, figura de palitos, reloj y tarjetas. Sin Steve, Creepers, bloque de pasto oficial ni logos; "Minecraft"
solo como texto. Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["MÁS GRANDE QUE", "LA TIERRA"], "resalta": "TIERRA"}

# paleta nueva: "día de exploración" cielo azul + verde pasto + café tierra + amarillo sol (antes: HUD carmesí + rojo + menta)
CIELO1 = (0.30, 0.62, 0.95)
CIELO2 = (0.10, 0.30, 0.66)
VERDE = (0.40, 0.85, 0.30)
VERDE_OSC = (0.22, 0.58, 0.18)
CAFE = (0.55, 0.36, 0.20)
CAFE_OSC = (0.38, 0.24, 0.13)
AZUL = (0.18, 0.50, 0.92)
SOL = (1.0, 0.84, 0.25)
CORAL = (1.0, 0.45, 0.35)
BLANCO = (1, 1, 1)
TINTA = (0.04, 0.05, 0.10)
GRIS = (0.80, 0.84, 0.92)

RESALTA = {1: ["bloque", "metro,", "lejísimos."], 2: ["Treinta", "millones", "cada", "dirección."], 3: ["Pero", "línea.", "cuadrado."],
           4: ["más", "raro:", "nadie", "borde"], 5: ["¿Cuánto", "mide?", "3,600", "millones"], 6: ["510", "siete", "veces"],
           7: ["pierdas…", "más", "grande", "planeta."]}
COLRES = {1: SOL, 2: VERDE, 3: SOL, 4: CORAL, 5: SOL, 6: VERDE, 7: SOL}


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


# ---------- piezas genéricas ----------
def cubo(cr, x, y, s, top=VERDE, izq=CAFE, der=CAFE_OSC, borde=6):
    """cubo isométrico liso; (x, y) = vértice central frontal-superior."""
    c = 0.866 * s
    cr.move_to(x, y - s / 2); cr.line_to(x + c, y - s); cr.line_to(x, y - 1.5 * s); cr.line_to(x - c, y - s); cr.close_path()
    cr.set_source_rgb(*top); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(borde); cr.stroke()
    cr.move_to(x - c, y - s); cr.line_to(x, y - s / 2); cr.line_to(x, y + s / 2); cr.line_to(x - c, y); cr.close_path()
    cr.set_source_rgb(*izq); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.stroke()
    cr.move_to(x + c, y - s); cr.line_to(x, y - s / 2); cr.line_to(x, y + s / 2); cr.line_to(x + c, y); cr.close_path()
    cr.set_source_rgb(*der); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.stroke()


def globo(cr, x, y, r, t, etiqueta=None):
    if r < 2: return
    cr.arc(x + r * 0.07, y + r * 0.09, r, 0, 2 * math.pi); cr.set_source_rgba(0, 0, 0, 0.4); cr.fill()
    cr.save(); cr.arc(x, y, r, 0, 2 * math.pi); cr.clip()
    cr.set_source_rgb(*AZUL); cr.paint()
    off = (t * 0.25) % 2.0
    for k in range(-1, 2):
        bx = x + (k * 2 + 0.0 - off) * r
        for (dx, dy, ex, ey) in ((-0.2, -0.3, 0.45, 0.3), (0.35, 0.25, 0.3, 0.42), (-0.55, 0.45, 0.25, 0.2), (0.75, -0.45, 0.22, 0.18)):
            cr.save(); cr.translate(bx + dx * r, y + dy * r); cr.scale(ex * r, ey * r); cr.arc(0, 0, 1, 0, 2 * math.pi); cr.restore()
            cr.set_source_rgb(*VERDE); cr.fill()
    cr.arc(x - r * 0.35, y - r * 0.4, r * 0.3, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.25); cr.fill()
    cr.restore()
    cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgb(*TINTA); cr.set_line_width(max(2, r * 0.06)); cr.stroke()
    if etiqueta: texto(cr, etiqueta, x, y + r + 60, 50, BLANCO, borde=8)


def flecha(cr, x0, y0, x1, y1, col=SOL, ancho=16):
    ang = math.atan2(y1 - y0, x1 - x0); lng = math.hypot(x1 - x0, y1 - y0)
    if lng < 4: return
    cr.save(); cr.translate(x0, y0); cr.rotate(ang)
    cr.move_to(0, -ancho / 2); cr.line_to(lng - 40, -ancho / 2); cr.line_to(lng - 40, -ancho * 1.7); cr.line_to(lng, 0)
    cr.line_to(lng - 40, ancho * 1.7); cr.line_to(lng - 40, ancho / 2); cr.line_to(0, ancho / 2); cr.close_path()
    cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
    cr.restore()


def monito(cr, x, y, t, esc=1.0):
    """figura de palitos caminando (genérica)."""
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    sw = math.sin(t * 9)
    cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_width(14); cr.set_source_rgb(*TINTA)
    cr.move_to(0, -150); cr.line_to(0, -60)
    cr.move_to(0, -60); cr.line_to(40 * sw, 0); cr.move_to(0, -60); cr.line_to(-40 * sw, 0)
    cr.move_to(0, -130); cr.line_to(-35 * sw, -80); cr.move_to(0, -130); cr.line_to(35 * sw, -80)
    cr.stroke()
    cr.arc(0, -185, 32, 0, 2 * math.pi); cr.set_source_rgb(*BLANCO); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(10); cr.stroke()
    cr.restore()


def reloj(cr, x, y, r, t):
    cr.arc(x + 8, y + 10, r, 0, 2 * math.pi); cr.set_source_rgba(0, 0, 0, 0.4); cr.fill()
    cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgb(*BLANCO); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(10); cr.stroke()
    for k in range(12):
        a = k * math.pi / 6
        cr.move_to(x + r * 0.8 * math.cos(a), y + r * 0.8 * math.sin(a)); cr.line_to(x + r * 0.92 * math.cos(a), y + r * 0.92 * math.sin(a))
    cr.set_line_width(5); cr.stroke()
    for (vel, lng, w) in ((14, 0.78, 7), (1.2, 0.5, 11)):
        a = t * vel - math.pi / 2
        cr.move_to(x, y); cr.line_to(x + r * lng * math.cos(a), y + r * lng * math.sin(a))
        cr.set_source_rgb(*(CORAL if vel > 5 else TINTA)); cr.set_line_width(w); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()


def chipb(cr, s, x, y, color, size=34, txt=TINTA):
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: bloque cuadrado con bisel y
    cubito isométrico a la izquierda (antes: píldora redonda con corazoncito)."""
    x = max(x, 340)
    font(cr, size); tw = cr.text_extents(s).x_advance; h = size + 34; w = min(tw + h + 50, W - 30 - x)
    bloque_rect(cr, x, y, w, h, color, prof=8)
    cubo(cr, x + h / 2 + 2, y + h / 2 + 8, h * 0.32, borde=3)
    z = size; font(cr, z)
    while cr.text_extents(s).x_advance > w - h - 24: z -= 2; font(cr, z)
    cr.set_source_rgb(*txt); cr.move_to(x + h + 8, y + h / 2 + z * 0.36); cr.show_text(s)


def fmt(n): return f"{int(n):,}"


AREA = [(0, 850, W, 450), (320, 1300, W - 320, 360), (0, 1660, W, 40)]


def escena_a(cr, t, final=False):
    """inicio y cierre: cubo de pasto liso que crece junto a un globo terráqueo que se encoge. Nada en y 300–820."""
    if not final:
        g = ease(t / 3.2)
    else:
        a = L[-1]["t0"]; b = L[-1]["t1"]
        g = 1 - ease((t - a) / max(0.1, b - a))  # regresa al tamaño del cuadro 0 para el bucle
        g = max(0.0, g)
    s = 170 * (1 + 0.35 * g) * (1 + 0.02 * math.sin(t * 3))
    cubo(cr, 600, 880 + 1.5 * s, s)
    globo(cr, 940, 1420, 95 * (1 - 0.55 * g), t)


def escena(cr, t):
    i = linea_en(t)
    u = local(i, t)
    if i == 0:
        escena_a(cr, t)
        return "Minecraft", VERDE
    if i == 1:
        e = back(min(1, u * 4))
        cubo(cr, 520, 1200, 190 * max(0.02, e))
        # regla genérica
        if u > 0.12:
            v = ease((u - 0.12) * 4)
            y0, y1 = 1105, 1105 + 190 * v
            cr.rectangle(770, y0, 46, y1 - y0); cr.set_source_rgb(*SOL); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
            for k in range(int(10 * v) + 1):
                yy = y0 + 19 * k; cr.move_to(770, yy); cr.line_to(790 if k % 5 else 806, yy)
            cr.set_line_width(4); cr.stroke()
            if v > 0.95: texto(cr, "1 m", 900, 1215, 60, SOL, borde=8)
        if u < 0.55:
            tarjeta(cr, "1 BLOQUE = 1 METRO", 690, 955, 64, TINTA, esc=back(max(0, u - 0.08) * 5), rot=-0.03, fondo=SOL)
            return "1 bloque = 1 metro", SOL
        x = lerp(700, 1010, ease((u - 0.55) * 2.5))
        texto(cr, "BORDE →", x, 960, 64 * (1 - 0.4 * ease((u - 0.55) * 2.5)), CORAL, borde=8)
        for k in range(12):
            xx = 640 + k * 30
            if xx < x - 120: cr.rectangle(xx, 952, 16, 6)
        cr.set_source_rgb(*BLANCO); cr.fill()
        return "el borde está lejísimos", CORAL
    if i == 2:
        cx, cy = 690, 1110
        v = ease(min(1, u * 1.6))
        cubo(cr, cx, cy + 40, 70)
        flecha(cr, cx + 70, cy, cx + 70 + 260 * v, cy)
        flecha(cr, cx - 70, cy, cx - 70 - 260 * v, cy)
        flecha(cr, cx, cy - 90, cx, cy - 90 - 150 * v)
        flecha(cr, cx, cy + 90, cx, cy + 90 + 150 * v)
        n = 30_000_000 * ease(min(1, u * 1.3))
        tarjeta(cr, fmt(n), 690, 1480, 76, TINTA, esc=back(u * 5), fondo=VERDE)
        return ("del centro a la orilla" if u < 0.6 else "en cada dirección"), VERDE
    if i == 3:
        cx, cy, lado = 690, 1100, 500
        if u < 0.42:
            v = ease(u / 0.3)
            flecha(cr, cx - lado / 2, cy, cx - lado / 2 + lado * v, cy, SOL, 18)
            texto(cr, "SOLO UNA LÍNEA", cx, cy - 70, 60, SOL, borde=9, alpha=min(1, u * 6))
            return "solo una línea", SOL
        v = ease((u - 0.42) / 0.3)
        hh = max(18, lado * v)
        x0 = cx - lado / 2; y0 = cy - hh / 2
        cr.rectangle(x0 + 12, y0 + 12, lado, hh); cr.set_source_rgba(0, 0, 0, 0.4); cr.fill()
        cr.rectangle(x0, y0, lado, hh); cr.set_source_rgb(*CAFE_OSC); cr.fill()
        nfill = int(100 * ease((u - 0.55) / 0.42))
        tam = lado / 10
        for k in range(nfill):
            r_, c_ = divmod(k, 10)
            yy = y0 + r_ * tam
            if yy + tam <= y0 + hh + 1:
                cr.rectangle(x0 + c_ * tam + 3, yy + 3, tam - 6, tam - 6)
        cr.set_source_rgb(*VERDE); cr.fill()
        cr.rectangle(x0, y0, lado, hh); cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
        return "todo el cuadrado", VERDE
    if i == 4:
        # banda que corre, figura de palitos caminando, reloj que gira rápido y "¿BORDE?" a lo lejos
        cr.rectangle(320, 1260, W - 320, 70); cr.set_source_rgb(*VERDE_OSC); cr.fill()
        cr.rectangle(320, 1290, W - 320, 40); cr.set_source_rgb(*CAFE); cr.fill()
        off = (t * 260) % 80
        for k in range(16):
            xx = 320 + k * 80 - off
            cr.rectangle(xx, 1260, 40, 30)
        cr.set_source_rgba(1, 1, 1, 0.18); cr.fill()
        monito(cr, 560, 1262, t, 1.0)
        reloj(cr, 830, 1010, 120 * back(u * 4) + 1, t)
        if u > 0.35:
            texto(cr, "¿BORDE?", 960, 1210, 54, GRIS, borde=7, alpha=min(1, (u - 0.35) * 5))
        return ("casi nadie ha llegado" if u < 0.5 else "horas y horas caminando"), CORAL
    if i == 5:
        if u < 0.26:
            texto(cr, "¿?", 690, 1290, 380 * back(u * 7) + 1, SOL, borde=16)
            return "¿cuánto mide?", SOL
        v = (u - 0.26) / 0.74
        y = lerp(860, 1110, rebote(min(1, v * 2.2)))
        tarjeta(cr, "3,600,000,000 km²", 690, y, 64, TINTA, rot=-0.03 + 0.03 * ease(v * 3), fondo=SOL)
        return "3,600 millones de km²", SOL
    if i == 6:
        cx, cy, lado = 690, 1100, 480
        x0, y0 = cx - lado / 2, cy - lado / 2
        cr.rectangle(x0 + 12, y0 + 12, lado, lado); cr.set_source_rgba(0, 0, 0, 0.4); cr.fill()
        cr.rectangle(x0, y0, lado, lado); cr.set_source_rgb(*VERDE_OSC); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
        pos = [(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)]  # 7 copias
        # el centro se queda para el contador ×7
        if u < 0.3:
            r = 150 * back(u * 5)
            globo(cr, cx, cy, r, t)
            if u > 0.08: tarjeta(cr, "510 M km²", cx, cy + 220, 54, TINTA, esc=back((u - 0.08) * 6), fondo=BLANCO)
            return "la Tierra: 510 millones", AZUL
        n = min(7, 1 + int((u - 0.3) / 0.4 * 7))
        for k in range(n):
            c_, r_ = pos[k]
            globo(cr, x0 + lado / 6 + c_ * lado / 3, y0 + lado / 6 + r_ * lado / 3, 70, t + k)
        if u > 0.72:
            tarjeta(cr, "×7", cx, cy + 30, 110, TINTA, esc=back((u - 0.72) * 5), rot=0.05, fondo=SOL)
        return (f"{n} Tierras" if u < 0.72 else "unas siete veces"), VERDE
    if i == 7:
        escena_a(cr, t, final=True)
        return ("si te pierdes…" if u < 0.4 else "más grande que el planeta"), VERDE
    return None, None


def nube(cr, x, y, s, a=0.85):
    for (dx, dy, w, h) in ((0, 0, 4, 1), (1, -1, 2, 1), (0.5, 1, 3, 0.6)):
        cr.rectangle(x + dx * s, y + dy * s, w * s, h * s)
    cr.set_source_rgba(1, 1, 1, a); cr.fill()


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *CIELO1); g.add_color_stop_rgb(1, *CIELO2)
    cr.set_source(g); cr.paint()
    # fondo nuevo: cielo de día con nubes cuadradas que avanzan + colinas escalonadas abajo + rejilla isométrica tenue
    # (antes: rejilla hexagonal roja que sube, líneas de escaneo y viñeta que late)
    for k, (yy, s, vel) in enumerate(((180, 40, 22), (300, 26, 14), (1180, 34, 18), (1560, 30, 26), (1760, 44, 12))):
        x = ((k * 330 + t * vel) % (W + 400)) - 250
        nube(cr, x, yy, s, 0.5 if yy > 900 else 0.8)
    cr.set_line_width(2); cr.set_source_rgba(1, 1, 1, 0.07)
    for k in range(-20, 30):
        x = k * 90 + (t * 6) % 90
        cr.move_to(x, H); cr.line_to(x + 0.577 * H, 0); cr.move_to(x, H); cr.line_to(x - 0.577 * H, 0)
    cr.stroke()
    # colinas escalonadas
    for k in range(0, W, 60):
        h = 70 + 40 * math.sin(k * 0.013 + 1.3) + 30 * math.sin(k * 0.031)
        h = round(h / 20) * 20
        cr.rectangle(k, H - h, 60, h)
    cr.set_source_rgba(*VERDE_OSC, 0.55); cr.fill()


def gancho(cr, t):
    # entrada nueva: placas tipo bloque con extrusión y bisel; cada palabra rebota en escalera (como bloques que se
    # acomodan) y "TIERRA" en verde con globito girando; legible completo desde el cuadro 0 (antes: placas HUD con glitch)
    ys = [610, 800]
    for k, (s, y) in enumerate(zip(GANCHO["lineas"], ys)):
        z = 130 if k == 0 else 190
        font(cr, z)
        while cr.text_extents(s).x_advance > 900: z -= 4; font(cr, z)
        wtot = cr.text_extents(s).x_advance; x0 = W / 2 - wtot / 2
        bob = 5 * math.sin(t * 3.0 + k * 1.4)
        bloque_rect(cr, x0 - 40, y - z * 0.86 + bob, wtot + 80, z * 1.1, BLANCO if k == 0 else TINTA, prof=16)
        if k == 0:
            texto(cr, s, W / 2, y + bob, z, TINTA, borde=0)
        else:
            x = x0
            for p in s.split(" "):
                font(cr, z); adv = cr.text_extents(p + " ").x_advance
                col = VERDE if p == GANCHO["resalta"] else BLANCO
                cr.move_to(x, y + bob); cr.text_path(p)
                cr.set_source_rgb(*col); cr.fill()
                x += adv


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: paneo lateral lento con leve balanceo (antes: acercamiento con sacudida en golpes)
    px = 22 * math.sin(t * 0.6); rot = 0.012 * math.sin(t * 0.45)
    cr.save()
    for r in AREA: cr.rectangle(*r)
    cr.clip()
    cr.translate(690 + px, 1150); cr.rotate(rot); cr.translate(-690, -1150)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0 or t > L[-1]["t1"] - 0.35:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1570, col if col else SOL, 40, BLANCO if col in (AZUL,) else TINTA)
    chipb(cr, "Minecraft Java Edition", 340, 1745, BLANCO, 34)
    cr.set_source_rgba(0, 0, 0, 0.25); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*VERDE); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        dd = t - x["t0"]
        if 0 <= dd < 0.1:
            cr.set_source_rgba(1, 1, 1, 0.30 * (1 - dd / 0.1)); cr.paint()
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
