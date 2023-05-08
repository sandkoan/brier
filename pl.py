import re
from typing import List, Callable, Dict, Any

# Operator definition
def defop(name: str, rankin: int, rankout: int, arity: int) -> Callable:
    def decorator(func: Callable) -> Callable:
        func.aipl_name = name
        func.aipl_rankin = rankin
        func.aipl_rankout = rankout
        func.aipl_arity = arity
        return func
    return decorator

class AIPLInterpreter:
    def __init__(self):
        self.operators: Dict[str, Callable] = {}
        self.register_operators()

    def register_operators(self):
        for name, obj in globals().items():
            if hasattr(obj, "aipl_name"):
                self.operators[obj.aipl_name] = obj

    def parse_args(self, arg_line: str) -> Dict[str, Any]:
        args = {}
        arg_parts = re.split(r'\s+(?=[^[\]]*(?:\[(?:[^[\]]*\])*\])*[^[\]]*$)', arg_line)
        for a in arg_parts:
            if not a:
                continue
            k, v = a.split("=", 1) if "=" in a else (a, True)
            if v.startswith("[") and v.endswith("]"):
                v = [x.strip().strip('"') for x in v[1:-1].split(",")]
            args[k] = v
        return args


    def call_operator(self, op_name: str, **kwargs) -> Any:
        op = self.operators.get(op_name)
        if op:
            return op(self, **kwargs)
        else:
            raise ValueError(f"Unknown operator: {op_name}")

    def process_line(self, line: str, prev_result: Any) -> Any:
        line = line.strip()
        if not line or line.startswith("#"):
            return None

        if line.startswith("!"):
            parts = line[1:].split(maxsplit=1)
            cmd, arg_line = parts[0], parts[1] if len(parts) > 1 else ""
            args = self.parse_args(arg_line)
            if 'v' not in args and prev_result is not None:
                args['v'] = prev_result
            return self.call_operator(cmd, **args)
        else:
            return line

    def process_script(self, script: str) -> Any:
        lines = script.split("\n")
        result = None
        for line in lines:
            result = self.process_line(line, result)
        return result


# Operator implementations
@defop("join", rankin=1, rankout=0, arity=1)
def op_join(aipl: AIPLInterpreter, v: List[str], sep=" ") -> str:
    return sep.join(v)

@defop("split", rankin=1, rankout=1, arity=1)
def op_split(aipl: AIPLInterpreter, v: str, sep=" ") -> List[str]:
    return v.split(sep)

@defop("print", rankin=1, rankout=1, arity=1)
def op_print(aipl: AIPLInterpreter, v: str) -> str:
    print(v)
    return v


if __name__ == "__main__":
    script = """
    !join v=["hello", "world"] sep="-"
    !split sep="-"
    !print
    """

    interpreter = AIPLInterpreter()
    result = interpreter.process_script(script)
    print(result)
