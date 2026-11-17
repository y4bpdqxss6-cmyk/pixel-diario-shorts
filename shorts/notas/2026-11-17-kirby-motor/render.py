"""Motor de respaldo Pixel Diario — Short 'Kirby iba a ser un dibujo temporal'.
Dibuja con cairo, sin personajes, logos ni diseños reconocibles: solo un círculo GRIS SIN CARA con etiqueta
"TEMP" (nada de bola rosa, ojos, mejillas ni pies). "Kirby", "Nintendo", "HAL" solo como texto simple.
Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["ERA SOLO", "RELLENO"], "resalta": "RELLENO"}

# paleta nueva: cuaderno de dibujo, papel crema + tinta + lápiz rojo y verde azulado
# (antes: amanecer de montaña azul petróleo + durazno)
PAPEL1 = (0.96, 0.93, 0.85)
PAPEL2 = (0.86, 0.78, 0.64)
RAYA = (0.55, 0.7, 0.85)
TINTA = (0.12, 0.14, 0.22)
ROJO = (0.9, 0.22, 0.2)
VERDE = (0.05, 0.6, 0.55)
AMBAR = (1.0, 0.72, 0.15)
GRIS = (0.62, 0.64, 0.68)
BLANCO = (1, 1, 1)
OSCURO = (0.02, 0.03, 0.06)

RESALTA = {1: ["1990,", "diecinueve", "HAL."], 2: ["protagonista", "listo."], 3: ["más", "fácil", "bolita."],
           4: ["Kirby:", "Popopo."], 5: ["Pero", "raro."], 6: ["¿Por", "qué", "cambiaron?"],
           7: ["mejor", "cualquier", "diseño."], 8: ["famosos", "relleno."]}
COLRES = {1: AMBAR, 2: ROJO, 3: VERDE, 4: AMBAR, 5: ROJO, 6: AMBAR, 7: VERDE, 8: AMBAR}


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
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: nota adhesiva de color
    ligeramente girada con cinta encima (antes: etiqueta blanca con barra de color)."""
    x = max(x, 340)
    font(cr, size); w = cr.text_extents(s).x_advance + 56; h = size + 34
    cr.save(); cr.translate(x, y); cr.rotate(-0.02)
    cr.rectangle(6, 8, w, h); cr.set_source_rgba(0, 0, 0, 0.25); cr.fill()
    cr.rectangle(0, 0, w, h); cr.set_source_rgb(*color); cr.fill()
    cr.rectangle(w / 2 - 50, -14, 100, 28); cr.set_source_rgba(1, 1, 1, 0.6); cr.fill()
    cr.set_source_rgb(*OSCURO); cr.move_to(28, size + 10); cr.show_text(s)
    cr.restore()


# ---------- dibujos genéricos ----------
def bolita(cr, x, y, r, t=0.0, etiqueta="TEMP", squash=0.0, a=1.0):
    """círculo gris sin cara (marcador temporal). y = centro"""
    cr.save(); cr.translate(x, y); cr.scale(1 + squash, 1 - squash)
    cr.new_sub_path(); cr.arc(6, 10, r, 0, 2 * math.pi); cr.set_source_rgba(0, 0, 0, 0.18 * a); cr.fill()
    cr.new_sub_path(); cr.arc(0, 0, r, 0, 2 * math.pi); cr.set_source_rgba(*GRIS, a); cr.fill_preserve()
    cr.set_source_rgba(*TINTA, a); cr.set_line_width(7); cr.set_dash([22, 14]); cr.stroke(); cr.set_dash([])
    cr.restore()
    if etiqueta:
        cr.save(); cr.translate(x + r * 0.55, y - r * 0.75); cr.rotate(0.18)
        font(cr, 40); w = cr.text_extents(etiqueta).x_advance + 36
        cr.rectangle(-w / 2, -32, w, 52); cr.set_source_rgba(*AMBAR, a); cr.fill()
        cr.set_source_rgba(*OSCURO, a); cr.move_to(-w / 2 + 18, 8); cr.show_text(etiqueta)
        cr.restore()


