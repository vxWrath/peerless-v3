from datetime import datetime
from typing import Any, overload, Union, Dict, List

type ConvertToString = Union[str, int, float, datetime]
type Convertable = Union[ConvertToString, Dict[ConvertToString, 'Convertable'], List['Convertable']]

@overload
def jsonify(obj: ConvertToString) -> str:
    ...

@overload
def jsonify(obj: Dict[Convertable, Convertable]) -> Dict[Any, Any]:
    ...

@overload
def jsonify(obj: List[Convertable]) -> List[Any]:
    ...

@overload
def jsonify[T](obj: T) -> T:
    ...

def jsonify(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {jsonify(k): jsonify(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [jsonify(x) for x in obj]
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj
    
def unjsonify(obj: Any) -> Any:
    if isinstance(obj, dict):
        obj = {unjsonify(k): unjsonify(v) for k, v in obj.items()}

        return obj
    elif isinstance(obj, list):
        return [unjsonify(x) for x in obj]
    elif isinstance(obj, str) and obj.replace('.', '').isdigit():
        try:
            return datetime.fromisoformat(obj)
        except ValueError:
            pass

        if '.' in obj:
            return float(obj)
        return int(obj)
    else:
        return obj