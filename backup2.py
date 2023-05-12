import re
import random
from typing import Callable, Any


# Operator definition
def defop(name: str, rankin: int | float, rankout: int | float, arity: int, needs_interpreter=False) -> Callable:
    def decorator(func: Callable) -> Callable:
        func.aipl_name = name
        func.aipl_rankin = rankin
        func.aipl_rankout = rankout
        func.aipl_arity = arity
        func.aipl_needs_interpreter = needs_interpreter
        return func

    return decorator

def apply_partial(func: Callable, *args: Any) -> Callable:
    def wrapper(*remaining_args: Any):
        return func(*args, *remaining_args)

    return wrapper

class AIPLInterpreter:
    def __init__(self):
        self.operators: dict[str, Callable] = {}
        self.results: list[Any] = []
        self.register_operators()

    def register_operators(self):
        for name, obj in globals().items():
            if hasattr(obj, "aipl_name"):
                self.operators[obj.aipl_name] = obj

    def parse_args(self, arg_line: str) -> dict[str, Any]:
        args = {}
        arg_parts = re.findall(r'(\w+)=((?:\[[^\]]*\])|(?:\"[^\"]*\")|\S+)', arg_line)
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
        if value.startswith("$") and value[1:].isdigit():
            index = int(value[1:])
            if 0 < index < len(self.results):
                return self.results[index]
            else:
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

    # def process_commands(self, line: str) -> Any:
    #     cmds = line[1:].split("|>")
    #     result = self.results[-1] if self.results else None
    #     composed = lambda x: x
    #     for cmd in cmds:
    #         cmd = cmd.strip()
    #         op, args = self.parse_command(cmd)
    #         partial_op = self.apply_operator(op, args, result)
    #         composed = lambda x, f=partial_op, g=composed: f(g(x))
    #     return composed(result)
    
    def process_commands(self, line: str) -> Any:
        cmds = line[1:].split("|>")
        result = self.results[-1] if self.results else None
        composed = lambda x: x
        for i, cmd in enumerate(cmds):
            cmd = cmd.strip()
            op, args = self.parse_command(cmd)
            partial_op = self.apply_operator(op, args, result)
            if i == len(cmds) - 1:  # If this is the last command in the pipeline
                return partial_op(result) if callable(partial_op) else partial_op
            if partial_op is None:
                continue  # Skip commands that return None
            composed = lambda x, f=partial_op, g=composed: f(g(x))
        return composed(result)



    def parse_command(self, cmd: str) -> tuple[str, dict[str, Any]]:
        parts = cmd.split(maxsplit=1)
        cmd_name, arg_line = parts[0], parts[1] if len(parts) > 1 else ""
        args = self.parse_args(arg_line)
        return cmd_name, args

    def apply_operator(self, op_name: str, args: dict[str, Any], result: Any) -> Any:
        op = self.operators.get(op_name)
        if op:
            if "v" not in args and result is not None and op.aipl_arity == len(args) + 1:
                args["v"] = result
            if op.aipl_arity > len(args):
                if op.aipl_needs_interpreter:
                    return apply_partial(op, self, *args.values())
                else:
                    return apply_partial(op, *args.values())
            else:
                if op.aipl_needs_interpreter:
                    return op(self, *args.values())
                else:
                    return op(*args.values())
        else:
            raise ValueError(f"Unknown operator: {op_name}")

    def process_script(self, script: str) -> Any:
        lines = script.split("\n")
        for line in lines:
            result = self.process_line(line)
            self.results.append(result)
        return self.results[-1]



# Operator implementations
# @defop("join", rankin=1, rankout=0, arity=2)
# def op_join(aipl: AIPLInterpreter, v: list[str], sep=" ") -> str:
#     return sep.join(v)


# @defop("split", rankin=1, rankout=1, arity=2)
# def op_split(aipl: AIPLInterpreter, v: str, sep=" ") -> list[str]:
#     return v.split(sep)


# @defop("sum", rankin=1, rankout=0, arity=1)
# def op_sum(aipl: AIPLInterpreter, v: list[float]) -> float:
#     return sum(v)


# @defop("int", rankin=0, rankout=0, arity=1)
# def op_int(aipl: AIPLInterpreter, v: Any) -> int:
#     return int(v)


# @defop("float", rankin=0, rankout=0, arity=1)
# def op_float(aipl: AIPLInterpreter, v: Any) -> float:
#     return float(v)


@defop("print", rankin=1, rankout=1, arity=1)
def op_print(v: str) -> str:
    print(v)
    return v


@defop("input", rankin=0, rankout=0, arity=1)
def op_input(prompt: str = "") -> str:
    return input(prompt)


# @defop("choice", rankin=1, rankout=0, arity=1)
# def op_choice(aipl: AIPLInterpreter, v: list[Any]) -> Any:
#     return random.choice(v)


# @defop("randint", rankin=0, rankout=0, arity=2)
# def op_randint(aipl: AIPLInterpreter, a: int, v: int) -> int:
#     return random.randint(a, v)


# @defop("format", rankin=0, rankout=0, arity=2)
# def op_format(aipl: AIPLInterpreter, fmt: str, v: Any) -> str:
#     return fmt.format(v)


# @defop("+", rankin=0, rankout=0, arity=2)
# def op_add(aipl: AIPLInterpreter, a: Any, v: Any) -> Any:
#     return a + v


# @defop("chain", rankin=1, rankout=1, arity=2)
# def op_chain(aipl: AIPLInterpreter, v: Any, cmds: list[str]) -> Any:
#     result = v
#     for cmd in cmds:
#         parts = cmd.split(maxsplit=1)
#         cmd_name, arg_line = parts[0], parts[1] if len(parts) > 1 else ""
#         args = aipl.parse_args(arg_line)
#         if "v" not in args:
#             args["v"] = result
#         result = aipl.call_operator(cmd_name, **args)
#     return result

# @defop("map", rankin=1, rankout=1, arity=2)
# def op_map(aipl: AIPLInterpreter, v: list[Any], op: str) -> list[Any]:
#     return [aipl.call_operator(op, v=x) for x in v]

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

if __name__ == "__main__":
    script = """
    !input prompt="Enter an operator to inspect: "
    !input prompt="Enter a value: "
    !inspect
    !print $0
    """

    interpreter = AIPLInterpreter()
    result = interpreter.process_script(script)

"""
- types: string, number, list, list of lists, dict, list of dicts

- parallel processing with `&`
- table processing with `|` and `||`
- `?` is a query

- split lines onto multiple lines with `\`


- defer execution till all lines are parsed,
    allowing forward references, and allowing for loops, inspection/modification of the script, etc.
    - get a line by number as a string[] with `!lines`
    - get a line by number as a parsed object with `!linesobj`
    - get the whole script as a string[]
- refer to output from an arbitrary line with `$` and the line number
- allow modification of arbitrary lines with `!edit`
"""
