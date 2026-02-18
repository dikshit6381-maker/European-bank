import streamlit as st
import pandas as pd

# Load the dataset within the Streamlit app environment
df = pd.read_csv('European_Bank.csv')

# --- Re-create necessary derived columns ---

# Engagement Profile
def create_engagement_profile(row):
    if row['IsActiveMember'] == 1 and row['NumOfProducts'] == 2:
        return 'Sticky Customers'
    elif row['IsActiveMember'] == 0 and row['NumOfProducts'] == 1:
        return 'Inactive & Disengaged'
    elif row['IsActiveMember'] == 1 and row['NumOfProducts'] == 1:
        return 'Active but Low-Product'
    elif row['IsActiveMember'] == 0 and row['NumOfProducts'] > 1:
        return 'Inactive but Multi-Product'
    elif row['IsActiveMember'] == 1 and row['NumOfProducts'] > 2:
        return 'Active & Engaged'
    else:
        return 'Other'
df['Engagement_Profile'] = df.apply(create_engagement_profile, axis=1)

# Product Category
df['ProductCategory'] = df['NumOfProducts'].apply(lambda x: 'Single-Product' if x == 1 else 'Multi-Product')

# Normalization helpers for scores
df['TenureScore'] = (df['Tenure'] / df['Tenure'].max()) * 100
df['ProductScore'] = (df['NumOfProducts'] / df['NumOfProducts'].max()) * 100
df['ActiveScore'] = df['IsActiveMember'].apply(lambda x: 100 if x==1 else 0)

# Engagement Score
df['EngagementScore'] = (
    0.5*df['ActiveScore'] +
    0.3*df['ProductScore'] +
    0.2*df['TenureScore']
)

# Balance and Salary Scores
df['BalanceScore'] = (df['Balance'] / df['Balance'].max()) * 100
df['SalaryScore'] = (df['EstimatedSalary'] / df['EstimatedSalary'].max()) * 100

# Value Score
df['ValueScore'] = (
    0.6*df['BalanceScore'] +
    0.4*df['SalaryScore']
)

# Retention Strength Score
df['RetentionStrengthScore'] = (
    0.4*df['EngagementScore'] +
    0.3*df['ProductScore'] +
    0.2*df['ValueScore'] +
    0.1*df['TenureScore']
)

# Risk Bucket
def risk_bucket(score):
    if score <= 40:
        return "High Risk"
    elif score <= 65:
        return "Medium Risk"
    elif score <= 80:
        return "Stable"
    else:
        return "Strong"
df['RiskCategory'] = df['RetentionStrengthScore'].apply(risk_bucket)
df['RetentionRisk'] = df['RetentionStrengthScore'].apply(risk_bucket)


# --- Streamlit App Layout ---
st.set_page_config(layout="wide")

st.title("Customer Engagement & Retention Strategy Dashboard")
st.markdown("### Analyze customer churn, engagement, and retention risks.")

# Sidebar for Filters
st.sidebar.header("Filters")

min_engagement = st.sidebar.slider("Min Engagement Score", 0, 100, 30)
min_products = st.sidebar.slider("Min Products", 1, 4, 1)
min_balance = st.sidebar.slider("Min Balance", 0, int(df['Balance'].max()), 0)
min_salary = st.sidebar.slider("Min Salary", 0, int(df['EstimatedSalary'].max()), 0)

filtered_df = df[
    (df['EngagementScore'] >= min_engagement) &
    (df['NumOfProducts'] >= min_products) &
    (df['Balance'] >= min_balance) &
    (df['EstimatedSalary'] >= min_salary)
]

# --- Dashboard Tabs ---
tab1, tab2, tab3 = st.tabs(["Overview", "High-Value Customers", "Retention Risk Analysis"])

with tab1:
    st.header("Overall Customer Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Customers", len(filtered_df), delta="", delta_color="off")
    col2.metric("Churn Rate (%)", round(filtered_df['Exited'].mean() * 100, 2), delta="", delta_color="off")
    col3.metric("Avg Retention Strength Score", round(filtered_df['RetentionStrengthScore'].mean(), 2), delta="", delta_color="off")

    st.subheader("Engagement Profile Churn Rates")
    churn_rates = filtered_df.groupby('Engagement_Profile')['Exited'].mean().sort_values(ascending=False) * 100
    st.bar_chart(churn_rates)

    st.subheader("Churn Rate by Product Category")
    churn_rate_by_category = filtered_df.groupby('ProductCategory')['Exited'].mean().sort_values(ascending=False) * 100
    st.bar_chart(churn_rate_by_category)

with tab2:
    st.header("Focus on High-Value Disengaged Customers")
    st.markdown("Customers with high 'ValueScore' but low 'EngagementScore' are critical for retention efforts.")

    high_value_disengaged = filtered_df[
        (filtered_df['ValueScore'] >= 70) &
        (filtered_df['EngagementScore'] <= 35)
    ]
    if not high_value_disengaged.empty:
        st.dataframe(high_value_disengaged.head())
        st.info(f"Found {len(high_value_disengaged)} high-value disengaged customers in current filter.")
    else:
        st.warning("No high-value disengaged customers found with the current filters.")

with tab3:
    st.header("Customer Retention Risk Distribution")
    st.markdown("Understanding the distribution of customers across different risk categories.")

    risk_counts = filtered_df['RetentionRisk'].value_counts().reindex(["High Risk", "Medium Risk", "Stable", "Strong"], fill_value=0)
    st.bar_chart(risk_counts)

    st.subheader("Average Balance by Activity and Churn Status")
    mean_balance_grouped = filtered_df.groupby(['IsActiveMember', 'Exited'])['Balance'].mean().unstack()
    st.dataframe(mean_balance_grouped)
'''

with open('app.py', 'w') as f:
    f.write(app_content)

print("app.py created successfully!")
