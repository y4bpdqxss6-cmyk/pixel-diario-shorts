"""Motor de respaldo Pixel Diario — Short 'Assassin's Creed te miente con tu vida'.
Dibuja con cairo objetos genéricos: barra de vida, corazón, burbuja de mensaje, estrellitas de golpe, lupa, moneda y
sello. Sin asesinos, capuchas, logos de Ubisoft ni nada de Doom; sin el ave ni el logo de Twitter/X. Nombres solo como
texto. Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, random, subprocess, sys
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["TU VIDA", "MIENTE"], "resalta": "MIENTE"}

# paleta nueva: "HUD de combate" carmesí oscuro + rojo vivo + verde menta (antes: noche art déco azul + dorado + crema)
FONDO1 = (0.06, 0.02, 0.04)
FONDO2 = (0.20, 0.04, 0.08)
ROJO = (1.0, 0.24, 0.27)
MENTA = (0.36, 1.0, 0.70)
AMAR = (1.0, 0.86, 0.28)
HUESO = (0.96, 0.93, 0.88)
BLANCO = (1, 1, 1)
TINTA = (0.03, 0.02, 0.03)
GRIS = (0.55, 0.52, 0.55)
BPM = 108

RESALTA = {1: ["diseñadora", "2017,", "Twitter."], 2: ["pegan,", "pedacito", "rojo."], 3: ["Pero", "no", "más", "golpes"],
           4: ["Doom", "mismo."], 5: ["¿Por", "qué?", "milagro."], 6: ["quince", "ciento…", "doble."],
           7: ["rayita", "roja…", "miente."]}
COLRES = {1: MENTA, 2: ROJO, 3: AMAR, 4: MENTA, 5: AMAR, 6: MENTA, 7: ROJO}


def ease(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)


def back(x):
    x = max(0, min(1, x)); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def lerp(a, b, u): return a + (b - a) * u


def latido(t, vel=1.0):
    """pulso tipo corazón (tum-tum) sincronizado con la música; 0..1"""
    b = (t * BPM / 60 * vel) % 2.0
    return max(math.exp(-b * 9), 0.6 * math.exp(-max(0, b - 0.5) * 9) if b >= 0.5 else 0)


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
    rrect(cr, -w / 2 + 10, -size * 0.95 + 12, w, size * 1.5, 22); cr.set_source_rgba(0, 0, 0, 0.45); cr.fill()
    rrect(cr, -w / 2, -size * 0.95, w, size * 1.5, 22); cr.set_source_rgb(*fondo); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 35, size * 0.25); cr.show_text(s)
    cr.restore()


def sello(cr, s, x, y, esc, rot, alfa=1.0, color=GRIS):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, 100); w = cr.text_extents(s).x_advance + 80
    rrect(cr, -w / 2, -85, w, 150, 18); cr.set_source_rgba(1, 1, 1, 0.85 * alfa); cr.fill()
    rrect(cr, -w / 2, -85, w, 150, 18); cr.set_source_rgba(*color, alfa); cr.set_line_width(14); cr.stroke()
    rrect(cr, -w / 2 + 16, -69, w - 32, 118, 10); cr.set_line_width(5); cr.stroke()
    cr.move_to(-w / 2 + 40, 26); cr.show_text(s)
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
            col = COLRES.get(i, AMAR) if p in RESALTA.get(i, []) else BLANCO
            if acc > vis: col = (0.86, 0.80, 0.82)
            font(cr, size); adv = cr.text_extents(p + " ").x_advance
            cr.move_to(x, y); cr.text_path(p)
            cr.set_source_rgba(*TINTA, 1); cr.set_line_width(12); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve()
            cr.set_source_rgba(*col, 1); cr.fill()
            x += adv
        y += 90


# ---------- piezas genéricas ----------
def corazon_path(cr, r):
    cr.move_to(0, r * 0.95)
    cr.curve_to(-r * 1.25, r * 0.05, -r * 1.05, -r * 1.05, 0, -r * 0.45)
    cr.curve_to(r * 1.05, -r * 1.05, r * 1.25, r * 0.05, 0, r * 0.95); cr.close_path()


def chipb(cr, s, x, y, color, size=34, txt=TINTA):
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: píldora redonda con corazoncito
    a la izquierda y línea de pulso (antes: listón con cola en V y doble filete)."""
    x = max(x, 340)
    font(cr, size); tw = cr.text_extents(s).x_advance; w = min(tw + 120, W - 20 - x); h = size + 34
    rrect(cr, x + 6, y + 8, w, h, h / 2); cr.set_source_rgba(0, 0, 0, 0.5); cr.fill()
    rrect(cr, x, y, w, h, h / 2); cr.set_source_rgb(*color); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(4); cr.stroke()
    cr.save(); cr.translate(x + h / 2 + 4, y + h / 2 + 2); corazon_path(cr, h * 0.26); cr.set_source_rgb(*TINTA); cr.fill(); cr.restore()
    z = size
    while cr.text_extents(s).x_advance > w - h - 30: z -= 2; font(cr, z)
    cr.set_source_rgb(*txt); cr.move_to(x + h + 6, y + h / 2 + z * 0.36); cr.show_text(s)


