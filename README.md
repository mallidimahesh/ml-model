# EcoSim: Real-Time Economic Data Analytics & Policy Simulation

A modern, interactive full-stack macroeconomic intelligence and policy simulation platform based on the academic presentation **`EcoSim_Ridge_Regression_Green_Teal_Theme.pptx`**.

Developed by:
- **Rohith Reddy** — 24BEC0065
- **Lakshmi Narasimha** — 24BEC0645  
Course: **Macro Economics**

---

## 🏛️ Project Architecture & Key Features

EcoSim combines empirical macroeconomic data from official institutions with machine learning and classical macroeconomic theory:

1. **Global Overview Dashboard**:
   - Worldwide aggregate KPI cards for **World GDP**, **Global GDP Growth**, **GDP Per Capita**, **Global Inflation**, **Unemployment**, and **Benchmark 10-Year Yield**.
   - Official aggregates calculated via World Bank Open Data (`1W / WLD`), never arbitrary country averages.
   - Comparative multi-country rankings across GDP, real growth, inflation, unemployment, and living standards.
   - 25-year historical world trend charts (2000–2023).

2. **Country Explorer**:
   - Detailed macroeconomic profile for 20+ major global economies with instant country switching.
   - Compares **Nominal GDP vs. Real GDP** and **Nominal Per Capita vs. Real Per Capita**.
   - Interactive historical line charts with customizable period selectors (`5Y`, `10Y`, `20Y`, `ALL`) and multi-country comparison overlays.
   - High-frequency quarterly time-series view for the United States (FRED series: `GDPC1`, `CPIAUCSL`, `UNRATE`, `FEDFUNDS`).

3. **Derived Indicators Engine**:
   - **Arthur Okun's Misery Index**: $\text{Misery Index} = \text{CPI Inflation Rate} + \text{Unemployment Rate}$, featuring dynamic severity gauge, decomposed driver contribution progress bars, historical trendlines, and cross-country benchmark rankings.
   - **Fisher Real Interest Rate**: Estimates ex-post real interest rates ($r \approx i - \pi$), with clear pedagogical distinctions between ex-ante expectations ($r \approx i - \pi^e$) and ex-post realized borrowing costs.

4. **Inflation Forecast Studio (Phillips Curve + Ridge Regression)**:
   - Next-period inflation forecasting utilizing an empirical Phillips Curve feature set: lagged inflation ($\pi_t$), labor slack ($u_t$), aggregate demand strain ($\text{GDP Growth}_t$), and monetary stance ($i_t$).
   - Regularized via **Ridge Regression** ($L_2$ penalty $\lambda \sum \beta_j^2$) with an interactive $\lambda$ tuning slider.
   - **Econometric Safeguards**: Strictly chronological train/test holdout partitions without random shuffling, zero lookahead leakage, scaler fit strictly on training partitions.
   - Evaluated against a **Naive Persistence Baseline** ($\hat{y}_{t+1} = y_t$), reporting MAE, RMSE, out-of-sample $R^2$, and 95% confidence prediction intervals ($\pm 1.96 \times \text{RMSE}$).
   - **Frequency Integrity**: High-frequency quarterly forecasting for nations with native quarterly reporting (US FRED series); transparent annual-frequency model for World Bank annual series.
   - Empirical Phillips Curve scatter plot ($u$ vs. $\pi$) with OLS fitted trendline and **Lucas Critique** academic disclaimer.

5. **Interactive Policy Laboratory**:
   - **A. Keynesian Government Spending Multiplier**: $\Delta Y = \frac{\Delta G}{1 - \text{MPC}}$, with interactive spending shock $\Delta G$, MPC slider ($0 < \text{MPC} < 1$), optional income tax ($t$) and import leakages ($m$), round-by-round ripple expansion chart and schedule.
   - **B. IS–LM Macroeconomic Framework**: Solves simultaneous goods-market ($Y = C + I + G$) and money-market ($M/P = L(Y, r)$) equilibrium. Interactive policy rate shocks ($\Delta r$), fiscal shocks ($\Delta G$), behavioral parameter adjustments ($c, b, k_y, h$), preset policy scenarios, and dynamic IS/LM curve shifts.

6. **Data Sources & Scientific Transparency**:
   - Complete inventory of FRED series IDs and World Bank indicator codes.
   - Mathematical formulations, data frequency integrity guidelines, and literature citations.

---

