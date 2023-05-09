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

    def call_operator(self, op_name: str, **kwargs) -> Any:
        op = self.operators.get(op_name)
        if op:
            return op(self, **kwargs)
        else:
            raise ValueError(f"Unknown operator: {op_name}")

    def parse_number_or_str(self, value: str) -> Any:
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    def process_script(self, script: str) -> Any:
        lines = script.split("\n")
        result = None
        results_by_line = {}
        for idx, line in enumerate(lines, start=1):
            result = self.process_line(line, result, results_by_line)
            results_by_line[idx] = result
        return result

    def parse_args(self, arg_line: str, results_by_line: dict[int, Any]) -> dict[str, Any]:
        args = {}
        arg_parts = re.findall(r'(\w+)=((?:\[[^\]]*\])|(?:\"[^\"]*\")|\S+)', arg_line)
        for k, v in arg_parts:
            if v.startswith("$"):
                line_number = int(v[1:])
                v = results_by_line.get(line_number, None)
            elif v.startswith("[") and v.endswith("]"):
                v = [self.parse_number_or_str(x.strip()) for x in v[1:-1].split(",")]
            elif v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            else:
                v = self.parse_number_or_str(v)
            args[k] = v
        return args

    def process_line(self, line: str, prev_result: Any, results_by_line: dict[int, Any]) -> Any:
        line = line.strip()
        if not line or line.startswith("#"):
            return prev_result

        if line.startswith("!"):
            parts = line[1:].split(maxsplit=1)
            cmd, arg_line = parts[0], parts[1] if len(parts) > 1 else ""
            args = self.parse_args(arg_line, results_by_line)
            if 'v' not in args and prev_result is not None:
                args['v'] = prev_result
            return self.call_operator(cmd, **args)
        else:
            return line

# Operator implementations
@defop("join", rankin=1, rankout=0, arity=1)
def op_join(aipl: AIPLInterpreter, v: list[str], sep=" ") -> str:
    return sep.join(v)

@defop("split", rankin=0, rankout=1, arity=1)
def op_split(aipl: AIPLInterpreter, v: str, sep=" ") -> list[str]:
    return v.split(sep)

@defop("sum", rankin=1, rankout=0, arity=1)
def op_sum(aipl: AIPLInterpreter, v: list[float]) -> float:
    return sum(v)

@defop("print", rankin=1, rankout=1, arity=1)
def op_print(aipl: AIPLInterpreter, v: str) -> str:
    print(v)
    return v


if __name__ == "__main__":
    script = """
    !join v=["hello", "world"] sep=", "
    # !split v="hello, world" sep=", "
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

- split lines onto multiple lines with `\`
- refer to output from an arbitrary line with `$` and the line number
- parallel processing with `&`
- table processing with `|` and `||`
- `?` is a query
- take input from console with `!input`
"""


@defop("input", rankin=0, rankout=0, arity=1)
def op_input(aipl: AIPLInterpreter, prompt: str = "") -> str:
    return input(prompt)

@defop("choice", rankin=1, rankout=0, arity=1)
def op_choice(aipl: AIPLInterpreter, v: list[Any]) -> Any:
    return random.choice(v)

@defop("randint", rankin=0, rankout=0, arity=2)
def op_randint(aipl: AIPLInterpreter, a: int, b: int) -> int:
    return random.randint(a, b)


@defop("format", rankin=0, rankout=0, arity=1)
def op_format(aipl: AIPLInterpreter, v: Any, fmt: str) -> str:
    return fmt.format(v)

@defop("chain", rankin=0, rankout=0, arity=1)
def op_chain(aipl: AIPLInterpreter, v: Any, *funcs: Callable) -> Any:
    for func in funcs:
        v = func(v)
    return v

if __name__ == "__main__":
    script = """
    # !join v=["hello", "world"] sep="- "
    # !split sep="-"
    # !sum v=[1, 2, 3, 4, 5]
    # !print v="hegllo"
    # !input prompt="Enter your name: "
    # !format v=3.14159265358979323846 fmt="{:.2f}"
    !chain v=3.14159265358979323846 !format fmt="{:.2f}" !print
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

- take input from console with `!input`
- support for f-strings with `!format`
- chain/curry multiple operators with `|>`
- split lines onto multiple lines with `\`
- refer to output from an arbitrary line with `$` and the line number
- parallel processing with `&`
- table processing with `|` and `||`
- `?` is a query
"""