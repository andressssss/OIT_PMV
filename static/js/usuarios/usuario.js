import {
  setFormDisabled,
  toastSuccess,
  validarErrorDRF,
  toastError,
  confirmAction,
  confirmToast,
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
  const tableEl = document.getElementById("usuarios_table");

  const table = new DataTable(tableEl, {
    serverSide: true,
    processing: false,
    ajax: {
      url: "/api/usuarios/perfiles/filtrar/",
      type: "GET",
    },
    columns: [
      { data: "nom" },
      { data: "apelli" },
      { data: "tipo_dni" },
      { data: "dni" },
      { data: "username" },
      { data: "last_login", defaultContent: "No registrado" },
      { data: "rol" },
      {
        data: "is_active",
        render: function (data, type, row) {
          return data ? "Activo" : "Inactivo";
        },
      },
      {
        data: null,
        orderable: false,
        render: function (data, type, row) {
          if (row.can_edit) {
            let botones = `
            <a class="btn btn-outline-secondary btn-sm mb-1 btn-establecer-contra"
                data-id="${row.id}"
                data-usuario="${row.nom} ${row.apelli}"
                data-toggle="tooltip"
                data-placement="top"
                title="Establecer contraseña"
                data-bs-toggle="modal"
                data-bs-target="#modalReset">
                <i class="bi bi-asterisk"></i>
            </a>
            <a class="btn btn-outline-secondary btn-sm mb-1 btn-permisos"
                data-id="${row.id}"
                data-usuario="${row.nom} ${row.apelli}"
                data-toggle="tooltip"
                data-placement="top"
                title="Establecer permisos"
                data-bs-toggle="modal"
                data-bs-target="#modalPermisos">
                <i class="bi bi-key"></i>
            </a>
          `;

            if (row.is_active) {
              botones += `
              <a class="btn btn-outline-warning btn-sm mb-1 btn-inhabilitar"
                data-id="${row.id}"
                data-toggle="tooltip"
                data-placement="top"
                title="Inhabilitar usuario">
                <i class="bi bi-person-x"></i>
              </a>
            `;
            } else {
              botones += `
              <a class="btn btn-outline-info btn-sm mb-1 btn-habilitar"
                data-id="${row.id}"
                data-toggle="tooltip"
                data-placement="top"
                title="Habilitar usuario">
                <i class="bi bi-person-check"></i>
              </a>
            `;
            }
            return botones;
          } else return "";
        },
      },
    ],
    language: {
      url: "https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json",
    },
    drawCallback: () => {
      document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
        new bootstrap.Tooltip(el);
      });
    },
  });

  function mostrarPlaceholdersTabla() {
    const tbody = document.querySelector("#usuarios_table tbody");
    if (!tbody) return;

    tbody.innerHTML = "";

    const tr = document.createElement("tr");

    const placeholders = [
      "col-10",
      "col-10",
      "col-8",
      "col-6",
      "col-6",
      "col-6",
      "col-6",
      "col-6",
      "col-4",
    ];

    placeholders.forEach((colClass) => {
      const td = document.createElement("td");
      td.innerHTML = `<span class="placeholder ${colClass} placeholder-glow placeholder-wave rounded"></span>`;
      tr.appendChild(td);
    });

    tbody.appendChild(tr);
  }

  table.on("preXhr.dt", function () {
    mostrarPlaceholdersTabla();
  });

  table.on("processing.dt", function (e, settings, processing) {
    const tbody = document.querySelector("#usuarios_table tbody");
    if (!tbody) return;

    if (processing) {
      mostrarPlaceholdersTabla();
    }
  });

  tableEl.addEventListener("click", async function (e) {
    if (e.target.closest(".btn-establecer-contra")) {
      const btn = e.target.closest(".btn-establecer-contra");
      const userId = btn.dataset.id;
      const nombre = btn.dataset.usuario;
      document.getElementById("user-id-reset").value = userId;
      document.getElementById("nombre-usr-restablecer").innerHTML = nombre;
      document.getElementById("new-password").value = "";
    }
    if (e.target.closest(".btn-inhabilitar")) {
      const btn = e.target.closest(".btn-inhabilitar");
      const userId = btn.dataset.id;
      if (await confirmAction({ message: "¿Inhabilitar usuario?" })) {
        try {
          const response = await fetch(`/api/usuarios/perfiles/${userId}/`, {
            method: "PATCH",
            headers: {
              "X-CSRFToken": csrfToken,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ is_active: false }),
          });
          const data = await response.json();
          if (validarErrorDRF(response, data)) return;
          toastSuccess(data.message);
          table.ajax.reload();
        } catch (e) {
          toastError(e);
        }
      }
    }
    if (e.target.closest(".btn-habilitar")) {
      const btn = e.target.closest(".btn-habilitar");
      const userId = btn.dataset.id;
      if (await confirmAction({ message: "¿Habilitar usuario?" })) {
        try {
          const response = await fetch(`/api/usuarios/perfiles/${userId}/`, {
            method: "PATCH",
            headers: {
              "X-CSRFToken": csrfToken,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ is_active: true }),
          });
          const data = await response.json();
          if (validarErrorDRF(response, data)) return;
          toastSuccess(data.message);
          table.ajax.reload();
        } catch (e) {
          toastError(e);
        }
      }
    }
    if (e.target.closest(".btn-permisos")) {
      const btn = e.target.closest(".btn-permisos");
      currentUserId = btn.dataset.id;
      const usuarioNombre = btn.dataset.usuario;

      // Mostrar el nombre del usuario en el modal
      modalPermisos.querySelector(".modal-title").textContent =
        "Permisos de " + usuarioNombre;

      // Limpiar el formulario antes de cargar
      permisosForm.reset();
      setFormDisabled(permisosForm, true);
      document.getElementById("btn-guardarPerm").disabled = true;
      // Cargar permisos actuales con GET
      try {
        const response = await fetch(
          `/api/usuarios/permisos/?perfil=${currentUserId}`
        );
        const data = await response.json();
        if (validarErrorDRF(response, data)) return;

        data.forEach((el) => {
          const { modu, acci, filtro } = el;

          const ckBoxName = `${modu}_${acci}`;
          const filtroName = `${modu}_filtro`;

          const checkbox = permisosForm.querySelector(`[name="${ckBoxName}"]`);
          if (checkbox) {
            checkbox.checked = true;
          }

          if (filtro !== null) {
            const filtroInput = permisosForm.querySelector(
              `[name="${filtroName}"]`
            );
            if (filtroInput) {
              filtroInput.value = JSON.stringify(filtro, null, 2);
            }
          }
        });
      } catch (err) {
        console.error("Error cargando permisos:", err);
        toastError("No se pudieron cargar los permisos del usuario.");
      } finally {
        setFormDisabled(permisosForm, false);
        document.getElementById("btn-guardarPerm").disabled = false;
      }
    }
  });

  const passwordInput = document.getElementById("new-password");

  if (passwordInput) {
    passwordInput.addEventListener("input", () => {
      const value = passwordInput.value;

      toggleRule("rule-length", value.length >= 8);
      toggleRule("rule-uppercase", /[A-Z]/.test(value));
      toggleRule("rule-lowercase", /[a-z]/.test(value));
      toggleRule("rule-number", /\d/.test(value));
      toggleRule(
        "rule-special",
        /[!@#$%^&*(),.?":{}|<>_\-+=/\\[\]`~%$]/.test(value)
      );
    });
  }

  function toggleRule(id, isValid) {
    const element = document.getElementById(id);
    if (!element) return;

    if (isValid) {
      element.classList.remove("text-danger");
      element.classList.add("text-success");
      element.textContent = element.textContent.replace("🔴", "🟢");
    } else {
      element.classList.remove("text-success");
      element.classList.add("text-danger");
      element.textContent = element.textContent.replace("🟢", "🔴");
    }
  }

  document
    .getElementById("form-reset")
    .addEventListener("submit", async (e) => {
      e.preventDefault();

      const userId = document.getElementById("user-id-reset").value;
      const password = document.getElementById("new-password").value;
      const btn = document.getElementById("btn-submit-contra");
      const originalBtnContent = btn.innerHTML;
      showSpinner(btn);
      try {
        const response = await fetch(`/api/usuario/restablecer_contrasena/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({
            user_id: userId,
            new_password: password,
          }),
        });

        const data = await response.json();
        if (response.ok) {
          toastSuccess(data.message);
          const modal = bootstrap.Modal.getInstance(
            document.getElementById("modalReset")
          );
          modal.hide();
        } else {
          toastError(
            `Error: ${
              data.message || data.error || "No se pudo cambiar la contraseña"
            }`
          );
        }
      } catch (error) {
        console.error(error);
        toastError("Error inesperado");
      } finally {
        hideSpinner(btn, originalBtnContent);
      }
    });

  const modalPermisos = document.getElementById("modalPermisos");
  const permisosForm = document.getElementById("permisosForm");
  let currentUserId = null;

  // Guardar permisos
  document
    .getElementById("btn-guardarPerm")
    .addEventListener("click", async (e) => {
      e.preventDefault();
      if (!currentUserId) return;
      const btn = document.getElementById("btn-guardarPerm");
      const originalBtnContent = btn.innerHTML;

      showSpinner(btn);
      // Construir objeto con los datos del formulario
      const formData = new FormData(permisosForm);
      setFormDisabled(permisosForm, true);
      const permisos = {};
      for (const [key, value] of formData.entries()) {
        const input = permisosForm.querySelector(`[name="${key}"]`);
        if (input.type === "checkbox") {
          permisos[key] = input.checked;
        } else {
          try {
            // Intentar parsear JSON en campos de texto
            permisos[key] = JSON.parse(value);
          } catch {
            permisos[key] = value;
          }
        }
      }

      try {
        // 1. Eliminar permisos actuales de este perfil
        await fetch(
          `/api/usuarios/permisos/eliminar_por_perfil/?perfil_id=${currentUserId}`,
          {
            method: "DELETE",
            headers: { "X-CSRFToken": csrfToken },
          }
        );

        // 2. Crear nuevos permisos con los datos del formulario
        const entries = Object.entries(permisos);
        for (const [key, value] of entries) {
          if (value && value !== "" && value !== false) {
            // separar "modulo_accion"
            if (key.includes("_")) {
              const [modu, acci] = key.split("_");

              if (acci === "filtro") {
                const check = await fetch(
                  `/api/usuarios/permisos/?perfil=${currentUserId}&modu=${modu}&acci=ver`
                );
                const data = await check.json();

                if (data.length > 0) {
                  const permisoId = data[0].id;
                  await fetch(`/api/usuarios/permisos/${permisoId}/`, {
                    method: "PATCH",
                    headers: {
                      "Content-Type": "application/json",
                      "X-CSRFToken": csrfToken,
                    },
                    body: JSON.stringify({ filtro: value }),
                  });
                } else {
                  const response = await fetch("/api/usuarios/permisos/", {
                    method: "POST",
                    headers: {
                      "Content-Type": "application/json",
                      "X-CSRFToken": csrfToken,
                    },
                    body: JSON.stringify({
                      perfil: currentUserId,
                      modu: modu,
                      acci: "ver",
                      filtro: value,
                    }),
                  });
                  const data = await response.json();
                  if (validarErrorDRF(response, data)) return;
                }
              } else {
                const response = await fetch("/api/usuarios/permisos/", {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                  },
                  body: JSON.stringify({
                    perfil: currentUserId,
                    modu: modu,
                    acci: acci,
                    filtro: null,
                  }),
                });
                const data = await response.json();
                if (validarErrorDRF(response, data)) return;
              }
            }
          }
        }

        toastSuccess("Permisos actualizados correctamente");
        const modal = bootstrap.Modal.getInstance(modalPermisos);
        modal.hide();
      } catch (err) {
        console.error("Error guardando permisos:", err);
        toastError("No se pudieron guardar los permisos.");
      } finally {
        hideSpinner(btn, originalBtnContent);
        setFormDisabled(permisosForm, false);
      }
    });
});
