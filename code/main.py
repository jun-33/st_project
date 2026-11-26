
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="ESS 날짜별 충전량과 방전량",
    page_icon="🔋",
    layout="wide"
)

st.title("🔋 ESS 날짜별 충전량과 방전량")


# =========================================================
# 데이터 파일 경로
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

# main.py가 code 폴더 안에 있을 때와
# 저장소 최상위 폴더에 있을 때 모두 대응
DATA_DIR = BASE_DIR / "data"

if not DATA_DIR.exists():
    DATA_DIR = BASE_DIR.parent / "data"

FILE_2024 = DATA_DIR / "지역별 에너지저장장치(ESS) 일단위 충전 및 방전 실적_2024.csv"
FILE_2025 = DATA_DIR / "지역별 에너지저장장치(ESS) 일단위 충전 및 방전 실적_2025.csv"


# =========================================================
# 데이터 불러오기
# =========================================================

@st.cache_data
def load_data():

    df_2024 = pd.read_csv(FILE_2024, encoding="utf-8-sig")
    df_2025 = pd.read_csv(FILE_2025, encoding="utf-8-sig")

    df = pd.concat(
        [df_2024, df_2025],
        ignore_index=True
    )

    return df


if not FILE_2024.exists() or not FILE_2025.exists():
    st.error("2024년 또는 2025년 CSV 파일을 찾을 수 없습니다.")
    st.stop()

try:
    df = load_data()

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()


# =========================================================
# 날짜, 충전량, 방전량 열 찾기
# =========================================================

date_col = next(
    (c for c in df.columns
     if "날짜" in c or "일자" in c or "date" in c.lower()),
    None
)

charge_col = next(
    (c for c in df.columns if "충전" in c),
    None
)

discharge_col = next(
    (c for c in df.columns if "방전" in c),
    None
)

if date_col is None or charge_col is None or discharge_col is None:
    st.error("날짜, 충전량, 방전량 열을 찾을 수 없습니다.")
    st.write("CSV 열 이름:", df.columns.tolist())
    st.stop()


# =========================================================
# 데이터 전처리
# =========================================================

df[date_col] = pd.to_datetime(
    df[date_col],
    errors="coerce"
)

df[charge_col] = pd.to_numeric(
    df[charge_col],
    errors="coerce"
)

df[discharge_col] = pd.to_numeric(
    df[discharge_col],
    errors="coerce"
)

df = df.dropna(subset=[date_col])

# 날짜별 충전량과 방전량 합계
# 지역별 데이터가 있다면 전체 지역의 합계로 계산
daily = (
    df.groupby(date_col)
    .agg({
        charge_col: lambda x: x.sum(min_count=1),
        discharge_col: lambda x: x.sum(min_count=1)
    })
    .reset_index()
)

daily = daily.sort_values(date_col)


# =========================================================
# 날짜별 충전량과 방전량 그래프
# =========================================================

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=daily[date_col],
        y=daily[charge_col],
        mode="lines",
        name="충전량",
        line=dict(width=2),
        connectgaps=False
    )
)

fig.add_trace(
    go.Scatter(
        x=daily[date_col],
        y=daily[discharge_col],
        mode="lines",
        name="방전량",
        line=dict(width=2),
        connectgaps=False
    )
)

fig.update_layout(
    title="2024~2025년 ESS 날짜별 충전량과 방전량",
    xaxis_title="날짜",
    yaxis_title="전력량",
    hovermode="x unified",
    legend_title="구분",
    template="plotly_white"
)

st.plotly_chart(
    fig,
    use_container_width=True
)
