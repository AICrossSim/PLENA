"""Tool for reading files from the codebase."""

from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Allowed directories for security
# NOTE: compiler/asm_templates is excluded - agent must write assembly from first principles
ALLOWED_DIRS = [
    "behavioral_simulator",
    "kernel_agents",
    "tools/assembler",
    "compiler/doc",  # Only docs, not templates
    "src/definitions",
]


def read_file(file_path: str, max_lines: int = 500) -> Dict[str, Any]:
    """
    Read a file from the codebase.

    Use sparingly - only when you need implementation details not in docs.
    Prefer using existing tools and documentation first.

    Args:
        file_path: Relative path from project root (e.g., "behavioral_simulator/src/op.rs")
        max_lines: Maximum lines to return (default 500)

    Returns:
        Dict with file content or error
    """
    result = {"success": False, "content": None, "error": None}

    # Resolve path
    if Path(file_path).is_absolute():
        full_path = Path(file_path)
    else:
        full_path = PROJECT_ROOT / file_path

    # Security: check if path is within allowed directories
    try:
        rel_path = full_path.resolve().relative_to(PROJECT_ROOT.resolve())
        rel_str = str(rel_path)
        if not any(rel_str.startswith(d) for d in ALLOWED_DIRS):
            result["error"] = f"Access denied. Allowed dirs: {ALLOWED_DIRS}"
            return result
    except ValueError:
        result["error"] = "Path must be within project root"
        return result

    # Check file exists
    if not full_path.exists():
        result["error"] = f"File not found: {file_path}"
        return result

    if not full_path.is_file():
        result["error"] = f"Not a file: {file_path}"
        return result

    # Read file
    try:
        lines = full_path.read_text().splitlines()
        if len(lines) > max_lines:
            content = "\n".join(lines[:max_lines])
            result["truncated"] = True
            result["total_lines"] = len(lines)
        else:
            content = "\n".join(lines)
            result["truncated"] = False
            result["total_lines"] = len(lines)

        result["success"] = True
        result["content"] = content
        result["file_path"] = str(rel_path)

    except Exception as e:
        result["error"] = f"Error reading file: {e}"

    return result
