
import streamlit as st
import pandas as pd
import plotly.express as px


# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="ESS 월별 충전량과 방전량",
    page_icon="🔋",
    layout="wide"
)

st.title("🔋 ESS의 월별 충전량과 방전량은 계절에 따라 어떤 차이를 보일까?")
st.write(
    "2024년과 2025년 ESS 데이터를 이용해 "
    "월별 충전량과 방전량을 계절별로 비교합니다."
)


# =========================================================
# 데이터 불러오기
# =========================================================

URL_2024 = "지역별 에너지저장장치(ESS) 일단위 충전 및 방전 실적_2024.csv"
URL_2025 = "지역별 에너지저장장치(ESS) 일단위 충전 및 방전 실적_2025.csv"

@st.cache_data
def load_data():
    df_2024 = pd.read_csv(URL_2024, encoding="utf-8-sig")
    df_2025 = pd.read_csv(URL_2025, encoding="utf-8-sig")

    df = pd.concat([df_2024, df_2025], ignore_index=True)

    return df


try:
    df = load_data()

except Exception as e:
    st.error("데이터 파일을 불러오지 못했습니다.")
    st.info("CSV 파일을 main.py와 같은 폴더에 넣어 주세요.")
    st.stop()


# =========================================================
# 데이터 전처리
# =========================================================

# 날짜 열 찾기
date_col = next(
    (c for c in df.columns if "날짜" in c or "일자" in c or "date" in c.lower()),
    None
)

# 충전량과 방전량 열 찾기
charge_col = next(
    (c for c in df.columns if "충전" in c),
    None
)

discharge_col = next(
    (c for c in df.columns if "방전" in c),
    None
)

if not all([date_col, charge_col, discharge_col]):
    st.error("날짜, 충전량, 방전량 열을 찾을 수 없습니다.")
    st.write("현재 CSV 열 이름:", df.columns.tolist())
    st.stop()

df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

df[charge_col] = pd.to_numeric(df[charge_col], errors="coerce")
df[discharge_col] = pd.to_numeric(df[discharge_col], errors="coerce")

df = df.dropna(subset=[date_col])

df["연도"] = df[date_col].dt.year
df["월"] = df[date_col].dt.month

# 계절 구분
season_map = {
    12: "겨울",
    1: "겨울",
    2: "겨울",
    3: "봄",
    4: "봄",
    5: "봄",
    6: "여름",
    7: "여름",
    8: "여름",
    9: "가을",
    10: "가을",
    11: "가을"
}

df["계절"] = df["월"].map(season_map)

# 월별 충전량과 방전량 합계
monthly = (
    df.groupby(["연도", "월", "계절"], as_index=False)
    .agg({
        charge_col: "sum",
        discharge_col: "sum"
    })
)

monthly = monthly.sort_values(["연도", "월"])

# 계절 순서
season_order = ["봄", "여름", "가을", "겨울"]


# =========================================================
# 월별 충전량과 방전량
# =========================================================

st.header("1. 월별 충전량과 방전량")

monthly["연월"] = (
    monthly["연도"].astype(str)
    + "-"
    + monthly["월"].astype(str).str.zfill(2)
)

monthly_long = monthly.melt(
    id_vars=["연도", "월", "계절", "연월"],
    value_vars=[charge_col, discharge_col],
    var_name="구분",
    value_name="전력량"
)

fig1 = px.bar(
    monthly_long,
    x="연월",
    y="전력량",
    color="구분",
    barmode="group",
    title="월별 ESS 충전량과 방전량",
    labels={
        "연월": "연월",
        "전력량": "전력량",
        "구분": "구분"
    },
    hover_data=["계절"]
)

st.plotly_chart(fig1, use_container_width=True)


# =========================================================
# 계절별 월평균 충전량과 방전량
# =========================================================

st.header("2. 계절별 충전량과 방전량 비교")

# 연도별 월 합계를 바탕으로 계절별 월평균 계산
seasonal = (
    monthly.groupby("계절", as_index=False)
    .agg({
        charge_col: "mean",
        discharge_col: "mean"
    })
)

seasonal_long = seasonal.melt(
    id_vars="계절",
    value_vars=[charge_col, discharge_col],
    var_name="구분",
    value_name="월평균 전력량"
)

fig2 = px.bar(
    seasonal_long,
    x="계절",
    y="월평균 전력량",
    color="구분",
    barmode="group",
    category_orders={"계절": season_order},
    title="계절별 월평균 ESS 충전량과 방전량",
    labels={
        "계절": "계절",
        "월평균 전력량": "월평균 전력량",
        "구분": "구분"
    }
)

st.plotly_chart(fig2, use_container_width=True)


# =========================================================
# 계절별 충전량과 방전량 표
# =========================================================

st.header("3. 계절별 월평균 전력량")

result = seasonal.copy()

result = result.rename(columns={
    charge_col: "월평균 충전량",
    discharge_col: "월평균 방전량"
})

result["계절"] = pd.Categorical(
    result["계절"],
    categories=season_order,
    ordered=True
)

result = result.sort_values("계절")

st.dataframe(
    result,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 분석 결과
# =========================================================

st.header("4. 분석 결과")

max_charge = seasonal.loc[seasonal[charge_col].idxmax()]
max_discharge = seasonal.loc[seasonal[discharge_col].idxmax()]

st.write(
    f"**월평균 충전량이 가장 많은 계절:** "
    f"{max_charge['계절']}"
)

st.write(
    f"**월평균 방전량이 가장 많은 계절:** "
    f"{max_discharge['계절']}"
)

