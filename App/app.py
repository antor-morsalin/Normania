import tkinter as tk
import customtkinter as ctk
# Theme
BACKGROUND = "#F7F6FC"

NAVY = "#282548"
NAVY_SOFT = "#35315B"

WHITE = "#FFFFFF"

TEXT = "#282548"
TEXT_SECONDARY = "#76728C"

PURPLE = "#7457E8"
PURPLE_HOVER = "#6346D8"
PURPLE_SOFT = "#ECE8FF"

PINK = "#F75C96"
PINK_SOFT = "#FFE5EF"

YELLOW = "#F4C84C"
YELLOW_SOFT = "#FFF2BA"

GREEN = "#3FC78A"
GREEN_SOFT = "#DDF7EB"

BLUE = "#4CA7F2"
BLUE_SOFT = "#E5F4FF"

BORDER = "#E3DFEF"

CODE_BACKGROUND = "#24223F"
CODE_TEXT = "#F7F6FF"

OUTPUT_BACKGROUND = "#FFFFFF"
# Customtkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
# App
class TangibleProgrammingApp:

    def __init__(
        self,
        root,
        capture_callback
    ):

        self.root = root
        self.capture_callback = capture_callback
        # Window
        self.root.title("Normania")

        self.root.geometry(
            "1250x800"
        )

        self.root.minsize(
            1000,
            680
        )

        self.root.configure(
            fg_color=BACKGROUND
        )

        self.root.grid_columnconfigure(
            0,
            weight=1
        )

        self.root.grid_rowconfigure(
            1,
            weight=1
        )
        # Build
        self.build_header()

        self.build_content()
    # Header
    def build_header(self):

        header = ctk.CTkFrame(
            self.root,
            height=90,
            fg_color=NAVY,
            corner_radius=0
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        header.grid_propagate(False)

        header.grid_columnconfigure(
            0,
            weight=1
        )
        # Brand
        brand = ctk.CTkFrame(
            header,
            fg_color="transparent"
        )

        brand.grid(
            row=0,
            column=0,
            sticky="w",
            padx=38,
            pady=16
        )

        title = ctk.CTkLabel(
            brand,
            text="NORMANIA",
            font=ctk.CTkFont(
                size=29,
                weight="bold"
            ),
            text_color=WHITE
        )

        title.pack(
            anchor="w"
        )

        subtitle = ctk.CTkLabel(
            brand,
            text="Build with blocks. Turn them into code.",
            font=ctk.CTkFont(
                size=13
            ),
            text_color="#CECBE1"
        )

        subtitle.pack(
            anchor="w",
            pady=(2, 0)
        )
    # Main content
    def build_content(self):

        content = ctk.CTkFrame(
            self.root,
            fg_color=BACKGROUND,
            corner_radius=0
        )

        content.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        content.grid_columnconfigure(
            0,
            weight=1
        )

        content.grid_rowconfigure(
            2,
            weight=1
        )

        self.build_steps(
            content
        )

        self.build_capture_station(
            content
        )

        self.build_results(
            content
        )
    # Top steps
    def build_steps(self, parent):

        steps = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        steps.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=36,
            pady=(20, 14)
        )

        steps.grid_columnconfigure(
            0,
            weight=1
        )

        steps.grid_columnconfigure(
            1,
            weight=0
        )

        steps.grid_columnconfigure(
            2,
            weight=1
        )

        steps.grid_columnconfigure(
            3,
            weight=0
        )

        steps.grid_columnconfigure(
            4,
            weight=1
        )

        self.create_step(
            steps,
            column=0,
            number="1",
            title="BUILD",
            description="Arrange your blocks",
            color=YELLOW,
            background=YELLOW_SOFT
        )

        self.create_arrow(
            steps,
            column=1
        )

        self.create_step(
            steps,
            column=2,
            number="2",
            title="CAPTURE",
            description="Show us your board",
            color=PINK,
            background=PINK_SOFT
        )

        self.create_arrow(
            steps,
            column=3
        )

        self.create_step(
            steps,
            column=4,
            number="3",
            title="RUN",
            description="See what happens",
            color=GREEN,
            background=GREEN_SOFT
        )
    # Step card
    def create_step(
        self,
        parent,
        column,
        number,
        title,
        description,
        color,
        background
    ):

        card = ctk.CTkFrame(
            parent,
            height=100,
            fg_color=background,
            corner_radius=24
        )

        card.grid(
            row=0,
            column=column,
            sticky="ew",
            padx=8
        )

        card.grid_propagate(False)

        card.grid_columnconfigure(
            1,
            weight=1
        )

        number_label = ctk.CTkLabel(
            card,
            text=number,
            width=52,
            height=52,
            corner_radius=26,
            fg_color=color,
            text_color=WHITE,
            font=ctk.CTkFont(
                size=19,
                weight="bold"
            )
        )

        number_label.grid(
            row=0,
            column=0,
            rowspan=2,
            padx=(20, 15),
            pady=24
        )

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(
                size=17,
                weight="bold"
            ),
            text_color=TEXT
        )

        title_label.grid(
            row=0,
            column=1,
            sticky="sw",
            pady=(22, 1)
        )

        description_label = ctk.CTkLabel(
            card,
            text=description,
            font=ctk.CTkFont(
                size=12
            ),
            text_color=TEXT_SECONDARY
        )

        description_label.grid(
            row=1,
            column=1,
            sticky="nw",
            pady=(0, 22)
        )
    # Step arrow
    def create_arrow(
        self,
        parent,
        column
    ):

        arrow = ctk.CTkLabel(
            parent,
            text="→",
            font=ctk.CTkFont(
                size=30,
                weight="bold"
            ),
            text_color="#ACA7BE"
        )

        arrow.grid(
            row=0,
            column=column,
            padx=6
        )
    # Capture station
    def build_capture_station(self, parent):

        station = ctk.CTkFrame(
            parent,
            height=195,
            fg_color=WHITE,
            border_width=1,
            border_color=BORDER,
            corner_radius=24
        )

        station.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=44,
            pady=(0, 18)
        )

        station.grid_propagate(False)

        station.grid_columnconfigure(
            0,
            weight=3
        )

        station.grid_columnconfigure(
            1,
            weight=4
        )
        # Board preview side
        preview_area = ctk.CTkFrame(
            station,
            fg_color=BLUE_SOFT,
            corner_radius=18
        )

        preview_area.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(16, 10),
            pady=14
        )

        preview_area.grid_columnconfigure(
            1,
            weight=1
        )
        # Mini board visual
        board_frame = ctk.CTkFrame(
            preview_area,
            fg_color="transparent"
        )

        board_frame.grid(
            row=0,
            column=0,
            padx=(18, 12),
            pady=10
        )


        self.board_canvas = tk.Canvas(
            board_frame,
            width=120,
            height=120,
            bg=BLUE_SOFT,
            highlightthickness=0
        )

        self.board_canvas.pack()

        self.draw_board_preview()
        # Preview text
        preview_text = ctk.CTkFrame(
            preview_area,
            fg_color="transparent"
        )

        preview_text.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(0, 14)
        )


        preview_label = ctk.CTkLabel(
            preview_text,
            text="BOARD PREVIEW",
            font=ctk.CTkFont(
                size=11,
                weight="bold"
            ),
            text_color=BLUE
        )

        preview_label.pack(
            anchor="w"
        )


        preview_title = ctk.CTkLabel(
            preview_text,
            text="Show us what you built",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            ),
            text_color=TEXT
        )

        preview_title.pack(
            anchor="w",
            pady=(2, 3)
        )


        preview_description = ctk.CTkLabel(
            preview_text,
            text=(
                "Press capture to open the camera.\n"
                "Show all four corner markers."
            ),
            font=ctk.CTkFont(
                size=11
            ),
            text_color=TEXT_SECONDARY,
            justify="left"
        )

        preview_description.pack(
            anchor="w"
        )
        # Capture side
        capture_area = ctk.CTkFrame(
            station,
            fg_color="transparent"
        )

        capture_area.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(25, 26),
            pady=20
        )

        capture_area.grid_columnconfigure(
            0,
            weight=1
        )


        capture_title = ctk.CTkLabel(
            capture_area,
            text="Ready to try your program?",
            font=ctk.CTkFont(
                size=21,
                weight="bold"
            ),
            text_color=TEXT
        )

        capture_title.grid(
            row=0,
            column=0,
            pady=(3, 3)
        )


        capture_description = ctk.CTkLabel(
            capture_area,
            text=(
                "Hold your board where the camera can see it, "
                "then capture."
            ),
            font=ctk.CTkFont(
                size=12
            ),
            text_color=TEXT_SECONDARY
        )

        capture_description.grid(
            row=1,
            column=0,
            pady=(0, 12)
        )


        self.capture_button = ctk.CTkButton(
            capture_area,
            text="CAPTURE BOARD",
            command=self.handle_capture,
            width=285,
            height=58,
            corner_radius=29,
            fg_color=PURPLE,
            hover_color=PURPLE_HOVER,
            text_color=WHITE,
            font=ctk.CTkFont(
                size=17,
                weight="bold"
            )
        )

        self.capture_button.grid(
            row=2,
            column=0
        )


        self.capture_status = ctk.CTkLabel(
            capture_area,
            text="Press capture when your board is ready",
            font=ctk.CTkFont(
                size=10
            ),
            text_color=TEXT_SECONDARY
        )

        self.capture_status.grid(
            row=3,
            column=0,
            pady=(7, 0)
        )
    # Draw mini board
    def draw_board_preview(self):

        canvas = self.board_canvas

        canvas.delete("all")

        x0 = 17
        y0 = 9

        width = 90
        height = 108

        columns = 5
        rows = 6

        cell_width = width / columns
        cell_height = height / rows


        # Board background

        canvas.create_rectangle(
            x0,
            y0,
            x0 + width,
            y0 + height,
            fill=WHITE,
            outline="#B9DDF6",
            width=2
        )


        # Grid

        for column in range(
            1,
            columns
        ):

            x = (
                x0
                + column * cell_width
            )

            canvas.create_line(
                x,
                y0,
                x,
                y0 + height,
                fill="#D5EAF8"
            )


        for row in range(
            1,
            rows
        ):

            y = (
                y0
                + row * cell_height
            )

            canvas.create_line(
                x0,
                y,
                x0 + width,
                y,
                fill="#D5EAF8"
            )
        # Decorative blocks
        blocks = [
            (0, 0, PURPLE),
            (0, 1, PINK),
            (0, 2, YELLOW),

            (2, 0, GREEN),
            (2, 1, BLUE),

            (4, 0, PURPLE)
        ]


        for row, column, color in blocks:

            left = (
                x0
                + column * cell_width
                + 2
            )

            top = (
                y0
                + row * cell_height
                + 2
            )

            right = (
                left
                + cell_width
                - 4
            )

            bottom = (
                top
                + cell_height
                - 4
            )

            canvas.create_rectangle(
                left,
                top,
                right,
                bottom,
                fill=color,
                outline=""
            )
    # Results
    def build_results(self, parent):

        results = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        results.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=36,
            pady=(0, 24)
        )

        results.grid_columnconfigure(
            0,
            weight=1
        )

        results.grid_columnconfigure(
            1,
            weight=1
        )

        results.grid_rowconfigure(
            0,
            weight=1
        )

        self.build_python_panel(
            results
        )

        self.build_output_panel(
            results
        )
    # Python panel
    def build_python_panel(self, parent):

        card = ctk.CTkFrame(
            parent,
            fg_color=PURPLE_SOFT,
            corner_radius=24
        )

        card.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10)
        )
        # Header
        header = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        header.pack(
            fill="x",
            padx=18,
            pady=(12, 7)
        )


        label = ctk.CTkLabel(
            header,
            text="PYTHON",
            width=94,
            height=32,
            corner_radius=16,
            fg_color=PURPLE,
            text_color=WHITE,
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            )
        )

        label.pack(
            side="left"
        )


        helper = ctk.CTkLabel(
            header,
            text="Generated from your blocks",
            font=ctk.CTkFont(
                size=11
            ),
            text_color=TEXT_SECONDARY
        )

        helper.pack(
            side="left",
            padx=12
        )
        # Code textbox
        self.python_text = ctk.CTkTextbox(
            card,
            fg_color=CODE_BACKGROUND,
            text_color=CODE_TEXT,
            corner_radius=18,
            border_width=0,
            font=ctk.CTkFont(
                family="Courier",
                size=14
            ),
            wrap="none"
        )

        self.python_text.pack(
            fill="both",
            expand=True,
            padx=14,
            pady=(0, 14)
        )


        self.python_text.insert(
            "1.0",
            "# Your Python code will appear here"
        )

        self.python_text.configure(
            state="disabled"
        )
    # Output panel
    def build_output_panel(self, parent):

        card = ctk.CTkFrame(
            parent,
            fg_color=GREEN_SOFT,
            corner_radius=24
        )

        card.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(10, 0)
        )
        # Header
        header = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        header.pack(
            fill="x",
            padx=18,
            pady=(12, 7)
        )


        label = ctk.CTkLabel(
            header,
            text="OUTPUT",
            width=94,
            height=32,
            corner_radius=16,
            fg_color=GREEN,
            text_color=WHITE,
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            )
        )

        label.pack(
            side="left"
        )


        helper = ctk.CTkLabel(
            header,
            text="Result of your program",
            font=ctk.CTkFont(
                size=11
            ),
            text_color=TEXT_SECONDARY
        )

        helper.pack(
            side="left",
            padx=12
        )
        # Output textbox
        self.output_text = ctk.CTkTextbox(
            card,
            fg_color=OUTPUT_BACKGROUND,
            text_color=TEXT,
            corner_radius=18,
            border_width=0,
            font=ctk.CTkFont(
                size=15
            ),
            wrap="word"
        )

        self.output_text.pack(
            fill="both",
            expand=True,
            padx=14,
            pady=(0, 14)
        )


        self.output_text.insert(
            "1.0",
            "Your program's output will appear here."
        )

        self.output_text.configure(
            state="disabled"
        )
    # Capture
    def handle_capture(self):
        # Processing state
        self.capture_button.configure(
            text="READING BOARD...",
            state="disabled",
            fg_color=PINK
        )

        self.capture_status.configure(
            text="Finding your blocks...",
            text_color=PINK
        )

        self.root.update_idletasks()


        try:
            # Main application callback
            if self.capture_callback() is False:
                self.capture_status.configure(
                    text="Capture cancelled.",
                    text_color=TEXT_SECONDARY
                )
                return
            # Complete
            self.capture_status.configure(
                text="Capture complete!",
                text_color=GREEN
            )


        except Exception:
            # Error
            self.capture_status.configure(
                text="Couldn't read the board. Try again.",
                text_color=PINK
            )

            raise


        finally:
            # Restore button
            self.capture_button.configure(
                text="CAPTURE BOARD",
                state="normal",
                fg_color=PURPLE
            )
    # Display python
    def set_python_code(
        self,
        code
    ):

        self.python_text.configure(
            state="normal"
        )

        self.python_text.delete(
            "1.0",
            "end"
        )

        self.python_text.insert(
            "1.0",
            code
        )

        self.python_text.configure(
            state="disabled"
        )
    # Display output
    def set_output(
        self,
        output
    ):

        self.output_text.configure(
            state="normal"
        )

        self.output_text.delete(
            "1.0",
            "end"
        )

        self.output_text.insert(
            "1.0",
            output
        )

        self.output_text.configure(
            state="disabled"
        )
    # Clear
    def clear(self):

        self.set_python_code("")

        self.set_output("")
