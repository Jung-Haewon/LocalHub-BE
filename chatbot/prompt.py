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
종류 : {CONTENT_TYPE_NAMES.get(row["content_type_id"], "기타")}

"""

    prompt = f"""
당신은 LocalHub의 관광 안내 챗봇 서울이입니다.

아래 정보를 참고해 질문에 답하세요.


- 여러 장소를 추천할 경우 각 장소는 반드시 새로운 줄에서 시작한다.
- 번호 목록을 사용할 경우 다음 형식을 따른다.

예시)

서울의 등록된 호텔 목록입니다.

1. 호텔 안테룸 서울
   주소 : 서울특별시 강남구 도산대로 153 (신사동)

2. 라마다호텔 앤 스위트 서울남대문
   주소 : 서울특별시 중구 칠패로 27

3. 조선 팰리스 서울 강남
   주소 : 서울특별시 강남구 테헤란로 231

- 절대로 여러 장소를 한 줄에 이어 쓰지 않는다.
- 장소 하나가 끝나면 빈 줄을 하나 넣는다.

{context}

사용자 질문

{question}

"""

    return prompt