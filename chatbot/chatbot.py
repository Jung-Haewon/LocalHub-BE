from chatbot import keyword_parser
from chatbot import retriever
from chatbot.prompt import build_prompt
from chatbot.llm import ask_llm


class Chatbot:

    def __init__(self, db_path):

        self.retriever = retriever.Retriever(db_path)

    def chat(self, question, history=None):

        parsed = keyword_parser.parse_question(question)

        rows = self.retriever.retrieve(parsed)

        prompt = build_prompt(question, rows)

        answer = ask_llm(prompt)

        return answer