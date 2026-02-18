
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression

st.title("European Bank Customer Churn Dashboard")

@st.cache_data
def load_data():
    return pd.read_csv("Churn_Modelling.csv")

df = load_data()

st.sidebar.header("Filters")

geography = st.sidebar.multiselect("Select Geography", df["Geography"].unique(), default=df["Geography"].unique())
gender = st.sidebar.multiselect("Select Gender", df["Gender"].unique(), default=df["Gender"].unique())

filtered_df = df[(df["Geography"].isin(geography)) & (df["Gender"].isin(gender))]

st.subheader("Filtered Data Overview")
st.write(filtered_df.head())

st.subheader("Churn Distribution")
st.bar_chart(filtered_df["Exited"].value_counts())

# Model training
df_model = df.drop(["RowNumber","CustomerId","Surname"], axis=1)
le = LabelEncoder()
df_model["Gender"] = le.fit_transform(df_model["Gender"])
df_model = pd.get_dummies(df_model, columns=["Geography"], drop_first=True)

X = df_model.drop("Exited", axis=1)
y = df_model["Exited"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

st.subheader("Predict Customer Churn")

credit_score = st.number_input("Credit Score", 300, 900, 600)
age = st.number_input("Age", 18, 100, 35)
balance = st.number_input("Balance", 0.0, 300000.0, 50000.0)
num_products = st.slider("Number of Products", 1, 4, 1)
active_member = st.selectbox("Is Active Member", [0,1])

if st.button("Predict"):
    input_data = np.array([[credit_score, age, 1, 1, balance, num_products, 1, active_member, 50000, 0, 1]])
    input_scaled = scaler.transform(input_data)
    prediction = model.predict(input_scaled)
    probability = model.predict_proba(input_scaled)[0][1]

    st.write("Prediction:", "Churn" if prediction[0] == 1 else "No Churn")
    st.write("Churn Probability:", round(probability*100,2), "%")
