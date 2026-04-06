Individual Report: Lab 3 - Chatbot vs ReAct Agent
Student Name: [Nguyễn Tiến Dũng]
Student ID: [2A202600427]
Date: [06/04/2026]
I. Technical Contribution (15 Points)
Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).

Modules Implemented:
test_comparison.py
test_results.json
Code Highlights:
1. test_comparison.py
Đã viết cấu hình chính của ứng dụng trong test_comparison.py, bao gồm:
Sử dụng một danh sách TEST_CASES chứa các đối tượng JSON.
Trong phương thức run_test, bạn triển khai luồng chạy song song cho cùng một Input:
  -Chatbot Baseline: Đóng vai trò là "nhóm đối chứng" (kiến thức thuần túy của LLM).
  -ReAct Agent: Đóng vai trò là "nhóm thử nghiệm" (LLM được trang bị thêm công cụ/suy luận).
  -Highlights: Việc sử dụng khối try-except cho từng hệ thống giúp bài test không bị dừng lại hoàn toàn nếu một trong hai bên gặp lỗi API hoặc logic.
Sử dụng thư viện time để đo thời gian phản hồi theo đơn vị
Hàm print_summary không chỉ in kết quả mà còn thực hiện logic so sánh:
  -Winner Logic: winner = "Chatbot" if cb_time < ag_time else "Agent". Ở đây bạn đang ưu tiên tốc độ (tuy nhiên, trong thực tế bạn có thể cần thêm tiêu chí "độ chính xác").
  -Thống kê: Tính toán average_time và total_wins giúp đưa ra cái nhìn tổng thể về hiệu năng của cả hệ thống sau khi chạy toàn bộ bộ test.
Sử dụng load_dotenv() và os.getenv để quản lý API Key, tránh việc bị lộ mã nguồn nhạy cảm.
Documentation:
test_comparison tương tự với main.py, là điểm vào (entry point) của hệ thống ReAct Agent.
File này có mục đích so sánh version giữa chatbot và Reactive.
2. test_results.json
   Là tập data để test case khitest_comparison.py
II. Debugging Case Study (10 điểm)
The Quoted Argument Parsing Bug — discovered and diagnosed using the telemetry logging system.

Problem Description: Simple call gây lỗi nghiêm trọng, còn reactive đã sửa phần overtime

Log Source (logs/2026-04-06.log):

Version 1: Đây là quote trên file json
{
    "test_id": 1,
    "test_name": "Simple Product Query",
    "complexity": "simple",
    "requires_tools": false,
    "chatbot": {
      "status": "success",
      "answer": "The price of an iPhone can vary greatly depending on the model and storage capacity. As of recent trends, here are some estimated prices for different models:\n\n- iPhone 14: Typically around $799 to $999, depending on storage options.\n- iPhone 14 Pro: Prices usually range from $999 to $1,299.\n- iPhone SE (latest model): Usually around $429 to $479.\n\nKeep in mind, these prices can vary based on promotions, trade-ins, and the retailer.",
      "time_ms": 2100.6360054016113,
      "tool_calls": 0
    },
    "agent": {
      "status": "success",
      "answer": "No answer found after max steps.",
      "time_ms": 7033.267259597778,
      "tool_calls": 1
    }
  },
  {
    "test_id": 2,
    "test_name": "Multi-step Reasoning",
    "complexity": "complex",
    "requires_tools": true,
    "chatbot": {
      "status": "success",
      "answer": "To give you an estimated total price, I will make a few assumptions:\n\n1. **iPhone Price:** A new iPhone typically ranges from $699 to $1,299, depending on the model. For calculation, I'll assume you are purchasing the iPhone 14 at about $799 each.\n\n2. **Coupon Code:** Assuming the \"WINNER\" coupon offers a 10% discount, a typical discount rate for such codes.\n\n3. **Shipping to Hanoi:** International shipping fees can vary, but an estimated cost might be around $30-$50.\n\nLet's do the math:\n\n- **Cost of 2 iPhones:** 2 x $799 = $1,598\n- **10% Discount from Coupon:** $1,598 x 10% = $159.80\n- **Discounted Price:** $1,598 - $159.80 = $1,438.20\n- **Estimated Shipping Cost:** Approximately $40\n\n**Total Estimated Price:** $1,438.20 (phones) + $40 (shipping) = $1,478.20\n\nPlease check the exact prices, coupon conditions, and shipping fees at the time of purchase on your chosen e-commerce site for the most accurate total cost.",
      "time_ms": 3698.1232166290283,
      "tool_calls": 0
    },
    "agent": {
      "status": "success",
      "answer": "No answer found after max steps.",
      "time_ms": 6298.415899276733,
      "tool_calls": 1
    }
  },


Solution (đề xuất cho v2):  "test_id": 3,
    "test_name": "Stock Check with Discount",
    "complexity": "complex",
    "requires_tools": true,
    "chatbot": {
      "status": "success",
      "answer": "I don't have real-time stock information, but MacBooks are typically in stock at major electronics retailers and online stores. Prices for MacBooks can vary depending on the model and specifications. As an estimate, the starting price for a new MacBook Air is around $999, while a MacBook Pro can start at approximately $1,299.\n\nStudent discounts usually range between 10-15% off the regular price. If we assume a 10% discount on a $999 MacBook Air, the price would be approximately $899.10. For a $1,299 MacBook Pro, the discounted price would be around $1,169.10.\n\nI recommend checking the official Apple website or a trusted retailer for the most accurate stock status and to apply the discount code during checkout for the exact discount amount.",
      "time_ms": 2838.5705947875977,
      "tool_calls": 0
    },
    "agent": {
      "status": "success",
      "answer": "The MacBook is in stock and originally priced at $1200. With the 10% STUDENT discount, the final price is $1080.",
      "time_ms": 9057.711839675903,
      "tool_calls": 1
    }
  },
  {
    "test_id": 4,
    "test_name": "Invalid Coupon Handling",
    "complexity": "complex",
    "requires_tools": true,
    "chatbot": {
      "status": "success",
      "answer": "The cost of AirPods generally ranges from $129 to $249 depending on the model. Let's use an average price of around $199 for a pair of AirPods for this estimate.\n\nFor 5 AirPods at $199 each, the total would be $995.\n\nPromo codes like \"INVALID\" are typically not recognized or accepted, so this code likely wouldn't provide a discount. \n\nShipping within the USA is often free for orders of this amount, or there might be minimal charges, often around $5 to $15. However, many retailers offer free shipping for expensive items like AirPods.\n\nIn this case, if we assume free shipping and no applicable discount from the promo code, the final cost would still be $995.",
      "time_ms": 3392.695426940918,
      "tool_calls": 0
    },
    "agent": {
      "status": "success",
      "answer": "The final cost for 5 AirPods with no discount applied and shipped to the USA is $1,020 ($995 for the AirPods and $25 for shipping).",
      "time_ms": 8047.671794891357,
      "tool_calls": 1
    }
  }
]


III. Personal Insights: Chatbot vs ReAct (10 Points)
Reflect on the reasoning capability difference.

Reasoning: So sánh reactive và simple cho thấy reactive tốt hơn
Reliability: Agent có lúc kém hơn
Observation: Tùy thuộc vào tính chất môi trường
IV. Future Improvements (5 Points)
How would you scale this for a production-level AI agent system?

Scalability:
Em đánh giá là 3/5
Safety:
Em đánh giá là 4/5
Performance:
Em đánh giá là 3/5
Note

Sau khi hoàn thành, đổi tên file thành REPORT_[YOUR_NAME].md và lưu vào thư mục này.
