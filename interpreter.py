import re
from functools import partial
from typing import Any, Callable, get_type_hints


# Operator definition decorator
def defop(name: str, rankin: int | float, rankout: int | float, arity: int, needs_interpreter=False) -> Callable:
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

    def process_line(self, line: str) -> Any:
        line = line.strip()
        if not line or line.startswith("#"):
            return self.get_last_result()

        if line.startswith("!"):
            return self.process_commands(line)
        elif line.startswith("?"):
            # ?<cmd> ==> !inspect <cmd>
            return self.process_commands("!inspect " + line[1:])
        else:
            return line

    def process_commands(self, line: str) -> Any:
        cmds = line[1:].split("|>")
        result = self.get_last_result()
        composed = lambda x: x
        for i, cmd in enumerate(cmds):
            cmd = cmd.strip()
            op, args = self.parse_command(cmd)
            partial_op = self.apply_operator(op, args, result)

            if i == len(cmds) - 1:  # If this is the last command in the pipeline
                result = self.call_partial_op(partial_op, result)
            else:
                composed = lambda x, f=partial_op, g=composed: f(g(x))
        return composed(result)

    def get_last_result(self) -> Any:
        return self.results[-1] if self.results else None

    def call_partial_op(self, partial_op: Callable, result: Any) -> Any:
        if callable(partial_op):
            arity = partial_op.func.aipl_arity if hasattr(partial_op, "func") else 0
            if arity == len(partial_op.args):
                return partial_op()
            else:
                return partial_op(result)
        else:
            return partial_op

    def parse_command(self, cmd: str) -> tuple[str, dict[str, Any]]:
        parts = cmd.split(maxsplit=1)
        cmd_name, arg_line = parts[0], parts[1] if len(parts) > 1 else ""

        args = {}
        arg_parts = re.findall(r"((\w+)=)?((?:\[[^\]]*\])|(?:\"\"\"(?:[^\"\\]*(?:\\.[^\"\\]*)*)\"\"\")|(?:\'\'\'(?:[^\'\\]*(?:\\.[^\'\\]*)*)\'\'\')|(?:\"(?:[^\"\\]*(?:\\.[^\"\\]*)*)\")|\S+)", arg_line)
        arg_position = 0
        for _, k, v in arg_parts:
            if k:
                args[k] = self.parse_value(v)
            else:
                args[str(arg_position)] = self.parse_value(v)
                arg_position += 1

        return cmd_name, args

    def parse_value(self, value: str) -> Any:
        if value.startswith("[") and value.endswith("]"):
            return [self.parse_number_or_str(x.strip()) for x in value[1:-1].split(",")]
        elif value.startswith('"') and value.endswith('"'):
            # Replace escaped newlines with actual newlines
            return value[1:-1].replace("\\n", "\n").replace('\\"', '"').replace('\\\\', '\\')
        else:
            return self.parse_number_or_str(value)

    def parse_number_or_str(self, value: str) -> Any:
        if value.startswith("$"):
            return self.parse_result_reference(value)
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    def parse_result_reference(self, value: str) -> Any:
        try:
            index = int(value[1:])
            return self.results[index]
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid result reference: {value}")

    def apply_operator(self, op_name: str, args: dict[str, Any], result: Any) -> Any:
        op = self.operators.get(op_name)
        if op:
            if self.should_pass_result(op, args, result):
                args = self.add_result_to_args(op, args, result)
            return self.call_operator(op, args)
        else:
            raise ValueError(f"Unknown operator: {op_name}")

    def should_pass_result(self, op: Callable, args: dict, result: Any) -> bool:
        return not result and len(args) < op.aipl_arity and not (op.aipl_needs_interpreter and len(args) == op.aipl_arity - 1)

    def add_result_to_args(self, op: Callable, args: dict, result: Any) -> dict:
        arg_types = get_type_hints(op)
        arg_types = [arg_types[arg] for arg in arg_types if arg not in {"return", "self"}]

        for i, arg_type in enumerate(arg_types):
            base_type = arg_type.__origin__ if hasattr(arg_type, "__origin__") else arg_type
            if isinstance(result, base_type) and i not in args:
                args[i] = result
                break

        return args

    def call_operator(self, op: Callable, args: dict) -> Any:
        if op.aipl_arity > len(args):
            if op.aipl_needs_interpreter:
                return partial(op, self, *list(args.values()))
            else:
                return partial(op, *list(args.values()))
        else:
            if op.aipl_needs_interpreter:
                return op(self, *list(args.values()))
            else:
                return op(*list(args.values()))

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
def op_inspect_op(aipl: AIPLInterpreter, op_name: str) -> None:
    import inspect
    op = aipl.operators.get(op_name)
    if op:
        print(f"Inspecting operator: {op_name}")
        print(inspect.getsource(op))
    else:
        raise ValueError(f"Operator not found: {op_name}")

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
def op_map_int(l: list[Any]) -> list[int]:
    return [int(x) for x in l]

@defop("map", rankin=1, rankout=1, arity=3, needs_interpreter=True)
def op_map(aipl: AIPLInterpreter, op_name: str, l: list[Any]) -> list[Any]:
    prev = aipl.get_last_result()
    return [aipl.apply_operator(op_name, {0: x}, prev) for x in l]


if __name__ == "__main__":
    script = """
    # !print "This is a multiline string.\\nIt has multiple lines.\\nYou can include quotes like this: \\" and use escape sequences like: \\\\."
    # ?print
    !input "Enter a list of numbers: "
    !input "Enter a separator: "
    !split s=$-2 sep=$-1
    !print
    !input "Enter a map operator: "
    !map $-1 $5
    !sum
    !print
    """

    interpreter = AIPLInterpreter()
    result = interpreter.process_script(script)
