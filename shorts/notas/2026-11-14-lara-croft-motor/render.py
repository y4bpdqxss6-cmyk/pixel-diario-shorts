"""Motor de respaldo Pixel Diario — Short 'Lara Croft iba a ser un hombre'.
Dibuja con cairo, sin personajes reconocibles: el explorador es una figura
geométrica genérica (círculo + cuerpo), sin rasgos del personaje real.
Zona de la mascota libre (x 60–310, y 1300–1660)."""
import json, math, subprocess, sys, random
import cairo

W, H, FPS = 1080, 1920, 30
T = json.load(open("tiempos.json"))
DUR = T["dur"]
L = T["lineas"]
GANCHO = {"lineas": ["LARA CROFT", "iba a ser", "hombre."], "resalta": "hombre."}

# paleta: noche de desierto, ciruela y arena (antes: azul tinta con muros lila)
BG = (0.11, 0.06, 0.09)
ARENA = (0.95, 0.74, 0.42)
TERRA = (0.86, 0.38, 0.26)
TEAL = (0.32, 0.86, 0.80)
ROJO = (1.0, 0.25, 0.28)
BLANCO = (1, 1, 1)
OSCURO = (0.06, 0.03, 0.05)

RESALTA = {1: ["noventa,", "Core", "Design"], 2: ["trampas", "pirámides."], 3: ["mujer."], 4: ["Lara."],
           5: ["Laura", "Cruz,", "sudamericana."], 6: ["inglés…", "guía", "telefónica."], 7: ["Lara", "Croft,", "británica."],
           8: ["Indiana", "Jones."], 9: ["demanda."], 10: ["Indiana", "Jones,", "hombre."]}
COLRES = {3: TEAL, 4: ROJO, 8: TERRA, 9: ROJO}


def ease(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)


def lerp(a, b, u): return a + (b - a) * u


def linea_en(t):
    for x in L:
        if t < x["t1"] + 0.18: return x["i"]
    return len(L) - 1


def local(i, t, i2=None):
    a = L[i]["t0"]; b = L[i2 if i2 is not None else i]["t1"]
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
    """chip de abajo; nunca entra en la zona de la mascota (x<=310). Estilo nuevo: contorno + punto."""
    x = max(x, 340)
    font(cr, size); w = cr.text_extents(s).x_advance + 74
    rrect(cr, x, y, w, size + 30, 14); cr.set_source_rgba(*OSCURO, 0.85); cr.fill_preserve()
    cr.set_source_rgb(*color); cr.set_line_width(4); cr.stroke()
    cr.arc(x + 26, y + (size + 30) / 2, 8, 0, 2 * math.pi); cr.fill()
    cr.set_source_rgb(*BLANCO); cr.move_to(x + 48, y + size + 8); cr.show_text(s)


# ---------- dibujos genéricos ----------
def piramide(cr, cx, base, w, h, alpha=1.0):
    cr.move_to(cx - w / 2, base); cr.line_to(cx, base - h); cr.line_to(cx + w / 2, base); cr.close_path()
    cr.set_source_rgba(*TERRA, 0.55 * alpha); cr.fill()
    cr.set_source_rgba(*ARENA, 0.35 * alpha); cr.set_line_width(3)
    for k in range(1, 6):
        y = base - h * k / 6; hw = w / 2 * (1 - k / 6)
        cr.move_to(cx - hw, y); cr.line_to(cx + hw, y)
    cr.stroke()


def suelo(cr, t):
    cr.set_source_rgba(*ARENA, 0.18); cr.rectangle(40, 1250, 1000, 6); cr.fill()
    rnd = random.Random(3)
    for k in range(30):
        x = (rnd.uniform(40, 1040) - t * 60) % 1000 + 40
        cr.set_source_rgba(*ARENA, 0.25); cr.arc(x, 1262 + rnd.uniform(0, 20), 2.5, 0, 2 * math.pi); cr.fill()


def marte(cr, x, y, r, color, lw=10):
    cr.set_source_rgb(*color); cr.set_line_width(lw)
    cr.new_sub_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.stroke()
    a = -math.pi / 4; x1, y1 = x + r * math.cos(a), y + r * math.sin(a); x2, y2 = x1 + r * 0.9, y1 - r * 0.9
    cr.move_to(x1, y1); cr.line_to(x2, y2); cr.stroke()
    cr.move_to(x2 - r * 0.55, y2); cr.line_to(x2, y2); cr.line_to(x2, y2 + r * 0.55); cr.stroke()


