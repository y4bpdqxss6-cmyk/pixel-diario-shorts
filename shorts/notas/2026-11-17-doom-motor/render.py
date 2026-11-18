"""Motor de respaldo Pixel Diario — Short 'Doom te miente con tu barra de vida'.
Dibuja con cairo, sin personajes, logos ni diseños reconocibles: barra de vida genérica, figura geométrica con
casco genérico (círculo + visera), proyectiles como bolitas de luz. "Doom" y "Assassin's Creed" solo como texto.
Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["TU VIDA", "MIENTE"], "resalta": "MIENTE"}

# paleta nueva: HUD nocturno, carbón azulado + rojo neón + cian (antes: cuaderno papel crema + tinta)
FONDO1 = (0.06, 0.07, 0.12)
FONDO2 = (0.16, 0.08, 0.12)
REJILLA = (0.25, 0.85, 0.95)
ROJO = (1.0, 0.18, 0.25)
CIAN = (0.2, 0.9, 1.0)
AMBAR = (1.0, 0.75, 0.15)
VERDE = (0.35, 1.0, 0.5)
GRIS = (0.55, 0.58, 0.66)
BLANCO = (1, 1, 1)
OSCURO = (0.02, 0.03, 0.06)

RESALTA = {1: ["2017,", "diseñadores", "Twitter."], 2: ["parejo…", "final."], 3: ["Pero", "último", "pedacito", "más", "golpes"],
           4: ["Doom:", "Assassin's", "Creed", "mismo."], 5: ["¿Por", "qué?"], 6: ["heroico,", "pelo."],
           7: ["pelito", "Doom", "vivo."]}
COLRES = {1: CIAN, 2: ROJO, 3: ROJO, 4: AMBAR, 5: AMBAR, 6: VERDE, 7: ROJO}
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
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: marco de HUD oscuro con
    esquinas en escuadra de color (antes: nota adhesiva con cinta)."""
    x = max(x, 340)
    font(cr, size); w = cr.text_extents(s).x_advance + 60; h = size + 34
    rrect(cr, x, y, w, h, 6); cr.set_source_rgba(*OSCURO, 0.85); cr.fill()
    cr.set_source_rgb(*color); cr.set_line_width(5)
    c = 22
    for (px, py, dx, dy) in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
        cr.move_to(px + dx * c, py); cr.line_to(px, py); cr.line_to(px, py + dy * c); cr.stroke()
    cr.set_source_rgb(*color); cr.move_to(x + 30, y + size + 10); cr.show_text(s)


# ---------- dibujos genéricos ----------
def barra(cr, x, y, w, h, frac, t, tiembla=0.0, brillo_final=0.0, segmentos=4):
    """barra de vida genérica. frac 0..1"""
    dx = tiembla * math.sin(t * 60) * 8
    cr.save(); cr.translate(dx, 0)
    rrect(cr, x - 10, y - 10, w + 20, h + 20, 14); cr.set_source_rgba(*OSCURO, 0.9); cr.fill()
    rrect(cr, x - 10, y - 10, w + 20, h + 20, 14); cr.set_source_rgb(*GRIS); cr.set_line_width(5); cr.stroke()
    fw = max(0, w * frac)
    if fw > 0:
        g = cairo.LinearGradient(0, y, 0, y + h); g.add_color_stop_rgb(0, 1, 0.45, 0.45); g.add_color_stop_rgb(1, *ROJO)
        rrect(cr, x, y, max(fw, 12), h, 8); cr.set_source(g); cr.fill()
    if brillo_final > 0:
        a = brillo_final * (0.6 + 0.4 * math.sin(t * 10))
        rrect(cr, x - 4, y - 4, max(fw, 12) + 8, h + 8, 10); cr.set_source_rgba(*AMBAR, a); cr.set_line_width(7); cr.stroke()
    cr.set_source_rgba(*OSCURO, 0.7); cr.set_line_width(4)
    for k in range(1, segmentos):
        cr.move_to(x + w * k / segmentos, y); cr.line_to(x + w * k / segmentos, y + h); cr.stroke()
    # icono de corazón genérico a la izquierda
    cr.save(); cr.translate(x - 60, y + h / 2); s = h / 60
    cr.scale(s, s)
    cr.move_to(0, 18); cr.curve_to(-40, -10, -20, -38, 0, -18); cr.curve_to(20, -38, 40, -10, 0, 18)
    cr.set_source_rgb(*ROJO); cr.fill(); cr.restore()
    cr.restore()


def figura(cr, x, y, esc=1.0, t=0.0, a=1.0):
    """figura geométrica con casco genérico (círculo + visera). y = pies"""
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    cr.move_to(-70, 0); cr.line_to(70, 0); cr.line_to(50, -170); cr.line_to(-50, -170); cr.close_path()
    cr.set_source_rgba(0.35, 0.5, 0.42, a); cr.fill()
    cr.new_sub_path(); cr.arc(0, -230, 62, 0, 2 * math.pi); cr.set_source_rgba(0.45, 0.6, 0.5, a); cr.fill()
    rrect(cr, -45, -250, 90, 32, 10); cr.set_source_rgba(*CIAN, a * (0.7 + 0.3 * math.sin(t * 6))); cr.fill()
    cr.restore()


