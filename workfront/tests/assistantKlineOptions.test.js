const assert = require('node:assert/strict')

async function main() {
  const {
    buildAssistantIndexOption,
    buildAssistantKlineOption,
    filterVarietiesByName,
    formatTradeDateWithWeekday,
    getZoomRange,
    normalizeAssistantKlineData
  } = await import('../src/utils/assistantKlineOptions.mjs')

  const rawPayload = {
    variety: { name: '铁矿石' },
    kline: [
      { trade_date: '2026-04-01', open: 700, close: 710, low: 695, high: 715, volume: 120000 },
      { trade_date: '2026-04-02', open: 710, close: 705, low: 701, high: 716, volume: 98000 }
    ],
    strength: [
      { trade_date: '2026-04-01', main_force: null, retail: null },
      { trade_date: '2026-04-02', main_force: '0.56', retail: '-0.22' }
    ]
  }

  const normalized = normalizeAssistantKlineData(rawPayload)

  assert.equal(normalized.varietyName, '铁矿石')
  assert.deepEqual(normalized.dates, ['2026-04-01', '2026-04-02'])
  assert.deepEqual(normalized.ohlcv[0], [700, 710, 695, 715])
  assert.equal(normalized.mainForce[0], null)
  assert.equal(normalized.mainForce[1], 0.56)
  assert.equal(normalized.retail[1], -0.22)

  const shortZoom = getZoomRange(2)
  assert.deepEqual(shortZoom, { start: 0, end: 100 })

  const longZoom = getZoomRange(60)
  assert.equal(longZoom.end, 100)
  assert.ok(longZoom.start > 0)

  const klineOption = buildAssistantKlineOption({
    dates: normalized.dates,
    ohlcv: normalized.ohlcv,
    volumes: normalized.volumes,
    title: normalized.varietyName
  })
  assert.equal(klineOption.series[1].sampling, false)
  assert.equal(klineOption.series[1].coordinateSystem, 'cartesian2d')
  assert.equal(klineOption.dataZoom[0].start, 0)
  assert.equal(
    klineOption.tooltip.formatter([
      { axisValue: '2026-04-01', seriesName: 'K线', data: [700, 710, 695, 715] },
      { axisValue: '2026-04-01', seriesName: '成交量', data: 120000 }
    ]).includes('2026-04-01 周三'),
    true
  )

  const indexOption = buildAssistantIndexOption({
    dates: normalized.dates,
    values: normalized.mainForce,
    title: '铁矿石 主力指数',
    color: '#2f7cff',
    gradientFactory: (stops) => ({ type: 'linear-gradient', stops })
  })
  assert.equal(indexOption.series[0].sampling, false)
  assert.equal(indexOption.series[0].coordinateSystem, 'cartesian2d')
  assert.equal(indexOption.series[0].data[0], null)
  assert.equal(indexOption.series[0].smooth, false)
  assert.equal(indexOption.series[0].areaStyle, undefined)
  assert.equal(indexOption.series[0].showSymbol, true)
  assert.equal(indexOption.series[0].symbol, 'circle')
  assert.equal(indexOption.series[0].symbolSize, 6)
  assert.equal(
    indexOption.tooltip.formatter([
      { axisValue: '2026-04-02', seriesName: '铁矿石 主力指数', data: 0.56, marker: '' }
    ]).includes('2026-04-02 周四'),
    true
  )

  assert.equal(formatTradeDateWithWeekday('2026-04-18'), '2026-04-18 周六')

  const varieties = [
    { id: 1, name: '螺纹钢' },
    { id: 2, name: '铁矿石' },
    { id: 3, name: '焦煤' }
  ]
  assert.deepEqual(
    filterVarietiesByName(varieties, '铁'),
    [{ id: 2, name: '铁矿石' }]
  )
  assert.deepEqual(filterVarietiesByName(varieties, 'jm'), [])

  console.log('assistant kline option tests passed')
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
