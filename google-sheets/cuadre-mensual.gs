/**
 * CUADRE MENSUAL AUTOMÁTICO - Google Apps Script
 * Repositorio: bythegiox/botsitojacobo
 *
 * Genera pestañas mensuales de cuadre copiando la plantilla,
 * actualizando fórmulas QUERY y fechas dd-mm en tablas.
 * Zona horaria: America/Caracas (Venezuela)
 */

// ─────────────────────────────────────────────
// CONFIGURACIÓN GLOBAL
// ─────────────────────────────────────────────
const CONFIG = {
  // URL del spreadsheet de historial (fuente de datos)
  HISTORIAL_URL: "https://docs.google.com/spreadsheets/d/15pGe3iaZNR1o9XjJaQKDFj6Gjb3Ul7boBevK9pHyuJ4",

  // Nombre(s) posibles de la hoja plantilla (en orden de prioridad)
  PLANTILLA_NOMBRES: ["CUADRE MARZO", "CUADRE plantilla", "PLANTILLA", "CUADRE TEMPLATE"],

  // Prefijo de las hojas generadas
  PREFIJO_HOJA: "Cuadre - ",

  // Nombre de la hoja CONFIG
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
// MENÚ PRINCIPAL
// ─────────────────────────────────────────────
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("⚙️ Cuadre Mensual")
    .addItem("📋 Generar Cuadre Actual", "generarCuadreActual")
    .addItem("📅 Generar Cuadre de Mes Específico", "generarCuadreMesEspecifico")
    .addSeparator()
    .addItem("🔁 Configurar Ejecución Automática (fin de mes)", "configurarTriggerAutomatico")
    .addItem("🗑️ Eliminar Trigger Automático", "eliminarTriggers")
    .addSeparator()
    .addItem("ℹ️ Ver Estado de Triggers", "verEstadoTriggers")
    .addToUi();
}

// ─────────────────────────────────────────────
// FUNCIÓN PRINCIPAL - GENERAR CUADRE ACTUAL
// ─────────────────────────────────────────────
function generarCuadreActual() {
  const ahora = obtenerFechaVenezuela();
  const mes = ahora.getMonth() + 1;   // 1-12
  const anio = ahora.getFullYear();

  Logger.log(`Generando cuadre para: ${CONFIG.MESES[mes - 1]} ${anio}`);
  generarCuadre(mes, anio);
}

