from datetime import datetime
import streamlit as st
import pandas as pd
import requests
from io import StringIO

st.title("📊 Haleon Awareness Tool")
st.set_page_config(layout="wide") 
# Dictionary of sheet names 
SHEETS = {
    "Report": "https://gist.githubusercontent.com/dimijaf/41ded8133ff12eceb0f18138a0073df7/raw/c79a9875654a6d05c4aa0aa0fd2efaceb4524c01/gistfile1.txt",
    "RealTime": "https://awarenesstool.azurewebsites.net/api/DatabaseBridge/GetAllReport?s=2hp2wNIDkzVgfwxak5719VtGn8FE1VQG90KHuh1tjJsOYjNI",
    "Questions": "https://gist.githubusercontent.com/dimijaf/3d4725c7b69e825eb5f41c2cf41487ce/raw/ada86adb2239795890c5b3fa8d937993778d6764/gistfile1.txt"
}
def load_data(url):
    r = requests.get(url)
    r.raise_for_status()
    return pd.read_csv(StringIO(r.text))

for name, url in SHEETS.items():
    if name not in st.session_state:
        st.session_state[name] = load_data(url)

#sheet_name = st.selectbox("Select Sheet", list(SHEETS.keys()))

tabs = st.tabs(list(SHEETS.keys()))

for i, sheet_name in enumerate(SHEETS.keys()):
    with tabs[i]:
        url = SHEETS[sheet_name]

        if sheet_name not in st.session_state:
            st.session_state[sheet_name] = load_data(url)

        if st.button(f"🔄 Refresh {sheet_name}", key=f"refresh_{sheet_name}"):
            st.session_state[sheet_name] = load_data(url)

        df = st.session_state[sheet_name]
        if sheet_name == "RealTime":
            st.dataframe(df, use_container_width=True)
    
        st.session_state["RealTime"]['QuestionnaireDate'] = pd.to_datetime(
            st.session_state["RealTime"]['QuestionnaireDate'], 
            errors='coerce'
        ).dt.strftime('%d/%m/%y')
        if sheet_name == "Report":
            counts = st.session_state["RealTime"]["DeviceId"].astype(str).value_counts()
            df_t = df.T.copy()
            sum_row = df_t.iloc[0].astype(str).map(counts).fillna(0).astype(int)
            df_t.loc['Sum'] = sum_row
            days_row = pd.Series(0, index=df_t.columns, name='Days Installed')
            installed_row = df_t.loc['Installed Day']
            for col in df_t.columns:
                date_str = str(installed_row[col]).strip()
                if date_str and '/' in date_str:
                    try:
                        days_row[col] = (datetime.now() - pd.to_datetime(date_str)).days
                    except:
                        pass
            df_t.loc['Days Installed'] = days_row
            realtime = st.session_state["RealTime"]
            last_seen_row = pd.Series('', index=df_t.columns, name='Last Seen')
            device_ids_row = df_t.loc['DeviceId']  # Exact row name
            
            for device_id in device_ids_row.index:  # Loop through DeviceIDs row
                device_id_val = str(device_ids_row[device_id]).strip()
                matching_rows = realtime[realtime['DeviceId'].astype(str).str.strip() == device_id_val]
                if not matching_rows.empty:
                    dates = pd.to_datetime(matching_rows['QuestionnaireDate'], errors='coerce')
                    max_date = dates.max()
                    if pd.notna(max_date):
                        last_seen_row[device_id] = max_date.strftime('%m/%d/%y')
                    else:
                        last_seen_row[device_id] = 'No date'
            df_t.loc['Last Seen'] = last_seen_row
            avg_row = (
                pd.to_numeric(df_t.loc["Sum"], errors="coerce") /
                pd.to_numeric(df_t.loc["Days Installed"], errors="coerce")
            ).round(3)
            df_t.loc['Average'] = avg_row
            styled_df = df_t.style.set_properties(
                **{
                    'background-color': 'black',
                    'color': 'white',
                    'font-weight': 'bold'
                }
            )
            st.dataframe(
                styled_df, 
                height=1000, 
                use_container_width=True,
                column_config={
                    col: st.column_config.Column(width="small") 
                    for col in df_t.columns
                }
            )
        if sheet_name == "Questions":
            realtime = st.session_state["RealTime"]
            question_names = df.index.tolist()
            df['NAI_Count'] = 0
            df['NAI_%'] = 0.0
    
    # Count NAI for each Q1, Q2, etc. column from RealTime
            for q_name in question_names:
                if q_name in realtime.columns:  # Check if Q1, Q2 etc exists in RealTime
                    #
                    nai_count = (realtime[q_name] == 1).sum()  # or realtime[q_name].eq('ΝΑΙ').sum()
                    total_count = realtime[q_name].notna().sum()
                    
                    df.loc[q_name, 'NAI_Count'] = nai_count
                    df.loc[q_name, 'NAI_%'] = round((nai_count / total_count * 100), 1) if total_count > 0 else 0
            
            st.dataframe(df, use_container_width=True, height=600)
#url = SHEETS[sheet_name]



####df = st.session_state[sheet_name]




    
    

