"""
Customer Engagement & Product Utilization Analytics
European Central Bank - Churn Retention Dashboard
All 4 modules + 3 user filters as specified in the ECB brief
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pickle, os
from matplotlib.colors import LinearSegmentedColormap
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import GradientBoostingClassifier

st.set_page_config(
    page_title="ECB Churn Retention Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Colours ───────────────────────────────────────────────────────────────────
NAVY, BLUE, TEAL = '#0D1B2A', '#1B4F8A', '#00897B'
AMBER, RED = '#F4A261', '#E63946'
PROFILES = ['Active Engaged','Active Low-Product','Inactive High-Balance','Inactive Disengaged']
PCOLS = [TEAL, BLUE, AMBER, RED]
CMAP = LinearSegmentedColormap.from_list('risk', [TEAL, AMBER, RED])

st.markdown("""
<style>
.main {background:#F4F7FB;}
.kpi-card {background:white;border-radius:12px;padding:18px 22px;
           box-shadow:0 2px 10px rgba(13,27,42,0.08);
           border-left:4px solid #00897B;margin-bottom:8px;}
.kpi-val  {font-size:28px;font-weight:800;color:#0D1B2A;}
.kpi-lbl  {font-size:12px;color:#555;font-weight:600;text-transform:uppercase;letter-spacing:1px;}
.kpi-note {font-size:11px;color:#888;margin-top:4px;}
</style>
""", unsafe_allow_html=True)

# ── Data & Model ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    for p in ['European_Bank.csv','../European_Bank.csv','data/European_Bank.csv']:
        if os.path.exists(p):
            return pd.read_csv(p)
    st.error("European_Bank.csv not found. Place it in the app folder.")
    st.stop()

@st.cache_resource
def get_model(df_raw):
    mp, sp, fp = 'model/churn_model.pkl','model/scaler.pkl','model/feature_names.pkl'
    if all(os.path.exists(x) for x in [mp,sp,fp]):
        with open(mp,'rb') as f: model = pickle.load(f)
        with open(sp,'rb') as f: scaler = pickle.load(f)
        with open(fp,'rb') as f: feats  = pickle.load(f)
        return model, scaler, feats
    # Train fresh if model files not found
    d = df_raw.copy()
    d = d.drop([c for c in ['Year','CustomerId','Surname'] if c in d.columns], axis=1)
    le = LabelEncoder(); d['Gender'] = le.fit_transform(d['Gender'])
    d = pd.get_dummies(d, columns=['Geography'], drop_first=False)
    BAL75 = df_raw['Balance'].quantile(0.75)
    d['RSI'] = df_raw['IsActiveMember']+(df_raw['NumOfProducts']-1)/3.0+df_raw['Tenure']/10.0
    d['SBR'] = df_raw['Balance']/(df_raw['EstimatedSalary']+1)
    X = d.drop('Exited', axis=1); y = d['Exited']
    feats = list(X.columns)
    sc = StandardScaler(); X_sc = sc.fit_transform(X)
    m = GradientBoostingClassifier(n_estimators=150,learning_rate=0.08,max_depth=4,random_state=42)
    m.fit(X_sc, y)
    return m, sc, feats

df_raw = load_data()
model, scaler, feature_names = get_model(df_raw)

# ── Feature Engineering ───────────────────────────────────────────────────────
df = df_raw.copy()
df = df.drop([c for c in ['Year','CustomerId','Surname'] if c in df.columns], axis=1)
BAL75 = df['Balance'].quantile(0.75)
SAL75 = df['EstimatedSalary'].quantile(0.75)

def ep(r):
    a=r['IsActiveMember']==1; m=r['NumOfProducts']>=2; hb=r['Balance']>BAL75
    if a and m: return 'Active Engaged'
    if a and not m: return 'Active Low-Product'
    if not a and hb: return 'Inactive High-Balance'
    return 'Inactive Disengaged'

df['EngagementProfile'] = df.apply(ep, axis=1)
df['RSI'] = df['IsActiveMember'] + (df['NumOfProducts']-1)/3.0 + df['Tenure']/10.0
df['RSI_Tier'] = pd.cut(df['RSI'], bins=[-0.01,0.5,1.2,2.0,3.1],
    labels=['Very Weak','Weak','Strong','Very Strong'])
df['SBR'] = df['Balance'] / (df['EstimatedSalary']+1)
df['SBR_Tier'] = pd.cut(df['SBR'], bins=[-0.01,0.3,0.8,100],
    labels=['Under-banked','Balanced','Over-banked'])
df['IsPremium'] = ((df['Balance']>BAL75)|(df['EstimatedSalary']>SAL75)).astype(int)
df['PremInactive'] = ((df['IsPremium']==1)&(df['IsActiveMember']==0)).astype(int)
df['AgeGroup'] = pd.cut(df['Age'], bins=[17,30,40,50,60,100],
    labels=['18-30','31-40','41-50','51-60','60+'])

# Score all customers
def score_df(df_in, model, scaler, feature_names):
    d = df_in.copy()
    le = LabelEncoder(); d['Gender'] = le.fit_transform(d['Gender'])
    d = pd.get_dummies(d, columns=['Geography'], drop_first=False)
    for col in feature_names:
        if col not in d.columns: d[col] = 0
    d = d[feature_names]
    X_sc = scaler.transform(d)
    return model.predict_proba(X_sc)[:,1]

df_score = df[['CreditScore','Gender','Age','Tenure','Balance','NumOfProducts',
               'HasCrCard','IsActiveMember','EstimatedSalary','Geography']].copy()
df_score['RSI'] = df['RSI']; df_score['SBR'] = df['SBR']
df['ChurnProb'] = score_df(df_score, model, scaler, feature_names)
df['RiskTier'] = pd.cut(df['ChurnProb'], bins=[0,0.30,0.60,1.0],
    labels=['Low Risk','Medium Risk','High Risk'])

# ── SIDEBAR FILTERS ───────────────────────────────────────────────────────────
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/European_Central_Bank_logo.svg/200px-European_Central_Bank_logo.svg.png", width=160)
st.sidebar.markdown("## Dashboard Filters")

# Module navigation
page = st.sidebar.radio("Navigate to Module", [
    "📊 Engagement vs Churn Overview",
    "📦 Product Utilisation Impact",
    "🔍 High-Value Disengaged Detector",
    "💪 Retention Strength Scoring",
    "🎯 Individual Risk Predictor",
])

st.sidebar.markdown("---")

st.sidebar.markdown("### Filter Data")

# Filter 1 — Engagement status
eng_filter = st.sidebar.multiselect(
    "Engagement Status",
    options=['Active','Inactive'],
    default=['Active','Inactive']
)

# Filter 2 — Product count slider (ECB required)
prod_range = st.sidebar.slider("Number of Products", 1, 4, (1, 4))

# Filter 3 — Balance threshold (ECB required)
bal_min = st.sidebar.number_input("Min. Balance (EUR)", 0, 250000, 0, step=5000)

# Filter 4 — Salary threshold (ECB required)
sal_min = st.sidebar.number_input("Min. Est. Salary (EUR)", 0, 250000, 0, step=5000)

# Filter 5 — Geography
geo_opts = df['Geography'].unique().tolist()
geo_filter = st.sidebar.multiselect("Geography", options=geo_opts, default=geo_opts)

# Apply filters
mask = pd.Series([True]*len(df), index=df.index)
if 'Active' in eng_filter and 'Inactive' not in eng_filter:
    mask &= df['IsActiveMember'] == 1
elif 'Inactive' in eng_filter and 'Active' not in eng_filter:
    mask &= df['IsActiveMember'] == 0
mask &= df['NumOfProducts'].between(prod_range[0], prod_range[1])
mask &= df['Balance'] >= bal_min
mask &= df['EstimatedSalary'] >= sal_min
mask &= df['Geography'].isin(geo_filter)
dff = df[mask].copy()

st.sidebar.markdown(f"**{len(dff):,} customers** shown")
st.sidebar.markdown("---")
st.sidebar.markdown("*European Central Bank*  \n*Churn Retention Analytics*")

st.sidebar.markdown("""
<div style='background:#1a1a2e; padding:10px; border-radius:10px; border:1px solid #333'>
👨‍💻 <b>Dikshit</b> &nbsp; | &nbsp; 🏢 <b>Unified Mentor</b>
</div>
""", unsafe_allow_html=True)

# ── MODULE 1 — Engagement vs Churn Overview ───────────────────────────────────
if page == "📊 Engagement vs Churn Overview":
    st.title("📊 Engagement vs Churn Overview")
    st.markdown("*How customer engagement levels affect churn across profiles and geographies*")

    c1,c2,c3,c4 = st.columns(4)
    act  = dff[dff['IsActiveMember']==1]['Exited'].mean()*100
    inact= dff[dff['IsActiveMember']==0]['Exited'].mean()*100
    ERR  = inact/act if act>0 else 0
    c1.markdown(f'<div class="kpi-card"><div class="kpi-lbl">Overall Churn</div><div class="kpi-val">{dff["Exited"].mean()*100:.1f}%</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card"><div class="kpi-lbl">Active Churn</div><div class="kpi-val">{act:.1f}%</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card"><div class="kpi-lbl">Inactive Churn</div><div class="kpi-val">{inact:.1f}%</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card" style="border-color:#E63946"><div class="kpi-lbl">KPI 1 — ERR</div><div class="kpi-val">{ERR:.2f}x</div><div class="kpi-note">Inactive churn {ERR:.1f}x more</div></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(7,5))
        pc = dff.groupby('EngagementProfile')['Exited'].mean().reindex(PROFILES)*100
        bars = ax.bar(range(4), pc.values, color=PCOLS, edgecolor='white', width=0.6)
        for b,v in zip(bars,pc.values): ax.text(b.get_x()+b.get_width()/2,v+0.3,f'{v:.1f}%',ha='center',fontweight='bold',fontsize=11)
        ax.set_xticks(range(4)); ax.set_xticklabels([p.replace(' ','\n') for p in PROFILES],fontsize=9)
        ax.set_title('Churn Rate by Engagement Profile',fontweight='bold',color=NAVY,fontsize=13)
        ax.set_ylabel('Churn Rate (%)'); ax.spines[['top','right']].set_visible(False)
        st.pyplot(fig); plt.close()
    with col2:
        fig, ax = plt.subplots(figsize=(7,5))
        piv = dff.pivot_table(values='Exited',index='EngagementProfile',columns='Geography',aggfunc='mean').reindex(PROFILES)*100
        sns.heatmap(piv,ax=ax,cmap=CMAP,annot=True,fmt='.0f',linewidths=0.5,linecolor='white',
            cbar_kws={'label':'Churn %','shrink':0.8},annot_kws={'size':12,'weight':'bold'})
        ax.set_title('Profile x Geography Heatmap',fontweight='bold',color=NAVY,fontsize=13)
        ax.set_xlabel(''); ax.set_ylabel('')
        st.pyplot(fig); plt.close()

    st.markdown("---")
    st.markdown("**Profile Distribution**")
    pcounts = dff['EngagementProfile'].value_counts().reindex(PROFILES)
    fig, ax = plt.subplots(figsize=(14,3.5))
    ct = dff.groupby(['EngagementProfile','Exited']).size().unstack(fill_value=0).reindex(PROFILES)
    ax.bar(range(4),ct[0],color=[c+'66' for c in ['#00897B','#1B4F8A','#F4A261','#E63946']],label='Retained',edgecolor='white',width=0.6)
    ax.bar(range(4),ct[1],bottom=ct[0],color=PCOLS,label='Churned',edgecolor='white',width=0.6)
    ax.set_xticks(range(4)); ax.set_xticklabels([f'{p}\n(n={pcounts[p]:,})' for p in PROFILES],fontsize=10)
    ax.set_title('Customer Count by Engagement Profile',fontweight='bold',color=NAVY,fontsize=13)
    ax.set_ylabel('Customers'); ax.legend(frameon=False); ax.spines[['top','right']].set_visible(False)
    st.pyplot(fig); plt.close()

# ── MODULE 2 — Product Utilisation Impact ─────────────────────────────────────
elif page == "📦 Product Utilisation Impact":
    st.title("📦 Product Utilisation Impact Analysis")
    st.markdown("*How product depth, credit card ownership, and financial commitment affect retention*")

    p1 = dff[dff['NumOfProducts']==1]['Exited'].mean()*100
    p2 = dff[dff['NumOfProducts']==2]['Exited'].mean()*100
    cc_no = dff[dff['HasCrCard']==0]['Exited'].mean()*100
    cc_yes= dff[dff['HasCrCard']==1]['Exited'].mean()*100
    hbi = dff[(dff['Balance']>BAL75)&(dff['IsActiveMember']==0)]['Exited'].mean()*100
    hba = dff[(dff['Balance']>BAL75)&(dff['IsActiveMember']==1)]['Exited'].mean()*100

    c1,c2,c3 = st.columns(3)
    c1.markdown(f'<div class="kpi-card"><div class="kpi-lbl">KPI 2 — Product Depth</div><div class="kpi-val">{p1-p2:.1f}pp</div><div class="kpi-note">Churn reduction: 1 to 2 products</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card"><div class="kpi-lbl">KPI 3 — High-Bal Disengagement</div><div class="kpi-val">{hbi:.1f}%</div><div class="kpi-note">Premium inactive churn rate</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card"><div class="kpi-lbl">KPI 4 — CC Stickiness</div><div class="kpi-val">{cc_no-cc_yes:+.1f}pp</div><div class="kpi-note">Credit card holders churn less</div></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(7,5))
        pd_c = dff.groupby('NumOfProducts')['Exited'].mean()*100
        pd_n = dff.groupby('NumOfProducts').size()
        bars = ax.bar(pd_c.index.astype(str),pd_c.values,
            color=[TEAL if v<15 else AMBER if v<50 else RED for v in pd_c.values],edgecolor='white',width=0.55)
        for b,v,n in zip(bars,pd_c.values,pd_n.values):
            ax.text(b.get_x()+b.get_width()/2,v+0.5,f'{v:.0f}%\n(n={n:,})',ha='center',fontsize=10,fontweight='bold')
        ax.set_title('KPI 2 - Product Depth Index',fontweight='bold',color=NAVY,fontsize=13)
        ax.set_xlabel('Number of Products'); ax.set_ylabel('Churn Rate (%)')
        ax.spines[['top','right']].set_visible(False)
        st.pyplot(fig); plt.close()
    with col2:
        fig, ax = plt.subplots(figsize=(7,5))
        piv2 = dff.pivot_table(values='Exited',index='NumOfProducts',columns='IsActiveMember',aggfunc='mean')*100
        piv2.columns=['Inactive','Active']
        sns.heatmap(piv2,ax=ax,cmap=CMAP,annot=True,fmt='.0f',linewidths=0.5,linecolor='white',
            cbar_kws={'label':'Churn %','shrink':0.8},annot_kws={'size':13,'weight':'bold'})
        ax.set_title('Products x Active Status',fontweight='bold',color=NAVY,fontsize=13)
        st.pyplot(fig); plt.close()

    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(7,5))
        segs = {
            'High-Bal Active':  dff[(dff['Balance']>BAL75)&(dff['IsActiveMember']==1)]['Exited'].mean()*100,
            'High-Bal Inactive':dff[(dff['Balance']>BAL75)&(dff['IsActiveMember']==0)]['Exited'].mean()*100,
            'Low-Bal Active':   dff[(dff['Balance']<=BAL75)&(dff['IsActiveMember']==1)]['Exited'].mean()*100,
            'Low-Bal Inactive': dff[(dff['Balance']<=BAL75)&(dff['IsActiveMember']==0)]['Exited'].mean()*100,
        }
        bars = ax.bar(range(4),list(segs.values()),color=[TEAL,RED,BLUE,AMBER],edgecolor='white',width=0.6)
        for b,v in zip(bars,segs.values()): ax.text(b.get_x()+b.get_width()/2,v+0.3,f'{v:.1f}%',ha='center',fontweight='bold',fontsize=12)
        ax.set_xticks(range(4)); ax.set_xticklabels([k.replace(' ','\n') for k in segs],fontsize=9)
        ax.set_title('KPI 3 - High-Balance Disengagement',fontweight='bold',color=NAVY,fontsize=13)
        ax.set_ylabel('Churn Rate (%)'); ax.spines[['top','right']].set_visible(False)
        st.pyplot(fig); plt.close()
    with col2:
        fig, ax = plt.subplots(figsize=(7,5))
        cc = dff.groupby('HasCrCard')['Exited'].mean()*100
        bars = ax.bar(['No Credit Card','Has Credit Card'],cc.values,color=[RED,TEAL],width=0.45,edgecolor='white')
        for b,v in zip(bars,cc.values): ax.text(b.get_x()+b.get_width()/2,v+0.3,f'{v:.1f}%',ha='center',fontweight='bold',fontsize=13)
        ax.text(0.5,0.88,f'Stickiness: {cc[0]-cc[1]:+.1f}pp',transform=ax.transAxes,ha='center',
            fontsize=11,color=TEAL,fontweight='bold',bbox=dict(boxstyle='round',facecolor='white',edgecolor=TEAL,alpha=0.9))
        ax.set_title('KPI 4 - Credit Card Stickiness',fontweight='bold',color=NAVY,fontsize=13)
        ax.set_ylabel('Churn Rate (%)'); ax.spines[['top','right']].set_visible(False)
        st.pyplot(fig); plt.close()

# ── MODULE 3 — High-Value Disengaged Detector ─────────────────────────────────
elif page == "🔍 High-Value Disengaged Detector":
    st.title("🔍 High-Value Disengaged Customer Detector")
    st.markdown("*Identify premium customers who are disengaged and at risk of churning silently*")

    col1, col2, col3 = st.columns(3)
    churn_thresh = col1.slider("Churn Probability Threshold", 0.1, 0.9, 0.40, 0.05)
    bal_thresh   = col2.number_input("Min Balance for 'Premium' (EUR)", 0, 250000, 50000, 5000)
    sal_thresh   = col3.number_input("Min Salary for 'Premium' (EUR)", 0, 250000, 80000, 5000)

    hvd = dff[
        ((dff['Balance'] > bal_thresh) | (dff['EstimatedSalary'] > sal_thresh)) &
        (dff['IsActiveMember'] == 0) &
        (dff['ChurnProb'] > churn_thresh)
    ].sort_values('ChurnProb', ascending=False)

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f'<div class="kpi-card" style="border-color:#E63946"><div class="kpi-lbl">Customers Flagged</div><div class="kpi-val">{len(hvd):,}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card" style="border-color:#E63946"><div class="kpi-lbl">Balance at Risk</div><div class="kpi-val">EUR {hvd["Balance"].sum()/1e6:.1f}M</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card"><div class="kpi-lbl">Avg Churn Prob</div><div class="kpi-val">{hvd["ChurnProb"].mean()*100:.1f}%</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card"><div class="kpi-lbl">Avg Balance</div><div class="kpi-val">EUR {hvd["Balance"].mean():,.0f}</div></div>', unsafe_allow_html=True)

    st.markdown(f"### {len(hvd):,} High-Value Disengaged Customers")
    if len(hvd) > 0:
        show_cols = ['Age','Geography','Gender','Balance','EstimatedSalary','NumOfProducts','Tenure','ChurnProb','RiskTier']
        show_cols = [c for c in show_cols if c in hvd.columns]
        disp = hvd[show_cols].copy()
        disp['ChurnProb'] = (disp['ChurnProb']*100).round(1).astype(str)+'%'
        disp['Balance'] = disp['Balance'].apply(lambda x: f"EUR {x:,.0f}")
        st.dataframe(disp.head(50), use_container_width=True)

        csv = hvd[show_cols].to_csv(index=False)
        st.download_button("Download Full List (CSV)", csv, "high_value_disengaged.csv", "text/csv")

        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots(figsize=(6,4))
            geo_c = hvd.groupby('Geography').size()
            ax.bar(geo_c.index, geo_c.values, color=[RED,AMBER,BLUE], edgecolor='white', width=0.5)
            for i,(g,v) in enumerate(geo_c.items()): ax.text(i,v+0.5,str(v),ha='center',fontweight='bold',fontsize=12)
            ax.set_title('Flagged Customers by Geography',fontweight='bold',color=NAVY,fontsize=12)
            ax.spines[['top','right']].set_visible(False)
            st.pyplot(fig); plt.close()
        with col2:
            fig, ax = plt.subplots(figsize=(6,4))
            ax.hist(hvd['ChurnProb'], bins=20, color=RED, alpha=0.8, edgecolor='white')
            ax.set_title('Churn Probability Distribution',fontweight='bold',color=NAVY,fontsize=12)
            ax.set_xlabel('Churn Probability'); ax.set_ylabel('Count')
            ax.spines[['top','right']].set_visible(False)
            st.pyplot(fig); plt.close()
    else:
        st.info("No customers match the current criteria. Try lowering the thresholds.")

# ── MODULE 4 — Retention Strength Scoring ─────────────────────────────────────
elif page == "💪 Retention Strength Scoring":
    st.title("💪 Retention Strength Scoring Panel")
    st.markdown("*KPI 5 — Relationship Strength Index and sticky customer analysis*")

    rt = ['Very Weak','Weak','Strong','Very Strong']
    rsi_c = dff.groupby('RSI_Tier',observed=True)['Exited'].mean().reindex(rt)*100
    rsi_n = dff.groupby('RSI_Tier',observed=True).size().reindex(rt)
    rsi_vw = dff[dff['RSI']<0.5]['Exited'].mean()*100
    rsi_vs = dff[dff['RSI']>2.0]['Exited'].mean()*100
    sticky = dff[(dff['RSI']>2.0)&(dff['NumOfProducts']>=2)&(dff['IsActiveMember']==1)]

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f'<div class="kpi-card"><div class="kpi-lbl">KPI 5 - Very Weak RSI</div><div class="kpi-val">{rsi_vw:.1f}%</div><div class="kpi-note">Churn rate</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card"><div class="kpi-lbl">KPI 5 - Very Strong RSI</div><div class="kpi-val">{rsi_vs:.1f}%</div><div class="kpi-note">Churn rate</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card"><div class="kpi-lbl">RSI Range</div><div class="kpi-val">{rsi_vw-rsi_vs:.0f}pp</div><div class="kpi-note">Improvement potential</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card" style="border-color:#00897B"><div class="kpi-lbl">Sticky Customers</div><div class="kpi-val">{len(sticky):,}</div><div class="kpi-note">RSI>2 + 2+ products + Active</div></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(7,5))
        bars = ax.bar(range(4),rsi_c.values,color=[RED,AMBER,BLUE,TEAL],edgecolor='white',width=0.6)
        for b,v,n in zip(bars,rsi_c.values,rsi_n.values):
            ax.text(b.get_x()+b.get_width()/2,v+0.3,f'{v:.0f}%\n(n={int(n):,})',ha='center',fontsize=10,fontweight='bold')
        ax.set_xticks(range(4)); ax.set_xticklabels(['Very\nWeak','Weak','Strong','Very\nStrong'],fontsize=9)
        ax.set_title('KPI 5 - Relationship Strength Index',fontweight='bold',color=NAVY,fontsize=13)
        ax.set_ylabel('Churn Rate (%)'); ax.spines[['top','right']].set_visible(False)
        st.pyplot(fig); plt.close()
    with col2:
        fig, ax = plt.subplots(figsize=(7,5))
        ax.hist(dff[dff['Exited']==0]['RSI'],bins=25,color=TEAL,alpha=0.7,label='Retained',edgecolor='white')
        ax.hist(dff[dff['Exited']==1]['RSI'],bins=25,color=RED,alpha=0.7,label='Churned',edgecolor='white')
        ax.set_xlabel('RSI Score (0-3)'); ax.set_ylabel('Count')
        ax.set_title('RSI Distribution by Churn Status',fontweight='bold',color=NAVY,fontsize=13)
        ax.legend(frameon=False); ax.spines[['top','right']].set_visible(False)
        st.pyplot(fig); plt.close()

    col1, col2 = st.columns(2)
    with col1:
        nonsticky = dff[~dff.index.isin(sticky.index)]
        fig, ax = plt.subplots(figsize=(7,5))
        sv = [sticky['Exited'].mean()*100 if len(sticky)>0 else 0,
              nonsticky['Exited'].mean()*100 if len(nonsticky)>0 else 0]
        bars = ax.bar(['Sticky\nCustomers','Non-Sticky\nCustomers'],sv,color=[TEAL,RED],width=0.45,edgecolor='white')
        for b,v in zip(bars,sv): ax.text(b.get_x()+b.get_width()/2,v+0.3,f'{v:.1f}%',ha='center',fontweight='bold',fontsize=14)
        ax.set_title(f'Sticky vs Non-Sticky Churn  (n={len(sticky):,})',fontweight='bold',color=NAVY,fontsize=13)
        ax.set_ylabel('Churn Rate (%)'); ax.spines[['top','right']].set_visible(False)
        st.pyplot(fig); plt.close()
    with col2:
        fig, ax = plt.subplots(figsize=(7,5))
        tenure_c = dff.groupby('Tenure')['Exited'].mean()*100
        ax.plot(tenure_c.index,tenure_c.values,color=BLUE,linewidth=2.5,marker='o',markersize=8,
            markerfacecolor=AMBER,markeredgecolor='white',markeredgewidth=1.5)
        ax.fill_between(tenure_c.index,tenure_c.values,alpha=0.12,color=BLUE)
        ax.axvspan(0,2,alpha=0.08,color=RED,label='High-risk window')
        ax.set_title('Churn Rate by Tenure',fontweight='bold',color=NAVY,fontsize=13)
        ax.set_xlabel('Years with Bank'); ax.set_ylabel('Churn Rate (%)')
        ax.legend(frameon=False,fontsize=9); ax.spines[['top','right']].set_visible(False)
        st.pyplot(fig); plt.close()

# ── MODULE 5 — Individual Risk Predictor ──────────────────────────────────────
elif page == "🎯 Individual Risk Predictor":
    st.title("🎯 Individual Customer Churn Risk Predictor")
    st.markdown("*Score a single customer and get a recommended retention action*")

    col1, col2, col3 = st.columns(3)
    with col1:
        age          = st.slider("Age", 18, 90, 42)
        credit_score = st.number_input("Credit Score", 300, 900, 650)
        balance      = st.number_input("Balance (EUR)", 0.0, 300000.0, 80000.0, 1000.0)
    with col2:
        salary       = st.number_input("Est. Salary (EUR)", 10000.0, 250000.0, 100000.0, 1000.0)
        tenure       = st.slider("Tenure (years)", 0, 10, 3)
        num_products = st.slider("Number of Products", 1, 4, 1)
    with col3:
        geography    = st.selectbox("Geography", ['France','Germany','Spain'])
        gender       = st.selectbox("Gender", ['Male','Female'])
        has_cc       = st.radio("Has Credit Card?", [1, 0], format_func=lambda x: 'Yes' if x else 'No')
        is_active    = st.radio("Active Member?", [1, 0], format_func=lambda x: 'Yes' if x else 'No')

    if st.button("Calculate Churn Risk", type="primary", use_container_width=True):
        rsi_val = is_active + (num_products-1)/3.0 + tenure/10.0
        sbr_val = balance / (salary+1)
        row = pd.DataFrame([{
            'CreditScore':credit_score,'Gender':gender,'Age':age,'Tenure':tenure,
            'Balance':balance,'NumOfProducts':num_products,'HasCrCard':has_cc,
            'IsActiveMember':is_active,'EstimatedSalary':salary,'Geography':geography,
            'RSI':rsi_val,'SBR':sbr_val
        }])
        prob = score_df(row, model, scaler, feature_names)[0]
        risk_pct = prob*100

        col1, col2 = st.columns([1,2])
        with col1:
            color = RED if risk_pct>60 else AMBER if risk_pct>30 else TEAL
            tier  = "HIGH RISK" if risk_pct>60 else "MEDIUM RISK" if risk_pct>30 else "LOW RISK"
            st.markdown(f"""
            <div style="background:white;border-radius:16px;padding:30px;text-align:center;
                        box-shadow:0 4px 20px rgba(0,0,0,0.1);border-top:6px solid {color}">
              <div style="font-size:13px;color:#888;font-weight:600;text-transform:uppercase;letter-spacing:1px">
                Churn Probability</div>
              <div style="font-size:56px;font-weight:900;color:{color};margin:10px 0">{risk_pct:.1f}%</div>
              <div style="font-size:16px;font-weight:700;color:{color}">{tier}</div>
              <div style="font-size:12px;color:#aaa;margin-top:8px">RSI Score: {rsi_val:.2f}</div>
            </div>""", unsafe_allow_html=True)

        with col2:
            st.markdown("#### Recommended Retention Actions")
            actions = []
            if is_active == 0:
                actions.append("🔴 **Re-engage immediately** — inactive member is #1 churn driver")
            if num_products == 1:
                actions.append("🟠 **Cross-sell opportunity** — offer a second product to reduce churn by ~20pp")
            if num_products >= 3:
                actions.append("🟡 **Review product fit** — 3+ products shows elevated churn risk")
            if tenure <= 2:
                actions.append("🟡 **Early lifecycle intervention** — new customers (0-2yr) are most vulnerable")
            if balance > BAL75 and is_active == 0:
                actions.append("🔴 **Premium silent churn risk** — assign a relationship manager immediately")
            if geography == 'Germany':
                actions.append("🟠 **Germany high-risk market** — offer Germany-specific retention programme")
            if not actions:
                actions.append("🟢 **Low risk** — maintain engagement with regular touchpoints")
            for a in actions: st.markdown(a)










