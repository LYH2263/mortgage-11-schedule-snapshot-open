<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
const detail = ref(null)
const error = ref('')
onMounted(async () => { items.value = (await getJSON('/api/history')).items })
const open = async (id) => {
  error.value = ''
  try {
    detail.value = await getJSON(`/api/history/${id}`)
  } catch (e) {
    detail.value = null
    error.value = `记录 #${id} 不存在或已删除`
  }
}
</script>
<template><div class="page"><h1>试算记录</h1>
<table>
  <tr><th>编号</th><th>时间</th><th>摘要月供</th><th>利息合计</th><th></th></tr>
  <tr v-for="h in items" :key="h.id">
    <td>#{{ h.id }}</td><td>{{ h.created_at }}</td>
    <td>{{ h.monthly_payment ?? '—' }}</td><td>{{ h.total_interest ?? '—' }}</td>
    <td><button @click="open(h.id)">打开</button></td>
  </tr>
</table>
<p v-if="error" class="err">{{ error }}</p>
<div v-if="detail" class="pinned">
  <h2>记录 #{{ detail.id }}（写入时快照）</h2>
  <p>写入时输入：本金 {{ detail.input.principal }} · 年利率 {{ detail.input.annual_rate }}% · {{ detail.input.months }} 期</p>
  <p>月供 <span class="hero-num">{{ detail.result.monthly_payment }}</span> · 利息合计 {{ detail.result.total_interest }}</p>
  <table v-if="detail.result.preview && detail.result.preview.length">
    <tr><th>期</th><th>月供</th><th>本金</th><th>利息</th><th>余额</th></tr>
    <tr v-for="r in detail.result.preview" :key="r.period">
      <td>{{ r.period }}</td><td>{{ r.payment }}</td><td>{{ r.principal }}</td><td>{{ r.interest }}</td><td>{{ r.balance }}</td>
    </tr>
  </table>
</div>
</div></template>
<style scoped>
.err { color: #a33; }
.pinned { margin-top: 1rem; border-top: 2px solid var(--accent); padding-top: 0.5rem; }
</style>
