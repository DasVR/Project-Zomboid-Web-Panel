const cpuData = [];
const ramData = [];
const labels = [];

const cpuCtx = document.getElementById("cpuChart").getContext("2d");
const ramCtx = document.getElementById("ramChart").getContext("2d");

const cpuChart = new Chart(cpuCtx, {
  type: "line",
  data: {
    labels: labels,
    datasets: [{
      label: 'CPU %',
      data: cpuData,
      fill: true,
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      borderColor: 'rgba(59, 130, 246, 1)',
      tension: 0.3,
      pointRadius: 3,
    }]
  },
  options: {
    responsive: false,
    animation: false,
    maintainAspectRatio: true,
    plugins: {
      legend: { labels: { color: "white" } }
    },
    scales: {
      x: {
        ticks: { color: "gray" },
        grid: { color: "rgba(255,255,255,0.1)" }
      },
      y: {
        min: 0,
        max: 100,
        ticks: { color: "gray" },
        grid: { color: "rgba(255,255,255,0.1)" }
      }
    }
  }
});

const ramChart = new Chart(ramCtx, {
  type: "line",
  data: {
    labels: labels,
    datasets: [{
      label: 'RAM %',
      data: ramData,
      fill: true,
      backgroundColor: 'rgba(168, 85, 247, 0.1)',
      borderColor: 'rgba(168, 85, 247, 1)',
      tension: 0.3,
      pointRadius: 2,
    }]
  },
  options: {
    responsive: false,
    animation: false,
    maintainAspectRatio: true,
    plugins: {
      legend: { labels: { color: "white" } }
    },
    scales: {
      x: {
        ticks: { color: "gray" },
        grid: { color: "rgb(255, 255, 255)" }
      },
      y: {
        min: 0,
        max: 100,
        ticks: { color: "gray" },
        grid: { color: "rgb(255, 255, 255)" }
      }
    }
  }
});

function fetchMetrics() {
  fetch("/stats")
    .then((res) => res.json())
    .then((data) => {
      const time = new Date().toLocaleTimeString();
      if (labels.length > 20) {
        labels.shift();
        cpuData.shift();
        ramData.shift();
      }
      labels.push(time);
      cpuData.push(data.cpu);
      ramData.push(data.ram);
      cpuChart.update();
      ramChart.update();
    });
}
setInterval(fetchMetrics, 3000);
