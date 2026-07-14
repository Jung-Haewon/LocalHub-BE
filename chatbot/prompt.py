CONTENT_TYPE_NAMES = {
    "12": "관광지",
    "14": "문화시설",
    "15": "축제/공연행사",
    "25": "여행코스",
    "28": "레포츠",
    "32": "숙박",
    "38": "쇼핑",
}


def build_prompt(question, rows):

    context = ""

    for i, row in enumerate(rows, start=1):

        context += f"""
{i}.
이름 : {row["title"]}
주소 : {row["addr1"]}
전화 : {row["tel"] or "정보 없음"}
종류 : {CONTENT_TYPE_NAMES.get(row["contenttypeid"], "기타")}

"""

    prompt = f"""
당신은 LocalHub의 관광 안내 챗봇입니다.

아래 정보만 이용해서 질문에 답하세요.

{context}

사용자 질문

{question}

규칙

- 없는 내용은 추측하지 않는다.
- 검색 결과가 없으면 찾을 수 없다고 말한다.
- 답변은 친절하게 한다.
"""

    return prompt