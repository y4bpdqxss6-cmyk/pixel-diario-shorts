"""Dibuja un personaje solo, en 3 momentos de su animación, para revisarlo antes de usarlo.
Uso: python3 shorts/personajes/prueba_personaje.py kirby   ->  prueba-kirby.png"""
import os, sys
import cairo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import personajes

nombre = sys.argv[1]
W, H = 1500, 700
s = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
cr = cairo.Context(s)
cr.set_source_rgb(0.96, 0.93, 0.85)
cr.paint()
for k, t in enumerate((0.0, 0.25, 0.6)):
    personajes.dibujar(cr, nombre, 250 + k * 500, 660, alto=600, t=t)
s.write_to_png(f"prueba-{nombre}.png")
print(f"prueba-{nombre}.png")