def bala(cr, x, y, r=18, a=1.0, col=ROJO):
    g = cairo.RadialGradient(x, y, 0, x, y, r * 2.2)
    g.add_color_stop_rgba(0, 1, 1, 1, a); g.add_color_stop_rgba(0.35, *col, a); g.add_color_stop_rgba(1, *col, 0)
    cr.set_source(g); cr.arc(x, y, r * 2.2, 0, 2 * math.pi); cr.fill()


def tarjeta(cr, s, x, y, size, color, esc=1.0, rot=0.0):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 60
    rrect(cr, -w / 2, -size * 0.95, w, size * 1.5, 14); cr.set_source_rgba(*OSCURO, 0.9); cr.fill()
    rrect(cr, -w / 2, -size * 0.95, w, size * 1.5, 14); cr.set_source_rgb(*color); cr.set_line_width(5); cr.stroke()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 30, size * 0.25); cr.show_text(s)
    cr.restore()


def globo(cr, x, y, w, a, col):
    if a <= 0.01: return
    cr.save(); cr.translate(x, y); cr.scale(lerp(0.6, 1, a), lerp(0.6, 1, a))
    rrect(cr, 0, 0, w, 110, 26); cr.set_source_rgba(0.14, 0.17, 0.26, a); cr.fill()
    cr.move_to(30, 110); cr.line_to(20, 140); cr.line_to(70, 110); cr.close_path(); cr.fill()
    cr.new_sub_path(); cr.arc(50, 55, 28, 0, 2 * math.pi); cr.set_source_rgba(*col, a); cr.fill()
    cr.set_source_rgba(*BLANCO, 0.75 * a)
    rrect(cr, 100, 30, w - 140, 16, 8); cr.fill(); rrect(cr, 100, 62, (w - 140) * 0.6, 16, 8); cr.fill()
    cr.restore()


def escena_a(cr, t, i):
    """imagen del inicio y del cierre: barra casi vacía temblando + figura esquivando bolitas de luz.
    Nada en y 300–820 (el texto del gancho va encima)."""
    barra(cr, 420, 900, 560, 70, 0.07, t, tiembla=1.0, brillo_final=0.4)
    sway = 120 * math.sin(t * 2.6)
    figura(cr, 660 + sway, 1380, 1.0, t)
    for k in range(6):
        ph = (t * 1.3 + k / 6) % 1
        y = lerp(1000, 1400, (k * 0.37) % 1)
        x = lerp(1120, 300, ph)
        if 330 < x < 1080: bala(cr, x, y - 30, 16)
    texto(cr, "¡CASI 0!", 700, 1060, 54, ROJO, borde=8)


