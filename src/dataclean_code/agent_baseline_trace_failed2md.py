import json
import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common_scaffold.db_utils.loader import query_db
from common_scaffold.agent_tools import (
    list_dbs,
    transform_tool_args,
    generate_var_name,
    execute_python,
    build_messages,
    get_tools_spec,
    VariableStore,
    format_preview,
    auto_ensure_databases,
    validate_and_log,
)
import textwrap
# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
query_dir = Path(__file__).parent / "query3"
deployment_name = "o3"

load_dotenv()

# ----------------------------------------------------------------------
# TraceRecorder
# ----------------------------------------------------------------------

class TraceRecorder:
    def __init__(self, path="agent_trace.md"):
        self.path = path
        self.lines = []
        self._last_messages = None

    def log_user(self, text: str):
        self.lines.append(f"🧑 **User:**\n{text.strip()}\n\n")

    def log_assistant(self, text: str):
        self.lines.append(f"🤖 **Agent:**\n{text.strip()}\n\n")

    def log_final_answer(self, answer: str):
        self.lines.append(f"\n✅ Final Answer:\n{answer}\n")

    def log_tool_result(self, tool_name, result):
        self.lines.append(f"📄 **Tool Result: {tool_name}**\n")
        self.lines.append(_format_tool_result_block(result))
        self.lines.append("\n")

    def set_history(self, messages):
        normed = []
        for msg in messages:
            normed.append(msg if isinstance(msg, dict) else msg.model_dump())
        self._last_messages = normed

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            if self._last_messages:
                f.write(self._render_history_readable(self._last_messages))
            for line in self.lines:
                f.write(line)
        print(f"📄 Trace saved to {self.path}")

    def _render_history_readable(self, messages):
        out = ["📜 **Full Message History (Readable)**\n"]
        for idx, msg in enumerate(messages, start=1):
            out.append(f"\n## 🪜 Step {idx}\n\n{'-' * 80}\n")
            out.append(_render_single_message(msg))
        out.append("\n\n---\n\n")
        return "".join(out)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _parse_possible_json(s: str):
    if not isinstance(s, str):
        return None
    try:
        return json.loads(s.strip())
    except Exception:
        return None

def _dump_yaml(obj) -> str:
    try:
        return yaml.safe_dump(obj, sort_keys=False, allow_unicode=True).rstrip()
    except Exception:
        return json.dumps(obj, indent=2, ensure_ascii=False)

def _dedent_text(text: str) -> str:
    return textwrap.dedent(text.strip()) + "\n"

def _indent_block(text: str, n_spaces: int) -> str:
    pad = " " * n_spaces
    if not text.endswith("\n"):
        text += "\n"
    return "".join(pad + line if line.strip() else "\n" for line in text.splitlines(keepends=True))

def _try_decode_code_string(v: str) -> str:
    try:
        if "\\n" in v:
            return bytes(v, "utf-8").decode("unicode_escape")
        return v
    except Exception:
        return v

def _detect_code_language(text: str) -> str:
    t = text.lstrip().lower()
    if t.startswith("select") or "\nselect " in t:
        return "sql"
    if "def " in t or "import " in t or "pd." in t or "print(" in t:
        return "python"
    return ""

def _format_tool_result_block(result) -> str:
    if isinstance(result, str):
        return _dedent_text(result)

    if isinstance(result, list) and result and all(isinstance(r, dict) for r in result):
        cols = list(result[0].keys())
        lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
        for row in result:
            lines.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")
        return "\n".join(lines) + "\n"

    return _dump_yaml(result) + "\n"

