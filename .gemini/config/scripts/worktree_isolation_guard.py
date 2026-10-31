#!/usr/bin/env python3
import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

from compact_threshold_tracker import sanitize_id
from skill_usage_tracker import extract_invoked_skill

DEFAULT_STATE_DIR: Path = Path("/tmp/agy_worktree_state")

TOOL_PATH_KEYS: tuple[str, ...] = (
    "Path",
    "TargetFile",
    "FilePath",
    "DirectoryPath",
    "SearchPath",
    "Cwd",
)

ALLOWED_MAIN_REPO_READ_DIRS: tuple[str, ...] = (
    ".gemini",
    ".agents",
    ".agent",
    "_agents",
    "_agent",
    ".claude",
)

GIT_WORKTREE_ADD_RE: re.Pattern[str] = re.compile(r"\bgit\b.*?\bworktree\s+add\b")
GIT_WORKTREE_REMOVE_RE: re.Pattern[str] = re.compile(r"\bgit\b.*?\bworktree\s+remove\b")


@dataclass(frozen=True)
class WorktreeIsolationState:
    conversation_id: str
    main_root: str
    worktree_path: str


def state_file_path(state_dir: Path, conv_id: str) -> Path:
    clean_id: str = sanitize_id(conv_id if conv_id else "default")
    return state_dir / f"{clean_id}.json"


def load_isolation_state(
    state_dir: Path, conv_id: str
) -> WorktreeIsolationState | None:
    path: Path = state_file_path(state_dir, conv_id)
    if not path.is_file():
        return None
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None
    if not isinstance(raw, dict):
        return None
    main_root_raw: object = raw.get("main_root")
    wt_path_raw: object = raw.get("worktree_path")
    if not isinstance(main_root_raw, str) or not isinstance(wt_path_raw, str):
        return None
    main_root: str = main_root_raw.strip()
    wt_path: str = wt_path_raw.strip()
    if not main_root or not wt_path:
        return None
    wt_resolved: Path = Path(wt_path)
    if not wt_resolved.is_dir():
        clear_isolation_state(state_dir, conv_id)
        return None
    return WorktreeIsolationState(
        conversation_id=sanitize_id(conv_id if conv_id else "default"),
        main_root=str(Path(main_root).resolve()),
        worktree_path=str(wt_resolved.resolve()),
    )


def save_isolation_state(state_dir: Path, state: WorktreeIsolationState) -> None:
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        target: Path = state_file_path(state_dir, state.conversation_id)
        tmp: Path = target.with_suffix(".json.tmp")
        payload: dict[str, str] = {
            "conversation_id": state.conversation_id,
            "main_root": state.main_root,
            "worktree_path": state.worktree_path,
        }
        tmp.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        os.replace(tmp, target)
    except Exception:
        pass


def clear_isolation_state(state_dir: Path, conv_id: str) -> None:
    try:
        target: Path = state_file_path(state_dir, conv_id)
        if target.exists():
            target.unlink()
    except Exception:
        pass


def extract_main_workspace_root(
    payload: dict[str, object], fallback_cwd: Path | None = None
) -> Path:
    ws_paths: object = payload.get("workspacePaths")
    if isinstance(ws_paths, list):
        for item in ws_paths:
            if isinstance(item, str) and item.strip():
                return Path(os.path.expanduser(item.strip())).resolve()
    for key in ("workspacePath", "cwd", "project_dir"):
        val: object = payload.get(key)
        if isinstance(val, str) and val.strip():
            return Path(os.path.expanduser(val.strip())).resolve()
    base: Path = fallback_cwd if fallback_cwd is not None else Path.cwd()
    return base.resolve()


def _split_shell_segments(cmd: str) -> list[str]:
    return [seg.strip() for seg in re.split(r"&&|\|\||;|\n", cmd) if seg.strip()]


def _resolve_shell_vars(token: str, env_vars: dict[str, str]) -> str:
    out: str = token
    for k, v in env_vars.items():
        out = out.replace(f"${{{k}}}", v).replace(f"${k}", v)
    return out


def _collect_simple_shell_vars(segments: list[str]) -> dict[str, str]:
    env_vars: dict[str, str] = {}
    assign_re: re.Pattern[str] = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
    for seg in segments:
        try:
            tokens: list[str] = shlex.split(seg, posix=True)
        except ValueError:
            continue
        if not tokens:
            continue
        for tok in tokens:
            m: re.Match[str] | None = assign_re.match(tok)
            if m is None:
                break
            var_name: str = m.group(1)
            raw_val: str = _resolve_shell_vars(m.group(2), env_vars)
            env_vars[var_name] = raw_val
    return env_vars


