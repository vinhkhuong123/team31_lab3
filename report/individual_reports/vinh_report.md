# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: khuong quang vinh
- **Student ID**: 2A202600467
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

*Implemented core agent logic, chatbot baseline, e-commerce tools, and the comparison test harness.*

- **Modules Implemented**:
  - `src/agent/agent.py` — ReAct loop core logic (~120 lines)
  - `src/chatbot.py` — Baseline chatbot for comparison (~60 lines)
  - `src/tools/ecommerce_tools.py` — 3 e-commerce tools (~150 lines)
  - `test_comparison.py` — Test harness with 4 test cases (~180 lines)

- **Code Highlights**:

**1. ReAct Loop (`src/agent/agent.py`, `run()` method):**
```python
while steps < self.max_steps:
    result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
    response_text = result["content"]

    tracker.track_request(
        provider=result.get("provider", "unknown"),
        model=self.llm.model_name,
        usage=result["usage"],
        latency_ms=result["latency_ms"]
    )

    thought, action, action_args = self._parse_response(response_text)

    if "Final Answer:" in response_text:
        final_answer = self._extract_final_answer(response_text)
        break

    if action:
        observation = self._execute_tool(action, action_args)
        current_prompt += f"\nObservation: {observation}"

    steps += 1
```

**2. Response Parser (`src/agent/agent.py`, `_parse_response()`):**
```python
def _parse_response(self, response: str) -> tuple:
    thought_match = re.search(r'Thought:\s?(.+?)(?:\nAction:|$)', response, re.DOTALL)
    action_match = re.search(r'Action:\s?(\w+)\(([^)]*)\)', response)
    # Returns (thought, action_name, action_args)
```

**3. Tool Execution (`src/agent/agent.py`, `_execute_tool()`):**
```python
def _execute_tool(self, tool_name: str, args: str) -> str:
    for tool in self.tools:
        if tool['name'].lower() == tool_name.lower():
            tool_func = tool.get('func')
            if tool_func and callable(tool_func):
                result = tool_func(args)
                return f"Tool '{tool_name}' returned: {result}"
    return f"Tool '{tool_name}' not found."
```

- **Documentation**:
  - The `run()` method drives the ReAct loop: it calls `llm.generate()` → `_parse_response()` → `_execute_tool()` → appends observation → repeats.
  - `tracker.track_request()` records metrics (tokens, latency, cost) at every step.
  - `logger.log_event()` logs structured JSON events (`AGENT_START`, `AGENT_STEP`, `TOOL_EXECUTION`, `AGENT_FINAL_ANSWER`, `AGENT_END`) for post-mortem analysis.

---

## II. Debugging Case Study (10 Points)

*The Quoted Argument Parsing Bug — discovered and diagnosed using the telemetry logging system.*

- **Problem Description**: Agent entered a retry loop on every test case. It called `check_stock("iPhone")` with literal quote characters in the argument, causing the tool to always return "not found". The agent retried the same call up to 5 times (max_steps), then either returned "No answer found" or hallucinated an answer.

- **Log Source** (`logs/2026-04-06.log`):

**Step 0 — Agent sends quoted argument:**
```json
{"timestamp": "2026-04-06T08:02:11.682612", "event": "AGENT_STEP", "data": {"step": 0, "thought": "To provide the current price of an iPhone, I need to check the stock and price information for it.", "action": "check_stock", "action_args": "\"iPhone\""}}
```

**Tool receives bad input — lookup fails:**
```json
{"timestamp": "2026-04-06T08:02:11.682612", "event": "TOOL_EXECUTION", "data": {"tool": "check_stock", "args": "\"iPhone\"", "observation": "Tool 'check_stock' returned: Product '\"iPhone\"' not found in inventory. Available products: ['iPhone', 'iPad', 'MacBook', 'AirPods']"}}
```

**Step 1 — Agent retries with same bad format:**
```json
{"timestamp": "2026-04-06T08:02:12.892616", "event": "AGENT_STEP", "data": {"step": 1, "thought": "The tool 'check_stock' previously returned that the product '\"iPhone\"' was not found due to incorrect formatting, but it also indicated that 'iPhone' is an available product. I will call the tool correctly this time.", "action": "check_stock", "action_args": "iPhone"}}
```
Note: the LLM realized the format issue in its Thought, but the parser still captured it incorrectly.

**Final result after 5 steps — failure:**
```json
{"timestamp": "2026-04-06T08:02:16.716657", "event": "AGENT_END", "data": {"steps": 5, "final_answer": null}}
```

- **Diagnosis**: The root cause is in `_parse_response()`. The regex `r'Action:\s?(\w+)\(([^)]*)\)'` captures `([^)]*)` — everything between parentheses including quote marks. When GPT-4o outputs `Action: check_stock("iPhone")`, the captured group is `"iPhone"` (with literal `"` chars). The tool function `check_stock()` then does `item_name.lower().strip('"')` but the `strip` only removes the outermost quotes while the inventory key is `iPhone` (lowercase). The combination of extra quotes + case mismatch caused every lookup to fail.

  This is a **tool interface bug**, not an LLM bug or a prompt bug. The LLM correctly identified the tool and argument — the parsing layer corrupted the data.

