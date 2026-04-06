/**
 * CUADRE MENSUAL AUTOMÁTICO - Google Apps Script
 * Repositorio: bythegiox/botsitojacobo
 *
 * FLUJO:
 * 1. Duplica el archivo COMPLETO "CUADRE plantilla" (todas las pestañas, formato, datos)
 * 2. Renombra la copia a "Cuadre - {Mes} {Año}"
 * 3. Adapta las fórmulas QUERY con las fechas del nuevo mes
 * 4. Actualiza las fechas dd-mm en las tablas
 * 5. Crea/actualiza la hoja CONFIG con fecha inicio y fin
 *
 * Zona horaria: America/Caracas (Venezuela)
 */

// ─────────────────────────────────────────────
// CONFIGURACIÓN GLOBAL
// ─────────────────────────────────────────────
const CONFIG = {
  // ID del archivo plantilla (CUADRE plantilla)
  // https://docs.google.com/spreadsheets/d/12bkHCsanz9PPdQac5wFqwTXpti-o-0Ok4c4sbycRQJk/
  PLANTILLA_SS_ID: "12bkHCsanz9PPdQac5wFqwTXpti-o-0Ok4c4sbycRQJk",

  // URL del spreadsheet de historial (fuente de datos para IMPORTRANGE)
  HISTORIAL_URL: "https://docs.google.com/spreadsheets/d/15pGe3iaZNR1o9XjJaQKDFj6Gjb3Ul7boBevK9pHyuJ4",

  // Carpeta de Google Drive donde guardar las copias (null = misma carpeta que la plantilla)
  CARPETA_DESTINO_ID: null,

  // Nombre de la hoja CONFIG dentro de la copia
  CONFIG_HOJA: "CONFIG",

  // Meses en español
  MESES: [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
  ],

  // Zona horaria de Venezuela
  TIMEZONE: "America/Caracas"
};

// ─────────────────────────────────────────────
// MENÚ PRINCIPAL (se ejecuta desde la plantilla)
// ─────────────────────────────────────────────
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("⚙️ Cuadre Mensual")
    .addItem("📋 Generar Cuadre del Mes Actual", "generarCuadreActual")
    .addItem("📅 Generar Cuadre de Mes Específico", "generarCuadreMesEspecifico")
    .addSeparator()
    .addItem("🔁 Configurar Ejecución Automática (fin de mes)", "configurarTriggerAutomatico")
    .addItem("🗑️ Eliminar Trigger Automático", "eliminarTriggers")
    .addSeparator()
    .addItem("ℹ️ Ver Estado de Triggers", "verEstadoTriggers")
    .addToUi();
}

// ─────────────────────────────────────────────
// GENERAR CUADRE DEL MES ACTUAL
// ─────────────────────────────────────────────
function generarCuadreActual() {
  const ahora = obtenerFechaVenezuela();
  const mes  = ahora.getMonth() + 1; // 1-12
  const anio = ahora.getFullYear();
  generarCuadre(mes, anio);
}

// ─────────────────────────────────────────────
// GENERAR CUADRE DE MES ESPECÍFICO (con diálogo)
// ─────────────────────────────────────────────
function generarCuadreMesEspecifico() {
  const ui = SpreadsheetApp.getUi();

  const respMes = ui.prompt(
    "📅 Generar Cuadre Específico",
    "Ingresa el número del mes (1-12):",
    ui.ButtonSet.OK_CANCEL
  );
  if (respMes.getSelectedButton() !== ui.Button.OK) return;
  const mes = parseInt(respMes.getResponseText().trim());
  if (isNaN(mes) || mes < 1 || mes > 12) {
    ui.alert("❌ Mes inválido. Debe ser un número entre 1 y 12.");
    return;
  }

  const respAnio = ui.prompt(
    "📅 Generar Cuadre Específico",
    "Ingresa el año (ej: 2026):",
    ui.ButtonSet.OK_CANCEL
  );
  if (respAnio.getSelectedButton() !== ui.Button.OK) return;
  const anio = parseInt(respAnio.getResponseText().trim());
  if (isNaN(anio) || anio < 2020 || anio > 2100) {
    ui.alert("❌ Año inválido. Debe ser un número entre 2020 y 2100.");
    return;
  }

  generarCuadre(mes, anio);
}

