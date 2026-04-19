const formatNumber = (value, digits = 2) => {
  if (value === null || value === undefined || value === '') {
    return '--'
  }
  const numeric = Number(value)
  if (Number.isNaN(numeric)) {
    return String(value)
  }
  return numeric.toFixed(digits)
}

const formatInteger = value => formatNumber(value, 0)

const formatList = (values, digits = 2) => {
  if (!Array.isArray(values) || !values.length) {
    return '--'
  }
  return `[${values.map(value => formatNumber(value, digits)).join(', ')}]`
}

const joinValues = values => values.filter(Boolean).join(' | ') || '--'

const getExtra = row => row.extra_json || {}

const getQuantiles = row => getExtra(row).window_quantiles || {}

const getComponents = row => getExtra(row).components || {}

const getStrengthText = row => {
  if (row.strength === null || row.strength === undefined) {
    return '--'
  }
  return formatNumber(row.strength)
}

const directionColumn = {
  key: 'direction',
  label: '方向',
  width: 110,
  type: 'direction'
}

const baseColumns = [
  {
    key: 'signal_date',
    label: '日期',
    width: 120,
    type: 'plain',
    value: row => row.signal_date || '--'
  },
  {
    key: 'variety_name',
    label: '品种',
    minWidth: 110,
    type: 'plain',
    value: row => row.variety_name || '--'
  },
  directionColumn
]

const edge3Schema = {
  label: '主力三连变起点',
  shortDesc: '按起点区域、起点值与近 3 日主力序列展示，不再混用“触发值 / 强度”表头。',
  columns: [
    {
      key: 'edge3_zone',
      label: '起点区域',
      minWidth: 170,
      type: 'metric',
      mainText: row => row.indicator_display_value || row.indicator_value || '--',
      subText: row => row.judgement_title || '起点区域分区结果',
      tooltipTitle: '起点区域说明',
      tooltipLines: row => [
        `当前分区：${row.indicator_display_value || row.indicator_value || '--'}`,
        `判读提示：${row.judgement_reason || '--'}`
      ]
    },
    {
      key: 'edge3_start_value',
      label: '起点值',
      minWidth: 150,
      type: 'metric',
      mainText: row => formatNumber(getExtra(row).start_value ?? row.strength),
      subText: row => {
        const quantiles = getQuantiles(row)
        return `p10 ${formatNumber(quantiles.p10)} / p50 ${formatNumber(quantiles.p50)}`
      },
      tooltipTitle: '起点值说明',
      tooltipLines: row => {
        const quantiles = getQuantiles(row)
        return [
          `start_val：${formatNumber(getExtra(row).start_value ?? row.strength)}`,
          `近 3 个月分位：p10 ${formatNumber(quantiles.p10)}，p50 ${formatNumber(quantiles.p50)}，p90 ${formatNumber(quantiles.p90)}`,
          row.strength_explanation || '--'
        ]
      }
    },
    {
      key: 'edge3_values',
      label: '近3日主力值',
      minWidth: 240,
      type: 'metric',
      mainText: row => formatList(getExtra(row).values),
      subText: () => '用于判断三连变起点的位置序列',
      tooltipTitle: '近3日主力值说明',
      tooltipLines: row => [
        `近 3 日主力值：${formatList(getExtra(row).values)}`,
        `算法说明：${row.calc_explanation || '--'}`
      ]
    }
  ],
  detailItems: [
    {
      label: '怎么算',
      value: row => row.calc_explanation || '--'
    },
    {
      label: '起点区域',
      value: row => row.indicator_display_value || row.indicator_value || '--'
    },
    {
      label: '起点值',
      value: row => formatNumber(getExtra(row).start_value ?? row.strength)
    },
    {
      label: '近3日主力值',
      value: row => formatList(getExtra(row).values)
    },
    {
      label: '起点值怎么看',
      value: row => row.strength_explanation || '--'
    }
  ]
}

