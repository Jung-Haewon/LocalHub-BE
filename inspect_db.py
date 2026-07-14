import sqlite3
from chatbot import keyword_parser
from chatbot import retriever
from chatbot import prompt
from chatbot.chatbot import Chatbot

retriever = retriever.Retriever("localhub.db") 

query = "선릉 주변 모텔 어딨는지 알려줘링 링딩동 동귀리리"

parsed = keyword_parser.parse_question(query)


results = retriever.retrieve(parsed)
for result in results:
    print(f"Result: {result}")

prompt = prompt.build_prompt(query, results)

bot = Chatbot("localhub.db")

while True:

    q = input("> ")

    print()

    print(bot.chat(q))

    print()



