# FinSkillOS v2.1

FinSkillOS v2.1 is a personal trading operating system.

Implementation order:

1. Read `.devmd/README.md`
2. Read `docs/v2_1/CONTEXT_INDEX.md`
3. Follow `.devmd` slices in numerical order when they exist
4. Use `docs/v2_1` as source-of-truth references
5. Use `prototypes/ui/os_style_mockup/index.html` as the UI direction when available
6. Do not implement direct buy/sell recommendation features

Project layout:

- `finskillos/`: v2.1 application code
- `docs/v2_1/`: source design documents
- `.devmd/`: agent execution instructions
- `prototypes/ui/`: HTML mockups and design references
- `data/sample/`: commit-safe sample data
- `data/cache/`, `data/logs/`, `data/parquet/`, `data/exports/`: local runtime data
- `tests/`: acceptance and regression tests
- `legacy_v1/`: preserved v1 competition project
