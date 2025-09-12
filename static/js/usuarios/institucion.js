import {
  confirmDeletion,
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
  const loadingDiv = document.getElementById("loading");
  const contenedor = document.getElementById("contenedor");
  const tableElement = document.getElementById("instituciones");
  const departamentoSelect = document.getElementById("departamento");
  const municipioSelect = document.getElementById("municipio");
  const zonaSelect = document.getElementById("zona");
  const estadoSelect = document.getElementById("estado");
  const ordenarPorSelect = document.getElementById("ordenar_por");
  const muniModalSelect = document.getElementById("muni");
  const depaModalSelect = document.getElementById("depa");
  const formCrearInstitucion = document.getElementById("formCrearInstitucion");
  const erroresDiv = document.getElementById("formCrearInstitucionErrores");
  const btnGuardar = document.getElementById("btnGuardarInstitucion");
  const formEditarInstitucion = document.getElementById(
    "formEditarInstitucion"
  );

  cargarDatosFiltro();

  // ============ LLenado inicial de tabla ==========
  const table = new DataTable(tableElement, {
    processing: true,
    serverSide: true,
    ajax: (data, callback, settings) => {
      const url = new URL("/api/institucion/", window.location.origin);

      const params = new URLSearchParams(serializeDataTableParams(data));

      // ====== Filtros especiales =========
      const municipio = document.getElementById("municipio")?.value;
      const departamento = document.getElementById("departamento")?.value;
      const zona = document.getElementById("zona")?.value;
      const estado = document.getElementById("estado")?.value;
      const ordenarPor = document.getElementById("ordenarPor")?.value;

      if (municipio) params.append("municipio", municipio);
      if (departamento) params.append("departamento", departamento);
      if (zona) params.append("zona", zona);
      if (estado) params.append("estado", estado);
      if (ordenarPor) params.append("ordenar_por", ordenarPor);

      url.search = params.toString();

      fetch(url)
        .then((response) => {
          if (!response.ok) {
            throw new Error("Error al obtener los datos");
          }
          return response.json();
        })
        .then((data) => callback(data))
        .catch((error) => {
          console.error("Error en la tabla:", error);
          callback({
            draw: data.draw,
            recordsTotal: 0,
            recordsFiltered: 0,
            data: [],
          });
        });
    },
    columns: [
      { data: "nom", orderable: true, title: "Nombre" },
      { data: "dire", orderable: true, title: "Dirección" },
      { data: "municipio_nombre", orderable: true, title: "Municipio" },
      { data: "departamento_nombre", orderable: true, title: "Departamento" },
      { data: "secto", orderable: true, title: "Sector" },
      { data: "esta", orderable: true, title: "Esta" },
      { data: "dane", orderable: true, title: "DANE" },
      {
        data: "gene",
        orderable: true,
        title: "Género",
        render: (data) =>
          ({
            mi: "Mixto",
            ma: "Masculino",
            fe: "Femenino",
          }[data] || "Desconocido"),
      },
      {
        data: "zona",
        orderable: true,
        title: "Zona",
        render: (data) =>
          ({
            r: "Rural",
            u: "Urbana",
          }[data] || "Desconocido"),
      },
      {
        data: "id",
        orderable: false,
        title: "Acciones",
        render: (data, type, row) => {
          return `
                      ${
                        row.can_edit
                          ? `<button class="btn btn-outline-warning btn-sm mb-1 editar-institucion" 
                                data-id="${data}" 
                                title="Editar"
                                data-bs-toggle="tooltip" 
                                data-bs-placement="top">
                            <i class="bi bi-pencil-square"></i>
                        </button>`
                          : ``
                      }
                        <button class="btn btn-outline-primary btn-sm mb-1 ver-btn" 
                            data-id="${data}"
                            title="Ver Institución"
                            data-bs-toggle="tooltip" 
                            data-bs-placement="top">
                            <i class="bi bi-plus-lg"></i>
                        </button>
                    `;
        },
      },
    ],
    language: {
      url: "https://cdn.datatables.net/plug-ins/1.13.6/i18n/es-ES.json",
    },
    drawCallback: () => {
      document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
        new bootstrap.Tooltip(el);
      });
    },
  });

  function serializeDataTableParams(data) {
    const params = new URLSearchParams();

    params.append("draw", data.draw);
    params.append("start", data.start);
    params.append("length", data.length);

    // Búsqueda
    if (data.search && data.search.value !== undefined) {
      params.append("search[value]", data.search.value);
    }

    // Ordenamiento
    if (Array.isArray(data.order)) {
      data.order.forEach((orderItem, index) => {
        params.append(`order[${index}][column]`, orderItem.column);
        params.append(`order[${index}][dir]`, orderItem.dir);
      });
    }

    // Columnas (opcional, por si las necesitas en el backend)
    if (Array.isArray(data.columns)) {
      data.columns.forEach((col, index) => {
        params.append(`columns[${index}][data]`, col.data);
        params.append(`columns[${index}][name]`, col.name || "");
        params.append(`columns[${index}][searchable]`, col.searchable);
        params.append(`columns[${index}][orderable]`, col.orderable);
        if (col.search) {
          params.append(`columns[${index}][search][value]`, col.search.value);
          params.append(`columns[${index}][search][regex]`, col.search.regex);
        }
      });
    }

    return params.toString();
  }

  function cargarDatosFiltro() {
    if (contenedor) {
      fadeIn(loadingDiv);
      fadeOutElement(contenedor);

      const promesasSelect2 = [
        poblarSelect(
          "/api/institucion/departamento",
          "departamento",
          "Todos los departamentos"
        ),
        poblarSelect(
          "/api/institucion/municipio",
          "municipio",
          "Todos los municipios"
        ),
        poblarSelect("/api/institucion/estado", "estado", "Todos los estados"),
        poblarSelect("/api/institucion/zona", "zona", "Todas las zonas"),
      ];

      Promise.all([...promesasSelect2]).finally(() => {
        fadeOut(loadingDiv);
        fadeInElement(contenedor);
      });
    }
  }

  function poblarSelect(url, selectId, placeholder = "Seleccione...") {
    const selectElement = document.getElementById(selectId);
    if (!selectElement) {
      console.error(`Elemento #${selectId} no encontrado`);
      return Promise.resolve(); // Devuelve promesa vacía, no rompe Promise.all
    }

    return fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Error al cargar datos desde ${url}`);
        }
        return response.json();
      })
      .then((data) => {
        selectElement.innerHTML = "";

        const emptyOption = document.createElement("option");
        emptyOption.value = "";
        emptyOption.textContent = placeholder;
        selectElement.appendChild(emptyOption);

        data.forEach((item) => {
          const option = document.createElement("option");
          option.value = item.value;
          option.textContent = item.label;
          selectElement.appendChild(option);
        });

        if (selectElement.tomselect) {
          selectElement.tomselect.destroy();
        }

        new TomSelect(selectElement, {
          placeholder: placeholder,
          allowEmptyOption: true,
          plugins: ["remove_button"],
          persist: false,
          create: false,
          closeAfterSelect: true,
          sortField: { field: "text", direction: "asc" },
        });
      })
      .catch((error) => console.error(`Error cargando ${selectId}:`, error));
  }

  if (document.getElementById("filtros-form")) {
    document.getElementById("filtros-form").addEventListener("change", (e) => {
      table.draw();
    });
  }

  // Función para llenar departamentos desde la API
  function cargarDepartamentos() {
    fetch("/api/departamentos/")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        depaModalSelect.innerHTML =
          '<option value="">Seleccione un departamento</option>';
        if (Array.isArray(data) && data.length > 0) {
          data.forEach((item) => {
            const option = document.createElement("option");
            option.value = item.id;
            option.textContent = item.nom_departa;
            depaModalSelect.appendChild(option);
          });
        }
      })
      .catch((error) => {
        console.error("Error al cargar departamentos:", error);
      });
  }

  // Cargar departamentos al abrir el modal
  const crearInstitucionModal = document.getElementById(
    "crearInstitucionModal"
  );

  if (crearInstitucionModal) {
    crearInstitucionModal.addEventListener("show.bs.modal", function () {
      cargarDepartamentos();
      muniModalSelect.innerHTML =
        '<option value="">Seleccione un municipio</option>';
      muniModalSelect.disabled = true;
    });
  }

  if (depaModalSelect) {
    // Al cambiar el departamento, cargar municipios
    depaModalSelect.addEventListener("change", function () {
      const departamentoId = this.value;
      muniModalSelect.innerHTML =
        '<option value="">Seleccione un municipio</option>';
      muniModalSelect.disabled = true;

      if (departamentoId) {
        fetch(`/api/municipiosFormInsti/?departamento_id=${departamentoId}`)
          .then((response) => {
            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
          })
          .then((data) => {
            if (Array.isArray(data) && data.length > 0) {
              data.forEach((item) => {
                const option = document.createElement("option");
                option.value = item.id;
                option.textContent = item.nom_munici;
                muniModalSelect.appendChild(option);
              });
            }
            muniModalSelect.disabled = false;
          })
          .catch((error) => {
            console.error("Error al cargar municipios:", error);
          });
      }
    });
  }

  if (formCrearInstitucion) {
    formCrearInstitucion.addEventListener("submit", function (event) {
      event.preventDefault();

      const formData = new FormData(formCrearInstitucion);
      const originalBtnContent = btnGuardar.innerHTML;
      btnGuardar.disabled = true;
      showSpinner(btnGuardar);
      formCrearInstitucion
        .querySelectorAll("input, select, button")
        .forEach((el) => (el.disabled = true));

      fetch(formCrearInstitucion.action, {
        method: "POST",
        body: formData,
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrfToken,
        },
      })
        .then((response) => {
          return response.json().then((data) => {
            if (!response.ok) {
              throw data;
            }
            return data;
          });
        })
        .then((data) => {
          showSuccessToast(data.message);
          const modalElement = document.getElementById("crearInstitucionModal");
          const modal = bootstrap.Modal.getInstance(modalElement);
          modal.hide();

          table.ajax.reload();
          formCrearInstitucion.reset();
          erroresDiv.classList.add("d-none");
          erroresDiv.innerHTML = "";
        })
        .catch((error) => {
          showErrorToast(error.message);

          erroresDiv.innerHTML = error.errors || "Error desconocido.";
          erroresDiv.classList.remove("d-none");
        })
        .finally(() => {
          hideSpinner(btnGuardar, originalBtnContent);
          formCrearInstitucion
            .querySelectorAll("input, select, button")
            .forEach((el) => (el.disabled = false));
        });
    });
  }

  // Función para abrir el modal de edición y cargar datos de la institución
  function abrirModalEdicionInstitucion(institucionId) {
    formEditarInstitucion
      .querySelectorAll("input, select, button")
      .forEach((el) => (el.disabled = true));

    return fetch(`/api/institucion/${institucionId}/`)
      .then((response) => {
        if (!response.ok)
          throw new Error("Error al obtener los datos de la institución");
        return response.json();
      })
      .then((data) => {
        // Rellenar los campos del formulario de edición
        document.getElementById("edit_nom").value = data.nom;
        document.getElementById("edit_dire").value = data.dire;
        document.getElementById("edit_secto").value = data.secto;
        document.getElementById("edit_coordi").value = data.coordi;
        document.getElementById("edit_coordi_mail").value = data.coordi_mail;
        document.getElementById("edit_coordi_tele").value = data.coordi_tele;
        document.getElementById("edit_esta").value = data.esta;
        document.getElementById("edit_insti_mail").value = data.insti_mail;
        document.getElementById("edit_recto").value = data.recto;
        document.getElementById("edit_recto_tel").value = data.recto_tel;
        document.getElementById("edit_cale").value = data.cale;
        document.getElementById("edit_dane").value = data.dane;
        document.getElementById("edit_gene").value = data.gene;
        document.getElementById("edit_grados").value = data.grados;
        document.getElementById("edit_jorna").value = data.jorna;
        document.getElementById("edit_num_sedes").value = data.num_sedes;
        document.getElementById("edit_zona").value = data.zona;
        document.getElementById("edit_muni").value = data.zona;

        // Guardar el ID de la institución para enviar con el formulario
        formEditarInstitucion.setAttribute("data-id", institucionId);

        // Mostrar el modal
        const modalEdicion = new bootstrap.Modal(
          document.getElementById("editarInstitucionModal")
        );
        modalEdicion.show();

        cargarMunicipiosEnSelect("edit_muni", data.municipio).finally(() => {
          formEditarInstitucion
            .querySelectorAll("input, select, button")
            .forEach((el) => (el.disabled = false));
        });
      })
      .catch((error) => {
        console.error("Error:", error);
        alert("No se pudo cargar la información de la institución.");
        formEditarInstitucion
          .querySelectorAll("input, select, button")
          .forEach((el) => (el.disabled = false));
      });
  }

  function cargarMunicipiosEnSelect(selectId, municipioSeleccionado = null) {
    return fetch("/api/listar_municipios/")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Error al obtener municipios");
        }
        return response.json();
      })
      .then((data) => {
        const select = document.getElementById(selectId);
        select.innerHTML = "";

        const optionDefault = document.createElement("option");
        optionDefault.value = "";
        optionDefault.textContent = "Seleccione un municipio";
        select.appendChild(optionDefault);

        data.forEach((muni) => {
          const option = document.createElement("option");
          option.value = muni.id;
          option.textContent = muni.nom_munici;
          select.appendChild(option);
        });

        if (select.tomselect) {
          select.tomselect.destroy();
        }

        const tomSelect = new TomSelect(`#${selectId}`, {
          placeholder: "Seleccione un municipio",
          allowEmptyOption: true,
          maxOptions: 1000,
          searchField: ["text"],
          sortField: { field: "text", direction: "asc" },
        });

        if (municipioSeleccionado) {
          tomSelect.setValue(municipioSeleccionado);
        }

        tomSelect.enable();
      })
      .catch((error) => {
        console.error("Error al cargar municipios:", error);
        throw error; // Para que .finally() se ejecute igual
      });
  }

  // Delegar el evento al contenedor
  if (document.getElementById("instituciones")) {
    document
      .getElementById("instituciones")
      .addEventListener("click", function (event) {
        if (event.target.closest(".editar-institucion")) {
          const boton = event.target.closest(".editar-institucion");
          const institucionId = boton.getAttribute("data-id");

          const contenidoOriginal = boton.innerHTML;
          showSpinner(boton);
          boton.disabled = true;

          // Llamar la función para abrir el modal con los datos
          abrirModalEdicionInstitucion(institucionId).finally(() => {
            boton.innerHTML = contenidoOriginal;
            boton.disabled = false;
          });
        }
      });
  }

  if (formEditarInstitucion) {
    formEditarInstitucion.addEventListener("submit", function (e) {
      e.preventDefault();

      const institucionId = formEditarInstitucion.getAttribute("data-id");

      const submitBtn = formEditarInstitucion.querySelector(
        'button[type="submit"]'
      );
      const originalBtnContent = submitBtn.innerHTML;

      showSpinner(submitBtn);
      submitBtn.disabled = true;

      const formData = new FormData(formEditarInstitucion);

      fetch(`/api/institucion/editar/${institucionId}/`, {
        method: "POST",
        body: formData,
        headers: {
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest",
        },
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Error al guardar los cambios");
          }
          return response.json();
        })
        .then((data) => {
          showSuccessToast(data.message);

          const modalElement = document.getElementById(
            "editarInstitucionModal"
          );
          const modal = bootstrap.Modal.getInstance(modalElement);
          modal.hide();

          table.ajax.reload();
        })
        .catch((err) => {
          console.log(err);
          console.error(err.message, err.errors);
          alert("Hubo un problema al actualizar la institución.");
        })
        .finally(() => {
          submitBtn.innerHTML = originalBtnContent;
          submitBtn.disabled = false;
        });
    });
  }

  // ========== Boton ver institucion ==========
  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".ver-btn");

    if (btn) {
      const contenidoInstitucion = document.getElementById(
        "contenidoInstitucion"
      );
      contenidoInstitucion.innerHTML = "<p>Cargando perfil...</p>";
      fadeIn(loadingDiv);
      const institucionId = btn.dataset.id;

      const modalElement = document.getElementById("modalVerInstitucion");
      const modalInstance = new bootstrap.Modal(modalElement);
      modalInstance.show();

      fetch(`/api/institucion/modal/ver_institucion/${institucionId}`)
        .then((response) => {
          if (!response.ok) {
            throw new Error("Error en la respuesta del servidor");
          }
          return response.text();
        })
        .then((data) => {
          contenidoInstitucion.innerHTML = data;
        })
        .catch((error) => {
          contenidoInstitucion.innerHTML =
            '<p class="text-danger">Error al cargar el perfil</p>';
        })
        .finally(() => {
          fadeOut(loadingDiv);
        });
    }
  });
});
