"""FastAPI adapter shell for FinSkillOS — Slice 13.6.

Thin read-only API layer that exposes existing view-model builders to
the React/Vite frontend (``frontend/``). Business logic stays in
``finskillos.services`` / ``finskillos.ui.view_models`` — the API
modules in this package only translate dataclass output into JSON-
ready Pydantic schemas.

This package is intentionally importable without ``streamlit``.
"""
