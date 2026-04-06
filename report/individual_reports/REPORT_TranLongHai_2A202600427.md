# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: [Trần Long Hải]
- **Student ID**: [2A202600427]
- **Date**: [06/04/2026]

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implemented**:
  - `main.py`
- **Code Highlights**:
  - Đã viết cấu hình chính của ứng dụng trong `main.py`, bao gồm:
    - Khởi tạo `OpenAIProvider` với `OPENAI_API_KEY` và model mặc định từ `.env`.
    - Định nghĩa các công cụ hỗ trợ agent: `calculator`, `search`, `weather`.
    - Tạo và chạy `ReActAgent` với `max_steps=5` trên các truy vấn thử nghiệm.
    - In kết quả và tóm tắt số liệu theo `tracker.session_metrics`.
- **Documentation**:
  - `main.py` là điểm vào (entry point) của hệ thống ReAct Agent.
  - File này kết nối provider LLM với agent và khai báo danh sách công cụ để agent gọi khi cần.
  - Cấu trúc chương trình bao gồm: nạp biến môi trường, khởi tạo LLM, định nghĩa tools, chạy agent với các câu hỏi mẫu và in báo cáo metric.

---

## II. Debugging Case Study (10 điểm)

*The Quoted Argument Parsing Bug — discovered and diagnosed using the telemetry logging system.*

-   **Problem Description**: Agent rơi vào vòng lặp retry ở mọi test case. Nó
    gọi `check_stock("iPhone")` với ký tự dấu ngoặc kép trong đối số,
    khiến tool luôn trả về "không tìm thấy". Agent lặp lại cùng một lời
    gọi tối đa 5 lần (max_steps), sau đó trả về "Không tìm thấy câu trả
    lời" hoặc tự bịa ra câu trả lời.

-   **Log Source** (`logs/2026-04-06.log`):

**Step 0 — Agent sends quoted argument:**

``` json
{"timestamp": "2026-04-06T08:02:11.682612", "event": "AGENT_STEP", "data": {"step": 0, "thought": "To provide the current price of an iPhone, I need to check the stock and price information for it.", "action": "check_stock", "action_args": "\"iPhone\""}}
```

**Tool receives bad input — lookup fails:**

``` json
{"timestamp": "2026-04-06T08:02:11.682612", "event": "TOOL_EXECUTION", "data": {"tool": "check_stock", "args": "\"iPhone\"", "observation": "Tool 'check_stock' returned: Product '\"iPhone\"' not found in inventory. Available products: ['iPhone', 'iPad', 'MacBook', 'AirPods']"}}
```

**Step 1 — Agent retries with same bad format:**

``` json
{"timestamp": "2026-04-06T08:02:12.892616", "event": "AGENT_STEP", "data": {"step": 1, "thought": "The tool 'check_stock' previously returned that the product '\"iPhone\"' was not found due to incorrect formatting, but it also indicated that 'iPhone' is an available product. I will call the tool correctly this time.", "action": "check_stock", "action_args": "iPhone"}}
```

Lưu ý: LLM đã nhận ra lỗi định dạng trong phần Thought, nhưng parser vẫn
lấy sai dữ liệu.

**Final result after 5 steps — failure:**

``` json
{"timestamp": "2026-04-06T08:02:16.716657", "event": "AGENT_END", "data": {"steps": 5, "final_answer": null}}
```

-   **Diagnosis**: Nguyên nhân gốc nằm ở `_parse_response()`. Regex
    `r'Action:\s?(\w+)\(([^)]*)\)'` bắt `([^)]*)` --- toàn bộ nội dung
    bên trong dấu ngoặc, bao gồm cả dấu ngoặc kép. Khi GPT-4o xuất
    `Action: check_stock("iPhone")`, phần được capture là `"iPhone"` (có
    ký tự `"` thật). Hàm tool `check_stock()` sau đó dùng
    `item_name.lower().strip('"')` nhưng `strip` chỉ loại bỏ dấu ngoặc
    kép ngoài cùng, trong khi key trong inventory là `iPhone` (chữ
    thường). Sự kết hợp giữa dấu ngoặc kép thừa + không khớp chữ
    hoa/thường khiến mọi lần tra cứu đều thất bại.

    Đây là một **tool interface bug**, không phải lỗi của LLM hay
    prompt. LLM đã xác định đúng tool và đối số --- lớp parsing đã làm
    sai dữ liệu.

-   **Solution** (đề xuất cho v2):

``` python
# Trong _parse_response(), sau khi lấy action_args:
action_args = action_args.strip().strip('"\'')  # Loại bỏ dấu ngoặc kép bao quanh
```

Và trong `ecommerce_tools.py`, chuẩn hóa key tra cứu:

``` python
# Sử dụng so khớp không phân biệt hoa/thường với chuỗi đã loại bỏ dấu ngoặc kép
for key in INVENTORY:
    if key.lower() == item_lower.strip('"'):
```

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: `Thought` block giúp agent tách bạch quá trình suy nghĩ và hành động. Với ReAct, agent có thể quyết định cần gọi tool nào trước khi trả lời, thay vì chỉ dựa vào câu trả lời “trực tiếp” của Chatbot.
2.  **Reliability**: Agent có thể kém hơn chatbot khi model hiểu sai mục đích của tool hoặc khi tool bị gọi quá mức. Trong `main.py`, nếu tool `calculator` nhận biểu thức không hợp lệ thì agent có thể dừng lại thay vì trả lời mềm dẻo như chatbot.
3.  **Observation**: Feedback từ môi trường (kết quả của `search`, `weather`, `calculator`) giúp agent cập nhật bước tiếp theo. Ví dụ, khi tool trả về kết quả quan trọng, agent có thể dùng thông tin đó để hoàn thiện câu trả lời cuối cùng.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**:
  - Tách `define_tools()` thành module riêng để dễ mở rộng và bổ sung tool mới.
  - Sử dụng hàng đợi bất đồng bộ cho các tác vụ tool call, đặc biệt với các tool yêu cầu IO.
- **Safety**:
  - Thay vì `eval()` trực tiếp, dùng parser an toàn cho `calculator`.
  - Thêm lớp kiểm soát đầu vào tool và cơ chế giới hạn action để tránh agent lặp vô hạn.
- **Performance**:
  - Caching kết quả tool `search`/`weather` để giảm số lần gọi API không cần thiết.
  - Dùng metric tracker để phát hiện các truy vấn tốn nhiều token và tối ưu model hoặc prompt.

---

> [!NOTE]
> Sau khi hoàn thành, đổi tên file thành `REPORT_[YOUR_NAME].md` và lưu vào thư mục này.






