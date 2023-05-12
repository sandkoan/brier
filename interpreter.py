import re
from typing import Callable, Any
from typing import get_type_hints, TypeVar
from functools import partial


def get_arg_types(func: Callable) -> list:
    hints = get_type_hints(func)
    return [hints[arg] for arg in hints if arg not in {"return", "self"}]


# Operator definition
def defop(
    name: str,
    rankin: int | float,
    rankout: int | float,
    arity: int,
    needs_interpreter=False,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        func.aipl_name = name
        func.aipl_rankin = rankin
        func.aipl_rankout = rankout
        func.aipl_arity = arity
        func.aipl_needs_interpreter = needs_interpreter
        return func

    return decorator


class AIPLInterpreter:
    def __init__(self):
        self.script: str = ""
        self.operators: dict[str, Callable] = {}
        self.results: list[Any] = []
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
                v = [self.parse_number_or_str(x.strip()) for x in v[1:-1].split(",")]
            elif v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            else:
                v = self.parse_number_or_str(v)
            args[k] = v
        return args

    def parse_number_or_str(self, value: str) -> Any:
        if value.startswith("$"):
            try:
                index = int(value[1:])
                return self.results[index]
            except (ValueError, IndexError) as e:
                raise ValueError(f"Invalid result reference: {value}")
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                if value.startswith('"') and value.endswith('"'):
                    return value[1:-1]
                else:
                    raise ValueError(f"Unquoted string: {value}")

    def call_operator(self, op_name: str, **kwargs) -> Any:
        op = self.operators.get(op_name)
        if op:
            return op(self, **kwargs)
        else:
            raise ValueError(f"Unknown operator: {op_name}")

    def process_line(self, line: str) -> Any:
        line = line.strip()
        if not line or line.startswith("#"):
            return self.results[-1] if self.results else None

        if line.startswith("!"):
            return self.process_commands(line)
        else:
            return line

    def process_commands(self, line: str) -> Any:
        cmds = line[1:].split("|>")
        result = self.results[-1] if self.results else None
        composed = lambda x: x
        for i, cmd in enumerate(cmds):
            cmd = cmd.strip()
            op, args = self.parse_command(cmd)
            partial_op = self.apply_operator(op, args, result)

            if i == len(cmds) - 1:  # If this is the last command in the pipeline
                if callable(partial_op):
                    arity = (
                        partial_op.func.aipl_arity if hasattr(partial_op, "func") else 0
                    )
                    if arity == len(args):
                        # Call the operator directly without passing the result
                        return partial_op()
                    else:
                        return partial_op(result)
                else:
                    return partial_op
            if partial_op is None:
                continue  # Skip commands that return None
            composed = lambda x, f=partial_op, g=composed: f(g(x))
        return composed(result)

    def parse_command(self, cmd: str) -> tuple[str, dict[str, Any]]:
        parts = cmd.split(maxsplit=1)
        cmd_name, arg_line = parts[0], parts[1] if len(parts) > 1 else ""

        if "=" not in arg_line:  # If there are no named arguments, treat as positional arguments
            arg_values = arg_line.split()
            arg_values = [
                self.parse_number_or_str(v) for v in arg_values
            ]  # Replace numbers prefixed with $
            arg_names = [str(i) for i in range(len(arg_values))]  # Convert arg_names to strings
            args = dict(zip(arg_names, arg_values))
        else:
            args = self.parse_args(arg_line)

        return cmd_name, args


    def apply_operator(self, op_name: str, args: dict[str, Any], result: Any) -> Any:
        op = self.operators.get(op_name)
        if op:
            arg_types = get_arg_types(op)
            arity = len(arg_types)

            # Match the result to the correct argument type
            if not result and len(args) < arity and not (op.aipl_needs_interpreter and len(args) == arity - 1):
                for i, arg_type in enumerate(arg_types):
                    # Use arg_type.__origin__ if it exists, otherwise use arg_type
                    base_type = arg_type.__origin__ if hasattr(arg_type, "__origin__") else arg_type
                    if isinstance(result, base_type) and i not in args:
                        args[i] = result
                        break

            if arity > len(args):
                if op.aipl_needs_interpreter:
                    return partial(op, self, *list(args.values()))
                else:
                    return partial(op, *list(args.values()))

            else:
                args_values = list(args.values())
                if op.aipl_needs_interpreter:
                    args_values.insert(0, self)  # Insert interpreter as the first argument
                return op(*args_values)
        else:
            raise ValueError(f"Unknown operator: {op_name}")


    def process_script(self, script: str) -> Any:
        self.script = script.split("\n")
        for line in self.script:
            result = self.process_line(line)
            self.results.append(result)
        return self.results[-1]


# Operator implementations
@defop("print", rankin=1, rankout=1, arity=1)
def op_print(v: str) -> str:
    print(v)
    return v

@defop("input", rankin=0, rankout=0, arity=1)
def op_input(prompt: str = "") -> str:
    return input(prompt)

@defop("inspect", rankin=0, rankout=0, arity=1, needs_interpreter=True)
def op_inspect_op(aipl: AIPLInterpreter, op_name: str) -> str:
    import inspect
    op = aipl.operators.get(op_name)
    if op:
        print(f"Inspecting operator: {op_name}")
        print(inspect.getsource(op))
    else:
        print(f"Operator not found: {op_name}")
    return op_name

@defop("join", rankin=1, rankout=0, arity=2)
def op_join(l: list[str], sep=" ") -> str:
    return sep.join(l)

@defop("split", rankin=1, rankout=1, arity=2)
def op_split(s: str, sep=" ") -> list[str]:
    return s.split(sep)

@defop("sum", rankin=1, rankout=0, arity=1)
def op_sum(l: list[int | float]) -> int | float:
    return sum(l)

@defop("int", rankin=0, rankout=0, arity=1)
def op_int(v: Any) -> int:
    return int(v)

@defop("float", rankin=0, rankout=0, arity=1)
def op_float(v: Any) -> float:
    return float(v)

@defop("format", rankin=0, rankout=0, arity=2)
def op_format(fmt: str, v: Any) -> str:
    return fmt.format(v)

@defop("add", rankin=0, rankout=0, arity=2)
def op_add(a: Any, b: Any) -> Any:
    return a + b

@defop("map_int", rankin=1, rankout=1, arity=1)
def op_map_int(l: list[Any]) -> list[Any]:
    return [int(x) for x in l]

@defop("map", rankin=1, rankout=1, arity=2, needs_interpreter=True)
def op_map(aipl: AIPLInterpreter, op: str, l: list[Any]) -> list[Any]:
    print(f"Mapping {op} over {l}")
    result = aipl.results[-1] if aipl.results else None
    return [aipl.apply_operator(op, {"$": x}, ) for x in l]


if __name__ == "__main__":
    # Current TODO: issue with mixing positional args and named args in the same command call: e.g., `!map op=int` and the previous value/list being passed in implicitly
    script = """
    !input prompt="Enter numbers: "
    !input prompt="Enter sep: "
    !split $1 $2
    !print
    !map op="int" l=$-1
    # !map_int
    !sum
    !format fmt="Sum: {}" v=$-1
    !print
    """

    interpreter = AIPLInterpreter()
    result = interpreter.process_script(script)

"""
* sqlite caching of expensive operations
* triple quotes for multiline strings
* parsing separate file as a script
* types: string, number, list, list of lists, dict, list of dicts

- parallel processing with `&` prefixing any operator 
- table processing with `|` and `||`
"""
