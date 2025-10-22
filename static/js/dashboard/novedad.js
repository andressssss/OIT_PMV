/**
 * @module novedadModule
 * @description Gestiona el detalle, documentos y acciones de una novedad (implementación Singleton con Revealing Module Pattern).
 * @version 1.1.0
 * @author
 *   @name Andrés Sanabria
 *   @date 2025-10-21
 * @last_update 2025-10-21
 */

import {
  $,
  hideSpinner,
  resetForm,
  showSpinner,
  fetchData,
  setText,
  setFormDisabled,
  csrfToken,
  toastSuccess,
  toastError,
} from "../utils.js";

const novedadModule = (() => {
  // === Estado interno ===
  /** @type {object|null} instancia única del módulo */
  let instance = null;
  let initialized = false;

  // === SELECTORES ===
  /** @type {object} Referencias a elementos del DOM */
  const el = {
    codigo: $("#detalle-codigo"),
    tipo: $("#detalle-tipo"),
    estado: $("#detalle-estado"),
    fecha: $("#detalle-fecha"),
    cierre: $("#detalle-cierre"),
    responsable: $("#detalle-responsable"),
    usuario: $("#detalle-usuario"),
    descripcion: $("#detalle-descripcion"),
    contenedorDocumentos: $("#contenedor-documentos"),
    listaAcciones: $("#lista-acciones"),
    btnGuardarAccion: $("#btn-guardar-accion"),
    formNuevaAccion: $("#form-nueva-accion"),
    modalNuevaAccion: $("#modalNuevaAccion"),
  };

  // === ENDPOINTS ===
  /** @type {string} ID de la novedad actual */
  const novedadId = window.location.pathname.split("/").filter(Boolean).pop();
  const BASE_URL = "/api/dashboard/novedades/";

  /** @type {object} Endpoints API */
  const ENDPOINTS = {
    detalle: `${BASE_URL}${novedadId}/detalle/`,
    documentos: `${BASE_URL}${novedadId}/documentos/`,
    acciones: `${BASE_URL}${novedadId}/acciones/`,
    crearAccion: `${BASE_URL}${novedadId}/acciones/create/`,
    crearDocumento: `${BASE_URL}${novedadId}/documentos/create/`,
  };

  // === MÉTODOS PRIVADOS ===

  /**
   * Devuelve una clase de color según el estado.
   * @private
   * @param {string} estado - Estado actual
   * @returns {string} Clase CSS correspondiente
   */
  const _estadoColor = (estado) => {
    const map = {
      pendiente: "bg-warning text-dark",
      gestion: "bg-primary",
      cerrada: "bg-success",
      cancelada: "bg-danger",
    };
    return map[estado] || "bg-secondary";
  };

  /**
   * Renderiza una tarjeta de documento.
   * @private
   * @param {object} doc - Documento
   * @param {string} doc.nombre - Nombre del documento
   * @param {string} doc.url - URL del documento
   * @returns {HTMLElement} Elemento HTML del documento
   */
  const _renderDocumento = (doc) => {
    const card = document.createElement("div");
    card.className = "card-documento";
    card.innerHTML = `
      <i class="bi bi-file-earmark-text"></i>
      <span title="${doc.nombre}">${doc.nombre}</span>
    `;
    card.addEventListener("click", () =>
      window.open(`/media/${doc.url}/`, "_blank")
    );
    return card;
  };

  /**
   * Renderiza una tarjeta de acción.
   * @private
   * @param {object} accion - Acción con posibles documentos adjuntos
   * @returns {string} HTML de la acción
   */
  const _renderAccion = (accion) => {
    const documentosHTML = accion.documentos?.length
      ? `<ul class="list-unstyled mb-0">${accion.documentos
          .map(
            (doc) =>
              `<li><a href="${doc.url}" target="_blank" class="text-decoration-none"><i class="bi bi-file-earmark-text me-1"></i>${doc.nombre}</a></li>`
          )
          .join("")}</ul>`
      : `<p class="text-muted small mb-0">Sin documentos</p>`;

    return `
      <div class="card shadow-sm border-0 mb-2">
        <div class="card-body">
          <h6 class="fw-bold mb-1">${accion.crea_por_nombre || "Sin usuario"}</h6>
          <p class="text-muted small mb-2">${accion.fecha}</p>
          <p class="mb-2">${accion.descri || "--"}</p>
          <div class="mt-2">
            <h6 class="text-muted small">Documentos adjuntos:</h6>
            ${documentosHTML}
          </div>
        </div>
      </div>
    `;
  };

  // === MÉTODOS PÚBLICOS ===

  /**
   * Carga los datos de detalle de la novedad.
   * @async
   */
  async function cargarDetalle() {
    try {
      const data = await fetchData(ENDPOINTS.detalle);
      el.codigo.textContent = data.num || "--";
      el.tipo.textContent = data.tipo || "--";
      el.estado.textContent = data.esta || "--";
      el.estado.className = `badge ${_estadoColor(data.esta)}`;
      el.fecha.textContent = data.fecha_regi || "--";
      el.cierre.textContent = data.fecha_venci || "--";
      el.responsable.textContent = data.respo_nom || "--";
      el.usuario.textContent = data.soli_nom || "--";
      el.descripcion.textContent = data.descri || "--";
    } catch (e) {
      toastError("Error cargando la novedad.");
    }
  }

  /**
   * Carga los documentos asociados.
   * @async
   */
  async function cargarDocumentos() {
    try {
      const documentos = await fetchData(ENDPOINTS.documentos);
      el.contenedorDocumentos.innerHTML = "";

      if (!documentos.length) {
        el.contenedorDocumentos.innerHTML = `<p class="text-muted">Sin documentos</p>`;
        return;
      }

      documentos.forEach((doc) =>
        el.contenedorDocumentos.appendChild(_renderDocumento(doc))
      );
    } catch (e) {
      toastError("Error cargando los documentos.");
    }
  }

  /**
   * Carga las acciones registradas.
   * @async
   */
  async function cargarAcciones() {
    try {
      const acciones = await fetchData(ENDPOINTS.acciones);
      el.listaAcciones.innerHTML = "";

      if (!acciones.length) {
        el.listaAcciones.innerHTML = `<p class="text-muted text-center mb-0">Sin acciones registradas</p>`;
        return;
      }

      acciones.forEach((accion) =>
        el.listaAcciones.insertAdjacentHTML("beforeend", _renderAccion(accion))
      );
    } catch (err) {
      console.error("Error cargando acciones:", err);
    }
  }

  /**
   * Envía el formulario para crear una nueva acción.
   * @async
   * @param {Event} e - Evento del formulario
   */
  async function crearAccion(e) {
    e.preventDefault();
    const formData = new FormData(el.formNuevaAccion);
    try {
      await fetch(ENDPOINTS.crearAccion, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: formData,
      });

      bootstrap.Modal.getInstance(el.modalNuevaAccion).hide();
      el.formNuevaAccion.reset();
      await cargarAcciones();
      toastSuccess("Acción creada correctamente.");
    } catch (err) {
      toastError("No se pudo crear la acción.");
    }
  }

  /**
   * Inicializa el módulo una sola vez.
   */
  function init() {
    if (initialized) return;
    initialized = true;
    cargarDetalle();
    cargarDocumentos();
    cargarAcciones();
    el.formNuevaAccion.addEventListener("submit", crearAccion);
  }

  /**
   * Devuelve la instancia única del módulo (Singleton).
   * @returns {{ init: Function, cargarAcciones: Function }}
   */
  function getInstance() {
    if (!instance) {
      instance = { init, cargarAcciones };
    }
    return instance;
  }

  return getInstance();
})();

// === Inicialización ===
document.addEventListener("DOMContentLoaded", () => {
  novedadModule.init();
});


/**
 * @changelog
 * 1.1.0 - 2025-10-21: Implementacion patrón Singleton + RMP y documentación JSDoc.
 *
 */