const accelSchema = {
  label: '趋势加速度',
  shortDesc: '围绕“加速 / 减速、加速度值、两步变化”展示，避免把不同含义塞进同一强度列。',
  columns: [
    {
      key: 'accel_result',
      label: '判定结果',
      minWidth: 170,
      type: 'metric',
      mainText: row => row.indicator_display_value || row.indicator_value || '--',
      subText: row => row.judgement_title || '--',
      tooltipTitle: '判定结果说明',
      tooltipLines: row => [
        `当前结果：${row.indicator_display_value || row.indicator_value || '--'}`,
        row.judgement_reason || '--'
      ]
    },
    {
      key: 'accel_strength',
      label: '加速度',
      minWidth: 140,
      type: 'metric',
      mainText: row => getStrengthText(row),
      subText: () => '|delta2| - |delta1|',
      tooltipTitle: '加速度说明',
      tooltipLines: row => [
        `加速度：${getStrengthText(row)}`,
        row.strength_explanation || '--'
      ]
    },
    {
      key: 'accel_steps',
      label: '两步变化',
      minWidth: 210,
      type: 'metric',
      mainText: row => {
        const extra = getExtra(row)
        return joinValues([
          `delta1 ${formatNumber(extra.delta1)}`,
          `delta2 ${formatNumber(extra.delta2)}`
        ])
      },
      subText: () => '比较第二步是否比第一步更猛',
      tooltipTitle: '两步变化说明',
      tooltipLines: row => {
        const extra = getExtra(row)
        return [
          `delta1：${formatNumber(extra.delta1)}`,
          `delta2：${formatNumber(extra.delta2)}`,
          row.calc_explanation || '--'
        ]
      }
    }
  ],
  detailItems: [
    { label: '怎么算', value: row => row.calc_explanation || '--' },
    { label: '当前判定', value: row => row.indicator_display_value || row.indicator_value || '--' },
    { label: '加速度', value: row => getStrengthText(row) },
    {
      label: '两步变化',
      value: row => {
        const extra = getExtra(row)
        return joinValues([
          `delta1 ${formatNumber(extra.delta1)}`,
          `delta2 ${formatNumber(extra.delta2)}`
        ])
      }
    },
    { label: '加速度怎么看', value: row => row.strength_explanation || '--' }
  ]
}

const durationSchema = {
  label: '趋势持续天数',
  shortDesc: '按持续档位、连续天数和主力序列展示，突出这是阶段信息，不再误导成统一强度分。',
  columns: [
    {
      key: 'duration_stage',
      label: '持续档位',
      minWidth: 150,
      type: 'metric',
      mainText: row => row.indicator_display_value || row.indicator_value || '--',
      subText: row => row.judgement_title || '--',
      tooltipTitle: '持续档位说明',
      tooltipLines: row => [
        `当前档位：${row.indicator_display_value || row.indicator_value || '--'}`,
        row.judgement_reason || '--'
      ]
    },
    {
      key: 'duration_days',
      label: '连续天数',
      minWidth: 140,
      type: 'metric',
      mainText: row => formatInteger(getExtra(row).streak_length ?? row.strength),
      subText: () => '当前同向趋势累计天数',
      tooltipTitle: '连续天数说明',
      tooltipLines: row => [
        `连续天数：${formatInteger(getExtra(row).streak_length ?? row.strength)}`,
        row.strength_explanation || '--'
      ]
    },
    {
      key: 'duration_values',
      label: '主力序列',
      minWidth: 240,
      type: 'metric',
      mainText: row => formatList(getExtra(row).values),
      subText: () => '用于识别 D3 / D5 / D7 的连续序列',
      tooltipTitle: '主力序列说明',
      tooltipLines: row => [
        `主力序列：${formatList(getExtra(row).values)}`,
        row.calc_explanation || '--'
      ]
    }
  ],
  detailItems: [
    { label: '怎么算', value: row => row.calc_explanation || '--' },
    { label: '当前档位', value: row => row.indicator_display_value || row.indicator_value || '--' },
    { label: '连续天数', value: row => formatInteger(getExtra(row).streak_length ?? row.strength) },
    { label: '主力序列', value: row => formatList(getExtra(row).values) },
    { label: '持续天数怎么看', value: row => row.strength_explanation || '--' }
  ]
}

