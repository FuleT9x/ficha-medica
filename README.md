# Ficha Médica — Formulario de ingreso de pacientes

Actividad Sumativa Semana 3 · Verificación y Validación de Software · AIEP

Sitio estático (HTML + CSS + JavaScript, sin dependencias externas) que implementa un
formulario de ingreso de ficha médica con validación completa, control de registros
duplicados y búsqueda por apellido.

## Contenido

| Archivo | Descripción |
|---|---|
| `index.html` | Formulario con los 10 campos, botones y bloque de búsqueda |
| `styles.css` | Hoja de estilos (tema claro y oscuro) |
| `app.js` | Validaciones, persistencia en `localStorage` y búsqueda |
| `pruebas/run_tests.py` | Batería automatizada de 56 casos (Playwright) |
| `pruebas/resultados.json` | Resultados obtenidos en la última ejecución |
| `img/` | Capturas de evidencia usadas en el informe |
| `informe/` | Informe de pruebas en formato Word |

## Funcionalidad

- **10 campos**: RUT, Nombres, Apellidos, Dirección, Ciudad, Teléfono, Email,
  Fecha de Nacimiento, Estado civil y Comentarios.
- **Validación de todos los campos y botones**, con mensajes en línea.
  El RUT se valida con el algoritmo de dígito verificador módulo 11.
- **Registro duplicado**: la clave del registro es el RUT normalizado. Si ya existe,
  el sistema pregunta si se desea sobrescribir y respeta la decisión del usuario.
- **Botones**: Guardar, Limpiar (con confirmación) y Cerrar (con confirmación y
  pantalla de respaldo cuando el navegador bloquea `window.close()`).
- **Búsqueda por apellido**: parcial, insensible a mayúsculas y tildes.

## Publicar en GitHub Pages

1. Crear un repositorio nuevo en GitHub, por ejemplo `ficha-medica`, marcándolo como **público**.
2. Subir el contenido de esta carpeta a la rama `main` (arrastrando los archivos en
   *Add file → Upload files*, o por consola):

   ```bash
   git init
   git add .
   git commit -m "Formulario de ficha médica - Sumativa Semana 3"
   git branch -M main
   git remote add origin https://github.com/USUARIO/ficha-medica.git
   git push -u origin main
   ```

3. En el repositorio ir a **Settings → Pages**.
4. En *Source* elegir **Deploy from a branch**, rama `main`, carpeta `/ (root)`, y guardar.
5. Esperar entre uno y dos minutos. La URL pública queda en
   `https://USUARIO.github.io/ficha-medica/`.

> `index.html` debe quedar en la raíz del repositorio para que GitHub Pages lo sirva
> como página de inicio.

### Alternativa con Netlify

Entrar a [app.netlify.com/drop](https://app.netlify.com/drop) y arrastrar la carpeta
completa. Netlify entrega una URL pública de inmediato, sin necesidad de repositorio.

## Ejecutar la batería de pruebas

```bash
pip install playwright
playwright install chromium
python pruebas/run_tests.py
```

El script levanta un servidor local, ejecuta los 56 casos, actualiza las capturas de
`img/` y escribe los resultados en `pruebas/resultados.json`.
Termina con código 0 solo si todos los casos son aprobados.

## Limitaciones conocidas

- El almacenamiento es `localStorage`, propio del navegador: los datos persisten entre
  sesiones del mismo equipo pero no se comparten entre dispositivos ni usuarios.
- La validación se ejecuta íntegramente en el cliente. En un sistema real debe
  replicarse en el servidor, ya que el cliente siempre puede ser manipulado.
