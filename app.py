import streamlit as st
import requests
import pandas as pd

TEAM_NAME_KO = {
    'Arsenal': '아스날',
    'Manchester City': '맨시티',
    'Manchester United': '맨유',
    'Aston Villa': '빌라',
    'Liverpool': '리버풀',
    'Bournemouth': '본머스',
    'Brighton and Hove Albion': '브라이튼',
    'Brighton & Hove Albion': '브라이튼',
    'Brentford': '브랜트포드',
    'Chelsea': '첼시',
    'Everton': '에버튼',
    'Fulham': '풀럼',
    'Sunderland': '선더랜드',
    'Newcastle United': '뉴캐슬',
    'Leeds United': '리즈',
    'Crystal Palace': '크리스탈팰리스',
    'Nottingham Forest': '노팅엄',
    'Tottenham Hotspur': '토트넘',
    'West Ham United': '웨스트햄',
    'Burnley': '번리',
    'Wolverhampton Wanderers': '울버햄튼',
}

PREDICTIONS = {
    '성진': ['리버풀','맨시티','첼시','아스날','뉴캐슬','토트넘','맨유','브라이튼','빌라','풀럼',
             '노팅엄','에버튼','크리스탈팰리스','웨스트햄','울버햄튼','본머스','브랜트포드','선더랜드','리즈','번리'],
    '원기': ['아스날','리버풀','첼시','맨시티','빌라','뉴캐슬','맨유','크리스탈팰리스','브라이튼','풀럼',
             '노팅엄','본머스','토트넘','에버튼','웨스트햄','울버햄튼','리즈','브랜트포드','번리','선더랜드'],
    '규성': ['리버풀','맨시티','아스날','첼시','뉴캐슬','빌라','브랜트포드','브라이튼','번리','본머스',
             '맨유','노팅엄','크리스탈팰리스','에버튼','토트넘','선더랜드','풀럼','울버햄튼','웨스트햄','리즈'],
}


@st.cache_data(ttl=3600)
def fetch_actual():
    url = "https://site.api.espn.com/apis/v2/sports/soccer/eng.1/standings"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    standings = []
    for group in data.get("children", []):
        for entry in group.get("standings", {}).get("entries", []):
            name_en = entry["team"]["displayName"]
            name_ko = TEAM_NAME_KO.get(name_en, name_en)
            pts = next(s["value"] for s in entry["stats"] if s["name"] == "points")
            standings.append((pts, name_ko))

    standings.sort(key=lambda x: -x[0])
    return [team for _, team in standings[:20]]


def compare(actual, predictions):
    scores = {}
    for name, pred in predictions.items():
        scores[name] = sum(1 for i in range(20) if pred[i] == actual[i])
    return scores


def build_dataframe(actual, predictions, scores):
    rows = []
    for i in range(20):
        row = {'순위': i + 1, '실제': actual[i]}
        for name, pred in predictions.items():
            row[name] = pred[i]
        rows.append(row)
    return pd.DataFrame(rows)


def highlight(df, actual, predictions):
    style = pd.DataFrame('', index=df.index, columns=df.columns)
    for i in range(20):
        for name in predictions:
            if predictions[name][i] == actual[i]:
                style.at[i, name] = 'background-color: #90EE90; font-weight: bold'
            else:
                style.at[i, name] = 'background-color: #FFB6B6'
    return style


# ── UI ────────────────────────────────────────────────────────
st.set_page_config(page_title='PL 예측 결과', page_icon='⚽', layout='centered')
st.title('⚽ 2025-26 프리미어리그 예측 결과')

if st.button('🔄 현재 순위 불러오기', type='primary'):
    st.cache_data.clear()

with st.spinner('순위 불러오는 중...'):
    try:
        actual = fetch_actual()
    except Exception as e:
        st.error(f'순위를 불러오지 못했습니다: {e}')
        st.stop()

scores = compare(actual, PREDICTIONS)
winner = max(scores, key=scores.get)

# 점수 카드
cols = st.columns(len(PREDICTIONS))
for col, (name, score) in zip(cols, scores.items()):
    with col:
        medal = '🏆' if name == winner else ''
        st.metric(label=f'{medal} {name}', value=f'{score}개 적중')

st.divider()

# 순위 표
df = build_dataframe(actual, PREDICTIONS, scores)
df_indexed = df.set_index('순위')
styled = df_indexed.style.apply(
    lambda _: highlight(df, actual, PREDICTIONS).drop(columns=['순위', '실제']).values,
    axis=None
)
st.dataframe(styled, use_container_width=True, height=720)
