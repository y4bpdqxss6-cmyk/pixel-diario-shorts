"""Motor de respaldo Pixel Diario — Short 'Max Payne te ayuda si juegas mal'.
Dibuja con cairo, sin personajes, caras, logos ni escenas reconocibles de Max Payne o Remedy: mira de tiro genérica,
siluetas rectangulares, botiquines con cruz, balanza, candado. Los nombres solo como texto.
Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["JUGAR MAL", "TE AYUDA"], "resalta": "AYUDA"}

# paleta nueva: noir de ciudad con lluvia, azul pizarra + ámbar de farol + hueso (antes: arcade morado + rojo neón + cian)
FONDO1 = (0.04, 0.06, 0.09)
FONDO2 = (0.13, 0.18, 0.25)
AMBAR = (1.0, 0.68, 0.16)
SOL = AMBAR
HUESO = (0.95, 0.92, 0.84)
ROJO = (0.90, 0.20, 0.18)
VERDE = (0.30, 0.82, 0.45)
VERDEO = (0.10, 0.50, 0.25)
AZUL = (0.38, 0.66, 0.95)
BLANCO = (1, 1, 1)
TINTA = (0.03, 0.04, 0.06)
GRIS = (0.50, 0.55, 0.62)
CIAN = AZUL
ROSA = (0.95, 0.45, 0.55)

RESALTA = {1: ["2001,", "Remedy,", "normal"], 2: ["caes,", "cambiar."], 3: ["Pero", "fallan", "menos."],
           4: ["más", "raro:", "contrario."], 5: ["¿Por", "qué?", "mide", "enemigos", "ayuda"], 6: ["fácil…", "peor"]}
COLRES = {1: AZUL, 2: ROJO, 3: AMBAR, 4: ROSA, 5: AMBAR, 6: AMBAR}

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
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: tira de cinta adhesiva inclinada
    con bordes dentados (antes: boleto de arcade con muescas)."""
    x = max(x, 340)
    font(cr, size); tw = cr.text_extents(s).x_advance; w = min(tw + 70, W - 20 - x); h = size + 30
    cr.save(); cr.translate(x + w / 2, y + h / 2); cr.rotate(-0.025)
    def forma(dx, dy):
        cr.new_path(); cr.move_to(-w / 2 + dx, -h / 2 + dy); cr.line_to(w / 2 + dx, -h / 2 + dy)
        for k in range(6): cr.line_to(w / 2 + dx + (10 if k % 2 == 0 else 0), -h / 2 + dy + h * (k + 1) / 6)
        cr.line_to(-w / 2 + dx, h / 2 + dy)
        for k in range(6): cr.line_to(-w / 2 + dx - (10 if k % 2 == 0 else 0), h / 2 + dy - h * (k + 1) / 6)
        cr.close_path()
    forma(5, 7); cr.set_source_rgba(0, 0, 0, 0.5); cr.fill()
    forma(0, 0); cr.set_source_rgba(*color, 0.96); cr.fill()
    cr.set_source_rgba(1, 1, 1, 0.18); cr.rectangle(-w / 2, -h / 2, w, h * 0.3); cr.fill()
    z = size
    while cr.text_extents(s).x_advance > w - 50: z -= 2; font(cr, z)
    cr.set_source_rgb(*txt); cr.move_to(-w / 2 + 35, z * 0.36); cr.show_text(s)
    cr.restore()


def mira(cr, x, y, r, col=ROJO, alfa=1.0):
    cr.save(); cr.translate(x, y)
    for lw, c in ((14, TINTA), (7, col)):
        cr.set_source_rgba(*c, alfa); cr.set_line_width(lw)
        cr.arc(0, 0, r, 0, 2 * math.pi); cr.stroke()
        cr.arc(0, 0, r * 0.45, 0, 2 * math.pi); cr.stroke()
        for a in range(4):
            ca, sa = math.cos(a * math.pi / 2), math.sin(a * math.pi / 2)
            cr.move_to(ca * r * 0.6, sa * r * 0.6); cr.line_to(ca * r * 1.3, sa * r * 1.3); cr.stroke()
    cr.arc(0, 0, 8, 0, 2 * math.pi); cr.set_source_rgba(*col, alfa); cr.fill()
    cr.restore()


