import os
import re
from slpp import slpp as lua
from lupa import LuaRuntime

def extract_table_block(content, var_name):
    lines = content.splitlines()
    start_idx, end_idx = None, None
    brace_count = 0
    found = False
    table_lines = []

    for i, line in enumerate(lines):
        if not found and f"{var_name} =" in line:
            found = True
            start_idx = i
            brace_count += line.count("{") - line.count("}")
            table_lines.append(line.split("=", 1)[1].strip())
            continue

        if found:
            brace_count += line.count("{") - line.count("}")
            table_lines.append(line.strip())
            if brace_count == 0:
                end_idx = i
                break

    if not found or start_idx is None or end_idx is None:
        raise ValueError(f"Could not extract {var_name} block")

    return "\n".join(table_lines)

def load_sandbox_options(path):
    with open(path, encoding="utf-8") as f:
        content = f.read()

    table_str = extract_table_block(content, "SandboxOptions")
    try:
        return lua.decode(table_str)
    except Exception as e:
        raise ValueError(f"Lua parse error: {e}")
