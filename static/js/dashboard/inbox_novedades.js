import { fetchData, setText, setFormDisabled } from "/static/js/utils.js";

document.addEventListener("DOMContentLoaded", () => {
  const ENDPOINTS = {
    indicadores: "/api/dashboard/indicadores/",
    crear_novedad: "/api/dashboard/novedades/",
  };

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
      { data: "descri", title: "Descripcion" },
      { data: "tipo", title: "Tipo" },
      { data: "esta", title: "Estado" },
      { data: "fecha", title: "Fecha" },
      {
        data: null,
        render: function (data, type, row) {
          return "HOla!";
        },
      },
    ],
    language: {
      url: "https://cdn.datatables.net/plug-ins/2.1.8/i18n/es-ES.json",
    },
  });

  const formEl = document.getElementById("form-nueva-novedad");
  formEl.addEventListener("submit", (e) => {
    e.preventDefault();
    const formData = new FormData(formEl);
  });

  async function loadIndicadores() {
    const data = await fetchData(ENDPOINTS.indicadores);
    setText("kpi-total-novedades", data?.total ?? "--");
    setText("kpi-novedades-pendientes", data?.pendientes ?? "--");
    setText("kpi-novedades-gestion", data?.gestion ?? "--");
    setText("kpi-novedades-cerradas", data?.cerradas ?? "--");
  }

  const formNuevaNovedad = document.getElementById("form-nueva-novedad");
  formNuevaNovedad.addEventListener("submit", async (e) => {
    e.preventDefault();
    setFormDisabled(formNuevaNovedad, true);
    const formData = new FormData(form);
    try {
      const data = await fetchData(ENDPOINTS.crear_novedad);
      toastSuccess(data.message);
    } catch (e) {
      toastError(e);
    }
  });
});
