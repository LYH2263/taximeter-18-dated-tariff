<script setup>
import { ref } from 'vue'
import { postJSON } from '../api'
const distance_km = ref(8)
const slow_min = ref(3)
const night = ref(false)
const service_date = ref('')
const out = ref(null)
const err = ref('')
const run = async () => {
  err.value = ''
  try {
    out.value = await postJSON('/api/fare', {
      distance_km: distance_km.value, slow_min: slow_min.value,
      night: night.value, persist: true,
      service_date: service_date.value || null,
    })
  } catch (e) { err.value = String(e.message || e); out.value = null }
}
</script>
<template>
  <div class="page"><h1>打表试算</h1>
    <div class="panel">
      <label>公里 <input type="number" v-model.number="distance_km" /></label>
      <label>低速分钟 <input type="number" v-model.number="slow_min" /></label>
      <label>服务日期 <input type="date" v-model="service_date" /></label>
      <label><input type="checkbox" v-model="night" /> 夜间</label>
      <button @click="run">计算</button>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
    <div v-if="out">
      <p class="hero-num">¥{{ out.total }}
        <span class="badge">{{ out.tariff_source === 'scheduled' ? '预约价' : '现行价' }}</span>
        <span v-if="out.effective_date" class="badge">{{ out.effective_date }} 起</span>
      </p>
      <p>起步 {{ out.start }} · 里程 {{ out.mileage }} · 低速 {{ out.slow_fee }} · 夜间系数 {{ out.night_factor }}</p>
      <p class="muted">
        起步价 {{ out.tariff.start_price }} · 含公里 {{ out.tariff.start_include_km }} ·
        每公里 {{ out.tariff.per_km }} · 低速单价 {{ out.tariff.per_slow_min }} ·
        夜间系数 {{ out.tariff.night_factor }}
      </p>
    </div>
  </div>
</template>