def blanco_tiro(cr, x, y, r):
    for k, c in enumerate([HUESO, ROJO, HUESO, ROJO]):
        cr.arc(x, y, r * (1 - k * 0.24), 0, 2 * math.pi); cr.set_source_rgb(*c); cr.fill()
    cr.arc(x, y, r, 0, 2 * math.pi); cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()


def agujero(cr, x, y):
    cr.arc(x, y, 13, 0, 2 * math.pi); cr.set_source_rgb(*TINTA); cr.fill()
    cr.set_source_rgba(*HUESO, 0.7); cr.set_line_width(3)
    for k in range(5):
        a = k * 1.3
        cr.move_to(x + 15 * math.cos(a), y + 15 * math.sin(a)); cr.line_to(x + 30 * math.cos(a), y + 30 * math.sin(a))
    cr.stroke()


def barra(cr, x, y, w, h, frac, col, etq=None):
    cr.rectangle(x + 5, y + 7, w, h); cr.set_source_rgba(0, 0, 0, 0.45); cr.fill()
    cr.rectangle(x, y, w, h); cr.set_source_rgb(0.15, 0.17, 0.2); cr.fill()
    cr.rectangle(x, y, w * max(0, min(1, frac)), h); cr.set_source_rgb(*col); cr.fill()
    cr.rectangle(x, y, w, h); cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()
    if etq: texto(cr, etq, x, y - 18, 40, HUESO, centro=False, borde=8)


def enemigo(cr, x, y, esc=1.0, col=GRIS, vida=1.0):
    """silueta rectangular genérica con mira por cabeza. y = pies."""
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    cr.rectangle(-45 + 5, -230 + 7, 90, 230); cr.set_source_rgba(0, 0, 0, 0.4); cr.fill()
    rrect(cr, -45, -230, 90, 160, 14); cr.set_source_rgb(*col); cr.fill()
    cr.rectangle(-40, -75, 32, 75); cr.rectangle(8, -75, 32, 75); cr.fill()
    cr.arc(0, -270, 38, 0, 2 * math.pi); cr.fill()
    cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.arc(0, -270, 38, 0, 2 * math.pi); cr.stroke()
    cr.move_to(-26, -270); cr.line_to(26, -270); cr.move_to(0, -296); cr.line_to(0, -244); cr.set_source_rgb(*ROJO); cr.set_line_width(5); cr.stroke()
    cr.restore()
    barra(cr, x - 60 * esc, y - 340 * esc, 120 * esc, 18, vida, ROJO)


def botiquin(cr, x, y, esc=1.0, alfa=1.0):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    rrect(cr, -55 + 5, -45 + 7, 110, 90, 14); cr.set_source_rgba(0, 0, 0, 0.4 * alfa); cr.fill()
    rrect(cr, -55, -45, 110, 90, 14); cr.set_source_rgba(*HUESO, alfa); cr.fill_preserve(); cr.set_source_rgba(*TINTA, alfa); cr.set_line_width(5); cr.stroke()
    cr.rectangle(-12, -32, 24, 64); cr.rectangle(-32, -12, 64, 24); cr.set_source_rgba(*ROJO, alfa); cr.fill()
    cr.restore()


