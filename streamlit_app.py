import streamlit as st
import pandas as pd
import altair as alt
import io

# set_page_config는 스크립트의 가장 상단에서 한 번만 호출해야 합니다.
st.set_page_config(
    page_title="가성불량 현황 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"
)

def data_prep(data):
    # 이 함수는 데이터 전처리 로직을 담고 있습니다.
    # 업로드되는 CSV 파일의 헤더와 데이터 유형에 따라 코드를 조정해야 할 수 있습니다.
    # 현재 코드는 GA4 샘플 데이터의 열 이름을 기준으로 작성되었습니다.
    
    # 예시 코드: 데이터 전처리
    data = data.dropna()
    data['user_pseudo_id'] = data['user_pseudo_id'].astype(str)
    
    # '(not set)' 값 처리
    data['item_id'] = pd.to_numeric(data['item_id'], errors='coerce').fillna(0).astype(int)
    
    # 날짜 데이터 유형 변환
    data['event_date'] = pd.to_datetime(data['event_date'], format="%Y%m%d")
    data['event_timestamp'] = pd.to_datetime(data['event_timestamp'], unit='us')
    
    return data

def show_dashboard(df):
    st.title("가성불량 현황 대시보드")
    st.caption("업로드된 CSV 파일을 기반으로 한 데이터 분석 결과")
    
    # 여기에 제공된 '가성불량 현황 데이터'를 기반으로 한 대시보드 로직을 추가합니다.
    # 사용자가 업로드하는 파일의 컬럼명이 "지표", "250908", ... 등이라고 가정합니다.
    
    # 데이터프레임 전치 및 정리
    df = df.set_index('지표').T
    df.index.name = '날짜'
    df = df.reset_index()
    
    for col in ['총 테스트 수', 'PASS', '가성불량', '진성불량', 'FAIL']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 필터: 날짜 선택
    dates = sorted(df['날짜'].unique())
    selected_date = st.selectbox("날짜를 선택하세요:", dates, index=len(dates) - 1)
    
    day_data = df[df['날짜'] == selected_date].iloc[0]
    
    # 지표 출력
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("총 테스트 수", f"{day_data['총 테스트 수']:,}")
    col2.metric("PASS", f"{day_data['PASS']:,}")
    col3.metric("FAIL", f"{day_data['FAIL']:,}")
    col4.metric("가성불량", f"{day_data['가성불량']:,}")
    col5.metric("진성불량", f"{day_data['진성불량']:,}")

    # 차트
    st.divider()
    st.subheader("일자별 불량 추이")
    chart_data = df.melt(id_vars=['날짜'], value_vars=['가성불량', '진성불량', 'FAIL'], var_name='불량 유형', value_name='수')
    
    line_chart = alt.Chart(chart_data).mark_line(point=True).encode(
        x=alt.X('날짜', sort=dates),
        y=alt.Y('수'),
        color='불량 유형',
        tooltip=['날짜', '불량 유형', '수']
    ).properties(height=400)
    
    st.altair_chart(line_chart, use_container_width=True)


def main():
    st.title("CSV 파일 업로드 대시보드")
    st.write("대시보드를 생성하려면 아래에 CSV 파일을 업로드하세요.")
    
    uploaded_file = st.file_uploader("파일 업로드", type=["csv"])
    
    if uploaded_file is not None:
        try:
            # 업로드된 파일을 DataFrame으로 읽기
            # pandas.read_csv는 file-like object를 직접 처리할 수 있습니다.
            df = pd.read_csv(uploaded_file)
            
            st.write("### 업로드된 데이터 미리보기")
            st.dataframe(df.head())
            
            # 여기서 show_dashboard 함수를 호출하여 대시보드를 표시합니다.
            show_dashboard(df)
            
        except Exception as e:
            st.error(f"파일을 처리하는 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
