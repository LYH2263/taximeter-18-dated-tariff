<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'

const FIELDS = [
  ['start_price', '起步价'],
  ['start_include_km', '含公里'],
  ['per_km', '每公里'],
  ['per_slow_min', '低速单价'],
  ['night_factor', '夜间系数'],
]

const cur = ref(null)
const sched = ref(null)
const showSchedForm = ref(false)
const curMsg = ref('')
const schedMsg = ref('')

const blank = () => ({ start_price: '', start_include_km: '', per_km: '', per_slow_min: '', night_factor: '' })
const curForm = ref(blank())
const schedForm = ref({ effective_date: '', ...blank() })

const load = async () => {
  const b = await getJSON('/api/tariff')
  cur.value = b.current
  sched.value = b.scheduled
  curForm.value = { ...blank(), ...Object.fromEntries(FIELDS.map(([k]) => [k, b.current?.[k] ?? ''])) }
  if (b.scheduled) schedForm.value = { ...b.scheduled }
}
onMounted(load)

const validate = (f) => {
  for (const [k, label] of FIELDS) {
    const v = Number(f[k])
    if (f[k] === '' || Number.isNaN(v)) return `${label}必须是数字`
    if (k === 'start_price' ? v <= 0 : (k === 'night_factor' ? v < 1 : v < 0)) {
      return k === 'start_price' ? '起步价必须大于 0' : k === 'night_factor' ? '夜间系数不能小于 1' : `${label}不能为负`
    }
  }
  return ''
}

const errText = (e) => {
  try {
    const d = JSON.parse(e.message)?.detail
    if (Array.isArray(d)) return d.map(x => x.msg).join('；')
    return String(d ?? e.message)
  } catch { return String(e.message) }
}

const saveCurrent = async () => {
  curMsg.value = ''
  const bad = validate(curForm.value)
  if (bad) { curMsg.value = bad; return }
  try {
    const r = await postJSON('/api/tariff/current', { ...curForm.value })
    cur.value = r.current
    curMsg.value = '已保存现行运价'
  } catch (e) { curMsg.value = errText(e) }
}

const saveScheduled = async () => {
  schedMsg.value = ''
  const bad = validate(schedForm.value)
  if (bad) { schedMsg.value = bad; return }
  if (!schedForm.value.effective_date) { schedMsg.value = '请选择生效日期'; return }
  try {
    const r = await postJSON('/api/tariff/scheduled', { ...schedForm.value })
    sched.value = r.scheduled
    schedForm.value = { ...r.scheduled }
    showSchedForm.value = false
    schedMsg.value = `预约运价已登记，将于 ${r.scheduled.effective_date} 起生效`
  } catch (e) { schedMsg.value = errText(e) }
}
</script>
<template>
  <div class="page">
    <h1>运价表</h1>

    <div class="panel">
      <h2>现行运价</h2>
      <label v-for="[k, label] in FIELDS" :key="k">
        {{ label }} <input type="number" step="0.01" v-model="curForm[k]" />
      </label>
      <div><button @click="saveCurrent">保存现行运价</button></div>
      <p v-if="curMsg" :class="{ err: !curMsg.startsWith('已保存') }">{{ curMsg }}</p>
    </div>

    <div class="panel">
      <h2>预约运价</h2>
      <template v-if="sched && !showSchedForm">
        <p>将于 <strong>{{ sched.effective_date }}</strong> 起生效（再次保存将覆盖）</p>
        <button @click="showSchedForm = true">修改预约运价</button>
      </template>
      <template v-else>
        <p v-if="!sched">未设置预约运价</p>
        <label>生效日期 <input type="date" v-model="schedForm.effective_date" /></label>
        <label v-for="[k, label] in FIELDS" :key="k">
          {{ label }} <input type="number" step="0.01" v-model="schedForm[k]" />
        </label>
        <div>
          <button @click="saveScheduled">保存预约运价</button>
          <button v-if="sched" class="ghost" @click="showSchedForm = false; schedForm = { ...sched }">取消</button>
        </div>
      </template>
      <p v-if="schedMsg" :class="{ err: !schedMsg.startsWith('预约运价已登记') }">{{ schedMsg }}</p>
    </div>
  </div>
</template>
