from typing import Any, Callable, Dict, List

class AIPLInterpreter:
    def __init__(self):
        self.operators: Dict[str, Callable] = {}
        self.outputs: List[Any] = []

    def defop(self, name: str, rankin: int, rankout: int, arity: int):
        def decorator(func: Callable):
            self.operators[name] = func
            setattr(func, "rankin", rankin)
            setattr(func, "rankout", rankout)
            setattr(func, "arity", arity)
            return func
        return decorator

    def call_operator(self, op: str, *args: Any, **kwargs: Any) -> Any:
        if op not in self.operators:
            raise ValueError(f"Operator '{op}' not found")
        return self.operators[op](self, *args, **kwargs)

    def run_script(self, script: str) -> None:
        lines = script.strip().split("\n")
        for line in lines:
            if not line.startswith("!"):
                continue
            tokens = line[1:].split(" ")
            op = tokens[0]
            kwargs = {}
            for token in tokens[1:]:
                key, value = token.split("=")
                if value.startswith("$"):
                    value = self.outputs[int(value[1:])]
                kwargs[key] = value
            result = self.call_operator(op, **kwargs)
            self.outputs.append(result)


# Define some basic operators

aipl = AIPLInterpreter()

@aipl.defop("input", rankin=0, rankout=0.5, arity=1)
def op_input(aipl: AIPLInterpreter, prompt: str="") -> str:
    return input(prompt)

@aipl.defop("split", rankin=0.5, rankout=1, arity=2)
def op_split(aipl: AIPLInterpreter, v: str, sep: str) -> List[str]:
    return v.split(sep)

@aipl.defop("map", rankin=1, rankout=1, arity=2)
def op_map(aipl: AIPLInterpreter, v: List[Any], op: str) -> List[Any]:
    return [aipl.call_operator(op, v=x) for x in v]

@aipl.defop("int", rankin=0, rankout=0, arity=1)
def op_int(aipl: AIPLInterpreter, v: str) -> int:
    return int(v)

@aipl.defop("sum", rankin=1, rankout=0, arity=1)
def op_sum(aipl: AIPLInterpreter, v: List[int]) -> int:
    return sum(v)

@aipl.defop("format", rankin=0, rankout=0, arity=2)
def op_format(aipl: AIPLInterpreter, fmt: str, v: Any) -> str:
    return fmt.format(v)

@aipl.defop("print", rankin=0, rankout=None, arity=1)
def op_print(aipl: AIPLInterpreter, v: str) -> None:
    print(v)
    return v

if __name__ == "__main__":
    script = """
    !input prompt="Enter some numbers: "
    !input prompt="Enter a separator: "
    !split v=$1 sep=$2 |> map op="int" |> sum
    !format fmt="The sum is {}"
    !print
    """

    aipl.run_script(script)
