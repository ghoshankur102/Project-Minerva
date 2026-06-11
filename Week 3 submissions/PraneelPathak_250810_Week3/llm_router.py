import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


# -----------------------
# API KEYS
# -----------------------

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# -----------------------
# MODELS
# -----------------------

# analyzer_llm = ChatGroq(
#     api_key=GROQ_API_KEY,
#     model="llama-3.1-8b-instant",
#     temperature=0
# )
analyzer_llm = ChatGoogleGenerativeAI(
    api_key=GEMINI_API_KEY,
    model="gemini-2.5-flash",
    temperature=0
)

planner_llm = ChatGoogleGenerativeAI(
    api_key=GEMINI_API_KEY,
    model="gemini-2.5-flash",
    temperature=0
)

generator_llm = ChatGoogleGenerativeAI(
    api_key=GEMINI_API_KEY,
    model="gemini-2.5-flash",
    temperature=0
)

critic_llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0
)

repair_llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0
)

# -----------------------
# SAFE CALL
# -----------------------

def safe_invoke(llm, messages):
    try:
        return llm.invoke(messages).content
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        raise


# -----------------------
# ROUTING LOGIC
# -----------------------

def call_analyzer(messages):
    return safe_invoke(analyzer_llm, messages)

def call_planner(messages):
    return safe_invoke(planner_llm, messages)

def call_generator(messages):
    return safe_invoke(generator_llm, messages)

def call_critic(messages):
    return safe_invoke(critic_llm, messages)

def call_repair(messages):
    return safe_invoke(repair_llm, messages)