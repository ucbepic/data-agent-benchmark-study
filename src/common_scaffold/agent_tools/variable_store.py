import json

class VariableStore:
    """
    A simple store to keep agent variables.
    Supports dict-like access and additional helpers.
    """

    def __init__(self):
        self._vars = {}

    def set(self, key, value):
        print(f"[VariableStore] Set {key}")
        self._vars[key] = value

    def get(self, key, default=None):
        return self._vars.get(key, default)

    def all(self):
        return self._vars

    def keys(self):
        return self._vars.keys()

    def __getitem__(self, key):
        return self._vars[key]

    def __setitem__(self, key, value):
        self.set(key, value)

    def __contains__(self, key):
        return key in self._vars

    def __str__(self):
        return str(self._vars)

    def save(self, path: str):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._vars, f, indent=2)
        print(f"[VariableStore] Saved to {path}")

    def load(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            self._vars = json.load(f)
        print(f"[VariableStore] Loaded from {path}")

    def copy(self):
        return self._vars.copy()
    
    def update(self, other: dict):
        self._vars.update(other)
