#!/usr/bin/env python3
"""
Batería de pruebas de verificación y validación del formulario de Ficha Médica.
Ejecuta pruebas de caja blanca (funciones de validación) y de caja negra (UI),
captura evidencia y emite un JSON con los resultados obtenidos.
"""
import json, os, subprocess, sys, time, http.server, socketserver, threading, functools

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(RAIZ, "img")
os.makedirs(IMG, exist_ok=True)
PUERTO = 8931

resultados = []

def registrar(cid, ciclo, descripcion, esperado, obtenido, ok, obs=""):
    resultados.append(dict(id=cid, ciclo=ciclo, descripcion=descripcion,
                           esperado=esperado, obtenido=obtenido,
                           estado="APROBADA" if ok else "FALLIDA", obs=obs))
    print(("  [OK]   " if ok else "  [FALLA] ") + cid + " - " + descripcion)

# ---------------------------------------------------------------- servidor
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=RAIZ)
socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(("127.0.0.1", PUERTO), handler)
srv.log_message = lambda *a: None
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/index.html" % PUERTO
time.sleep(0.6)

from playwright.sync_api import sync_playwright

RUT_A = "12.345.678-5"
RUT_B = "9.876.543-3"

PACIENTE_A = {
    "rut": RUT_A, "nombres": "Juan Andrés", "apellidos": "Pérez Soto",
    "direccion": "Av. Los Leones 1234, Depto. 52", "ciudad": "Santiago",
    "telefono": "+56912345678", "email": "juan.perez@correo.cl",
    "fechaNacimiento": "1990-05-14", "estadoCivil": "Casado/a",
    "comentarios": "Paciente sin alergias conocidas. Control anual.",
}
PACIENTE_B = {
    "rut": RUT_B, "nombres": "María José", "apellidos": "Pérez Lagos",
    "direccion": "Calle Colón 456", "ciudad": "Valparaíso",
    "telefono": "+56987654321", "email": "mj.perez@correo.cl",
    "fechaNacimiento": "1985-11-02", "estadoCivil": "Soltero/a",
    "comentarios": "Deriva desde atención primaria.",
}

def llenar(page, datos):
    for k, v in datos.items():
        if k == "estadoCivil":
            page.select_option("#" + k, v)
        else:
            page.fill("#" + k, v)

def texto_error(page, campo):
    return page.inner_text("#err-" + campo).strip()

