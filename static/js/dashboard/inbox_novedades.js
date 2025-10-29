/**
 * @file inbox_novedades.js
 * @module inboxNovedadesModule
 * @description
 * Gestiona el listado de novedades (inbox) y los indicadores (KPIs) del panel principal.
 * Incluye inicialización de DataTable, carga de indicadores y registro de nuevas novedades.
 * @version 1.0.0
 * @author
 *   @name Andrés Sanabria
 *   @date 2025-10-24
 * @last_update 2025-10-24
 */

import {
  hideSpinner,
  resetForm,
  showSpinner,
  fetchData,
  setText,
  setFormDisabled,
  csrfToken,
  toastSuccess,
  toastError,
} from "/static/js/utils.js";

const inboxNovedadesModule = (() => {
  /** @type {object} Referencias a elementos del DOM */
  const el = {};

  /** @type {object} Rol del usuario legal */
  const userRole = document.body.dataset.userRole;

  /** @type {object} Endpoints del módulo */
  const ENDPOINTS = {
    indicadores: "/api/dashboard/novedades/kpis/",
    crear_novedad: "/api/dashboard/novedades/crear/",
    filtrar: "/api/dashboard/novedades/filtrar/",
  };

  /** @type {DataTable} Instancia de DataTable */
  let table;

  /**
   * Carga los indicadores de novedades desde la API.
   * @async
   * @returns {Promise<void>}
   */
  async function loadIndicadores() {
    const data = await fetchData(ENDPOINTS.indicadores);
    setText("kpi-total-novedades", data?.total_novedades ?? "--");
    setText("kpi-novedades-pendientes", data?.nove_pendi ?? "--");
    setText("kpi-novedades-gestion", data?.nove_gesti ?? "--");
    setText("kpi-novedades-cerradas", data?.nove_cerra ?? "--");
  }

  /**
   * Inicializa la tabla de novedades con DataTables.
   * @returns {void}
   */
  function initTable() {
    table = new DataTable(el.tablaNovedades, {
      serverSide: true,
      processing: false,
      ajax: {
        url: ENDPOINTS.filtrar,
        type: "GET",
      },
      columns: [
        { data: "num", title: "Número" },
        {
          data: "descri",
          title: "Descripción",
          render: function (data, type) {
            if (type === "display" && data) {
              return data.length > 50 ? `${data.substring(0, 50)}...` : data;
            }
            return data;
          },
        },
        { data: "tipo", title: "Tipo" },
        { data: "esta", title: "Estado" },
        { data: "responsable", title: "Responsable" },
        {
          data: "fecha",
          title: "Vencimiento",
          render: (data, type, row) => {
            if (!data) return "--";

            const estado = row.esta?.toLowerCase().trim();
            const fecha = new Date(data.replace(" ", "T"));
            const ahora = new Date();

            if (estado === "cerrado") {
              return `<span>${data}</span>`;
            }

            const vencido = fecha < ahora;
            const clase = vencido
              ? "text-danger fw-bold"
              : "text-success fw-semibold";

            return `<span class="${clase}">${data}</span>`;
          },
        },

        {
          data: null,
          render: (data, type, row) =>
            `<a class="btn btn-sm btn-outline-primary" href="/novedad/${row.id}/">
              <i class="bi bi-search"></i>
            </a>`,
        },
      ],
      language: {
        url: "https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json",
      },
    });
  }

  /**
   * Maneja el evento de creación de una nueva novedad.
   * @async
   * @param {SubmitEvent} e
   * @returns {Promise<void>}
   */
  async function crearNovedad(e) {
    e.preventDefault();

    const btn = el.btnSubmit;
    const originalBtnContent = btn.innerHTML;
    const formData = new FormData(el.formNuevaNovedad);
    const modal = bootstrap.Modal.getInstance(el.modalNuevaNovedad);

    if (formData.getAll("documentos").length > 3)
      return toastError("Maximo 3 archivos");

    showSpinner(btn);
    setFormDisabled(el.formNuevaNovedad, true);

    try {
      await fetchData(ENDPOINTS.crear_novedad, {
        method: "POST",
        body: formData,
        headers: { "X-CSRFToken": csrfToken },
      });

      resetForm(el.formNuevaNovedad);
      toastSuccess("Registro creado exitosamente");
      table.ajax.reload();
      loadIndicadores();
      modal.hide();
    } finally {
      hideSpinner(btn, originalBtnContent);
      setFormDisabled(el.formNuevaNovedad, false);
    }
  }

  /**
   * Control de visibilidad de elementos según el rol
   * @param {string} rol - Rol logueado en el sistema
   * @returns {void}
   */
  function aplicarRestricciones(rol) {
    const esAdmin = rol?.trim() === "admin";

    el.contenedorKpi.classList.add("d-none");

    if (esAdmin) {
      el.contenedorKpi.classList.remove("d-none");
    }
  }

  /**
   * Inicializa el módulo y todos sus componentes.
   * @async
   * @returns {Promise<void>}
   */
  async function init() {
    Object.assign(el, {
      tablaNovedades: document.getElementById("tabla-novedades"),
      formNuevaNovedad: document.getElementById("form-nueva-novedad"),
      modalNuevaNovedad: document.getElementById("modalNuevaNovedad"),
      btnSubmit: document.getElementById("btn-submit"),
      contenedorKpi: document.getElementById("contenedor-kpi"),
    });

    initTable();
    await loadIndicadores();

    // Eventos
    el.formNuevaNovedad.addEventListener("submit", crearNovedad);

    aplicarRestricciones(userRole);
  }

  return { init };
})();

// Inicializacion
document.addEventListener("DOMContentLoaded", inboxNovedadesModule.init);

/**
 * @changelog
 * 1.1.0 - 2025-10-24: Implementación patrón Singleton + RMP y documentación JSDoc.
 *
 */
