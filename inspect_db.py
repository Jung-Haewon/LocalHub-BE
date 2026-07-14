import sqlite3
from chatbot import keyword_parser
from chatbot import retriever
from chatbot import prompt
from chatbot.chatbot import Chatbot

retriever = retriever.Retriever("localhub.db") 

bot = Chatbot("localhub.db")

while True:

    q = input("> ")

    print()

    print(bot.chat(q))

    print()



