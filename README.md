# Premium DCF Valuation Model

A high-fidelity, interactive Discounted Cash Flow (DCF) valuation application built with Python and Streamlit. This tool allows users to perform professional-grade financial analysis with real-time data and premium aesthetics.

🚀 **Live App**: [https://490-project-1-7athvaazgmchwe4fwbjkqc.streamlit.app/](https://490-project-1-7athvaazgmchwe4fwbjkqc.streamlit.app/)

---

## 📈 Features

- **Real-Time Data**: Integrated with `yfinance` to pull live market prices, beta, and financial statements for any ticker.
- **Premium Design System**: Custom CSS implementation providing a dark, glassmorphism-inspired interface with responsive layouts.
- **Multi-Stage DCF Engine**:
  - **Explicit Forecast**: 3-10 year projection periods for Revenue and Free Cash Flow.
  - **WACC Builder**: CAPM-based Cost of Equity calculation with adjustable risk-free rates, beta, and market premiums.
  - **Terminal Value**: Supports both Gordon Growth (Perpetuity) and Exit Multiple methods.
- **Analytics Suite**:
  - **Sensitivity Matrix**: Heatmap visualization of Intrinsic Value vs. WACC and Terminal Growth.
  - **Scenario Analysis**: Side-by-side comparison of Bear, Base, and Bull cases with visual charting.
  - **Enterprise Value Bridge**: Breakdown of value components from PV of FCF to Equity Value.

---

## 🏗 Project Structure

- `app.py`: Main application entry point. Handles the Streamlit UI, multi-page navigation, and premium styling.
- `dcf_engine.py`: The core mathematical engine. Contains functions for WACC calculation, FCF forecasting, and valuation logic.
- `data_service.py`: Handles data ingestion. Includes live API fetching via `yfinance` and a verified static fallback for major tech tickers (NVDA, AAPL, etc.).
- `requirements.txt`: List of Python dependencies required for the environment.

---

## 🛠 Setup & Installation

To run this project locally, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/itayjmayer-stack/490-Project-1.git
   cd 490-Project-1
   ```

2. **Set up a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**:
   ```bash
   streamlit run app.py
   ```

---

## 🏗 Development Methodology (DRIVER)

This project was built using the **DRIVER** framework for advanced agentic coding:

1. **D (Define)**: Requirement gathering for shareability and UI parity.
2. **R (Represent)**: Technical planning and architectural mapping.
3. **I (Implement)**: Modular Python development and CSS skinning.
4. **V (Validate)**: Debugging dependency conflicts and state management.
5. **E (Evolve)**: Polishing animations and premium dashboard components.
6. **R (Reflect)**: Automated walkthroughs and technical documentation.

---

## 📖 Methodology & Disclosure

This tool uses institutional-grade financial logic but is intended for educational purposes. All calculations are derived from public data and user-provided assumptions.

*Built in collaboration with Antigravity AI.*
