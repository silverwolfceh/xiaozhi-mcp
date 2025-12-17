# xiaozhi-mcp

**MCP cho xiaozhi AI với mục tiêu dễ tích hợp, dễ phát triển**

---

## Giới thiệu

`xiaozhi-mcp` là một dự án mã nguồn mở được phát triển bằng Python với mục tiêu mang lại một cách triển khai đơn giản cho các quy trình hoặc tác vụ tự động hóa. Dự án này tập trung vào việc xây dựng các công cụ, module hỗ trợ xử lý và tích hợp dễ dàng, phù hợp cho các nhà phát triển muốn tạo hệ thống mở rộng hoặc thử nghiệm nhanh.

Hệ thống bao gồm hai thành phần chính:
- **Web Interface (app.py)**: Giao diện quản trị và đăng ký người dùng
- **Worker Manager (main.py)**: Quản lý và giám sát các worker tự động

---

## Cấu trúc dự án

### Tệp chính

- **`app.py`**  
  Ứng dụng web Flask cung cấp:
  - Giao diện đăng ký người dùng
  - Trang quản trị (admin) để quản lý users và tools
  - Quản lý kết nối giữa users và tools
  - API endpoints cho các thao tác CRUD

- **`main.py`**  
  Chương trình chính khởi chạy worker manager:
  - Tạo và quản lý các worker cho mỗi user
  - Tích hợp database monitor tự động
  - Xử lý shutdown gracefully

- **`monitor.py`**  
  Hệ thống giám sát database tự động:
  - Polling database mỗi 5 giây để phát hiện thay đổi
  - Tự động thêm/xóa/khởi động lại worker khi User thay đổi
  - Chạy trong background thread

- **`worker.py`**  
  Định nghĩa các class worker:
  - `worker`: Kết nối với xiaozhi và xử lý tool calls
  - `worker_manager`: Quản lý tất cả worker instances

### Database

- **`database/models.py`**  
  Định nghĩa các model và quản lý database:
  - Model `User`: Thông tin người dùng (email, URL, trạng thái, premium)
  - Model `Tool`: Công cụ có sẵn trong hệ thống
  - Relationship nhiều-nhiều giữa User và Tool
  - Manager classes: `UserManager`, `ToolManager`, `ConnectionManager`
  - Database event listeners cho monitoring

### Utilities

- **`logcfg.py`**  
  Quản lý cấu hình logging cho toàn bộ ứng dụng

- **`tool_manager.py`**  
  Đăng ký và quản lý các công cụ từ thư mục `tools/`

- **`response_format.py`**  
  Định nghĩa định dạng phản hồi chuẩn

- **`utils.py`**  
  Tập hợp các hàm tiện ích dùng chung

### Thư mục

- **`tools/`**  
  Chứa các công cụ mở rộng:
  - `ipaddress.py`: Công cụ xử lý IP address
  - `news.py`: Công cụ lấy tin tức
  - Các tool khác có thể được thêm vào

- **`xiaozhi/`**  
  Module kết nối với xiaozhi AI:
  - `xiaozhiconn.py`: Xử lý WebSocket connection

- **`templates/`**  
  Templates HTML cho Flask:
  - `admin_login.html`: Trang đăng nhập admin
  - `admin.html`: Trang quản trị
  - `user.html`: Trang đăng ký user
  - `get_premium.html`: Trang nâng cấp premium
  - `base.html`: Template cơ bản

- **`static/`**  
  Tài nguyên tĩnh (CSS, JS, images)

- **`data/`**  
  Thư mục dữ liệu:
  - `logs/`: Log files
  - `persistent/`: Database và dữ liệu lâu dài
  - `runtime/`: Dữ liệu tạm thời khi chạy

### Cấu hình

- **`.env_example`**  
  Ví dụ cấu hình môi trường

- **`.gitignore`**  
  Danh sách các file/thư mục bị bỏ qua khi commit

- **`requirements.txt`**  
  Danh sách các gói phụ thuộc Python

