# Tests

Use `python3 -m unittest` to run tests.

# Skills Management

Khi được yêu cầu tạo hoặc chỉnh sửa skill:
- **Chỉ chỉnh sửa file nguồn** trong `.gemini/antigravity-cli/` (thư mục `.gemini/antigravity-cli/skills/`).
- **Tự động đồng bộ**: Chạy script `./sync_workflows.sh` để tự động đồng bộ sang `.gemini/config/skills/` và `.agents/skills/`.
- **Không chỉnh sửa thủ công** ở các thư mục đích để tránh phải sửa nhiều file trùng lặp.
