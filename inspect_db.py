import sqlite3
from chatbot import keyword_parser
from chatbot import retriever

retriever = retriever.Retriever("localhub.db") 

query = "선릉 주변 모텔 어딨는지 알려줘링 링딩동 동귀리리"

parsed = keyword_parser.parse_question(query)


results = retriever.retrieve(parsed)
for result in results:
    print(f"Result: {result}")

conn = sqlite3.connect("localhub.db")
cur = conn.cursor()

cur.execute("SELECT addr1 FROM locations;")
rows = cur.fetchall()

conn.close()

