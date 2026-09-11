import io
import customtkinter as ctk

from contextlib import redirect_stdout

from App.app import TangibleProgrammingApp
from App.imageProcess import ImageProcessor
from Parsing.parse import Parser


# =========================================================
# PROGRAM EXECUTION
# =========================================================

def execute_python(
    python_code
):

    """
    Execute generated Python and capture anything
    printed by the program.
    """

    output_buffer = io.StringIO()


    try:

        with redirect_stdout(
            output_buffer
        ):

            exec(
                python_code,
                {}
            )


        output = (
            output_buffer.getvalue()
        )


        if not output:
            output = (
                "Program completed "
                "with no output."
            )


        return output


    except Exception as error:

        return (
            "Program Error:\n"
            + str(error)
        )


# =========================================================
# MAIN
# =========================================================

def main():

    image_processor = ImageProcessor()
    parser = Parser()

    root = ctk.CTk()

    app = None

    def handle_capture():

        try:

            image = image_processor.get_image()

            aruco_matrix = (
                image_processor.image_to_aruco_matrix(
                    image
                )
            )

            print("\nARUCO MATRIX")
            print("=" * 60)

            for index, row in enumerate(
                aruco_matrix
            ):
                print(
                    f"Row {index + 1}: {row}"
                )

            print("\nPRIMARY TRANSLATED SYNTAX")
            print("=" * 60)

            for index, row in enumerate(
                aruco_matrix
            ):

                tokens = parser.translate_row(
                    row
                )

                if tokens:
                    print(
                        f"Row {index + 1}: "
                        + " | ".join(tokens)
                    )

            statements = parser.create_statements(
                aruco_matrix
            )

            python_code = parser.convert_to_python(
                statements
            )

            app.set_python_code(
                python_code
            )

            output = execute_python(
                python_code
            )

            app.set_output(
                output
            )

        except Exception as error:

            app.set_python_code("")

            app.set_output(
                "Error:\n"
                + str(error)
            )


    app = TangibleProgrammingApp(
        root,
        handle_capture
    )

    root.mainloop()


if __name__ == "__main__":
    main()