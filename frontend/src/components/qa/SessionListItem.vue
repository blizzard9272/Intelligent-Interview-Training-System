<template>
  <button
    type="button"
    class="session-item"
    :class="{ active }"
    @click="$emit('select')"
  >
    <div v-if="badge || secondaryLabel" class="session-item-head">
      <strong>{{ title }}</strong>
      <span v-if="badge" class="pill">{{ badge }}</span>
    </div>
    <strong v-else>{{ title }}</strong>
    <span v-if="secondaryLabel" class="session-secondary">{{ secondaryLabel }}</span>
    <span v-if="timeLabel" class="session-time">{{ timeLabel }}</span>
  </button>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  timeLabel?: string;
  secondaryLabel?: string;
  badge?: string;
  active?: boolean;
}>();

defineEmits<{
  (event: "select"): void;
}>();
</script>

<style scoped>
.session-item {
  text-align: left;
  border: 1px solid rgba(20, 33, 61, 0.06);
  background: rgba(243, 247, 251, 0.86);
  border-radius: 16px;
  padding: 16px;
  cursor: pointer;
  display: grid;
  gap: 8px;
  transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}

.session-item:hover {
  transform: translateY(-1px);
  border-color: rgba(31, 111, 235, 0.2);
  box-shadow: var(--shadow-sm);
}

.session-item.active {
  background: rgba(31, 111, 235, 0.1);
  border-color: rgba(31, 111, 235, 0.24);
}

.session-item-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.session-secondary,
.session-time {
  color: var(--text-secondary);
}
</style>
