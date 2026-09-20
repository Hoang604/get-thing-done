# Nguyên tắc làm việc của Repository (Working Principles)

## 1. Kiểm thử (Tests)
- Chạy kiểm thử: `python3 -m unittest`.
- **Tuyệt đối không chạy test** khi chỉ thao tác hoặc chỉnh sửa các file Markdown (`.md`).

## 2. Nguyên tắc Single Source of Truth (SSoT)
- **Nguồn duy nhất**: Mọi cấu hình, kịch bản, quy tắc và kỹ năng tùy biến đều phải được khởi tạo hoặc chỉnh sửa tại thư mục nguồn gốc `.gemini/antigravity-cli/`.
- **Không sửa thủ công ở thư mục đích**: Các thư mục như `.gemini/config/` hay `.agents/` là nơi nhận đồng bộ/đóng gói; không chỉnh sửa trực tiếp tại các thư mục này để tránh xung đột và ghi đè dữ liệu.

## 3. Quản lý Kỹ năng (Skills Management)
Khi được yêu cầu tạo hoặc chỉnh sửa skill:
- **Chỉ chỉnh sửa file nguồn** trong `.gemini/antigravity-cli/` (thư mục `.gemini/antigravity-cli/skills/<skill-name>/`).
- **Tự động đồng bộ**: Chạy script `./sync_workflows.sh` để tự động đồng bộ sang `.gemini/config/skills/` và `.agents/skills/`.

## 4. Quản lý Custom Subagents
Khi tạo hoặc chỉnh sửa custom subagent:
- **Vị trí file nguồn**:
  - Đặt file định nghĩa subagent định dạng Markdown (`.md` có YAML frontmatter) tại thư mục nguồn: `.gemini/antigravity-cli/agents/<name>.md` (hoặc `.gemini/antigravity-cli/agents/<name>/agent.md`).
  - Đồng bộ sang `.gemini/config/agents/` (để cài đặt Global) và `.agents/agents/` (để dùng cho Workspace).
- **Cơ chế hoạt động với `install.sh`**:
  - Script `./install.sh` sẽ sao chép toàn bộ `.gemini/` vào `~/.gemini/`. Do đó, subagent trong `.gemini/config/agents/` sẽ tự động được cài đặt vào `~/.gemini/config/agents/<name>.md` — vị trí Antigravity tự động phát hiện subagent toàn cục (Global Custom Subagents).

## 5. Cài đặt và Phân phối (Installation)
- Sử dụng script `./install.sh` để cài đặt toàn bộ GTD framework (skills, scripts, subagents, hooks, statusline) vào môi trường máy tính (`~/.gemini/` và `~/.agents/`).

