# PEC4 - Visualizacion de datos

## Requisitos
- Python 3.9+
- Librerias: pandas, numpy, matplotlib
- Opcional para IC en regresiones: statsmodels

## Uso
1) Instala dependencias:
   python -m pip install -r requirements.txt

2) Ejecuta el pipeline:
   python main.py

## GitHub Pages
1) Genera las figuras:
   python main.py
2) Copia las figuras a la web:
   xcopy /E /I /Y outputs\\figures docs\\figures
3) Activa GitHub Pages desde la carpeta `docs/`.
4) Abre `docs/index.html` localmente o en Pages.

## Salidas
- Figuras en outputs/figures/*.png (300 dpi)
- Manifest en outputs/figures/manifest.csv

## Notas
- Las figuras excluyen DNFs cuando se indica en la nota.
- Los fines de semana con sprint se identifican por presencia en sprint_results.csv.
