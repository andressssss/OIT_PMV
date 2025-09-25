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
  crearSelect,
} from "/static/js/utils.js";

document.addEventListener("DOMContentLoaded", () => {
  const loadingDiv = document.getElementById("loading");
  const tableElement = document.getElementById("aprendices");
  const form = document.getElementById("formEditarAprendiz");
  let table;

  cargarDatosTabla();

  // ======== Funcion para llenar la tabla =========
  async function cargarDatosTabla() {
    
    const estadosSelect = await crearSelect({
      id: "estados",
      nombre: "estados",
      url: "/api/aprendices/estados/",
      placeholderTexto: "Seleccione un estado",
      contenedor: "#contenedor-estado",
    })

    // ======= Inicialización de DataTable =======
    table = new DataTable(tableElement, {
      serverSide: true,
      processing: false,
      ajax: {
        url: `/api/usuarios/aprendices/filtrar/`,
        type: "GET",
        data: function (d) {
            d.estados = estadosSelect ? estadosSelect.getValue() : [];
        },
      },
      columns: [
        { data: "perfil.nom", title: "Nombre" },
        { data: "perfil.apelli", title: "Apellido" },
        { data: "perfil.tele", title: "Teléfono" },
        { data: "perfil.dire", title: "Dirección" },
        { data: "perfil.fecha_naci", title: "Fecha de nacimiento" },
        { data: "perfil.tipo_dni", title: "Tipo de DNI" },
        { data: "perfil.dni", title: "DNI" },
        {
          data: null,
          orderable: false,
          render: (_, __, row) => {
            let botones = `<button class="btn btn-outline-primary btn-sm mb-1 perfil-btn" 
                    data-id="${row.perfil.id}"
                    title="Ver Perfil"
                    data-bs-toggle="tooltip" 
                    data-bs-placement="top">
                    <i class="bi bi-plus-lg"></i>
                </button>`;
            if (row.can_edit) {
              botones += `<button class="btn btn-outline-warning btn-sm mb-1 edit-btn" 
                    data-id="${row.perfil.id}"
                    title="Editar"
                    data-bs-toggle="tooltip" 
                    data-bs-placement="top">
                    <i class="bi bi-pencil-square"></i>
                </button>`;
            }
            return botones;
          },
        },
      ],
      language: {
        url: "https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json",
      },
      drawCallback: () => {
        document
          .querySelectorAll('[data-bs-toggle="tooltip"]')
          .forEach((el) => {
            new bootstrap.Tooltip(el);
          });
      },
    });

    table.on("preXhr.dt", () => mostrarPlaceholdersTabla());

    // Aplicar filtros al cambiar
    document
      .querySelector("#estados")
      .addEventListener("change", () => table.ajax.reload());
  }

  function mostrarPlaceholdersTabla() {
    const tbody = document.querySelector("#aprendices tbody");
    tbody.innerHTML = "";

    const rows = 10;
    const cols = 8;

    for (let i = 0; i < rows; i++) {
      const tr = document.createElement("tr");
      for (let j = 0; j < cols; j++) {
        tr.innerHTML += `
        <td>
          <span class="placeholder col-8 placeholder-glow rounded d-block" style="height: 1.2rem;"></span>
        </td>
      `;
      }
      tbody.appendChild(tr);
    }
  }

  // ======= Botón Editar Aprendiz =======
  document.addEventListener("click", function (e) {
    if (e.target.closest(".edit-btn")) {
      const btn = e.target.closest(".edit-btn");
      const aprendizId = btn.dataset.id;

      const modalElement = document.getElementById("editAprendizModal");
      const modalInstance = new bootstrap.Modal(modalElement);
      modalInstance.show();

      cargarDatosEditarAprendiz(aprendizId);
    }
  });

  function cargarDatosEditarAprendiz(aprendizId) {
    const url = `/api/aprendiz/${aprendizId}/`;
    const inputs = form.querySelectorAll("input, select, button");

    // Deshabilitar inputs mientras se cargan datos
    inputs.forEach((el) => (el.disabled = true));

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        form.querySelector('input[name="perfil-nom"]').value =
          data["perfil-nom"];
        form.querySelector('input[name="perfil-apelli"]').value =
          data["perfil-apelli"];
        form.querySelector('select[name="perfil-tipo_dni"]').value =
          data["perfil-tipo_dni"];
        form.querySelector('input[name="perfil-dni"]').value =
          data["perfil-dni"];
        form.querySelector('input[name="perfil-tele"]').value =
          data["perfil-tele"];
        form.querySelector('input[name="perfil-dire"]').value =
          data["perfil-dire"];
        form.querySelector('input[name="perfil-mail"]').value =
          data["perfil-mail"];
        form.querySelector('select[name="perfil-gene"]').value =
          data["perfil-gene"];
        form.querySelector('input[name="perfil-fecha_naci"]').value =
          data["perfil-fecha_naci"];
        form.querySelector('input[name="representante-nom"]').value =
          data["representante-nom"];
        form.querySelector('input[name="representante-dni"]').value =
          data["representante-dni"];
        form.querySelector('input[name="representante-tele"]').value =
          data["representante-tele"];
        form.querySelector('input[name="representante-dire"]').value =
          data["representante-dire"];
        form.querySelector('input[name="representante-mail"]').value =
          data["representante-mail"];
        form.querySelector('select[name="representante-paren"]').value =
          data["representante-paren"];

        form.setAttribute("action", `/aprendices/editar/${aprendizId}/`);
      })
      .catch((error) => {
        console.error("Error cargando al aprendiz", error);
      })
      .finally(() => {
        inputs.forEach((el) => (el.disabled = false));
      });
  }

  // ======= Botón Ver Perfil =======
  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".perfil-btn");

    if (btn) {
      const contenidoPerfil = document.getElementById("contenidoPerfil");
      contenidoPerfil.innerHTML = "<p>Cargando perfil...</p>";
      fadeIn(loadingDiv);
      const aprendizId = btn.dataset.id;

      const modalElement = document.getElementById("modalVerPerfil");
      const modalInstance = new bootstrap.Modal(modalElement);
      modalInstance.show();

      fetch(`/api/aprendices/modal/ver_perfil_aprendiz/${aprendizId}`)
        .then((response) => {
          if (!response.ok) {
            throw new Error("Error en la respuesta del servidor");
          }
          return response.text();
        })
        .then((data) => {
          contenidoPerfil.innerHTML = data;
        })
        .catch((error) => {
          console.error("Error al cargar perfil:", error);
          contenidoPerfil.innerHTML =
            '<p class="text-danger">Error al cargar el perfil</p>';
        })
        .finally(() => {
          fadeOut(loadingDiv);
        });
    }
  });

  //======== Guardar formulario editar aprendiz
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      const url = form.action;

      const formData = new FormData(form);
      const data = new URLSearchParams(formData).toString();

      const inputs = form.querySelectorAll("input, select, button");
      inputs.forEach((el) => (el.disabled = true));

      fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-Requested-With": "XMLHttpRequest",
        },
        body: data,
      })
        .then((response) => {
          if (!response.ok) {
            return response.json().then((error) => {
              throw error;
            });
          }
          return response.json();
        })
        .then((data) => {
          showSuccessToast(data.message);

          const modalElement = document.getElementById("editAprendizModal");
          const modalInstance = bootstrap.Modal.getInstance(modalElement);
          modalInstance.hide();

          table.ajax.reload();
        })
        .catch((error) => {
          showErrorToast(error.message);
        })
        .finally(() => {
          inputs.forEach((el) => (el.disabled = false));
        });
    });
  }
});
