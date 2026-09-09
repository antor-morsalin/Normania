from Data.arucoMap import ARUCO_TO_TOKEN
from Data.syntaxMap import SYNTAX_MAP


# Simple data structure

class Statement:

    def __init__(self, statement, statement_type):
        self.statement = statement
        self.statement_type = statement_type


# PARSER

class Parser:

    # ARUCO MATRIX -> STATEMENT OBJECTS

    def create_statements(self, aruco_matrix):

        statements = []

        for row in aruco_matrix:

            # Convert ArUco IDs to primary human-readable tokens
            tokens = self.translate_row(row)

            # Ignore empty rows
            if not tokens:
                continue

            # Determine what kind of statement this row is
            statement_type = self.get_statement_type(tokens)

            # Create Statement object
            statement = Statement(
                tokens,
                statement_type
            )

            statements.append(statement)

        return statements


    # RAW ARUCO IDs -> PRIMARY TOKENS

    def translate_row(self, row):

        tokens = []

        for aruco_id in row:

            # Empty board cell
            if aruco_id is None:
                continue

            # Unknown ArUco marker
            if aruco_id not in ARUCO_TO_TOKEN:
                raise ValueError(
                    f"Unknown ArUco ID: {aruco_id}"
                )

            tokens.append(
                ARUCO_TO_TOKEN[aruco_id]
            )

        return tokens


    # DETERMINE STATEMENT TYPE

    def get_statement_type(self, tokens):

        first_token = tokens[0]

        if first_token not in SYNTAX_MAP:
            raise ValueError(
                f"Unknown token: {first_token}"
            )

        token_type = SYNTAX_MAP[first_token]["type"]


        # X IS 5
        # X IS Y PLUS 3
        if token_type == "general_variable":
            return "general_assignment"


        # CONDITION1 IS X MORE THAN 5
        if token_type == "condition_variable":
            return "conditional_assignment"


        # SHOW X
        if token_type == "output_command":
            return "output"


        # IF X MORE THAN 5 THEN
        if token_type == "condition_opener":
            return "conditional"


        # REPEAT 3 TIMES
        if token_type == "repeat_opener":
            return "loop"


        # OTHERWISE
        # END
        if token_type in (
            "alternative_branch",
            "scope_closer"
        ):
            return "auxiliary"


        raise ValueError(
            f"Could not determine statement type: {tokens}"
        )

    # TRANSLATE ONE PRIMARY TOKEN -> PYTHON TOKEN

    def translate_token(self, token, context=None):

        if token not in SYNTAX_MAP:
            raise ValueError(
                f"Token not found in syntax map: {token}"
            )

        token_data = SYNTAX_MAP[token]

        if token == "IS":

            return str(
                token_data["syntax"][context]
            )

        if token == "TIMES":

            return str(
                token_data["syntax"][context]
            )

        # STRING LITERAL
        if token_data["type"] == "string_literal":

            return repr(
                token_data["syntax"]
            )

        return str(
            token_data["syntax"]
        )

    def parse_general_assignment(self, statement):

        parsed_tokens = []

        for token in statement.statement:

            # IS means assignment here
            if token == "IS":

                parsed_tokens.append(
                    self.translate_token(
                        token,
                        "assignment"
                    )
                )


            # TIMES means multiplication here
            elif token == "TIMES":

                parsed_tokens.append(
                    self.translate_token(
                        token,
                        "arithmetic"
                    )
                )


            # Everything else can be translated directly
            else:

                parsed_tokens.append(
                    self.translate_token(token)
                )


        return " ".join(parsed_tokens)


    def parse_conditional_assignment(self, statement):

        parsed_tokens = []

        for index, token in enumerate(statement.statement):

            if token == "IS":

                if index == 1:

                    parsed_tokens.append(
                        self.translate_token(
                            token,
                            "assignment"
                        )
                    )


                # Any IS inside the comparison means ==
                else:

                    parsed_tokens.append(
                        self.translate_token(
                            token,
                            "comparison"
                        )
                    )


            else:

                parsed_tokens.append(
                    self.translate_token(token)
                )


        return " ".join(parsed_tokens)


    def parse_output(self, statement):

        tokens = statement.statement

        command = self.translate_token(
            tokens[0]
        )

        value = self.translate_token(
            tokens[1]
        )

        return f"{command}({value})"

    def parse_conditional(self, statement):

        tokens = statement.statement

        # Translate IF using the map
        keyword = self.translate_token(
            tokens[0]
        )


        # Everything between IF and THEN
        condition_tokens = tokens[1:-1]

        parsed_tokens = []


        for token in condition_tokens:


            # IS inside an IF always means equality
            if token == "IS":

                parsed_tokens.append(
                    self.translate_token(
                        token,
                        "comparison"
                    )
                )


            else:

                parsed_tokens.append(
                    self.translate_token(token)
                )


        condition = " ".join(parsed_tokens)


        # THEN disappears.
        # Colon is added manually.
        return f"{keyword} {condition}:"

    def parse_loop(self, statement):

        tokens = statement.statement

        # REPEAT maps to "for"
        keyword = self.translate_token(
            tokens[0]
        )

        # Number of repetitions
        amount = self.translate_token(
            tokens[1]
        )


        # TIMES is structural here.
        # It is not translated into *.
        return f"{keyword} _ in range({amount}):"

    def handle_auxiliary(
        self,
        statement,
        scope_stack,
        indent_level
    ):

        token = statement.statement[0]


        # -------------------------------------------------
        # OTHERWISE
        # -------------------------------------------------

        if token == "OTHERWISE":


            # Must have an open scope
            if not scope_stack:

                raise ValueError(
                    "OTHERWISE used without an open IF."
                )


            # Nearest scope must be IF
            if scope_stack[-1] != "if":

                raise ValueError(
                    "OTHERWISE must belong to an open IF."
                )


            # Leave the IF body indentation
            indent_level -= 1


            # OTHERWISE maps to "else"
            keyword = self.translate_token(
                token
            )


            line = (
                "    " * indent_level
                + f"{keyword}:"
            )


            # Change the open IF to ELSE
            # so another OTHERWISE cannot be used
            scope_stack[-1] = "else"


            # Enter ELSE body
            indent_level += 1


            return line, indent_level


        # -------------------------------------------------
        # END
        # -------------------------------------------------

        if token == "END":


            if not scope_stack:

                raise ValueError(
                    "END used without an open IF or REPEAT."
                )


            # Close nearest scope
            scope_stack.pop()

            indent_level -= 1


            # END generates no Python code
            return None, indent_level


        raise ValueError(
            f"Unknown auxiliary token: {token}"
        )

    # STATEMENT OBJECTS -> COMPLETE PYTHON CODE

    def convert_to_python(self, statements):

        python_lines = []

        indent_level = 0

        # Tracks open IF / ELSE / LOOP scopes
        scope_stack = []


        for statement in statements:

            statement_type = statement.statement_type

            # AUXILIARY
            if statement_type == "auxiliary":

                line, indent_level = self.handle_auxiliary(
                    statement,
                    scope_stack,
                    indent_level
                )


                # END returns None because END produces no code
                if line is not None:
                    python_lines.append(line)


                continue


            # GENERAL ASSIGNMENT

            if statement_type == "general_assignment":

                line = self.parse_general_assignment(
                    statement
                )


            # CONDITIONAL ASSIGNMENT

            elif statement_type == "conditional_assignment":

                line = self.parse_conditional_assignment(
                    statement
                )


            # OUTPUT

            elif statement_type == "output":

                line = self.parse_output(
                    statement
                )


            # IF

            elif statement_type == "conditional":

                line = self.parse_conditional(
                    statement
                )


            # REPEAT

            elif statement_type == "loop":

                line = self.parse_loop(
                    statement
                )


            else:

                raise ValueError(
                    f"Unknown statement type: {statement_type}"
                )


            python_lines.append(
                "    " * indent_level
                + line
            )


            # OPEN NEW SCOPE

            if statement_type == "conditional":

                scope_stack.append("if")

                indent_level += 1


            elif statement_type == "loop":

                scope_stack.append("loop")

                indent_level += 1


        # MAKE SURE ALL SCOPES WERE CLOSED

        if scope_stack:

            raise ValueError(
                "Program ended before an IF or REPEAT "
                "was closed with END."
            )


        # Convert list of Python lines into one Python program
        return "\n".join(python_lines)