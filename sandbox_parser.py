# sandbox_parser.py

import os
import re
import ast
from pathlib import Path

def lua_to_python_dict(lua_str: str) -> dict:
    table_str = re.search(r"SandboxVars\s*=\s*(\{.*\})", lua_str, re.DOTALL)
    if not table_str:
        raise ValueError("Could not find SandboxVars block")
    lua_table = table_str.group(1)

    # Simple Lua to Python dict conversion
    lua_table = re.sub(r"--.*", "", lua_table)  # remove comments
    lua_table = re.sub(r"\[\"(.*?)\"\]", r"'\1'", lua_table)
    lua_table = re.sub(r"=", ":", lua_table)
    lua_table = re.sub(r"true", "True", lua_table)
    lua_table = re.sub(r"false", "False", lua_table)
    lua_table = re.sub(r"\bnil\b", "None", lua_table)

    try:
        return ast.literal_eval(lua_table)
    except Exception as e:
        raise ValueError(f"Lua parse error: {e}")

def python_to_lua_table(py_dict: dict, indent: int = 0) -> str:
    lua_lines = ["{"]
    pad = "    " * (indent + 1)
    for key, value in py_dict.items():
        if isinstance(value, dict):
            inner = python_to_lua_table(value, indent + 1)
            lua_lines.append(f"{pad}{key} = {inner},")
        elif isinstance(value, str):
            escaped = value.replace('"', '\\"')
            lua_lines.append(f'{pad}{key} = "{escaped}",')
        else:
            lua_lines.append(f"{pad}{key} = {value},")
    lua_lines.append("    " * indent + "}")
    return "\n".join(lua_lines)

def prettify_keys(data):
    if isinstance(data, dict):
        return {
            " ".join(re.findall(r"[A-Z]?[a-z]+", k)): prettify_keys(v)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [prettify_keys(item) for item in data]
    else:
        return data

def get_all_sandbox_mod_options(mod_root):
    mod_options = {}
    for root, dirs, files in os.walk(mod_root):
        for file in files:
            if file == "SandboxOptions.lua":
                full_path = os.path.join(root, file)
                with open(full_path, encoding="utf-8") as f:
                    raw = f.read()
                try:
                    parsed = lua_to_python_dict(raw)
                    mod_name = Path(root).name
                    mod_options[mod_name] = parsed
                except Exception as e:
                    print(f"Failed to parse {file}: {e}")
    return mod_options

def build_combined_sandbox(sandbox_path, base_dir, mod_dir):
    with open(sandbox_path, encoding="utf-8") as f:
        raw = f.read()

        print("[DEBUG] Lua raw data:\n", raw)  # Add this line temporarily
    active_vars = lua_to_python_dict(raw)

    base_options = get_all_sandbox_mod_options(base_dir)
    mod_options = get_all_sandbox_mod_options(mod_dir)

    combined = {
        "__active__": active_vars,
        "Base": base_options.get("Base", {}),
        "Mods": mod_options,
    }

    return combined