// ─────────────────────────────────────────────
// NÚCLEO: DUPLICA EL ARCHIVO Y ADAPTA FECHAS
// ─────────────────────────────────────────────
function generarCuadre(mes, anio) {
  const ui = SpreadsheetApp.getUi();
  const nombreMes = CONFIG.MESES[mes - 1];
  const nombreArchivo = `Cuadre - ${nombreMes} ${anio}`;

  // ── 1. Verificar que la plantilla existe
  let archivoPlantilla;
  try {
    archivoPlantilla = DriveApp.getFileById(CONFIG.PLANTILLA_SS_ID);
  } catch (e) {
    ui.alert(
      "❌ Plantilla no encontrada",
      `No se pudo acceder al archivo plantilla.\nID: ${CONFIG.PLANTILLA_SS_ID}\n\nError: ${e.message}`,
      ui.ButtonSet.OK
    );
    return;
  }

  // ── 2. Verificar si ya existe un archivo con ese nombre en la misma carpeta
  const carpetaDestino = obtenerCarpetaDestino(archivoPlantilla);
  const archivosExistentes = carpetaDestino.getFilesByName(nombreArchivo);
  if (archivosExistentes.hasNext()) {
    const resp = ui.alert(
      "⚠️ Archivo ya existe",
      `Ya existe un archivo llamado "${nombreArchivo}" en la carpeta.\n\n¿Deseas crear uno nuevo de todas formas? (el anterior no se borrará)`,
      ui.ButtonSet.YES_NO
    );
    if (resp !== ui.Button.YES) return;
  }

  // ── 3. DUPLICAR el archivo completo (todas las pestañas, formato, datos, todo)
  ui.alert("⏳ Generando...", `Duplicando plantilla y adaptando fechas para ${nombreMes} ${anio}...\n\nEsto puede tomar unos segundos. Presiona Aceptar y espera.`, ui.ButtonSet.OK);

  let archivoCopia;
  if (CONFIG.CARPETA_DESTINO_ID) {
    const carpeta = DriveApp.getFolderById(CONFIG.CARPETA_DESTINO_ID);
    archivoCopia = archivoPlantilla.makeCopy(nombreArchivo, carpeta);
  } else {
    archivoCopia = archivoPlantilla.makeCopy(nombreArchivo, carpetaDestino);
  }

  // ── 4. Abrir la copia como Spreadsheet
  const ssCopia = SpreadsheetApp.openById(archivoCopia.getId());

  // ── 5. Calcular fechas del mes
  const diasEnMes = obtenerDiasEnMes(mes, anio);
  const fechaInicio = formatearFechaDDMM(1, mes);
  const fechaFin    = formatearFechaDDMM(diasEnMes, mes);
  const fechaInicioQuery = `${anio}-${padDos(mes)}-01`;
  const fechaFinQuery    = `${anio}-${padDos(mes)}-${padDos(diasEnMes)}`;

  // ── 6. Recorrer TODAS las pestañas de la copia y adaptar
  const hojas = ssCopia.getSheets();
  let totalFormulas = 0;
  let totalFechas   = 0;

  for (const hoja of hojas) {
    totalFormulas += actualizarFormulas(hoja, fechaInicioQuery, fechaFinQuery);
    totalFechas   += actualizarFechasTabla(hoja, mes, anio, diasEnMes);
  }

  // ── 7. Crear/actualizar hoja CONFIG en la copia
  actualizarHojaConfig(ssCopia, fechaInicio, fechaFin, mes, anio);

  // ── 8. Éxito - mostrar resumen con enlace al nuevo archivo
  const urlCopia = ssCopia.getUrl();
  ui.alert(
    "✅ Cuadre Generado",
    `Se duplicó la plantilla y se creó:\n"${nombreArchivo}"\n\n` +
    `📅 Período: ${fechaInicio} al ${fechaFin}\n` +
    `📆 Días en el mes: ${diasEnMes}${esBisiesto(anio) && mes === 2 ? " (año bisiesto)" : ""}\n` +
    `📊 Fórmulas adaptadas: ${totalFormulas}\n` +
    `📝 Fechas dd-mm actualizadas: ${totalFechas}\n\n` +
    `🔗 Abrir archivo:\n${urlCopia}`,
    ui.ButtonSet.OK
  );

  Logger.log(`✅ Cuadre generado: ${nombreArchivo} | ${fechaInicioQuery} → ${fechaFinQuery} | URL: ${urlCopia}`);
}

