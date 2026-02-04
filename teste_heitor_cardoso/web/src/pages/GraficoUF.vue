<template>
  <section>
    <h2>Distribuição de despesas por UF</h2>
    <p v-if="erro" class="erro">{{ erro }}</p>
    <canvas ref="canvas"></canvas>
  </section>
</template>

<script setup>
import { ref, onMounted } from "vue";
import Chart from "chart.js/auto";

const API = "http://127.0.0.1:8000";
const canvas = ref(null);
const erro = ref("");
let chart;

onMounted(async () => {
  erro.value = "";
  try {
    const res = await fetch(`${API}/api/ufs`);
    if (!res.ok) throw new Error(`API erro: ${res.status}`);
    const json = await res.json();
    console.log("primeiro item:", json[0]);
    console.log("chaves:", Object.keys(json[0] || {}));

    

    const labels = json.map(x => x.uf);

    function toNumber(v) {
    if (v === null || v === undefined) return 0;
    const s0 = String(v).trim();
    if (!s0) return 0;

    // remove tudo que não seja dígito, ponto, vírgula ou sinal
    const s = s0.replace(/[^\d,.\-]/g, "");

    // pt-BR: 1.234.567,89
    if (s.includes(".") && s.includes(",")) {
        const n = Number(s.replace(/\./g, "").replace(",", "."));
        return Number.isFinite(n) ? n : 0;
    }

    // decimal com vírgula: 123,45
    if (s.includes(",")) {
        const n = Number(s.replace(",", "."));
        return Number.isFinite(n) ? n : 0;
    }

    const n = Number(s);
    return Number.isFinite(n) ? n : 0;
    }

    const values = json.map(x =>
    toNumber(
        x.total_uf ?? x.total ?? x.total_despesas ?? x.totalDespesas ?? x.valor ?? 0
    )
    );

    console.log("max:", Math.max(...values));


    

    chart = new Chart(canvas.value, {
      type: "bar",
      data: {
        labels,
        datasets: [{ label: "Total de despesas", data: values }],
      },
      options: {
        responsive: true,
      },
    });
  } catch (e) {
    erro.value = "Erro ao carregar dados do gráfico (UF).";
    console.error(e);
  }
});
</script>

<style scoped>
h2 { margin-top: 12px; }
.erro { color: #b00020; }
</style>