def _render_single_message(msg: dict) -> str:
    lines = []
    role = msg.get("role", "unknown")
    lines.append(f"role: {role}\n")

    if role == "tool":
        lines.append("\n")
        lines.append(_render_tool_content(msg.get("content")))
    elif "content" in msg:
        content = msg["content"]
        lines.append("\n")
        if content is None:
            lines.append("content: null\n")
        elif role == "system":
            lines.append("content:\n")
            lines.append(_indent_block(_dedent_text(content), 2))
            lines.append("\n")
        else:
            parsed = _parse_possible_json(content)
            if parsed is not None:
                lines.append("content (parsed):\n")
                lines.append(_indent_block(_dump_yaml(parsed), 2))
                lines.append("\n")
            else:
                lang = _detect_code_language(content)
                if lang:
                    fenced = f"```{lang}\n{_dedent_text(content).strip()}\n```"
                    lines.append("content:\n")
                    lines.append(_indent_block(fenced, 2))
                    lines.append("\n")
                else:
                    lines.append("content:\n")
                    lines.append(_indent_block(content, 2))
                    lines.append("\n")

    if "tool_calls" in msg and msg["tool_calls"]:
        lines.append("tool_calls:\n")
        for call in msg["tool_calls"]:
            cid = call.get("id")
            ctype = call.get("type")
            fn = call.get("function", {})
            fname = fn.get("name")
            fargs_raw = fn.get("arguments", "")

            lines.append(_indent_block(f"- id: {cid}", 2))
            lines.append(_indent_block(f"type: {ctype}", 4))
            lines.append(_indent_block("function:", 4))
            lines.append(_indent_block(f"name: {fname}", 6))
            lines.append(_indent_block("arguments:", 6))

            parsed_args = _parse_possible_json(fargs_raw)
            if parsed_args is not None and isinstance(parsed_args, dict):
                for k, v in parsed_args.items():
                    lines.append(_indent_block(f"{k}:", 8))
                    if isinstance(v, str) and ("\\n" in v or "\n" in v):
                        decoded = _try_decode_code_string(v)
                        lines.append("\n")
                        lines.append(_indent_block(_dedent_text(decoded), 10))
                        lines.append("\n")
                    else:
                        lines.append(_indent_block(_dump_yaml(v), 10))
            else:
                lines.append(_indent_block(_dedent_text(fargs_raw), 8))
            lines.append("\n")

    for k in ("tool_call_id", "name"):
        if k in msg:
            lines.append(f"{k}: {msg[k]}\n")

    for k, v in msg.items():
        if k not in ("role", "content", "tool_calls", "tool_call_id", "name"):
            lines.append(f"{k}: {v}\n\n")  

    return "".join(lines)


def _render_tool_content(content: str) -> str:
    lines = []
    if content is None:
        return "content: null\n"

    parsed = _parse_possible_json(content)
    if parsed is None:
        lines.append("content:\n")
        lines.append("\n")
        lines.append(_indent_block(_dedent_text(content), 2))
        return "".join(lines)

    avail = parsed.get("available_variables")
    rvar = parsed.get("result_variable")
    preview = parsed.get("result_preview")

    lines.append("content:\n")
    lines.append("\n")
    lines.append(_indent_block(f"available_variables: {_dump_yaml(avail) if avail is not None else 'null'}", 2))
    lines.append(_indent_block(f"result_variable: {rvar}", 2))
    lines.append(_indent_block("result_preview:", 2))

    if preview is not None:
        try:
            parsed_preview = json.loads(preview)
            compact = json.dumps(parsed_preview, ensure_ascii=False, indent=2)
            lines.append("\n")
            lines.append(_indent_block(compact + "\n", 4))
        except Exception:
            lines.append(_indent_block(_try_decode_code_string(preview).strip(), 4))
    else:
        lines.append(_indent_block("null", 4))

    return "".join(lines)

# -----------------------------------------------------------------------------
# Load query + DB config
# -----------------------------------------------------------------------------
with open(query_dir / "query.json") as f:
    query_content = json.load(f)

if isinstance(query_content, str):
    user_query = query_content
elif isinstance(query_content, dict) and "query" in query_content:
    user_query = query_content["query"]
else:
    raise ValueError("query.json wrong format")

with open("db_description.txt") as f:
    db_description = f.read()

project_dir = Path(__file__).parent
with open(project_dir / "db_config.yaml") as f:
    db_config = yaml.safe_load(f)
db_clients = db_config["db_clients"]

auto_ensure_databases(db_clients)
print(f"\n✅ DB connections ready: {db_clients.keys()}")


