# EA2 — Panel del catálogo con integración y despliegue continuos

[![CI](https://github.com/jesusjoelgonca/ea2-devops-panel-catalogo/actions/workflows/ci.yml/badge.svg)](https://github.com/jesusjoelgonca/ea2-devops-panel-catalogo/actions/workflows/ci.yml)

Continuación de la Evidencia de aprendizaje 1 del curso **Programación para
Análisis de Datos** (PREICA2602B020048). El catálogo de teléfonos inteligentes
construido con *web scraping* en la EA1 se convierte aquí en un panel web que
se construye, prueba y despliega de forma automática con Git, GitHub Actions
y GitHub Pages.

- **Estudiante:** Jesus Gonzalez
- **Datos de entrada:** `data/catalogo_consolidado.csv` — 16 productos extraídos
  de Amazon.com en la EA1 (método BeautifulSoup, artículo principal:
  Samsung Galaxy A57 5G, ASIN `B0GW9TVHJB`)
- **Sitio publicado:** <https://jesusjoelgonca.github.io/ea2-devops-panel-catalogo/>
- **Entregable:** informe en PDF (`docs/Gonzalez_Jesus_Optimizando_EA2.pdf`)

## Qué hace el proyecto

1. Carga y valida el catálogo consolidado de la EA1.
2. Calcula métricas del mercado: precio promedio, calificación, descuentos y
   distribución por marca.
3. Genera un panel HTML estático con esas cifras.
4. Un flujo de GitHub Actions ejecuta las pruebas en cada cambio y, al llegar
   a `main`, construye y publica el panel en GitHub Pages.

## Ejecución

Requiere Python 3.11 o superior. No hay dependencias externas: todo el código
usa la biblioteca estándar, por lo que las pruebas corren en segundos y el
pipeline no depende de descargas de paquetes.

```bash
# Construir el panel a partir del catálogo
python -m src.panel construir --catalogo data/catalogo_consolidado.csv --salida site

# Pruebas unitarias
python -m unittest discover -s tests -v
```

El panel queda en `site/index.html` con los datos también en `site/datos.json`.

## Estructura

```
EA2/
├── src/panel/
│   ├── datos.py       # carga y validación del catálogo
│   ├── metricas.py    # indicadores del mercado
│   ├── sitio.py       # generación del HTML y del JSON
│   └── __main__.py    # interfaz de línea de comandos
├── tests/             # pruebas unitarias (unittest)
├── data/              # catálogo consolidado de la EA1
├── .github/workflows/ # integración continua y despliegue
└── docs/              # informe de la evidencia
```

## Flujo de trabajo

El desarrollo siguió un esquema de ramas por funcionalidad con revisión antes
de fusionar:

1. `main` parte del esqueleto del proyecto y del catálogo de datos.
2. Cada funcionalidad se desarrolla en una rama `feature/...` y entra a
   `main` por medio de un *pull request*, que GitHub Actions verifica antes
   de la fusión.
3. Al fusionarse en `main`, el flujo de despliegue reconstruye el panel y lo
   publica en GitHub Pages.

### Integración continua (`.github/workflows/ci.yml`)

Se ejecuta en cada *push* y en cada *pull request*, sobre **Ubuntu y Windows**
con Python 3.12. Comprueba que todos los módulos compilan (`compileall`) y
ejecuta la suite de pruebas. La matriz de sistemas operativos es la prueba de
la portabilidad: el proyecto no usa rutas absolutas ni APIs de un solo sistema.

### Despliegue continuo (`.github/workflows/cd.yml`)

Al actualizarse `main`, un segundo flujo vuelve a correr las pruebas, genera
el panel, empaqueta la carpeta `site/` y la publica en **GitHub Pages** con
`actions/deploy-pages`. La publicación se hace desde el servidor de Actions,
nunca desde el equipo local: el sitio publicado sale siempre del código de la
rama principal, no de una carpeta local.

## Estado

En construcción. Las secciones de integración y despliegue se completan con
el flujo de trabajo de GitHub Actions.
