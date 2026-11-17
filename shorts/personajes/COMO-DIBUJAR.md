# Cómo dibujar personajes en los Shorts

Regla: el personaje principal del Short sale **dibujado y reconocible** desde el cuadro 0 (el gancho), con nuestro estilo de caricatura: trazo de tinta grueso, colores planos, una sombra y un brillo. Es un dibujo propio, no arte oficial.

Sigue prohibido: logos oficiales, capturas o imágenes oficiales pegadas, y el audio original de los juegos. Los nombres de empresas van solo como texto.

## Paso a paso

1. **¿Ya existe?** Mira `PERSONAJES` en `personajes.py`. Si está, úsalo:
   ```python
   import sys; sys.path.insert(0, "shorts/personajes")
   import personajes
   personajes.dibujar(cr, "kirby", x, y_pies, alto=520, t=t)         # se anima solo (rebota, parpadea)
   personajes.dibujar(cr, "kirby", x, y_pies, alto=520, t=t, rebote=False)  # si la escena ya lo mueve
   personajes.dibujar(cr, "sonic", x, y_pies, alto=620, t=t, mira=-1)  # mira=-1 lo voltea
   personajes.dibujar(cr, "sonic", x, y_pies, alto=620, t=t, alpha=0.5)  # para fundidos
   ```
2. **Si no existe, agrégalo.** Antes de dibujar, escribe en las notas del Short la lista de rasgos que lo hacen reconocible:
   - silueta (forma general vista en negro),
   - 2-3 colores exactos (hex),
   - cómo son los ojos,
   - 2-3 rasgos firma.
   Ejemplos: Kirby = bola rosa, pies rojos ovalados, ojos óvalo altos negros con azul abajo, mejillas rosas. Sonic = tres o cuatro púas grandes hacia atrás, ojos unidos en una sola pieza blanca con pupilas verdes, hocico color piel que sobresale, zapatos rojos con correa blanca, guantes blancos.
3. Escribe una función `_nombre(cr, t, **_)` que dibuje en una caja de 1000 × 1000 con los pies en (500, 1000). Usa las ayudas `_elipse`, `_relleno` y `_contorno_y_relleno`, borde 12-14, y algo que se mueva con `t` (respirar, parpadear con `_parpadeo`). Regístrala en `PERSONAJES`.
4. **Prueba visual obligatoria:** renderiza un PNG del personaje solo sobre fondo claro, ábrelo y compáralo con la lista del paso 2. Si un rasgo no se ve, corrígelo. Máximo 3 rondas.
5. Si después de 3 rondas no se parece, no lo pongas grande: úsalo pequeño o de espaldas con su nombre en texto, y anótalo en las notas del Short para mejorarlo después.
6. Guarda el personaje nuevo en `personajes.py` en main (commit propio), para que el próximo Short lo reuse.

## En las notas del Short

Anota qué personajes salieron, si eran de la biblioteca o nuevos, y cuántas rondas de prueba llevó cada uno nuevo.
