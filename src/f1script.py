import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from openpyxl import load_workbook
import warnings

warnings.filterwarnings('ignore')

# ==========================================
# 1. DATA LOADING & CLEANING
# ==========================================
file_path = r'E:\Pie\test_task.xlsx'
print(f"Loading data from {file_path}...")
df = pd.read_excel(file_path)

# Function to clean dirty data (commas, Excel errors, strings)
def clean_numeric(val):
    if isinstance(val, str):
        val = val.replace(',', '').replace('ERROR:#DIV/0!', '0').replace('- 0', '0').strip()
        try: 
            return float(val)
        except ValueError: 
            return 0.0
    return float(val) if pd.notnull(val) else 0.0

df['Packs'] = df['Packs'].apply(clean_numeric)
df['Value'] = df['Value'].apply(clean_numeric)
df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-01')

# Separate historical data (for training) and future template (for writing)
hist_df = df[df['year'] < 2021].copy()
future_df = df[df['year'] == 2021].copy()

# ==========================================
# 2. FORECASTING LOGIC
# ==========================================
def forecast_sku(ts_packs, ts_value, steps=11):
    """
    Forecasts Packs and Value. 
    Logic: Holt-Winters for mature SKUs, Seasonal Naive for new SKUs.
    """
    def _predict_single(ts):
        ts = ts.asfreq('MS') # Ensure continuous monthly frequency
        
        # Fallback 1: Not enough data for seasonality (< 24 months)
        if len(ts) >= 12:
            # Seasonal Naive: Use last 12 months as proxy for next 12 months
            return ts.iloc[-12:].values[:steps]
        else:
            # Fallback to mean if less than 12 months of data
            return np.full(steps, ts.mean())
        
        # Primary Model: Holt-Winters (Additive Trend & Seasonality)
        try:
            model = ExponentialSmoothing(
                ts, trend='add', seasonal='add', seasonal_periods=12,
                initialization_method='estimated'
            )
            fit = model.fit(optimized=True)
            return fit.forecast(steps).values
        except Exception:
            # Fallback 2: If model fails to converge, use 3-month moving average
            return np.full(steps, ts.tail(3).mean())

    pred_packs = _predict_single(ts_packs)
    pred_value = _predict_single(ts_value)
    
    # Business Logic: Sales cannot be negative
    pred_packs = np.maximum(pred_packs, 0)
    pred_value = np.maximum(pred_value, 0)
    
    return pred_packs, pred_value

# Store forecasts
forecasts = {}
skus = hist_df['ProductName'].unique()

print(f"Forecasting for {len(skus)} unique SKUs...")
for sku in skus:
    sku_hist = hist_df[hist_df['ProductName'] == sku].set_index('date')
    
    # Resample to ensure continuous timeline (fill missing months with 0)
    ts_packs = sku_hist['Packs'].resample('MS').sum().fillna(0)
    ts_value = sku_hist['Value'].resample('MS').sum().fillna(0)
    
    packs_pred, value_pred = forecast_sku(ts_packs, ts_value)
    forecasts[sku] = {'packs': packs_pred, 'value': value_pred}

# ==========================================
# 3. VISUALIZATION (Sample SKU)
# ==========================================
sample_sku = 'SKU66' # High-volume example
if sample_sku in forecasts:
    sku_hist_vis = hist_df[hist_df['ProductName'] == sample_sku].set_index('date')['Value'].resample('MS').sum().fillna(0)
    sku_forecast_vis = forecasts[sample_sku]['value']

    plt.figure(figsize=(12, 6))
    plt.plot(sku_hist_vis.index, sku_hist_vis.values, label='Historical Value (2017-2020)', color='blue', linewidth=2)
    future_dates = pd.date_range(start='2021-01-01', periods=11, freq='MS')
    plt.plot(future_dates, sku_forecast_vis, label='2021 Forecast (Holt-Winters)', color='red', linestyle='--', linewidth=2)
    plt.title(f'Sales Value Forecast for {sample_sku}')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

# ==========================================
# 4. WRITE BACK TO EXCEL (Range G4261:H5599)
# ==========================================
print("Writing forecasts back to Excel...")
wb = load_workbook(file_path)
ws = wb.active

# Map forecasts to the specific rows for 2021
# Based on data structure: Record ID 4260 corresponds to Row 4261 (Header is Row 1)
for index, row in future_df.iterrows():
    sku = row['ProductName']
    month = row['month'] # 1 to 11
    
    if sku in forecasts:
        forecast_idx = month - 1  # month 1 is index 0, month 2 is index 1, etc.
        packs_val = forecasts[sku]['packs'][forecast_idx]
        value_val = forecasts[sku]['value'][forecast_idx]
    else:
        # Fallback for completely new SKUs appearing only in 2021
        packs_val = 0
        value_val = 0
    
    # Calculate Excel Row Number: Record ID + 1 
    excel_row = int(row['Record ID']) + 1 
    
    # Write to Column G (7) and Column H (8)
    ws.cell(row=excel_row, column=7, value=round(packs_val, 0))
    ws.cell(row=excel_row, column=8, value=round(value_val, 0))

output_file = r'E:\Pie\test_task_forecasted.xlsx'
wb.save(output_file)
print(f"Success! Forecasted file saved as: {output_file}")