def venus(cr, x, y, r, color, lw=10):
    cr.set_source_rgb(*color); cr.set_line_width(lw)
    cr.new_sub_path(); cr.arc(x, y, r, 0, 2 * math.pi); cr.stroke()
    cr.move_to(x, y + r); cr.line_to(x, y + r * 2.1); cr.move_to(x - r * 0.55, y + r * 1.55); cr.line_to(x + r * 0.55, y + r * 1.55); cr.stroke()


def figura(cr, x, y, t, color=ARENA, esc=1.0, mujer=0.0, paso=True, alpha=1.0):
    """figura geométrica genérica; 'mujer' 0..1 solo cambia la silueta del cuerpo."""
    cr.save(); cr.translate(x, y); cr.scale(esc, esc)
    bob = 4 * math.sin(t * 10) if paso else 0
    cr.set_source_rgba(*color, alpha)
    cr.set_line_width(14); cr.set_line_cap(cairo.LINE_CAP_ROUND)
    sw = 0.45 * math.sin(t * 10) if paso else 0
    for s in (1, -1):
        cr.move_to(0, -40); cr.line_to(40 * math.sin(s * sw + s * 0.15), 0); cr.stroke()
    top_w, bot_w = lerp(26, 16, mujer), lerp(26, 34, mujer)
    cr.move_to(-top_w, -130 + bob); cr.line_to(top_w, -130 + bob); cr.line_to(bot_w, -40); cr.line_to(-bot_w, -40); cr.close_path(); cr.fill()
    cr.move_to(-top_w + 4, -122 + bob); cr.line_to(-40, -70 + 18 * sw); cr.move_to(top_w - 4, -122 + bob); cr.line_to(40, -70 - 18 * sw); cr.stroke()
    cr.new_sub_path(); cr.arc(0, -158 + bob, 24, 0, 2 * math.pi); cr.fill()
    cr.restore()


def etiqueta(cr, s, x, y, size, color, tachado=0.0, rot=0.0, esc=1.0):
    cr.save(); cr.translate(x, y); cr.rotate(rot); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 70
    rrect(cr, -w / 2, -size * 0.95, w, size * 1.5, 18); cr.set_source_rgb(*BLANCO); cr.fill()
    cr.new_sub_path(); cr.arc(-w / 2 + 26, -size * 0.2, 9, 0, 2 * math.pi); cr.set_source_rgb(*BG); cr.fill()
    cr.set_source_rgb(*color); cr.move_to(-w / 2 + 50, size * 0.25); cr.show_text(s)
    if tachado > 0:
        cr.set_source_rgb(*ROJO); cr.set_line_width(12)
        cr.move_to(-w / 2 + 20, 0); cr.line_to(-w / 2 + 20 + (w - 40) * tachado, -size * 0.1); cr.stroke()
    cr.restore()


def sello(cr, s, x, y, size, color, u):
    k = ease(u * 4); esc = 2.2 - 1.2 * k
    cr.save(); cr.translate(x, y); cr.rotate(-0.18); cr.scale(esc, esc)
    font(cr, size); w = cr.text_extents(s).x_advance + 60
    cr.set_source_rgba(*color, k); cr.set_line_width(8)
    rrect(cr, -w / 2, -size * 0.95, w, size * 1.4, 12); cr.stroke()
    cr.move_to(-w / 2 + 30, size * 0.2); cr.show_text(s)
    cr.restore()


