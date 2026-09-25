"""Coach tools — stubs for the main agent.

Implement skill extraction, role comparison, simple search, and an
optional calculator. Split this module when implementations grow.
"""


def skill_extractor(text: str) -> list[str]:
    raise NotImplementedError("Implement skill extraction")


def role_comparator(resume_skills: list[str], jd_skills: list[str]) -> dict:
    raise NotImplementedError("Implement resume vs JD role comparison")


def simple_search(query: str) -> list[str]:
    raise NotImplementedError("Implement search (docs or web)")


def calculator(expression: str) -> float:
    raise NotImplementedError("Optional calculator tool")
