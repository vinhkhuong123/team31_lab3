# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: team 31
- **Team Members**: 2A202600427 - Trần Long Hải, 2A202600146 - Nguyễn Đức Anh, 2A202600219-Nguyễn Tiến Dũng
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

*Comparison of a baseline chatbot (pure LLM) vs a ReAct Agent (LLM + Tools) on an E-commerce Assistant scenario with 4 test cases.*

- **Success Rate**: Chatbot 4/4 (100%) — Agent 1/4 (25%, 1 partial answer + 2 failures + 1 hallucinated)
- **Key Outcome**: The chatbot outperformed the agent in v1 due to a critical argument-parsing bug that prevented the agent from executing tools correctly. The agent entered retry loops on 3/4 tests, consuming 2.5x more time and 4x more tokens. However, the failure analysis revealed a clear fix path for v2, and the agent's tool-based architecture remains the correct approach for production multi-step queries.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

```
User Query
    ↓
┌─────────────────────────────────────┐
│  System Prompt (tools + format)     │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  LLM generates:                     │
│    Thought: reasoning               │
│    Action: tool_name(arguments)     │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Parse Action → Execute Tool        │
│  Observation: tool result           │
└──────────────┬──────────────────────┘
               ↓
       Append Observation to prompt
               ↓
       Loop until "Final Answer"
       or max_steps (5) reached
```

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `check_stock` | `string` (item_name) | Check product availability & price. Returns stock count and unit price. |
| `get_discount` | `string` (coupon_code) | Validate coupon code and return discount percentage. |
| `calc_shipping` | `float, string` (weight_kg, destination) | Calculate shipping cost based on weight and destination city/region. |

**Mock Database:**
- Products: iPhone ($999.99), iPad ($499.99), MacBook ($1299.99), AirPods ($199.99)
- Coupons: WINNER (20%), SUMMER (10%), STUDENT (15%), INVALID (no discount)
- Shipping: Hanoi ($5 base + $2/kg), USA ($15 base + $5/kg)

### 2.3 LLM Providers Used
- **Primary**: GPT-4o (OpenAI)
- **Secondary (Backup)**: Gemini 1.5 Flash (implemented but not tested in this run)

---

## 3. Telemetry & Performance Dashboard

*Metrics collected from `test_comparison.py` run on 2026-04-06, 4 test cases.*

### Chatbot Metrics
| Metric | Test 1 | Test 2 | Test 3 | Test 4 | Aggregate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Prompt Tokens | 67 | 82 | 74 | 74 | 297 |
| Completion Tokens | 104 | 252 | 163 | 146 | 665 |
| Total Tokens | 171 | 334 | 237 | 220 | **962** |
| Latency (ms) | 2,101 | 3,698 | 2,839 | 3,393 | avg **3,008** |

### Agent Metrics
| Metric | Test 1 | Test 2 | Test 3 | Test 4 | Aggregate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Total Tokens (all steps) | 182+243+267+297+332 = 1,321 | 222+289+289+326+374 = 1,500 | 209+241+322+310+473 = 1,555 | 218+302+300+502 = 1,322 | **5,698** |
| Steps Used | 5 (max) | 5 (max) | 4 | 3 | avg **4.25** |
| Latency (ms) | 7,033 | 6,298 | 9,058 | 8,048 | avg **7,609** |

### Summary Dashboard
- **Average Latency Chatbot (P50)**: 3,008ms
- **Average Latency Agent (P50)**: 7,609ms
- **Max Latency (P99)**: 9,058ms (Agent, Test 3)
- **Average Tokens per Task — Chatbot**: 240 tokens
- **Average Tokens per Task — Agent**: 1,424 tokens (5.9x more)
- **Total Cost of Test Suite**: Chatbot ~$0.0096 | Agent ~$0.057 (Agent 5.9x more expensive)

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study: Quoted Argument Parsing Bug

- **Input**: "What is the price of an iPhone?"
- **Expected**: Agent calls `check_stock(iPhone)` → Tool returns "$999.99, 15 units in stock"
- **Actual**: Agent calls `check_stock("iPhone")` with literal quotes in the argument string

