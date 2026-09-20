<script setup>
import { onMounted, reactive, ref } from 'vue'
import { getJSON, putJSON } from '../api'

const blank = { start_price: 0, start_include_km: 0, per_km: 0, per_slow_min: 0, night_factor: 1 }
const current = reactive({ ...blank })
const sched = reactive({ effective_date: '', ...blank })
const scheduled = ref(null)
const msg = ref('')
const err = ref('')

const fill = (dst, src) => { for (const k of Object.keys(blank)) dst[k] = src[k] }
const load = async () => {
  const t = await getJSON('/api/tariff')
  fill(current, t.current)
  scheduled.value = t.scheduled
  if (t.scheduled) { fill(sched, t.scheduled); sched.effective_date = t.scheduled.effective_date }
}
const saveCurrent = async () => {
  msg.value = ''; err.value = ''
  try { fill(current, await putJSON('/api/tariff', current)); msg.value = '现行运价已保存' }
  catch (e) { err.value = '校验失败，未保存：' + e.message }
}
const saveScheduled = async () => {
  msg.value = ''; err.value = ''
  try { scheduled.value = await putJSON('/api/tariff/scheduled', sched); msg.value = '预约运价已登记' }
  catch (e) { err.value = '校验失败，未登记：' + e.message }
}
onMounted(load)
</script>
<template>
  <div class="page"><h1>运价表</h1>
    <p v-if="msg" class="ok">{{ msg }}</p>
    <p v-if="err" class="bad">{{ err }}</p>
    <div class="panel">
      <h2>现行运价</h2>
      <label>起步价 <input type="number" step="0.1" v-model.number="current.start_price" /></label>
      <label>含公里 <input type="number" step="0.1" v-model.number="current.start_include_km" /></label>
      <label>每公里 <input type="number" step="0.1" v-model.number="current.per_km" /></label>
      <label>低速单价 <input type="number" step="0.1" v-model.number="current.per_slow_min" /></label>
      <label>夜间系数 <input type="number" step="0.01" v-model.number="current.night_factor" /></label>
      <button @click="saveCurrent">保存现行</button>
    </div>
    <div class="panel">
      <h2>预约运价</h2>
      <p v-if="scheduled">已登记：{{ scheduled.effective_date }} 起生效 · 起步 ¥{{ scheduled.start_price }} / 含 {{ scheduled.start_include_km }}km · 每公里 ¥{{ scheduled.per_km }} · 低速 ¥{{ scheduled.per_slow_min }}/分 · 夜间 ×{{ scheduled.night_factor }}</p>
      <p v-else>未登记预约运价</p>
      <label>生效日期 <input type="date" v-model="sched.effective_date" /></label>
      <label>起步价 <input type="number" step="0.1" v-model.number="sched.start_price" /></label>
      <label>含公里 <input type="number" step="0.1" v-model.number="sched.start_include_km" /></label>
      <label>每公里 <input type="number" step="0.1" v-model.number="sched.per_km" /></label>
      <label>低速单价 <input type="number" step="0.1" v-model.number="sched.per_slow_min" /></label>
      <label>夜间系数 <input type="number" step="0.01" v-model.number="sched.night_factor" /></label>
      <button @click="saveScheduled">登记预约</button>
    </div>
  </div>
</template>
