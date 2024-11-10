from typing import Dict, MutableMapping, TypeVar, Union

K = TypeVar('K')
V = TypeVar('V')

class Namespace(Dict[K, V]):
    def __init__(self, *args: MutableMapping[K, V], **kwargs: V):
        super().__init__(*args, **kwargs)

        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = Namespace(value)  # type: ignore
            elif isinstance(value, list):
                self[key] = [Namespace(item) if isinstance(item, dict) else item for item in value]  # type: ignore

    def __getattr__(self, key: K) -> V:
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'Namespace' object has no attribute '{key}'")

    def __setattr__(self, key: K, value: V) -> None:
        if isinstance(value, dict):
            self[key] = Namespace(value) # type: ignore
        else:
            self[key] = value

    def __delattr__(self, key: K) -> None:
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"'Namespace' object has no attribute '{key}'")