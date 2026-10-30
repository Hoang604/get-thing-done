# Nguyên tắc làm việc của Repository (Working Principles)

## 1. Kiểm thử (Tests)
- Chạy kiểm thử: `python3 -m unittest`.
- **Tuyệt đối không chạy test** khi chỉ thao tác hoặc chỉnh sửa các file Markdown (`.md`) và script (`.sh`).
- **Nguyên lý kiểm thử (4 tiêu chuẩn REAL test)**: Mọi bài test viết ra phải đạt chuẩn **REAL** theo cả 4 nguyên tắc sau:
  1. **Contract**: Bài test bảo vệ một quy tắc mà code cam kết với bên gọi hoặc bên đọc đầu ra trên mọi đầu vào hợp lệ. Phát biểu được cam kết đó trong một câu mà không trích dẫn giá trị literal của test; nếu chỉ lặp lại giá trị kỳ vọng cố định hoặc ghim cứng câu chữ tĩnh thì đó là ghim kết quả (pinning outcome), không phải test hợp đồng.
  2. **Kills a mutant**: Một chỉnh sửa hợp lý trên một dòng code sản phẩm (`file:line`, old → new) làm gãy quy tắc ở mục 1 phải được logic sản phẩm dẫn truyền tới assertion và làm test đỏ, mà chưa có bài test REAL nào khác trong phạm vi giết trực tiếp. Mọi phần kết quả do quy tắc mục 1 quyết định phải được kiểm tra để không lọt **surviving mutant**.
  3. **Survives refactors**: Mọi chỉnh sửa giữ nguyên hợp đồng đều phải giữ cho test xanh. Assertion chỉ được quan sát những gì hợp đồng cam kết; bất kỳ chi tiết nội bộ hay câu chữ tĩnh nào được phép thay đổi khi refactor đều không được ghim vào test.
  4. **Reaches the product**: Bài test đi vào code sản phẩm giống hệt cách caller thực tế gọi, bắt đầu từ trạng thái mà luồng thật tạo ra, và chỉ dùng stand-in có trạng thái (stateful contract) tại biên ngoài tiến trình (out-of-process) thay vì mock đếm lời gọi.

## 2. Nguyên tắc Single Source of Truth (SSoT)
- **Phạm vi thư mục nguồn gốc (`.gemini/antigravity-cli/`)**: Thư mục này CHỈ chứa duy nhất nguồn của **Skills** (`skills/`) và **Custom Subagents** (`agents/`), tuyệt đối không chứa bất cứ thứ gì khác (không chứa file `.sh`, không chứa hook hay cấu hình nào khác).
- **Không sửa thủ công ở thư mục đích**: Các thư mục như `.gemini/config/` hay `.agents/` là nơi nhận đồng bộ/đóng gói; không chỉnh sửa trực tiếp skills và subagents tại các thư mục này để tránh xung đột và ghi đè dữ liệu.
- **Quy tắc file duy nhất (Không kiểm tra trùng lặp)**: Tất cả các file không phải là skill (bao gồm script, cấu hình, hook, templates...) luôn chỉ có một bản duy nhất trong repository; **tuyệt đối không tìm kiếm hay kiểm tra xem có nhiều bản khác nhau hay không**.

## 3. Quản lý Kỹ năng (Skills Management)
Khi được yêu cầu tạo hoặc chỉnh sửa skill:
- **Chỉ chỉnh sửa file nguồn** trong `.gemini/antigravity-cli/` (thư mục `.gemini/antigravity-cli/skills/<skill-name>/`).
- **Quy tắc đặt và nối file Reference (`references/`)**:
  - Đặt file reference của skill tại `.gemini/antigravity-cli/skills/<skill-name>/references/<ref-name>.md`.
  - Khi nối reference vào `SKILL.md`, viết trực tiếp câu context pointer dùng đường dẫn tương đối `references/<ref-name>.md` theo mẫu `**When** [condition], read \`references/<ref-name>.md\` to [goal].` (hoặc `<skill-dir>/references/<ref-name>.md` khi truyền đường dẫn cho subagent).
  - **Tuyệt đối không dùng đường dẫn tuyệt đối** và **không chạy lệnh lùng sục (`fd`, `rg`) hay đọc các skill khác để dò cách viết**.
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

