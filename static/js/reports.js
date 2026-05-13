(function () {
    const yearSelect = document.getElementById("report-year");
    const monthSelect = document.getElementById("report-month");
    const toggle = document.getElementById("granularity-toggle");
    const ordersTotalEl = document.getElementById("orders-total");
    const revenueTotalEl = document.getElementById("revenue-total");

    const ordersCanvas = document.getElementById("orders-chart");
    const revenueCanvas = document.getElementById("revenue-chart");

    if (!yearSelect || !monthSelect || !toggle || !ordersCanvas || !revenueCanvas) {
        return;
    }

    let granularity = "daily";
    let ordersChart = null;
    let revenueChart = null;

    const accentGreen = "#315c35";
    const accentGreenSoft = "rgba(49, 92, 53, 0.15)";
    const accentBlue = "#3d6f91";
    const accentBlueSoft = "rgba(61, 111, 145, 0.15)";

    function formatNumber(value) {
        return value.toLocaleString("tr-TR");
    }

    function sum(arr) {
        let total = 0;
        for (let i = 0; i < arr.length; i++) {
            total += arr[i];
        }
        return total;
    }

    function buildChartConfig(labels, data, color, fill) {
        return {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    borderColor: color,
                    backgroundColor: fill,
                    borderWidth: 2.5,
                    pointBackgroundColor: color,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    tension: 0.35,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#2f2f2f",
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: function (ctx) {
                                return formatNumber(ctx.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: "#666", font: { size: 11 } }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: "#f1e7d8" },
                        ticks: {
                            color: "#666",
                            font: { size: 11 },
                            callback: function (value) {
                                return formatNumber(value);
                            }
                        }
                    }
                }
            }
        };
    }

    function renderCharts(payload) {
        const labels = payload.labels;

        if (ordersChart) {
            ordersChart.data.labels = labels;
            ordersChart.data.datasets[0].data = payload.orders;
            ordersChart.update();
        } else {
            ordersChart = new Chart(
                ordersCanvas.getContext("2d"),
                buildChartConfig(labels, payload.orders, accentGreen, accentGreenSoft)
            );
        }

        if (revenueChart) {
            revenueChart.data.labels = labels;
            revenueChart.data.datasets[0].data = payload.revenue;
            revenueChart.update();
        } else {
            revenueChart = new Chart(
                revenueCanvas.getContext("2d"),
                buildChartConfig(labels, payload.revenue, accentBlue, accentBlueSoft)
            );
        }

        ordersTotalEl.textContent = "Toplam: " + formatNumber(sum(payload.orders));
        revenueTotalEl.textContent = "Toplam: " + formatNumber(sum(payload.revenue)) + " TL";
    }

    async function fetchAndRender() {
        const params = new URLSearchParams({
            granularity: granularity,
            year: yearSelect.value,
            month: monthSelect.value
        });

        try {
            const response = await fetch("/api/reports/data?" + params.toString());

            if (!response.ok) {
                throw new Error("Veri alınamadı");
            }

            const data = await response.json();
            renderCharts(data);
        } catch (error) {
            console.error(error);
        }
    }

    function updateMonthVisibility() {
        const isMonthly = granularity === "monthly";
        monthSelect.disabled = isMonthly;
        monthSelect.style.opacity = isMonthly ? "0.4" : "1";
    }

    toggle.addEventListener("click", function (event) {
        const button = event.target.closest("button[data-granularity]");
        if (!button) return;

        granularity = button.dataset.granularity;

        toggle.querySelectorAll("button").forEach(function (b) {
            b.classList.toggle("active", b === button);
        });

        updateMonthVisibility();
        fetchAndRender();
    });

    yearSelect.addEventListener("change", fetchAndRender);
    monthSelect.addEventListener("change", fetchAndRender);

    updateMonthVisibility();
    fetchAndRender();
})();
