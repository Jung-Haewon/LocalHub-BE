import sqlite3
from chatbot import keyword_parser
from chatbot import retriever
from chatbot import prompt
from chatbot.chatbot import Chatbot

retriever = retriever.Retriever("localhub.db") 

bot = Chatbot("localhub.db")

import sqlite3

conn = sqlite3.connect("localhub.db")
cur = conn.cursor()

cur.execute("PRAGMA table_info(locations)")
for row in cur.fetchall():
    print(row)

while True:

    q = input("> ")

    print()

    print(bot.chat(q))

    print()



