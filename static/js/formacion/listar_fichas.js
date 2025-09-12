import {
  setFormDisabled,
  setSelectValue,
  validarArchivo,
  reiniciarTooltips,
  crearSelectForm,
  crearSelect,
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
  const userRole = document.body.dataset.userRole;

  const tableEl = document.getElementById("listado_fichas_table");
  const table = new DataTable(tableEl, {
    language: {
      url: "https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json",
    },
    deferRender: true,
    ordering: false,
    drawCallback: () => {
      document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
        new bootstrap.Tooltip(el);
      });
    },
  });

  cargarDatosTabla();

  async function cargarDatosTabla() {
    try {
      await Promise.all([
        crearSelect({
          id: "estado",
          nombre: "estados",
          url: "/api/fichas/estados/",
          placeholderTexto: "Seleccione un estado",
          contenedor: "#contenedor-estado",
        }),
        crearSelect({
          id: "instructor",
          nombre: "instructores",
          url: "/api/fichas/instructores/",
          placeholderTexto: "Seleccione un instructor",
          contenedor: "#contenedor-instructor",
        }),
        crearSelect({
          id: "programa",
          nombre: "programas",
          url: "/api/fichas/programas/",
          placeholderTexto: "Seleccione un programa",
          contenedor: "#contenedor-programa",
        }),
      ]);

      document
        .querySelectorAll("#estado, #instructor, #programa")
        .forEach((el) => el.addEventListener("change", aplicarFiltros));

      const response = await fetch(`/api/fichas/filtrar/`);
      const data = await response.json();
      if (!response.ok) {
        toastError(data.error || "No tiene permisos para ver este módulo.");
        return;
      }
      renderTabla(data);
    } catch (error) {
      toastError(error);
    }
  }

  function renderTabla(data) {
    table.clear();

    data.forEach((el) => {
      let botones = "";

      if (el.can_view_p) {
        botones += `
        <a class="btn btn-outline-primary btn-sm mb-1" 
            href="/ficha/${el.id}/"
            title="Ver ficha"
            data-bs-toggle="tooltip" 
            data-bs-placement="top">
            <i class="bi bi-journals"></i>
        </a>
      `;
      }
      if (el.can_edit) {
        botones += `
          <a class="btn btn-outline-warning btn-sm mb-1 btnEditarFicha" 
              data-id="${el.id}"
              title="Editar ficha"
              data-bs-toggle="tooltip" 
              data-bs-placement="top">
              <i class="bi bi-pencil-square"></i>
          </a>
        `;
      }

      table.row.add([
        el.num || "No registrado",
        el.grupo ?? "No registrado",
        el.estado,
        el.fecha_aper,
        el.centro,
        el.institucion,
        el.instru ?? "No asignado",
        el.matricu,
        el.progra,
        botones,
      ]);
    });

    table.draw();
  }

  function mostrarPlaceholdersTabla() {
    const tbody = document.querySelector("#listado_fichas_table tbody");
    tbody.innerHTML = "";

    const tr = document.createElement("tr");
    tr.innerHTML = `
            <td><span class="placeholder col-10 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-8 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-6 placeholder-glow placeholder-wave rounded"></span></td>
            <td><span class="placeholder col-4 placeholder-glow placeholder-wave rounded d-block" style="height: 1.5rem;"></span></td>
        `;
    tbody.appendChild(tr);
  }

  async function aplicarFiltros() {
    mostrarPlaceholdersTabla();
    const formData = new FormData(document.getElementById("filtros-form"));
    const params = new URLSearchParams(formData).toString();

    try {
      const response = await fetch(`/api/fichas/filtrar/?${params}`);
      const data = await response.json();
      renderTabla(data);
    } catch (error) {
      toastError(error);
    }
  }

  if (tableEl) {
    tableEl.addEventListener("click", async (e) => {
      if (e.target.closest(".btnEditarFicha")) {
        const btn = e.target.closest(".btnEditarFicha");
        const originalBtnContent = btn.innerHTML;
        const fichaId = btn.getAttribute("data-id");
        showSpinner(btn);

        const modalEl = document.getElementById("editarFichaModal");
        const modalInstance = new bootstrap.Modal(modalEl);
        modalInstance.show();

        await cargarDatosEditarFicha(fichaId);
        hideSpinner(btn, originalBtnContent);
      }
    });
  }
  const formEditarFicha = document.getElementById("formEditarFicha");

  async function cargarDatosEditarFicha(fichaId) {
    setFormDisabled(formEditarFicha, true);
    try {
      await Promise.all([
        crearSelectForm({
          id: "centro",
          nombre: "centro_id",
          url: "/api/usuarios/centros/",
          contenedor: "#contenedor-centros",
          placeholderTexto: "Seleccione un centro",
          required: true,
          disabled: true,
        }),
        crearSelectForm({
          id: "departamento",
          nombre: "departamento",
          url: "/api/usuarios/departamentos/",
          contenedor: "#contenedor-departamentos",
          placeholderTexto: "Seleccione un departamento",
          required: true,
          disabled: true,
        }),
      ]);
    } catch (error) {
      toastError(error);
    }
    try {
      const response = await fetch(`/api/formacion/fichas/${fichaId}/`);
      const data = await response.json();

      setSelectValue("centro", data.centro_id);
      setSelectValue("fase", data.fase_id);
      setSelectValue("departamento", data.depa_id);
      document.querySelector("#num_ficha").value = data.num;

      await crearSelectForm({
        id: "municipio",
        nombre: "municipio",
        url: `/api/usuarios/municipios/?departamento=${data.depa_id}`,
        contenedor: "#contenedor-municipios",
        placeholderTexto: "Seleccione un municipio",
        required: true,
        disabled: true,
      });

      setSelectValue("municipio", data.muni_id);

      const institucionResponse = await fetch(
        `/api/usuarios/instituciones/${data.insti_id}/`
      );
      const institucionData = await institucionResponse.json();

      const select = document.querySelector("#institucion");
      select.innerHTML = `
                <option value="${institucionData.id}" selected>${institucionData.nom}</option>
            `;

      formEditarFicha.dataset.action = `/api/formacion/fichas/${data.id}/`;
    } catch (e) {
      toastError(e);
    } finally {
      setFormDisabled(formEditarFicha, false);
    }
  }

  if (formEditarFicha) {
    formEditarFicha.addEventListener("change", async function (e) {
      const target = e.target;

      if (target && target.id === "departamento") {
        const departamentoId = target.value;

        // Filtrar municipios por departamento
        await crearSelectForm({
          id: "municipio",
          nombre: "municipio",
          url: `/api/usuarios/municipios/?departamento=${departamentoId}`,
          contenedor: "#contenedor-municipios",
          placeholderTexto: "",
          disabled: false,
          required: true,
        });

        document.querySelector("#contenedor-instituciones").innerHTML = `
                <select id="institucion" class="form-select" name="institucion" disabled required>
                    <option value="">Seleccione una opción</option>
                </select>
            `;
      } else if (target && target.id === "municipio") {
        const municipioId = target.value;

        // Filtrar instituciones por municipio
        await crearSelectForm({
          id: "institucion",
          nombre: "insti_id",
          url: `/api/usuarios/instituciones/?municipio=${municipioId}`,
          contenedor: "#contenedor-instituciones",
          placeholderTexto: "",
          disabled: false,
          required: true,
        });
      }
    });

    formEditarFicha.addEventListener("submit", async (e) => {
      e.preventDefault();

      const formData = new FormData(formEditarFicha);
      const numFicha = formData.get("num")?.trim();
      const btn = document.getElementById("btnEditarFicha");
      const originalBtnContent = btn.innerHTML;

      if (!numFicha) {
        const confirmed = await confirmAction(
          "¿Está seguro de editar la ficha sin número?"
        );
        if (!confirmed) return;
      }

      showSpinner(btn);
      setFormDisabled(formEditarFicha, true);

      try {
        const response = await fetch(formEditarFicha.dataset.action, {
          method: "PATCH",
          headers: {
            "X-CSRFTOKEN": csrfToken,
            "X-Requested-With": "XMLHttpRequest",
          },
          body: formData,
        });
        const data = await response.json();

        if (!response.ok) {
          let mensaje = "Ocurrió un error.";
          if (data.message) {
            mensaje = data.message;
          } else if (data.detail) {
            mensaje = data.detail;
          } else if (typeof data === "object") {
            mensaje = Object.values(data).flat().join(", ");
          }
          toastError(mensaje);
          return;
        }

        toastSuccess(data.message || data.detail);
        const modalEl = document.getElementById("editarFichaModal");
        const modalInstance = bootstrap.Modal.getInstance(modalEl);
        modalInstance.hide();
        aplicarFiltros();
      } catch (error) {
        toastError(error);
      } finally {
        setFormDisabled(formEditarFicha, false);
        hideSpinner(btn, originalBtnContent);
        reiniciarTooltips();
      }
    });
  }
  // *******************************************************************
  // *                                                                 *
  // *        ¡ADVERTENCIA! ZONA DE CÓDIGO IMPORTAR FICHAS             *
  // *                                                                 *
  // *******************************************************************

  const formImportarFichas = document.getElementById("formImportarFichas");

  if (formImportarFichas) {
    formImportarFichas.addEventListener("submit", async (e) => {
      e.preventDefault();
      const alertError = document.getElementById("erroresFichas");
      alertError.textContent = "";
      alertError.classList.add("d-none");
      const formData = new FormData(formImportarFichas);
      const btn = document.getElementById("btnImportar");
      const originalBtnContent = btn.innerHTML;

      if (btn.disabled) return;

      const archivoInput = document.getElementById("archivoFichas");
      const archivo = archivoInput.files[0];

      if (!archivo) {
        toastError("Debe seleccionar un archivo antes de enviar.");
        return;
      }

      if (!archivo.name.endsWith(".csv")) {
        toastError("Solo se permiten archivos .csv");
        return;
      }

      setFormDisabled(formImportarFichas, true);
      showSpinner(btn);

      try {
        const response = await fetch(`/api/formacion/fichas/importar/`, {
          method: "POST",
          body: formData,
          headers: { "X-CSRFToken": csrfToken },
        });

        const data = await response.json();

        if (!response.ok) {
          if (data.errores) {
            const alertError = document.getElementById("erroresFichas");
            alertError.textContent = data.errores
              .join("\n\n")
              .replace(/\\n/g, "\n");
            alertError.classList.remove("d-none");
          }
          toastError(data.message || "Error desconocido");
          return;
        }

        const resumenFicha = document.getElementById("resumenFichas");

        resumenFicha.innerHTML = `
                <li><strong>Fichas insertadas:</strong> ${data.resumen.insertados}</li>
            `;

        toastSuccess(data.message || "Carga finalizada");
        formImportarFichas.reset();
        archivoInput.value = "";
      } catch (error) {
        console.error(error);
        toastError(
          error.message || "Error inesperado al conectar con el servidor."
        );
      } finally {
        setFormDisabled(formImportarFichas, false);
        hideSpinner(btn, originalBtnContent);
      }
    });
  }
  // *******************************************************************
  // *                                                                 *
  // *        ¡ADVERTENCIA! ZONA DE CÓDIGO IMPORTAR FICHAS             *
  // *                                                                 *
  // *******************************************************************

  const formAsignarAprendices = document.getElementById(
    "formAsignarAprendices"
  );

  if (formAsignarAprendices) {
    formAsignarAprendices.addEventListener("submit", async (e) => {
      e.preventDefault();
      const alertError = document.getElementById("erroresAprendices");
      alertError.textContent = "";
      alertError.classList.add("d-none");
      const formData = new FormData(formAsignarAprendices);
      const btn = document.getElementById("btnAsignar");
      const originalBtnContent = btn.innerHTML;

      if (btn.disabled) return;

      const archivoInput = document.getElementById("archivoAprendices");
      const archivo = archivoInput.files[0];

      if (!archivo) {
        toastError("Debe seleccionar un archivo antes de enviar.");
        return;
      }

      if (!archivo.name.endsWith(".csv")) {
        toastError("Solo se permiten archivos .csv");
        return;
      }

      setFormDisabled(formAsignarAprendices, true);
      showSpinner(btn);

      try {
        const response = await fetch(`/api/formacion/fichas/asignar_apre/`, {
          method: "POST",
          body: formData,
          headers: { "X-CSRFToken": csrfToken },
        });

        const data = await response.json();

        if (!response.ok) {
          if (data.errores) {
            const alertError = document.getElementById("erroresAprendices");
            alertError.textContent = data.errores
              .join("\n\n")
              .replace(/\\n/g, "\n");
            alertError.classList.remove("d-none");
          }
          toastError(data.message || "Error desconocido");
          return;
        }

        const resumenAprendices = document.getElementById("resumenAprendices");

        resumenAprendices.innerHTML = `
                <li><strong>Aprendices asignados:</strong> ${data.resumen.insertados}</li>
            `;

        toastSuccess(data.message || "Carga finalizada");
        formAsignarAprendices.reset();
        archivoInput.value = "";
      } catch (error) {
        console.error(error);
        toastError(
          error.message || "Error inesperado al conectar con el servidor."
        );
      } finally {
        setFormDisabled(formAsignarAprendices, false);
        hideSpinner(btn, originalBtnContent);
      }
    });
  }
});
