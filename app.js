/* =========================================================================
   Ficha Médica — lógica de validación, persistencia y búsqueda
   Actividad Sumativa Semana 3 — Taller de Testing y Calidad de Software (AIEP)

   Estructura:
     1. Utilidades de almacenamiento (localStorage)
     2. Funciones de validación puras  -> "back end" testeable
     3. Enlace con el DOM y pintado de errores
     4. Acciones: Guardar / Limpiar / Cerrar / Buscar
   ========================================================================= */
'use strict';

/* ----------------------------------------------------------------------
   1. ALMACENAMIENTO
   La clave del registro es el RUT normalizado (sin puntos ni guion).
   ---------------------------------------------------------------------- */
const CLAVE_ALMACEN = 'fichasMedicas';

function leerFichas() {
  try {
    const crudo = localStorage.getItem(CLAVE_ALMACEN);
    const datos = crudo ? JSON.parse(crudo) : {};
    return (datos && typeof datos === 'object') ? datos : {};
  } catch (e) {
    console.error('Almacenamiento corrupto, se reinicia:', e);
    return {};
  }
}

function escribirFichas(fichas) {
  try {
    localStorage.setItem(CLAVE_ALMACEN, JSON.stringify(fichas));
    return true;
  } catch (e) {
    console.error('No se pudo escribir en localStorage:', e);
    return false;
  }
}

function existeFicha(rut) {
  return Object.prototype.hasOwnProperty.call(leerFichas(), normalizarRut(rut));
}

/* ----------------------------------------------------------------------
   2. VALIDACIONES  (funciones puras: reciben un valor, devuelven mensaje)
      Devuelven "" cuando el valor es válido.
   ---------------------------------------------------------------------- */

/* --- RUT ------------------------------------------------------------- */
function normalizarRut(rut) {
  return String(rut || '').replace(/[.\-\s]/g, '').toUpperCase();
}

/** Calcula el dígito verificador por módulo 11. */
function calcularDv(cuerpo) {
  let suma = 0;
  let multiplicador = 2;
  for (let i = cuerpo.length - 1; i >= 0; i--) {
    suma += parseInt(cuerpo[i], 10) * multiplicador;
    multiplicador = (multiplicador === 7) ? 2 : multiplicador + 1;
  }
  const resto = 11 - (suma % 11);
  if (resto === 11) return '0';
  if (resto === 10) return 'K';
  return String(resto);
}

function validarRut(valor) {
  const limpio = normalizarRut(valor);
  if (limpio === '') return 'El RUT es obligatorio.';
  // Aviso específico para el caso en que el campo conserva texto anterior:
  // sin él, un RUT pegado sobre otro solo informa "formato inválido" y confunde.
  if (limpio.length > 9) return 'El RUT es demasiado largo. Borre el contenido del campo e ingréselo de nuevo.';
  if (!/^\d{7,8}[0-9K]$/.test(limpio)) return 'Formato inválido. Use 12345678-5 o 12.345.678-5.';
  const cuerpo = limpio.slice(0, -1);
  const dv = limpio.slice(-1);
  if (dv !== calcularDv(cuerpo)) return 'RUT inválido: el dígito verificador no corresponde.';
  return '';
}

/** Presenta el RUT con puntos y guion: 12.345.678-5 */
function formatearRut(valor) {
  const limpio = normalizarRut(valor);
  if (limpio.length < 2) return limpio;
  const cuerpo = limpio.slice(0, -1);
  const dv = limpio.slice(-1);
  return cuerpo.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + '-' + dv;
}