## 🛠️ Technology Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS (v4), Recharts, Lucide React.
- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2.
- **Data & Modeling**: pandas, NumPy, scikit-learn (`sklearn.linear_model.Ridge`, `StandardScaler`).
- **Data APIs**: Federal Reserve Economic Data (FRED), World Bank Open Data (WDI).
- **Caching**: Multi-tier in-memory and disk cache with TTL and verified offline fallback benchmarks.
- **Testing**: pytest, HTTPX / FastAPI TestClient (10/10 test suite).

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- Python 3.10 or higher
- Node.js v18 or higher (v20+ recommended)
- npm or pnpm

### 2. Backend Setup
```powershell
# Navigate to the project root
cd C:\Users\rohit\.gemini\antigravity\scratch\ecosim

# Create & activate a virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install Python backend dependencies
pip install -r requirements.txt
```

### 3. Environment Variables (.env)
EcoSim connects to the **World Bank Open Data API** (no key required) and the **Federal Reserve FRED Direct Data Feed** natively out-of-the-box.

If you possess a personal FRED API key, configure it in `.env`:
```powershell
# Copy template
cp .env.example .env
```
Inside `.env`:
```env
FRED_API_KEY=your_actual_key_here  # Optional: leave blank for automatic direct feed
PORT=8000
HOST=127.0.0.1
```

### 4. Running the Tests
Run the comprehensive 10-test suite verifying API endpoints, derived metrics, Ridge regression, Keynesian multiplier, and IS-LM solvers:
```powershell
python -m pytest backend/tests
```

### 5. Running the Application

#### Option A: Standalone Unified Server (Recommended)
FastAPI automatically serves both the backend API and the compiled React production frontend on port 8000:
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

#### Option B: Full-Stack Development Mode (Live Hot-Reload)
**Terminal 1 — Backend API:**
```powershell
cd C:\Users\rohit\.gemini\antigravity\scratch\ecosim
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — Frontend Dev Server:**
```powershell
cd C:\Users\rohit\.gemini\antigravity\scratch\ecosim\frontend
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser (Vite proxies `/api` to `localhost:8000`).

---

## 📊 Econometric Models & Assumptions

### 1. Phillips Curve & Ridge Regression
$$\pi_{t+1} = \beta_0 + \sum_{j} \beta_j X_{j,t} + \varepsilon$$
$$\min_{\beta} \left\{ \sum (y_i - X_i \beta)^2 + \lambda \sum \beta_j^2 \right\}$$
- **Feature Set**: Lagged CPI inflation ($\pi_t$), Unemployment rate ($u_t$), Real GDP Growth ($g_t$), Policy rate ($i_t$).
- **Anti-Leakage Protocol**: Target is next quarter's inflation ($t+1$). All features are strictly observed at or prior to quarter $t$.
- **Chronological Split**: Forward-chaining / holdout testing without random shuffling.
- **Lucas Critique Disclaimer**: The empirical relationship reflects observational associations, not invariant policy levers.

### 2. Keynesian Multiplier
$$\Delta Y = \frac{\Delta G}{1 - \text{MPC}}$$
$$\text{With Leakages: } k_{\text{ext}} = \frac{1}{1 - \text{MPC}(1 - t) + m}$$
- **Assumptions**: Rigid short-run prices, spare productive capacity, passive monetary policy (no rate response), zero crowding out.

### 3. IS–LM Equilibrium
- **Goods Market (IS Curve)**: $Y = C(Y - T) + I(r) + G \implies r = \frac{A - (1 - c)Y}{b}$
- **Money Market (LM Curve)**: $\frac{M}{P} = L(Y, r) = k_y Y - h r \implies r = \frac{k_y Y - (M/P)}{h}$
- **Equilibrium**: Solves for simultaneous clearing $(Y^*, r^*)$ under policy shocks $\Delta r$ and fiscal shocks $\Delta G$.

---

## 📚 Academic References

1. Hoerl, A. E., & Kennard, R. W. (1970). *"Ridge Regression: Biased Estimation for Nonorthogonal Problems."* Technometrics, 12(1), 55–67.
2. McCracken, M. W., & Ng, S. (2016). *"FRED-MD: A Monthly Database for Macroeconomic Research."* Journal of Business & Economic Statistics, 34(4), 574–589.
3. Medeiros, M. C., et al. (2021). *"Forecasting Inflation in a Data-Rich Environment: The Benefits of Machine Learning Methods."* JBES, 39(1), 98–119.
4. Phillips, A. W. (1958). *"The Relation Between Unemployment and the Rate of Change of Money Wage Rates in the United Kingdom, 1861–1957."* Economica, 25(100), 283–299.
5. Keynes, J. M. (1936). *The General Theory of Employment, Interest, and Money.* Macmillan.
6. Hicks, J. R. (1937). *"Mr. Keynes and the 'Classics': A Suggested Interpretation."* Econometrica, 5(2), 147–159.
