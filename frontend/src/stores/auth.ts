import { defineStore } from "pinia";

import { fetchMe, login, LoginPayload, register, RegisterPayload, UserInfo } from "../api/auth";

interface AuthState {
  token: string;
  user: UserInfo | null;
}

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    token: localStorage.getItem("access_token") || "",
    user: null
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token)
  },
  actions: {
    setToken(token: string) {
      this.token = token;
      localStorage.setItem("access_token", token);
    },
    async register(payload: RegisterPayload) {
      return register(payload);
    },
    async login(payload: LoginPayload) {
      const result = await login(payload);
      this.setToken(result.access_token);
      await this.loadCurrentUser();
      return result;
    },
    async loadCurrentUser() {
      if (!this.token) {
        return null;
      }
      const user = await fetchMe();
      this.user = user;
      return user;
    },
    clearAuth() {
      this.token = "";
      this.user = null;
      localStorage.removeItem("access_token");
    }
  }
});

export type { UserInfo };