def barra(cr, cx, cy, w, frac, t, parpadeo=True, h=90, etiqueta=None, real=None):
    """barra de vida genérica centrada en (cx, cy). frac 0..1. real: tramo 'fantasma' que muestra la vida de verdad."""
    x0 = cx - w / 2; y0 = cy - h / 2
    rrect(cr, x0 + 10, y0 + 12, w, h, 18); cr.set_source_rgba(0, 0, 0, 0.5); cr.fill()
    rrect(cr, x0, y0, w, h, 18); cr.set_source_rgb(0.12, 0.08, 0.10); cr.fill_preserve(); cr.set_source_rgb(*HUESO); cr.set_line_width(7); cr.stroke()
    if real is not None and real > frac:
        rrect(cr, x0 + 10, y0 + 10, (w - 20) * real, h - 20, 10)
        cr.set_source_rgba(*MENTA, 0.35 + 0.25 * math.sin(t * 6)); cr.fill()
    if frac > 0.003:
        col = ROJO if frac < 0.3 else MENTA
        a = 1.0
        if parpadeo and frac < 0.3: a = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(t * 12))
        rrect(cr, x0 + 10, y0 + 10, max(20, (w - 20) * frac), h - 20, 10); cr.set_source_rgba(*col, a); cr.fill()
        cr.rectangle(x0 + 16, y0 + 16, max(8, (w - 32) * frac), 10); cr.set_source_rgba(1, 1, 1, 0.35 * a); cr.fill()
    for k in range(1, 10):  # marcas
        cr.move_to(x0 + w * k / 10, y0 + 8); cr.line_to(x0 + w * k / 10, y0 + 22)
    cr.set_source_rgba(*HUESO, 0.5); cr.set_line_width(3); cr.stroke()
    if etiqueta: texto(cr, etiqueta, cx, y0 - 26, 46, HUESO, borde=7)


def corazon(cr, x, y, esc, t, vel=1.0, col=ROJO):
    p = latido(t, vel)
    s = esc * (1 + 0.14 * p)
    cr.save(); cr.translate(x, y); cr.scale(s, s)
    cr.save(); cr.translate(10, 12); corazon_path(cr, 150); cr.set_source_rgba(0, 0, 0, 0.45); cr.fill(); cr.restore()
    corazon_path(cr, 150); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(8); cr.stroke()
    cr.arc(-60, -45, 26, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.45); cr.fill()
    cr.restore()
    # ondas de latido
    if p > 0.05:
        cr.arc(x, y, esc * (190 + 80 * (1 - p)), 0, 2 * math.pi); cr.set_source_rgba(*col, 0.35 * p); cr.set_line_width(8); cr.stroke()


def burbuja(cr, x, y, esc, s, t, n_puntos=True):
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    rrect(cr, -250 + 10, -110 + 12, 500, 200, 40); cr.set_source_rgba(0, 0, 0, 0.45); cr.fill()
    rrect(cr, -250, -110, 500, 200, 40); cr.move_to(-150, 88); cr.line_to(-200, 150); cr.line_to(-90, 88)
    cr.set_source_rgb(*HUESO); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
    if s: texto(cr, s, 0, 20, 70, TINTA, borde=0)
    elif n_puntos:
        for k in range(3):
            cr.arc(-60 + k * 60, -10 - 14 * max(0, math.sin(t * 8 - k)), 18, 0, 2 * math.pi)
            cr.set_source_rgb(*GRIS); cr.fill()
    cr.restore()


