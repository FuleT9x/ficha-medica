# Ficha Médica — Formulario de ingreso de pacientes



**Sitio publicado:** https://fulet9x.github.io/ficha-medica/

Sitio estático en HTML, CSS y JavaScript, sin dependencias externas, que implementa un
formulario de ingreso de ficha médica con validación de todos sus campos, control de
registros duplicados y búsqueda de pacientes por apellido.

---

## Funcionalidad

**Diez campos:** RUT, Nombres, Apellidos, Dirección, Ciudad, Teléfono, Email,
Fecha de Nacimiento, Estado civil y Comentarios.

**Validación de todos los campos y botones**, con mensajes en línea bajo cada campo.
El RUT se valida con el algoritmo de dígito verificador módulo 11, incluido el caso
del dígito K. El teléfono acepta el formato chileno con o sin prefijo internacional.
La fecha de nacimiento rechaza fechas futuras y edades superiores a 120 años.

**Control de registros duplicados:** la clave del registro es el RUT normalizado.
Si el RUT ya existe, el sistema informa de qué paciente se trata y pregunta si se
desea sobrescribir, respetando la decisión del usuario en ambos sentidos.

**Botones:** Guardar valida el formulario completo y no almacena nada si hay errores;
Limpiar pide confirmación antes de descartar datos; Cerrar pide confirmación y muestra
una pantalla de respaldo cuando el navegador bloquea `window.close()`.

**Búsqueda por apellido:** admite coincidencias parciales y es insensible a mayúsculas
y tildes. Informa explícitamente cuando no hay resultados.

---

## Archivos

| Archivo | Descripción |
|---|---|
| `index.html` | Formulario con los diez campos, los botones y el bloque de búsqueda |
| `styles.css` | Hoja de estilos, con tema claro y oscuro |
| `app.js` | Validaciones, persistencia en `localStorage` y búsqueda |
| `pruebas/run_tests.py` | Batería automatizada de 59 casos (Playwright) |
| `pruebas/resultados.json` | Resultados de la última ejecución |

---

## Pruebas

La verificación y validación se ejecutó con dos técnicas complementarias.

**Batería automatizada:** 59 casos organizados en cuatro ciclos —pruebas unitarias de
las funciones de validación, validación de campos desde la interfaz, botones y
persistencia, y búsqueda por apellido— aplicando partición de equivalencia y análisis
de valores límite. Todos aprobados.

**Ejecución manual** sobre el sitio publicado, para cubrir lo que la automatización no
alcanza: los diálogos nativos del navegador, la persistencia entre sesiones y el
comportamiento en pantalla real.

### Ejecutar la batería

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install playwright
playwright install chromium
playwright install-deps          # solo en Linux
python pruebas/run_tests.py
```

El script levanta un servidor local, ejecuta los 59 casos, genera las capturas de
evidencia y escribe los resultados en `pruebas/resultados.json`. Termina con código 0
únicamente si todos los casos son aprobados, de modo que puede integrarse a un flujo
de integración continua.

---

## Defectos encontrados y corregidos

Durante el proceso se detectaron dos defectos reales. Ambos están documentados en el
informe de la actividad, y cada uno cuenta hoy con pruebas de regresión.

**Botón Cerrar.** La regla `.overlay { display: grid }` anulaba el ocultamiento nativo
del atributo `hidden`, dejando un elemento invisible que interceptaba los clics del
usuario. No era un error de lógica sino una colisión en la cascada de estilos. Se
corrigió declarando `[hidden] { display: none !important; }`.

**Campo RUT.** El atributo `maxlength="12"` coincidía exactamente con el largo de un
RUT ya formateado, de modo que el campo quedaba lleno tras el autoformateo y el
navegador dejaba de aceptar pulsaciones: al intentar ingresar un RUT sobre otro, el
sistema rechazaba valores correctos. Se eliminó el atributo, se agregó un mensaje
específico para el valor demasiado largo, y el contenido se selecciona al enfocar el
campo para que escribir lo reemplace.

El segundo defecto es el más instructivo del ejercicio: **la batería automatizada no
podía detectarlo**, porque la instrucción `fill` de Playwright asigna los valores de
una sola vez y nunca simula el teclado, que es donde `maxlength` actúa. Fue la prueba
manual la que lo encontró, en el primer minuto de uso.

---

## Limitaciones conocidas

**Almacenamiento local.** Los datos se guardan en `localStorage`, que está aislado por
dominio y por navegador. Persisten entre sesiones del mismo equipo, pero no se
comparten entre dispositivos ni entre usuarios: quien abra el enlace verá el formulario
vacío, y ese es el comportamiento esperado. Un sistema clínico real requiere un
servidor con base de datos y control de acceso, ya que una ficha médica contiene datos
sensibles regulados por la Ley 19.628 sobre protección de la vida privada.

**Validación del lado del cliente.** Toda la validación se ejecuta en el navegador, lo
que basta para el alcance de esta actividad pero nunca en producción: el cliente
siempre puede ser manipulado, de modo que cada regla debe replicarse en el servidor.
