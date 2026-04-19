const assert = require('node:assert/strict')

async function main() {
  const { buildAssistantContextChartOption } = await import('../src/utils/assistantContextChartOptions.mjs')

  const option = buildAssistantContextChartOption({
    seriesData: [
      { trade_date: '2026-04-01', close_price: 701.2, main_force: 0.35, retail: -0.18 },
      { trade_date: '2026-04-02', close_price: 705.6, main_force: null, retail: 0.08 }
    ]
  })

  const mainForceSeries = option.series[1]
  const retailSeries = option.series[2]

  assert.equal(mainForceSeries.name, '主力')
  assert.equal(mainForceSeries.type, 'line')
  assert.equal(mainForceSeries.showSymbol, true)
  assert.equal(mainForceSeries.symbol, 'circle')
  assert.equal(mainForceSeries.symbolSize, 6)
  assert.deepEqual(mainForceSeries.data, [0.35, null])

  assert.equal(retailSeries.name, '散户')
  assert.equal(retailSeries.type, 'line')
  assert.equal(retailSeries.showSymbol, true)
  assert.equal(retailSeries.symbol, 'circle')
  assert.equal(retailSeries.symbolSize, 6)
  assert.deepEqual(retailSeries.data, [-0.18, 0.08])

  console.log('assistant context chart option tests passed')
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