// ─────────────────────────────────────────────
// GENERAR CUADRE PARA MES ESPECÍFICO (con UI)
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
// NÚCLEO: GENERA EL CUADRE
// ─────────────────────────────────────────────
function generarCuadre(mes, anio) {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // ── 1. Validar plantilla
  const plantilla = obtenerHojaPlantilla(ss);
  if (!plantilla) {
    ui.alert(
      "❌ Plantilla no encontrada",
      `No se encontró ninguna hoja con los nombres: ${CONFIG.PLANTILLA_NOMBRES.join(", ")}\n\nAsegúrate de que la hoja plantilla exista con uno de esos nombres.`,
      ui.ButtonSet.OK
    );
    return;
  }

  // ── 2. Nombre de la nueva hoja
  const nombreMes = CONFIG.MESES[mes - 1];
  const nombreHoja = `${CONFIG.PREFIJO_HOJA}${nombreMes} ${anio}`;

  // ── 3. Verificar duplicado
  if (ss.getSheetByName(nombreHoja)) {
    const resp = ui.alert(
      "⚠️ Hoja ya existe",
      `La hoja "${nombreHoja}" ya existe.\n¿Deseas sobreescribirla?`,
      ui.ButtonSet.YES_NO
    );
    if (resp !== ui.Button.YES) return;
    ss.deleteSheet(ss.getSheetByName(nombreHoja));
  }

  // ── 4. Calcular fechas del mes
  const diasEnMes = obtenerDiasEnMes(mes, anio);
  const fechaInicio = formatearFechaDDMM(1, mes);
  const fechaFin    = formatearFechaDDMM(diasEnMes, mes);

  // Formato YYYY-MM-DD para las QUERY
  const fechaInicioQuery = `${anio}-${padDos(mes)}-01`;
  const fechaFinQuery    = `${anio}-${padDos(mes)}-${padDos(diasEnMes)}`;

  // ── 5. Copiar plantilla
  const nuevaHoja = plantilla.copyTo(ss);
  nuevaHoja.setName(nombreHoja);

  // Mover la nueva hoja al final (antes de CONFIG si existe)
  const hojaConfig = ss.getSheetByName(CONFIG.CONFIG_HOJA);
  if (hojaConfig) {
    ss.moveActiveSheet(ss.getSheets().length - 1);
  }

  // ── 6. Actualizar/crear hoja CONFIG
  actualizarHojaConfig(ss, fechaInicio, fechaFin);

  // ── 7. Actualizar fórmulas QUERY en la nueva hoja
  actualizarFormulas(nuevaHoja, fechaInicioQuery, fechaFinQuery);

  // ── 8. Actualizar fechas dd-mm en tablas
  actualizarFechasTabla(nuevaHoja, mes, anio, diasEnMes);

  // ── 9. Éxito
  ss.setActiveSheet(nuevaHoja);
  ui.alert(
    "✅ Cuadre Generado",
    `Se creó correctamente la hoja:\n"${nombreHoja}"\n\n` +
    `📅 Período: ${fechaInicio.replace("-", "/")} al ${fechaFin.replace("-", "/")}\n` +
    `📆 Días en el mes: ${diasEnMes}${esBisiesto(anio) && mes === 2 ? " (año bisiesto)" : ""}`,
    ui.ButtonSet.OK
  );

  Logger.log(`✅ Cuadre generado: ${nombreHoja} | ${fechaInicioQuery} → ${fechaFinQuery}`);
}

// ─────────────────────────────────────────────
// ACTUALIZAR HOJA CONFIG
// ─────────────────────────────────────────────
function actualizarHojaConfig(ss, fechaInicio, fechaFin) {
  let hojaConfig = ss.getSheetByName(CONFIG.CONFIG_HOJA);

  if (!hojaConfig) {
    hojaConfig = ss.insertSheet(CONFIG.CONFIG_HOJA);
    // Encabezados básicos
    hojaConfig.getRange("A1").setValue("Fecha Inicio (dd-mm)");
    hojaConfig.getRange("A2").setValue("Fecha Fin (dd-mm)");
    hojaConfig.getRange("A3").setValue("Última Actualización");
    hojaConfig.getRange("A1:A3").setFontWeight("bold");
  }

  hojaConfig.getRange("B1").setValue(fechaInicio);
  hojaConfig.getRange("B2").setValue(fechaFin);
  hojaConfig.getRange("B3").setValue(new Date());

  Logger.log(`CONFIG actualizado: B1=${fechaInicio}, B2=${fechaFin}`);
}

// ─────────────────────────────────────────────
// ACTUALIZAR FÓRMULAS QUERY
// ─────────────────────────────────────────────
function actualizarFormulas(hoja, fechaInicioQuery, fechaFinQuery) {
  const totalFilas = hoja.getLastRow();
  const totalCols  = hoja.getLastColumn();
  if (totalFilas === 0 || totalCols === 0) return;

  const rango = hoja.getRange(1, 1, totalFilas, totalCols);
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
        Logger.log(`Fórmula actualizada en (${f + 1},${c + 1})`);
      }
    }
  }

  Logger.log(`Total fórmulas actualizadas: ${cambios}`);
}

/**
 * Adapta una fórmula reemplazando fechas date 'YYYY-MM-DD' y month(date ...) / year(date ...)
 */