def escena(cr, t):
    i = linea_en(t)
    if t < L[1]["t0"] or i == 10:  # A y cierre en bucle: misma imagen
        u = t / L[1]["t0"] if i == 0 else local(10, t)
        piramide(cr, 760, 1250, 420, 300)
        suelo(cr, t)
        fx = lerp(320, 560, u)
        figura(cr, fx, 1250, t, ARENA, 1.25)
        marte(cr, fx + 90, 960, 34 + 4 * math.sin(t * 6), TEAL, 9)
        return ("¿hombre?", TEAL) if i == 10 else (None, None)
    if i == 1:
        u = local(1, t)
        anio = int(lerp(1990, 1995, ease(u * 1.4)))
        texto(cr, f"{anio}", 540, 1010, 150, ARENA, borde=10)
        cr.save(); cr.rectangle(0, 1050, W, 260 * ease(u * 1.5) + 1); cr.clip()
        figura(cr, 540, 1260, t, BLANCO, 0.95, paso=False, alpha=0.9)
        cr.restore()
        px, py = 540 + 80 * math.cos(t * 5), 1080 + 170 * ease(u * 1.5)
        cr.save(); cr.translate(px + 40, py); cr.rotate(0.7)
        cr.rectangle(-8, -70, 16, 70); cr.set_source_rgb(*ARENA); cr.fill()
        cr.move_to(-8, 0); cr.line_to(8, 0); cr.line_to(0, 18); cr.close_path(); cr.set_source_rgb(*BLANCO); cr.fill(); cr.restore()
        return "Core Design · Reino Unido", ARENA
    if i == 2:
        u = local(2, t)
        cr.set_source_rgba(*TERRA, 0.35); cr.rectangle(60, 900, 960, 350); cr.fill()
        for k in range(6):
            x0 = 560 + k * 40
            cr.move_to(x0, 1250); cr.line_to(x0 + 20, 1200); cr.line_to(x0 + 40, 1250); cr.close_path()
            cr.set_source_rgb(*BLANCO); cr.fill()
        fx = lerp(300, 950, u); salto = max(0, math.sin(math.pi * max(0, min(1, (fx - 500) / 380))))
        figura(cr, fx, 1250 - 150 * salto, t, ARENA, 1.0, paso=salto < 0.05)
        rx = lerp(-60, 480, ease(u)); cr.save(); cr.translate(rx, 1170); cr.rotate(t * 4)
        cr.new_sub_path(); cr.arc(0, 0, 80, 0, 2 * math.pi); cr.set_source_rgb(0.45, 0.3, 0.28); cr.fill()
        cr.set_source_rgba(0, 0, 0, 0.35); cr.set_line_width(6); cr.move_to(-60, 0); cr.line_to(60, 0); cr.stroke(); cr.restore()
        return "trampas y pirámides", TERRA
    if i == 3:
        u = local(3, t)
        a = 1 - ease(u * 2.2)
        figura(cr, 400, 1250, t, ARENA, 1.2, 0, paso=False, alpha=max(a, 0.12))
        e = ease((u - 0.3) * 2.5)
        if e > 0: figura(cr, 680, 1250, t, TEAL, 1.2 * e, 1.0, paso=False)
        marte(cr, 400, 960, 36, (0.5, 0.45, 0.45) if u > 0.4 else ARENA, 9)
        if u > 0.32: venus(cr, 680, 930, 36 * ease((u - 0.3) * 3), TEAL, 9)
        cr.set_source_rgb(*BLANCO); cr.set_line_width(8)
        cr.move_to(480, 1100); cr.line_to(590, 1100); cr.move_to(570, 1085); cr.line_to(590, 1100); cr.line_to(570, 1115); cr.stroke()
        return "de hombre a mujer", TEAL
    if i == 4:
        u = local(4, t)
        figura(cr, 540, 1260, t, TEAL, 0.7, 1.0, paso=False)
        sh = 10 * math.sin(t * 30) * (1 if u > 0.55 else 0)
        etiqueta(cr, "LARA", 540 + sh, 1000, 96, BG, tachado=ease((u - 0.55) * 4), rot=-0.05)
        if u < 0.55: texto(cr, "?", 790, 1010, 130, ROJO, borde=8)
        return "no era su nombre", ROJO
    if i == 5:
        u = local(5, t)
        figura(cr, 300 + 40 * ease(u), 1260, t, TEAL, 0.8, 1.0, paso=False)
        etiqueta(cr, "LAURA CRUZ", 620, 1000, 80, TERRA, esc=0.6 + 0.4 * ease(u * 3))
        cr.save(); cr.translate(760, 1160); cr.set_source_rgb(*ARENA); cr.set_line_width(6)
        cr.new_sub_path(); cr.arc(0, 0, 60, 0, 2 * math.pi); cr.stroke(); cr.rotate(math.pi * 0.8 + 0.4 * math.sin(t * 3))
        cr.move_to(0, -50); cr.line_to(12, 0); cr.line_to(0, 50); cr.line_to(-12, 0); cr.close_path(); cr.set_source_rgb(*ROJO); cr.fill(); cr.restore()
        texto(cr, "SUR", 760, 1270, 34, ARENA, borde=0)
        return "aventurera sudamericana", TERRA
    if i == 6:
        u = local(6, t)
        cr.save(); cr.translate(540, 1080)
        rrect(cr, -320, -170, 640, 340, 16); cr.set_source_rgb(0.92, 0.88, 0.78); cr.fill()
        cr.set_source_rgb(0.3, 0.25, 0.2); cr.set_line_width(4); cr.move_to(0, -170); cr.line_to(0, 170); cr.stroke()
        rnd = random.Random(int(t * 8) if u < 0.75 else 99)
        for col in (-1, 1):
            for r in range(9):
                y = -140 + r * 34; w = rnd.uniform(140, 260)
                cr.set_source_rgba(0.25, 0.2, 0.18, 0.55); cr.rectangle(30 if col > 0 else -30 - w, y, w, 12); cr.fill()
        if u < 0.75:
            fl = (t * 8) % 1; sxx = abs(1 - 2 * fl) + 0.02
            cr.save(); cr.scale(sxx, 1)
            cr.rectangle(0, -170, 320, 340); cr.set_source_rgba(0.98, 0.95, 0.86, 0.9); cr.fill(); cr.restore()
        else:
            k = ease((u - 0.75) * 5)
            rrect(cr, 40, -30, 260, 60, 10); cr.set_source_rgba(*ARENA, k); cr.fill()
            cr.set_source_rgba(*BG, k); font(cr, 40); cr.move_to(90, 14); cr.show_text("CROFT")
        cr.restore()
        lx = 540 + 200 * math.sin(t * 2.5); cr.set_source_rgb(*BLANCO); cr.set_line_width(10)
        cr.new_sub_path(); cr.arc(lx, 1050, 60, 0, 2 * math.pi); cr.stroke(); cr.move_to(lx + 42, 1092); cr.line_to(lx + 100, 1150); cr.stroke()
        return "guía telefónica", ARENA
    if i == 7:
        u = local(7, t)
        figura(cr, 300, 1260, t, TEAL, 0.8, 1.0, paso=False)
        etiqueta(cr, "LAURA CRUZ", 640, 950, 64, TERRA, tachado=ease(u * 3), esc=0.85)
        if u > 0.3:
            k = ease((u - 0.3) * 3)
            etiqueta(cr, "LARA CROFT", 640, 1120, 76, BG, rot=-0.04, esc=0.4 + 0.6 * k)
        cy = 1080 - 15 * math.sin(t * 4)
        cr.move_to(260, cy); cr.line_to(270, cy - 40); cr.line_to(290, cy - 15); cr.line_to(300, cy - 48)
        cr.line_to(310, cy - 15); cr.line_to(330, cy - 40); cr.line_to(340, cy); cr.close_path(); cr.set_source_rgb(*ARENA); cr.fill()
        return "aristócrata británica", ARENA
    if i == 8:
        u = local(8, t)
        figura(cr, 330, 1250, t, ARENA, 1.1, 0, paso=False)
        marte(cr, 330, 940, 30, ARENA, 8)
        if u > 0.35:
            k = ease((u - 0.35) * 3)
            texto(cr, "≈", 540, 1130, 140, BLANCO, borde=8, alpha=k)
            cr.save(); cr.translate(780, 1100); cr.scale(max(k, 0.01), max(k, 0.01))
            rrect(cr, -190, -110, 380, 220, 24); cr.set_source_rgb(*TERRA); cr.fill()
            texto(cr, "INDIANA", 0, -10, 62, BLANCO, borde=0); texto(cr, "JONES", 0, 60, 62, BLANCO, borde=0)
            cr.restore()
        else:
            texto(cr, "¿por qué?", 720, 1110, 80, TERRA, borde=8)
        return "demasiado parecido", TERRA
    if i == 9:
        u = local(9, t)
        figura(cr, 330, 1250, t, ARENA, 1.1, 0, paso=False, alpha=0.5)
        a = -0.9 + 0.9 * ease(min(1, u * 3)); cr.save(); cr.translate(700, 1220); cr.rotate(a)
        cr.set_source_rgb(0.55, 0.36, 0.22); cr.rectangle(-10, -230, 20, 230); cr.fill()
        rrect(cr, -70, -280, 140, 70, 14); cr.fill(); cr.restore()
        rrect(cr, 600, 1225, 200, 30, 8); cr.set_source_rgb(0.4, 0.26, 0.16); cr.fill()
        sello(cr, "DEMANDA", 560, 1000, 96, ROJO, max(0, (u - 0.25) / 0.75))
        return "miedo a una demanda", ROJO
    return None, None


