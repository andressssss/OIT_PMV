import {
  validarErrorDRF,
  resetForm,
  setSelectValue,
  reiniciarTooltips,
  cargarOpciones,
  crearSelect,
  crearSelectForm,
  showPlaceholder,
  setFormDisabled,
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
  const tableEl = document.getElementById("competencias_table");
  const table = new DataTable(tableEl, {
    language: {
      url: "https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json",
    },
    deferRender: true,
    ordering: false,
  });

  cargarDatosTabla();

  //== Carga inicial a la tabla
  async function cargarDatosTabla() {
    try {
      document.querySelectorAll("#fase, #programa").forEach((el) => {
        el.addEventListener("change", aplicarFiltros);
      });

      const response = await fetch("/api/formacion/competencias/tabla/");
      const data = await response.json();
      renderTabla(data);
    } catch (error) {
      toastError(error);
    }
  }

  //== renderizar tabla
  function renderTabla(data) {
    table.clear();

    data.forEach((item) => {
      table.row.add([
        item.nom,
        item.cod,
        item.can_edit
          ? `<button class="btn btn-outline-warning btn-sm mb-1 editBtn" 
                    data-id="${item.id}"
                    title="Editar"
                    data-bs-toggle="tooltip"
                    data-bs-placement="top">
                    <i class="bi bi-pencil-square"></i>
                </button>
                <button class="btn btn-outline-danger btn-sm mb-1 deleteBtn" 
                    data-id="${item.id}"
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
    const tbody = document.querySelector("#competencias_table tbody");
    tbody.innerHTML = "";

    const tr = document.createElement("tr");
    tr.innerHTML = `
            <td><span class="placeholder col-10 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-8 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-4 placeholder-glow placeholder-wave rounded d-block" style="height: 1.5rem;"></span></td>
        `;
    tbody.appendChild(tr);
  }

  //== Filtrar tabla
  async function aplicarFiltros() {
    mostrarPlaceholdersTabla();
    // const formData = new FormData(document.getElementById("filtros-form"));
    // const params = new URLSearchParams(formData).toString();

    try {
      const response = await fetch(`/api/formacion/competencias/tabla/?`);
      const data = await response.json();
      renderTabla(data);
    } catch (error) {
      toastError(error);
    }
  }

  //== Crear competencia
  const formCrearCompetencia = document.getElementById("formCrearCompetencia");
  if (formCrearCompetencia) {
    formCrearCompetencia.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = document.getElementById("btnCrearCompetencia");
      const originalBtnContent = btn.innerHTML;
      const formData = new FormData(formCrearCompetencia);
      const modal = bootstrap.Modal.getInstance(
        document.getElementById("crearCompetenciaModal")
      );

      showSpinner(btn);

      setFormDisabled(formCrearCompetencia, true);
      console.log(formData);
      try {
        const response = await fetch(`/api/formacion/competencias/`, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrfToken,
          },
          body: formData,
        });
        const data = await response.json();
        if (validarErrorDRF(response, data)) return;
        toastSuccess(data.message);
        resetForm(formCrearCompetencia);
        modal.hide();
        aplicarFiltros();
      } catch (error) {
        toastError(error);
      } finally {
        hideSpinner(btn, originalBtnContent);
        setFormDisabled(formCrearCompetencia, false);
      }
    });
  }

  //== Boton editar competencia
  if (tableEl) {
    tableEl.addEventListener("click", async (e) => {
      if (e.target.closest(".editBtn")) {
        const btn = e.target.closest(".editBtn");
        const originalBtnContent = btn.innerHTML;
        const competenciaId = btn.dataset.id;
        showSpinner(btn);
        const modalEl = document.getElementById("editarCompetenciaModal");
        const modalInstance = new bootstrap.Modal(modalEl);
        document.getElementById("btnEditarCompetencia").disabled = true;
        modalInstance.show();

        await cargarDatosEditarCompetencia(competenciaId);
        hideSpinner(btn, originalBtnContent);
        document.getElementById("btnEditarCompetencia").disabled = false;
      } else if (e.target.closest(".deleteBtn")) {
        const btn = e.target.closest(".deleteBtn");
        const originalBtnContent = btn.innerHTML;
        const rapId = btn.dataset.id;
        showSpinner(btn);

        const confirmed = await confirmDeletion(
          "¿Desea eliminar esta competencia?"
        );
        if (confirmed) {
          try {
            const response = await fetch(
              `/api/formacion/competencias/${rapId}/`,
              {
                method: "DELETE",
                headers: {
                  "X-CSRFToken": csrfToken,
                },
              }
            );
            const data = await response.json();
            if (validarErrorDRF(response, data)) return;
            toastSuccess("Competencia eliminada correctamente");
            aplicarFiltros();
          } catch (error) {
            toastError(error.message);
          } finally {
            hideSpinner(btn, originalBtnContent);
            reiniciarTooltips();
          }
        }
      }
    });
  }
  const formEditarCompetencia = document.getElementById(
    "formEditarCompetencia"
  );

  async function cargarDatosEditarCompetencia(competenciaId) {
    setFormDisabled(formEditarCompetencia, true);

    try {
      const response = await fetch(
        `/api/formacion/competencias/${competenciaId}/`
      );
      const data = await response.json();

      document.querySelector("#nom_edit").value = data.nom || "";
      document.querySelector("#cod_edit").value = data.cod ?? "";
      formEditarCompetencia.setAttribute(
        "action",
        `/api/formacion/competencias/${competenciaId}/`
      );
    } catch (error) {
      toastError(error);
    } finally {
      setFormDisabled(formEditarCompetencia, false);
    }
  }

  //== Guardar formulario editar competencia
  if (formEditarCompetencia) {
    formEditarCompetencia.addEventListener("submit", async (e) => {
      e.preventDefault();

      const formData = new FormData(formEditarCompetencia);
      const btn = document.getElementById("btnEditarCompetencia");
      const originalBtnContent = btn.innerHTML;
      showSpinner(btn);
      setFormDisabled(formEditarCompetencia, true);

      try {
        const response = await fetch(formEditarCompetencia.action, {
          method: "PATCH",
          headers: {
            "X-CSRFToken": csrfToken,
          },
          body: formData,
        });
        const data = await response.json();
        if (validarErrorDRF(response, data)) return;

        toastSuccess(data.message);

        const modalEl = document.getElementById("editarCompetenciaModal");
        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        modalInstance.hide();

        aplicarFiltros();
      } catch (error) {
        toastError(error);
      } finally {
        setFormDisabled(formEditarCompetencia, false);
        hideSpinner(btn, originalBtnContent);
      }
    });
  }
});
