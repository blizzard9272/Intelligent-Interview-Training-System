<template>
  <div class="auth-page">
    <div class="card">
      <h2>登录 Interview Agent</h2>
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
      <RouterLink to="/register">没有账号？去注册</RouterLink>
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
    errorMessage.value = "请填写邮箱和密码";
    return;
  }
  submitting.value = true;
  errorMessage.value = "";
  try {
    await authStore.login(form);
    await router.push("/");
  } catch (error) {
    errorMessage.value = "登录失败，请检查账号或后端服务状态";
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
</style>
