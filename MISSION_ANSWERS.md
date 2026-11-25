# Day 14 Lab — Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found

1. API key và database URL được hard-code trong `develop/app.py`; nếu commit lên repo public, thông tin nhạy cảm có thể bị lộ.
2. API key được in ra log, làm tăng nguy cơ lộ secret.
3. `DEBUG = True` và `reload=True` được bật cố định; đây là cấu hình phát triển.
4. Server chỉ bind vào `localhost`, nên không nhận được kết nối từ bên ngoài container.
5. Port bị cố định ở `8000`, không đọc biến `PORT` từ môi trường deploy.
6. Không có health check endpoint để nền tảng kiểm tra tình trạng ứng dụng.
7. Dùng `print()` thay cho logging có cấu trúc.
8. Không có xử lý shutdown rõ ràng cho lúc ứng dụng bị dừng.

### Exercise 1.3: So sánh

| Đặc điểm | Develop | Production | Vì sao quan trọng |
|---|---|---|---|
| Config và secret | Giá trị hard-code | Đọc từ biến môi trường | Tránh lộ secret và đổi cấu hình theo môi trường |
| Host và port | `localhost`, port cố định | Đọc từ config/env | Cho phép nhận traffic bên ngoài container và dùng được trên cloud |
| Debug | Bật cố định | Bật theo cấu hình | Tránh chạy chế độ debug khi phục vụ thật |
| Logging | `print()`; có thể in secret | Structured logging; tránh log secret | Dễ tìm kiếm và giảm nguy cơ lộ dữ liệu |
| Health check | Không có | Có `/health` và `/ready` | Nền tảng có thể kiểm tra app còn sống và sẵn sàng |
| Shutdown | Không quản lý rõ ràng | Có lifecycle/shutdown handling | Giúp dừng dịch vụ có trật tự |

### AI log

- Hỏi AI: Hướng dẫn thực hiện CP1.
- Nhận được: Gợi ý tìm anti-pattern và so sánh bản develop với production.
- Tự kiểm tra: Đối chiếu từng ý với `01-localhost-vs-production/develop/app.py` và `production/app.py`.

## Part 2: Docker

### Exercise 2.1: Dockerfile cơ bản

1. Base image: `python:3.11`.
2. Working directory: `/app`.
3. Copy và cài `requirements.txt` trước source code để Docker tái sử dụng layer dependencies khi chỉ source thay đổi, giúp build nhanh hơn.
4. `CMD` là lệnh mặc định khi container chạy và có thể được thay bằng lệnh ở `docker run`. `ENTRYPOINT` định nghĩa chương trình chính; các đối số truyền lúc chạy thường được nối vào chương trình đó.

### Exercise 2.2: Build và chạy image develop

- Image: `my-agent:develop`.
- Content size đo bằng `docker images`: **426 MB** (Disk usage: 1.67 GB).
- Kết quả: container chạy và `POST /ask?question=What%20is%20Docker%3F` trả câu trả lời JSON thành công.

### Exercise 2.3: Multi-stage build

- Stage 1 (`builder`): cài dependencies và công cụ build.
- Stage 2 (`runtime`): dùng Python slim, chỉ nhận thư viện và source cần để chạy; chạy dưới user `appuser`.
- Kích thước develop: **426 MB** content size.
- Kích thước production: **57.4 MB** content size.
- Production nhỏ hơn khoảng **86.5%**, theo công thức `(426 - 57.4) / 426 × 100`.

### Exercise 2.4: Docker Compose stack

```text
Client → Nginx (:80/:443) → Agent (:8000)
                             ├→ Redis (:6379)
                             └→ Qdrant (:6333)
```

- Compose khởi động các service `agent`, `redis`, `qdrant` và `nginx`; agent, Redis và Qdrant khỏe mạnh theo trạng thái healthcheck.
- `GET /health` qua Nginx trả HTTP 200.
- `POST /ask` qua Nginx với JSON hợp lệ trả HTTP 200 và câu trả lời mock.
- Lần thử đầu của POST trả 500 do JSON bị PowerShell biến dạng khi quote trực tiếp; gửi JSON từ file tạm đã thành công.

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

- Project: `day14-production-agent`, environment `production`, service `day14-agent`.
- Public URL: https://day14-agent-production-439d8b50.up.railway.app
- Live checks on 2026-11-26: `GET /health` → **200**; `GET /ready` → **200**; `POST /ask` without `X-API-Key` → **401**.
- Authenticated `/ask` still needs verification after rotating the Redis credential that was exposed during troubleshooting. See `DEPLOYMENT.md` for the safe test command.