def regla(cr, y0, y1):
    cr.set_source_rgba(*TINTA, 0.35); cr.set_line_width(3)
    cr.move_to(330, y1); cr.line_to(1010, y1); cr.stroke()


def silueta(cr, x, y, esc, a=1.0):
    """silueta vacía punteada genérica (cabeza + cuerpo), y = pies"""
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    cr.set_source_rgba(*TINTA, a); cr.set_line_width(8); cr.set_dash([20, 14])
    cr.new_sub_path(); cr.arc(0, -330, 70, 0, 2 * math.pi); cr.stroke()
    rrect(cr, -95, -250, 190, 250, 50); cr.stroke(); cr.set_dash([])
    cr.restore()


def lapiz(cr, x, y, ang):
    cr.save(); cr.translate(x, y); cr.rotate(ang)
    cr.move_to(0, 0); cr.line_to(-22, -50); cr.line_to(22, -50); cr.close_path(); cr.set_source_rgb(0.95, 0.8, 0.6); cr.fill()
    cr.move_to(0, 0); cr.line_to(-7, -16); cr.line_to(7, -16); cr.close_path(); cr.set_source_rgb(*TINTA); cr.fill()
    cr.rectangle(-22, -250, 44, 200); cr.set_source_rgb(*AMBAR); cr.fill()
    cr.rectangle(-22, -290, 44, 40); cr.set_source_rgb(*ROJO); cr.fill()
    cr.restore()


def escritorio(cr, u, t):
    cr.rectangle(330, 1180, 690, 40); cr.set_source_rgb(0.55, 0.38, 0.24); cr.fill()
    cr.rectangle(370, 1220, 30, 200); cr.rectangle(950, 1220, 30, 200); cr.fill()
    # monitor genérico de los 90
    rrect(cr, 600, 900, 330, 260, 18); cr.set_source_rgb(0.85, 0.83, 0.76); cr.fill()
    rrect(cr, 630, 925, 270, 190, 10); cr.set_source_rgb(0.1, 0.25, 0.2); cr.fill()
    cr.set_source_rgb(0.4, 1, 0.6)
    for k in range(4):
        w = 60 + 140 * ((k * 37 + int(t * 6)) % 5) / 5
        cr.rectangle(650, 950 + k * 36, w, 14); cr.fill()
    cr.rectangle(730, 1160, 70, 20); cr.set_source_rgb(0.75, 0.73, 0.66); cr.fill()


def vela(cr, x, y, t, a):
    if a <= 0.01: return
    rrect(cr, x - 70, y, 140, 90, 14); cr.set_source_rgba(*BLANCO, a); cr.fill()
    cr.set_source_rgba(*ROJO, a); cr.set_line_width(6); rrect(cr, x - 70, y, 140, 90, 14); cr.stroke()
    texto(cr, "19", x, y - 20, 110, VERDE, borde=8, alpha=a)
    fl = 1 + 0.15 * math.sin(t * 20)
    cr.save(); cr.translate(x, y - 140); cr.scale(1, fl)
    cr.new_sub_path(); cr.arc(0, 0, 18, 0, 2 * math.pi); cr.set_source_rgba(*AMBAR, a); cr.fill(); cr.restore()


def tarjeta(cr, s, x, y, size, color, esc=1.0, rot=0.0):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 60
    rrect(cr, -w / 2, -size * 0.95, w, size * 1.5, 14); cr.set_source_rgb(*TINTA); cr.fill()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 30, size * 0.25); cr.show_text(s)
    cr.restore()