def estrella_golpe(cr, x, y, r, a=1.0, rot=0.0):
    cr.save(); cr.translate(x, y); cr.rotate(rot)
    cr.move_to(r, 0)
    for k in range(1, 16):
        rr = r if k % 2 == 0 else r * 0.45
        ang = k * math.pi / 8; cr.line_to(rr * math.cos(ang), rr * math.sin(ang))
    cr.close_path(); cr.set_source_rgba(*AMAR, a); cr.fill_preserve(); cr.set_source_rgba(*TINTA, a); cr.set_line_width(6); cr.stroke()
    cr.restore()


def lupa(cr, x, y, r, dibujar_dentro):
    cr.save(); cr.translate(x, y)
    cr.save(); cr.rotate(0.7); rrect(cr, r - 10, -24, r * 1.1, 48, 20); cr.set_source_rgb(0.35, 0.22, 0.16); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke(); cr.restore()
    cr.arc(0, 0, r, 0, 2 * math.pi); cr.set_source_rgb(0.10, 0.06, 0.08); cr.fill()
    cr.save(); cr.arc(0, 0, r - 4, 0, 2 * math.pi); cr.clip(); dibujar_dentro(); cr.restore()
    cr.arc(0, 0, r, 0, 2 * math.pi); cr.set_source_rgb(*HUESO); cr.set_line_width(16); cr.stroke()
    cr.arc(-r * 0.4, -r * 0.4, r * 0.18, 0, 2 * math.pi); cr.set_source_rgba(1, 1, 1, 0.25); cr.fill()
    cr.restore()


def moneda(cr, x, y, r, giro, s_a, s_b):
    """moneda que voltea: giro 0 = cara A, 1 = cara B."""
    c = math.cos(giro * math.pi); s = s_a if c >= 0 else s_b
    sx = max(0.04, abs(c))
    cr.save(); cr.translate(x, y); cr.scale(sx, 1)
    cr.arc(10, 12, r, 0, 2 * math.pi); cr.set_source_rgba(0, 0, 0, 0.45); cr.fill()
    cr.arc(0, 0, r, 0, 2 * math.pi); cr.set_source_rgb(*(ROJO if c >= 0 else MENTA)); cr.fill_preserve()
    cr.set_source_rgb(*TINTA); cr.set_line_width(10); cr.stroke()
    cr.arc(0, 0, r * 0.82, 0, 2 * math.pi); cr.set_source_rgba(*TINTA, 0.5); cr.set_line_width(4); cr.stroke()
    texto(cr, s, 0, r * 0.22, r * 0.62, BLANCO if c >= 0 else TINTA, borde=8 if c >= 0 else 0)
    cr.restore()


def escena_a(cr, t, final=False):
    """inicio y cierre: barra casi vacía que parpadea en rojo + corazón latiendo rápido. Nada en y 300–820."""
    barra(cr, 690, 1000, 640, 0.15, t, etiqueta="VIDA")
    corazon(cr, 690, 1390, 0.85, t, vel=1.6)


