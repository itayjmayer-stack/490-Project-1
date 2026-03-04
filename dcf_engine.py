import math
import datetime

def calc_wacc(assumptions):
    """Calculate Weight Average Cost of Capital (WACC) using CAPM."""
    if assumptions.get('wacc_mode') == 'direct':
        return assumptions.get('wacc_direct', 0.10)

    # Build WACC via CAPM
    cost_equity = assumptions.get('risk_free', 0.042) + assumptions.get('beta', 1.0) * assumptions.get('mkt_premium', 0.055)
    wacc = (assumptions.get('equity_weight', 1.0) * cost_equity) + \
           (assumptions.get('debt_weight', 0.0) * assumptions.get('cost_of_debt', 0.05) * (1 - assumptions.get('tax_rate_wacc', 0.21)))
    return wacc

def build_forecast(base_revenue, base_ebitda, assumptions, wacc):
    """Build a 5-year forecast table."""
    n = assumptions.get('years_forecast', 5)
    rows = []
    current_year = datetime.datetime.now().year

    for t in range(1, n + 1):
        revenue = base_revenue * math.pow(1 + assumptions.get('revenue_growth', 0.1), t)
        fcf = revenue * assumptions.get('fcf_margin', 0.15)
        
        # Use provided EBITDA or estimate as 25% of revenue
        if base_ebitda is not None:
            ebitda = base_ebitda * math.pow(1 + assumptions.get('revenue_growth', 0.1), t)
        else:
            ebitda = revenue * 0.25
            
        pv_fcf = fcf / math.pow(1 + wacc, t)

        rows.append({
            'year': current_year + t,
            't': t,
            'revenue': revenue,
            'ebitda': ebitda,
            'fcf': fcf,
            'pv_fcf': pv_fcf,
        })

    return rows

def calc_terminal_value(forecast, assumptions, wacc):
    """Calculate terminal value using perpetuity growth or exit multiple methods."""
    n = len(forecast)
    if n == 0:
        return {'terminal_value': 0, 'pv_terminal_value': 0}

    last_row = forecast[-1]
    tv = 0

    if assumptions.get('terminal_method') == 'perpetuity':
        terminal_growth = assumptions.get('terminal_growth', 0.02)
        fcf_next = last_row['fcf'] * (1 + terminal_growth)
        denominator = wacc - terminal_growth
        if denominator <= 0:
            tv = last_row['fcf'] * 50  # Cap at 50x FCF if WACC <= growth
        else:
            tv = fcf_next / denominator
    else:
        # Exit multiple method
        tv = last_row['ebitda'] * assumptions.get('exit_ebitda_multiple', 10.0)

    pv_tv = tv / math.pow(1 + wacc, n)

    return {
        'terminal_value': tv,
        'pv_terminal_value': pv_tv,
    }

def run_full_model(company, assumptions):
    """Orchestrate the full DCF valuation model."""
    wacc = calc_wacc(assumptions)

    base_revenue = company.get('latestRevenue', 0)
    base_ebitda = company.get('latestEBITDA', None)
    
    net_debt = assumptions.get('net_debt_override')
    if net_debt is None:
        net_debt = company.get('net_debt', 0)
        
    shares_out = assumptions.get('shares_out_override')
    if shares_out is None:
        shares_out = company.get('shares_out', 1)

    forecast = build_forecast(base_revenue, base_ebitda, assumptions, wacc)
    pv_fcf_sum = sum(row['pv_fcf'] for row in forecast)

    tv_results = calc_terminal_value(forecast, assumptions, wacc)
    pv_tv = tv_results['pv_terminal_value']

    ev = pv_fcf_sum + pv_tv
    equity = ev - net_debt
    per_share = equity / shares_out if shares_out > 0 else 0
    
    upside_pct = (per_share - company.get('price', 0)) / company.get('price', 1) if company.get('price', 0) > 0 else 0

    return {
        'valuation': {
            'wacc': wacc,
            'pv_fcf_sum': pv_fcf_sum,
            'terminal_value': tv_results['terminal_value'],
            'pv_terminal_value': pv_tv,
            'enterprise_value': ev,
            'equity_value': equity,
            'per_share_value': per_share,
            'upside_pct': upside_pct,
            'net_debt': net_debt,
            'shares_out': shares_out
        },
        'forecast': forecast
    }
