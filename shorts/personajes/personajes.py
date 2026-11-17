"""Pixel Diario: biblioteca de personajes dibujados con cairo (fan-art propio, trazo de tinta grueso).

Uso desde render.py:
    import personajes
    personajes.dibujar(cr, "kirby", x, y, alto=520, t=t)       # x, y = centro de los pies
    personajes.dibujar(cr, "sonic", x, y, alto=620, t=t, mira=-1)  # mira=-1 lo voltea

Cada personaje recibe t (segundos) y se anima solo: respira, rebota y parpadea.
Para agregar un personaje: escribe una función _nombre(cr, t) que dibuje en una caja de
1000 x 1000 con los pies en (500, 1000) y regístrala en PERSONAJES.
"""
import math
import cairo

TINTA = (0.10, 0.10, 0.16)
BLANCO = (1, 1, 1)


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _relleno(cr, color, borde=14):
    cr.set_source_rgb(*color)
    cr.fill_preserve()
    cr.set_source_rgb(*TINTA)
    cr.set_line_width(borde)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.stroke()


def _elipse(cr, cx, cy, rx, ry, ang=0.0):
    cr.save()
    cr.translate(cx, cy)
    cr.rotate(ang)
    cr.scale(rx, ry)
    cr.new_sub_path()
    cr.arc(0, 0, 1, 0, 2 * math.pi)
    cr.restore()


def _parpadeo(t, cada=3.1, fase=0.0):
    """1 = ojo abierto, 0 = cerrado. Parpadea 0,15 s cada `cada` segundos."""
    u = ((t + fase) % cada) / 0.15
    if u < 1:
        return abs(1 - 2 * u) * 0.9 + 0.1
    return 1.0


