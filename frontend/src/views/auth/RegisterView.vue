<template>
  <div class="auth-page">
    <div class="auth-layout">
      <section class="auth-hero">
        <span class="section-label">Create Account</span>
        <h1>注册一个账号，开始管理你的面试资料与知识库。</h1>
        <p>注册后即可登录系统，继续保留当前项目里的所有上传、问答和入库能力。</p>
      </section>

      <section class="card">
        <h2>注册账号</h2>
        <el-form :model="form" label-position="top" @submit.prevent="handleSubmit">
          <el-form-item label="用户名">
            <el-input v-model="form.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="邮箱">
            <el-input v-model="form.email" placeholder="请输入邮箱" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" type="password" show-password placeholder="至少 8 位" />
          </el-form-item>
          <el-button type="primary" :loading="submitting" class="full" @click="handleSubmit">注册</el-button>
        </el-form>
        <p v-if="message" class="success">{{ message }}</p>
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
        <RouterLink to="/login" class="switch-link">已有账号？去登录</RouterLink>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";

import { useAuthStore } from "../../stores/auth";

const authStore = useAuthStore();

const form = reactive({
  username: "",
  email: "",
  password: ""
});
const submitting = ref(false);
const message = ref("");
const errorMessage = ref("");

async function handleSubmit() {
  if (!form.username || !form.email || !form.password) {
    errorMessage.value = "请完整填写注册信息。";
    return;
  }
  submitting.value = true;
  errorMessage.value = "";
  message.value = "";
  try {
    await authStore.register(form);
    message.value = "注册成功，请返回登录页继续登录。";
    form.username = "";
    form.email = "";
    form.password = "";
  } catch {
    errorMessage.value = "注册失败，请检查后端服务或输入信息。";
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
    linear-gradient(145deg, rgba(255, 255, 255, 0.9), rgba(255, 247, 239, 0.8));
  border: 1px solid rgba(255, 255, 255, 0.72);
  box-shadow: var(--shadow-lg);
}

.auth-hero h1 {
  margin: 16px 0 12px;
  font-size: clamp(2rem, 4vw, 3.2rem);
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

.success {
  color: #147d64;
  margin: 12px 0;
}

@media (max-width: 900px) {
  .auth-layout {
    grid-template-columns: 1fr;
  }
}
</style>
