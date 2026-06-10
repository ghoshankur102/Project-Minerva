# Project Minerva - Stateful Cyclic Self-Healing Competitive Programmer Agent

## Overview

This project implements a **Stateful Cyclic Self-Healing AI Agent** using **LangGraph**.

The goal of the agent is to autonomously solve competitive programming problems by:

1. Understanding the problem statement.
2. Generating a solution.
3. Reviewing its own solution.
4. Detecting mistakes.
5. Learning from previous failures.
6. Regenerating improved solutions.

The agent follows a cyclic workflow where failed solutions are automatically reviewed and corrected until either:

* A valid solution is produced.
* The retry limit is reached.

This architecture demonstrates how LangGraph can be used to create agents that maintain state, use memory, and improve outputs through iterative self-correction.

---

# Objective

The objective of this project is to test whether a simple stateful agent can improve competitive programming performance through:

* Structured reasoning
* Self-review
* Failure memory
* Cyclic retries

instead of relying on a single LLM call.

The target domain is Codeforces-style algorithmic problems.

---

# Technologies Used

* Python
* LangGraph
* LangChain
* Google Gemini API
* TypedDict State Management

---

# Architecture

The agent is implemented as a directed graph using LangGraph.

The workflow contains four nodes:

1. Analyze Problem
2. Generate Solution
3. Review Solution
4. Store Failure

The graph contains a feedback loop which enables self-healing behavior.

---

# Architectural Flow Chart

```text
                    ┌─────────────────┐
                    │ Problem Input   │
                    └────────┬────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Analyze Problem     │
                  └────────┬────────────┘
                           │
                           ▼
                  ┌─────────────────────┐
                  │ Generate Solution   │
                  └────────┬────────────┘
                           │
                           ▼
                  ┌─────────────────────┐
                  │ Review Solution     │
                  └────────┬────────────┘
                           │
              ┌────────────┴─────────────┐
              │                          │
              ▼                          ▼
         PASS Found                  FAIL Found
              │                          │
              ▼                          ▼
            END                 ┌────────────────┐
                                │ Store Failure  │
                                └───────┬────────┘
                                        │
                                        ▼
                              Generate Improved
                                   Solution
                                        │
                                        ▼
                                  Review Again
```

---

# State Design

The agent uses a shared state object that is passed between nodes.

```python
class AgentState(TypedDict):
    problem: str
    analysis: str
    code: str
    review: str
    retries: int
    memory: List[str]
```

## State Variables

### problem

Stores the original competitive programming problem statement.

### analysis

Stores the reasoning generated during the analysis stage.

### code

Stores the generated C++ solution.

### review

Stores the reviewer verdict.

Possible values:

```text
PASS
```

or

```text
FAIL: reason
```

### retries

Tracks the number of self-correction attempts.

### memory

Stores reviewer feedback from failed attempts.

This acts as a lightweight memory system.

---

# Node Descriptions

## Node 1 - Analyze Problem

Purpose:

Understand the problem before generating code.

Responsibilities:

* Identify algorithm type
* Determine required data structures
* Estimate complexity
* Detect edge cases

Output:

```text
analysis
```

stored in the state.

---

## Node 2 - Generate Solution

Purpose:

Generate a complete competitive programming solution.

Inputs:

* Problem statement
* Analysis
* Previous failure memory

Responsibilities:

* Produce C++17 code
* Incorporate previous reviewer feedback
* Attempt to fix earlier mistakes

Output:

```text
code
```

stored in state.

---

## Node 3 - Review Solution

Purpose:

Act as an automated competitive programming reviewer.

Responsibilities:

* Check algorithm correctness
* Check complexity
* Check edge cases

Possible outputs:

```text
PASS
```

or

```text
FAIL: reason
```

Output is stored in:

```text
review
```

---

## Node 4 - Store Failure

Purpose:

Create memory from unsuccessful attempts.

Responsibilities:

* Save reviewer feedback
* Increase retry count

Example:

```text
FAIL: Does not handle n = 1
```

is added to memory.

Future generations can use this information.

---

# Self-Healing Mechanism

The self-healing behavior comes from the feedback loop.

Workflow:

1. Generate solution.
2. Review solution.
3. If failure occurs:

   * Save feedback.
   * Increment retry count.
   * Generate improved solution.
4. Repeat until:

   * PASS
   * Maximum retries reached

This allows the agent to improve without human intervention.

---

# Memory Mechanism

The memory component stores failures from previous attempts.

Example:

```text
FAIL: Overflow possible for large values.
```

```text
FAIL: Edge case n = 1 not handled.
```

These messages are appended to memory and provided to future generations.

This helps prevent repeated mistakes.

---

# LangGraph Usage

LangGraph was chosen because it provides:

* Explicit graph structure
* State management
* Cyclic workflows
* Conditional routing
* Memory support

The project demonstrates the core concepts taught in:

* LangGraph Quickstart
* Thinking in LangGraph
* Workflows and Agents
* Memory Systems

---

# Routing Logic

After each review:

```python
if PASS:
    END

if retries >= 3:
    END

otherwise:
    store_failure
```

This creates the cyclic correction loop.

---

# Example Execution Flow

```text
Input Problem
      │
      ▼
Analyze Problem
      │
      ▼
Generate Solution
      │
      ▼
Review Solution
      │
      ▼
FAIL
      │
      ▼
Store Failure
      │
      ▼
Generate Improved Solution
      │
      ▼
Review Again
      │
      ▼
PASS
      │
      ▼
END
```

---

# Key Features

* Stateful execution
* Cyclic workflow
* Self-healing architecture
* Memory-based correction
* Competitive programming focus
* LangGraph implementation
* C++ code generation
* Automated solution review

---

# Limitations

Current reviewer is LLM-based and does not execute code.

Future improvements may include:

* Compilation checking
* Automated test execution
* Multiple reviewer agents
* Tool calling
* Retrieval-augmented memory
* Contest history memory
* Dynamic test generation

---

# Conclusion

This project demonstrates a simple but effective Stateful Cyclic Self-Healing Agent using LangGraph.

Instead of relying on a single LLM response, the system repeatedly reviews and improves its own outputs through memory and feedback loops. The architecture serves as a foundation for more advanced autonomous competitive programming agents capable of tackling increasingly difficult Codeforces problems.
