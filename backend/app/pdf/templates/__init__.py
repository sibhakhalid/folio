"""
Template registry. To add a new layout:
  1. Copy classic.py to a new file and change the look.
  2. Import it here and add it to TEMPLATES.
  3. Add its name to the Literal[...] in app/schemas.py and mention it in app/gemini_service.py.
"""

from .classic import ClassicTemplate
from .modern import ModernTemplate
from .report import ReportTemplate

TEMPLATES = {t.name: t() for t in (ReportTemplate, ModernTemplate, ClassicTemplate)}


def get_template(name: str):
    return TEMPLATES.get(name, TEMPLATES["report"])
