import asyncio
import os

from app.config import Settings
from app.services.chunking.dynamic_chunker import chunk_section_dynamic
from app.services.chunking.sectionizer import Section


def make_cfg(**overrides):
    cfg = Settings()
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


def test_prose_section_chunk_sizes_close_to_max():
    text = (
        "Việc học tập là quá trình suốt đời. Học sinh cần đọc sách và viết mỗi ngày. "
        "Learning is a lifelong journey. Students should read and write daily. "
        "This paragraph is intended to be split into multiple sentences for testing. "
        "Chúng ta sẽ kiểm tra việc chia câu và đếm token LaBSE."
    )
    sec = Section(headingPath=["Intro"], text=text)
    cfg = make_cfg(CHUNK_MODE="DYNAMIC", CHUNK_MIN_TOKENS=180, CHUNK_MAX_TOKENS=480)

    chunks = asyncio.get_event_loop().run_until_complete(
        chunk_section_dynamic(sec, cfg)
    )
    assert len(chunks) >= 1
    for ch in chunks:
        assert ch.tokens < cfg.LABSE_MAX_TOKENS - 1


def test_long_sentence_is_split_safely():
    long_sentence = "A" * 5000
    sec = Section(headingPath=["Long"], text=long_sentence)
    cfg = make_cfg(CHUNK_MODE="DYNAMIC")
    chunks = asyncio.get_event_loop().run_until_complete(
        chunk_section_dynamic(sec, cfg)
    )
    assert len(chunks) >= 1
    for ch in chunks:
        assert ch.tokens <= cfg.LABSE_MAX_TOKENS - 1