---

## Yêu cầu hệ thống

- Python 3.12
- pip để quản lý thư viện
- SQLite3 (đã có sẵn trong Python)

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

3. **Thiết lập file môi trường:**
   - Sao chép `.env_example` thành `.env` và chỉnh sửa thông số:
   ```bash
   cp .env_example .env
   ```
   - Cấu hình các biến môi trường cần thiết (ADMIN_USER, ADMIN_PASSWORD, v.v.)

4. **Khởi tạo database:**
   Database sẽ được tự động khởi tạo khi chạy lần đầu tiên

---

## Sử dụng

### 1. Chạy Web Interface (Flask App)

Khởi động server web để quản lý users và tools:

```bash
python app.py
```

Truy cập:
- **Trang người dùng**: http://localhost:5000/user
- **Trang admin**: http://localhost:5000/admin/login

### 2. Chạy Worker Manager

Khởi động worker manager để quản lý các kết nối:

```bash
python main.py
```

Worker manager sẽ:
- Tự động tạo worker cho tất cả users đã kích hoạt
- Giám sát database và đồng bộ workers theo thay đổi
- Log tất cả hoạt động vào `data/logs/`

### 3. Luồng hoạt động

1. **Đăng ký User:**
   - Truy cập trang `/user`
   - Nhập email và WebSocket URL (wss://...)
   - Hệ thống tạo User trong database

2. **Tự động tạo Worker:**
   - Monitor phát hiện User mới trong database
   - Tự động tạo và khởi động worker cho User đó
   - Worker kết nối với xiaozhi qua WebSocket URL

3. **Quản lý từ Admin:**
   - Đăng nhập vào `/admin/login`
   - Kích hoạt/vô hiệu hóa users
   - Quản lý tools và permissions
   - Nâng cấp users lên premium

4. **Đồng bộ tự động:**
   - Khi admin thay đổi user (enable/disable, đổi URL)
   - Monitor tự động cập nhật worker tương ứng
   - Không cần khởi động lại ứng dụng

---

## Tính năng Database Monitoring

Hệ thống tự động giám sát và đồng bộ workers:

### Các thay đổi được phát hiện:

- **User mới được thêm:**
  - Nếu `user_enable = True`: Worker tự động được tạo
  - Nếu `user_enable = False`: Không tạo worker

- **User được cập nhật:**
  - `user_enable` thay đổi `False → True`: Worker được khởi động
  - `user_enable` thay đổi `True → False`: Worker bị dừng
  - `user_url` thay đổi: Worker được khởi động lại với URL mới
  - `is_premium` thay đổi: Ghi log, tool access được cập nhật

- **User bị xóa:**
  - Worker tự động bị dừng và xóa
  - Tài nguyên được giải phóng

### Cấu hình Polling Interval:

Mặc định kiểm tra database mỗi 5 giây. Để thay đổi, chỉnh sửa trong `main.py`:

```python
db_monitor = monitor(wm, poll_interval=10)  # 10 giây
```

---

## Cấu trúc Database

### Bảng Users
- `user_id`: ID tự động tăng
- `user_email`: Email người dùng (unique)
- `user_url`: WebSocket URL kết nối (unique)
- `user_enable`: Trạng thái kích hoạt
- `is_premium`: Trạng thái premium
- `last_update`: Thời gian cập nhật cuối

### Bảng Tools
- `tool_id`: ID tự động tăng
- `tool_name`: Tên công cụ (unique)
- `tool_enable`: Trạng thái kích hoạt
- `is_premium`: Yêu cầu premium
- `last_update`: Thời gian cập nhật cuối

### Bảng Connection
- Quan hệ nhiều-nhiều giữa Users và Tools
- Quản lý quyền truy cập công cụ của từng user

---

## Logging

Tất cả logs được lưu trong `data/logs/`:
- Chi tiết về worker lifecycle (start, stop, restart)
- Database changes được phát hiện
- Errors và exceptions
- Admin actions

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