def parse_git_worktree_add_target(
    command_line: str, base_dir: Path
) -> Path | None:
    if not GIT_WORKTREE_ADD_RE.search(command_line):
        return None
    segments: list[str] = _split_shell_segments(command_line)
    env_vars: dict[str, str] = _collect_simple_shell_vars(segments)
    current_dir: Path = base_dir

    for seg in segments:
        try:
            tokens: list[str] = shlex.split(seg, posix=True)
        except ValueError:
            continue
        if not tokens:
            continue
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=.*$", tokens[0]):
            tokens.pop(0)
        if not tokens:
            continue

        if tokens[0] == "cd" and len(tokens) >= 2:
            cd_target_str: str = _resolve_shell_vars(tokens[1], env_vars)
            cd_path: Path = Path(os.path.expanduser(cd_target_str))
            current_dir = (
                cd_path.resolve()
                if cd_path.is_absolute()
                else (current_dir / cd_path).resolve()
            )
            continue

        if tokens[0] == "rtk" and len(tokens) >= 2 and tokens[1] == "git":
            tokens = tokens[1:]

        if tokens[0] != "git":
            continue

        git_base: Path = current_dir
        idx: int = 1
        while idx < len(tokens):
            tok: str = tokens[idx]
            if tok == "-C" and idx + 1 < len(tokens):
                c_str: str = _resolve_shell_vars(tokens[idx + 1], env_vars)
                c_path: Path = Path(os.path.expanduser(c_str))
                git_base = (
                    c_path.resolve()
                    if c_path.is_absolute()
                    else (git_base / c_path).resolve()
                )
                idx += 2
                continue
            if tok == "worktree" and idx + 1 < len(tokens) and tokens[idx + 1] == "add":
                idx += 2
                positional: list[str] = []
                while idx < len(tokens):
                    arg: str = tokens[idx]
                    if arg in ("-b", "-B", "--orphan") and idx + 1 < len(tokens):
                        idx += 2
                        continue
                    if arg.startswith("-"):
                        idx += 1
                        continue
                    positional.append(_resolve_shell_vars(arg, env_vars))
                    idx += 1
                if positional:
                    wt_raw: str = positional[0]
                    wt_p: Path = Path(os.path.expanduser(wt_raw))
                    return (
                        wt_p.resolve()
                        if wt_p.is_absolute()
                        else (git_base / wt_p).resolve()
                    )
                break
            idx += 1
    return None


def is_git_worktree_remove_for_target(
    command_line: str, worktree_path: Path, base_dir: Path
) -> bool:
    if not GIT_WORKTREE_REMOVE_RE.search(command_line):
        return False
    segments: list[str] = _split_shell_segments(command_line)
    env_vars: dict[str, str] = _collect_simple_shell_vars(segments)
    current_dir: Path = base_dir

    for seg in segments:
        try:
            tokens: list[str] = shlex.split(seg, posix=True)
        except ValueError:
            continue
        if not tokens:
            continue
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=.*$", tokens[0]):
            tokens.pop(0)
        if not tokens:
            continue

        if tokens[0] == "cd" and len(tokens) >= 2:
            cd_target_str: str = _resolve_shell_vars(tokens[1], env_vars)
            cd_path: Path = Path(os.path.expanduser(cd_target_str))
            current_dir = (
                cd_path.resolve()
                if cd_path.is_absolute()
                else (current_dir / cd_path).resolve()
            )
            continue

        if tokens[0] == "rtk" and len(tokens) >= 2 and tokens[1] == "git":
            tokens = tokens[1:]

        if tokens[0] != "git":
            continue

        git_base: Path = current_dir
        idx: int = 1
        while idx < len(tokens):
            tok: str = tokens[idx]
            if tok == "-C" and idx + 1 < len(tokens):
                c_str: str = _resolve_shell_vars(tokens[idx + 1], env_vars)
                c_path: Path = Path(os.path.expanduser(c_str))
                git_base = (
                    c_path.resolve()
                    if c_path.is_absolute()
                    else (git_base / c_path).resolve()
                )
                idx += 2
                continue
            if (
                tok == "worktree"
                and idx + 1 < len(tokens)
                and tokens[idx + 1] == "remove"
            ):
                idx += 2
                while idx < len(tokens):
                    arg: str = tokens[idx]
                    if arg.startswith("-"):
                        idx += 1
                        continue
                    resolved_arg: str = _resolve_shell_vars(arg, env_vars)
                    cand: Path = Path(os.path.expanduser(resolved_arg))
                    cand_resolved: Path = (
                        cand.resolve()
                        if cand.is_absolute()
                        else (git_base / cand).resolve()
                    )
                    if cand_resolved == worktree_path.resolve():
                        return True
                    idx += 1
                break
            idx += 1
    return False


