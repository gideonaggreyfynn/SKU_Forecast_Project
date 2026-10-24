# 📊 Pharmaceutical SKU Sales Forecasting

## 📌 Executive Summary
This project forecasts monthly `Packs` and `Value` for ~120 pharmaceutical SKUs for the year 2021. Using a robust time-series approach, the model handles both mature products with clear seasonal trends and "cold-start" new products. The final forecasts are automatically written back to the target Excel template.

## 🧠 Methodology
I utilized **Holt-Winters (Triple Exponential Smoothing)** to capture historical trends and annual seasonality. To ensure robustness across the entire portfolio, I implemented a **Tiered Fallback Strategy**:
1. **Tier 1 (Mature SKUs):** >24 months of data $\rightarrow$ Holt-Winters (Additive Trend & Seasonality).
2. **Tier 2 (Emerging SKUs):** 12-24 months of data $\rightarrow$ Seasonal Naive (Year-over-Year).
3. **Tier 3 (Brand New SKUs):** <12 months of data $\rightarrow$ Historical Mean / Zero.

*Business Logic:* Enforced non-negative constraints post-forecasting, as sales cannot be negative.

## 💡 Key Business Insights
The model successfully identifies product lifecycle stages, preventing costly inventory mistakes:

### 📉 SKU66: Declining Product (Discontinued)
![SKU66 Forecast](visualizations/sku66_declining.png)
*Insight:* SKU66 was a top performer (~$3M/month) but crashed to near-zero in early 2020. The model correctly detected this structural break and forecasted near-zero demand for 2021, preventing massive overstocking.

### 📈 SKU62: Healthy High-Value Product
![SKU62 Forecast](visualizations/sku62_healthy.png)
*Insight:* SKU62 shows strong, recurring annual seasonality. The model accurately captures these peaks and troughs, allowing the supply chain team to proactively plan inventory for high-demand months.

## 🚀 How to Run
1. Clone the repository:
   ```bash
   git clone [your-repo-url]
   cd SKU_Forecast_Project