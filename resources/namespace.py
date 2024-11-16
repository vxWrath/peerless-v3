from typing import Mapping, Any, overload

class Namespace[K, V](dict[K, V]):
    @overload
    def __init__(self, /) -> None:
        ...

    @overload
    def __init__(self: 'Namespace[str, V]', /, **kwargs: V) -> None: # type: ignore[reportInvalidTypeVarUse]
        ...

    @overload
    def __init__(self, mapping: Mapping[K, V], /) -> None:
        ...

    @overload
    def __init__(self: 'Namespace[str, V]', mapping: Mapping[str, V], /, **kwargs: V) -> None: # type: ignore[reportInvalidTypeVarUse]
        ...

    def __init__(self, mapping: Mapping[Any, Any]={}, /, **kwargs: V) -> None:
        super().__init__(mapping, **kwargs)

        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = Namespace(value)  # type: ignore
            elif isinstance(value, list):
                self[key] = [Namespace(item) if isinstance(item, dict) else item for item in value]  # type: ignore

    def __getattr__(self, key: K) -> V: # type: ignore[misc]
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'Namespace' object has no attribute '{key}'")

    def __setattr__(self, key: K, value: V) -> None: # type: ignore[misc,override]
        if isinstance(value, dict):
            self[key] = Namespace(value) # type: ignore
        else:
            self[key] = value

    def __delattr__(self, key: K) -> None: # type: ignore[misc,override]
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"'Namespace' object has no attribute '{key}'")
        
    def has(self, key: K) -> bool:
        return key in self