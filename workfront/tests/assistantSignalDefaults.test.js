const assert = require('node:assert/strict')

async function main() {
  const {
    getDefaultSignalDate,
    getFirstIndicatorValue
  } = await import('../src/utils/assistantSignalDefaults.mjs')

  assert.equal(getDefaultSignalDate(new Date('2026-04-13T12:00:00')), '2026-04-13')
  assert.equal(getDefaultSignalDate(new Date('2026-04-17T12:00:00')), '2026-04-17')
  assert.equal(getDefaultSignalDate(new Date('2026-04-18T12:00:00')), '2026-04-17')
  assert.equal(getDefaultSignalDate(new Date('2026-04-19T12:00:00')), '2026-04-17')

  assert.equal(
    getFirstIndicatorValue([
      { value: 'MF_Edge3', label: '主力边际变化' },
      { value: 'MF_Accel', label: '主力加速度' }
    ]),
    'MF_Edge3'
  )
  assert.equal(getFirstIndicatorValue([]), '')
  assert.equal(getFirstIndicatorValue(null), '')

  console.log('assistant signal defaults tests passed')
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
