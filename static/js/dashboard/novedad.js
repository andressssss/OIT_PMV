/**
 * @file novedad.js
 * @module novedadModule
 * @description Gestiona el detalle, documentos y acciones de una novedad (implementación Singleton con Revealing Module Pattern real + ESM).
 * @version 1.4.0
 * @author
 *   @name Andrés Sanabria
 *   @date 2025-10-22
 * @last_update 2025-10-24
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

// ============================
//   MÓDULO: novedadModule
// ============================
const novedadModule = (() => {
  // === VARIABLES PRIVADAS ===
  /** @type {object} Id de la novedad */
  const novedadId = window.location.pathname.split("/").filter(Boolean).pop();

  /** @type {object} Rol del usuario legal */
  const userRole = document.body.dataset.userRole;

  /** @type {object} Referencias a la API */
  const ENDPOINTS = {};

  /** @type {object} Referencias al DOM */
  const el = {};

  /** @type {object} Motivos de estado */
  const MOTIVOS_POR_ESTADO = {};

  /** @type {object} Personas relacionadas a un grupo */
  let personasData = {};

  // === FUNCIONES PRIVADAS ===

  /**
   * Devuelve la clase de color Bootstrap asociada a un estado
   * @param {string} estado - Estado actual de la novedad
   * @returns {string} Clases CSS de color
   */
  function getEstadoColor(estado) {
    const map = {
      nuevo: "bg-info text-dark",
      en_curso: "bg-primary text-white",
      pendiente: "bg-warning text-dark",
      planificacion: "bg-secondary text-white",
      terminado: "bg-success text-white",
      rechazado: "bg-danger text-white",
      cerrado: "bg-dark text-white",
      reabierto: "bg-primary-subtle text-primary-emphasis",
    };

    return map[estado] || "bg-light text-dark";
  }

  /**
   * Devuelve una clase de alerta si la fecha está vencida o próxima a vencer.
   * @param {string} fechaStr - Fecha en formato "YYYY-MM-DD HH:mm:ss"
   * @returns {string} Clases CSS para aplicar estilo
   */
  function getVencido(fechaStr) {
    if (!fechaStr) return "bg-secondary text-white";

    const fecha = new Date(fechaStr.replace(" ", "T"));
    const ahora = new Date();

    const diffMs = fecha - ahora;
    const diffDias = diffMs / (1000 * 60 * 60 * 24);

    if (diffDias < 0) {
      return "bg-danger text-white";
    } else if (diffDias <= 1) {
      return "bg-warning text-dark";
    } else {
      return "bg-success text-white";
    }
  }

  /**
   * Renderiza un documento como tarjeta.
   * @param {{ nombre: string, url: string }} doc
   * @returns {HTMLElement}
   */
  function renderDocumento(doc) {
    const card = document.createElement("div");
    card.className = "card-documento";
    card.innerHTML = `
      <i class="bi bi-file-earmark-text"></i>
      <span title="${doc.nombre}">${doc.nombre}</span>
    `;
    card.addEventListener("click", () => window.open(`${doc.url}/`, "_blank"));
    return card;
  }

  /**
   * Renderiza una acción con sus documentos adjuntos.
   * @param {object} accion
   * @returns {HTMLElement}
   */
  function renderAccion(accion) {
    const card = document.createElement("div");
    card.className = "card shadow-sm border-0 mb-2";

    // Cuerpo principal
    card.innerHTML = `
      <div class="card-body d-flex justify-content-between align-items-start">
        <div class="info">
          <h6 class="fw-bold mb-1">${
            accion.crea_por_nombre || "Sin usuario"
          }</h6>
          <p class="text-muted small mb-2">${accion.fecha}</p>
          <p class="mb-0">${accion.descri || "--"}</p>
        </div>
        <div class="contenedor-documentos2 d-flex flex-wrap justify-content-end gap-2"></div>
      </div>
    `;

    const contenedor = card.querySelector(".contenedor-documentos2");

    if (accion.documentos?.length) {
      accion.documentos.forEach((doc) =>
        contenedor.appendChild(renderDocumento(doc))
      );
    } else {
      contenedor.remove(); // No mostrar nada si no hay documentos
    }

    return card;
  }

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
      el.estado.className = `badge ${getEstadoColor(data.esta)}`;
      el.motivo.textContent = data.motivo_solucion || "--";
      el.fecha.textContent = data.fecha_regi || "--";
      el.cierre.textContent = data.fecha_venci || "--";
      el.cierre.className = `badge ${getVencido(data.fecha_venci)}`;
      el.responsable.textContent = data.respo_nom || "--";
      el.grupo.textContent = data.grupo || "--";
      el.usuario.textContent = data.soli_nom || "--";
      el.descripcion.textContent = data.descri || "--";
    } catch {
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

      const fragment = document.createDocumentFragment();
      documentos.forEach((doc) => fragment.appendChild(renderDocumento(doc)));
      el.contenedorDocumentos.appendChild(fragment);
    } catch {
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

      const fragment = document.createDocumentFragment();
      acciones.forEach((accion) => fragment.appendChild(renderAccion(accion)));
      el.listaAcciones.appendChild(fragment);
    } catch (err) {
      console.error("Error cargando acciones:", err);
    }
  }

  /**
   * Carga el estado actual en el modal
   * @async
   */
  async function cargarEstado() {
    setFormDisabled(el.formEstado, true);
    try {
      const data = await fetchData(ENDPOINTS.estados, {
        headers: { "X-CSRFToken": csrfToken },
      });
      el.formEstadoSelectEstado.innerHTML = "";
      const fragment = document.createDocumentFragment();

      data.forEach((el) => {
        const option = document.createElement("option");
        option.value = el;
        option.textContent = el.replace("_", " ").toUpperCase();
        fragment.appendChild(option);
      });
      el.formEstadoSelectEstado.appendChild(fragment);
      const estadoActual = el.formEstadoSelectEstado.value || data[0];
      actualizarMotivoEstado(estadoActual);
    } catch (err) {
      toastError(err);
    } finally {
      setFormDisabled(el.formEstado, false);
    }
    return null;
  }

  /**
   * Apoyar el cambi de estado con motivos de estado
   */
  function actualizarMotivoEstado(estado) {
    const motivos = MOTIVOS_POR_ESTADO[estado] || [];
    el.formEstadoSelectMotivo.innerHTML = "";

    if (!motivos.length) {
      const opt = document.createElement("option");
      opt.textContent = "Sin motivos disponibles";
      opt.disabled = true;
      opt.selected = true;
      el.formEstadoSelectMotivo.appendChild(opt);
      return;
    }

    const fragment = document.createDocumentFragment();

    motivos.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m;
      opt.textContent = m.replace("_", " ").toUpperCase();
      fragment.appendChild(opt);
    });

    el.formEstadoSelectMotivo.appendChild(fragment);
  }

  /**
   *  Cambia estado de la novedad
   * @async
   * @param {SubmitEvent} e
   */
  async function cambiarEstado(e) {
    e.preventDefault();
    const formData = new FormData(el.formEstado);
    const originalBtnContent = el.btnGuardarEstado.innerHTML;

    showSpinner(el.btnGuardarEstado);
    setFormDisabled(el.formEstado, true);

    try {
      await fetchData(ENDPOINTS.cambiarEstado, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: formData,
      });

      bootstrap.Modal.getInstance(el.modalEstado).hide();
      el.formEstado.reset();
      await cargarDetalle();
      aplicarRestricciones(userRole, el.estado.textContent);

      toastSuccess("Estado actualizado correctamente");
    } catch (e) {
    } finally {
      hideSpinner(el.btnGuardarEstado, originalBtnContent);
      setFormDisabled(el.formEstado, false);
    }
  }

  /**
   * Envía el formulario para crear una nueva acción.
   * @async
   * @param {SubmitEvent} e
   */
  async function crearAccion(e) {
    e.preventDefault();
    const formData = new FormData(el.formNuevaAccion);
    const originalBtnContent = el.btnGuardarAccion.innerHTML;

    if (formData.getAll("documentos").length > 3)
      return toastError("Maximo 3 archivos");

    showSpinner(el.btnGuardarAccion);
    setFormDisabled(el.formNuevaAccion, true);

    try {
      await fetchData(ENDPOINTS.crearAccion, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: formData,
      });

      bootstrap.Modal.getInstance(el.modalNuevaAccion).hide();
      el.formNuevaAccion.reset();
      await cargarAcciones();
      toastSuccess("Acción creada correctamente.");
    } catch (e) {
    } finally {
      hideSpinner(el.btnGuardarAccion, originalBtnContent);
      setFormDisabled(el.formNuevaAccion, false);
    }
  }

  /**
   * Control de visibilidad de elementos según el rol y el estado actual
   * @param {string} rol - Rol logueado en el sistema
   * @param {string} estado - Estado actual de la novedad
   * @returns {void}
   */
  /**
   * Aplica restricciones de visibilidad según el rol y el estado.
   * Solo el rol "instructor" tiene los botones deshabilitados.
   *
   * @param {string} rol - Rol del usuario logueado.
   * @param {string} estado - Estado actual de la novedad.
   * @returns {void}
   */
  function aplicarRestricciones(rol, estado) {
    const esInstructor = rol?.trim().toLowerCase() === "instructor";
    const esCerrado = estado?.trim().toLowerCase() === "cerrado";

    // Reiniciar visibilidad
    el.btnCambiarEstado.classList.remove("d-none");
    el.btnNuevaAccion.classList.remove("d-none");
    el.btnReasignar.classList.remove("d-none");

    // Si es instructor, ocultar todo
    if (esInstructor) {
      el.btnCambiarEstado.classList.add("d-none");
      el.btnNuevaAccion.classList.add("d-none");
      el.btnReasignar.classList.add("d-none");
      return;
    }

    // Si no es instructor pero la novedad está cerrada
    if (esCerrado) {
      el.btnNuevaAccion.classList.add("d-none");
      el.btnReasignar.classList.add("d-none");
    }
  }

  /**
   * Carga de responsable en modal
   * @async
   * @returns {void}
   */
  async function cargarResponsable() {
    setFormDisabled(el.formAsignacion, true);
    try {
      const data = await fetchData(ENDPOINTS.asignado, {
        headers: { "X-CSRFToken": csrfToken },
      });

      personasData = data.personas;

      el.formAsignacionSelectGrupo.innerHTML = "";
      el.formAsignacionSelectPersona.innerHTML = "";

      const fragmentG = document.createDocumentFragment();

      data.grupos.forEach((g) => {
        const option = document.createElement("option");
        option.value = g.id;
        option.textContent = g.nombre;
        fragmentG.appendChild(option);
      });

      el.formAsignacionSelectGrupo.appendChild(fragmentG);

      if (data.grupos.length) {
        cargarPersonasPorGrupo(data.grupos[0].id, personasData);
      }
    } catch (error) {
      toastError(error);
    } finally {
      setFormDisabled(el.formAsignacion, false);
    }
  }
  /**
   * Carga las personas asociadas a un grupo
   * @param {number} grupoSeleccionado - Grupo seleccionado en el select grupo para la reasignacion de responsable
   * @param {array} personasData - Arreglo de personas separadas por grupo
   * @returns {void}
   */
  function cargarPersonasPorGrupo(grupoSeleccionado, personasData) {
    const personas = personasData[String(grupoSeleccionado)] || [];
    el.formAsignacionSelectPersona.innerHTML = "";

    const fragmentP = document.createDocumentFragment();
    personas.forEach((p) => {
      const option = document.createElement("option");
      option.value = p.id;
      option.textContent = p.nombre;
      fragmentP.appendChild(option);
    });

    el.formAsignacionSelectPersona.appendChild(fragmentP);
  }

  /**
   * Actualiza persona asignada al caso
   * @param {event} e - Evento del formulario que se debe interceptar y evitar
   * @async
   * @returns {void}
   */
  async function cambiarAsignado(e) {
    e.preventDefault();
    const formData = new FormData(el.formAsignacion);
    const originalBtnContent = el.btnGuardarAsignacion.innerHTML;

    showSpinner(el.btnGuardarAsignacion);
    setFormDisabled(el.formAsignacion, true);

    try {
      await fetchData(ENDPOINTS.cambiarAsignado, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: formData,
      });

      bootstrap.Modal.getInstance(el.modalAsignacion).hide();
      el.formAsignacion.reset();
      await cargarDetalle();
      toastSuccess("Caso reasignado correctamente");
    } catch (error) {
    } finally {
      hideSpinner(el.btnGuardarAsignacion, originalBtnContent);
      setFormDisabled(el.formAsignacion, false);
    }
  }

  // === FUNCIÓN PÚBLICA ===
  async function init() {
    Object.assign(el, {
      codigo: $("#detalle-codigo"),
      tipo: $("#detalle-tipo"),
      estado: $("#detalle-estado"),
      motivo: $("#detalle-motivo"),
      fecha: $("#detalle-fecha"),
      cierre: $("#detalle-cierre"),
      responsable: $("#detalle-responsable"),
      usuario: $("#detalle-usuario"),
      descripcion: $("#detalle-descripcion"),
      grupo: $("#detalle-grupo"),
      contenedorDocumentos: $("#contenedor-documentos"),
      listaAcciones: $("#lista-acciones"),
      btnCambiarEstado: $("#btn-cambiar-estado"),
      btnReasignar: $("#btn-reasignar"),
      modalAsignacion: $("#modalAsignacion"),
      formAsignacion: $("#form-asignacion"),
      formAsignacionSelectGrupo: $("#form-asignacion select[name='grupo']"),
      formAsignacionSelectPersona: $("#form-asignacion select[name='persona']"),
      btnNuevaAccion: $("#btn-nueva-accion"),
      btnGuardarAccion: $("#btn-guardar-accion"),
      formNuevaAccion: $("#form-nueva-accion"),
      modalNuevaAccion: $("#modalNuevaAccion"),
      modalEstado: $("#modalEstado"),
      formEstado: $("#form-estado"),
      formEstadoSelectEstado: $("#form-estado select[name='estado']"),
      formEstadoSelectMotivo: $("#form-estado select[name='motivo']"),
      btnGuardarEstado: $("#btn-guardar-estado"),
      btnGuardarAsignacion: $("#btn-guardar-asignacion"),
    });

    const BASE_URL = `/api/dashboard/novedades/${novedadId}/`;

    Object.assign(ENDPOINTS, {
      detalle: `${BASE_URL}detalle/`,
      documentos: `${BASE_URL}documentos/`,
      acciones: `${BASE_URL}acciones/`,
      crearAccion: `${BASE_URL}acciones/create/`,
      estados: `${BASE_URL}estados/`,
      cambiarEstado: `${BASE_URL}estados/cambiar/`,
      asignado: `${BASE_URL}asignado/`,
      cambiarAsignado: `${BASE_URL}asignado/guardar/`,
    });

    Object.assign(MOTIVOS_POR_ESTADO, {
      nuevo: ["en_curso"],
      en_curso: ["en_curso"],
      pendiente: ["cronograma", "accion_otro_proveedor", "accion_solicitante"],
      planificacion: [
        "cronograma",
        "accion_otro_proveedor",
        "accion_solicitante",
      ],
      terminado: ["exito", "exito_problemas", "cierre_cliente"],
      rechazado: ["cancelado_soporte", "accion_otro_proveedor"],
      cerrado: ["exito", "exito_problemas", "cierre_cliente"],
      reabierto: ["en_curso", "accion_solicitante", "accion_otro_proveedor"],
    });

    el.formNuevaAccion.addEventListener("submit", crearAccion);
    el.modalEstado.addEventListener("show.bs.modal", cargarEstado);
    el.formEstadoSelectEstado.addEventListener("change", (e) =>
      actualizarMotivoEstado(e.target.value)
    );
    el.formEstado.addEventListener("submit", cambiarEstado);
    el.modalAsignacion.addEventListener("show.bs.modal", cargarResponsable);
    el.formAsignacionSelectGrupo.addEventListener("change", (e) => {
      const grupoId = e.target.value;
      cargarPersonasPorGrupo(grupoId, personasData);
    });

    el.formAsignacion.addEventListener("submit", cambiarAsignado);

    await cargarDetalle();
    aplicarRestricciones(userRole, el.estado.textContent);
    await Promise.all([cargarDocumentos(), cargarAcciones()]);
  }

  // === API PÚBLICA (solo init) ===
  return { init };
})();

// Inicialización
document.addEventListener("DOMContentLoaded", novedadModule.init);

/**
 * @changelog
 * 1.1.0 - 2025-10-21: Implementación patrón Singleton + RMP y documentación JSDoc.
 * 1.2.0 - 2025-10-22: Simplificación a ESM puro.
 * 1.3.0 - 2025-10-22: Reintroducción de RMP real para encapsulamiento completo.
 * 1.4.0 - 2025-10-22: Creacion de logica para el cambio de estados y reasignacion de responsables.
 */
