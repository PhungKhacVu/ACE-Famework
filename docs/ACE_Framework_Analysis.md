# ACE Framework — Phân tích & Hướng Dẫn Triển Khai

## 1. ACE là gì?

**ACE (Agentic Context Engineering)** là một framework thiết kế để xây dựng các agent AI tự học và cải thiện theo thời gian thông qua vòng lặp:

```
Task → Generator → Reflector → Curator → MergeEngine → Playbook (cập nhật)
         ↑____________________________________________________|
```

Ý tưởng cốt lõi: thay vì chỉ trả lời một lần, agent **ghi nhớ những gì đã học** (dưới dạng "bullets" trong playbook) và dùng kiến thức đó để cải thiện câu trả lời cho những task tương tự trong tương lai.

---

## 2. Các thành phần chính

### Generator Agent
- Nhận task và ngữ cảnh (playbook hiện tại)
- Sinh ra reasoning + câu trả lời
- Mô phỏng quá trình "suy nghĩ" của agent

### Reflector Agent
- Phân tích kết quả của Generator
- Rút ra insights từ reasoning
- Tăng confidence score dựa trên số insights

### Curator Agent
- Chuyển insights thành "delta bullets" (ứng viên bullet mới)
- Đây là bước chuẩn hóa kiến thức để lưu vào playbook

### Merge Engine
- So sánh bullet ứng viên với playbook hiện tại (Jaccard similarity)
- Nếu tương tự: tăng `helpful_count` (hoặc `harmful_count`)
- Nếu mới: thêm bullet mới
- Tự động cập nhật `confidence = helpful / (helpful + harmful)`

### Playbook Store
- Lưu trữ danh sách Bullet dưới dạng JSON local
- Không cần database, không cần internet
- Có thể đọc/ghi trực tiếp bằng text editor

---

## 3. Cấu trúc dữ liệu

### Bullet
```json
{
  "id": "uuid",
  "text": "Always decompose complex tasks before acting",
  "helpful_count": 5,
  "harmful_count": 1,
  "confidence": 0.83,
  "tags": [],
  "created_at": 1700000000.0,
  "updated_at": 1700000100.0
}
```

### TaskInput
```json
{
  "id": "task-001",
  "description": "How do I reverse a linked list?",
  "domain": "algorithms",
  "context": ""
}
```

### TaskResult
```json
{
  "task_id": "task-001",
  "reasoning": "...",
  "answer": "...",
  "confidence": 0.80,
  "insights": ["..."],
  "delta_bullets": ["..."]
}
```

---

## 4. Luồng xử lý một task

```
1. Pipeline.run(task)
   ├─ Tải playbook từ disk (JSON)
   ├─ Tạo context string từ top-5 bullets
   ├─ Generator.run(task, context) → TaskResult (reasoning, answer)
   ├─ Reflector.run(result, task) → insights
   ├─ Curator.run(result, task) → delta_bullets
   ├─ MergeEngine.merge(existing_bullets, delta_bullets)
   └─ Store.save(updated_bullets) → ghi ra disk
```

---

## 5. Hướng dẫn mở rộng

### Thay Mock LLM bằng Ollama (local)
```python
# Trong app/services/__init__.py, hàm get_llm_service():
# Thêm provider "ollama":
import urllib.request, json as _json

class OllamaLLMService:
    def __init__(self, model="llama3", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def _call(self, prompt):
        data = json.dumps({"model": self.model, "prompt": prompt, "stream": False})
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data.encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())["response"]
    
    def generate(self, task_description, context=""):
        return self._call(f"Task: {task_description}\nContext:\n{context}")
    
    def reflect(self, reasoning, task_description):
        result = self._call(f"Extract 2-3 key insights from:\n{reasoning}")
        return [line.strip("- •").strip() for line in result.split("\n") if line.strip()]
    
    def curate(self, insights, domain):
        result = self._call(f"Convert to actionable guidelines ({domain}):\n" + "\n".join(insights))
        return [line.strip("- •").strip() for line in result.split("\n") if line.strip()]
```

### Thêm domain tags cho bullets
Sửa `CuratorAgent.run()` để truyền `task.domain` vào Bullet khi tạo mới trong MergeEngine.

### Export playbook sang Markdown
```python
# Thêm vào PlaybookStore:
def to_markdown(self) -> str:
    bullets = sorted(self.load(), key=lambda b: -b.confidence)
    lines = ["# ACE Playbook\n"]
    for b in bullets:
        lines.append(f"- [{b.confidence:.2f}] {b.text}")
    return "\n".join(lines)
```

---

## 6. Giải thích thiết kế kiến trúc

### Tại sao dùng Jaccard similarity?
- Không cần thư viện ngoài (numpy, scikit-learn)
- Chạy được trên a-Shell iPhone
- Đủ chính xác cho deduplication text ngắn

### Tại sao JSON thay vì SQLite?
- Dễ đọc bằng mắt, dễ sửa bằng tay
- Không cần driver
- Phù hợp với quy mô playbook nhỏ (< 10,000 bullets)
- Có thể commit vào git để chia sẻ

### Tại sao Mock LLM mặc định?
- Chạy được 100% offline
- Deterministic → test ổn định
- Dễ swap sang real LLM sau này (chỉ cần implement interface `generate/reflect/curate`)
