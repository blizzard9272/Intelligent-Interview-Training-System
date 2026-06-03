<template>
  <div class="auth-page">
    <div class="card">
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
      <RouterLink to="/login">已有账号？去登录</RouterLink>
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
    errorMessage.value = "请完整填写注册信息";
    return;
  }
  submitting.value = true;
  errorMessage.value = "";
  message.value = "";
  try {
    await authStore.register(form);
    message.value = "注册成功，请返回登录页登录";
    form.username = "";
    form.email = "";
    form.password = "";
  } catch {
    errorMessage.value = "注册失败，请检查后端服务或输入信息"
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.auth-page {
  display: grid;
  place-items: center;
  min-height: 100vh;
}

.card {
  width: 420px;
  padding: 32px;
  background: #ffffff;
  border-radius: 18px;
  box-shadow: 0 18px 60px rgba(15, 23, 42, 0.08);
}

.full {
  width: 100%;
}

.error {
  color: #dc2626;
  margin: 12px 0;
}

.success {
  color: #15803d;
  margin: 12px 0;
}
</style>
