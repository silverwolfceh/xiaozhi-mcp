# xiaozhi-mcp

**MCP cho xiaozhi AI với mục tiêu dễ tích hợp, dễ phát triển**

---

## Giới thiệu

`xiaozhi-mcp` là một dự án mã nguồn mở được phát triển bằng Python với mục tiêu mang lại một cách triển khai đơn giản cho các quy trình hoặc tác vụ tự động hóa. Dự án này tập trung vào việc xây dựng các công cụ, module hỗ trợ xử lý và tích hợp dễ dàng, phù hợp cho các nhà phát triển muốn tạo hệ thống mở rộng hoặc thử nghiệm nhanh.

---

## Cấu trúc dự án

- `main.py`  
  Tệp khởi chạy chính của dự án.

- `logcfg.py`  
  Quản lý cấu hình logging.

- `tool_registry.py`  
  Đăng ký và quản lý các công cụ.

- `response_format.py`  
  Định nghĩa định dạng phản hồi.

- `utils.py`  
  Tập hợp các hàm tiện ích dùng chung.

- `tools/`  
  Thư mục chứa các công cụ mở rộng.

- `.env_example`  
  Ví dụ cấu hình môi trường.

- `.gitignore`  
  Danh sách các file/thư mục bị bỏ qua khi commit.

- `requirements.txt`  
  Danh sách các gói phụ thuộc Python.

---

## Yêu cầu hệ thống

- Python 3.7 trở lên
- pip để quản lý thư viện

---

## Cài đặt

1. **Clone repository:**
   ```bash
   git clone https://github.com/silverwolfceh/xiaozhi-mcp.git
   cd xiaozhi-mcp
   ```

2. **Cài đặt các thư viện phụ thuộc:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Thiết lập file môi trường (nếu cần):**
   - Sao chép `.env_example` thành `.env` và chỉnh sửa thông số phù hợp.

---

## Sử dụng

Chạy file chính:
```bash
python main.py
```
Hoặc tích hợp các module, công cụ theo nhu cầu phát triển của bạn.

---

## Đóng góp

Bạn có thể đóng góp mã nguồn, báo lỗi hoặc đề xuất tính năng mới qua [Issues](https://github.com/silverwolfceh/xiaozhi-mcp/issues) hoặc gửi Pull Request.

---

## Tác giả

- [silverwolfceh](https://github.com/silverwolfceh)

---

## Giấy phép

Chưa công bố giấy phép. Liên hệ tác giả nếu cần sử dụng cho mục đích thương mại.

---

## Thông tin bổ sung

Dự án đang trong giai đoạn phát triển. Hãy theo dõi để nhận cập nhật mới nhất!
