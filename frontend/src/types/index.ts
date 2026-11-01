export interface CountryMeta {
  code: string
  iso2: string
  name: string
  region: string
  income: string
  flag: string
  currency: string
  has_quarterly: boolean
  policy_rate_source?: string
}

export interface IndicatorMeta {
  value: number | null
  year: number | null
  indicator_code: string
  name: string
  short_name: string
  units: string
  frequency: string
  source: string
  is_live: boolean
}

export interface PolicyRateInfo {
  value: number
  period: string
  source: string
  units: string
  frequency: string
}

export interface TimeSeriesPoint {
  year: number
  value: number
}

export interface QuarterlySeriesPoint {
  quarter: string
  date: string
  gdp_growth_yoy: number | null
  inflation_yoy: number | null
  unemployment: number | null
  fedfunds: number | null
}

export interface CountryProfile {
  metadata: CountryMeta
  latest: Record<string, IndicatorMeta>
  policy_rate: PolicyRateInfo
  series: Record<string, TimeSeriesPoint[]>
  quarterly_series: QuarterlySeriesPoint[]
  timestamp: string
}

export interface GlobalKPI {
  id: string
  label: string
  value: number
  formatted: string
  unit: string
  period: string
  change: number
  coverage: string
  source: string
}

export interface RankingItem {
  code: string
  name: string
  flag: string
  region: string
  income: string
  gdp_cd: number
  gdp_formatted: string
  gdp_growth: number
  inflation: number
  unemployment: number
  gdp_pcap: number
  interest_rate: number
}

export interface GlobalHistoricalTrend {
  year: number
  gdp_growth?: number
  inflation?: number
  unemployment?: number
}

export interface GlobalOverviewData {
  kpis: GlobalKPI[]
  rankings: {
    by_gdp: RankingItem[]
    by_growth: RankingItem[]
    by_inflation: RankingItem[]
    by_unemployment: RankingItem[]
    by_pcap: RankingItem[]
  }
  historical_trends: GlobalHistoricalTrend[]
  data_status: {
    fred_live: boolean
    world_bank_live: boolean
    timestamp: string
  }
}

export interface MiseryHistoricalPoint {
  year: number
  inflation: number
  unemployment: number
  misery_index: number
}

export interface RealRateHistoricalPoint {
  year: number
  inflation: number
  real_rate: number
  zero_line: number
}

export interface DerivedIndicatorsData {
  country: CountryMeta
  misery_index: {
    value: number | null
    severity: string
    severity_color: string
    severity_desc: string
    inflation_component: {
      value: number | null
      year: number | null
      share_percent: number
      source: string
    }
    unemployment_component: {
      value: number | null
      year: number | null
      share_percent: number
      source: string
    }
    compatibility_note: string
    historical: MiseryHistoricalPoint[]
    benchmarks: {
      code: string
      name: string
      flag: string
      inflation: number
      unemployment: number
      misery_index: number
    }[]
    interpretation: string
  }
  real_interest_rate: {
    nominal_rate: number
    nominal_source: string
    nominal_period: string
    inflation_used: number | null
    inflation_period: string
    ex_post_real_rate: number | null
    policy_stance: string
    policy_stance_desc: string
    policy_stance_color: string
    fisher_equation: string
    methodology_note: string
    historical: RealRateHistoricalPoint[]
  }
}

export interface ForecastChartPoint {
  date: string
  label: string
  split: 'train' | 'test' | 'forecast'
  actual: number | null
  predicted: number
  interval_low?: number
  interval_high?: number
}

export interface CoefficientItem {
  feature: string
  name: string
  role: string
  coefficient: number
  abs_weight: number
  direction: string
  description: string
}

export interface PhillipsPoint {
  unemployment: number
  inflation: number
  period: string
}

export interface RidgeForecastResult {
  country: CountryMeta
  frequency: string
  is_quarterly_native: boolean
  frequency_disclaimer?: string
  target_variable: string
  alpha: number
  test_ratio: number
  features_used: string[]
  metrics: {
    test_mae: number
    test_rmse: number
    test_r2: number
    train_mae?: number
    train_rmse?: number
    baseline_mae: number
    baseline_rmse: number
    beats_baseline: boolean
    total_observations: number
    train_size: number
    test_size: number
    train_period: string
    test_period: string
  }
  next_forecast: {
    target_period: string
    point_forecast: number
    confidence_95: {
      low: number
      high: number
      margin_error: number
    }
  }
  coefficients: CoefficientItem[]
  chart_data: ForecastChartPoint[]
  phillips_curve: {
    scatter: PhillipsPoint[]
    ols_slope: number
    ols_intercept: number
    interpretation: string
  }
}

export interface KeynesianRound {
  round: number
  description: string
  round_addition: number
  cumulative_output: number
  percent_realized: number
}

export interface KeynesianResult {
  inputs: {
    baseline_gdp: number
    delta_g: number
    mpc: number
    tax_rate: number
    import_propensity: number
    has_leakages: boolean
  }
  results: {
    basic_multiplier: number
    extended_multiplier: number
    active_multiplier: number
    delta_y: number
    simulated_gdp: number
    percent_change: number
    mps: number
  }
  round_breakdown: KeynesianRound[]
  explanation: string
  assumptions_disclaimer: string
}

export interface ISLMCurvePoint {
  y: number
  is_baseline: number
  is_policy: number
  lm_baseline: number
  lm_policy: number
}

export interface TransmissionStep {
  step: number
  title: string
  description: string
}

export interface PresetScenario {
  id: string
  name: string
  description: string
  delta_r: number
  delta_g: number
}

export interface ISLMResult {
  baseline: {
    y: number
    r: number
    m: number
    g: number
  }
  policy: {
    y: number
    r: number
    m_implied: number
    g: number
  }
  deltas: {
    delta_y: number
    delta_r: number
    delta_m: number
    delta_g: number
    delta_i: number
    percent_y_change: number
  }
  parameters: {
    c: number
    b: number
    k_y: number
    h: number
    p: number
    multiplier: number
  }
  curve_points: ISLMCurvePoint[]
  transmission_steps: TransmissionStep[]
  preset_scenarios: PresetScenario[]
  assumptions_disclaimer: string
}
