import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class Section:
    headingPath: List[str]
    text: str
    pageStart: Optional[int] = None
    pageEnd: Optional[int] = None
    type: str = "normal"  # normal | list | table | code
    charStart: Optional[int] = None
    charEnd: Optional[int] = None


def _is_header(line: str) -> bool:
    if re.match(r"^\s*#{1,6}[^#]", line):
        return True
    if re.match(r"^\s*(?:\d+\.|[IVXLCMivxlcm]+\.)\s+\S", line):
        return True
    if re.match(r"^\s*={3,}\s*$|^\s*-{3,}\s*$", line):
        return True
    return False


def _detect_block_type(text: str) -> str:
    if re.search(r"```|\bclass\b|\bdef\b|\{\}|;", text):
        return "code"
    if re.search(r"\n\s*[-*•]\s+|\n\s*\d+\.\s+", text):
        return "list"
    if re.search(r"\|.*\|\n\|[-: ]+\|", text):
        return "table"
    return "normal"


def _filter_noise(lines: List[str]) -> List[str]:
    filtered = []
    for ln in lines:
        if len(ln.strip()) == 0:
            continue
        # Drop likely headers/footers/page numbers
        if re.match(r"^\s*Page\s+\d+\s*$", ln):
            continue
        if re.match(r"^\s*\d+\s*/\s*\d+\s*$", ln):
            continue
        if re.match(r"^\s*Table of Contents\s*$", ln, re.IGNORECASE):
            continue
        filtered.append(ln)
    return filtered


def sectionize_document(text: str, structure: Dict[str, Any]) -> List[Section]:
    """Structure-aware sectionization. If no structure, use simple heading heuristics."""
    lines = text.splitlines()
    lines = _filter_noise(lines)

    sections: List[Section] = []
    current_heading: List[str] = []
    buffer: List[str] = []
    char_index = 0
    sec_start_char: Optional[int] = None
    page_num = 1

    for raw_line in lines:
        line = raw_line.rstrip()
        if _is_header(line):
            # Flush current buffer
            if buffer:
                sec_text = "\n".join(buffer).strip()
                sections.append(
                    Section(
                        headingPath=current_heading[:],
                        text=sec_text,
                        pageStart=page_num,
                        pageEnd=page_num,
                        type=_detect_block_type(sec_text),
                        charStart=sec_start_char,
                        charEnd=char_index + len(line),
                    )
                )
                buffer = []
                sec_start_char = None
            # Update heading path
            heading_text = re.sub(r"^\s*#+\s*", "", line).strip()
            if heading_text:
                current_heading = [*current_heading[:-1], heading_text] if current_heading else [heading_text]
        else:
            if sec_start_char is None:
                sec_start_char = char_index
            buffer.append(line)
        char_index += len(raw_line) + 1
        # crude page increment on many newlines / long text; placeholder
        if len(buffer) % 60 == 0:
            page_num += 1

    if buffer:
        sec_text = "\n".join(buffer).strip()
        sections.append(
            Section(
                headingPath=current_heading[:],
                text=sec_text,
                pageStart=page_num,
                pageEnd=page_num,
                type=_detect_block_type(sec_text),
                charStart=sec_start_char,
                charEnd=char_index,
            )
        )

    return sections