def diseno_final(cr, x, y, sep, a):
    """diseño 'final' genérico inventado lleno de detalles; sep separa las piezas (se desarma)"""
    if a <= 0.01: return
    # capa
    cr.save(); cr.translate(x - sep * 1.2, y + sep * 0.6); cr.rotate(-sep / 400)
    cr.move_to(-150, -60); cr.line_to(150, -60); cr.line_to(200, 220); cr.line_to(-200, 220); cr.close_path()
    cr.set_source_rgba(0.45, 0.2, 0.55, a); cr.fill(); cr.restore()
    # armadura
    cr.save(); cr.translate(x + sep, y + sep * 0.3); cr.rotate(sep / 300)
    rrect(cr, -110, -40, 220, 200, 30); cr.set_source_rgba(0.5, 0.55, 0.62, a); cr.fill()
    cr.set_source_rgba(*AMBAR, a); cr.rectangle(-15, -40, 30, 200); cr.fill(); cr.restore()
    # casco con cuernos
    cr.save(); cr.translate(x - sep * 0.4, y - 150 - sep * 1.3); cr.rotate(-sep / 250)
    cr.new_sub_path(); cr.arc(0, 0, 90, 0, 2 * math.pi); cr.set_source_rgba(0.3, 0.32, 0.4, a); cr.fill()
    for s in (-1, 1):
        cr.move_to(s * 60, -50); cr.line_to(s * 150, -170); cr.line_to(s * 90, -20); cr.close_path()
        cr.set_source_rgba(*BLANCO, a); cr.fill()
    cr.restore()
    # espada
    cr.save(); cr.translate(x + 220 + sep * 1.4, y - sep * 0.8); cr.rotate(0.3 + sep / 200)
    cr.rectangle(-12, -260, 24, 260); cr.set_source_rgba(0.85, 0.88, 0.92, a); cr.fill()
    cr.rectangle(-50, 0, 100, 20); cr.set_source_rgba(*AMBAR, a); cr.fill(); cr.restore()


def sello(cr, x, y, s, u):
    if u <= 0: return
    esc = 1.8 - 0.8 * ease(u * 2.5)
    cr.save(); cr.translate(x, y); cr.rotate(-0.18); cr.scale(esc, esc)
    font(cr, 86); w = cr.text_extents(s).x_advance + 60
    a = ease(u * 4)
    rrect(cr, -w / 2, -80, w, 120, 14); cr.set_source_rgba(*VERDE, a); cr.set_line_width(10); cr.stroke()
    cr.set_source_rgba(*VERDE, a); cr.move_to(-w / 2 + 30, 10); cr.show_text(s)
    cr.restore()


def escena_a(cr, t, i):
    """imagen del inicio y del cierre: círculo gris 'TEMP' rebotando en la cuadrícula. Nada en y 300–820."""
    per = 0.9; u = (t % per) / per
    h = abs(math.sin(math.pi * u))
    y = 1230 - 300 * h
    sq = 0.14 * max(0, 1 - h * 5)
    regla(cr, 0, 1360)
    cr.new_sub_path(); cr.save(); cr.translate(660, 1362); cr.scale(1, 0.18)
    cr.arc(0, 0, 130 * (1 - 0.4 * h), 0, 2 * math.pi); cr.restore(); cr.set_source_rgba(0, 0, 0, 0.2); cr.fill()
    bolita(cr, 660, y, 130, t, "TEMP", squash=sq)
    # marcas de cota del diseñador
    cr.set_source_rgba(*ROJO, 0.9); cr.set_line_width(4)
    cr.move_to(460, 1100); cr.line_to(460, 1360); cr.stroke()
    texto(cr, "BORRADOR", 460, 1080, 38, ROJO, borde=0)


