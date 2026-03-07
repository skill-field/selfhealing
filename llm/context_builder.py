"""Code context assembly for LLM prompts."""

from __future__ import annotations

import json
import re
from typing import Optional

from modules.github_client import GitHubClient


class ContextBuilder:
    """Build code context for LLM prompts by fetching relevant source files."""

    def __init__(self, github_client: GitHubClient):
        self.github = github_client
        self.max_context_lines = 500

    async def build_fix_context(self, error: dict) -> dict:
        """Build context for fix generation from an error record.

        Returns: {files: [{path, content, relevant_lines}], total_lines}
        """
        file_entries: list[dict] = []
        seen_paths: set[str] = set()

        # 1. Parse affected_files from error record
        affected_files_raw = error.get("affected_files", "[]")
        if isinstance(affected_files_raw, str):
            try:
                affected_files = json.loads(affected_files_raw)
            except (json.JSONDecodeError, TypeError):
                affected_files = []
        else:
            affected_files = affected_files_raw or []

        # Also consider single affected_file field
        affected_file = error.get("affected_file")
        if affected_file and affected_file not in affected_files:
            affected_files.insert(0, affected_file)

        # 2. Parse stack_trace to find additional files
        stack_trace = error.get("stack_trace", "") or ""
        stack_files = self._extract_files_from_stack(stack_trace)

        # Merge: affected_files first, then stack files (deduplicated)
        all_targets: list[dict] = []
        for path in affected_files:
            if path not in seen_paths:
                seen_paths.add(path)
                all_targets.append({"path": path, "line": None, "function": None})

        for sf in stack_files:
            if sf["path"] not in seen_paths:
                seen_paths.add(sf["path"])
                all_targets.append(sf)

        # 3. Fetch each file from GitHub (up to 5 files)
        total_lines = 0
        for target in all_targets[:5]:
            path = target["path"]
            content = await self.github.get_file_content(path)
            if content is None:
                continue

            target_line = target.get("line")
            trimmed = self._trim_to_context(content, target_line, window=50)
            lines_count = trimmed.count("\n") + 1
            total_lines += lines_count

            file_entries.append({
                "path": path,
                "content": trimmed,
                "relevant_lines": f"around line {target_line}" if target_line else "full context",
            })

            # Stop if we've accumulated too many lines
            if total_lines >= self.max_context_lines:
                break

        return {"files": file_entries, "total_lines": total_lines}

    async def build_feature_context(self, title: str, description: str) -> dict:
        """Build code context for feature generation by fetching relevant source files.

        Uses heuristics to identify likely-relevant files from the repo based on
        keywords in the title and description.
        """
        file_entries: list[dict] = []
        total_lines = 0

        # Extract likely file paths or module names from description
        import re
        # Look for explicit file paths mentioned
        path_pattern = re.compile(r"(?:src/\S+\.\w+)")
        mentioned_paths = path_pattern.findall(f"{title} {description}")

        # Also try to fetch key structural files for context
        structural_files = [
            "src/lib/services/index.ts",
            "prisma/schema.prisma",
        ]

        # Keywords to search for relevant service files
        keywords = re.findall(r"\b([a-z]{3,})\b", f"{title} {description}".lower())
        keyword_paths = [f"src/lib/services/{kw}/{kw}.service.ts" for kw in keywords[:3]]

        all_paths = list(dict.fromkeys(mentioned_paths + keyword_paths + structural_files))

        for path in all_paths[:5]:
            content = await self.github.get_file_content(path)
            if content is None:
                continue

            trimmed = self._trim_to_context(content, None, window=50)
            lines_count = trimmed.count("\n") + 1
            total_lines += lines_count

            file_entries.append({
                "path": path,
                "content": trimmed,
                "relevant_lines": "full context",
            })

            if total_lines >= self.max_context_lines:
                break

        return {"files": file_entries, "total_lines": total_lines}

    def _extract_files_from_stack(self, stack_trace: str) -> list[dict]:
        """Extract file paths and line numbers from stack trace.

        Parses lines like:
          at MetricService.calculate (src/lib/services/metric/metric.service.ts:245:12)
          at /app/src/lib/utils.ts:30:5
        """
        results: list[dict] = []
        seen: set[str] = set()

        # Pattern: optional function name, then file path with line number
        patterns = [
            # "at FunctionName (path:line:col)"
            re.compile(r"at\s+(\S+)\s+\((?:\/app\/)?(.+?):(\d+):\d+\)"),
            # "at path:line:col"
            re.compile(r"at\s+(?:\/app\/)?(.+?):(\d+):\d+"),
            # Generic "File path:line" pattern
            re.compile(r"(?:\/app\/)?(src/\S+?\.\w+):(\d+)"),
        ]

        for line in stack_trace.split("\n"):
            line = line.strip()

            # Skip node_modules
            if "node_modules" in line:
                continue

            for i, pattern in enumerate(patterns):
                match = pattern.search(line)
                if match:
                    groups = match.groups()
                    if i == 0:
                        func_name, path, line_no = groups
                    elif i == 1:
                        func_name = None
                        path, line_no = groups
                    else:
                        func_name = None
                        path, line_no = groups

                    # Normalize path
                    path = path.lstrip("/")
                    if path.startswith("app/"):
                        path = path[4:]

                    if path not in seen and path.startswith("src/"):
                        seen.add(path)
                        results.append({
                            "path": path,
                            "line": int(line_no),
                            "function": func_name,
                        })
                    break

        return results

    def _trim_to_context(
        self, content: str, target_line: int | None, window: int = 50
    ) -> str:
        """Trim file content to relevant section around target line."""
        lines = content.split("\n")

        if target_line is None or target_line <= 0 or len(lines) <= self.max_context_lines:
            # Return all lines if file is small enough or no target
            if len(lines) > self.max_context_lines:
                return "\n".join(lines[: self.max_context_lines])
            return content

        # Calculate window around target line (1-indexed to 0-indexed)
        start = max(0, target_line - 1 - window)
        end = min(len(lines), target_line - 1 + window)

        selected = lines[start:end]

        # Add line number annotations for clarity
        numbered = []
        for i, line_text in enumerate(selected, start=start + 1):
            marker = " >>>" if i == target_line else "    "
            numbered.append(f"{marker} {i}: {line_text}")

        return "\n".join(numbered)