def list_dbs_tool(**tool_args):
    return list_dbs(tool_args["db_name"], db_clients)


client = AzureOpenAI(
    api_key=os.getenv("AZURE_API_KEY_o3"),
    api_version=os.getenv("AZURE_API_VERSION_o3", "2023-05-15"),
    azure_endpoint=os.getenv("AZURE_API_BASE_o3"),
)

messages = build_messages(user_query, db_description)

TOOLS = {
    "query_db": query_db,
    "list_dbs": list_dbs_tool,
    "execute_python": lambda code: execute_python(code, _vars),
    "return_answer": lambda **kwargs: return_answer(**kwargs),
}

tools_spec = get_tools_spec()


def call_llm(messages):
    resp = client.chat.completions.create(
        model=deployment_name,
        messages=messages,
        tools=tools_spec,
    )
    assistant_msg = resp.choices[0].message
    print(f"\n💬 LLM response:\n{assistant_msg}\n")

    if assistant_msg.tool_calls:
        tool_call = assistant_msg.tool_calls[0]
        tool_call_id = tool_call.id
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        if isinstance(tool_args, dict) and "args" in tool_args:
            tool_args = tool_args["args"]
        return assistant_msg, tool_call_id, tool_name, tool_args

    if assistant_msg.content:
        try:
            obj = json.loads(assistant_msg.content)
            if isinstance(obj, dict) and obj.get("tool") == "return_answer" and "args" in obj:
                return assistant_msg, None, "return_answer", obj["args"]
        except Exception as e:
            print(f"⚠️ Failed to parse fallback content: {e}")

    raise ValueError("❌ LLM did not return any tool_calls or valid return_answer.")


def return_answer(answer: str):
    print(f"\n✅ Final Answer: {answer}")

    is_valid, reason = validate_and_log(query_dir, answer)

    if is_valid:
        print("✅ Validation passed!")
        recorder.log_assistant("✅ Validation passed!")
    else:
        print(f"❌ Validation failed: {reason}")
        recorder.log_assistant(f"❌ Validation failed: {reason}")

    recorder.log_final_answer(answer)
    recorder.save()
    sys.exit(0)


def run_agent_loop(messages, db_clients, _vars, recorder: TraceRecorder):
    step = 1

    # Log initial user query (human readable)
    recorder.log_user(user_query)

    while True:
        # Capture *current full* message list; overwritten each step (cheap)
        recorder.set_history(messages)

        assistant_msg, tool_call_id, tool_name, tool_args = call_llm(messages)

        if assistant_msg.content:
            # This is rarely used (agent freeform content), but record it
            recorder.log_user(assistant_msg.content)  # optional debugging

        print(f"🤖 Agent chose tool: {tool_name}")
        print(f"🔷 Args: {tool_args}")

        if tool_name == "return_answer":
            # record final full history again (just in case)
            recorder.set_history(messages + [assistant_msg])
            recorder.save()
            TOOLS[tool_name](**tool_args)
            break

        if tool_name not in TOOLS:
            raise ValueError(f"❌ Unknown tool: {tool_name}")

        if tool_name == "query_db":
            tool_args = transform_tool_args(tool_args, db_clients)

        result = TOOLS[tool_name](**tool_args)

        var_name = generate_var_name(tool_name, tool_args, step)
        _vars[var_name] = result

        print(f"📄 Tool result stored in `{var_name}`")

        preview = format_preview(result)

        messages.append(assistant_msg)
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": json.dumps(
                    {
                        "available_variables": list(_vars.keys()),
                        "result_variable": var_name,
                        "result_preview": preview[:10000],
                    }
                ),
            }
        )

        print(f"📄 Preview sent to LLM:\n{preview[:10000]}...\n")

        step += 1


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    _vars = VariableStore()
    recorder = TraceRecorder()
    try:
        success = run_agent_loop(messages, db_clients, _vars, recorder)
    except Exception as e:
        fail_reason = f"❌ Agent crashed: {type(e).__name__}: {e}"
        print(fail_reason)
        recorder.lines.append(fail_reason + "\n")
        recorder.save()
        success = False

    sys.exit(0 if success else 1)
