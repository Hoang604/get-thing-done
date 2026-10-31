# Nguyên tắc làm việc của Repository (Working Principles)

## 1. Kiểm thử (Tests)
- Chạy kiểm thử: `python3 -m unittest`.
- **Tuyệt đối không chạy test** khi chỉ thao tác hoặc chỉnh sửa các file Markdown (`.md`) và script (`.sh`).
- **Nguyên lý kiểm thử (4 tiêu chuẩn REAL test)**: Mọi bài test viết ra phải đạt chuẩn **REAL** theo cả 4 nguyên tắc sau:
  1. **Contract**: Bài test bảo vệ một quy tắc mà code cam kết với bên gọi hoặc bên đọc đầu ra trên mọi đầu vào hợp lệ. Phát biểu được cam kết đó trong một câu mà không trích dẫn giá trị literal của test; nếu chỉ lặp lại giá trị kỳ vọng cố định hoặc ghim cứng câu chữ tĩnh thì đó là ghim kết quả (pinning outcome), không phải test hợp đồng.
  2. **Kills a mutant**: Một chỉnh sửa hợp lý trên một dòng code sản phẩm (`file:line`, old → new) làm gãy quy tắc ở mục 1 phải được logic sản phẩm dẫn truyền tới assertion và làm test đỏ, mà chưa có bài test REAL nào khác trong phạm vi giết trực tiếp. Mọi phần kết quả do quy tắc mục 1 quyết định phải được kiểm tra để không lọt **surviving mutant**.
  3. **Survives refactors**: Mọi chỉnh sửa giữ nguyên hợp đồng đều phải giữ cho test xanh. Assertion chỉ được quan sát những gì hợp đồng cam kết; bất kỳ chi tiết nội bộ hay câu chữ tĩnh nào được phép thay đổi khi refactor đều không được ghim vào test.
  4. **Reaches the product**: Bài test đi vào code sản phẩm giống hệt cách caller thực tế gọi, bắt đầu từ trạng thái mà luồng thật tạo ra, và chỉ dùng stand-in có trạng thái (stateful contract) tại biên ngoài tiến trình (out-of-process) thay vì mock đếm lời gọi.

## 2. Nguyên tắc Single Source of Truth (SSoT) & Đồng bộ
- **When** tạo hoặc chỉnh sửa **Skill** (`.gemini/antigravity-cli/skills/<skill-name>/`), **Custom Subagent** (`.gemini/antigravity-cli/agents/<name>.md` hoặc `.gemini/antigravity-cli/agents/<name>/agent.md`), hoặc **Global Instructions** (`.gemini/GEMINI.md`), chỉ chỉnh sửa duy nhất tại file nguồn tương ứng rồi chạy `./sync_workflows.sh` để đồng bộ sang `.gemini/config/` và `.agents/`. **Tuyệt đối không** chỉnh sửa trực tiếp các file đích trong `.gemini/config/` hoặc `.agents/` (kể cả khi khôi phục hay cập nhật lại một thay đổi vừa sửa ở nguồn), và **tuyệt đối không** đặt bất kỳ file nào ngoài `skills/` và `agents/` (như `.sh`, hook, cấu hình) vào `.gemini/antigravity-cli/`.
- **When** lưu hoặc cập nhật quy tắc làm việc, chỉ ghi các quy tắc đặc thù của repository này vào `GEMINI.md` ở thư mục gốc của repo; **tuyệt đối không** ghi quy tắc riêng của repository này vào `.gemini/GEMINI.md` (vì `.gemini/GEMINI.md` là bộ quy tắc toàn cục được `./sync_workflows.sh` trích xuất sang `.agents/AGENTS.md` và được `./install.sh` cài đặt vào `~/.gemini/GEMINI.md`).
- **When** thao tác với bất kỳ file nào không nằm trong luồng đồng bộ của `./sync_workflows.sh` (như script, cấu hình, hook, template), thao tác trực tiếp trên bản duy nhất đó; **tuyệt đối không** tìm kiếm hay kiểm tra xem có nhiều bản khác nhau trong repository hay không.

## 3. Quản lý Kỹ năng (Skills Management)
- **When** đặt hoặc nối file tham chiếu cho một skill, đặt file tại `.gemini/antigravity-cli/skills/<skill-name>/references/<ref-name>.md` và viết trực tiếp câu context pointer trong `SKILL.md` dùng đường dẫn tương đối theo mẫu `**When** [condition], read \`references/<ref-name>.md\` to [goal].` (hoặc `<skill-dir>/references/<ref-name>.md` khi truyền đường dẫn cho subagent). **Tuyệt đối không** dùng đường dẫn tuyệt đối và **không** chạy lệnh lùng sục (`fd`, `rg`) hay đọc các skill khác để dò cách viết.

## 4. Phạm vi Chỉnh sửa (Edit Scope)
- **When** thực hiện một yêu cầu chỉnh sửa, chỉ thay đổi đúng những phần của file trực tiếp thực hiện yêu cầu đó và giữ nguyên từng chữ của mọi phần còn lại. **Tuyệt đối không** nhân tiện đang sửa file mà tự ý sửa thêm bất kỳ phần nào người dùng chưa yêu cầu — kể cả những vấn đề đã được phát hiện hay thảo luận ở các lượt trước nhưng chưa có lệnh sửa, hoặc các khái niệm và câu chữ nằm cạnh vùng đang sửa nhưng không thuộc đối tượng mà yêu cầu chỉ định.

## 5. Cài đặt và Phân phối (Installation)
- Sử dụng script `./install.sh` để cài đặt toàn bộ GTD framework (skills, scripts, subagents, hooks, statusline) vào môi trường máy tính (`~/.gemini/` và `~/.agents/`).

