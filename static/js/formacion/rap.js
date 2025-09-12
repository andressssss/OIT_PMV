import {
  setSelectValue,
  resetForm,
  reiniciarTooltips,
  setFormDisabled,
  cargarOpciones,
  validarErrorDRF,
  crearSelect,
  crearSelectForm,
  showPlaceholder,
  hidePlaceholder,
  confirmToast,
  confirmAction,
  confirmDialog,
  confirmDeletion,
  toastSuccess,
  toastError,
  toastWarning,
  toastInfo,
  fadeIn,
  fadeOut,
  fadeInElement,
  fadeOutElement,
  showSpinner,
  hideSpinner,
  csrfToken,
  showSuccessToast,
  showErrorToast,
} from "/static/js/utils.js";

document.addEventListener("DOMContentLoaded", () => {
  const tableEl = document.getElementById("raps_table");
  const table = new DataTable(tableEl, {
    language: {
      url: "https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json",
    },
    deferRender: true,
    ordering: false,
  });

  cargarDatosTabla();

  async function cargarDatosTabla() {
    try {
      await Promise.all([
        crearSelect({
          id: "fase",
          nombre: "fases",
          url: "/api/raps/fases/",
          placeholderTexto: "Seleccione una fase",
          contenedor: "#contenedor-fase",
        }),
        crearSelect({
          id: "competencia",
          nombre: "competencias",
          url: "/api/raps/competencias/",
          placeholderTexto: "Seleccione una competencia",
          contenedor: "#contenedor-competencia",
        }),
        crearSelect({
          id: "programa",
          nombre: "programas",
          url: "/api/raps/programas/",
          placeholderTexto: "Seleccione un programa",
          contenedor: "#contenedor-programa",
        }),
        crearSelectForm({
          id: "compe_crear",
          nombre: "compe",
          url: "/api/formacion/competencias/",
          placeholderTexto: "Seleccione una competencia",
          contenedor: "#contenedor-competencias-crear",
          multiple: false,
          required: true,
        }),
        crearSelectForm({
          id: "progra_crear",
          nombre: "progra",
          url: "/api/formacion/programas/",
          placeholderTexto: "Seleccione un programa",
          contenedor: "#contenedor-programas-crear",
          multiple: false,
          required: true,
        }),
        crearSelectForm({
          id: "fase_crear",
          nombre: "fase",
          url: "/api/formacion/fases/",
          placeholderTexto: "Seleccione una fase",
          contenedor: "#contenedor-fases-crear",
          multiple: true,
          required: true,
        }),
        crearSelectForm({
          id: "compe_editar",
          nombre: "compe",
          url: "/api/formacion/competencias/",
          placeholderTexto: "Seleccione una competencia",
          contenedor: "#contenedor-competencias-editar",
          multiple: false,
          required: true,
        }),
        crearSelectForm({
          id: "progra_editar",
          nombre: "progra",
          url: "/api/formacion/programas/",
          placeholderTexto: "Seleccione un programa",
          contenedor: "#contenedor-programas-editar",
          multiple: false,
          required: true,
        }),
        crearSelectForm({
          id: "fase_editar",
          nombre: "fase",
          url: "/api/formacion/fases/",
          placeholderTexto: "Seleccione una fase",
          contenedor: "#contenedor-fases-editar",
          multiple: true,
          required: true,
        }),
      ]);

      document
        .querySelectorAll("#fase, #programa, #competencia")
        .forEach((el) => {
          el.addEventListener("change", aplicarFiltros);
        });

      const response = await fetch(`/api/formacion/raps/tabla/`);
      const data = await response.json();
      renderTabla(data);
    } catch (error) {
      toastError(error);
    }
  }

  function renderTabla(data) {
    table.clear();

    data.forEach((el) => {
      const listaFases = `<ul class="lista-estilo">${el.fase
        .map((p) => `<li><i class="bi bi-dot"></i> ${p}</li>`)
        .join("")}</ul>`;

      table.row.add([
        el.nom,
        el.cod,
        el.compe,
        el.progra,
        listaFases || "Sin registro",
        el.can_edit
          ? `<button class="btn btn-outline-warning btn-sm mb-1 editBtn" 
                    data-id="${el.id}"
                    title="Editar"
                    data-bs-toggle="tooltip"
                    data-bs-placement="top">
                    <i class="bi bi-pencil-square"></i>
                </button>
                <button class="btn btn-outline-danger btn-sm mb-1 deleteBtn" 
                    data-id="${el.id}"
                    title="Eliminar"
                    data-bs-toggle="tooltip"
                    data-bs-placement="top">
                    <i class="bi bi-trash"></i>
                </button>`
          : "",
      ]);
    });

    table.draw();

    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
      new bootstrap.Tooltip(el);
    });
  }

  function mostrarPlaceholdersTabla() {
    const tbody = document.querySelector("#raps_table tbody");
    tbody.innerHTML = "";

    const tr = document.createElement("tr");
    tr.innerHTML = `
            <td><span class="placeholder col-10 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-8 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-4 placeholder-glow placeholder-wave rounded d-block" style="height: 1.5rem;"></span></td>
        `;
    tbody.appendChild(tr);
  }

  //== Filtrar tabla
  async function aplicarFiltros() {
    mostrarPlaceholdersTabla();
    const formData = new FormData(document.getElementById("filtros-form"));
    const params = new URLSearchParams(formData).toString();

    try {
      const response = await fetch(`/api/formacion/raps/tabla/?${params}`);
      const data = await response.json();
      renderTabla(data);
    } catch (error) {
      toastError(error);
    }
  }

  //==Crear RAP
  const formCrearRAP = document.getElementById("formCrearRAP");

  if (formCrearRAP) {
    formCrearRAP.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = document.getElementById("btnCrearRAP");
      const originalBtnContent = btn.innerHTML;
      const formData = new FormData(formCrearRAP);
      const modal = bootstrap.Modal.getInstance(
        document.getElementById("crearRAPModal")
      );

      showSpinner(btn);
      setFormDisabled(formCrearRAP, true);

      try {
        const response = await fetch(`/api/formacion/raps/`, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrfToken,
            "X-Requested-With": "XMLHttpRequest",
          },
          body: formData,
        });

        const data = await response.json();

        if (validarErrorDRF(response, data)) return;

        toastSuccess(data.message);
        resetForm(formCrearRAP);
        modal.hide();
        aplicarFiltros();
      } catch (error) {
        toastError(error || "Ocurrió un error inesperado");
      } finally {
        hideSpinner(btn, originalBtnContent);
        setFormDisabled(formCrearRAP, false);
      }
    });
  }

  if (tableEl) {
    //== Boton editar RAP
    tableEl.addEventListener("click", async (e) => {
      if (e.target.closest(".editBtn")) {
        const btn = e.target.closest(".editBtn");
        const originalBtnContent = btn.innerHTML;
        const rapId = btn.dataset.id;
        showSpinner(btn);
        const modalEl = document.getElementById("editarRAPModal");
        const modalInstance = new bootstrap.Modal(modalEl);
        modalInstance.show();

        await cargarDatosEditarRap(rapId);
        hideSpinner(btn, originalBtnContent);
      } else if (e.target.closest(".deleteBtn")) {
        const btn = e.target.closest(".deleteBtn");
        const originalBtnContent = btn.innerHTML;
        const rapId = btn.dataset.id;
        showSpinner(btn);

        const confirmed = await confirmDeletion("¿Desea eliminar este RAP?");
        if (confirmed) {
          try {
            const response = await fetch(`/api/formacion/raps/${rapId}/`, {
              method: "DELETE",
              headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken,
                "X-Requested-With": "XMLHttpRequest",
              },
            });
            const data = await response.json();

            if (validarErrorDRF(response, data)) return;
            toastSuccess(data.message || "RAP eliminado correctamente");
            aplicarFiltros();
          } catch (error) {
            toastError(error.message);
          }
        }
        hideSpinner(btn, originalBtnContent);
        reiniciarTooltips();
      }
    });
  }
  const formEditarRAP = document.getElementById("formEditarRAP");

  async function cargarDatosEditarRap(rapId) {
    setFormDisabled(formEditarRAP, true);

    try {
      const response = await fetch(`/api/formacion/raps/${rapId}/`);
      const data = await response.json();

      if (validarErrorDRF(response, data)) return;
      formEditarRAP.querySelector('input[name="nom"]').value = data.nom;
      formEditarRAP.querySelector('input[name="cod"]').value = data.cod;
      setSelectValue("fase_editar", data.fase);
      setSelectValue("progra_editar", data.progra);
      setSelectValue("compe_editar", data.compe);

      formEditarRAP.setAttribute("action", `/api/formacion/raps/${rapId}/`);
    } catch (error) {
      toastError(error);
    } finally {
      setFormDisabled(formEditarRAP, false);
    }
  }

  if (formEditarRAP) {
    formEditarRAP.addEventListener("submit", async (e) => {
      e.preventDefault();

      const formData = new FormData(formEditarRAP);
      const btn = document.getElementById("btnEditarRAP");
      const originalBtnContent = btn.innerHTML;

      showSpinner(btn);
      setFormDisabled(formEditarRAP, true);
      try {
        const response = await fetch(formEditarRAP.action, {
          method: "PATCH",
          headers: {
            "X-CSRFToken": csrfToken,
            "X-Requested-With": "XMLHttpRequest",
          },
          body: formData,
        });
        const data = await response.json();

        if (validarErrorDRF(response, data)) return;

        toastSuccess(data.message);

        const modalEl = document.getElementById("editarRAPModal");
        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        modalInstance.hide();

        aplicarFiltros();
      } catch (error) {
        toastError(error);
      } finally {
        setFormDisabled(formEditarRAP, false);
        hideSpinner(btn, originalBtnContent);
        reiniciarTooltips();
      }
    });
  }
});
