<script setup>
import { ref } from 'vue'
import { postJSON } from '../api'
const distance_km = ref(8)
const slow_min = ref(3)
const night = ref(false)
const service_date = ref('')
const persist = ref(true)
const out = ref(null)
const err = ref('')
const run = async () => {
  err.value = ''
  const body = { distance_km: distance_km.value, slow_min: slow_min.value, night: night.value, persist: persist.value }
  if (service_date.value) body.service_date = service_date.value
  try { out.value = await postJSON('/api/fare', body) } catch (e) { err.value = e.message }
}
</script>
<template>
  <div class="page"><h1>打表试算</h1>
    <div class="panel">
      <label>公里 <input type="number" v-model.number="distance_km" /></label>
      <label>低速分钟 <input type="number" v-model.number="slow_min" /></label>
      <label><input type="checkbox" v-model="night" /> 夜间</label>
      <label>服务日期 <input type="date" v-model="service_date" /></label>
      <label><input type="checkbox" v-model="persist" /> 写入记录</label>
      <button @click="run">计算</button>
    </div>
    <p v-if="err" class="bad">{{ err }}</p>
    <div v-if="out" class="panel">
      <p class="hero-num">¥{{ out.total }}</p>
      <p>取价：{{ out.tariff_source === 'scheduled' ? '预约运价' : '现行运价' }}<template v-if="out.service_date">（服务日期 {{ out.service_date }}）</template> · {{ out.run_id ? `已写入记录 #${out.run_id}` : '只读未写记录' }}</p>
      <table>
        <tr><th>起步价</th><th>含公里</th><th>每公里</th><th>低速单价</th><th>夜间系数</th></tr>
        <tr><td>{{ out.tariff.start_price }}</td><td>{{ out.tariff.start_include_km }}</td><td>{{ out.tariff.per_km }}</td><td>{{ out.tariff.per_slow_min }}</td><td>{{ out.tariff.night_factor }}</td></tr>
      </table>
    </div>
  </div>
</template>
