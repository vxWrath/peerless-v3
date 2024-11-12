from typing import Mapping, Dict, List, Tuple, Union, Optional, Iterator, overload

class Namespace[K, V]:
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

    def __init__(self, mapping={}, /, **kwargs: V) -> None:
        object.__setattr__(self, '__mapping__', dict())

        self.__mapping__: Dict[K, V]
        self.__mapping__.update(mapping | kwargs)

    def copy(self) -> 'Namespace[K, V]':
        return Namespace(self.__mapping__)
    
    def keys(self) -> List[K]:
        return list(self.__mapping__.keys())
    
    def values(self) -> List[V]:
        return list(self.__mapping__.values())
    
    def items(self) -> List[Tuple[K, V]]:
        return list(self.__mapping__.items())
    
    @overload
    def get(self, key: K, /) -> Optional[V]:
        ...

    @overload
    def get(self, key: K, default: V, /) -> V:
        ...

    @overload
    def get[T](self, key: K, default: T, /) -> Union[V, T]:
        ...

    def get[T](self, key: K, default: Optional[Union[V, T]]=None, /) -> Optional[Union[V, T]]:
        return self.__mapping__.get(key, default)
    
    @overload
    def pop(self, key: K, /) -> Optional[V]:
        ...

    @overload
    def pop(self, key: K, default: V, /) -> V:
        ...

    @overload
    def pop[T](self, key: K, default: T, /) -> Union[V, T]:
        ...

    def pop[T](self, key: K, default: Optional[Union[V, T]]=None, /) -> Optional[Union[V, T]]:
        return self.__mapping__.pop(key, default)
    
    def has(self, key: K) -> bool:
        return key in self
    
    def __repr__(self) -> str:
        return f'Namespace({repr(self.__mapping__)})'
    
    def __str__(self) -> str:
        return f'Namespace({str(self.__mapping__)})'
    
    def __len__(self) -> int:
        return len(self.__mapping__)
    
    def __getitem__(self, key: K) -> V:
        return self.__mapping__[key]
    
    def __setitem__(self, key: K, value: V) -> None:
        self.__mapping__[key] = value

    def __delitem__(self, key: K) -> None:
        del self.__mapping__[key]

    def __getattr__(self, key: K) -> V: # type: ignore[misc]
        try:
            return self.__mapping__[key]
        except KeyError as e:
            raise AttributeError(f"'Namespace' object has no attribute '{key}'") from e
    
    def __setattr__(self, key: K, value: V) -> None: # type: ignore[misc,override]
        self[key] = value

    def __delattr__(self, key: K) -> None: # type: ignore[misc,override]
        del self[key]

    def __iter__(self) -> Iterator[K]:
        return iter(self.__mapping__)
    
    def __eq__(self, value: object) -> bool:
        return self.__mapping__ == value
    
    def __reversed__(self) -> Iterator[K]:
        return reversed(self.__mapping__)