def escena(cr, t):
    i = linea_en(t)
    u = local(i, t)
    if i == 0:
        escena_a(cr, t)
        return "Assassin's Creed", ROJO
    if i == 1:
        tarjeta(cr, "2017", 690, 960, 90, TINTA, esc=back(u * 4), rot=-0.04, fondo=MENTA)
        burbuja(cr, 690, 1230, max(0.02, 0.9 * back(min(1, u * 3 + 0.2))), "" if u < 0.45 else "#secretos", t)
        if u > 0.6: burbuja(cr, 790, 1470, 0.6 * back((u - 0.6) * 4), "", t)
        return ("una diseñadora lo contó" if u < 0.55 else "hilo de mensajes"), MENTA
    if i == 2:
        golpes = [0.12, 0.38, 0.64]
        frac = 1.0
        for g, f_ in zip(golpes, (0.62, 0.33, 0.15)):
            if u > g: frac = f_
        if u > 0.12 and u < 0.12 + 0.02: frac = 0.62
        barra(cr, 690, 1020, 700, frac, t, etiqueta="VIDA")
        for k, g in enumerate(golpes):
            d = u - g
            if 0 <= d < 0.18:
                estrella_golpe(cr, 520 + k * 170, 1250 + (k % 2) * 90, 120 * back(d * 8), 1 - d / 0.18, t * 2 + k)
        corazon(cr, 690, 1420, 0.6, t, vel=1.4)
        return ("¡golpe!" if u < 0.7 else "un pedacito rojo"), ROJO
    if i == 3:
        barra(cr, 690, 1020, 700, 0.15, t, etiqueta="VIDA")
        lx = lerp(880, 520, ease(min(1, u * 2)))
        def dentro():
            # dentro de la lupa: el pedacito rojo se ve estiradísimo
            cr.save(); cr.translate(-lx, -1220)
            rrect(cr, 340 + 10, 1180, 700, 80, 10); cr.set_source_rgb(*ROJO); cr.fill()
            for k in range(5):
                cr.move_to(380 + k * 130, 1190); cr.line_to(380 + k * 130, 1250)
            cr.set_source_rgba(1, 1, 1, 0.5); cr.set_line_width(5); cr.stroke()
            cr.restore()
        lupa(cr, lx, 1220, 140, dentro)
        cr.move_to(lx - 60, 1090); cr.line_to(420, 1060); cr.set_source_rgba(*AMAR, 0.6); cr.set_line_width(4); cr.stroke()
        texto(cr, "15 %", 400, 920, 60, ROJO, borde=8)
        if u > 0.6: tarjeta(cr, "AGUANTA MÁS", 760, 1530, 50, TINTA, esc=back((u - 0.6) * 5), rot=0.05, fondo=AMAR)
        return ("no es lo que parece" if u < 0.6 else "aguanta más golpes"), AMAR
    if i == 4:
        e1 = max(0.02, back(min(1, u * 4))); e2 = back(max(0, min(1, (u - 0.25) * 4)))
        cr.save(); cr.translate(690, 1010); cr.scale(e1, e1); barra(cr, 0, 0, 640, 0.15, t, etiqueta="ASSASSIN'S CREED"); cr.restore()
        if e2 > 0.01:
            cr.save(); cr.translate(690, 1300); cr.scale(e2, e2); barra(cr, 0, 0, 640, 0.15, t, etiqueta="DOOM"); cr.restore()
        if u > 0.7: texto(cr, "=", 690, 1190, 120 * back((u - 0.7) * 5) + 1, AMAR, borde=10)
        return ("no es el único" if u < 0.4 else "mismo truco"), MENTA
    if i == 5:
        if u < 0.32:
            texto(cr, "¿?", 690, 1360, 360 * back(u * 6) + 1, AMAR, borde=16)
            return "¿por qué?", AMAR
        v = (u - 0.32) / 0.68
        corazon(cr, 690, 1230, 0.8, t, vel=0.7, col=ROJO)
        if v > 0.35: sello(cr, "DE MILAGRO", 690, 1470, back((v - 0.35) * 4) * 0.85, -0.10, 1.0, ROJO)
        return "sobreviviste de milagro", ROJO
    if i == 6:
        giro = ease(max(0, min(1, (u - 0.35) / 0.3)))
        moneda(cr, 690, 1170, 210, giro, "15 %", "30 %")
        real = 0.15 + 0.15 * giro
        barra(cr, 690, 1480, 600, 0.15, t, h=80, real=real if giro > 0 else None)
        if u > 0.7: tarjeta(cr, "EL DOBLE", 860, 940, 50, TINTA, esc=back((u - 0.7) * 5), rot=0.06, fondo=MENTA)
        return ("dice 15 %" if giro < 0.5 else "te queda el doble"), (ROJO if giro < 0.5 else MENTA)
    if i == 7:
        escena_a(cr, t, final=True)
        return ("la última rayita" if u < 0.5 else "la parte que más miente"), ROJO
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *FONDO1); g.add_color_stop_rgb(0.55, *FONDO2); g.add_color_stop_rgb(1, *FONDO1)
    cr.set_source(g); cr.paint()
    # fondo nuevo: rejilla hexagonal que sube despacio + líneas de escaneo + viñeta roja que late con la música
    # (antes: abanicos art déco con confeti dorado)
    r = 70; dy = (t * 18) % (r * math.sqrt(3))
    cr.set_line_width(2); cr.set_source_rgba(*ROJO, 0.10)
    for row in range(-1, int(H / (r * math.sqrt(3))) + 2):
        for col in range(-1, int(W / (r * 1.5)) + 2):
            cx = col * r * 1.5; cy = row * r * math.sqrt(3) + (col % 2) * r * math.sqrt(3) / 2 - dy
            for k in range(6):
                a = k * math.pi / 3
                (cr.move_to if k == 0 else cr.line_to)(cx + r * 0.92 * math.cos(a), cy + r * 0.92 * math.sin(a))
            cr.close_path()
    cr.stroke()
    for y in range(0, H, 8):
        cr.rectangle(0, y, W, 2)
    cr.set_source_rgba(0, 0, 0, 0.18); cr.fill()
    p = latido(t)
    vg = cairo.RadialGradient(W / 2, H / 2, 500, W / 2, H / 2, 1150)
    vg.add_color_stop_rgba(0, *ROJO, 0); vg.add_color_stop_rgba(1, *ROJO, 0.10 + 0.22 * p)
    cr.set_source(vg); cr.paint()


