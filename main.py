"""Normania GUI and camera-free replay of saved images or marker matrices."""
import argparse
import ast
import io
import json
from pathlib import Path
import sys
import time

from Parsing.parse import Parser


def execute_python(python_code, source_rows=None, *, max_steps=20000, timeout=2.0, output_limit=20000):
    """Execute the displayed code with bounded loops/output and board-row errors."""
    output = io.StringIO()
    previous_trace = sys.gettrace()
    current_line = None
    filename = "<Normania>"
    steps = 0
    checks = {}
    source_rows = source_rows or {}

    def print_value(*values, sep=" ", end="\n"):
        text = sep.join(str(v) for v in values) + end
        if output.tell() + len(text) > output_limit:
            raise ValueError("The output is too long. Use fewer repetitions.")
        output.write(text)

    def repeat_range(value):
        if type(value) is not int or value < 0:
            raise ValueError("REPEAT needs a non-negative whole number. Check the value of its variable.")
        return range(value)

    def operand_value(node, variables):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in variables:
                raise NameError(f"{node.id.upper()} has no value yet.", name=node.id)
            return variables[node.id]
        raise ValueError("Use only one arithmetic operator in each instruction.")

    def trace(frame, event, arg):
        nonlocal steps, current_line
        if frame.f_code.co_filename != filename:
            return None
        if event == "line":
            current_line = frame.f_lineno
            steps += 1
            if steps > max_steps or time.monotonic() - started > timeout:
                raise ValueError("This program repeats too much. Reduce the number of repetitions.")
            for operands in checks.get(current_line, []):
                if any(type(operand_value(n, frame.f_locals)) not in (int, float) for n in operands):
                    raise ValueError("Arithmetic and ordering comparisons need numbers, not message blocks.")
        return trace

    try:
        if not isinstance(python_code, str) or len(python_code) > 4096:
            raise ValueError("The generated program is invalid or too long.")
        tree = ast.parse(python_code, filename=filename)
        # This entry point accepts the board language's generated Python only.
        allowed = (ast.Module, ast.Assign, ast.Name, ast.Store, ast.Load, ast.Constant,
                   ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Compare,
                   ast.Eq, ast.NotEq, ast.Gt, ast.GtE, ast.Lt, ast.LtE,
                   ast.BoolOp, ast.And, ast.Or, ast.If, ast.For, ast.Expr, ast.Call)
        names = {"a", "b", "c", "x", "y", "z", "condition1", "condition2", "_", "range", "print"}
        for node in ast.walk(tree):
            if not isinstance(node, allowed):
                raise ValueError("This program contains an instruction outside the board language.")
            if isinstance(node, ast.Name) and node.id not in names:
                raise ValueError(f"Unknown variable: {node.id}.")
            if isinstance(node, ast.Call) and (not isinstance(node.func, ast.Name)
                    or node.func.id not in ("print", "range") or len(node.args) != 1 or node.keywords):
                raise ValueError("This program contains an unsupported command.")
            if isinstance(node, ast.BinOp):
                checks.setdefault(node.lineno, []).append((node.left, node.right))
            if isinstance(node, ast.Compare) and any(isinstance(op, (ast.Gt, ast.GtE, ast.Lt, ast.LtE)) for op in node.ops):
                checks.setdefault(node.lineno, []).append((node.left, *node.comparators))
        code = compile(tree, filename, "exec")
        started = time.monotonic()
        sys.settrace(trace)
        exec(code, {"__builtins__": {"print": print_value, "range": repeat_range}})
        return output.getvalue() or "Program completed with no output."
    except Exception as error:
        row = source_rows.get(current_line)
        location = f"Row {row}: " if row is not None else ""
        if isinstance(error, NameError):
            message = f"{(getattr(error, 'name', None) or 'Variable').upper()} has no value yet. Assign it with IS before using it."
        elif isinstance(error, ZeroDivisionError):
            message = "A number cannot be divided by zero."
        else:
            message = str(error)
        partial = output.getvalue()
        suffix = "\n\nOutput before the error:\n" + partial if partial else ""
        return "Program Error:\n" + location + message + suffix
    finally:
        sys.settrace(previous_trace)


def main(argv=None):
    arguments = argparse.ArgumentParser(description="Run Normania or replay a saved board.")
    source = arguments.add_mutually_exclusive_group()
    source.add_argument("--matrix", type=Path, help="JSON matrix or last_capture.json")
    source.add_argument("--image", type=Path, help="Saved board photograph")
    arguments.add_argument("--debug", type=Path, help="Save detected_board.png and last_capture.json")
    arguments.add_argument("--camera", type=int, default=0, help="Camera device index (default 0)")
    args = arguments.parse_args(argv)
    parser = Parser()
    if args.matrix or args.image:
        try:
            if args.matrix:
                data = json.loads(args.matrix.read_text(encoding="utf-8"))
                matrix = data["matrix"] if isinstance(data, dict) else data
            else:
                import cv2
                from App.imageProcess import ImageProcessor
                processor = ImageProcessor()
                image = cv2.imread(str(args.image))
                scan = processor.scan_image(image)
                matrix = scan.matrix
                if args.debug:
                    processor.save_debug(image, scan, args.debug)
            statements = parser.create_statements(matrix)
            if not statements:
                raise ValueError("No programming blocks were read.")
            code = parser.convert_to_python(statements)
            print("PYTHON\n" + code + "\n\nOUTPUT")
            output = execute_python(code, parser.line_map)
            print(output, end="" if output.endswith("\n") else "\n")
            return 1 if output.startswith("Program Error:") else 0
        except Exception as error:
            print(f"Board Error: {error}", file=sys.stderr)
            return 1

    import customtkinter as ctk
    from App.app import TangibleProgrammingApp
    from App.imageProcess import ImageProcessor, print_aruco_matrix, print_primary_syntax
    image_processor = ImageProcessor()
    root = ctk.CTk()
    app = None

    def handle_capture():
        image = image_processor.get_image(parent=root, camera_index=args.camera)
        if image is None:
            return False
        # Reuse the exact matrix that passed capture validation. Re-detecting
        # the saved image could yield a different program from a later pass.
        matrix = image_processor.last_capture.matrix
        print_aruco_matrix(matrix)
        print_primary_syntax(parser, matrix)
        app.set_detected_rows(matrix)
        code = parser.convert_to_python(parser.create_statements(matrix))
        app.set_python_code(code)
        output = execute_python(code, parser.line_map)
        app.set_output(output)
        return "program_error" if output.startswith("Program Error:") else True

    app = TangibleProgrammingApp(root, handle_capture)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
