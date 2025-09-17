import streamlit as st
import pandas as pd
import altair as alt
import io
import re

def create_dashboard():
    # 제공된 텍스트 데이터를 파싱하여 DataFrame으로 변환합니다.
    data_text = """
    구분: 100.00
    지표,250908,250909,250910,250911,250912,250913
    총 테스트 수,4157,5798,5039,2445,6426,1809
    PASS,3944,5548,4834,2340,6221,1729
    가성불량,81,110,108,47,86,44
    진성불량,132,140,97,58,119,36
    FAIL,213,250,205,105,205,80
    구분: 101.00
    지표,250908,250909,250910,250911,250912,250913
    총 테스트 수,3258,4760,4419,2233,5625,975
    PASS,2872,4065,3985,1952,5050,876
    가성불량,60,102,96,67,130,18
    진성불량,326,593,338,214,445,81
    FAIL,386,695,434,281,575,99
    구분: 102.00
    지표,250908,250909,250910,250911,250912,250913
    총 테스트 수,20,N/A,1148,1180,4292,756
    PASS,20,N/A,1064,1123,3923,715
    가성불량,0,N/A,57,27,247,20
    진성불량,0,N/A,27,30,122,21
    FAIL,0,N/A,84,57,369,41
    구분: 103.00
    지표,250908,250909,250910,250911,250912,250913
    총 테스트 수,1924,3757,3087,1434,4463,731
    PASS,1830,3471,2896,1353,4139,689
    가성불량,29,184,60,24,85,14
    진성불량,65,102,131,57,239,28
    FAIL,94,286,191,81,324,42
    """
    
    parts = re.split(r'구분:\s*', data_text.strip())[1:]
    
    dfs = []
    for part in parts:
        category, rest = part.split('\n', 1)
        category = category.strip()
        df = pd.read_csv(io.StringIO(rest.strip()))
        
        # Transpose the DataFrame
        df = df.set_index('지표').T
        df.index.name = '날짜'
        df = df.reset_index()
        
        # Add a new column for the '구분' (category)
        df['구분'] = category
        
        # Convert to numeric, coercing errors
        for col in ['총 테스트 수', 'PASS', '가성불량', '진성불량', 'FAIL']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        dfs.append(df)
        
    df_combined = pd.concat(dfs, ignore_index=True)

    st.set_page_config(
        page_title="가성불량 현황 대시보드",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="auto"
    )

    st.title("가성불량 현황 대시보드")
    st.caption("제공된 테스트 데이터를 기반으로 한 대시보드입니다.")
    
    # Sidebar for selection
    st.divider()
    st.sidebar.header("대시보드 필터")
    categories = df_combined['구분'].unique()
    selected_category = st.sidebar.selectbox("구분 (장비)", categories)
    
    filtered_df = df_combined[df_combined['구분'] == selected_category]
    
    # Select date from filtered data
    dates = sorted(filtered_df['날짜'].unique())
    selected_date = st.sidebar.selectbox("날짜", dates, index=len(dates)-1)
    
    # Display key metrics using columns
    st.divider()
    st.subheader(f"날짜: {selected_date} / 구분: {selected_category} 요약")

    col1, col2, col3, col4, col5 = st.columns(5)
    
    day_data = filtered_df[filtered_df['날짜'] == selected_date].iloc[0]
    
    col1.metric("총 테스트 수", f"{day_data['총 테스트 수']:,}", delta=None)
    col2.metric("PASS", f"{day_data['PASS']:,}", delta=None)
    col3.metric("FAIL", f"{day_data['FAIL']:,}", delta=None)
    
    # Calculate delta for false and true defects
    delta_false = None
    delta_true = None
    if len(dates) > 1:
        prev_date = dates[dates.index(selected_date) - 1]
        prev_data = filtered_df[filtered_df['날짜'] == prev_date].iloc[0]
        delta_false = day_data['가성불량'] - prev_data['가성불량']
        delta_true = day_data['진성불량'] - prev_data['진성불량']
    
    col4.metric("가성불량", f"{day_data['가성불량']:,}", delta=f"{int(delta_false)}" if delta_false is not None else None)
    col5.metric("진성불량", f"{day_data['진성불량']:,}", delta=f"{int(delta_true)}" if delta_true is not None else None)
    
    st.divider()
    
    # Charts section
    st.subheader("일자별 불량 추이")
    
    # Line chart for defect trends over time
    chart_data = filtered_df.melt(id_vars=['날짜'], value_vars=['가성불량', '진성불량', 'FAIL'], var_name='불량 유형', value_name='수')
    
    line_chart = alt.Chart(chart_data).mark_line(point=True).encode(
        x=alt.X('날짜', sort=dates, title='날짜'),
        y=alt.Y('수', title='불량 건수'),
        color=alt.Color('불량 유형', legend=alt.Legend(title="불량 유형")),
        tooltip=['날짜', '불량 유형', '수']
    ).properties(
        height=400,
        title='일자별 불량 건수 추이'
    )
    
    st.altair_chart(line_chart, use_container_width=True)
    
    st.divider()
    
    st.subheader("선택한 날짜의 불량 유형별 비율")
    
    # Stacked bar chart for daily breakdown
    day_data_for_chart = filtered_df[filtered_df['날짜'] == selected_date].iloc[0]
    breakdown_data = pd.DataFrame({
        '지표': ['PASS', '가성불량', '진성불량'],
        '수': [day_data_for_chart['PASS'], day_data_for_chart['가성불량'], day_data_for_chart['진성불량']]
    })
    
    bar_chart = alt.Chart(breakdown_data).mark_bar().encode(
        x=alt.X('지표', title='지표', sort=['PASS', '가성불량', '진성불량']),
        y=alt.Y('수', title='수'),
        color=alt.Color('지표', legend=alt.Legend(title="지표")),
        tooltip=['지표', '수']
    ).properties(
        height=400
    )
    st.altair_chart(bar_chart, use_container_width=True)
    
if __name__ == "__main__":
    create_dashboard()