def escena(cr, t):
    i = linea_en(t)
    if i == 0 or i == 8:
        escena_a(cr, t, i)
        return ("Kirby · HAL · 1990", AMBAR) if i == 0 else ("sigue siendo relleno", AMBAR)
    if i == 1:
        u = local(1, t)
        escritorio(cr, u, t)
        tarjeta(cr, "1990 · HAL", 560 if u < 0.5 else lerp(560, 470, ease((u - 0.5) * 4)), 820 if u < 0.5 else 800,
                70, AMBAR, esc=ease(u * 5), rot=-0.04)
        vela(cr, 450, 1060, t, ease((u - 0.45) * 5))
        return "Masahiro Sakurai", VERDE
    if i == 2:
        u = local(2, t)
        regla(cr, 0, 1360)
        silueta(cr, 560, 1360, 1.0 + 0.03 * math.sin(t * 3), 1)
        a = ease((u - 0.2) * 4)
        cr.save(); cr.translate(840, 950); cr.rotate(0.06 * math.sin(t * 4))
        rrect(cr, -150, -80, 300, 170, 12); cr.set_source_rgba(*BLANCO, a); cr.fill()
        texto(cr, "PROTA:", 0, -10, 52, TINTA, borde=0, alpha=a)
        texto(cr, "PENDIENTE", 0, 60, 52, ROJO, borde=0, alpha=a)
        cr.restore()
        return "protagonista: pendiente", ROJO
    if i == 3:
        u = local(3, t)
        regla(cr, 0, 1360)
        silueta(cr, 560, 1360, 1.0, 0.35)
        p = ease(u * 1.6)
        cx, cy, r = 560, 1180, 130
        cr.set_source_rgb(*TINTA); cr.set_line_width(9)
        cr.new_sub_path(); cr.arc(cx, cy, r, -math.pi / 2, -math.pi / 2 + 2 * math.pi * p); cr.stroke()
        ang = -math.pi / 2 + 2 * math.pi * p
        lapiz(cr, cx + r * math.cos(ang), cy + r * math.sin(ang), 0.5)
        if p >= 1:
            bolita(cr, cx, cy, r, t, None, a=ease((u - 0.62) * 4))
            texto(cr, "1 trazo", 860, 1000, 60, VERDE, borde=8)
        return "lo más fácil", VERDE
    if i == 4:
        u = local(4, t)
        regla(cr, 0, 1360)
        bolita(cr, 560, 1180, 130, t, None)
        texto(cr, "KIRBY", 760, 930, 80, BLANCO, borde=10)
        if u > 0.25:
            cr.set_source_rgb(*ROJO); cr.set_line_width(12)
            cr.move_to(640, 905); cr.line_to(lerp(640, 880, ease((u - 0.25) * 5)), 905); cr.stroke()
        if u > 0.5:
            e = ease((u - 0.5) * 4)
            cr.save(); cr.translate(820, 1100); cr.rotate(0.1); cr.scale(e, e)
            font(cr, 60); w = cr.text_extents("POPOPO").x_advance + 50
            cr.rectangle(-w / 2, -55, w, 90); cr.set_source_rgb(*AMBAR); cr.fill()
            cr.set_source_rgb(*OSCURO); cr.move_to(-w / 2 + 25, 15); cr.show_text("POPOPO")
            cr.restore()
        return "su nombre: Popopo", AMBAR
    if i == 5:
        u = local(5, t)
        regla(cr, 0, 1360)
        bolita(cr, 560, 1180, 130, t, "POPOPO", squash=0.05 * math.sin(t * 12))
        texto(cr, "¿?", 820, 1000, 160 + 60 * ease(u * 2) + 10 * math.sin(t * 8), ROJO, borde=12)
        return "algo raro", ROJO
    if i == 6:
        u = local(6, t)
        regla(cr, 0, 1360)
        diseno_final(cr, 640, 1050, 0, ease(u * 4))
        bolita(cr, 400, 1250, 80, t, None)
        tarjeta(cr, "DISEÑO FINAL", 640, 1440 - 140, 48, AMBAR, esc=ease((u - 0.3) * 4), rot=0.03)
        return "el diseño de verdad", AMBAR
    if i == 7:
        u = local(7, t)
        # cambio visual más fuerte: el papel se ilumina en verde, el diseño se desarma y la bolita gana
        cr.rectangle(-1000, -1000, W + 2000, H + 2000); cr.set_source_rgba(*VERDE, 0.18 * ease(u * 3)); cr.fill()
        regla(cr, 0, 1360)
        sep = 600 * ease(u * 1.8)
        diseno_final(cr, 640, 1050, sep, 1 - ease(u * 3.5))
        bx = lerp(400, 640, ease((u - 0.25) * 3)); br = lerp(80, 140, ease((u - 0.25) * 3))
        bolita(cr, bx, 1360 - br - 20, br, t, None)
        sello(cr, 760, 980, "APROBADO", (u - 0.5) * 1.6)
        return "la bolita gana", VERDE
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *PAPEL1); g.add_color_stop_rgb(1, *PAPEL2)
    cr.set_source(g); cr.paint()
    # cuadrícula de papel que se desliza despacio + migas de goma de borrar (antes: montañas en paralaje + nieve)
    off = (t * 18) % 60
    cr.set_source_rgba(*RAYA, 0.35); cr.set_line_width(2)
    for k in range(-1, 20):
        x = k * 60 + off; cr.move_to(x, 0); cr.line_to(x, H)
    for k in range(-1, 34):
        y = k * 60 + off * 0.5; cr.move_to(0, y); cr.line_to(W, y)
    cr.stroke()
    cr.set_source_rgba(*ROJO, 0.35); cr.set_line_width(4); cr.move_to(120, 0); cr.line_to(120, H); cr.stroke()
    rnd = random.Random(5)
    for k in range(25):
        x0 = rnd.uniform(0, W); sp = rnd.uniform(20, 60)
        y = (rnd.uniform(0, H) - t * sp) % H
        cr.save(); cr.translate(x0 + 15 * math.sin(t + k), y); cr.rotate(t * 0.5 + k)
        cr.rectangle(-5, -3, 10, 6); cr.set_source_rgba(0.85, 0.5, 0.55, 0.45); cr.fill(); cr.restore()
    # oscurecer arriba para que subtítulos y gancho tengan contraste
    g2 = cairo.LinearGradient(0, 200, 0, 900)
    g2.add_color_stop_rgba(0, *TINTA, 0.0); g2.add_color_stop_rgba(0.5, *TINTA, 0.10); g2.add_color_stop_rgba(1, *TINTA, 0.0)
    cr.set_source(g2); cr.paint()


