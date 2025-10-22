import { hideSpinner, resetForm, showSpinner, fetchData, setText, setFormDisabled, csrfToken, toastSuccess } from "/static/js/utils.js";

document.addEventListener("DOMContentLoaded", () => {
  const ENDPOINTS = {
    indicadores: "/api/dashboard/novedades/kpis/",
    crear_novedad: "/api/dashboard/novedades/crear/",
  };

  loadIndicadores();

  const tableEl = document.getElementById("tabla-novedades");
  const table = new DataTable(tableEl, {
    serverSide: true,
    processing: false,
    ajax: {
      url: "/api/dashboard/novedades/filtrar/",
      type: "GET",
    },
    columns: [
      { data: "num", title: "Numero" },
      { data: "descri", title: "Descripcion",
        render: function (data, type, row){
          if (type === 'display' && data) {
            return data.length > 50 ? data.substring(0, 50) + "..." : data;
          }
          return data;
        }
      },
      { data: "tipo", title: "Tipo" },
      { data: "esta", title: "Estado" },
      { data: "fecha", title: "Fecha" },
      {
        data: null,
        render: function (data, type, row) {
          return `<a class='btn btn-sm btn-outline-primary' href='/novedad/${row.id}/'><i class="bi bi-search"></i></a>`;
        },
      },
    ],
    language: {
      url: "https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json",
    },
  });

  async function loadIndicadores() {
    const data = await fetchData(ENDPOINTS.indicadores);
    setText("kpi-total-novedades", data?.total_novedades ?? "--");
    setText("kpi-novedades-pendientes", data?.nove_pendi ?? "--");
    setText("kpi-novedades-gestion", data?.nove_gesti ?? "--");
    setText("kpi-novedades-cerradas", data?.nove_cerra ?? "--");
  }


  const formNuevaNovedad = document.getElementById("form-nueva-novedad");
  formNuevaNovedad.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("btn-submit");
    const originalBtnContent = btn.innerHTML;
    const formData = new FormData(formNuevaNovedad);
    const modal = bootstrap.Modal.getInstance(
      document.getElementById("modalNuevaNovedad")
    );
    showSpinner(btn)
    setFormDisabled(formNuevaNovedad, true);

    await fetchData(ENDPOINTS.crear_novedad, {
      method: "POST",
      body: formData,
      headers: { "X-CSRFToken": csrfToken },
    });
    resetForm(formNuevaNovedad);
    hideSpinner(btn, originalBtnContent);
    setFormDisabled(formNuevaNovedad, false);
    modal.hide();
    table.ajax.reload();
    toastSuccess("Registro creado exitosamente");
    loadIndicadores();
  });
});
