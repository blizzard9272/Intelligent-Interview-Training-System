<template>
  <div class="shell">
    <aside class="sidebar">
      <h1>Interview Agent</h1>
      <nav>
        <RouterLink to="/">概览</RouterLink>
        <RouterLink to="/knowledge-bases">知识库</RouterLink>
        <RouterLink to="/documents">文档</RouterLink>
        <RouterLink to="/qa">问答</RouterLink>
        <RouterLink to="/history">历史</RouterLink>
      </nav>
    </aside>
    <main class="content">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 100vh;
}

.sidebar {
  padding: 24px;
  background: #132238;
  color: #f8fafc;
}

.sidebar h1 {
  margin: 0 0 24px;
  font-size: 22px;
}

.sidebar nav {
  display: grid;
  gap: 12px;
}

.sidebar a {
  padding: 10px 12px;
  border-radius: 10px;
  color: #dbeafe;
}

.sidebar a.router-link-active {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.content {
  padding: 32px;
}
</style>