with sync_playwright() as p:
    nav = p.chromium.launch()
    ctx = nav.new_context(viewport={"width": 1280, "height": 1000}, locale="es-CL")
    page = ctx.new_page()
    page.goto(URL)

    # =============================================================
    # CICLO 1 — Caja blanca: funciones puras de validación
    # =============================================================
    print("\nCICLO 1 - Pruebas unitarias de funciones de validación (back end)")

    casos_bb = [
        ("CB-01", "validarRut",             "12.345.678-5",     "", "RUT válido con puntos y guion es aceptado"),
        ("CB-02", "validarRut",             "12345678-5",       "", "RUT válido sin formato es aceptado"),
        ("CB-03", "validarRut",             "12.345.678-9",     "ERROR", "DV incorrecto es rechazado (módulo 11)"),
        ("CB-04", "validarRut",             "1234-5",           "ERROR", "RUT con largo insuficiente es rechazado"),
        ("CB-05", "validarRut",             "",                 "ERROR", "RUT vacío es rechazado"),
        ("CB-06", "validarRut",             "15.467.893-K",     "", "RUT con DV = K es aceptado"),
        ("CB-07", "validarNombres",         "Juan Andrés",      "", "Nombre con tilde y espacio es aceptado"),
        ("CB-08", "validarNombres",         "Juan123",          "ERROR", "Nombre con dígitos es rechazado"),
        ("CB-09", "validarNombres",         "J",                "ERROR", "Nombre de 1 carácter es rechazado (mínimo 2)"),
        ("CB-10", "validarApellidos",       "Pérez-Soto",       "", "Apellido compuesto con guion es aceptado"),
        ("CB-11", "validarDireccion",       "Av. Los Leones 1234", "", "Dirección válida es aceptada"),
        ("CB-12", "validarDireccion",       "Av 1",             "ERROR", "Dirección menor a 5 caracteres es rechazada"),
        ("CB-13", "validarCiudad",          "Valparaíso",       "", "Ciudad con tilde es aceptada"),
        ("CB-14", "validarCiudad",          "Santiago 2",       "ERROR", "Ciudad con dígitos es rechazada"),
        ("CB-15", "validarTelefono",        "+56912345678",     "", "Móvil con prefijo +56 es aceptado"),
        ("CB-16", "validarTelefono",        "912345678",        "", "Móvil sin prefijo es aceptado"),
        ("CB-17", "validarTelefono",        "12345",            "ERROR", "Teléfono de largo insuficiente es rechazado"),
        ("CB-18", "validarTelefono",        "9abc45678",        "ERROR", "Teléfono con letras es rechazado"),
        ("CB-19", "validarEmail",           "juan.perez@correo.cl", "", "Correo con formato válido es aceptado"),
        ("CB-20", "validarEmail",           "juan.perez.correo.cl", "ERROR", "Correo sin @ es rechazado"),
        ("CB-21", "validarEmail",           "juan@correo",      "ERROR", "Correo sin dominio de primer nivel es rechazado"),
        ("CB-22", "validarFechaNacimiento", "1990-05-14",       "", "Fecha pasada válida es aceptada"),
        ("CB-23", "validarFechaNacimiento", "2099-01-01",       "ERROR", "Fecha futura es rechazada"),
        ("CB-24", "validarFechaNacimiento", "1850-01-01",       "ERROR", "Edad mayor a 120 años es rechazada"),
        ("CB-25", "validarEstadoCivil",     "",                 "ERROR", "Estado civil sin seleccionar es rechazado"),
        ("CB-26", "validarEstadoCivil",     "Casado/a",         "", "Estado civil de la lista es aceptado"),
        ("CB-27", "validarComentarios",     "X" * 301,          "ERROR", "Comentario de 301 caracteres es rechazado"),
        ("CB-28", "validarComentarios",     "",                 "", "Comentario vacío es aceptado (campo opcional)"),
        ("CB-29", "validarComentarios",     "<script>",         "ERROR", "Comentario con < > es rechazado (inyección)"),
        ("CB-30", "validarBusqueda",        "P",                "ERROR", "Búsqueda de 1 carácter es rechazada"),
        ("CB-31", "validarRut",             "9.876.543-315467893K", "ERROR", "RUT sobre otro RUT es rechazado con aviso de largo"),
    ]

    for cid, fn, entrada, esperado, desc in casos_bb:
        salida = page.evaluate("([f,v]) => window.FichaMedica[f](v)", [fn, entrada])
        if esperado == "":
            ok = (salida == "")
            obt = "Sin error (valor aceptado)" if ok else 'Rechazado: "%s"' % salida
        else:
            ok = (salida != "")
            obt = 'Rechazado: "%s"' % salida if ok else "Aceptado incorrectamente"
        registrar(cid, "Ciclo 1", desc,
                  "Valor aceptado" if esperado == "" else "Valor rechazado con mensaje",
                  obt, ok, "%s(%r)" % (fn, entrada[:30]))

    # Verificación del algoritmo de dígito verificador
    dv = page.evaluate("() => window.FichaMedica.calcularDv('12345678')")
    registrar("CB-32", "Ciclo 1", "calcularDv('12345678') retorna el DV correcto",
              "DV = 5", "DV = %s" % dv, dv == "5", "Algoritmo módulo 11")

    # =============================================================
    # CICLO 2 — Caja negra: validación de campos en la interfaz
    # =============================================================
    print("\nCICLO 2 - Validación de campos desde la interfaz (front end)")

    page.evaluate("() => localStorage.clear()")
    page.reload()
    page.screenshot(path=os.path.join(IMG, "01_formulario_inicial.png"), full_page=True)

    # PF-01 Guardar con formulario vacío
    page.click("#btnGuardar")
    page.wait_for_timeout(300)
    errores = page.eval_on_selector_all(".error", "ns => ns.filter(n => n.textContent.trim()).length")
    resumen = page.inner_text("#errResumen").strip()
    registrar("PF-01", "Ciclo 2", "Presionar Guardar con el formulario vacío",
              "El sistema no guarda y marca todos los campos obligatorios",
              "Se muestran %d mensajes de error. Resumen: \"%s\"" % (errores, resumen),
              errores >= 9 and "No se guardó" in resumen,
              "9 campos obligatorios + resumen")
    page.screenshot(path=os.path.join(IMG, "02_validacion_campos_vacios.png"), full_page=True)

    # PF-02 RUT con DV incorrecto
    page.fill("#rut", "12.345.678-9")
    page.click("#nombres")
    page.wait_for_timeout(200)
    msg = texto_error(page, "rut")
    registrar("PF-02", "Ciclo 2", "Ingresar RUT 12.345.678-9 (dígito verificador erróneo)",
              "Mensaje de RUT inválido bajo el campo",
              'Mensaje mostrado: "%s"' % msg, "dígito verificador" in msg)
    page.screenshot(path=os.path.join(IMG, "03_rut_invalido.png"), clip={"x":0,"y":120,"width":1280,"height":420})

    # PF-03 Email inválido
    page.fill("#rut", RUT_A)
    page.fill("#email", "juan.perez.correo.cl")
    page.click("#ciudad")
    page.wait_for_timeout(200)
    msg = texto_error(page, "email")
    registrar("PF-03", "Ciclo 2", "Ingresar email sin @",
              "Mensaje de correo inválido", 'Mensaje mostrado: "%s"' % msg, msg != "")

    # PF-04 Teléfono con letras
    page.fill("#telefono", "9abc45678")
    page.click("#ciudad")
    page.wait_for_timeout(200)
    msg = texto_error(page, "telefono")
    registrar("PF-04", "Ciclo 2", "Ingresar teléfono con letras",
              "Mensaje de teléfono inválido", 'Mensaje mostrado: "%s"' % msg, msg != "")

    # PF-05 Fecha futura
    page.fill("#fechaNacimiento", "2099-01-01")
    page.click("#ciudad")
    page.wait_for_timeout(200)
    msg = texto_error(page, "fechaNacimiento")
    registrar("PF-05", "Ciclo 2", "Ingresar fecha de nacimiento futura (2099-01-01)",
              "Mensaje indicando que la fecha no puede ser futura",
              'Mensaje mostrado: "%s"' % msg, "futura" in msg)

    # PF-06 Estado civil sin seleccionar
    msg_ec = page.evaluate("() => window.FichaMedica.validarEstadoCivil(document.getElementById('estadoCivil').value)")
    registrar("PF-06", "Ciclo 2", "Dejar el combo Estado civil sin seleccionar",
              "Mensaje solicitando seleccionar un estado civil",
              'Mensaje: "%s"' % msg_ec, msg_ec != "")

    # PF-07 Corrección en vivo
    page.fill("#email", "juan.perez@correo.cl")
    page.wait_for_timeout(250)
    msg = texto_error(page, "email")
    clases = page.get_attribute("#email", "class") or ""
    registrar("PF-07", "Ciclo 2", "Corregir un campo previamente marcado como inválido",
              "El mensaje desaparece y el campo se marca como válido",
              'Mensaje: "%s" / clase CSS: "%s"' % (msg, clases),
              msg == "" and "valido" in clases, "Validación en vivo evento input")

    # PF-08 Contador de comentarios
    page.fill("#comentarios", "Control anual")
    page.wait_for_timeout(150)
    cont = page.inner_text("#contadorComentarios")
    registrar("PF-08", "Ciclo 2", "Escribir en Comentarios y observar el contador",
              "El contador refleja los caracteres escritos sobre 300",
              "Contador muestra: %s" % cont, cont == "13/300")

    # PF-09 Escribir un RUT nuevo sobre uno ya formateado, tecla por tecla
    page.reload()
    page.click("#rut")
    page.type("#rut", "12345678-5", delay=15)
    page.click("#nombres")
    page.wait_for_timeout(200)
    formateado = page.input_value("#rut")
    page.click("#rut")
    page.keyboard.press("End")
    page.type("#rut", "9876543-3", delay=15)
    page.click("#nombres")
    page.wait_for_timeout(250)
    valor = page.input_value("#rut")
    msg = texto_error(page, "rut")
    registrar("PF-09", "Ciclo 2", "Escribir un RUT nuevo sobre uno ya formateado, sin borrar el anterior",
              "El campo admite el texto completo y el sistema advierte que el RUT quedó demasiado largo",
              'Valor en el campo: "%s". Mensaje: "%s"' % (valor, msg),
              len(valor) > len(formateado) and "demasiado largo" in msg,
              "Regresión del defecto de maxlength detectado en la ejecución manual")

    # PF-10 Al enfocar un RUT válido, escribir lo reemplaza
    page.click("#rut")
    page.keyboard.press("Control+a")
    page.type("#rut", "12345678-5", delay=15)
    page.click("#nombres")
    page.wait_for_timeout(200)
    page.click("#rut")
    page.type("#rut", "9876543-3", delay=15)
    page.click("#nombres")
    page.wait_for_timeout(250)
    valor = page.input_value("#rut")
    msg = texto_error(page, "rut")
    registrar("PF-10", "Ciclo 2", "Enfocar un RUT ya válido y escribir uno nuevo sin borrarlo",
              "El contenido anterior se reemplaza y el nuevo RUT queda válido",
              'Valor en el campo: "%s". Mensaje: "%s"' % (valor, msg or "sin error"),
              valor == "9.876.543-3" and msg == "",
              "Selección automática del contenido al enfocar")

    # =============================================================
    # CICLO 3 — Botones y persistencia
    # =============================================================
    print("\nCICLO 3 - Botones Guardar / Limpiar / Cerrar y persistencia")

    page.reload()
    llenar(page, PACIENTE_A)
    page.wait_for_timeout(200)
    page.screenshot(path=os.path.join(IMG, "04_formulario_valido.png"), full_page=True)

    page.click("#btnGuardar")
    page.wait_for_timeout(400)
    toast = page.inner_text("#toast").strip()
    total = page.evaluate("() => Object.keys(window.FichaMedica.leerFichas()).length")
    registrar("PB-01", "Ciclo 3", "Guardar una ficha nueva con todos los datos válidos",
              "Se almacena el registro y se confirma en pantalla",
              'Aviso: "%s". Registros en almacenamiento: %d' % (toast, total),
              "guardada correctamente" in toast and total == 1)
    page.screenshot(path=os.path.join(IMG, "05_guardado_ok.png"))

    vacio = page.evaluate("() => document.getElementById('rut').value === ''")
    registrar("PB-02", "Ciclo 3", "Verificar el formulario después de guardar",
              "Los campos quedan limpios para un nuevo ingreso",
              "Campo RUT vacío: %s" % ("sí" if vacio else "no"), vacio)

    # PB-03 Registro duplicado, se CANCELA la sobrescritura
    dialogos = []
    def cancelar(d):
        dialogos.append(d.message); d.dismiss()
    page.on("dialog", cancelar)
    llenar(page, dict(PACIENTE_A, nombres="Juan Modificado"))
    page.click("#btnGuardar")
    page.wait_for_timeout(400)
    guardado = page.evaluate("() => window.FichaMedica.leerFichas()['123456785'].nombres")
    pregunto = any("sobrescribir" in m for m in dialogos)
    registrar("PB-03", "Ciclo 3", "Guardar un RUT ya existente y cancelar la sobrescritura",
              "El sistema pregunta si desea sobrescribir y, al cancelar, no modifica el registro",
              'Diálogo mostrado: %s. Nombre almacenado sigue siendo "%s"' % ("sí" if pregunto else "no", guardado),
              pregunto and guardado == "Juan Andrés",
              "Mensaje: %s" % (dialogos[-1].replace("\n", " | ") if dialogos else "-"))
    page.remove_listener("dialog", cancelar)

    # PB-04 Registro duplicado, se ACEPTA la sobrescritura
    page.on("dialog", lambda d: d.accept())
    page.click("#btnGuardar")
    page.wait_for_timeout(400)
    toast = page.inner_text("#toast").strip()
    guardado = page.evaluate("() => window.FichaMedica.leerFichas()['123456785'].nombres")
    total = page.evaluate("() => Object.keys(window.FichaMedica.leerFichas()).length")
    registrar("PB-04", "Ciclo 3", "Guardar un RUT ya existente y aceptar la sobrescritura",
              "El registro se actualiza sin duplicarse",
              'Aviso: "%s". Nombre actualizado a "%s". Total de registros: %d' % (toast, guardado, total),
              "sobrescrita" in toast and guardado == "Juan Modificado" and total == 1)

    # PB-05 Botón Limpiar con confirmación
    llenar(page, PACIENTE_B)
    page.wait_for_timeout(150)
    page.click("#btnLimpiar")
    page.wait_for_timeout(350)
    quedo_vacio = page.evaluate(
        "() => ['rut','nombres','apellidos','direccion','ciudad','telefono','email','comentarios']"
        ".every(id => document.getElementById(id).value === '')")
    registrar("PB-05", "Ciclo 3", "Presionar Limpiar con datos cargados y confirmar",
              "Solicita confirmación y deja todos los campos en blanco",
              "Todos los campos quedaron vacíos: %s" % ("sí" if quedo_vacio else "no"), quedo_vacio)

    # PB-06 Botón Limpiar sobre formulario ya vacío
    page.click("#btnLimpiar")
    page.wait_for_timeout(300)
    toast = page.inner_text("#toast").strip()
    registrar("PB-06", "Ciclo 3", "Presionar Limpiar con el formulario ya vacío",
              "Informa que no hay datos que limpiar y no pide confirmación",
              'Aviso: "%s"' % toast, "ya está vacío" in toast)

    # PB-07 Botón Cerrar
    page.click("#btnCerrar")
    page.wait_for_timeout(600)
    visible = page.is_visible("#overlayCerrado")
    registrar("PB-07", "Ciclo 3", "Presionar Cerrar y confirmar",
              "Cierra la ficha; si el navegador bloquea window.close() muestra la pantalla de sesión cerrada",
              "Pantalla de respaldo visible: %s" % ("sí" if visible else "no"), visible,
              "El navegador bloquea window.close() en pestañas no abiertas por script")
    page.screenshot(path=os.path.join(IMG, "06_cerrar_sesion.png"), full_page=True)
    page.click("#btnReabrir")
    page.wait_for_timeout(200)

    # PB-08 Persistencia tras recargar
    page.reload()
    page.wait_for_timeout(300)
    total = page.evaluate("() => Object.keys(window.FichaMedica.leerFichas()).length")
    badge = page.inner_text("#contadorFichas")
    registrar("PB-08", "Ciclo 3", "Recargar la página y verificar los registros",
              "Los registros guardados se mantienen disponibles",
              "Registros tras recargar: %d. Contador en pantalla: %s" % (total, badge), total == 1)

    # =============================================================
    # CICLO 4 — Búsqueda por apellido
    # =============================================================
    print("\nCICLO 4 - Búsqueda por apellido")

    page.on("dialog", lambda d: d.accept())
    llenar(page, PACIENTE_B)
    page.click("#btnGuardar")
    page.wait_for_timeout(400)
    llenar(page, dict(PACIENTE_A, rut="15.467.893-K", nombres="Carla",
                      apellidos="González Ríos", email="carla.gonzalez@correo.cl"))
    page.click("#btnGuardar")
    page.wait_for_timeout(400)

    # PBQ-01 Búsqueda con coincidencias
    page.fill("#buscaApellido", "Pérez")
    page.click("#btnBuscar")
    page.wait_for_timeout(350)
    filas = page.eval_on_selector_all("#tablaResultados tbody tr", "ns => ns.length")
    registrar("PBQ-01", "Ciclo 4", 'Buscar el apellido "Pérez" (2 pacientes registrados)',
              "Se listan los 2 registros coincidentes",
              "Filas devueltas: %d" % filas, filas == 2)
    page.evaluate("() => document.getElementById('toast').hidden = true")
    page.screenshot(path=os.path.join(IMG, "07_busqueda_resultados.png"), full_page=True)

    # PBQ-02 Búsqueda sin acentos y en minúsculas
    page.fill("#buscaApellido", "perez")
    page.click("#btnBuscar")
    page.wait_for_timeout(350)
    filas = page.eval_on_selector_all("#tablaResultados tbody tr", "ns => ns.length")
    registrar("PBQ-02", "Ciclo 4", 'Buscar "perez" en minúsculas y sin tilde',
              "Devuelve los mismos 2 registros (búsqueda insensible a tildes y mayúsculas)",
              "Filas devueltas: %d" % filas, filas == 2)

    # PBQ-03 Búsqueda parcial
    page.fill("#buscaApellido", "Gon")
    page.click("#btnBuscar")
    page.wait_for_timeout(350)
    filas = page.eval_on_selector_all("#tablaResultados tbody tr", "ns => ns.length")
    registrar("PBQ-03", "Ciclo 4", 'Buscar por coincidencia parcial "Gon"',
              "Devuelve el registro González Ríos",
              "Filas devueltas: %d" % filas, filas == 1)

    # PBQ-04 Búsqueda sin resultados
    page.fill("#buscaApellido", "Zúñiga")
    page.click("#btnBuscar")
    page.wait_for_timeout(350)
    aviso = page.inner_text("#resultados").strip()
    registrar("PBQ-04", "Ciclo 4", 'Buscar un apellido inexistente ("Zúñiga")',
              "Mensaje de sin resultados, no una tabla vacía",
              'Mensaje: "%s"' % aviso, "Sin resultados" in aviso)
    page.screenshot(path=os.path.join(IMG, "08_busqueda_sin_resultados.png"), full_page=True)

    # PBQ-05 Búsqueda vacía
    page.fill("#buscaApellido", "")
    page.click("#btnBuscar")
    page.wait_for_timeout(300)
    msg = texto_error(page, "buscaApellido")
    registrar("PBQ-05", "Ciclo 4", "Presionar Buscar con el campo apellido vacío",
              "Solicita ingresar un apellido y no ejecuta la búsqueda",
              'Mensaje: "%s"' % msg, msg != "")

    # PBQ-06 Búsqueda con caracteres no permitidos
    page.fill("#buscaApellido", "P3rez")
    page.click("#btnBuscar")
    page.wait_for_timeout(300)
    msg = texto_error(page, "buscaApellido")
    registrar("PBQ-06", "Ciclo 4", 'Buscar con dígitos ("P3rez")',
              "Rechaza la entrada indicando que solo se admiten letras",
              'Mensaje: "%s"' % msg, msg != "")

    # PBQ-07 Ver todos
    page.click("#btnVerTodos")
    page.wait_for_timeout(350)
    filas = page.eval_on_selector_all("#tablaResultados tbody tr", "ns => ns.length")
    registrar("PBQ-07", "Ciclo 4", 'Presionar "Ver todos"',
              "Lista los 3 registros almacenados",
              "Filas devueltas: %d" % filas, filas == 3)

    # PBQ-08 Cargar ficha desde resultados
    page.click("#tablaResultados tbody tr:first-child .btn-mini")
    page.wait_for_timeout(400)
    rut_cargado = page.input_value("#rut")
    registrar("PBQ-08", "Ciclo 4", "Cargar una ficha desde la tabla de resultados",
              "Los datos del paciente se cargan en el formulario para editarlos",
              "RUT cargado en el formulario: %s" % rut_cargado, rut_cargado != "")
    page.evaluate("() => document.getElementById('toast').hidden = true")
    page.screenshot(path=os.path.join(IMG, "09_ficha_cargada.png"), full_page=True)

    # PBQ-09 Responsividad
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(400)
    scroll_h = page.evaluate("() => document.documentElement.scrollWidth")
    registrar("PBQ-09", "Ciclo 4", "Visualizar el formulario en pantalla de 390 px (móvil)",
              "El contenido se adapta sin desbordar horizontalmente",
              "Ancho de desplazamiento: %d px" % scroll_h, scroll_h <= 400,
              "Diseño responsivo con CSS Grid")
    page.screenshot(path=os.path.join(IMG, "10_vista_movil.png"), full_page=True)

    ctx.close(); nav.close()

srv.shutdown()

aprobadas = sum(1 for r in resultados if r["estado"] == "APROBADA")
print("\n" + "=" * 62)
print("RESUMEN: %d/%d pruebas aprobadas" % (aprobadas, len(resultados)))
print("=" * 62)
for r in resultados:
    if r["estado"] == "FALLIDA":
        print("FALLIDA -> %s: %s | obtenido: %s" % (r["id"], r["descripcion"], r["obtenido"]))

with open(os.path.join(RAIZ, "pruebas", "resultados.json"), "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=1)

sys.exit(0 if aprobadas == len(resultados) else 1)
