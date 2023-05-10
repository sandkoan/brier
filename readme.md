- Types: string, number, list, dict, table (list of dicts), box (list of lists)

@defop registers the decorated function as the named operator.
rankin is what the function takes as input:
0: a scalar (number or string)
0.5: a whole row (dict)
1: a whole column of values
1.5: the whole table (array of rows)
rankout is what the function returns
0: a scalar value
0.5: a dict of values
1: a whole column of values
1.5: the whole table
arity for how many operands it takes; only 0 and 1 supported currently
The join operator is rankin=1 rankout=0 which means that it takes a list of strings and outputs a single string. Which it does.





- defer execution till all lines are parsed,
    allowing forward references, and allowing for loops, inspection/modification of the script, etc.
    - get a line by number as a string[] with `!lines`
    - get a line by number as a parsed object with `!linesobj`
    - get the whole script as a string[]
- refer to output from an arbitrary line with `$` and the line number
- allow modification of arbitrary lines with `!edit`

- parallel processing with `&`
- table processing with `|` and `||`
<!-- - `?` is a query -->

- chain/partially apply multiple operators with `|>` (syntactic sugar for `!chain`)
- split lines onto multiple lines with `\`



- escape characters with `\` in strings