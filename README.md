# Anti-Scam Chatbot for Elders
(Demo project)
Trợ lý AI phòng chống lừa đảo dành cho người cao tuổi, hỗ trợ phát hiện các hình thức lừa đảo phổ biến tại Việt Nam.

**Demo**: [anti-scam-chatbot-for-elders.onrender.com](https://anti-scam-chatbot-for-elders.onrender.com/) (Render free tier — có thể mất 30–50 giây để khởi động nếu không có hoạt động trong 15 phút)

## Tính năng

- **Phát hiện lừa đảo** — 6 loại kịch bản: trúng tuyển, từ thiện, đầu tư tiền ảo, đặt bàn ăn, đặt phòng khách sạn, định danh CCCD
- **RAG (Retrieval-Augmented Generation)** — tra cứu dữ liệu kịch bản trước khi trả lời
- **HallucinationGuard** — lọc phát hiện và ngăn chặn hallucination
- **Xưng hô thích ứng** — tự động nhận diện cách xưng hô của người dùng (ông, bà, cô, chú, ...) và đáp lại phù hợp
- **Chuẩn hóa phương ngữ** — 110+ từ địa phương được chuẩn hóa về tiếng Việt phổ thông
- **Đa luồng hội thoại** — Turn 1: cấu trúc đầy đủ; Turn 2+: hội thoại tự nhiên
- **Fallback** — Groq → OpenRouter → degraded response (503)
- **Giao diện web** — chat real-time, voice input, TTS, lịch sử trò chuyện, xuất tin nhắn
- **Số điện thoại công cộng** — cung cấp số khẩn cấp (113, 114, 115, ...) và tổng đài hỗ trợ khi cần

## Công nghệ

- **Backend**: FastAPI (Python)
- **LLM**: Llama 3.1 8B (Groq) / Llama 3.1 8B Instruct (OpenRouter fallback)
- **Frontend**: HTML + CSS + JavaScript (vanilla)
- **RAG**: JSON knowledge base with keyword-domain matching (≥2 keywords)

## Cấu trúc

```
Anti-Scam-chatbot/
├── main.py                          # FastAPI app
├── SystemPrompt.txt                 # LLM system prompt
├── requirements.txt                 # Python dependencies
├── .gitignore
├── templates/
│   └── index.html                   # Web UI
├── Data_Kich_Ban/                   # RAG knowledge base
│   ├── Lừa đảo trúng tuyển, tuyển sinh/
│   ├── Lừa đảo từ thiện/
│   ├── Lừa đảo đầu tư tiền ảo/
│   ├── Lừa đảo đặt bàn ăn/
│   ├── Lừa đảo đặt phòng khách sạn/
│   └── Lừa đảo định danh cccd/
└── overleaf-project/                # Báo cáo luận văn (LaTeX)
```

## Deploy

### Local

1. Clone repo:
   ```
   git clone https://github.com/lostinnowhere/anti-scam-chatbot-for-elders.git
   cd anti-scam-chatbot-for-elders
   ```
2. Tạo môi trường ảo và cài dependencies:
   ```
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Tạo file `.env` trong thư mục gốc:
   ```
   GROQ_API_KEY=gsk_xxxx
   OPENROUTER_API_KEY=sk-or-xxxx  # optional, fallback
   ```
4. Chạy:
   ```
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
5. Mở trình duyệt: [http://localhost:8000](http://localhost:8000)

### Render (free)

Demo: [https://anti-scam-chatbot-for-elders.onrender.com/](https://anti-scam-chatbot-for-elders.onrender.com/)

1. Push repo lên GitHub
2. Vào [Render Dashboard](https://dashboard.render.com) → New Web Service
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Set environment variables (Render Dashboard → Environment):
   - `GROQ_API_KEY` — từ [Groq Console](https://console.groq.com)
   - `OPENROUTER_API_KEY` — từ [OpenRouter](https://openrouter.ai) (optional, fallback)

> **Lưu ý**: Render free tier sẽ ngủ sau 15 phút không hoạt động. Lần truy cập đầu tiên sau giấc ngủ mất 30–50 giây để khởi động lại (cold start).

## API

| Endpoint | Method | Mô tả |
|---|---|---|
| `/` | GET | Web UI |
| `/chat` | POST | Gửi tin nhắn |
| `/health` | GET | Trạng thái hệ thống |

### `/chat`

```json
POST /chat
{
  "messages": [
    {"role": "user", "content": "có người gọi bảo trúng quạt máy"}
  ]
}
```

Response: `{ "status": "success", "bot_response": "...", "debug": {...} }`

## License

MIT
