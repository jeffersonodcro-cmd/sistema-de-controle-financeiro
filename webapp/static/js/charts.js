/* Configuração compartilhada dos gráficos (tema escuro combinando com o CSS). */

const CORES = {
  grid: "#2a2f3d",
  texto: "#9aa1b4",
  brand: "#5b8def",
  success: "#34c77b",
  danger: "#ef5a6f",
  paleta: ["#5b8def", "#34c77b", "#f0ad4e", "#ef5a6f", "#a78bfa", "#38bdf8", "#fb923c", "#f472b6", "#4ade80"],
};

Chart.defaults.color = CORES.texto;
Chart.defaults.font.family = "'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Arial, sans-serif";

function criarGraficoPizza(canvasId, labels, valores) {
  const el = document.getElementById(canvasId);
  if (!el) return;
  new Chart(el, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{ data: valores, backgroundColor: CORES.paleta, borderWidth: 0 }],
    },
    options: {
      plugins: { legend: { position: "bottom", labels: { boxWidth: 10, padding: 12 } } },
      cutout: "62%",
    },
  });
}

function criarGraficoBarras(canvasId, labels, receitas, despesas) {
  const el = document.getElementById(canvasId);
  if (!el) return;
  new Chart(el, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        { label: "Receitas", data: receitas, backgroundColor: CORES.success, borderRadius: 4 },
        { label: "Despesas", data: despesas, backgroundColor: CORES.danger, borderRadius: 4 },
      ],
    },
    options: {
      plugins: { legend: { position: "bottom" } },
      scales: {
        x: { grid: { display: false } },
        y: { grid: { color: CORES.grid }, beginAtZero: true },
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
        borderColor: CORES.brand,
        backgroundColor: "rgba(91, 141, 239, 0.15)",
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
