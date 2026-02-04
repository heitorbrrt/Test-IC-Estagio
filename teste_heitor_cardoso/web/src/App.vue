<template>
  <div class="container">
    <header class="topbar">
      <h1>Operadoras ANS</h1>
      <nav class="nav">
        <RouterLink to="/" class="link" active-class="active">Operadoras</RouterLink>
        <RouterLink to="/grafico" class="link" active-class="active">Gráfico (UF)</RouterLink>
      </nav>
    </header>

    <main>
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.container { max-width: 1100px; margin: 0 auto; padding: 16px; font-family: Arial, sans-serif; }
.topbar { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
h1 { margin: 0; font-size: 28px; }
.nav { display: flex; gap: 12px; }
.link { text-decoration: none; color: #333; padding: 6px 10px; border: 1px solid #ddd; }
.active { background: #f3f3f3; }
</style>