def escena(cr, t):
    i = linea_en(t)
    if i == 0 or i == 7:
        escena_a(cr, t, i)
        return ("DOOM", ROJO) if i == 0 else ("Doom te dejó vivo", ROJO)
    if i == 1:
        u = local(1, t)
        tarjeta(cr, "2017", 680, 930, 110 + 6 * math.sin(t * 5), CIAN, esc=ease(u * 5), rot=-0.03)
        globo(cr, 380, 1050, 560, ease((u - 0.2) * 4), CIAN)
        globo(cr, 440, 1210, 520, ease((u - 0.4) * 4), AMBAR)
        globo(cr, 360, 1370, 580, ease((u - 0.6) * 4), VERDE)
        return "hilo de diseñadores", CIAN
    if i == 2:
        u = local(2, t)
        golpes = min(3, int(u * 4.2))
        frac = 1 - 0.25 * golpes
        barra(cr, 420, 1000, 560, 80, frac, t)
        lab = ["100", "75", "50", "25"][golpes]
        texto(cr, lab, 700, 1250, 150, BLANCO, borde=12)
        d = (u * 4.2) % 1
        if d < 0.25 and golpes > 0 and u * 4.2 < 3.4:
            bala(cr, lerp(1000, 700, d * 4), 1040, 26)
        figura(cr, 840, 1430, 0.55, t)
        return "baja parejo", BLANCO
    if i == 3:
        u = local(3, t)
        z = lerp(1.0, 2.0, ease(u * 2))
        cr.save(); cr.translate(470, 1060); cr.scale(z, z); cr.translate(-470, -1060)
        barra(cr, 420, 1020, 560, 80, 0.25, t, brillo_final=ease(u * 3))
        cr.restore()
        hits = min(4, int(u * 5))
        for k in range(hits):
            d = (u * 5 - k)
            if d < 0.6:
                bx = lerp(1050, 760, min(1, d * 3)); by = 1060 + (0 if d < 0.33 else -400 * (d - 0.33))
                bala(cr, bx, by, 24)
        if hits:
            texto(cr, f"×{hits}", 760, 1330, 140 + 10 * math.sin(t * 9), AMBAR, borde=12)
        return "el último pedacito", AMBAR
    if i == 4:
        u = local(4, t)
        for k, (nom, col) in enumerate((("DOOM", ROJO), ("ASSASSIN'S CREED", AMBAR))):
            y0 = 960 + k * 300
            a = ease((u - k * 0.3) * 4)
            if a <= 0: continue
            cr.save(); cr.translate(660, y0 + 60); cr.scale(a, a); cr.translate(-660, -(y0 + 60))
            tarjeta(cr, nom, 680, y0, 62, col)
            barra(cr, 450, y0 + 70, 460, 60, 0.1, t, brillo_final=1)
            cr.restore()
        if u > 0.65:
            texto(cr, "=", 680, 1210, 120, BLANCO, borde=10, alpha=ease((u - 0.65) * 5))
        return "los dos lo hacen", AMBAR
    if i == 5:
        u = local(5, t)
        texto(cr, "¿?", 680, 1300, 260 + 80 * ease(u * 2) + 10 * math.sin(t * 8), AMBAR, borde=14)
        return "¿por qué?", AMBAR
    if i == 6:
        u = local(6, t)
        # cambio visual más fuerte: cámara lenta, la figura sale de una nube de bolitas; destello verde
        cr.rectangle(-1000, -1000, W + 2000, H + 2000); cr.set_source_rgba(*VERDE, 0.14 * ease(u * 3)); cr.fill()
        rnd = random.Random(7)
        for k in range(22):
            ang = rnd.uniform(0, 2 * math.pi); r0 = rnd.uniform(60, 300)
            r = r0 + 120 * u
            bala(cr, 640 + r * math.cos(ang + u * 0.3), 1160 + r * 0.8 * math.sin(ang + u * 0.3), 15, a=1 - 0.6 * u)
        fx = lerp(640, 820, ease((u - 0.3) * 2)); figura(cr, fx, 1400, 0.9, t)
        barra(cr, 420, 880, 560, 60, 0.04, t, brillo_final=1)
        if u > 0.5:
            e = ease((u - 0.5) * 4)
            cr.save(); cr.translate(660, 1540); cr.rotate(-0.06); cr.scale(e, e)
            texto(cr, "¡POR UN PELO!", 0, 0, 92, VERDE, borde=12); cr.restore()
        return None, None
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *FONDO1); g.add_color_stop_rgb(1, *FONDO2)
    cr.set_source(g); cr.paint()
    # suelo en perspectiva que avanza + líneas de escaneo (antes: cuadrícula de papel + migas)
    hz = 1450
    cr.set_source_rgba(*REJILLA, 0.22); cr.set_line_width(2)
    for k in range(-12, 13):
        cr.move_to(W / 2 + k * 40, hz); cr.line_to(W / 2 + k * 260, H); cr.stroke()
    off = (t * 0.9) % 1
    for k in range(10):
        p = ((k + off) / 10) ** 2
        y = hz + p * (H - hz)
        cr.move_to(0, y); cr.line_to(W, y); cr.stroke()
    cr.set_source_rgba(0, 0, 0, 0.12)
    for y in range(0, H, 6): cr.rectangle(0, y, W, 2)
    cr.fill()
    rnd = random.Random(5)
    for k in range(30):
        x0 = rnd.uniform(0, W); sp = rnd.uniform(30, 90)
        y = (rnd.uniform(0, H) - t * sp) % H
        cr.set_source_rgba(*ROJO, 0.35); cr.arc(x0, y, rnd.uniform(2, 5), 0, 2 * math.pi); cr.fill()


def gancho(cr, t):
    # entrada nueva: cada línea cae desde arriba y golpea con un temblor (antes: entraba de lado girando como sello);
    # en el cuadro 0 ya está casi en su sitio y legible
    ys = [570, 800]; sizes = [150, 190]
    for k, (s, y, z) in enumerate(zip(GANCHO["lineas"], ys, sizes)):
        u = max(0, min(1, 0.9 + (t - k * 0.06) / 0.4))
        dy = -(1 - ease(u)) * 220
        shake = 10 * math.sin(t * 70) * max(0, 1 - abs(t - (0.09 + k * 0.1)) * 5)
        col = ROJO if s == GANCHO["resalta"] else BLANCO
        cr.save(); cr.translate(W / 2 + shake, y + dy)
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
    # cámara nueva: deriva lateral lenta + empuje al cambiar de escena + temblor en los golpes
    # (antes: acercamiento lento por escena + leve giro)
    u = local(i, t)
    zc = 1.0 + 0.06 * (1 - ease(u * 3))
    dx = 18 * math.sin(t * 0.7)
    sh = 0.0
    if i == 0 or i == 7: sh = 3
    if i in (2, 3): sh = 9 * max(0, 1 - ((u * (4.2 if i == 2 else 5)) % 1) * 4)
    cr.save(); cr.translate(660 + dx + sh * math.sin(t * 63), 1150 + sh * math.cos(t * 51)); cr.scale(zc, zc); cr.translate(-660, -1150)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0 and t < L[0]["t1"] + 0.1:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1480, col, 40)
    chipb(cr, "El juego te ayuda en secreto", 360, 1740, CIAN, 34)
    cr.set_source_rgba(0, 0, 0, 0.15); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*CIAN); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
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