def gancho(cr, t):
    # entrada nueva: cada línea entra de lado como un sello que se asienta con giro (antes: aparecía grande y se encogía);
    # en el cuadro 0 ya está casi en su sitio y legible
    ys = [600, 790]; sizes = [140, 170]
    for k, (s, y, z) in enumerate(zip(GANCHO["lineas"], ys, sizes)):
        u = max(0, min(1, 0.85 + (t - k * 0.08) / 0.5))
        dx = (1 - ease(u)) * (-160 if k == 0 else 160)
        rot = (1 - ease(u)) * (-0.12 if k == 0 else 0.12) + (0.0 if k == 0 else -0.03)
        col = AMBAR if s == GANCHO["resalta"] else BLANCO
        cr.save(); cr.translate(W / 2 + dx, y); cr.rotate(rot)
        texto(cr, s, 0, 0, z, col, borde=24)
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
            if acc > vis: col = (0.78, 0.78, 0.8)
            font(cr, size); adv = cr.text_extents(p + " ").x_advance
            cr.move_to(x, y); cr.text_path(p)
            cr.set_source_rgba(*OSCURO, 1); cr.set_line_width(11); cr.set_line_join(cairo.LINE_JOIN_ROUND); cr.stroke_preserve()
            cr.set_source_rgba(*col, 1); cr.fill()
            x += adv
        y += 90


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: acercamiento lento continuo por escena + leve giro (antes: deriva vertical + vaivén lateral)
    u = local(i, t)
    zc = 1.0 + 0.07 * u
    rot = 0.012 * math.sin(t * 0.8)
    cr.save(); cr.translate(660, 1150); cr.rotate(rot); cr.scale(zc, zc); cr.translate(-660, -1150)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0 and t < L[0]["t1"] + 0.1:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1480, col, 40)
    chipb(cr, "Iba a ser otra cosa", 360, 1740, BLANCO, 28)
    cr.set_source_rgba(0, 0, 0, 0.15); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*ROJO); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        d = t - x["t0"]
        if 0 <= d < 0.1:
            cr.set_source_rgba(1, 1, 1, 0.14 * (1 - d / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [round(L[-1]["t1"] - 0.3, 1), round(L[7]["t1"] - 0.5, 1)]
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