def engrane(cr, x, y, r, rot, col=GRIS):
    cr.save(); cr.translate(x, y); cr.rotate(rot)
    cr.new_path()
    for k in range(24):
        rr = r if (k // 2) % 2 == 0 else r * 0.8
        a = k * 2 * math.pi / 24
        cr.line_to(rr * math.cos(a), rr * math.sin(a))
    cr.close_path(); cr.set_source_rgb(*col); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(5); cr.stroke()
    cr.arc(0, 0, r * 0.32, 0, 2 * math.pi); cr.set_source_rgb(*FONDO1); cr.fill()
    cr.restore()


def balanza(cr, x, y, ang, esc=1.0):
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    cr.rectangle(-14, -40, 28, 330); cr.set_source_rgb(*AMBAR); cr.fill()
    cr.rectangle(-110, 280, 220, 30); cr.fill()
    cr.rotate(ang)
    cr.rectangle(-300, -52, 600, 24); cr.fill()
    for sx, et, col in ((-260, "TÚ", AZUL), (260, "EL JUEGO", ROJO)):
        cr.save(); cr.translate(sx, -40); cr.rotate(-ang)
        cr.move_to(0, 0); cr.line_to(-80, 150); cr.move_to(0, 0); cr.line_to(80, 150)
        cr.set_source_rgb(*HUESO); cr.set_line_width(4); cr.stroke()
        cr.save(); cr.translate(0, 150); cr.scale(1, 0.3); cr.arc(0, 0, 100, 0, math.pi); cr.restore()
        cr.set_source_rgb(*AMBAR); cr.fill()
        tarjeta(cr, et, 0, 115, 40, col, fondo=HUESO)
        cr.restore()
    cr.arc(0, -40, 26, 0, 2 * math.pi); cr.set_source_rgb(*HUESO); cr.fill()
    cr.restore()


def candado(cr, x, y, esc):
    if esc <= 0.01: return
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    cr.arc(0, -90, 75, math.pi, 2 * math.pi); cr.set_source_rgb(*GRIS); cr.set_line_width(30); cr.stroke()
    rrect(cr, -130 + 7, -90 + 9, 260, 200, 24); cr.set_source_rgba(0, 0, 0, 0.5); cr.fill()
    rrect(cr, -130, -90, 260, 200, 24); cr.set_source_rgb(*AMBAR); cr.fill_preserve(); cr.set_source_rgb(*TINTA); cr.set_line_width(7); cr.stroke()
    texto(cr, "SECRETO", 0, 30, 54, TINTA, borde=0)
    cr.restore()


def selector(cr, x, y, u):
    ops = ["FÁCIL", "NORMAL", "DIFÍCIL"]
    for k, s in enumerate(ops):
        e = back((u - 0.2 - k * 0.12) * 5)
        if e <= 0.01: continue
        yy = y + k * 130
        cr.save(); cr.translate(x, yy); cr.scale(e, e)
        sel = (k == 1)
        rrect(cr, -260, -55, 520, 100, 16); cr.set_source_rgb(*(AMBAR if sel else (0.16, 0.2, 0.26))); cr.fill_preserve()
        cr.set_source_rgb(*TINTA); cr.set_line_width(6); cr.stroke()
        texto(cr, s, 0, 18, 56, TINTA if sel else HUESO, borde=0)
        if sel and u > 0.6:
            texto(cr, "▶", -215, 18, 50, TINTA, borde=0)
        cr.restore()


def lluvia(cr, t, alfa=0.25):
    cr.set_source_rgba(0.7, 0.8, 0.95, alfa); cr.set_line_width(2.5)
    for k in range(70):
        x = (k * 157 + t * 260) % (W + 200) - 100
        y = (k * 263 + t * 1500) % (H + 200) - 100
        cr.move_to(x, y); cr.line_to(x - 14, y + 46)
    cr.stroke()


def escena_a(cr, t, i, intentos):
    """inicio y cierre: blanco de tiro, mira que tiembla y falla, contador de intentos. Nada en y 300–820."""
    blanco_tiro(cr, 690, 1130, 190)
    for k in range(min(6, int(t * 2.2) + 1)):
        agujero(cr, 690 + 260 * math.cos(k * 2.1 + 0.5), 1130 + 230 * math.sin(k * 2.1 + 0.5))
    mx = 690 + 120 * math.sin(t * 3.1) + 25 * math.sin(t * 17)
    my = 1130 + 90 * math.cos(t * 2.3) + 25 * math.cos(t * 19)
    mira(cr, mx, my, 120)
    tarjeta(cr, f"INTENTOS: {intentos}", 820, 1490, 46, ROJO, fondo=HUESO, rot=0.03)


def escena(cr, t):
    i = linea_en(t)
    if i in (0, 6):
        n = 3 + int(t * 1.6) if i == 0 else 9 + int((t - L[6]["t0"]) * 1.6)
        escena_a(cr, t, i, n)
        return ("Max Payne · 2001", AZUL) if i == 0 else ("¿jugabas mal?", AMBAR)
    u = local(i, t)
    if i == 1:
        tarjeta(cr, "2001 · REMEDY", 690, 930, 70, AZUL, esc=back(u * 4), rot=-0.03, fondo=HUESO)
        selector(cr, 690, 1100, u)
        return "modo normal", AMBAR
    if i == 2:
        v = 1 - ease(u / 0.35) if u < 0.55 else ease((u - 0.55) / 0.3)
        barra(cr, 390, 940, 600, 60, v, VERDE if v > 0.35 else ROJO, "VIDA")
        if 0.3 < u < 0.62:
            texto(cr, "OTRA VEZ", 690, 1180, 120 * back((u - 0.3) * 6) + 1, ROJO, borde=14)
        if u > 0.55:
            ee = back((u - 0.55) * 4)
            engrane(cr, 690, 1270, 150 * ee + 1, t * 2.5, AMBAR)
            engrane(cr, 900, 1150, 80 * ee + 1, -t * 4.5, GRIS)
        return "algo cambia", ROJO
    if i == 3:
        for k in range(3):
            x = 470 + k * 220; v = back((u - k * 0.1) * 4)
            vida = 1 - 0.6 * ease((u - 0.45) / 0.4)
            enemigo(cr, x, 1540, 0.95 * v + 0.01, GRIS, vida)
            # disparos que se desvían
            for j in range(2):
                p = ((t * 1.4 + k * 0.3 + j * 0.5) % 1.0)
                if u > 0.2:
                    sx = x + 50; sy = 1330
                    ex = sx + 300 * p; ey = sy - 380 * p * (1 + 0.8 * j)
                    cr.move_to(sx + (ex - sx) * 0.7, sy + (ey - sy) * 0.7); cr.line_to(ex, ey)
                    cr.set_source_rgba(*AMBAR, 1 - p); cr.set_line_width(8); cr.stroke()
        if u > 0.3:
            tarjeta(cr, "FALLAN", 820, 930, 54, AMBAR, esc=back((u - 0.3) * 4), rot=0.05, fondo=TINTA)
        return "enemigos más flojos", AMBAR
    if i == 4:
        # pantalla dividida: VAS MAL (botiquines) / VAS BIEN (más enemigos, se van los botiquines)
        cr.rectangle(340, 850, 690, 700); cr.set_source_rgba(0, 0, 0, 0.25); cr.fill()
        cr.move_to(685, 860); cr.line_to(685, 1550); cr.set_source_rgb(*HUESO); cr.set_line_width(6); cr.stroke()
        texto(cr, "VAS MAL", 512, 930, 50, AZUL, borde=8)
        texto(cr, "VAS BIEN", 858, 930, 50, ROJO, borde=8)
        for k in range(3):
            botiquin(cr, 512, 1060 + k * 150, back((u - k * 0.1) * 4))
        n_en = 1 + int(ease(u / 0.8) * 3)
        for k in range(n_en):
            enemigo(cr, 775 + (k % 2) * 165, 1250 + (k // 2) * 200, 0.55, GRIS, 1.0)
        a = 1 - ease((u - 0.3) / 0.4)
        botiquin(cr, 858, 1010, 0.6, a)
        return "pasa lo contrario", ROSA
    if i == 5:
        if u < 0.22:
            texto(cr, "¿?", 690, 1300, 320 * back(u * 6) + 1, AMBAR, borde=16)
            return "¿por qué?", AMBAR
        if u < 0.82:
            v = (u - 0.22) / 0.6
            ang = 0.35 * math.cos(v * 9) * math.exp(-v * 3.5)
            balanza(cr, 690, 1130, ang, back(v * 5) * 0.95 + 0.01)
            return ("mide cómo te va" if v < 0.5 else "ajusta lo que viene"), AMBAR
        balanza(cr, 690, 1130, 0, 0.95)
        candado(cr, 690, 1230, back((u - 0.82) * 6) * 1.2)
        return "y no te avisa", ROJO
    return None, None


def fondo(cr, t, i):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *FONDO1); g.add_color_stop_rgb(0.65, *FONDO2); g.add_color_stop_rgb(1, *FONDO1)
    cr.set_source(g); cr.paint()
    # fondo nuevo: edificios genéricos con ventanas ámbar + lluvia (antes: estrellas y rejilla de neón)
    for k in range(9):
        bx = k * 130 - 20; bh = 260 + (k * 97) % 300; by = 1700 - bh
        cr.rectangle(bx, by, 120, bh + 220); cr.set_source_rgb(0.07, 0.09, 0.13); cr.fill()
        for r in range(int(bh / 60)):
            for c in range(3):
                if (k * 7 + r * 3 + c) % 4 == 0:
                    al = 0.35 + 0.25 * math.sin(t * 1.5 + k + r)
                    cr.rectangle(bx + 14 + c * 36, by + 20 + r * 60, 20, 30); cr.set_source_rgba(*AMBAR, al); cr.fill()
    # cono de luz de farol
    cr.move_to(W - 120, 0); cr.line_to(W + 200, H * 0.7); cr.line_to(W - 600, H * 0.7); cr.close_path()
    cr.set_source_rgba(*AMBAR, 0.05); cr.fill()
    lluvia(cr, t)


def gancho(cr, t):
    # entrada nueva: expediente con cinta; texto completo desde el cuadro 0, con un "retroceso" de disparo
    # (sacudida corta cada 1.1 s) y subrayado ámbar que se dibuja (antes: letrero de neón que parpadea)
    ys = [600, 800]
    ciclo = (t % 1.1) / 1.1
    sac = 10 * math.exp(-ciclo * 12) * math.sin(ciclo * 60)
    for k, (s, y) in enumerate(zip(GANCHO["lineas"], ys)):
        z = 170 if k == 0 else 190
        font(cr, z)
        while cr.text_extents(s).x_advance > 920: z -= 4; font(cr, z)
        wtot = cr.text_extents(s).x_advance
        cr.save(); cr.translate(sac * (1 if k else -1), sac * 0.5)
        cr.translate(W / 2, y - z * 0.35); cr.rotate(-0.02 if k == 0 else 0.015); cr.translate(-W / 2, -(y - z * 0.35))
        x0 = W / 2 - wtot / 2
        rrect(cr, x0 - 40 + 10, y - z * 0.9 + 12, wtot + 80, z * 1.15, 10); cr.set_source_rgba(0, 0, 0, 0.5); cr.fill()
        rrect(cr, x0 - 40, y - z * 0.9, wtot + 80, z * 1.15, 10)
        cr.set_source_rgb(*(HUESO if k == 0 else TINTA)); cr.fill_preserve()
        cr.set_source_rgb(*AMBAR); cr.set_line_width(8); cr.stroke()
        col = AMBAR if GANCHO["resalta"] in s else TINTA
        if k == 0: texto(cr, s, W / 2, y, z, TINTA, centro=True, borde=0)
        else:
            # "TE " en hueso, "AYUDA" en ámbar
            font(cr, z); w1 = cr.text_extents("TE ").x_advance
            texto(cr, "TE ", x0, y, z, HUESO, centro=False, borde=0)
            texto(cr, "AYUDA", x0 + w1, y, z, AMBAR, centro=False, borde=0)
            p = min(1, 0.55 + t * 0.6)
            cr.move_to(x0 + w1, y + 28); cr.line_to(x0 + w1 + (wtot - w1) * p, y + 28)
            cr.set_source_rgb(*AMBAR); cr.set_line_width(12); cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.stroke()
        cr.restore()


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    i = linea_en(t)
    fondo(cr, t, i)
    # cámara nueva: "cámara en mano" con leve vaivén y descenso vertical lento por toma (antes: empuje con inclinación)
    d = max(0, t - L[i]["t0"])
    zc = 1.04
    dy = -30 + 30 * ease(d / 3.0)
    hx = 7 * math.sin(t * 1.7) + 3 * math.sin(t * 4.3); hy = 6 * math.cos(t * 1.3)
    cr.save()
    cr.rectangle(0, 830, W, 470); cr.rectangle(320, 1300, W - 320, 360); cr.rectangle(0, 1660, W, 40); cr.clip()
    cr.translate(690 + hx, 1220 + dy + hy); cr.scale(zc, zc); cr.translate(-690, -1220)
    eti, col = escena(cr, t)
    cr.restore()
    if i == 0 or t > L[-1]["t1"] - 0.35:
        gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1570, col if col else AMBAR, 40)
    chipb(cr, "El juego te ayuda en secreto", 340, 1745, AZUL, 34)
    cr.set_source_rgba(0, 0, 0, 0.25); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*AMBAR); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        dd = t - x["t0"]
        if 0 <= dd < 0.1:
            cr.set_source_rgba(1, 1, 1, 0.35 * (1 - dd / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        ts = [0, 1.5] + [round((x["t0"] + x["t1"]) / 2, 1) for x in L[1:]] + [9.0, 10.8, 13.0, 17.5, 21.5, 23.5, 26.8, round(L[-1]["t1"] - 0.3, 1)]
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