# ---------------------------------------------------------------- Kirby
def _kirby(cr, t, rebote=True):
    rosa = _rgb("#F6A6C8")
    rosa_sombra = _rgb("#E77FAE")
    rojo = _rgb("#D91E45")
    rojo_sombra = _rgb("#A3122F")
    mejilla = _rgb("#F05C8C")
    azul = _rgb("#2A57D6")

    salto = abs(math.sin(t * 3.2)) if rebote else 1.0   # rebote
    aplasta = 1 + 0.06 * (1 - salto) if rebote else 1.0  # se aplasta al tocar el suelo
    dy = -70 * salto if rebote else 0.0

    if rebote:  # sombra en el suelo (sin rebote, la escena pone su propia sombra)
        _elipse(cr, 500, 985, 260 - 70 * salto, 26)
        cr.set_source_rgba(0, 0, 0, 0.18)
        cr.fill()

    cr.save()
    cr.translate(500, 1000 + dy)
    cr.scale(aplasta, 1 / aplasta)
    cr.translate(-500, -1000)

    # pies rojos (detrás del cuerpo)
    for lado in (-1, 1):
        _elipse(cr, 500 + lado * 175, 935, 150, 78, lado * 0.32)
        _relleno(cr, rojo)
        _elipse(cr, 500 + lado * 185, 955, 105, 34, lado * 0.32)
        cr.set_source_rgba(*rojo_sombra, 0.55)
        cr.fill()

    # bracitos
    ola = math.sin(t * 6) * 0.25
    _elipse(cr, 215, 610, 95, 72, -0.6 - ola)
    _relleno(cr, rosa)
    _elipse(cr, 785, 640, 92, 70, 0.5)
    _relleno(cr, rosa)

    # cuerpo
    cr.new_path()
    cr.arc(500, 590, 330, 0, 2 * math.pi)
    cr.set_source_rgb(*rosa)
    cr.fill()
    # sombra suave abajo a la derecha
    cr.save()
    cr.arc(500, 590, 330, 0, 2 * math.pi)
    cr.clip()
    cr.arc(430, 520, 330, 0, 2 * math.pi)
    cr.rectangle(2000, -1000, -4000, 4000)  # invierte: todo menos el círculo desplazado
    cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    cr.set_source_rgb(*rosa_sombra)
    cr.fill()
    cr.restore()
    # brillo
    _elipse(cr, 380, 400, 70, 40, -0.6)
    cr.set_source_rgba(1, 1, 1, 0.45)
    cr.fill()
    cr.arc(500, 590, 330, 0, 2 * math.pi)
    cr.set_source_rgb(*TINTA)
    cr.set_line_width(14)
    cr.stroke()

    # mejillas
    for lado in (-1, 1):
        _elipse(cr, 500 + lado * 175, 640, 52, 24)
        cr.set_source_rgba(*mejilla, 0.85)
        cr.fill()

    # ojos (óvalos altos, negro con azul abajo y brillo blanco)
    abre = _parpadeo(t)
    for lado in (-1, 1):
        cx = 500 + lado * 62
        if abre < 0.3:
            cr.move_to(cx - 26, 540)
            cr.curve_to(cx - 10, 552, cx + 10, 552, cx + 26, 540)
            cr.set_source_rgb(*TINTA)
            cr.set_line_width(12)
            cr.stroke()
            continue
        cr.save()
        cr.translate(cx, 530)
        cr.scale(1, abre)
        _elipse(cr, 0, 0, 32, 82)
        cr.set_source_rgb(*TINTA)
        cr.fill_preserve()
        cr.clip()
        g = cairo.LinearGradient(0, -10, 0, 82)
        g.add_color_stop_rgba(0, *azul, 0)
        g.add_color_stop_rgba(1, *azul, 1)
        cr.rectangle(-40, -90, 80, 180)
        cr.set_source(g)
        cr.fill()
        _elipse(cr, 0, -40, 17, 30)
        cr.set_source_rgb(*BLANCO)
        cr.fill()
        cr.restore()

    # boca abierta con lengua
    cr.move_to(462, 645)
    cr.curve_to(470, 705, 530, 705, 538, 645)
    cr.close_path()
    _relleno(cr, rojo_sombra, 10)
    cr.save()
    cr.move_to(462, 645)
    cr.curve_to(470, 705, 530, 705, 538, 645)
    cr.close_path()
    cr.clip()
    _elipse(cr, 500, 700, 30, 22)
    cr.set_source_rgb(*_rgb("#FF7C8E"))
    cr.fill()
    cr.restore()

    cr.restore()


# ---------------------------------------------------------------- Sonic
def _contorno_y_relleno(cr, color, borde=12):
    """Para formas hechas de varias piezas: traza el borde y luego rellena encima,
    así las piezas se ven como una sola silueta."""
    cr.set_source_rgb(*TINTA)
    cr.set_line_width(borde * 2)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    cr.stroke_preserve()
    cr.set_source_rgb(*color)
    cr.fill()


