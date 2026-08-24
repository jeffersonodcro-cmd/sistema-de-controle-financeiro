/* Configuração compartilhada dos gráficos (tema escuro combinando com o CSS). */

const CORES = {
  grid: "#1A222C",
  gridZero: "#232C38",
  texto: "#8A97A6",
  accent: "#3DD9B0",
  danger: "#F4737F",
  warning: "#F5B759",
  invest: "#8FA6FF",
  surface: "#101720",
  paleta: ["#3DD9B0", "#F4737F", "#F5B759", "#8FA6FF", "#C084FC", "#38BDF8", "#FB923C", "#F472B6", "#4ADE80"],
};

Chart.defaults.color = CORES.texto;
Chart.defaults.font.family = "'JetBrains Mono', ui-monospace, monospace";

function formatarMoedaAbrev(valor) {
  const abs = Math.abs(valor);
  if (abs >= 1000) return (valor / 1000).toFixed(abs >= 10000 ? 0 : 1).replace(".", ",") + "k";
  return String(Math.round(valor));
}

function formatarMoedaCompleta(valor) {
  return "R$ " + valor.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const centroDonutPlugin = {
  id: "centroDonut",
  afterDraw(chart) {
    if (chart.config.type !== "doughnut") return;
    const total = chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
    const { ctx, chartArea } = chart;
    const cx = (chartArea.left + chartArea.right) / 2;
    const cy = (chartArea.top + chartArea.bottom) / 2;
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = "#E9EEF3";
    ctx.font = "700 16px 'JetBrains Mono', monospace";
    ctx.fillText(formatarMoedaAbrev(total), cx, cy);
    ctx.restore();
  },
};

function criarGraficoPizza(canvasId, labels, valores) {
  const el = document.getElementById(canvasId);
  if (!el) return;
  new Chart(el, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: valores,
        backgroundColor: CORES.paleta,
        borderColor: CORES.surface,
        borderWidth: 2,
      }],
    },
    options: {
      cutout: "74%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            boxWidth: 9,
            boxHeight: 9,
            padding: 12,
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
            generateLabels(chart) {
              const data = chart.data;
              const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
              return data.labels.map((label, i) => {
                const valor = data.datasets[0].data[i];
                const pct = total > 0 ? Math.round((valor / total) * 100) : 0;
                return {
                  text: `${label} · ${pct}%`,
                  fillStyle: data.datasets[0].backgroundColor[i],
                  strokeStyle: data.datasets[0].backgroundColor[i],
                  index: i,
                };
              });
            },
          },
        },
        tooltip: {
          callbacks: { label: (ctx) => `${ctx.label}: ${formatarMoedaCompleta(ctx.raw)}` },
        },
      },
    },
    plugins: [centroDonutPlugin],
  });
}

function criarGraficoBarras(canvasId, labels, receitas, despesas) {
  const el = document.getElementById(canvasId);
  if (!el) return;
  const ctx = el.getContext("2d");

  const gradReceita = ctx.createLinearGradient(0, 0, 0, 220);
  gradReceita.addColorStop(0, "#4FE0BC");
  gradReceita.addColorStop(1, "#2FA98C");

  const gradDespesa = ctx.createLinearGradient(0, 0, 0, 220);
  gradDespesa.addColorStop(0, "#FF8A94");
  gradDespesa.addColorStop(1, "#C9505E");

  new Chart(el, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        { label: "Receitas", data: receitas, backgroundColor: gradReceita, borderRadius: { topLeft: 4, topRight: 4 }, borderSkipped: false, barThickness: 9, categoryPercentage: 0.7, barPercentage: 0.9 },
        { label: "Despesas", data: despesas, backgroundColor: gradDespesa, borderRadius: { topLeft: 4, topRight: 4 }, borderSkipped: false, barThickness: 9, categoryPercentage: 0.7, barPercentage: 0.9 },
      ],
    },
    options: {
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${formatarMoedaCompleta(c.raw)}` } },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { family: "'JetBrains Mono', monospace", size: 10 } },
        },
        y: {
          grid: { color: (c) => (c.tick.value === 0 ? CORES.gridZero : CORES.grid) },
          beginAtZero: true,
          ticks: {
            font: { family: "'JetBrains Mono', monospace", size: 10 },
            callback: (v) => formatarMoedaAbrev(v),
          },
        },
      },
    },
  });
}

function criarGraficoLinha(canvasId, labels, valores) {
  const el = document.getElementById(canvasId);
  if (!el) return;
  new Chart(el, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        data: valores,
        borderColor: CORES.invest,
        backgroundColor: "rgba(143, 166, 255, 0.15)",
        fill: true,
        tension: 0.3,
        pointRadius: 3,
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: { grid: { color: CORES.grid }, beginAtZero: true },
      },
    },
  });
}
