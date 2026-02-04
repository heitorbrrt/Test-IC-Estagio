import { createRouter, createWebHistory } from "vue-router";
import OperadorasTable from "./pages/OperadorasTable.vue";
import GraficoUF from "./pages/GraficoUF.vue";

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: OperadorasTable },
    { path: "/grafico", component: GraficoUF },
  ],
});