def _is_subpath(candidate: Path, parent: Path) -> bool:
    try:
        candidate.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _is_allowed_main_repo_customization(
    target_path: Path, main_root: Path, is_read_only: bool
) -> bool:
    if not is_read_only:
        return False
    try:
        rel: Path = target_path.resolve().relative_to(main_root.resolve())
    except ValueError:
        return False
    parts: tuple[str, ...] = rel.parts
    if not parts:
        return False
    return parts[0] in ALLOWED_MAIN_REPO_READ_DIRS


def _command_enters_worktree(
    command_line: str, main_root: Path, worktree_path: Path
) -> bool:
    segments: list[str] = _split_shell_segments(command_line)
    if not segments:
        return False
    env_vars: dict[str, str] = _collect_simple_shell_vars(segments)

    for seg in segments:
        try:
            tokens: list[str] = shlex.split(seg, posix=True)
        except ValueError:
            return False
        if not tokens:
            continue
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=.*$", tokens[0]):
            tokens.pop(0)
        if not tokens:
            continue

        if tokens[0] == "cd" and len(tokens) >= 2:
            raw_target: str = _resolve_shell_vars(tokens[1], env_vars)
            cand: Path = Path(os.path.expanduser(raw_target))
            resolved: Path = (
                cand.resolve()
                if cand.is_absolute()
                else (main_root / cand).resolve()
            )
            return _is_subpath(resolved, worktree_path)

        if tokens[0] == "rtk" and len(tokens) >= 2 and tokens[1] == "git":
            tokens = tokens[1:]

        if tokens[0] == "git" and len(tokens) >= 3 and tokens[1] == "-C":
            raw_c: str = _resolve_shell_vars(tokens[2], env_vars)
            cand_c: Path = Path(os.path.expanduser(raw_c))
            resolved_c: Path = (
                cand_c.resolve()
                if cand_c.is_absolute()
                else (main_root / cand_c).resolve()
            )
            return _is_subpath(resolved_c, worktree_path)

        return False
    return False


def _command_references_outside_main_repo(
    command_line: str, main_root: Path, worktree_path: Path
) -> Path | None:
    segments: list[str] = _split_shell_segments(command_line)
    env_vars: dict[str, str] = _collect_simple_shell_vars(segments)
    main_resolved: Path = main_root.resolve()
    wt_resolved: Path = worktree_path.resolve()

    for seg in segments:
        try:
            tokens: list[str] = shlex.split(seg, posix=True)
        except ValueError:
            continue
        for raw_tok in tokens:
            if "=" in raw_tok and not raw_tok.startswith("/"):
                _, raw_tok = raw_tok.split("=", 1)
            resolved_tok: str = _resolve_shell_vars(raw_tok, env_vars)
            if not resolved_tok.startswith("/"):
                continue
            cand: Path = Path(resolved_tok).resolve()
            if cand == main_resolved:
                continue
            if _is_subpath(cand, wt_resolved):
                continue
            if _is_subpath(cand, main_resolved):
                if _is_allowed_main_repo_customization(cand, main_resolved, True):
                    continue
                return cand
    return None