/* --- Nombres y apellidos --------------------------------------------- */
const RE_LETRAS = /^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[ '\-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$/;

function validarTextoPersona(valor, etiqueta) {
  const v = String(valor || '').trim();
  if (v === '') return 'El campo ' + etiqueta + ' es obligatorio.';
  if (v.length < 2 || v.length > 40) return etiqueta + ' debe tener entre 2 y 40 caracteres.';
  if (!RE_LETRAS.test(v)) return etiqueta + ' solo admite letras, espacios, guion y apóstrofe.';
  return '';
}

function validarNombres(valor)   { return validarTextoPersona(valor, 'Nombres'); }
function validarApellidos(valor) { return validarTextoPersona(valor, 'Apellidos'); }

/* --- Dirección -------------------------------------------------------- */
function validarDireccion(valor) {
  const v = String(valor || '').trim();
  if (v === '') return 'La dirección es obligatoria.';
  if (v.length < 5 || v.length > 80) return 'La dirección debe tener entre 5 y 80 caracteres.';
  if (!/^[A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ\s.,#°\-']+$/.test(v)) return 'La dirección contiene caracteres no permitidos.';
  if (!/[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]/.test(v)) return 'La dirección debe incluir el nombre de la calle.';
  return '';
}

/* --- Ciudad ----------------------------------------------------------- */
function validarCiudad(valor) {
  const v = String(valor || '').trim();
  if (v === '') return 'La ciudad es obligatoria.';
  if (v.length < 3 || v.length > 40) return 'La ciudad debe tener entre 3 y 40 caracteres.';
  if (!RE_LETRAS.test(v)) return 'La ciudad solo admite letras y espacios.';
  return '';
}

/* --- Teléfono (Chile) -------------------------------------------------- */
function normalizarTelefono(valor) {
  return String(valor || '').replace(/[\s()\-.]/g, '');
}

function validarTelefono(valor) {
  const v = normalizarTelefono(valor);
  if (v === '') return 'El teléfono es obligatorio.';
  if (/[A-Za-z]/.test(v)) return 'El teléfono solo admite dígitos.';
  if (!/^(\+?56)?[2-9]\d{8}$/.test(v)) {
    return 'Formato inválido. Use +56 9 1234 5678 (9 dígitos nacionales).';
  }
  return '';
}

/* --- Email ------------------------------------------------------------- */
function validarEmail(valor) {
  const v = String(valor || '').trim();
  if (v === '') return 'El correo electrónico es obligatorio.';
  if (v.length > 60) return 'El correo no puede superar 60 caracteres.';
  if (!/^[^\s@,;]+@[^\s@,;.]+(\.[^\s@,;.]+)+$/.test(v)) return 'Correo electrónico inválido. Ejemplo: nombre@correo.cl';
  return '';
}

/* --- Fecha de nacimiento ------------------------------------------------ */
function calcularEdad(fechaIso, hoy) {
  const ref = hoy || new Date();
  const f = new Date(fechaIso + 'T00:00:00');
  let edad = ref.getFullYear() - f.getFullYear();
  const m = ref.getMonth() - f.getMonth();
  if (m < 0 || (m === 0 && ref.getDate() < f.getDate())) edad--;
  return edad;
}

function validarFechaNacimiento(valor) {
  const v = String(valor || '').trim();
  if (v === '') return 'La fecha de nacimiento es obligatoria.';
  if (!/^\d{4}-\d{2}-\d{2}$/.test(v)) return 'Fecha inválida.';
  const f = new Date(v + 'T00:00:00');
  if (isNaN(f.getTime())) return 'Fecha inválida.';
  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  if (f > hoy) return 'La fecha de nacimiento no puede ser futura.';
  const edad = calcularEdad(v);
  if (edad > 120) return 'La edad no puede superar los 120 años.';
  return '';
}

/* --- Estado civil -------------------------------------------------------- */
const ESTADOS_CIVILES = ['Soltero/a', 'Casado/a', 'Conviviente civil', 'Divorciado/a', 'Viudo/a'];

function validarEstadoCivil(valor) {
  const v = String(valor || '').trim();
  if (v === '') return 'Debe seleccionar un estado civil.';
  if (ESTADOS_CIVILES.indexOf(v) === -1) return 'Estado civil no permitido.';
  return '';
}

/* --- Comentarios (opcional) ---------------------------------------------- */
function validarComentarios(valor) {
  const v = String(valor || '');
  if (v.length > 300) return 'Los comentarios no pueden superar los 300 caracteres.';
  if (/[<>]/.test(v)) return 'No se permiten los caracteres < ni > en los comentarios.';
  return '';
}

/* --- Apellido de búsqueda ------------------------------------------------- */
function validarBusqueda(valor) {
  const v = String(valor || '').trim();
  if (v === '') return 'Ingrese un apellido para buscar.';
  if (v.length < 2) return 'Ingrese al menos 2 caracteres.';
  if (!RE_LETRAS.test(v)) return 'El apellido solo admite letras y espacios.';
  return '';
}

/* Mapa campo -> validador. Es la tabla que recorre el botón Guardar. */
const VALIDADORES = {
  rut:              validarRut,
  nombres:          validarNombres,
  apellidos:        validarApellidos,
  direccion:        validarDireccion,
  ciudad:           validarCiudad,
  telefono:         validarTelefono,
  email:            validarEmail,
  fechaNacimiento:  validarFechaNacimiento,
  estadoCivil:      validarEstadoCivil,
  comentarios:      validarComentarios
};

/* ----------------------------------------------------------------------
   3. ENLACE CON EL DOM
   ---------------------------------------------------------------------- */
const $ = function (id) { return document.getElementById(id); };

const formulario   = $('fichaForm');
const formBusqueda = $('buscaForm');
const cajaResultados = $('resultados');
const errResumen   = $('errResumen');

function pintarError(campo, mensaje) {
  const input = $(campo);
  const spanError = $('err-' + campo);
  if (!input || !spanError) return;
  spanError.textContent = mensaje;
  input.classList.toggle('invalido', mensaje !== '');
  input.classList.toggle('valido', mensaje === '' && String(input.value).trim() !== '');
  input.setAttribute('aria-invalid', mensaje !== '' ? 'true' : 'false');
}

function validarCampo(campo) {
  const input = $(campo);
  if (!input) return '';
  const mensaje = VALIDADORES[campo](input.value);
  pintarError(campo, mensaje);
  return mensaje;
}

/** Valida el formulario completo. Devuelve un arreglo de campos con error. */
function validarFormulario() {
  const conError = [];
  Object.keys(VALIDADORES).forEach(function (campo) {
    if (validarCampo(campo) !== '') conError.push(campo);
  });
  return conError;
}

/* Validación en vivo: al salir del campo (blur) y al corregir (input). */
Object.keys(VALIDADORES).forEach(function (campo) {
  const input = $(campo);
  if (!input) return;
  input.addEventListener('blur', function () { validarCampo(campo); });
  input.addEventListener('input', function () {
    if (input.classList.contains('invalido')) validarCampo(campo);
  });
});

/* Al enfocar un RUT ya completo se selecciona todo su contenido, de modo que
   escribir lo reemplace en lugar de intentar agregarse al final. */
$('rut').addEventListener('focus', function () {
  if (validarRut(this.value) === '') this.select();
});

/* Formateo automático del RUT al salir del campo */
$('rut').addEventListener('blur', function () {
  const v = this.value.trim();
  if (v !== '' && validarRut(v) === '') this.value = formatearRut(v);
});

/* Contador de caracteres de comentarios */
$('comentarios').addEventListener('input', function () {
  $('contadorComentarios').textContent = this.value.length + '/300';
});

/* Mensajes emergentes */
let temporizadorToast = null;
function avisar(mensaje, tipo) {
  const toast = $('toast');
  toast.textContent = mensaje;
  toast.classList.toggle('toast--error', tipo === 'error');
  toast.hidden = false;
  clearTimeout(temporizadorToast);
  temporizadorToast = setTimeout(function () { toast.hidden = true; }, 3800);
}

function actualizarContador() {
  const total = Object.keys(leerFichas()).length;
  $('contadorFichas').textContent = total + (total === 1 ? ' ficha' : ' fichas');
}

/* ----------------------------------------------------------------------
   4. ACCIONES
   ---------------------------------------------------------------------- */

/* ---------- GUARDAR ---------- */
formulario.addEventListener('submit', function (evento) {
  evento.preventDefault();

  const conError = validarFormulario();

  if (conError.length > 0) {
    errResumen.textContent = 'No se guardó: hay ' + conError.length +
      (conError.length === 1 ? ' campo con error.' : ' campos con errores.');
    const primero = $(conError[0]);
    primero.focus();
    primero.scrollIntoView({ behavior: 'smooth', block: 'center' });
    avisar('Corrija los campos marcados en rojo', 'error');
    return;
  }

  errResumen.textContent = '';

  const clave  = normalizarRut($('rut').value);
  const fichas = leerFichas();

  if (Object.prototype.hasOwnProperty.call(fichas, clave)) {
    const anterior = fichas[clave];
    const deseaSobrescribir = window.confirm(
      'Ya existe una ficha registrada con el RUT ' + formatearRut(clave) + '\n' +
      'Paciente: ' + anterior.nombres + ' ' + anterior.apellidos + '\n\n' +
      '¿Desea sobrescribir el registro existente?'
    );
    if (!deseaSobrescribir) {
      avisar('Operación cancelada: el registro no fue modificado', 'error');
      return;
    }
  }

  const esNuevo = !Object.prototype.hasOwnProperty.call(fichas, clave);

  fichas[clave] = {
    rut:             formatearRut(clave),
    nombres:         $('nombres').value.trim(),
    apellidos:       $('apellidos').value.trim(),
    direccion:       $('direccion').value.trim(),
    ciudad:          $('ciudad').value.trim(),
    telefono:        $('telefono').value.trim(),
    email:           $('email').value.trim(),
    fechaNacimiento: $('fechaNacimiento').value,
    estadoCivil:     $('estadoCivil').value,
    comentarios:     $('comentarios').value.trim(),
    registradoEn:    new Date().toISOString()
  };

  if (!escribirFichas(fichas)) {
    avisar('Error: no se pudo guardar en el almacenamiento local', 'error');
    return;
  }

  actualizarContador();
  avisar(esNuevo ? 'Ficha guardada correctamente' : 'Ficha sobrescrita correctamente');
  limpiarFormulario(true);
});

/* ---------- LIMPIAR ---------- */
function formularioTieneDatos() {
  return Object.keys(VALIDADORES).some(function (campo) {
    return String($(campo).value).trim() !== '';
  });
}

function limpiarFormulario(silencioso) {
  formulario.reset();
  Object.keys(VALIDADORES).forEach(function (campo) {
    pintarError(campo, '');
    $(campo).classList.remove('valido', 'invalido');
    $(campo).removeAttribute('aria-invalid');
  });
  errResumen.textContent = '';
  $('contadorComentarios').textContent = '0/300';
  if (!silencioso) avisar('Formulario limpiado');
}

$('btnLimpiar').addEventListener('click', function () {
  if (!formularioTieneDatos()) {
    avisar('El formulario ya está vacío', 'error');
    return;
  }
  if (window.confirm('¿Desea limpiar todos los campos del formulario?\nLos datos no guardados se perderán.')) {
    limpiarFormulario(false);
    $('rut').focus();
  }
});

/* ---------- CERRAR ---------- */
$('btnCerrar').addEventListener('click', function () {
  const mensaje = formularioTieneDatos()
    ? 'Hay datos sin guardar en el formulario.\n¿Desea cerrar de todas formas?'
    : '¿Desea cerrar el formulario?';
  if (!window.confirm(mensaje)) return;

  limpiarFormulario(true);
  // El navegador solo permite window.close() en pestañas abiertas por script.
  // Si el cierre no ocurre, se muestra la pantalla de sesión cerrada (respaldo).
  window.close();
  setTimeout(function () {
    if (!window.closed) $('overlayCerrado').hidden = false;
  }, 250);
});

$('btnReabrir').addEventListener('click', function () {
  $('overlayCerrado').hidden = true;
  $('rut').focus();
});

/* ---------- BUSCAR POR APELLIDO ---------- */
function sinAcentos(texto) {
  return String(texto || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
}

function buscarPorApellido(termino) {
  const fichas = leerFichas();
  const aguja = sinAcentos(termino);
  return Object.keys(fichas)
    .map(function (k) { return fichas[k]; })
    .filter(function (f) { return sinAcentos(f.apellidos).indexOf(aguja) !== -1; })
    .sort(function (a, b) { return a.apellidos.localeCompare(b.apellidos, 'es'); });
}

function pintarResultados(lista, titulo) {
  if (lista.length === 0) {
    cajaResultados.innerHTML = '<p class="aviso" id="avisoResultados">Sin resultados: no existen fichas que coincidan con la búsqueda.</p>';
    return;
  }

  let html = '<div class="tabla-scroll"><table id="tablaResultados">' +
    '<caption>' + titulo + ' &mdash; ' + lista.length +
    (lista.length === 1 ? ' registro encontrado' : ' registros encontrados') + '</caption>' +
    '<thead><tr>' +
    '<th>RUT</th><th>Apellidos</th><th>Nombres</th><th>Ciudad</th>' +
    '<th>Teléfono</th><th>Email</th><th>F. Nac.</th><th>Estado civil</th><th></th>' +
    '</tr></thead><tbody>';

  lista.forEach(function (f) {
    html += '<tr>' +
      '<td>' + escapar(f.rut) + '</td>' +
      '<td>' + escapar(f.apellidos) + '</td>' +
      '<td>' + escapar(f.nombres) + '</td>' +
      '<td>' + escapar(f.ciudad) + '</td>' +
      '<td>' + escapar(f.telefono) + '</td>' +
      '<td>' + escapar(f.email) + '</td>' +
      '<td>' + escapar(f.fechaNacimiento) + '</td>' +
      '<td>' + escapar(f.estadoCivil) + '</td>' +
      '<td><button type="button" class="btn-mini" data-rut="' + escapar(normalizarRut(f.rut)) + '">Cargar</button></td>' +
      '</tr>';
  });

  html += '</tbody></table></div>';
  cajaResultados.innerHTML = html;
}

function escapar(texto) {
  return String(texto == null ? '' : texto)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

formBusqueda.addEventListener('submit', function (evento) {
  evento.preventDefault();
  const termino = $('buscaApellido').value;
  const mensaje = validarBusqueda(termino);
  pintarError('buscaApellido', mensaje);
  if (mensaje !== '') {
    cajaResultados.innerHTML = '';
    return;
  }
  const encontrados = buscarPorApellido(termino);
  pintarResultados(encontrados, 'Resultados para "' + escapar(termino.trim()) + '"');
});

$('buscaApellido').addEventListener('input', function () {
  if (this.classList.contains('invalido')) pintarError('buscaApellido', validarBusqueda(this.value));
});

$('btnVerTodos').addEventListener('click', function () {
  pintarError('buscaApellido', '');
  $('buscaApellido').value = '';
  const fichas = leerFichas();
  const todas = Object.keys(fichas).map(function (k) { return fichas[k]; })
    .sort(function (a, b) { return a.apellidos.localeCompare(b.apellidos, 'es'); });
  pintarResultados(todas, 'Todas las fichas registradas');
});

/* Cargar una ficha en el formulario desde la tabla de resultados */
cajaResultados.addEventListener('click', function (evento) {
  const boton = evento.target.closest('.btn-mini');
  if (!boton) return;
  const ficha = leerFichas()[boton.getAttribute('data-rut')];
  if (!ficha) return;
  Object.keys(VALIDADORES).forEach(function (campo) {
    $(campo).value = ficha[campo] != null ? ficha[campo] : '';
    pintarError(campo, '');
  });
  $('contadorComentarios').textContent = (ficha.comentarios || '').length + '/300';
  avisar('Ficha cargada. Modifique y presione Guardar para sobrescribir.');
  formulario.scrollIntoView({ behavior: 'smooth', block: 'start' });
  $('nombres').focus();
});

/* ---------- Inicio ---------- */
actualizarContador();

/* Exposición para pruebas automatizadas (verificación de caja blanca) */
window.FichaMedica = {
  validarRut: validarRut,
  calcularDv: calcularDv,
  formatearRut: formatearRut,
  normalizarRut: normalizarRut,
  validarNombres: validarNombres,
  validarApellidos: validarApellidos,
  validarDireccion: validarDireccion,
  validarCiudad: validarCiudad,
  validarTelefono: validarTelefono,
  validarEmail: validarEmail,
  validarFechaNacimiento: validarFechaNacimiento,
  validarEstadoCivil: validarEstadoCivil,
  validarComentarios: validarComentarios,
  validarBusqueda: validarBusqueda,
  buscarPorApellido: buscarPorApellido,
  existeFicha: existeFicha,
  leerFichas: leerFichas
};
