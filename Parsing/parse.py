"""Validate physical rows before generating Python and matching scopes."""
from dataclasses import dataclass
from numbers import Integral
from Data.arucoMap import ARUCO_TO_TOKEN
from Data.syntaxMap import SYNTAX_MAP

BOARD_ROWS, BOARD_COLUMNS = 6, 5


class ProgramValidationError(ValueError):
    def __init__(self, message, row=None):
        self.row = row
        super().__init__(f"Row {row}: {message}" if row is not None else message)


@dataclass
class Statement:
    statement: list
    statement_type: str
    row_number: int = None


@dataclass
class _Scope:
    kind: str
    row: int
    has_body: bool = False
    has_else: bool = False


class Parser:
    """One statement per physical row; empty cells never become tokens."""
    def __init__(self):
        self.line_map = {}

    def create_statements(self, aruco_matrix):
        if aruco_matrix is None:
            raise ProgramValidationError("No board was read. Capture the board again.")
        rows = list(aruco_matrix)
        if len(rows) > BOARD_ROWS:
            raise ProgramValidationError("The board supports at most 6 rows.")
        statements = []
        for row_number, row in enumerate(rows, 1):
            tokens = self.translate_row(row, row_number)
            if tokens:
                try:
                    kind = self.get_statement_type(tokens)
                except ProgramValidationError as error:
                    raise ProgramValidationError(str(error), row_number) from error
                statement = Statement(tokens, kind, row_number)
                # Validate rows before scope errors can hide a missing token.
                self.validate_statement(statement)
                statements.append(statement)
        return statements

    def translate_row(self, row, row_number=None):
        if row is None or isinstance(row, (str, bytes)):
            raise ProgramValidationError("This is not a valid board row.", row_number)
        try:
            cells = list(row)
        except TypeError as error:
            raise ProgramValidationError("This is not a valid board row.", row_number) from error
        if len(cells) > BOARD_COLUMNS:
            raise ProgramValidationError("Keep each instruction within 5 cells.", row_number)
        tokens = []
        for column, marker_id in enumerate(cells, 1):
            if marker_id is None:
                continue
            if (isinstance(marker_id, bool) or not isinstance(marker_id, Integral)
                    or marker_id not in ARUCO_TO_TOKEN):
                raise ProgramValidationError(
                    f"Unknown block {marker_id!r} in column {column}. Check its marker.", row_number)
            tokens.append(ARUCO_TO_TOKEN[int(marker_id)])
        return tokens

    def get_statement_type(self, tokens):
        if not tokens:
            raise ProgramValidationError("This instruction is empty.")
        first = tokens[0]
        token_type = SYNTAX_MAP.get(first, {}).get("type")
        types = {"general_variable": "general_assignment",
                 "condition_variable": "conditional_assignment", "output_command": "output",
                 "condition_opener": "conditional", "repeat_opener": "loop",
                 "alternative_branch": "auxiliary", "scope_closer": "auxiliary"}
        if token_type not in types:
            raise ProgramValidationError(
                f"An instruction cannot start with {first}. Check for a missing first block.")
        return types[token_type]

    @staticmethod
    def _is(token, *types):
        return SYNTAX_MAP.get(token, {}).get("type") in types

    def _value(self, token):
        return self._is(token, "general_variable", "number_literal", "string_literal")

    def _comparison(self, tokens):
        return (len(tokens) == 3 and self._value(tokens[0]) and self._value(tokens[2])
                and (tokens[1] == "IS" or self._is(tokens[1], "comparison_operator")))

    def _boolean(self, tokens):
        return ((len(tokens) == 1 and self._is(tokens[0], "condition_variable"))
                or (len(tokens) == 3 and tokens[1] in ("AND", "OR")
                    and self._is(tokens[0], "condition_variable")
                    and self._is(tokens[2], "condition_variable")))

    def validate_statement(self, statement):
        tokens, row = statement.statement, statement.row_number
        def fail(message):
            raise ProgramValidationError(message, row)
        if not tokens:
            fail("This instruction is empty.")
        for token in tokens:
            if token not in SYNTAX_MAP:
                fail(f"Unknown token: {token}.")
        if len(tokens) > BOARD_COLUMNS:
            fail("Keep each instruction within 5 cells; instructions cannot wrap to another row.")
        try:
            expected_type = self.get_statement_type(tokens)
        except ProgramValidationError as error:
            fail(str(error))
        if statement.statement_type != expected_type:
            fail("The instruction type does not match its first block.")
        first = tokens[0]
        if expected_type in ("general_assignment", "conditional_assignment"):
            if len(tokens) < 2 or tokens[1] != "IS":
                fail(f"{first} needs IS followed by a value. Check whether IS was missed by the camera.")
            if expected_type == "conditional_assignment":
                if not self._comparison(tokens[2:]):
                    fail(f"Use {first} IS value comparison value, for example {first} IS X MORE THAN 5.")
            elif not ((len(tokens) == 3 and self._value(tokens[2]))
                      or (len(tokens) == 5 and self._value(tokens[2]) and self._value(tokens[4])
                          and tokens[3] in ("PLUS", "MINUS", "TIMES", "DIVIDED BY"))):
                fail(f"Use {first} IS value, or {first} IS value operator value. Check for a missing block.")
        elif first == "SHOW":
            if len(tokens) != 2 or not self._value(tokens[1]):
                fail("SHOW needs exactly one value block (a number, message, or variable). "
                     "If that block is already there, make its marker visible and recapture.")
        elif first == "IF":
            if tokens[-1] != "THEN":
                fail("IF needs THEN at the end of this row. Check whether THEN was missed by the camera.")
            if not (self._comparison(tokens[1:-1]) or self._boolean(tokens[1:-1])):
                fail("Use IF X MORE THAN 5 THEN, IF CONDITION1 THEN, or "
                     "IF CONDITION1 AND CONDITION2 THEN. Check for a missing value or comparison.")
        elif first == "REPEAT":
            if (len(tokens) != 3 or tokens[-1] != "TIMES"
                    or not self._is(tokens[1], "number_literal", "general_variable")):
                fail("Use REPEAT number TIMES or REPEAT variable TIMES. The value must be a whole number.")
        elif len(tokens) != 1:
            fail(f"{first} must be alone on its row; move the other blocks to a separate row.")

    def translate_token(self, token, context=None):
        if token not in SYNTAX_MAP:
            raise ProgramValidationError(f"Unknown token: {token}.")
        data = SYNTAX_MAP[token]
        syntax = data["syntax"]
        if isinstance(syntax, dict):
            if context not in syntax:
                raise ProgramValidationError(f"{token} needs a valid statement context.")
            syntax = syntax[context]
        if data["type"] == "string_literal":
            return repr(syntax)
        return "" if syntax is None else str(syntax)

    def _expression(self, tokens):
        return " ".join(self.translate_token(
            token, "comparison" if token == "IS" else "arithmetic" if token == "TIMES" else None
        ) for token in tokens)

    def parse_general_assignment(self, statement):
        self.validate_statement(statement)
        tokens = statement.statement
        return f"{self.translate_token(tokens[0])} = {self._expression(tokens[2:])}"

    parse_conditional_assignment = parse_general_assignment

    def parse_output(self, statement):
        self.validate_statement(statement)
        return f"print({self.translate_token(statement.statement[1])})"

    def parse_conditional(self, statement):
        self.validate_statement(statement)
        return f"if {self._expression(statement.statement[1:-1])}:"

    def parse_loop(self, statement):
        self.validate_statement(statement)
        return f"for _ in range({self.translate_token(statement.statement[1])}):"

    def convert_to_python(self, statements):
        self.line_map = {}
        statements = list(statements)
        if len(statements) > BOARD_ROWS:
            raise ProgramValidationError("The board supports at most 6 rows.")
        for index, statement in enumerate(statements, 1):
            if statement.row_number is None:
                statement.row_number = index
            self.validate_statement(statement)
        lines, scopes = [], []
        just_closed_if = None
        def emit(text, depth, row):
            lines.append("    " * depth + text)
            self.line_map[len(lines)] = row
        for statement in statements:
            first, row = statement.statement[0], statement.row_number
            # Support both IF / OTHERWISE / END and IF / END / OTHERWISE / END.
            # An already-open IF takes precedence, preserving nested scope rules.
            # A closed IF is eligible only for the next nonempty instruction.
            if (first == "OTHERWISE" and just_closed_if is not None
                    and (not scopes or scopes[-1].kind != "IF")):
                scopes.append(just_closed_if)
            just_closed_if = None
            if first == "OTHERWISE":
                if not scopes:
                    raise ProgramValidationError(
                        "OTHERWISE needs an open IF. Check that the IF row was detected.", row)
                scope = scopes[-1]
                if scope.kind != "IF":
                    raise ProgramValidationError(
                        f"Close REPEAT from row {scope.row} with END before OTHERWISE.", row)
                if scope.has_else:
                    raise ProgramValidationError(f"IF from row {scope.row} already has OTHERWISE.", row)
                if not scope.has_body:
                    raise ProgramValidationError(
                        f"IF from row {scope.row} has no instruction before OTHERWISE. Check for a missed row.", row)
                emit("else:", len(scopes) - 1, row)
                scope.has_else, scope.has_body = True, False
                continue
            if first == "END":
                if not scopes:
                    raise ProgramValidationError(
                        "END has no open IF or REPEAT to close. Check that the opening row was "
                        "detected and that there is only one END per structure.", row)
                scope = scopes[-1]
                if not scope.has_body:
                    branch = "OTHERWISE" if scope.has_else else scope.kind
                    raise ProgramValidationError(
                        f"{branch} from the structure at row {scope.row} needs an instruction before END. "
                        "Check for a missed row.", row)
                scopes.pop()
                if scope.kind == "IF" and not scope.has_else:
                    just_closed_if = scope
                continue
            if scopes:
                scopes[-1].has_body = True
            translator = {"general_assignment": self.parse_general_assignment,
                          "conditional_assignment": self.parse_conditional_assignment,
                          "output": self.parse_output, "conditional": self.parse_conditional,
                          "loop": self.parse_loop}[statement.statement_type]
            emit(translator(statement), len(scopes), row)
            if first in ("IF", "REPEAT"):
                scopes.append(_Scope(first, row))
        if scopes:
            scope = scopes[-1]
            raise ProgramValidationError(f"{scope.kind} needs a matching END before the board ends.", scope.row)
        code = "\n".join(lines)
        try:
            compile(code, "<Normania>", "exec")
        except SyntaxError as error:
            raise ProgramValidationError("This instruction could not be compiled.",
                                         self.line_map.get(error.lineno)) from error
        return code
