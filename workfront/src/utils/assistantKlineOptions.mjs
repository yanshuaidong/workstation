const DEFAULT_UP_COLOR = '#ef5350'
const DEFAULT_DOWN_COLOR = '#26a69a'
const WEEKDAY_NAMES = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

function normalizeNumber(value) {
  if (value === null || value === undefined || value === '') {
    return null
  }
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : null
}

function normalizeVolume(value) {
  const numeric = normalizeNumber(value)
  return numeric === null ? 0 : numeric
}

export function formatTradeDateWithWeekday(value) {
  if (!value) {
    return '-'
  }

  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) {
    return String(value)
  }

  return `${value} ${WEEKDAY_NAMES[date.getDay()]}`
}

export function filterVarietiesByName(varieties = [], keyword = '') {
  const normalizedKeyword = String(keyword || '').trim()
  if (!normalizedKeyword) {
    return [...varieties]
  }

  return varieties.filter((item) => String(item?.name || '').includes(normalizedKeyword))
}

function formatTooltipValue(value) {
  return value === null || value === undefined || value === '' ? '-' : value
}

function buildKlineTooltipFormatter(params = []) {
  const [candlestick, volume] = params
  const tradeDate = formatTradeDateWithWeekday(candlestick?.axisValue || volume?.axisValue || '')
  const priceData = Array.isArray(candlestick?.data) ? candlestick.data : []

  return [
    tradeDate,
    `开盘: ${formatTooltipValue(priceData[0])}`,
    `收盘: ${formatTooltipValue(priceData[1])}`,
    `最低: ${formatTooltipValue(priceData[2])}`,
    `最高: ${formatTooltipValue(priceData[3])}`,
    `成交量: ${formatTooltipValue(volume?.data)}`
  ].join('<br/>')
}

function buildIndexTooltipFormatter(params = []) {
  const firstItem = params[0] || {}
  return [
    formatTradeDateWithWeekday(firstItem.axisValue || ''),
    `${firstItem.seriesName || '数值'}: ${formatTooltipValue(firstItem.data)}`
  ].join('<br/>')
}

export function normalizeAssistantKlineData(data = {}) {
  const klineRows = Array.isArray(data.kline) ? data.kline : []
  const strengthRows = Array.isArray(data.strength) ? data.strength : []
  const strengthMap = new Map(
    strengthRows.map((row) => [row?.trade_date, row || {}])
  )

  const dates = []
  const ohlcv = []
  const volumes = []
  const mainForce = []
  const retail = []

  klineRows.forEach((row) => {
    const tradeDate = row?.trade_date
    if (!tradeDate) {
      return
    }

    const strengthRow = strengthMap.get(tradeDate) || {}
    dates.push(tradeDate)
    ohlcv.push([
      normalizeNumber(row?.open),
      normalizeNumber(row?.close),
      normalizeNumber(row?.low),
      normalizeNumber(row?.high)
    ])
    volumes.push(normalizeVolume(row?.volume))
    mainForce.push(normalizeNumber(strengthRow.main_force))
    retail.push(normalizeNumber(strengthRow.retail))
  })

  return {
    dates,
    ohlcv,
    volumes,
    mainForce,
    retail,
    varietyName: data?.variety?.name || ''
  }
}

export function getZoomRange(length) {
  if (!length) {
    return { start: 0, end: 100 }
  }
  if (length <= 20) {
    return { start: 0, end: 100 }
  }
  return {
    start: Math.max(0, Math.round(((length - 20) / length) * 100)),
    end: 100
  }
}

export function buildAssistantKlineOption({
  dates = [],
  ohlcv = [],
  volumes = [],
  title = '',
  upColor = DEFAULT_UP_COLOR,
  downColor = DEFAULT_DOWN_COLOR
} = {}) {
  const zoomRange = getZoomRange(dates.length)

  return {
    title: { text: `${title} K线`, left: 12, top: 8, textStyle: { fontSize: 13, color: '#3c5168' } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' }, formatter: buildKlineTooltipFormatter },
    axisPointer: { link: [{ xAxisIndex: [0, 1] }] },
    grid: [
      { left: 60, right: 16, top: 44, bottom: 80 },
      { left: 60, right: 16, height: 50, bottom: 20 }
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0, axisLabel: { show: false } },
      { type: 'category', data: dates, gridIndex: 1, axisLabel: { fontSize: 11 } }
    ],
    yAxis: [
      { scale: true, gridIndex: 0, splitLine: { lineStyle: { color: '#f0f4f8' } } },
      { scale: true, gridIndex: 1, splitLine: { show: false }, axisLabel: { formatter: (value) => `${(value / 10000).toFixed(0)}w` } }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: zoomRange.start, end: zoomRange.end },
      { type: 'slider', xAxisIndex: [0, 1], bottom: 4, height: 14, start: zoomRange.start, end: zoomRange.end }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: ohlcv,
        itemStyle: {
          color: upColor,
          color0: downColor,
          borderColor: upColor,
          borderColor0: downColor
        }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        sampling: false,
        coordinateSystem: 'cartesian2d',
        data: volumes,
        itemStyle: { color: '#b0bec5' }
      }
    ]
  }
}

export function buildAssistantIndexOption({
  dates = [],
  values = [],
  title = '',
  color = '#2f7cff'
} = {}) {
  const zoomRange = getZoomRange(dates.length)

  return {
    title: { text: title, left: 12, top: 6, textStyle: { fontSize: 13, color: '#3c5168' } },
    tooltip: { trigger: 'axis', formatter: buildIndexTooltipFormatter },
    grid: { left: 60, right: 16, top: 36, bottom: 28 },
    xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 11 } },
    yAxis: { scale: true, splitLine: { lineStyle: { color: '#f0f4f8' } } },
    dataZoom: [{ type: 'inside', start: zoomRange.start, end: zoomRange.end }],
    series: [{
      name: title,
      type: 'line',
      coordinateSystem: 'cartesian2d',
      sampling: false,
      data: values,
      smooth: false,
      connectNulls: false,
      showSymbol: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { color, width: 2 }
    }]
  }
}