def _sonic(cr, t, **_):
    azul = _rgb("#1E5BD8")
    azul_sombra = _rgb("#1546B0")
    piel = _rgb("#F4C28E")
    piel_sombra = _rgb("#DDA470")
    verde = _rgb("#18A043")
    rojo = _rgb("#E1252E")
    rojo_sombra = _rgb("#A5151D")
    oro = _rgb("#F2C230")

    golpe = max(0.0, math.sin(t * 7)) * 14     # golpea el pie de adelante, impaciente
    resp = math.sin(t * 2.4) * 6               # respira

    _elipse(cr, 520, 985, 260, 24)
    cr.set_source_rgba(0, 0, 0, 0.18)
    cr.fill()

    # piernas delgadas
    for x0, x1 in ((465, 430), (545, 610)):
        for ancho, col in ((44, TINTA), (20, azul)):
            cr.move_to(x0, 770)
            cr.line_to(x1, 905)
            cr.set_source_rgb(*col)
            cr.set_line_width(ancho)
            cr.set_line_cap(cairo.LINE_CAP_ROUND)
            cr.stroke()

    # zapatos rojos que apuntan al frente, con correa blanca y hebilla
    for cx, levanta in ((445, 0.0), (650, golpe)):
        cr.save()
        cr.translate(cx, 935 - levanta)
        cr.rotate(-0.04 if levanta else 0)
        cr.move_to(-70, 30)
        cr.curve_to(-95, -40, -20, -55, 40, -40)
        cr.curve_to(120, -25, 150, 10, 130, 35)
        cr.curve_to(110, 52, -40, 55, -70, 30)
        cr.close_path()
        _relleno(cr, rojo)
        _elipse(cr, 30, 38, 95, 14)
        cr.set_source_rgba(*rojo_sombra, 0.7)
        cr.fill()
        cr.rectangle(-30, -52, 40, 92)
        _relleno(cr, BLANCO, 10)
        cr.rectangle(-21, -22, 22, 26)
        _relleno(cr, oro, 6)
        cr.restore()

    cr.save()
    cr.translate(0, resp * 0.5)
    # brazo de atrás en la cadera
    for ancho, col in ((42, TINTA), (18, piel)):
        cr.move_to(420, 650)
        cr.curve_to(350, 690, 355, 765, 415, 770)
        cr.set_source_rgb(*col)
        cr.set_line_width(ancho)
        cr.stroke()
    _elipse(cr, 420, 772, 46, 40)
    _relleno(cr, BLANCO, 12)

    # cuerpo y panza
    _elipse(cr, 515, 690, 115, 125)
    _relleno(cr, azul)
    _elipse(cr, 535, 715, 75, 92)
    cr.set_source_rgb(*piel)
    cr.fill()

    # brazo de adelante con el pulgar arriba, lejos de la cara
    for ancho, col in ((42, TINTA), (18, piel)):
        cr.move_to(600, 660)
        cr.curve_to(660, 670, 720, 660, 760, 630)
        cr.set_source_rgb(*col)
        cr.set_line_width(ancho)
        cr.stroke()
    _elipse(cr, 785, 625, 54, 46)
    _relleno(cr, BLANCO, 12)
    _elipse(cr, 790, 568, 19, 36, 0.12)
    _relleno(cr, BLANCO, 10)
    cr.move_to(750, 640)
    cr.line_to(815, 640)
    cr.set_source_rgb(*TINTA)
    cr.set_line_width(8)
    cr.stroke()
    cr.restore()

    # ---- cabeza
    cr.save()
    cr.translate(0, resp)
    hx, hy, r = 480, 380, 190

    def punto(gr):
        a = math.radians(gr)
        return hx + r * math.cos(a), hy + r * math.sin(a)

    # púas: anchas en la base, curvas hacia atrás; se dibujan de abajo hacia arriba
    puas = [(165, 115, (150, 610)), (195, 145, (60, 440)), (222, 175, (90, 250)), (258, 210, (250, 95))]
    for g0, g1, (px, py) in puas:
        x0, y0 = punto(g0)
        x1, y1 = punto(g1)
        cr.move_to(x0, y0)
        cr.curve_to((x0 + px) / 2, (y0 + py) / 2 - 25, px + 30, py - 10, px, py)
        cr.curve_to(px + 40, py + 15, (x1 + px) / 2, (y1 + py) / 2 - 10, x1, y1)
        cr.line_to(hx, hy)
        cr.close_path()
        _relleno(cr, azul)
        # brillo en cada púa
        cr.move_to((x0 * 2 + px) / 3, (y0 * 2 + py) / 3)
        cr.line_to((x0 + px * 2) / 3, (y0 + py * 2) / 3 + 6)
        cr.set_source_rgba(1, 1, 1, 0.25)
        cr.set_line_width(10)
        cr.stroke()

    # oreja
    cr.move_to(510, 215)
    cr.curve_to(520, 170, 545, 120, 575, 100)
    cr.curve_to(600, 140, 615, 185, 618, 230)
    cr.close_path()
    _relleno(cr, azul)
    cr.move_to(535, 210)
    cr.curve_to(545, 180, 560, 150, 574, 138)
    cr.curve_to(590, 165, 597, 195, 598, 222)
    cr.close_path()
    cr.set_source_rgb(*piel)
    cr.fill()

    # cráneo
    cr.arc(hx, hy, r, 0, 2 * math.pi)
    _relleno(cr, azul)
    cr.save()
    cr.arc(hx, hy, r - 7, 0, 2 * math.pi)
    cr.clip()
    _elipse(cr, 350, 470, 110, 150, 0.4)
    cr.set_source_rgba(*azul_sombra, 0.7)
    cr.fill()
    cr.restore()

    # hocico: sale de la cabeza hacia el frente
    cr.move_to(455, 455)
    cr.curve_to(470, 395, 560, 395, 610, 410)
    cr.curve_to(680, 395, 760, 405, 765, 450)
    cr.curve_to(770, 500, 700, 560, 610, 565)
    cr.curve_to(520, 570, 445, 525, 455, 455)
    cr.close_path()
    _contorno_y_relleno(cr, piel)
    cr.save()
    cr.move_to(455, 455)
    cr.curve_to(470, 395, 560, 395, 610, 410)
    cr.curve_to(680, 395, 760, 405, 765, 450)
    cr.curve_to(770, 500, 700, 560, 610, 565)
    cr.curve_to(520, 570, 445, 525, 455, 455)
    cr.close_path()
    cr.clip()
    _elipse(cr, 580, 572, 140, 42)
    cr.set_source_rgba(*piel_sombra, 0.7)
    cr.fill()
    cr.restore()

    # ojos unidos: dos óvalos blancos que forman una sola pieza
    abre = max(_parpadeo(t, 2.7, 0.8), 0.07)
    cr.save()
    cr.translate(0, 395)
    cr.scale(1, abre)
    cr.translate(0, -395)
    _elipse(cr, 548, 318, 52, 84, -0.12)
    _elipse(cr, 640, 326, 42, 72, 0.12)
    _contorno_y_relleno(cr, BLANCO, 11)
    if abre > 0.5:
        for cx, cy, rx, ry in ((572, 335, 25, 40), (658, 340, 21, 35)):
            _elipse(cr, cx, cy, rx, ry)
            cr.set_source_rgb(*verde)
            cr.fill()
            _elipse(cr, cx + 5, cy + 4, rx * 0.55, ry * 0.6)
            cr.set_source_rgb(*TINTA)
            cr.fill()
            _elipse(cr, cx - 6, cy - 15, 7, 11)
            cr.set_source_rgb(*BLANCO)
            cr.fill()
    cr.restore()

    # nariz negra en la punta del hocico
    _elipse(cr, 770, 432, 30, 25)
    cr.set_source_rgb(*TINTA)
    cr.fill()
    _elipse(cr, 760, 423, 9, 6)
    cr.set_source_rgb(*BLANCO)
    cr.fill()
    # sonrisa de lado
    cr.move_to(590, 500)
    cr.curve_to(630, 530, 690, 525, 720, 490)
    cr.set_source_rgb(*TINTA)
    cr.set_line_width(12)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.stroke()
    cr.move_to(710, 478)
    cr.line_to(732, 500)
    cr.stroke()
    cr.restore()


PERSONAJES = {"kirby": _kirby, "sonic": _sonic}


def dibujar(cr, nombre, x, y, alto=520, t=0.0, mira=1, alpha=1.0, **opciones):
    """Dibuja `nombre` con los pies en (x, y) y `alto` px de altura.
    mira=-1 lo voltea; alpha < 1 lo hace aparecer transparente (para fundidos).
    Opciones extra van a la función del personaje (ej. rebote=False en Kirby)."""
    if alpha <= 0:
        return
    f = PERSONAJES[nombre]
    s = alto / 1000
    if alpha < 1:
        cr.push_group()
    cr.save()
    cr.translate(x, y)
    cr.scale(s * mira, s)
    cr.translate(-500, -1000)
    f(cr, t, **opciones)
    cr.restore()
    if alpha < 1:
        cr.pop_group_to_source()
        cr.paint_with_alpha(alpha)
