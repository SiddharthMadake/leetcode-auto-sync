from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageSpec:
    slug: str
    display_name: str
    extension: str


SUPPORTED_LANGUAGES: dict[str, LanguageSpec] = {
    "python": LanguageSpec("python", "Python", "py"),
    "python3": LanguageSpec("python", "Python", "py"),
    "javascript": LanguageSpec("javascript", "JavaScript", "js"),
    "typescript": LanguageSpec("typescript", "TypeScript", "ts"),
    "cpp": LanguageSpec("cpp", "C++", "cpp"),
    "c++": LanguageSpec("cpp", "C++", "cpp"),
    "java": LanguageSpec("java", "Java", "java"),
    "golang": LanguageSpec("go", "Go", "go"),
    "go": LanguageSpec("go", "Go", "go"),
    "rust": LanguageSpec("rust", "Rust", "rs"),
}


def normalize_language(raw: str) -> LanguageSpec | None:
    key = raw.strip().lower()
    if key in SUPPORTED_LANGUAGES:
        return SUPPORTED_LANGUAGES[key]
    return None
