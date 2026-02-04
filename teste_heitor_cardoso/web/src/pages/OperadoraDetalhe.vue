<template>
  <div>
    <router-link to="/">← Voltar</router-link>

    <div v-if="loading">Carregando...</div>
    <div v-else-if="erro" class="erro">{{ erro }}</div>

    <div v-else>
      <h2>{{ operadora.razao_social }}</h2>
      <p><b>CNPJ:</b> {{ formatCnpj(operadora.cnpj) }}</p>
      <p><b>UF:</b> {{ operadora.uf }}</p>
      <p><b>Modalidade:</b> {{ operadora.modalidade }}</p>

      <h3>Histórico de despesas</h3>

      <div v-if="loadingDesp">Carregando despesas...</div>
      <div v-else-if="erroDesp" class="erro">{{ erroDesp }}</div>

      <table v-else class="tabela">
        <thead>
          <tr>
            <th>Ano</th>
            <th>Trimestre</th>
            <th>Valor</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in despesas" :key="d.id">
            <td>{{ d.ano }}</td>
            <td>{{ d.trimestre }}</td>
            <td>{{ formatMoney(d.valor_despesas) }}</td>
          </tr>
        </tbody>
      </table>

      <div v-if="despesas.length === 0">
        Essa operadora não tem despesas registradas nos 3 trimestres analisados.
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { api } from "../api";
import { useRoute } from "vue-router";

const route = useRoute();
const cnpj = route.params.cnpj;

const operadora = ref(null);
const despesas = ref([]);

const loading = ref(false);
const erro = ref("");

const loadingDesp = ref(false);
const erroDesp = ref("");

function formatCnpj(cnpj) {
  if (!cnpj) return "";
  const digits = String(cnpj).replace(/\D/g, "");
  if (digits.length !== 14) return digits;
  return digits.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, "$1.$2.$3/$4-$5");
}

function formatMoney(v) {
  const n = Number(v || 0);
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

async function carregarOperadora() {
  loading.value = true;
  erro.value = "";
  try {
    const resp = await api.get(`/api/operadoras/${cnpj}`);
    operadora.value = resp.data;
  } catch (e) {
    erro.value = "Operadora não encontrada.";
  } finally {
    loading.value = false;
  }
}

async function carregarDespesas() {
  loadingDesp.value = true;
  erroDesp.value = "";
  try {
    const resp = await api.get(`/api/operadoras/${cnpj}/despesas`);
    despesas.value = resp.data;
  } catch (e) {
    erroDesp.value = "Erro ao carregar despesas.";
  } finally {
    loadingDesp.value = false;
  }
}

onMounted(async () => {
  await carregarOperadora();
  await carregarDespesas();
});
</script>

<style>
.tabela {
  width: 100%;
  border-collapse: collapse;
}
.tabela th, .tabela td {
  border: 1px solid #ddd;
  padding: 8px;
}
.erro {
  color: #b00020;
}
</style>