// ─────────────────────────────────────────────
// ACTUALIZAR HOJA CONFIG EN LA COPIA
// ─────────────────────────────────────────────
function actualizarHojaConfig(ss, fechaInicio, fechaFin, mes, anio) {
  let hojaConfig = ss.getSheetByName(CONFIG.CONFIG_HOJA);

  if (!hojaConfig) {
    hojaConfig = ss.insertSheet(CONFIG.CONFIG_HOJA);
  }

  // Encabezados
  hojaConfig.getRange("A1").setValue("Fecha Inicio (dd-mm)");
  hojaConfig.getRange("A2").setValue("Fecha Fin (dd-mm)");
  hojaConfig.getRange("A3").setValue("Mes");
  hojaConfig.getRange("A4").setValue("Año");
  hojaConfig.getRange("A5").setValue("Generado el");
  hojaConfig.getRange("A1:A5").setFontWeight("bold");

  // Valores
  hojaConfig.getRange("B1").setValue(fechaInicio);
  hojaConfig.getRange("B2").setValue(fechaFin);
  hojaConfig.getRange("B3").setValue(CONFIG.MESES[mes - 1]);
  hojaConfig.getRange("B4").setValue(anio);
  hojaConfig.getRange("B5").setValue(new Date());
}

// ─────────────────────────────────────────────
// ACTUALIZAR FÓRMULAS QUERY EN UNA HOJA
// ─────────────────────────────────────────────
function actualizarFormulas(hoja, fechaInicioQuery, fechaFinQuery) {
  const totalFilas = hoja.getLastRow();
  const totalCols  = hoja.getLastColumn();
  if (totalFilas === 0 || totalCols === 0) return 0;

  const rango    = hoja.getRange(1, 1, totalFilas, totalCols);
  const formulas = rango.getFormulas();
  let cambios = 0;

  for (let f = 0; f < formulas.length; f++) {
    for (let c = 0; c < formulas[f].length; c++) {
      const formula = formulas[f][c];
      if (!formula) continue;

      const nuevaFormula = adaptarFormula(formula, fechaInicioQuery, fechaFinQuery);
      if (nuevaFormula !== formula) {
        hoja.getRange(f + 1, c + 1).setFormula(nuevaFormula);
        cambios++;
      }
    }
  }

  return cambios;
}

/**
 * Adapta una fórmula reemplazando fechas date 'YYYY-MM-DD'
 * y month(date ...) / year(date ...)
 */