def gancho(cr, t):
    # entrada nueva: dos líneas tipo HUD; "MIENTE" en rojo con un falló (glitch) de colores desplazados que tiembla y
    # se calma; todo legible completo desde el cuadro 0 (antes: marco art déco con brillo dorado que barre)
    ys = [600, 800]
    for k, (s, y) in enumerate(zip(GANCHO["lineas"], ys)):
        z = 170 if k == 0 else 200
        font(cr, z)
        while cr.text_extents(s).x_advance > 900: z -= 4; font(cr, z)
        wtot = cr.text_extents(s).x_advance; x0 = W / 2 - wtot / 2
        bob = 3 * math.sin(t * 2.4 + k)
        cr.move_to(x0 - 50 + 10, y - z * 0.88 + 12 + bob); cr.rel_line_to(wtot + 100, 0); cr.rel_line_to(-30, z * 1.12); cr.rel_line_to(-(wtot + 70), 0); cr.close_path()
        cr.set_source_rgba(0, 0, 0, 0.55); cr.fill()
        cr.move_to(x0 - 50, y - z * 0.88 + bob); cr.rel_line_to(wtot + 100, 0); cr.rel_line_to(-30, z * 1.12); cr.rel_line_to(-(wtot + 70), 0); cr.close_path()
        cr.set_source_rgb(*(HUESO if k == 0 else TINTA)); cr.fill_preserve()
        cr.set_source_rgb(*(TINTA if k == 0 else ROJO)); cr.set_line_width(8); cr.stroke()
        if k == 0:
            texto(cr, s, W / 2, y + bob, z, TINTA, centro=True, borde=0)
        else:
            gl = 14 * (0.35 + 0.65 * abs(math.sin(t * 9))) * (1.0 if (int(t * 6) % 5 == 0) else 0.3)
            font(cr, z)
            for (dx, colr) in ((-gl, (0.2, 0.9, 1.0)), (gl, MENTA)):
                cr.move_to(x0 + dx, y + bob); cr.text_path(s); cr.set_source_rgba(*colr, 0.55); cr.fill()
            cr.move_to(x0, y + bob); cr.text_path(s); cr.set_source_rgb(*ROJO); cr.fill()


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: acercamiento lento (push-in) en cada toma + sacudida corta en los golpes (antes: inclinación vertical)
    d = max(0, t - L[i]["t0"]) if i else t
    z = 1.0 + 0.07 * ease(d / 5.0)
    sx = sy = 0.0
    if i == 2:
        u = local(2, t)
        for g in (0.12, 0.38, 0.64):
            dd = u - g
            if 0 <= dd < 0.08:
                sx += 16 * math.sin(t * 90) * (1 - dd / 0.08); sy += 10 * math.cos(t * 77) * (1 - dd / 0.08)
    cr.save()
    cr.rectangle(0, 850, W, 450); cr.rectangle(320, 1300, W - 320, 360); cr.rectangle(0, 1660, W, 40); cr.clip()
    cr.translate(sx, sy); cr.translate(690, 1200); cr.scale(z, z); cr.translate(-690, -1200)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0 or t > L[-1]["t1"] - 0.35:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1570, col if col else AMAR, 40)
    chipb(cr, "El juego te ayuda en secreto", 340, 1745, MENTA, 34)
    cr.set_source_rgba(0, 0, 0, 0.25); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*ROJO); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        dd = t - x["t0"]
        if 0 <= dd < 0.1:
            cr.set_source_rgba(1, 1, 1, 0.30 * (1 - dd / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0, 1.5] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [5.0, 8.9, 10.0, 13.0, 15.0, 17.5, 20.0, 22.0, 24.0, 25.6, round(L[-1]["t1"] - 0.2, 1)]
        for t in sorted(set(ts)):
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