- **Solution** (proposed for v2):
```python
# In _parse_response(), after capturing action_args:
action_args = action_args.strip().strip('"\'')  # Remove surrounding quotes
```
And in `ecommerce_tools.py`, normalize the lookup key:
```python
# Use case-insensitive matching with stripped quotes
for key in INVENTORY:
    if key.lower() == item_lower.strip('"'):
        return f"Product '{item_name}' has {INVENTORY[key]['stock']} units. Price: ${INVENTORY[key]['price']}"
```

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning: How `Thought` Helps

The `Thought` block forces the agent to **plan before acting**. Evidence from Test 2 logs:

```json
"thought": "To determine the total price, I need to find the price and availability of the iPhone, the discount percentage of the coupon code, and the shipping cost to Hanoi. I'll start by checking the stock and price of the iPhone."
```

Compare with the chatbot's approach to the same query — it jumped straight to **making assumptions**:
> "Assuming the WINNER coupon offers a 10% discount..." (actual: 20%)
> "Estimated shipping: $40" (actual: $5.40)

The agent **decomposed** the problem into 3 sub-tasks (stock → discount → shipping) while the chatbot **estimated everything in one shot**. Even though the agent failed due to the parsing bug, its reasoning structure was correct.

### 2. Reliability: When Agent Performed Worse

From `test_results.json`, the agent performed **worse in all 4 tests**:

| Test | Chatbot | Agent | Why Agent Lost |
| :--- | :--- | :--- | :--- |
| Test 1 (Simple) | Reasonable estimate in 2.1s | "No answer" in 7.0s | Parsing bug → 5 failed retries |
| Test 2 (Multi-step) | Estimated $1,478.20 in 3.7s | "No answer" in 6.3s | Same parsing bug × 5 retries |
| Test 3 (Stock+Discount) | Estimated $899-$1169 in 2.8s | Hallucinated $1,080 in 9.1s | Gave up, guessed wrong price ($1200 instead of $1299.99) and wrong discount (10% instead of 15%) |
| Test 4 (Invalid Coupon) | Estimated $995 in 3.4s | Hallucinated $1,020 in 8.0s | Gave up, invented $25 shipping (actual: $17.50) |

**Key insight**: When the agent **cannot execute tools**, it becomes a **worse chatbot** — slower (2.5x), more expensive (5.9x tokens), and it gives **precise but wrong numbers** (more dangerous than hedged estimates).

### 3. Observation: How Environment Feedback Influenced Steps

From Test 1 logs, after the tool returned "not found", the agent's next Thought was:

```json
"thought": "The tool 'check_stock' previously returned that the product '\"iPhone\"' was not found due to incorrect formatting, but it also indicated that 'iPhone' is an available product. I will call the tool correctly this time."
```

The agent **read the observation**, **understood the problem** (formatting), and **attempted to fix it**. However, the fix happened in the LLM's text output — the parser still corrupted the argument on the next call. This shows:
- The feedback loop (Observation → next Thought) **works as designed**
- The parser layer **negated** the agent's self-correction ability
- Lesson: The observation must reach the tool **exactly as the agent intended**

---

## IV. Future Improvements (5 Points)

### Scalability
- **Async tool execution**: Use `asyncio` for parallel tool calls (e.g., check stock + check discount simultaneously instead of sequentially). Current implementation burns 2 API round-trips (1s each) that could be parallelized.
- **Semantic caching**: Cache common queries (e.g., "iPhone price") in Redis with a TTL. From test data, identical `check_stock("iPhone")` was called 5 times in Test 1 — all could have been cached after the first call.

### Safety
- **Supervisor pattern**: Add a second LLM call that validates the agent's action before execution. Example: before calling `check_stock`, verify the argument is a known product name. Cost: +1 API call per action, but prevents hallucinated tool calls.
- **Guardrails**: Current `max_steps=5` prevents infinite loops (verified: all 4 tests terminated). Add a **token budget** guard (e.g., stop if total tokens > 2000 per query) to control costs.

### Performance
- **OpenAI Function Calling**: Replace regex-based parsing with OpenAI's native `tools` parameter. This eliminates the quotes parsing bug entirely — the API returns structured JSON with typed arguments. From OpenAI docs:
```python
tools = [{"type": "function", "function": {"name": "check_stock", "parameters": {"type": "object", "properties": {"item_name": {"type": "string"}}}}}]
response = client.chat.completions.create(model="gpt-4o", messages=messages, tools=tools)
# Returns: tool_calls[0].function.arguments = '{"item_name": "iPhone"}' ← Clean JSON!


