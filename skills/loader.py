import logging
from pathlib import Path
from config.settings import settings

logger = logging.getLogger("ruby.skills")

class Skill:
    def __init__(self, name: str, description: str, prompt: str):
        self.name = name
        self.description = description
        self.prompt = prompt

class SkillLoader:
    def __init__(self):
        self.skills_dir = Path(__file__).parent
        self.skills: list[Skill] = []
        self._load()

    def _load(self):
        for f in sorted(self.skills_dir.glob("*.md")):
            name = f.stem
            content = f.read_text(encoding="utf-8")
            lines = content.split("\n", 2)
            description = lines[0].lstrip("# ").strip() if lines else name
            self.skills.append(Skill(name, description, content))
            logger.info("Loaded skill: %s", name)

    def get_prompt_extension(self) -> str:
        if not self.skills:
            return ""
        parts = ["## Loaded Skills"]
        for skill in self.skills:
            parts.append(f"### {skill.name}")
            parts.append(skill.description)
        return "\n\n".join(parts)

    def list_skills(self) -> list[dict]:
        return [{"name": s.name, "description": s.description} for s in self.skills]