**Observation from logs** (`logs/2026-04-06.log`):
```json
{
  "event": "AGENT_STEP",
  "data": {
    "step": 0,
    "action": "check_stock",
    "action_args": "\"iPhone\""
  }
}
{
  "event": "TOOL_EXECUTION",
  "data": {
    "tool": "check_stock",
    "args": "\"iPhone\"",
    "observation": "Tool 'check_stock' returned: Product '\"iPhone\"' not found in inventory. Available products: ['iPhone', 'iPad', 'MacBook', 'AirPods']"
  }
}
```

- **Root Cause**: The regex parser in `_parse_response()` captures `([^)]*)` which includes quote characters. The LLM consistently outputs `Action: check_stock("iPhone")` with quotes, but the tool function receives `'"iPhone"'` (with extra quotes) causing a dictionary key mismatch.

**Cascade Effect:**
```
Parsing bug → Tool returns "not found"
           → Agent retries same call (no self-correction)
           → Hits max_steps=5
           → Returns "No answer found" or hallucinated answer
           → 2.5x latency, 5.9x tokens, 5.9x cost
```

### Affected Tests
| Test | Steps Used | Outcome |
| :--- | :--- | :--- |
| Test 1 (Simple Query) | 5/5 (max) | Failed: "No answer found after max steps" |
| Test 2 (Multi-step) | 5/5 (max) | Failed: "No answer found after max steps" |
| Test 3 (Stock+Discount) | 4/5 | Partial: Agent hallucinated "$1200 with 10% off = $1080" (real price: $1299.99, real discount: 15%) |
| Test 4 (Invalid Coupon) | 3/5 | Partial: Agent hallucinated "$995 + $25 shipping = $1020" (real: 5×$199.99 = $999.95, no discount, shipping $15+$2.5=$17.50) |

---

## 5. Ablation Studies & Experiments

### Experiment 1: Chatbot vs Agent on E-commerce Queries

| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Test 1: Simple Price Query | Estimated $799-$1299 (reasonable range) | "No answer found" (tool failure) | **Chatbot** |
| Test 2: Multi-step (buy 2 iPhones + coupon + shipping) | Estimated $1,478.20 (assumed 10% discount, $40 shipping) | "No answer found" (tool failure) | **Chatbot** |
| Test 3: Stock + Discount | Estimated $899-$1169 (assumed 10% student discount) | Hallucinated "$1200 with 10% = $1080" | **Draw** (both inaccurate) |
| Test 4: Invalid Coupon | Estimated $995 (no discount, free shipping) | Hallucinated "$995 + $25 = $1020" | **Chatbot** (closer to logic) |

**Key Insight:**
- Chatbot consistently gives **reasonable estimates** with disclaimers ("please check the exact prices")
- Agent either **fails completely** or **hallucinates precise but wrong numbers**
- For production: wrong precise numbers (Agent) are **more dangerous** than hedged estimates (Chatbot) because users trust precision

### Experiment 2: Chatbot Accuracy Analysis

The chatbot's answers reveal consistent **hallucination patterns**:
| Data Point | Chatbot Guess | Actual (Database) | Error |
| :--- | :--- | :--- | :--- |
| iPhone price | $799 | $999.99 | -25% |
| WINNER discount | 10% | 20% | -50% |
| Shipping to Hanoi | $40 | $5.40 (0.4kg) | +641% |
| STUDENT discount | 10% | 15% | -33% |
| AirPods price | $199 | $199.99 | -0.5% |

**Conclusion:** Chatbot sounds reasonable but **every number is wrong**. This proves the need for tool-backed agents in production.

---

## 6. Production Readiness Review

### Security
- **Input sanitization**: Tool arguments are currently passed as raw strings — vulnerable to injection. Fix: Pydantic validation with strict schemas.
- **API key management**: Using `.env` with `python-dotenv`. Keys never logged (OpenAI masks them in error messages).

### Guardrails
- **Loop limit**: `max_steps=5` prevents infinite billing. Evidence: All 4 tests terminated correctly.
- **Error logging**: Every step logged to `logs/` with timestamp, enabling post-mortem analysis.
- **Cost tracking**: `metrics.py` estimates cost per request (e.g., $0.00182 for 182 tokens).

### Scaling Considerations
- **Current**: Single-agent, synchronous, 1 LLM call per step.
- **Next**: Transition to LangGraph or CrewAI for complex branching and multi-agent orchestration.
- **Production**: Add semantic caching (Redis), rate limiting, and circuit breaker for API failures.