const divergenceSchema = {
  label: '主散背离强度',
  shortDesc: '按背离类型、背离分和主散均变展示，强调这是主散反向拉扯，不是统一强度值。',
  columns: [
    {
      key: 'divergence_type',
      label: '背离类型',
      minWidth: 170,
      type: 'metric',
      mainText: row => row.indicator_display_value || row.indicator_value || '--',
      subText: row => row.judgement_title || '--',
      tooltipTitle: '背离类型说明',
      tooltipLines: row => [
        `当前结果：${row.indicator_display_value || row.indicator_value || '--'}`,
        row.judgement_reason || '--'
      ]
    },
    {
      key: 'divergence_score',
      label: '背离分',
      minWidth: 140,
      type: 'metric',
      mainText: row => getStrengthText(row),
      subText: () => '|主力平均变化| + |散户平均变化|',
      tooltipTitle: '背离分说明',
      tooltipLines: row => [
        `背离分：${getStrengthText(row)}`,
        row.strength_explanation || '--'
      ]
    },
    {
      key: 'divergence_avgs',
      label: '主散均变',
      minWidth: 210,
      type: 'metric',
      mainText: row => {
        const extra = getExtra(row)
        return joinValues([
          `主力 ${formatNumber(extra.main_force_delta_avg)}`,
          `散户 ${formatNumber(extra.retail_delta_avg)}`
        ])
      },
      subText: () => '看主散是否真的反向',
      tooltipTitle: '主散均变说明',
      tooltipLines: row => {
        const extra = getExtra(row)
        return [
          `主力均变：${formatNumber(extra.main_force_delta_avg)}`,
          `散户均变：${formatNumber(extra.retail_delta_avg)}`,
          row.calc_explanation || '--'
        ]
      }
    }
  ],
  detailItems: [
    { label: '怎么算', value: row => row.calc_explanation || '--' },
    { label: '背离类型', value: row => row.indicator_display_value || row.indicator_value || '--' },
    { label: '背离分', value: row => getStrengthText(row) },
    {
      label: '主散均变',
      value: row => {
        const extra = getExtra(row)
        return joinValues([
          `主力 ${formatNumber(extra.main_force_delta_avg)}`,
          `散户 ${formatNumber(extra.retail_delta_avg)}`
        ])
      }
    },
    { label: '背离分怎么看', value: row => row.strength_explanation || '--' }
  ]
}

const magnitudeSchema = {
  label: '主力变化幅度',
  shortDesc: '按幅度分档、三日总变化和分位参考展示，突出这是动作大小而不是统一强度分。',
  columns: [
    {
      key: 'magnitude_type',
      label: '幅度分档',
      minWidth: 170,
      type: 'metric',
      mainText: row => row.indicator_display_value || row.indicator_value || '--',
      subText: row => row.judgement_title || '--',
      tooltipTitle: '幅度分档说明',
      tooltipLines: row => [
        `当前分档：${row.indicator_display_value || row.indicator_value || '--'}`,
        row.judgement_reason || '--'
      ]
    },
    {
      key: 'magnitude_value',
      label: '三日总变化',
      minWidth: 150,
      type: 'metric',
      mainText: row => formatNumber(getExtra(row).magnitude ?? row.strength),
      subText: () => '|v2 - v0|',
      tooltipTitle: '三日总变化说明',
      tooltipLines: row => [
        `三日总变化：${formatNumber(getExtra(row).magnitude ?? row.strength)}`,
        row.strength_explanation || '--'
      ]
    },
    {
      key: 'magnitude_quantiles',
      label: '分位参考',
      minWidth: 210,
      type: 'metric',
      mainText: row => {
        const quantiles = getQuantiles(row)
        return joinValues([
          `p25 ${formatNumber(quantiles.p25)}`,
          `p75 ${formatNumber(quantiles.p75)}`
        ])
      },
      subText: () => '和近 3 个月滚动分位比较',
      tooltipTitle: '分位参考说明',
      tooltipLines: row => {
        const quantiles = getQuantiles(row)
        return [
          `p25：${formatNumber(quantiles.p25)}`,
          `p75：${formatNumber(quantiles.p75)}`,
          row.calc_explanation || '--'
        ]
      }
    }
  ],
  detailItems: [
    { label: '怎么算', value: row => row.calc_explanation || '--' },
    { label: '幅度分档', value: row => row.indicator_display_value || row.indicator_value || '--' },
    { label: '三日总变化', value: row => formatNumber(getExtra(row).magnitude ?? row.strength) },
    {
      label: '分位参考',
      value: row => {
        const quantiles = getQuantiles(row)
        return `p25 ${formatNumber(quantiles.p25)} / p75 ${formatNumber(quantiles.p75)}`
      }
    },
    { label: '幅度怎么看', value: row => row.strength_explanation || '--' }
  ]
}

