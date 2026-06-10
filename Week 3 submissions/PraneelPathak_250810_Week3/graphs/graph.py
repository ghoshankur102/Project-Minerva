from langgraph.graph import StateGraph, END

from graphs.state import CPState

from nodes.analyze import analyze_node
from nodes.planner import planner_node
from nodes.generator import generator_node
from nodes.test_node import test_node
from nodes.critic import critic_node
from nodes.repair import repair_node


MAX_ATTEMPTS = 3

def route_after_test(state: CPState):

    if state.get("solved", False):
        return "end"

    if state.get("attempts", 0) >= MAX_ATTEMPTS:
        print("Max attempts reached.")
        return "end"

    return "critic"

def route_after_critic(state: CPState):
    if not state.get("reflection", "").strip():
        return "end"

    return "repair"

def build_graph():

    builder = StateGraph(CPState)

    builder.add_node("analyze", analyze_node)
    builder.add_node("plan", planner_node)
    builder.add_node("generate", generator_node)
    builder.add_node("test",test_node)
    builder.add_node("critic", critic_node)
    builder.add_node("repair", repair_node)

    builder.set_entry_point("analyze")

    builder.add_edge(
        "analyze",
        "plan"
    )

    builder.add_edge(
        "plan",
        "generate"
    )

    builder.add_edge(
        "generate",
        "test"
    )

    builder.add_conditional_edges(
        "test",
        route_after_test,
        {
            "critic": "critic",
            "end": END
        }
    )

    builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "repair": "repair",
            "end": END
        }
    )

    builder.add_edge(
        "repair",
        "test"
    )

    graph = builder.compile()

    return graph