# European-bank
Comprehensive Customer Churn Analysis: Key Findings & Strategic Insights

This analysis of the European Bank customer data aimed to identify key drivers of churn and classify customer engagement to inform retention strategies. The process involved data validation, engagement and product utilization analysis, financial commitment assessment, and retention strength scoring, culminating in an interactive dashboard.
Key Findings:

 Data Quality: The dataset was found to be clean and complete, with no missing values and consistent data types across all columns. This ensures the reliability of our analysis.

  Churn Patterns Related to Balance:
        High-Balance Churners: A critical insight is that customers who churn, regardless of their active membership status, consistently exhibit higher average balances than those who are retained. Specifically, inactive churned customers had an average balance of approximately $90,988 (vs. $72,048 for retained), and active churned customers had about $91,320 (vs. $73,304 for retained). This indicates that the bank is losing its more financially significant customers.
        At-Risk Premium Segment: A substantial group of 1,908 high-value customers (those in the top 25% balance bracket) were identified as being at risk of churning, representing a significant potential loss.

   Product Utilization and Churn:
        Product Count Impact: The number of products a customer holds is a strong indicator of churn risk. Customers with only one product (Single-Product) have a significantly higher churn rate (27.71%) compared to Multi-Product customers (12.77%).
        Optimal Product Number: Customers with two products exhibit the lowest churn rate (7.58%). Conversely, customers with three products (82.71%) and four products (100%) have extremely high churn rates, suggesting dissatisfaction or an overwhelming product experience for these segments.

   Customer Engagement Profiles and Churn Rates:
        'Sticky Customers' (Active & 2 Products): This group demonstrates the lowest churn rate at ~5.56%, highlighting the effectiveness of being an active member with an optimal number of products.
        'Active & Engaged' (Active & >2 Products): Surprisingly, this segment shows the highest churn rate at ~80.28%. This aligns with the finding that 3+ products correlate with very high churn, indicating that simply being active with many products does not guarantee retention; it might even be a risk factor.
        'Inactive & Disengaged': As expected, this group has a high churn rate of ~36.65%.

   Retention Strength Scoring: A RetentionStrengthScore was developed, categorizing customers into 'High Risk', 'Medium Risk', 'Stable', and 'Strong' groups, providing a comprehensive view of individual customer churn probability.

   Credit Card Ownership: Customers with a credit card show a high Credit Card Stickiness Score of ~79.82%, indicating that credit card holders are generally more loyal.

Valuable Insights & Proposed Retention Strategies:

  Prioritize High-Value At-Risk Customers: Implement a targeted, personalized outreach program for the 1,908 identified high-balance, non-churned customers. Offer exclusive benefits, relationship manager support, or tailored product recommendations.

   Optimize Product Portfolio and Bundling:
        Promote 2-Product Adoption: Actively encourage single-product customers to adopt a second product, as this profile (

Interactive Visualization: Streamlit Dashboard

For an interactive exploration of these findings, the Streamlit dashboard provides a dynamic interface to filter customer segments, visualize churn rates by engagement profiles and product categories, identify high-value disengaged customers, and analyze retention risk distribution.
