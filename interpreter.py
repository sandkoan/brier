import re
from typing import Callable, Any


# Operator definition
def defop(name: str, rankin: int | float, rankout: int | float, arity: int) -> Callable:
    def decorator(func: Callable) -> Callable:
        func.aipl_name = name
        func.aipl_rankin = rankin
        func.aipl_rankout = rankout
        func.aipl_arity = arity
        return func

    return decorator


class AIPLInterpreter:
    def __init__(self):
        self.operators: dict[str, Callable] = {}
        self.register_operators()

    def register_operators(self):
        for name, obj in globals().items():
            if hasattr(obj, "aipl_name"):
                self.operators[obj.aipl_name] = obj

    def parse_args(self, arg_line: str) -> dict[str, Any]:
        args = {}
        arg_parts = re.findall(r"(\w+)=((?:\[[^\]]*\])|(?:\"[^\"]*\")|\S+)", arg_line)
        for k, v in arg_parts:
            if v.startswith("[") and v.endswith("]"):
                v = [x.strip().strip('"') for x in v[1:-1].split(",")]
            elif v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
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
            return prev_result

        if line.startswith("!"):
            parts = line[1:].split(maxsplit=1)
            cmd, arg_line = parts[0], parts[1] if len(parts) > 1 else ""
            args = self.parse_args(arg_line)
            if "v" not in args and prev_result is not None:
                args["v"] = prev_result
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
def op_join(aipl: AIPLInterpreter, v: list[str], sep=" ") -> str:
    return sep.join(v)


@defop("split", rankin=1, rankout=1, arity=1)
def op_split(aipl: AIPLInterpreter, v: str, sep=" ") -> list[str]:
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

"""
`@defop` registers the decorated function as the named operator.
rankin is what the function takes as input:
`0`: a scalar (number or string)
0.5`: a whole row
`1`: a whole column of values
`2`: the whole table
rankout is what the function returns
`0`: a scalar value
`0.5`: a dict of values
`1`: a column of values
`2`: a whole table
`arity` for how many operands it takes

"""