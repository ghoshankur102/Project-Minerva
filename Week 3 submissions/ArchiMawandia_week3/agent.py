from dotenv import load_dotenv
load_dotenv(override=True)

from engine import run_local_tests, extract_problem

from langchain_google_genai import ChatGoogleGenerativeAI
# Step 1: Define tools and model

from langchain.tools import tool
from langchain.chat_models import init_chat_model


# model = init_chat_model(
#     "gemini-1.5-flash",
#     model_provider="google_genai",
#     temperature=0
# )

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0,
    max_retries=6) # to pause and retry when limit is hit

# Define tools
@tool
def test_solution(code: str) -> str:
    """
    Compiles and runs the provided C++ code string against the problem's sample test cases.
    Args:
        code: The complete raw C++ source code string to test.
    Returns:
        The string 'success' if all samples pass, or a detailed compilation/runtime error log.
    """
    result = run_local_tests(code, current_test_cases)
    if result["success"]:
        return "success"
    else:
        return result["error_log"]




# Augment the LLM with tools
tools = [test_solution]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)


# Step 2: Define state

from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
import operator


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


# Step 3: Define model node
from langchain.messages import SystemMessage


def llm_call(state: MessagesState):
    """LLM decides whether to generate code, call compiler or end"""

    system_instruction = (
        "You are an elite competitive programmer. Your task is to write a flawless, optimized C++ solution "
        "for the given problem description. Treat standard input/output bounds carefully.\n\n"
        "CRITICAL RULE: You are forbidden from giving a final text answer or stopping until you have successfully "
        "called the `test_solution` tool at least once to verify your code. "
        "If the tool returns errors, debug your logic, fix the code boundaries, and call the tool again."
    )

    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content=system_instruction
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }


# Step 4: Define tool node

from langchain.messages import ToolMessage


def tool_node(state: MessagesState):
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
    return {"messages": result}

# Step 5: Define logic to determine whether to end

from typing import Literal
from langgraph.graph import StateGraph, START, END


# Conditional edge function to route to the tool node or end based upon whether the LLM made a tool call
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """Decide if we should loop back to fix error or stop if we secceed or hit our limit"""

    messages = state["messages"]
    last_message = messages[-1]

    #  additional safety so that agent does not get stuck in an infinite loop in cases where the llm gets completely stuck on an edge case
    if state.get("llm_calls", 0) >= 4:
        print("skill issue :(")
        return END

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_node"

    # Otherwise, we stop (reply to the user)
    return END

# Step 6: Build agent

# Build workflow
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
agent_builder.add_edge("tool_node", "llm_call")

# Compile the agent
agent = agent_builder.compile()


# modifying to save evaluation report
# Invoke
from langchain.messages import HumanMessage
import os
import csv
import time

if __name__ == "__main__": # so that this doesnt run if this file is imorted somewhere

    result_file = "evaluation_report.csv"
    input_file = "Test Questions - Sheet1.csv"

    # loading the test questions
    test_problems = []
    with open(input_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_problems.append((row["Problems"].strip(), int(row["ratings"].strip())))

    # read what is already there in the results csv
    solved_questions = set()
    if os.path.exists(result_file):
        with open(result_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url_key = row.get("problem URL") or row.get("Problems")
                if url_key:
                    solved_questions.add(url_key.strip())

    # writing into the result file
    if not os.path.exists(result_file):
        with open(result_file, mode="w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["problem URL", "rating", "status", "total llm calls"])

    remaining_problems = [(url, diff) for url, diff in test_problems if url.strip() not in solved_questions]


    idx = 1
    while idx <= len(remaining_problems):
        url, difficulty = remaining_problems[idx - 1]

        # take any test question
        test_url = url
        try:
            ps, test_cases = extract_problem(test_url)
        except Exception as e:
            print(e)
            idx += 1
            continue

        # store test cases in a global variable for the tool call function
        global current_test_cases
        current_test_cases = test_cases

        user_query = f"Please solve this Codeforces challenge.\n\nProblem Statement:\n{ps}"

        try:
            output_state = agent.invoke({
                "messages": [HumanMessage(content=user_query)],
                "llm_calls": 0
            })

            for m in output_state["messages"]:
                m.pretty_print()

            total_attempts = output_state.get("llm_calls", 0)

            if total_attempts >= 4:
                status = "failed (max limit reached)"

            else:
                status = "success"

            # Instantly save the row after the problem finishes running
            with open(result_file, mode="a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([url, difficulty, status, total_attempts])

            idx += 1
            time.sleep(30)

        except Exception as e:
            # If the error is an API limit (429 or resource full)
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print("Hit API limit! Waiting 50 seconds before trying this question again...")
                time.sleep(50)
                # Notice we do NOT add 1 to idx here, so the loop repeats this exact question!

            else:
                # If it's a regular error (like a scraping or code error), log it and move on
                print(f"Error on this problem: {e}")
                with open(result_file, mode="a", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerow([url, difficulty, "failed_error", 0])

                idx += 1  # Move to the next question
                time.sleep(30)