const breakZoneSchema = {
  label: '区域突破信号',
  shortDesc: '按区域状态、档位和近 3 日主力值展示，强调重点是有没有穿越关键边界。',
  columns: [
    {
      key: 'breakzone_state',
      label: '区域状态',
      minWidth: 190,
      type: 'metric',
      mainText: row => row.indicator_display_value || row.indicator_value || '--',
      subText: row => row.judgement_title || '--',
      tooltipTitle: '区域状态说明',
      tooltipLines: row => [
        `当前状态：${row.indicator_display_value || row.indicator_value || '--'}`,
        row.judgement_reason || '--'
      ]
    },
    {
      key: 'breakzone_level',
      label: '档位',
      minWidth: 140,
      type: 'metric',
      mainText: row => getStrengthText(row),
      subText: () => '2 突破 / 1 震荡 / 0 普通',
      tooltipTitle: '档位说明',
      tooltipLines: row => [
        `当前档位：${getStrengthText(row)}`,
        row.strength_explanation || '--'
      ]
    },
    {
      key: 'breakzone_values',
      label: '近3日主力值',
      minWidth: 240,
      type: 'metric',
      mainText: row => formatList(getExtra(row).values),
      subText: row => {
        const quantiles = getQuantiles(row)
        return `p10 ${formatNumber(quantiles.p10)} / p90 ${formatNumber(quantiles.p90)}`
      },
      tooltipTitle: '近3日主力值说明',
      tooltipLines: row => {
        const quantiles = getQuantiles(row)
        return [
          `近 3 日主力值：${formatList(getExtra(row).values)}`,
          `边界参考：p10 ${formatNumber(quantiles.p10)}，p90 ${formatNumber(quantiles.p90)}`,
          row.calc_explanation || '--'
        ]
      }
    }
  ],
  detailItems: [
    { label: '怎么算', value: row => row.calc_explanation || '--' },
    { label: '区域状态', value: row => row.indicator_display_value || row.indicator_value || '--' },
    { label: '档位', value: row => getStrengthText(row) },
    { label: '近3日主力值', value: row => formatList(getExtra(row).values) },
    { label: '档位怎么看', value: row => row.strength_explanation || '--' }
  ]
}

