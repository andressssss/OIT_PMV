document.addEventListener("DOMContentLoaded", async () => {
  const ENDPOINTS = {
    kpis: "/api/dashboard/kpis/",
    fichasChart: "/api/dashboard/fichas/",
    usuariosChart: "/api/dashboard/usuarios-rol/",
    rapsChart: "/api/dashboard/juicios/",
  };

  const chartInstances = {};
  let filtroDesde = "";
  let filtroHasta = "";

  function buildUrl(base) {
    const params = new URLSearchParams();
    if (filtroDesde) params.set("desde", filtroDesde);
    if (filtroHasta) params.set("hasta", filtroHasta);
    const qs = params.toString();
    return qs ? `${base}?${qs}` : base;
  }

  async function fetchData(url) {
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error("Error en el request");
      return await response.json();
    } catch (error) {
      console.error("❌ Error al cargar:", url, error);
      return null;
    }
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  async function loadKpis() {
    const data = await fetchData(buildUrl(ENDPOINTS.kpis));
    if (!data) return;
    setText("kpi-total-fichas", data.total_fichas ?? "--");
    setText("kpi-fichas-sin-juicios", data.fichas_sin_juicios ?? "--");
    setText("kpi-fichas-con-juicios", data.fichas_con_juicios ?? "--");
    setText("kpi-total-usuarios", data.usuarios_total ?? "--");
    setText("kpi-usuarios-activos", data.usuarios_activos ?? "--");
    setText("kpi-usuarios-inactivos", data.usuarios_inactivos ?? "--");
    setText("kpi-documentos-total", data.documentos_total ?? "--");
    setText("kpi-documentos-fichas", data.documentos_fichas ?? "--");
    setText("kpi-documentos-aprendices", data.documentos_aprendices ?? "--");
    setText("kpi-carpetas-vacias-total", data.carpetas_vacias_total ?? "--");
    setText("kpi-carpetas-vacias-fichas", data.carpetas_vacias_fichas ?? "--");
    setText("kpi-carpetas-vacias-aprendices", data.carpetas_vacias_aprendices ?? "--");
  }

  const CHART_COLORS = [
    "#01B8AA", "#374649", "#FD625E", "#F2C80F", "#5F6B6D",
    "#8AD4EB", "#FE9666", "#A66999", "#3599B8", "#DFBFBF",
  ];

  function renderDonutChart(elId, title, dataset) {
    const el = document.getElementById(elId);
    if (!el) return;

    if (!chartInstances[elId]) {
      chartInstances[elId] = echarts.init(el);
      window.addEventListener("resize", () => chartInstances[elId].resize());
    }

    chartInstances[elId].setOption({
      baseOption: {
        title: {
          text: title,
          left: "left",
          top: 10,
          textStyle: { fontSize: 14 },
        },
        tooltip: {
          show: true,
          trigger: "item",
          confine: true,
          formatter: (params) =>
            `${params.data.fullName}<br/>${params.value} (${params.percent}%)`,
        },
        legend: {
          orient: "vertical",
          right: 10,
          top: "middle",
          type: "scroll",
          formatter: (name) =>
            name.length > 10 ? name.substring(0, 10) + "..." : name,
        },
        series: [
          {
            name: title,
            type: "pie",
            radius: ["40%", "70%"],
            center: ["30%", "50%"],
            avoidLabelOverlap: true,
            label: { show: false, position: "center" },
            emphasis: {
              label: { show: true, fontSize: 16, fontWeight: "bold", formatter: "{b}\n{d}%" },
            },
            labelLine: { show: false },
            data: dataset.map((item, i) => ({
              value: item.total,
              name: item.alias,
              fullName: item.nombre,
              itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
            })),
          },
        ],
      },
      media: [
        {
          query: { maxWidth: 768 },
          option: {
            legend: { top: "bottom", left: "center", orient: "horizontal" },
            series: [{ center: ["50%", "45%"] }],
          },
        },
        {
          query: { maxWidth: 480 },
          option: {
            legend: { top: "bottom", left: "center", orient: "horizontal" },
            series: [{ center: ["50%", "50%"], radius: ["35%", "65%"] }],
          },
        },
      ],
    });
  }

  async function loadCharts() {
    const [fichas, usuarios, raps] = await Promise.all([
      fetchData(buildUrl(ENDPOINTS.fichasChart)),
      fetchData(buildUrl(ENDPOINTS.usuariosChart)),
      fetchData(buildUrl(ENDPOINTS.rapsChart)),
    ]);
    if (fichas) renderDonutChart("chart-fichas", "Fichas", fichas);
    if (usuarios) renderDonutChart("chart-usuarios", "Usuarios", usuarios);
    if (raps) renderDonutChart("chart-raps", "RAPS", raps);
  }

  function toISODate(d) {
    return d.toISOString().split("T")[0];
  }

  function aplicarPreset(preset) {
    const hoy = new Date();
    const desdeInput = document.getElementById("filtro-desde");
    const hastaInput = document.getElementById("filtro-hasta");

    if (preset === "mes_actual") {
      desdeInput.value = toISODate(new Date(hoy.getFullYear(), hoy.getMonth(), 1));
      hastaInput.value = toISODate(hoy);
    } else if (preset === "mes_anterior") {
      desdeInput.value = toISODate(new Date(hoy.getFullYear(), hoy.getMonth() - 1, 1));
      hastaInput.value = toISODate(new Date(hoy.getFullYear(), hoy.getMonth(), 0));
    } else if (preset === "ultimos_30") {
      const d = new Date(hoy);
      d.setDate(d.getDate() - 30);
      desdeInput.value = toISODate(d);
      hastaInput.value = toISODate(hoy);
    } else if (preset === "todo") {
      desdeInput.value = "";
      hastaInput.value = "";
    }
  }

  async function recargarDashboard() {
    filtroDesde = document.getElementById("filtro-desde")?.value || "";
    filtroHasta = document.getElementById("filtro-hasta")?.value || "";
    await Promise.all([loadKpis(), loadCharts()]);
  }

  document.querySelectorAll("[data-preset]").forEach((btn) => {
    btn.addEventListener("click", () => {
      aplicarPreset(btn.dataset.preset);
      recargarDashboard();
    });
  });

  document.getElementById("btn-aplicar-filtro")?.addEventListener("click", recargarDashboard);

  await Promise.all([loadKpis(), loadCharts()]);
});
