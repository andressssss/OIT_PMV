document.addEventListener("DOMContentLoaded", async () => {
  const ENDPOINTS = {
    kpis: "/api/dashboard/kpis/",
    fichasChart: "/api/dashboard/fichas/",
    usuariosChart: "/api/dashboard/usuarios-rol/",
    rapsChart: "/api/dashboard/juicios/",
  };

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

  // ========= KPIs =========
  async function loadKpis() {
    const data = await fetchData(ENDPOINTS.kpis);
    if (!data) return;
    setText("kpi-total-fichas", data.total_fichas || "--");
    setText("kpi-fichas-sin-juicios", data.fichas_sin_juicios || "--");
    setText("kpi-fichas-con-juicios", data.fichas_con_juicios || "--");
    setText("kpi-total-usuarios", data.usuarios_total || "--");
    setText("kpi-usuarios-activos", data.usuarios_activos || "--");
    setText("kpi-usuarios-inactivos", data.usuarios_inactivos || "--");
    setText("kpi-documentos-total", data.documentos_total || "--");
    setText("kpi-documentos-fichas", data.documentos_fichas || "--");
    setText("kpi-documentos-aprendices", data.documentos_aprendices || "--");
    setText("kpi-carpetas-vacias-total", data.carpetas_vacias_total || "--");
    setText("kpi-carpetas-vacias-fichas", data.carpetas_vacias_fichas || "--");
    setText(
      "kpi-carpetas-vacias-aprendices",
      data.carpetas_vacias_aprendices || "--"
    );
  }

  const CHART_COLORS = [
    "#01B8AA",
    "#374649",
    "#FD625E",
    "#F2C80F",
    "#5F6B6D",
    "#8AD4EB",
    "#FE9666",
    "#A66999",
    "#3599B8",
    "#DFBFBF",
  ];

  // ========= Render ECharts Donut =========
  function renderDonutChart(elId, title, dataset) {
    const el = document.getElementById(elId);
    if (!el) return;

    const chart = echarts.init(el);

    chart.setOption({
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
          confine: true, // 👈 evita que se salga de la pantalla
          formatter: function (params) {
            return `${params.data.fullName}<br/>${params.value} (${params.percent}%)`;
          },
        },
        legend: {
          orient: "vertical",
          right: 10,
          top: "middle",
          type: "scroll",
          formatter: function (name) {
            const maxLength = 10;
            return name.length > maxLength
              ? name.substring(0, maxLength) + "..."
              : name;
          },
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
              label: {
                show: true,
                fontSize: 16,
                fontWeight: "bold",
                formatter: "{b}\n{d}%",
              },
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

    window.addEventListener("resize", () => chart.resize());
  }

  // ========= Load Charts =========
  async function loadCharts() {
    // Fichas
    const fichas = await fetchData(ENDPOINTS.fichasChart);
    if (fichas) {
      renderDonutChart("chart-fichas", "Fichas", fichas);
    }

    // Usuarios
    const usuarios = await fetchData(ENDPOINTS.usuariosChart);
    if (usuarios) {
      renderDonutChart("chart-usuarios", "Usuarios", usuarios);
    }

    // RAPS
    const raps = await fetchData(ENDPOINTS.rapsChart);
    if (raps) {
      renderDonutChart("chart-raps", "RAPS", raps);
    }
  }

  await loadKpis();
  await loadCharts();
});
