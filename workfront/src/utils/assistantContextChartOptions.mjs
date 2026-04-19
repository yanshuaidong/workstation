function formatValue(value) {
  return value !== null && value !== undefined ? Number(value).toFixed(2) : '--'
}

export function buildAssistantContextChartOption({ seriesData = [] } = {}) {
  const dates = seriesData.map((item) => item.trade_date)
  const closeSeries = seriesData.map((item) => item.close_price)
  const mainForceSeries = seriesData.map((item) => item.main_force)
  const retailSeries = seriesData.map((item) => item.retail)

  return {
    color: ['#2f7cff', '#db7c26', '#2f9d62'],
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const date = params?.[0]?.axisValue || '--'
        const lines = params.map((item) => `${item.marker}${item.seriesName}：${formatValue(item.data)}`)
        return [`日期：${date}`, ...lines].join('<br/>')
      }
    },
    legend: {
      top: 0,
      data: ['收盘价', '主力', '散户']
    },
    grid: [
      { top: 40, left: 50, right: 20, height: '42%' },
      { left: 50, right: 20, top: '60%', height: '28%' }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        boundaryGap: false
      },
      {
        type: 'category',
        data: dates,
        boundaryGap: false,
        gridIndex: 1
      }
    ],
    yAxis: [
      {
        type: 'value',
        scale: true,
        name: '收盘价'
      },
      {
        type: 'value',
        scale: true,
        gridIndex: 1,
        name: '资金值'
      }
    ],
    series: [
      {
        name: '收盘价',
        type: 'line',
        smooth: true,
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 6,
        data: closeSeries,
        lineStyle: { width: 3 },
        areaStyle: {
          opacity: 0.12
        }
      },
      {
        name: '主力',
        type: 'line',
        xAxisIndex: 1,
        yAxisIndex: 1,
        smooth: true,
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 6,
        data: mainForceSeries,
        lineStyle: { width: 2 }
      },
      {
        name: '散户',
        type: 'line',
        xAxisIndex: 1,
        yAxisIndex: 1,
        smooth: true,
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 6,
        data: retailSeries,
        lineStyle: { width: 2 }
      }
    ]
  }
}
