---
name: npm-error-fixer
description: >
  Autonomous agent chạy `npm run dev`, phát hiện lỗi, gọi Anthropic API
  để phân tích nguyên nhân, tự sửa code và lặp lại tối đa 10 lần cho đến khi
  dev server khởi động thành công không còn lỗi. Dùng skill này khi user muốn:
  chạy dev và tự fix, UI đang bị lỗi compile, "make it run", "fix npm dev errors",
  "sửa cho đến khi chạy được". Trigger ngay cả khi user chỉ nói "chạy dev",
  "UI bị lỗi", "sửa lỗi npm" mà không nói rõ loại lỗi.
---

# NPM Error Fixer Agent

Autonomous loop: chạy npm → phát hiện lỗi → phân tích → sửa code → lặp lại cho đến khi sạch.

## Quy trình tổng quát

```
START
  │
  ▼
[1] Chạy: npm run dev (timeout 30s)
  │
  ├─ ✅ Không có lỗi → DONE
  │
  └─ ❌ Có lỗi
        │
        ▼
       [2] Capture full error output
        │
        ▼
       [3] Gọi Anthropic API phân tích lỗi
            → nhận: root cause + fix strategy + files cần sửa
        │
        ▼
       [4] Áp dụng fix theo chỉ dẫn từ API
        │
        ▼
       [5] attempt_count += 1
        │
        ├─ attempt >= MAX (10) → Báo cáo và dừng
        │
        └─ Quay lại bước [1]
```

## Bước 1 — Chạy npm run dev

Luôn dùng lệnh sau, không thay đổi:
```bash
timeout 30 npm run dev -- --no-open 2>&1 || true
```

- `timeout 30` — tránh treo vô hạn
- `--no-open` — không mở browser tự động
- `2>&1` — capture cả stderr
- `|| true` — không crash script dù exit code khác 0

Trước khi chạy lần đầu, kiểm tra script tồn tại:
```bash
cat package.json | grep '"dev"'
```

**Nhận biết dev server thành công:**
```
VITE v4.x.x  ready in Xms   ← Vite
Local:   http://localhost:5173/

webpack compiled successfully  ← Webpack/CRA
started server on 0.0.0.0:3000
```

## Bước 2 — Capture error output

Lưu toàn bộ output vào biến `error_output`. Trích xuất thông tin thô:
- Tên file bị lỗi
- Số dòng / cột
- Mã lỗi (TS2304, SyntaxError, etc.)
- Message đầy đủ

Không tự phán đoán nguyên nhân ở bước này — chuyển raw output sang bước 3.

## Bước 3 — Gọi Anthropic API phân tích lỗi

Gọi Anthropic API với prompt sau để nhận fix strategy:

```python
import anthropic, json

client = anthropic.Anthropic()

def analyze_error(error_output: str, project_context: str) -> dict:
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        system="""Bạn là expert frontend developer. Phân tích lỗi npm run dev 
và trả về JSON với format:
{
  "root_cause": "mô tả ngắn nguyên nhân gốc rễ",
  "errors": [
    {
      "file": "đường dẫn file",
      "line": 42,
      "type": "typescript|import|syntax|dependency|eslint|vite",
      "message": "mô tả lỗi",
      "fix": "mô tả cụ thể cách sửa"
    }
  ],
  "fix_order": ["file1.tsx", "file2.ts"],
  "install_packages": ["package-name"],
  "warning": "cảnh báo nếu có rủi ro khi sửa"
}
Chỉ trả về JSON, không giải thích thêm.""",
        messages=[{
            "role": "user",
            "content": f"Project context:\n{project_context}\n\nError output:\n{error_output}"
        }]
    )
    return json.loads(response.content[0].text)
```

**Project context** cần bao gồm:
```bash
# Thu thập trước khi gọi API
cat package.json                    # dependencies, scripts
ls src/                             # cấu trúc thư mục
cat tsconfig.json 2>/dev/null       # TypeScript config (nếu có)
```

**Sau khi nhận response từ API:**
- Nếu `install_packages` không rỗng → chạy `npm install` trước
- Sửa files theo thứ tự `fix_order`
- Log `root_cause` ra console để user theo dõi

## Bước 4 — Áp dụng fix

Theo đúng chỉ dẫn từ Anthropic API response:

1. **Install packages trước** (nếu có):
   ```bash
   npm install <packages từ install_packages>
   ```

2. **Sửa từng file theo fix_order:**
   - Đọc file trước khi sửa
   - Áp dụng đúng `fix` được chỉ định cho từng error
   - Không sửa thêm bất kỳ thứ gì ngoài phạm vi lỗi được báo

3. **Quy tắc bắt buộc:**
   - Không dùng `@ts-ignore` hay `eslint-disable` để "giả fix"
   - Không xóa code logic để tránh lỗi TypeScript
   - Nếu `warning` trong API response có cảnh báo → log ra và thận trọng

## Bước 5 — Vòng lặp & giới hạn

```python
MAX_ATTEMPTS = 10
attempt = 0

while attempt < MAX_ATTEMPTS:
    output = run_npm_dev()           # timeout 30s
    
    if is_success(output):
        print(f"✅ Thành công sau {attempt+1} lần thử!")
        break
    
    analysis = call_anthropic_api(output, project_context)
    apply_fixes(analysis)
    attempt += 1
else:
    report_remaining_errors()
```

### Khi đạt MAX_ATTEMPTS (10 lần)

```
## Kết quả sau 10 lần thử

### Đã fix ✅
- src/App.tsx:5 — Missing import useState

### Còn lại ❌
- src/api/client.ts:22 — [mô tả lỗi]
  Root cause (từ API): ...
  Gợi ý thủ công: ...
```

## Nhận biết "npm run dev thành công"

**✅ Thành công:**
```
# Vite
VITE v4.x.x  ready in Xms
Local:   http://localhost:5173/

# Webpack / CRA
webpack compiled successfully
Started on port 3000
```

**❌ Vẫn còn lỗi:**
- Output chứa `error`, `Error`, `ERROR`, `failed`, `Failed to compile`
- Process exit trước khi in "ready" hoặc "compiled successfully"
- Timeout 30s hết mà chưa thấy success message

## Ví dụ output mỗi vòng lặp

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 Lần thử #1/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Chạy: npm run dev (timeout 30s)
❌ Dev server crash sau 2s

🤖 Gọi Anthropic API phân tích...
Root cause: "Missing React import — JSX transform chưa được bật"

Errors nhận từ API:
  1. src/App.tsx:1 [syntax] → Thêm import React from 'react'
  2. src/components/Header.tsx:3 [import] → Sửa path './utils' → '../utils'

🔧 Đang sửa 2 files...
  ✓ App.tsx — thêm React import
  ✓ Header.tsx — sửa import path

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 Lần thử #2/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Dev server khởi động thành công!
   Local: http://localhost:5173/
   Hoàn thành sau 2 lần thử.
```

## Lưu ý quan trọng

- Lỗi lặp lại y hệt sau khi sửa → báo API context đầy đủ hơn (include file content)
- Nếu API trả về `install_packages` → luôn install trước khi sửa code
- Không timeout dưới 30s vì một số bundler khởi động chậm
