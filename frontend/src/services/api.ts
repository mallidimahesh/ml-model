import type {
  CountryMeta,
  GlobalOverviewData,
  CountryProfile,
  DerivedIndicatorsData,
  RidgeForecastResult,
  KeynesianResult,
  ISLMResult,
} from '../types'

const BASE_URL = '/api'

export async function fetchStatus(): Promise<any> {
  const res = await fetch(`${BASE_URL}/status`)
  if (!res.ok) throw new Error(`Status error: ${res.statusText}`)
  return res.json()
}

export async function fetchCountries(): Promise<CountryMeta[]> {
  const res = await fetch(`${BASE_URL}/countries`)
  if (!res.ok) throw new Error(`Failed to load countries: ${res.statusText}`)
  return res.json()
}

export async function fetchGlobalOverview(): Promise<GlobalOverviewData> {
  const res = await fetch(`${BASE_URL}/global/overview`)
  if (!res.ok) throw new Error(`Failed to load global overview: ${res.statusText}`)
  return res.json()
}

export async function fetchCountryProfile(countryCode: string): Promise<CountryProfile> {
  const res = await fetch(`${BASE_URL}/country/${countryCode}`)
  if (!res.ok) throw new Error(`Failed to load profile for ${countryCode}: ${res.statusText}`)
  return res.json()
}

export async function fetchDerivedIndicators(countryCode: string): Promise<DerivedIndicatorsData> {
  const res = await fetch(`${BASE_URL}/country/${countryCode}/derived`)
  if (!res.ok) throw new Error(`Failed to load derived indicators: ${res.statusText}`)
  return res.json()
}

export async function runRidgeForecast(params: {
  country_code: string
  alpha: number
  test_ratio: number
  features: string[]
}): Promise<RidgeForecastResult> {
  const res = await fetch(`${BASE_URL}/forecast/ridge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Ridge model error (${res.status})`)
  }
  return res.json()
}

export async function simulateKeynesian(params: {
  baseline_gdp: number
  delta_g: number
  mpc: number
  tax_rate?: number
  import_propensity?: number
  max_rounds?: number
}): Promise<KeynesianResult> {
  const res = await fetch(`${BASE_URL}/simulate/keynesian`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Keynesian simulation error (${res.status})`)
  }
  return res.json()
}

export async function simulateISLM(params: {
  delta_r: number
  delta_g: number
  c?: number
  b?: number
  k_y?: number
  h?: number
  c0?: number
  i0?: number
  g0?: number
  t0?: number
  m0?: number
  p?: number
}): Promise<ISLMResult> {
  const res = await fetch(`${BASE_URL}/simulate/is-lm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `IS-LM simulation error (${res.status})`)
  }
  return res.json()
}

export async function fetchMethodology(): Promise<any> {
  const res = await fetch(`${BASE_URL}/methodology`)
  if (!res.ok) throw new Error(`Methodology error: ${res.statusText}`)
  return res.json()
}