def evaluate_pre_tool_use(
    payload: dict[str, object],
    state_dir: Path = DEFAULT_STATE_DIR,
    fallback_cwd: Path | None = None,
) -> dict[str, object]:
    conv_id_obj: object = payload.get("conversationId")
    conv_id: str = conv_id_obj if isinstance(conv_id_obj, str) else "default"

    state: WorktreeIsolationState | None = load_isolation_state(state_dir, conv_id)
    if state is None:
        return {"decision": "allow"}

    main_root: Path = Path(state.main_root)
    worktree_path: Path = Path(state.worktree_path)

    tool_call_obj: object = payload.get("toolCall")
    if not isinstance(tool_call_obj, dict):
        return {"decision": "allow"}

    tool_name_obj: object = tool_call_obj.get("name")
    tool_name: str = tool_name_obj if isinstance(tool_name_obj, str) else ""
    args_obj: object = tool_call_obj.get("args")
    args: dict[str, object] = args_obj if isinstance(args_obj, dict) else {}

    if tool_name == "read_file":
        invoked_skill: str | None = extract_invoked_skill(payload)
        if invoked_skill == "finishing-a-development-branch":
            return {"decision": "allow"}

    is_read_only_tool: bool = tool_name in ("read_file", "view_file")

    for key in TOOL_PATH_KEYS:
        raw_val: object = args.get(key)
        if not isinstance(raw_val, str) or not raw_val.strip():
            continue
        p: Path = Path(os.path.expanduser(raw_val.strip()))
        resolved_p: Path = (
            p.resolve() if p.is_absolute() else (main_root / p).resolve()
        )
        if _is_subpath(resolved_p, worktree_path):
            continue
        if _is_subpath(resolved_p, main_root):
            if _is_allowed_main_repo_customization(
                resolved_p, main_root, is_read_only_tool
            ):
                continue
            try:
                rel_to_main: Path = resolved_p.relative_to(main_root)
                suggested_path: Path = worktree_path / rel_to_main
            except ValueError:
                suggested_path = worktree_path
            return {
                "decision": "deny",
                "reason": (
                    f"BLOCKED (Worktree Isolation): This session is isolated to worktree "
                    f"'{worktree_path}'. Accessing main repository path '{resolved_p}' via "
                    f"'{tool_name}' is prohibited. Target the worktree path instead: "
                    f"'{suggested_path}'."
                ),
            }

    if tool_name == "run_command":
        cmd_obj: object = args.get("CommandLine")
        cmd: str = cmd_obj.strip() if isinstance(cmd_obj, str) else ""
        if not cmd:
            return {"decision": "allow"}

        if is_git_worktree_remove_for_target(cmd, worktree_path, main_root):
            return {"decision": "allow"}

        if not _command_enters_worktree(cmd, main_root, worktree_path):
            return {
                "decision": "deny",
                "reason": (
                    f"BLOCKED (Worktree Isolation): Each 'run_command' starts in a fresh shell "
                    f"at '{main_root}', while this session is isolated to worktree "
                    f"'{worktree_path}'. Prefix your command with: "
                    f'cd "{worktree_path}" && ...'
                ),
            }

        leaked_main_path: Path | None = _command_references_outside_main_repo(
            cmd, main_root, worktree_path
        )
        if leaked_main_path is not None:
            try:
                rel_leak: Path = leaked_main_path.relative_to(main_root.resolve())
                suggested_cmd_path: Path = worktree_path.resolve() / rel_leak
            except ValueError:
                suggested_cmd_path = worktree_path.resolve()
            return {
                "decision": "deny",
                "reason": (
                    f"BLOCKED (Worktree Isolation): Command references main repository path "
                    f"'{leaked_main_path}' outside active worktree '{worktree_path}'. "
                    f"Use '{suggested_cmd_path}' instead."
                ),
            }

    return {"decision": "allow"}


def handle_post_tool_use(
    payload: dict[str, object],
    state_dir: Path = DEFAULT_STATE_DIR,
    fallback_cwd: Path | None = None,
) -> dict[str, object]:
    error_val: object = payload.get("error")
    if isinstance(error_val, str) and error_val.strip():
        return {}

    conv_id_obj: object = payload.get("conversationId")
    conv_id: str = conv_id_obj if isinstance(conv_id_obj, str) else "default"

    tool_call_obj: object = payload.get("toolCall")
    if not isinstance(tool_call_obj, dict):
        return {}

    tool_name_obj: object = tool_call_obj.get("name")
    tool_name: str = tool_name_obj if isinstance(tool_name_obj, str) else ""
    args_obj: object = tool_call_obj.get("args")
    args: dict[str, object] = args_obj if isinstance(args_obj, dict) else {}

    if tool_name == "read_file":
        skill_name: str | None = extract_invoked_skill(payload)
        if skill_name == "finishing-a-development-branch":
            clear_isolation_state(state_dir, conv_id)
        return {}

    if tool_name == "run_command":
        cmd_obj: object = args.get("CommandLine")
        cmd: str = cmd_obj.strip() if isinstance(cmd_obj, str) else ""
        if not cmd:
            return {}

        main_root: Path = extract_main_workspace_root(payload, fallback_cwd)

        existing: WorktreeIsolationState | None = load_isolation_state(
            state_dir, conv_id
        )
        if existing is not None:
            if is_git_worktree_remove_for_target(
                cmd, Path(existing.worktree_path), main_root
            ) or not Path(existing.worktree_path).is_dir():
                clear_isolation_state(state_dir, conv_id)
                return {}

        added_wt: Path | None = parse_git_worktree_add_target(cmd, main_root)
        if added_wt is not None and added_wt.is_dir():
            save_isolation_state(
                state_dir,
                WorktreeIsolationState(
                    conversation_id=sanitize_id(conv_id if conv_id else "default"),
                    main_root=str(main_root.resolve()),
                    worktree_path=str(added_wt.resolve()),
                ),
            )

    return {}


def main() -> None:
    mode: str = sys.argv[1] if len(sys.argv) > 1 else "pre"
    try:
        raw_input: str = sys.stdin.read()
        payload: object = json.loads(raw_input) if raw_input.strip() else {}
    except Exception:
        if mode == "post":
            print(json.dumps({}))
        else:
            print(json.dumps({"decision": "allow"}))
        return

    if not isinstance(payload, dict):
        if mode == "post":
            print(json.dumps({}))
        else:
            print(json.dumps({"decision": "allow"}))
        return

    if mode == "post":
        res: dict[str, object] = handle_post_tool_use(payload)
    else:
        res = evaluate_pre_tool_use(payload)

    print(json.dumps(res))


if __name__ == "__main__":
    main()
