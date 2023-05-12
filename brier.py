from brier import AIPLInterpreter


def repl():
    aipl = AIPLInterpreter()
    print("Welcome to the Brier REPL")
    print("Enter your commands, or type 'exit' to quit")

    input_history = []

    while True:
        try:
            line = input("> ")
            if line.lower() == "exit":
                break
            elif line.lower().startswith("save"):
                save_history(input_history, line.split(maxsplit=1)[-1].strip())
            else:
                input_history.append(line + "\n")
                result = aipl.process_line(line)
                aipl.results.append(result)
        except Exception as e:
            print(f"Error: {e}")

def save_history(history, file_name):
    if not file_name:
        print("Error: Please provide a file name after `save`")
        return

    try:
        with open(file_name, "w") as f:
            f.writelines(history)
        print(f"Saved input history to `{file_name}`")
    except Exception as e:
        print(f"Error saving history to file: `{e}`")


def run_file(file_name):
    with open(file_name, "r") as f:
        script = f.read()
    aipl = AIPLInterpreter()
    aipl.process_script(script)

if __name__ == "__main__":
    repl()
