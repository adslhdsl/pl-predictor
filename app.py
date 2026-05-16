import streamlit as st
import requests
import openpyxl
from pathlib import Path

TEAM_NAME_KO = {
    'Arsenal': '아스날',
    'Manchester City': '맨시티',
    'Manchester United': '맨유',
    'Aston Villa': '빌라',
    'Liverpool': '리버풀',
    'Bournemouth': '본머스',
    'AFC Bournemouth': '본머스',
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

def load_predictions():
    path = Path(__file__).parent / 'predictions.xlsx'
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    names = [h for h in rows[0] if h]
    predictions = {name: [] for name in names}
    for row in rows[1:]:
        for idx, name in enumerate(names):
            predictions[name].append(row[idx + 1])
    return predictions

PREDICTIONS = load_predictions()


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



def render_html_table(actual, predictions, scores):
    names = list(predictions.keys())
    header_cells = '<th>순위</th><th>실제</th>' + ''.join(f'<th>{n}</th>' for n in names)

    rows_html = ''
    for i in range(20):
        rank = i + 1
        act = actual[i]
        bg = '#f9f9f9' if i % 2 == 0 else '#ffffff'
        row = f'<td style="background:{bg};text-align:center">{rank}</td>'
        row += f'<td style="background:{bg}">{act}</td>'
        for name in names:
            pred = predictions[name][i]
            color = '#90EE90' if pred == act else '#FFB6B6'
            row += f'<td style="background:{color}">{pred}</td>'
        rows_html += f'<tr>{row}</tr>'

    return f"""
    <style>
      .pl-table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
      .pl-table {{ border-collapse: collapse; width: 100%; min-width: 320px; font-size: 11px; }}
      .pl-table th {{ background: #1E3A5F; color: white; padding: 8px 6px; text-align: center; position: sticky; top: 0; }}
      .pl-table td {{ padding: 6px 8px; border-bottom: 1px solid #ddd; white-space: nowrap; }}
    </style>
    <div class="pl-table-wrap">
      <table class="pl-table">
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """


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
cards = ''
for name, score in scores.items():
    medal = '🏆 ' if name == winner else ''
    cards += f'''
    <div style="flex:1;text-align:center;padding:8px;background:#f0f2f6;border-radius:8px;margin:0 4px">
      <div style="font-size:12px;color:#555">{medal}{name}</div>
      <div style="font-size:16px;font-weight:bold">{score}개 적중</div>
    </div>'''
st.markdown(f'<div style="display:flex;margin-bottom:12px">{cards}</div>', unsafe_allow_html=True)

st.divider()

# 순위 표
st.markdown(render_html_table(actual, PREDICTIONS, scores), unsafe_allow_html=True)