const compositeSchema = {
  label: '综合评分',
  shortDesc: '按综合得分、分项构成和关键上下文展示，明确这是规则加权结果，不再混成统一强度列。',
  columns: [
    {
      key: 'composite_score',
      label: '综合得分',
      minWidth: 150,
      type: 'metric',
      mainText: row => row.indicator_display_value || getStrengthText(row),
      subText: row => row.judgement_title || '--',
      tooltipTitle: '综合得分说明',
      tooltipLines: row => [
        `展示值：${row.indicator_display_value || '--'}`,
        `strength 字段：${getStrengthText(row)}`,
        row.strength_explanation || '--'
      ]
    },
    {
      key: 'composite_components',
      label: '分项构成',
      minWidth: 260,
      type: 'metric',
      mainText: row => {
        const components = getComponents(row)
        return joinValues([
          `持续 ${formatInteger(components.duration_score)}`,
          `加速 ${formatInteger(components.accel_score)}`,
          `起点 ${formatInteger(components.edge_score)}`,
          `背离 ${formatInteger(components.divergence_score)}`,
          `幅度 ${formatInteger(components.magnitude_score)}`
        ])
      },
      subText: () => '五项规则离散打分后加权',
      tooltipTitle: '分项构成说明',
      tooltipLines: row => {
        const components = getComponents(row)
        return [
          `持续天数分：${formatInteger(components.duration_score)}`,
          `加速度分：${formatInteger(components.accel_score)}`,
          `起点位置分：${formatInteger(components.edge_score)}`,
          `主散背离分：${formatInteger(components.divergence_score)}`,
          `幅度强度分：${formatInteger(components.magnitude_score)}`
        ]
      }
    },
    {
      key: 'composite_context',
      label: '关键上下文',
      minWidth: 240,
      type: 'metric',
      mainText: row => {
        const extra = getExtra(row)
        return joinValues([
          `持续 ${formatInteger(extra.streak_length)} 天`,
          `幅度 ${formatNumber(extra.current_magnitude)}`
        ])
      },
      subText: row => {
        const quantiles = getQuantiles(row)
        return `edge p10 ${formatNumber(quantiles.edge_p10)} / p90 ${formatNumber(quantiles.edge_p90)}`
      },
      tooltipTitle: '关键上下文说明',
      tooltipLines: row => {
        const quantiles = getQuantiles(row)
        return [
          `连续天数：${formatInteger(getExtra(row).streak_length)}`,
          `当前幅度：${formatNumber(getExtra(row).current_magnitude)}`,
          `边缘区分位：p10 ${formatNumber(quantiles.edge_p10)}，p20 ${formatNumber(quantiles.edge_p20)}，p80 ${formatNumber(quantiles.edge_p80)}，p90 ${formatNumber(quantiles.edge_p90)}`,
          `幅度分位：p25 ${formatNumber(quantiles.magnitude_p25)}，p75 ${formatNumber(quantiles.magnitude_p75)}`
        ]
      }
    }
  ],
  detailItems: [
    { label: '怎么算', value: row => row.calc_explanation || '--' },
    { label: '综合得分', value: row => row.indicator_display_value || getStrengthText(row) },
    {
      label: '分项构成',
      value: row => {
        const components = getComponents(row)
        return joinValues([
          `持续 ${formatInteger(components.duration_score)}`,
          `加速 ${formatInteger(components.accel_score)}`,
          `起点 ${formatInteger(components.edge_score)}`,
          `背离 ${formatInteger(components.divergence_score)}`,
          `幅度 ${formatInteger(components.magnitude_score)}`
        ])
      }
    },
    {
      label: '关键上下文',
      value: row => {
        const extra = getExtra(row)
        return joinValues([
          `持续 ${formatInteger(extra.streak_length)} 天`,
          `幅度 ${formatNumber(extra.current_magnitude)}`
        ])
      }
    },
    { label: '综合分怎么看', value: row => row.strength_explanation || '--' }
  ]
}

export const indicatorOptions = [
  { value: 'MF_Edge3', label: edge3Schema.label },
  { value: 'MF_Accel', label: accelSchema.label },
  { value: 'MF_Duration', label: durationSchema.label },
  { value: 'MS_Divergence', label: divergenceSchema.label },
  { value: 'MF_Magnitude', label: magnitudeSchema.label },
  { value: 'MF_BreakZone', label: breakZoneSchema.label },
  { value: 'Composite_Score', label: compositeSchema.label }
]

export const signalTableSchemas = {
  MF_Edge3: edge3Schema,
  MF_Accel: accelSchema,
  MF_Duration: durationSchema,
  MS_Divergence: divergenceSchema,
  MF_Magnitude: magnitudeSchema,
  MF_BreakZone: breakZoneSchema,
  Composite_Score: compositeSchema
}

export const getSignalTableSchema = indicator => {
  if (!indicator) {
    return null
  }
  const schema = signalTableSchemas[indicator]
  if (!schema) {
    return null
  }
  return {
    ...schema,
    columns: [...baseColumns, ...(schema.columns || [])]
  }
}