function adaptarFormula(formula, fechaInicioQuery, fechaFinQuery) {
  let nueva = formula;

  // A) Reemplazar date 'YYYY-MM-DD' → día 01 = inicio, otro día = fin
  nueva = nueva.replace(/date\s*'(\d{4}-\d{2}-\d{2})'/gi, function(match, fecha) {
    const dia = parseInt(fecha.split("-")[2]);
    return dia === 1 ? `date '${fechaInicioQuery}'` : `date '${fechaFinQuery}'`;
  });

  // B) month(date 'YYYY-MM-DD') → mes correcto
  nueva = nueva.replace(
    /month\s*\(\s*date\s*'(\d{4}-\d{2}-\d{2})'\s*\)/gi,
    `month(date '${fechaFinQuery}')`
  );

  // C) year(date 'YYYY-MM-DD') → año correcto
  nueva = nueva.replace(
    /year\s*\(\s*date\s*'(\d{4}-\d{2}-\d{2})'\s*\)/gi,
    `year(date '${fechaFinQuery}')`
  );

  return nueva;
}

// ─────────────────────────────────────────────
// ACTUALIZAR FECHAS dd-mm EN TABLAS
// ─────────────────────────────────────────────
function actualizarFechasTabla(hoja, mes, anio, diasEnMes) {
  const totalFilas = hoja.getLastRow();
  const totalCols  = hoja.getLastColumn();
  if (totalFilas === 0 || totalCols === 0) return 0;

  const rango    = hoja.getRange(1, 1, totalFilas, totalCols);
  const valores  = rango.getValues();
  const formulas = rango.getFormulas();
  const regexFechaDDMM = /^(\d{1,2})-(\d{1,2})$/;
  let cambios = 0;

  for (let f = 0; f < valores.length; f++) {
    for (let c = 0; c < valores[f].length; c++) {
      if (formulas[f][c]) continue; // Saltar celdas con fórmula

      const strVal = String(valores[f][c]).trim();
      const match  = strVal.match(regexFechaDDMM);
      if (!match) continue;

      const dia     = parseInt(match[1]);
      const mesOrig = parseInt(match[2]);

      if (dia < 1 || dia > 31) continue;
      if (mesOrig === mes) continue; // Ya tiene el mes correcto

      if (dia > diasEnMes) {
        // Día no existe en el nuevo mes → limpiar celda
        hoja.getRange(f + 1, c + 1).setValue("");
      } else {
        hoja.getRange(f + 1, c + 1).setValue(`${padDos(dia)}-${padDos(mes)}`);
      }
      cambios++;
    }
  }

  return cambios;
}

// ─────────────────────────────────────────────
// TRIGGER AUTOMÁTICO - FIN DE MES
// ─────────────────────────────────────────────
function configurarTriggerAutomatico() {
  const ui = SpreadsheetApp.getUi();

  eliminarTriggersPorFuncion("ejecutarCuadreAutomatico");

  // Ejecutar días 28-31 a las 23:00 VE; solo actúa si es el último día del mes
  [28, 29, 30, 31].forEach(dia => {
    ScriptApp.newTrigger("ejecutarCuadreAutomatico")
      .timeBased()
      .onMonthDay(dia)
      .atHour(23)
      .inTimezone(CONFIG.TIMEZONE)
      .create();
  });

  ui.alert(
    "✅ Trigger Configurado",
    "Ejecución automática configurada para el último día de cada mes a las 23:00 (hora Venezuela).\n\n" +
    "El script detectará el último día real del mes automáticamente.",
    ui.ButtonSet.OK
  );
}

function ejecutarCuadreAutomatico() {
  const ahora     = obtenerFechaVenezuela();
  const mes       = ahora.getMonth() + 1;
  const anio      = ahora.getFullYear();
  const dia       = ahora.getDate();
  const diasEnMes = obtenerDiasEnMes(mes, anio);

  // Solo ejecutar si hoy es el último día del mes
  if (dia === diasEnMes) {
    // Generar cuadre del MES SIGUIENTE
    let mesSiguiente = mes + 1;
    let anioSiguiente = anio;
    if (mesSiguiente > 12) {
      mesSiguiente = 1;
      anioSiguiente++;
    }
    generarCuadreSilencioso(mesSiguiente, anioSiguiente);
  }
}

/**
 * Versión sin UI para ejecución automática por trigger
 */
