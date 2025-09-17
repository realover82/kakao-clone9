import streamlit as st
import pandas as pd
import altair as alt
import io
import re

def show_dashboard(df):
    """
    업로드된 데이터프레임을 기반으로 대시보드를 생성
    """
    try:
        # 데이터프레임 전치 및 정리
        df_transposed = df.set_index('지표').T
        df_transposed.index.name = '날짜'
        df_transposed = df_transposed.reset_index()
        
        # 숫자형 데이터로 변환 (N/A 값 포함)
        for col in ['총 테스트 수', 'PASS', '가성불량', '진성불량', 'FAIL']:
            df_transposed[col] = pd.to_numeric(df_transposed[col], errors='coerce')

        # 필터: 날짜 선택
        dates = sorted(df_transposed['날짜'].unique())
        selected_date = st.selectbox("날짜를 선택하세요:", dates, index=len(dates) - 1)
        
        day_data = df_transposed[df_transposed['날짜'] == selected_date].iloc[0]
        
        # 지표 출력
        st.subheader(f"날짜: {selected_date} 요약")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        col1.metric("총 테스트 수", f"{day_data['총 테스트 수']:,}")
        col2.metric("PASS", f"{day_data['PASS']:,}")
        col3.metric("FAIL", f"{day_data['FAIL']:,}")
        
        # 이전 날짜와 비교하여 증감량 계산
        delta_false = None
        delta_true = None
        if len(dates) > 1:
            prev_date = dates[dates.index(selected_date) - 1]
            prev_data = df_transposed[df_transposed['날짜'] == prev_date].iloc[0]
            delta_false = day_data['가성불량'] - prev_data['가성불량']
            delta_true = day_data['진성불량'] - prev_data['진성불량']
        
        col4.metric("가성불량", f"{day_data['가성불량']:,}", delta=f"{int(delta_false)}" if delta_false is not None else None)
        col5.metric("진성불량", f"{day_data['진성불량']:,}", delta=f"{int(delta_true)}" if delta_true is not None else None)

        # 차트: 일자별 불량 추이
        st.divider()
        st.subheader("일자별 불량 추이")
        chart_data = df_transposed.melt(id_vars=['날짜'], value_vars=['가성불량', '진성불량', 'FAIL'], var_name='불량 유형', value_name='수')
        
        line_chart = alt.Chart(chart_data).mark_line(point=True).encode(
            x=alt.X('날짜', sort=dates),
            y=alt.Y('수'),
            color='불량 유형',
            tooltip=['날짜', '불량 유형', '수']
        ).properties(height=400, title='일자별 불량 건수 추이')
        
        st.altair_chart(line_chart, use_container_width=True)
            
    except Exception as e:
        st.error(f"대시보드를 생성하는 중 오류가 발생했습니다: {e}")
        st.dataframe(df)

def read_multi_table_csv(uploaded_file):
    """
    여러 테이블이 포함된 CSV 파일을 읽어 하나의 DataFrame으로 통합
    """
    try:
        file_content = uploaded_file.getvalue().decode('cp949')
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        file_content = uploaded_file.getvalue().decode('utf-8')

    # '지표'로 시작하는 행을 기준으로 파일을 여러 부분으로 분리
    parts = re.split(r'\n지표,', file_content.strip())
    
    dfs = []
    for i, part in enumerate(parts):
        # 첫 번째 부분은 이미 '지표,'로 시작하므로 그대로 사용
        if i > 0:
            part = '지표,' + part
        
        try:
            df = pd.read_csv(io.StringIO(part))
            
            # 컬럼 이름의 앞뒤 공백 제거
            df.columns = df.columns.str.strip()
            
            # DataFrame 전치 (Transpose)
            df_transposed = df.set_index('지표').T
            df_transposed.index.name = '날짜'
            df_transposed = df_transposed.reset_index()
            
            # '구분' 컬럼 추가 (100.00, 101.00 등으로 가정)
            df_transposed['구분'] = f"{100 + i:.2f}"
            
            # 모든 컬럼을 숫자형으로 변환
            for col in ['총 테스트 수', 'PASS', '가성불량', '진성불량', 'FAIL']:
                df_transposed[col] = pd.to_numeric(df_transposed[col], errors='coerce')
                
            dfs.append(df_transposed)
        except Exception as e:
            st.warning(f"테이블 파싱 중 오류 발생: {e}. 해당 테이블은 건너뜁니다.")
    
    if not dfs:
        st.error("파일에서 유효한 데이터를 찾을 수 없습니다. 파일 형식을 확인해주세요.")
        return None
        
    return pd.concat(dfs, ignore_index=True)


def main():
    st.set_page_config(
        page_title="가성불량 현황 대시보드",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="auto"
    )

    st.title("CSV 파일 업로드 대시보드")
    st.write("대시보드를 생성하려면 아래에 CSV 파일을 업로드하세요.")
    
    uploaded_file = st.file_uploader("파일 업로드", type=["csv"])
    
    if uploaded_file is not None:
        st.session_state['df'] = read_multi_table_csv(uploaded_file)
        
        if st.session_state['df'] is not None:
            st.write("### 업로드된 데이터 미리보기")
            st.dataframe(st.session_state['df'].head())
            
            if st.button("분석 시작"):
                st.session_state['show_dashboard'] = True

            if 'show_dashboard' in st.session_state and st.session_state['show_dashboard']:
                show_dashboard(st.session_state['df'])

if __name__ == "__main__":
    if 'show_dashboard' not in st.session_state:
        st.session_state['show_dashboard'] = False
        st.session_state['df'] = None
    main()