function adaptarFormula(formula, fechaInicioQuery, fechaFinQuery) {
  let nueva = formula;

  // ── A) Reemplazar patrones date 'YYYY-MM-DD' dentro de QUERY strings
  // Captura cualquier date 'AAAA-MM-DD' y determina si es inicio (día 01) o fin
  nueva = nueva.replace(/date\s*'(\d{4}-\d{2}-\d{2})'/gi, function(match, fecha) {
    const partes = fecha.split("-");
    const dia = parseInt(partes[2]);
    if (dia === 1) {
      return `date '${fechaInicioQuery}'`;
    } else {
      return `date '${fechaFinQuery}'`;
    }
  });

  // ── B) Reemplazar month(date 'YYYY-MM-DD') → mes correcto
  nueva = nueva.replace(
    /month\s*\(\s*date\s*'(\d{4}-\d{2}-\d{2})'\s*\)/gi,
    `month(date '${fechaFinQuery}')`
  );

  // ── C) Reemplazar year(date 'YYYY-MM-DD') → año correcto
  nueva = nueva.replace(
    /year\s*\(\s*date\s*'(\d{4}-\d{2}-\d{2})'\s*\)/gi,
    `year(date '${fechaFinQuery}')`
  );

  return nueva;
}

// ─────────────────────────────────────────────
// ACTUALIZAR FECHAS dd-mm EN TABLAS
// ─────────────────────────────────────────────
/**
 * Busca celdas con valores en formato "DD-MM" (01-03, 15-03, etc.)
 * y las reemplaza por el nuevo mes (01-04, 15-04, etc.)
 * También elimina filas de días que no existen en el nuevo mes.
 */
function actualizarFechasTabla(hoja, mes, anio, diasEnMes) {
  const totalFilas = hoja.getLastRow();
  const totalCols  = hoja.getLastColumn();
  if (totalFilas === 0 || totalCols === 0) return;

  const rango  = hoja.getRange(1, 1, totalFilas, totalCols);
  const valores = rango.getValues();
  const formulas = rango.getFormulas();

  const regexFechaDDMM = /^(\d{2})-(\d{2})$/;
  let cambiosFechas = 0;

  for (let f = 0; f < valores.length; f++) {
    for (let c = 0; c < valores[f].length; c++) {
      // Saltar celdas con fórmula (ya fueron procesadas)
      if (formulas[f][c]) continue;

      const valor = valores[f][c];
      if (typeof valor !== "string" && typeof valor !== "number") continue;

      const strVal = String(valor).trim();
      const match  = strVal.match(regexFechaDDMM);
      if (!match) continue;

      const dia    = parseInt(match[1]);
      const mesOrig = parseInt(match[2]);

      // Solo procesar si parece una fecha de día válido (1-31) y mes anterior
      if (dia < 1 || dia > 31) continue;
      if (mesOrig === mes) continue; // Ya está en el mes correcto

      if (dia > diasEnMes) {
        // Día no existe en el nuevo mes → limpiar celda
        hoja.getRange(f + 1, c + 1).setValue("");
        cambiosFechas++;
      } else {
        // Reemplazar con nueva fecha
        const nuevaFecha = `${padDos(dia)}-${padDos(mes)}`;
        hoja.getRange(f + 1, c + 1).setValue(nuevaFecha);
        cambiosFechas++;
      }
    }
  }

  Logger.log(`Fechas dd-mm actualizadas: ${cambiosFechas}`);
}

// ─────────────────────────────────────────────
// TRIGGER AUTOMÁTICO - FIN DE MES
// ─────────────────────────────────────────────
function configurarTriggerAutomatico() {
  const ui = SpreadsheetApp.getUi();

  // Eliminar triggers existentes de esta función para evitar duplicados
  eliminarTriggersPorFuncion("ejecutarCuadreAutomatico");

  // Crear trigger mensual: se ejecuta el último día del mes a las 23:00 VE
  // Apps Script no tiene trigger "último día del mes", usamos día 28 como
  // mínimo común y verificamos en la función si es el último día.
  ScriptApp.newTrigger("ejecutarCuadreAutomatico")
    .timeBased()
    .onMonthDay(28)
    .atHour(23)
    .inTimezone(CONFIG.TIMEZONE)
    .create();

  // También crear uno para días 29, 30, 31 para cubrir todos los meses
  ScriptApp.newTrigger("ejecutarCuadreAutomatico")
    .timeBased()
    .onMonthDay(29)
    .atHour(23)
    .inTimezone(CONFIG.TIMEZONE)
    .create();

  ScriptApp.newTrigger("ejecutarCuadreAutomatico")
    .timeBased()
    .onMonthDay(30)
    .atHour(23)
    .inTimezone(CONFIG.TIMEZONE)
    .create();

  ScriptApp.newTrigger("ejecutarCuadreAutomatico")
    .timeBased()
    .onMonthDay(31)
    .atHour(23)
    .inTimezone(CONFIG.TIMEZONE)
    .create();

  ui.alert(
    "✅ Trigger Configurado",
    "Se configurará la ejecución automática al final de cada mes (días 28-31 a las 23:00 hora Venezuela).\n\n" +
    "El script detectará automáticamente el último día del mes y solo ejecutará una vez por mes.",
    ui.ButtonSet.OK
  );
}