def fondo(cr, t):
    cr.set_source_rgb(*BG); cr.paint()
    rnd = random.Random(11)
    for k in range(80):
        x = (rnd.uniform(0, W) + t * rnd.uniform(4, 12)) % W; y = rnd.uniform(0, H)
        a = 0.1 + 0.15 * (1 + math.sin(t * rnd.uniform(1, 4) + k)) / 2
        cr.set_source_rgba(1, 0.9, 0.75, a); cr.new_sub_path(); cr.arc(x, y, rnd.uniform(1.2, 3), 0, 2 * math.pi); cr.fill()
    cr.move_to(0, 1700)
    for x in range(0, W + 40, 40):
        cr.line_to(x, 1660 + 30 * math.sin(x / 160 + t * 0.4))
    cr.line_to(W, H); cr.line_to(0, H); cr.close_path(); cr.set_source_rgba(*TERRA, 0.18); cr.fill()


def gancho(cr, t):
    # entrada nueva: las líneas se deslizan desde los lados (antes: pop central); el cuadro 0 ya se lee completo
    ys = [450, 610, 800]; sizes = [120, 110, 190]
    u = 0.88 + 0.12 * ease(t / 0.3)
    for k, (s, y, z) in enumerate(zip(GANCHO["lineas"], ys, sizes)):
        dx = (1 - u) * (300 if k % 2 == 0 else -300)
        col = ARENA if s == GANCHO["resalta"] else BLANCO
        texto(cr, s, W / 2 + dx, y, z, col, borde=14)


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
            col = COLRES.get(i, ARENA) if p in RESALTA.get(i, []) else BLANCO
            a = 1.0 if acc <= vis else 0.28
            font(cr, size); adv = cr.text_extents(p + " ").x_advance
            cr.move_to(x, y); cr.text_path(p)
            cr.set_source_rgba(*OSCURO, a); cr.set_line_width(9); cr.stroke_preserve()
            cr.set_source_rgba(*col, a); cr.fill()
            x += adv
        y += 90


