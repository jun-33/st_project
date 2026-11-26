
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
    st.error("CSV 파일을 찾을 수 없습니다.")
    st.stop()

try:
    df = load_data()

except Exception as e:
    st.error(f"데이터 불러오기 오류: {e}")
    st.stop()


# =========================================================
# 실제 CSV 열 이름 사용
# =========================================================

date_col = "거래일"
year_col = "연도"
charge_col = "충전량 합계(kWh)"
discharge_col = "방전량 합계(kWh)"

required_cols = [
    date_col,
    year_col,
    charge_col,
    discharge_col
]

if not all(col in df.columns for col in required_cols):
    st.error("CSV 열 이름이 예상과 다릅니다.")
    st.write(df.columns.tolist())
    st.stop()


# =========================================================
# 날짜 데이터 처리
# =========================================================

# 거래일을 문자열로 변환
date_text = df[date_col].astype(str).str.strip()

# 한글 날짜 형식 정리
normalized_date = (
    date_text
    .str.replace("년", "-", regex=False)
    .str.replace("월", "-", regex=False)
    .str.replace("일", "", regex=False)
    .str.strip()
)

# 거래일 자체에 연도가 포함된 경우
direct_date = pd.to_datetime(
    normalized_date,
    errors="coerce"
)

# 연도가 따로 있는 경우
combined_date = pd.to_datetime(
    df[year_col].astype(str) + "-" + normalized_date,
    errors="coerce"
)

# 거래일에 연도가 없거나 날짜 변환에 실패한 경우
df["날짜"] = direct_date

invalid = (
    df["날짜"].isna()
    | (df["날짜"].dt.year != pd.to_numeric(df[year_col], errors="coerce"))
)

df.loc[invalid, "날짜"] = combined_date[invalid]


# =========================================================
# 충전량과 방전량 숫자 변환
# =========================================================

df[charge_col] = pd.to_numeric(
    df[charge_col],
    errors="coerce"
)

df[discharge_col] = pd.to_numeric(
    df[discharge_col],
    errors="coerce"
)

df = df.dropna(subset=["날짜"])


# =========================================================
# 날짜별 전체 지역 합계 계산
# =========================================================

daily = (
    df.groupby("날짜")
    .agg({
        charge_col: lambda x: x.sum(min_count=1),
        discharge_col: lambda x: x.sum(min_count=1)
    })
    .reset_index()
)

daily = daily.sort_values("날짜")


# =========================================================
# 날짜별 충전량과 방전량 그래프
# =========================================================

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=daily["날짜"],
        y=daily[charge_col],
        mode="lines",
        name="충전량",
        connectgaps=False
    )
)

fig.add_trace(
    go.Scatter(
        x=daily["날짜"],
        y=daily[discharge_col],
        mode="lines",
        name="방전량",
        connectgaps=False
    )
)

fig.update_layout(
    title="2024~2025년 ESS 날짜별 충전량과 방전량",
    xaxis_title="날짜",
    yaxis_title="전력량 (kWh)",
    hovermode="x unified",
    template="plotly_white",
    legend_title="구분"
)

st.plotly_chart(
    fig,
    use_container_width=True
)
