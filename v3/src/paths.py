from src import *

SRC = Path(__file__).resolve().parent
BASE = SRC.parent
PROGRAMS = BASE / 'programs'
RULESETS = BASE / 'rulesets'
LOGS = BASE / 'logs'

generated_folders = [
    PROGRAMS,
    RULESETS,
    LOGS,
]

def generate_folders():
    for folder in generated_folders:
        folder.mkdir(parents=True,exist_ok=True)

__all__ = [
    'SRC',
    'BASE',
    'PROGRAMS',
    'RULESTS',
    'generated_folders',
    'generate_folders'
]