def cuadro(t):
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H); cr = cairo.Context(surf)
    fondo(cr, t)
    i = linea_en(t)
    # cámara: paneo lateral suave + zoom (antes: zoom central) y sacudida en DEMANDA
    zc = 1.0 + 0.05 * local(i, t)
    if t < L[1]["t0"]: zc = 1.0 + 0.08 * (t / L[1]["t0"])
    pan = 18 * math.sin(t * 0.7); sx = 0
    if i == 9 and 0.25 < local(9, t) < 0.45: sx = 8 * math.sin(t * 70)
    cr.save(); cr.translate(540 + pan + sx, 1100); cr.scale(zc, zc); cr.translate(-540, -1100)
    eti, col = escena(cr, t)
    cr.restore()
    if t < L[1]["t0"] - 0.05: gancho(cr, t)
    else: subtitulo(cr, i, t)
    if eti: chipb(cr, eti, 360, 1340, col, 40)
    chipb(cr, "iba a ser otra cosa", 360, 1730, ARENA, 30)
    cr.set_source_rgba(1, 1, 1, 0.12); cr.rectangle(0, 0, W, 10); cr.fill()
    cr.set_source_rgb(*TEAL); cr.rectangle(0, 0, W * t / DUR, 10); cr.fill()
    for x in L[1:]:
        d = t - x["t0"]
        if 0 <= d < 0.1:
            cr.set_source_rgba(1, 0.9, 0.7, 0.16 * (1 - d / 0.1)); cr.paint()
    return surf


if __name__ == "__main__":
    modo = sys.argv[1]
    if modo == "prueba":
        import os; os.makedirs("prueba", exist_ok=True)
        for t in [0, 1.8, 5.5, 8.8, 11.5, 14.5, 17, 20.5, 23.5, 27, 29.6, 32.5]:
            cuadro(t).write_to_png(f"prueba/t{t:05.1f}.png")
    else:
        n = int(DUR * FPS)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
                              "-i", "-", "-i", "mezcla.wav", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
                              "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", "short.mp4"], stdin=subprocess.PIPE)
        for f in range(n):
            p.stdin.write(bytes(cuadro(f / FPS).get_data()))
        p.stdin.close(); p.wait()
