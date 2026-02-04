<template>
  <section>
    <div class="toolbar">
      <input
        v-model="q"
        class="input"
        placeholder="Buscar por razão social ou CNPJ..."
        @keyup.enter="buscar"
      />
      <button class="btn" @click="buscar">Buscar</button>
      <button class="btn" @click="limpar">Limpar</button>

      <div class="spacer"></div>

      <label class="label">
        Por página:
        <select v-model.number="limit" class="select" @change="mudarLimit">
          <option :value="10">10</option>
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </label>
    </div>

    <p v-if="erro" class="erro">{{ erro }}</p>

    <table class="table" v-if="!erro">
      <thead>
        <tr>
          <th>Razão Social</th>
          <th>CNPJ</th>
          <th>UF</th>
          <th>Modalidade</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="op in data" :key="op.registro_ans">
          <td>{{ op.razao_social }}</td>
          <td>{{ op.cnpj }}</td>
          <td>{{ op.uf }}</td>
          <td>{{ op.modalidade }}</td>
        </tr>
      </tbody>
    </table>

    

    <div class="pager">
      <button class="btn" :disabled="page<=1" @click="page--; carregar()">Anterior</button>
      <span>Página {{ page }} / {{ totalPages }}</span>
      <button class="btn" :disabled="page>=totalPages" @click="page++; carregar()">Próxima</button>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";

const API = "http://127.0.0.1:8000";

const data = ref([]);
const page = ref(1);
const limit = ref(25);
const total = ref(0);
const q = ref("");
const erro = ref("");

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit.value)));

async function carregar() {
  erro.value = "";
  try {
    const params = new URLSearchParams({
      page: String(page.value),
      limit: String(limit.value),
    });
    if (q.value.trim()) params.set("q", q.value.trim());

    const res = await fetch(`${API}/api/operadoras?${params.toString()}`);
    if (!res.ok) throw new Error(`API erro: ${res.status}`);
    const json = await res.json();
    data.value = json.data || [];
    total.value = json.total || 0;
  } catch (e) {
    erro.value = "Erro ao carregar operadoras.";
    console.error(e);
  }
}

function buscar() {
  page.value = 1;
  carregar();
}

function limpar() {
  q.value = "";
  page.value = 1;
  carregar();
}

function mudarLimit() {
  page.value = 1;
  carregar();
}

onMounted(carregar);
</script>

<style scoped>
.table-wrap {
  max-height: 520px;      
  overflow: auto;         
  border: 1px solid #ddd; 
}

.table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 0;         
}

.table th, .table td {
  border: 1px solid #ddd;
  padding: 6px 8px;
  font-size: 13px;
  vertical-align: top;
}


.table td:nth-child(1) {
  max-width: 420px;     
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}


.pager {
  position: sticky; 
  bottom: 0;
  background: #fff;
  padding: 10px 0;
  border-top: 1px solid #ddd;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}

</style>

