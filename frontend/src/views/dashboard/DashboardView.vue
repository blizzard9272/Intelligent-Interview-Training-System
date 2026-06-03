<template>
  <AppShell>
    <div class="grid">
      <section class="hero">
        <h2>项目概览</h2>
        <p>一期目标是打通知识库上传、异步入库和 RAG 问答闭环。</p>
      </section>
      <section class="hero">
        <h2>当前用户</h2>
        <p v-if="authStore.user">{{ authStore.user.username }} / {{ authStore.user.email }}</p>
        <p v-else>尚未加载用户信息</p>
      </section>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import AppShell from "../../layout/AppShell.vue";
import { useAuthStore } from "../../stores/auth";

const authStore = useAuthStore();
</script>

<style scoped>
.grid {
  display: grid;
  gap: 20px;
}

.hero {
  padding: 28px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 18px 60px rgba(15, 23, 42, 0.06);
}
</style>
