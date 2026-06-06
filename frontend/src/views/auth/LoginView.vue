<template>
  <div class="auth-page">
    <div class="auth-layout">
      <section class="auth-hero">
        <span class="section-label">Interview Agent</span>
        <h1>更简洁的面试知识工作台，从登录开始。</h1>
        <p>登录后即可继续使用知识库、文档上传、入库任务和 RAG 问答，不影响任何原有功能。</p>
      </section>

      <section class="card">
        <h2>登录</h2>
        <el-form :model="form" label-position="top" @submit.prevent="handleSubmit">
          <el-form-item label="邮箱">
            <el-input v-model="form.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
          </el-form-item>
          <el-button type="primary" :loading="submitting" class="full" @click="handleSubmit">登录</el-button>
        </el-form>
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
        <RouterLink to="/register" class="switch-link">还没有账号？去注册</RouterLink>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "../../stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const form = reactive({
  email: "",
  password: ""
});
const submitting = ref(false);
const errorMessage = ref("");

async function handleSubmit() {
  if (!form.email || !form.password) {
    errorMessage.value = "请填写邮箱和密码。";
    return;
  }
  submitting.value = true;
  errorMessage.value = "";
  try {
    await authStore.login(form);
    await router.push("/");
  } catch {
    errorMessage.value = "登录失败，请检查账号信息或后端服务状态。";
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.auth-page {
  display: grid;
  min-height: 100vh;
  padding: 24px;
  place-items: center;
}

.auth-layout {
  display: grid;
  grid-template-columns: minmax(280px, 520px) minmax(320px, 420px);
  gap: 24px;
  width: min(1040px, 100%);
}

.auth-hero {
  padding: 36px;
  border-radius: 28px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.9), rgba(241, 248, 255, 0.76));
  border: 1px solid rgba(255, 255, 255, 0.72);
  box-shadow: var(--shadow-lg);
}

.auth-hero h1 {
  margin: 16px 0 12px;
  font-size: clamp(2rem, 4vw, 3.3rem);
  line-height: 1.1;
}

.auth-hero p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.card {
  width: 100%;
  padding: 32px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid var(--border-soft);
  border-radius: 24px;
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(18px);
}

.card h2 {
  margin: 0 0 20px;
}

.full {
  width: 100%;
}

.switch-link {
  display: inline-block;
  margin-top: 14px;
  color: #2356a8;
  font-weight: 600;
}

.error {
  color: #c2410c;
  margin: 12px 0;
}

@media (max-width: 900px) {
  .auth-layout {
    grid-template-columns: 1fr;
  }
}
</style>