/**
 * Función ejecutada por el trigger automático.
 * Solo genera el cuadre si hoy es el último día del mes.
 */
function ejecutarCuadreAutomatico() {
  const ahora = obtenerFechaVenezuela();
  const mes   = ahora.getMonth() + 1;
  const anio  = ahora.getFullYear();
  const dia   = ahora.getDate();
  const diasEnMes = obtenerDiasEnMes(mes, anio);

  if (dia === diasEnMes) {
    Logger.log(`Trigger automático: ejecutando cuadre para ${CONFIG.MESES[mes - 1]} ${anio}`);
    generarCuadre(mes, anio);
  } else {
    Logger.log(`Trigger automático: hoy es día ${dia}, el mes tiene ${diasEnMes} días. No es el último día, omitiendo.`);
  }
}

function eliminarTriggers() {
  const ui = SpreadsheetApp.getUi();
  const resp = ui.alert(
    "🗑️ Eliminar Triggers",
    "¿Estás seguro de que deseas eliminar todos los triggers automáticos de cuadre mensual?",
    ui.ButtonSet.YES_NO
  );
  if (resp !== ui.Button.YES) return;

  eliminarTriggersPorFuncion("ejecutarCuadreAutomatico");
  ui.alert("✅ Todos los triggers automáticos han sido eliminados.");
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
    ui.alert("ℹ️ Estado de Triggers", "No hay triggers automáticos configurados.", ui.ButtonSet.OK);
  } else {
    const info = triggers.map(t =>
      `• Función: ${t.getHandlerFunction()} | Tipo: ${t.getEventType()}`
    ).join("\n");
    ui.alert("ℹ️ Triggers Activos", `Se encontraron ${triggers.length} trigger(s):\n\n${info}`, ui.ButtonSet.OK);
  }
}

// ─────────────────────────────────────────────
// UTILIDADES
// ─────────────────────────────────────────────

/** Obtiene la fecha actual en la zona horaria de Venezuela */
function obtenerFechaVenezuela() {
  const ahora = new Date();
  const strFecha = Utilities.formatDate(ahora, CONFIG.TIMEZONE, "yyyy-MM-dd");
  const partes = strFecha.split("-");
  return new Date(parseInt(partes[0]), parseInt(partes[1]) - 1, parseInt(partes[2]));
}

/** Retorna la hoja plantilla buscando por nombre en orden de prioridad */
function obtenerHojaPlantilla(ss) {
  for (const nombre of CONFIG.PLANTILLA_NOMBRES) {
    const hoja = ss.getSheetByName(nombre);
    if (hoja) return hoja;
  }
  return null;
}

/** Calcula cuántos días tiene un mes (con soporte de año bisiesto) */
function obtenerDiasEnMes(mes, anio) {
  // new Date(anio, mes, 0) = último día del mes (mes es 1-indexado, pero Date usa 0-indexado)
  return new Date(anio, mes, 0).getDate();
}

/** Verifica si un año es bisiesto */
function esBisiesto(anio) {
  return (anio % 4 === 0 && anio % 100 !== 0) || (anio % 400 === 0);
}

/** Formatea fecha como "DD-MM" */
function formatearFechaDDMM(dia, mes) {
  return `${padDos(dia)}-${padDos(mes)}`;
}

/** Pad de 2 dígitos */
function padDos(n) {
  return String(n).padStart(2, "0");
}