## Part 4: API Security (CP3)

### Exercise 4.1: API key cơ bản

- Bản develop nhận `question` qua query string. Gửi JSON body vào bản này trả 422 vì thiếu query parameter.
- Không có `X-API-Key`: **401**.
- Có `X-API-Key` hợp lệ (`secret-key-123` trong môi trường lab): **200**.
- Theo code, API key sai trả **403**.

### Exercise 4.2–4.3: JWT và rate limit

- Lấy JWT tại `POST /auth/token` bằng tài khoản lab `student` / `demo123`; token hợp lệ gọi `POST /ask` thành công với **200**.
- Rate limit user là 10 request/phút. Trong vòng lặp 12 lần, kết quả quan sát được: request 1–9 trả **200**, request 10–12 trả **429**. Request kiểm tra `/ask` trước vòng lặp cũng đã tính vào quota.
- Token không được lưu trong báo cáo.

### Exercise 4.4: Cost guard

- Cost guard kiểm tra ngân sách trước khi gọi LLM; sau phản hồi, tính và ghi nhận token/chi phí. Ngân sách mặc định là $1/ngày cho mỗi user và $10/ngày toàn hệ thống.
- Khi ngân sách user bị vượt, code trả **402**; khi ngân sách toàn hệ thống bị vượt, code hiện trả **503**.
- Chưa chủ động tiêu hết budget trong lab; kết quả 402 chưa được kiểm chứng bằng request thực tế. Có thể xem usage qua `GET /me/usage` với JWT hợp lệ.

### Vì sao cần cả rate limit và cost guard?

Rate limit hạn chế tần suất gọi để bảo vệ dịch vụ khỏi spam/quá tải. Cost guard giới hạn mức chi tiêu để tránh bill LLM vượt ngân sách; một request có thể tốn nhiều hơn request khác nên chỉ giới hạn số request là chưa đủ.

## Part 5: Scaling & Reliability (CP4)

### Exercise 5.1–5.3: Health check và graceful shutdown

- `/health` là liveness check: báo tiến trình còn sống; nền tảng có thể khởi động lại instance nếu check thất bại.
- `/ready` là readiness check: báo instance đã sẵn sàng nhận traffic; load balancer có thể ngừng gửi traffic khi instance chưa sẵn sàng.
- Graceful shutdown nhận tín hiệu dừng, ngừng nhận request mới, chờ request đang xử lý hoàn thành rồi mới thoát để tránh cắt ngang request.
- Đã kiểm tra develop: `GET /health`, `GET /ready`, và `POST /ask?question=hello` đều trả **HTTP 200**. `/ready` báo `ready: true`.
- Gửi SIGTERM trong khi một request `/ask` đang chạy; request hoàn tất với **HTTP 200**, và log Uvicorn ghi `Application shutdown complete` cùng `Finished server process`.
- Phép thử hai request đồng thời chỉ ghi nhận một request ở server; request còn lại trả HTTP 000. Không tính lần đó là thành công cho request thứ hai.

### Exercise 5.4–5.5: Stateless agent với Redis

- Chạy stack bằng `docker compose -p k5-day14-scaling up -d --build --scale agent=3` và kiểm tra bằng `python3 test_stateless.py`.
- Năm request trong cùng session được phục vụ bởi ba instance: `instance-7d7517`, `instance-f30d29`, `instance-36baa6`.
- Lịch sử đọc lại có **10 messages** (5 câu hỏi và 5 câu trả lời), chứng minh session state được chia sẻ qua Redis giữa các instance.
- Kết quả: tất cả request được phục vụ dù đổi instance; lịch sử hội thoại được bảo toàn.
- Nginx nhận request ở cổng `8080` và cân bằng tải tới agent; các agent và Redis giao tiếp trong mạng Compose nội bộ.

## Part 6: Final production-ready agent

- Production-readiness checker: **PASS 12/12 criteria; 41/41 checks passed** (full Docker run, as reported during the lab).
- Production Docker image: **238 MB**, below the 500 MB limit.
- Railway public service: https://day14-agent-production-439d8b50.up.railway.app
- CP6 deployment and Redis credential rotation completed (confirmed by the student); `/health` and `/ready` returned 200, missing API key returned 401, and authenticated `/ask` was verified by the student.
- Deployment commands and endpoint details: see `DEPLOYMENT.md`.
