import http from "./http";

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface UserInfo {
  id: number;
  username: string;
  email: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export async function register(payload: RegisterPayload) {
  const { data } = await http.post<UserInfo>("/auth/register", payload);
  return data;
}

export async function login(payload: LoginPayload) {
  const { data } = await http.post<TokenResponse>("/auth/login", payload);
  return data;
}

export async function fetchMe() {
  const { data } = await http.get<UserInfo>("/auth/me");
  return data;
}