function generarCuadreSilencioso(mes, anio) {
  const nombreMes     = CONFIG.MESES[mes - 1];
  const nombreArchivo = `Cuadre - ${nombreMes} ${anio}`;

  const archivoPlantilla = DriveApp.getFileById(CONFIG.PLANTILLA_SS_ID);
  const carpetaDestino   = obtenerCarpetaDestino(archivoPlantilla);
  const archivoCopia     = archivoPlantilla.makeCopy(nombreArchivo, carpetaDestino);
  const ssCopia          = SpreadsheetApp.openById(archivoCopia.getId());

  const diasEnMes        = obtenerDiasEnMes(mes, anio);
  const fechaInicio      = formatearFechaDDMM(1, mes);
  const fechaFin         = formatearFechaDDMM(diasEnMes, mes);
  const fechaInicioQuery = `${anio}-${padDos(mes)}-01`;
  const fechaFinQuery    = `${anio}-${padDos(mes)}-${padDos(diasEnMes)}`;

  for (const hoja of ssCopia.getSheets()) {
    actualizarFormulas(hoja, fechaInicioQuery, fechaFinQuery);
    actualizarFechasTabla(hoja, mes, anio, diasEnMes);
  }

  actualizarHojaConfig(ssCopia, fechaInicio, fechaFin, mes, anio);

  Logger.log(`✅ Cuadre automático: ${nombreArchivo} | URL: ${ssCopia.getUrl()}`);
}

function eliminarTriggers() {
  const ui = SpreadsheetApp.getUi();
  const resp = ui.alert(
    "🗑️ Eliminar Triggers",
    "¿Eliminar todos los triggers automáticos?",
    ui.ButtonSet.YES_NO
  );
  if (resp !== ui.Button.YES) return;

  eliminarTriggersPorFuncion("ejecutarCuadreAutomatico");
  ui.alert("✅ Triggers eliminados.");
}

function eliminarTriggersPorFuncion(nombreFuncion) {
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === nombreFuncion) {
      ScriptApp.deleteTrigger(trigger);
    }
  });
}

function verEstadoTriggers() {
  const ui = SpreadsheetApp.getUi();
  const triggers = ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === "ejecutarCuadreAutomatico");

  if (triggers.length === 0) {
    ui.alert("ℹ️ No hay triggers automáticos configurados.");
  } else {
    const info = triggers.map(t =>
      `• ${t.getHandlerFunction()} | ${t.getEventType()}`
    ).join("\n");
    ui.alert("ℹ️ Triggers Activos", `${triggers.length} trigger(s):\n\n${info}`, ui.ButtonSet.OK);
  }
}

// ─────────────────────────────────────────────
// UTILIDADES
// ─────────────────────────────────────────────

function obtenerFechaVenezuela() {
  const ahora    = new Date();
  const strFecha = Utilities.formatDate(ahora, CONFIG.TIMEZONE, "yyyy-MM-dd");
  const partes   = strFecha.split("-");
  return new Date(parseInt(partes[0]), parseInt(partes[1]) - 1, parseInt(partes[2]));
}

/** Obtiene la carpeta donde está la plantilla (o la configurada) */
function obtenerCarpetaDestino(archivoPlantilla) {
  if (CONFIG.CARPETA_DESTINO_ID) {
    return DriveApp.getFolderById(CONFIG.CARPETA_DESTINO_ID);
  }
  const carpetas = archivoPlantilla.getParents();
  return carpetas.hasNext() ? carpetas.next() : DriveApp.getRootFolder();
}

function obtenerDiasEnMes(mes, anio) {
  return new Date(anio, mes, 0).getDate();
}

function esBisiesto(anio) {
  return (anio % 4 === 0 && anio % 100 !== 0) || (anio % 400 === 0);
}

function formatearFechaDDMM(dia, mes) {
  return `${padDos(dia)}-${padDos(mes)}`;
}

function padDos(n) {
  return String(n).padStart(2, "0");
}
