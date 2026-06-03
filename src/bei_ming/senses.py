from .wings import Wings

_wings = None

def init_senses(imagination, ethics_rules, config=None):
    global _wings
    if config is None:
        config = {}
    _wings = Wings(imagination, ethics_rules, config)

def fetch_from_web(task: str, max_pages: int = 5) -> int:
    if not _wings:
        raise RuntimeError("感官未初始化")
    return _wings.explore(task, max_pages)
