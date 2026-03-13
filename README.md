# Customer Engagement & Product Utilization Analytics
## European Central Bank — Churn Retention Strategy

### Quick Start
**Notebook:**
```bash
jupyter notebook European_Bank_Analysis.ipynb
```
**Streamlit App:**
```bash
cd app/
streamlit run app.py
```

### Package Contents
| File | Description |
|------|-------------|
| European_Bank_Analysis.ipynb | Full 31-cell analysis notebook |
| docs/Research_Paper_ECB.docx | Complete research paper (11 sections, 5 figures) |
| app/app.py | Streamlit dashboard (4 modules, 5 filters) |
| app/model/ | Pre-trained Gradient Boosting model |
| figures/ | 5 publication-quality chart panels |
| European_Bank.csv | Dataset (10,000 customers) |

### Key Results
- Overall churn: 20.4% | Germany: 32.4%
- Engagement Retention Ratio: 1.88x
- Product sweet spot: 2 products = 7.6% churn
- 2,154 premium inactive customers | EUR 232.9M at risk
- Best model: Gradient Boosting (AUC = 0.8694)
