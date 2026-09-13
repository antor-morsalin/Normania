from pathlib import Path
import sys
import time
import tkinter as tk

import cv2
import numpy as np
from PIL import Image, ImageTk

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from Parsing.parse import Parser


BOARD_ROWS = 8
BOARD_COLUMNS = 6


# Markers use DICT_5X5_250. These four IDs identify the board corners.

TOP_LEFT_MARKER = 200
TOP_RIGHT_MARKER = 201
BOTTOM_RIGHT_MARKER = 202
BOTTOM_LEFT_MARKER = 203

BOARD_CORNER_IDS = {
    TOP_LEFT_MARKER,
    TOP_RIGHT_MARKER,
    BOTTOM_RIGHT_MARKER,
    BOTTOM_LEFT_MARKER,
}


# Board coordinates span 6 columns and 8 rows; each cell is one unit.

LOGICAL_BOARD_CORNERS = np.float32([
    [0, 0],                              # top-left
    [BOARD_COLUMNS, 0],                  # top-right
    [BOARD_COLUMNS, BOARD_ROWS],         # bottom-right
    [0, BOARD_ROWS],                     # bottom-left
])

# Image processor

class ImageProcessor:

    def __init__(self):

        # Use the same dictionary used to create all physical ArUco markers.

        self.aruco_dictionary = (
            cv2.aruco.getPredefinedDictionary(
                cv2.aruco.DICT_5X5_250
            )
        )

        detector_parameters = (
            cv2.aruco.DetectorParameters()
        )

        self.detector = cv2.aruco.ArucoDetector(
            self.aruco_dictionary,
            detector_parameters
        )

    # Image acquisition

    def get_image(self, parent=None, camera_index=0):

        """Wait for four corners, capture the board, and save test.png."""

        image_path = Path(__file__).resolve().parent / "test.png"
        backend = cv2.CAP_AVFOUNDATION if sys.platform == "darwin" else cv2.CAP_ANY
        camera = cv2.VideoCapture(camera_index, backend)
        window = None
        owned_root = None
        after_id = None
        captured_image = None
        capture_error = None
        last_frame_time = time.monotonic()
        corners_visible_since = None

        try:
            if not camera.isOpened():
                raise RuntimeError(
                    "Could not open the camera. Close other camera apps and allow "
                    "camera access for Python or your terminal/IDE in macOS "
                    "System Settings > Privacy & Security > Camera."
                )

            # Request a clear image; the camera may choose a supported size.
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

            if parent is None:
                owned_root = tk.Tk()
                owned_root.withdraw()
                parent = owned_root

            window = tk.Toplevel(parent)
            window.title("Capture board")
            window.resizable(False, False)
            if owned_root is None:
                window.transient(parent)

            tk.Label(
                window,
                text="Show the back of the board. Keep all four corner markers visible for 2 seconds.",
                padx=16,
                pady=12
            ).pack()

            preview = tk.Label(window)
            preview.pack(padx=12)

            status = tk.Label(window, text="Starting camera...", pady=10)
            status.pack()

            def close_camera(event=None):
                nonlocal after_id
                if after_id is not None:
                    window.after_cancel(after_id)
                    after_id = None
                window.destroy()

            tk.Button(window, text="Cancel", command=close_camera).pack(pady=(0, 12))
            window.protocol("WM_DELETE_WINDOW", close_camera)
            window.bind("<Escape>", close_camera)

            # Resize only the preview. Detection and saving use the original frame.
            preview_size = (
                min(960, max(320, window.winfo_screenwidth() - 80)),
                min(540, max(240, window.winfo_screenheight() - 200))
            )

            def update_frame():
                nonlocal after_id, captured_image, capture_error, last_frame_time
                nonlocal corners_visible_since
                after_id = None

                try:
                    ok, frame = camera.read()
                    if not ok or frame is None or frame.size == 0:
                        corners_visible_since = None
                        if time.monotonic() - last_frame_time >= 5:
                            raise RuntimeError("The camera stopped sending images. Try capturing again.")
                        status.configure(text="Waiting for the camera...")
                        after_id = window.after(100, update_frame)
                        return

                    last_frame_time = time.monotonic()

                    try:
                        detections = self.detect_markers(frame)
                    except ValueError:
                        detections = []

                    corner_ids = [d["id"] for d in detections if d["id"] in BOARD_CORNER_IDS]
                    if len(corner_ids) == 4 and set(corner_ids) == BOARD_CORNER_IDS:
                        now = time.monotonic()
                        if corners_visible_since is None:
                            corners_visible_since = now
                        remaining = 2.0 - (now - corners_visible_since)
                        if remaining <= 0:
                            # Use this frame, where all four corners were checked again.
                            captured_image = frame.copy()
                            close_camera()
                            return
                        status.configure(text=f"All corners visible. Hold still: {remaining:.1f}s")
                    else:
                        corners_visible_since = None
                        status.configure(text=f"Show all four corners. Found: {len(set(corner_ids))}/4")

                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    preview_image = Image.fromarray(rgb)
                    preview_image.thumbnail(preview_size)
                    photo = ImageTk.PhotoImage(preview_image, master=window)
                    preview.configure(image=photo)
                    preview.image = photo
                    after_id = window.after(30, update_frame)

                except Exception as error:
                    capture_error = error
                    close_camera()

            window.wait_visibility()
            window.grab_set()
            window.focus_set()
            last_frame_time = time.monotonic()
            after_id = window.after(0, update_frame)
            parent.wait_window(window)

            if capture_error is not None:
                raise capture_error

        finally:
            camera.release()
            try:
                if window is not None and window.winfo_exists():
                    if after_id is not None:
                        window.after_cancel(after_id)
                    window.destroy()
                if owned_root is not None:
                    owned_root.destroy()
            except tk.TclError:
                pass

        # Cancel leaves the previous test.png alone and does not process it.
        if captured_image is None:
            return None

        # Check orientation only after taking the photo and closing the camera.
        captured_image = self.orient_captured_image(captured_image)
        if not cv2.imwrite(str(image_path), captured_image):
            raise OSError(f"Could not save image: {image_path}")
        return captured_image


    def orient_captured_image(self, image):

        """Use corner positions to decide whether the captured photo needs a flip."""

        detections = self.detect_markers(image)
        self.get_board_corners(detections)
        centers = {d["id"]: d["center"] for d in detections if d["id"] in BOARD_CORNER_IDS}
        top_left = centers[TOP_LEFT_MARKER]
        top_right = centers[TOP_RIGHT_MARKER]
        bottom_right = centers[BOTTOM_RIGHT_MARKER]
        bottom_left = centers[BOTTOM_LEFT_MARKER]

        if top_left[1] >= bottom_left[1] or top_right[1] >= bottom_right[1]:
            raise ValueError("Hold the board upright, with markers 200 and 201 above 203 and 202.")

        if top_left[0] < top_right[0] and bottom_left[0] < bottom_right[0]:
            return image

        if top_left[0] > top_right[0] and bottom_left[0] > bottom_right[0]:
            return cv2.flip(image, 1)

        raise ValueError("Check the corner layout: 200 top-left, 201 top-right, 202 bottom-right, 203 bottom-left.")


    # ArUco detection

    def detect_markers(self, image):

        """Detect markers and keep repeated IDs as separate physical blocks."""

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        corners, ids, rejected = (
            self.detector.detectMarkers(gray)
        )

        # A mirrored image also mirrors the marker patterns. Decode a flipped
        # copy when needed, then put the detections back in the image coordinates.
        corner_ids = set() if ids is None else set(ids.flatten()) & BOARD_CORNER_IDS
        if corner_ids != BOARD_CORNER_IDS:
            flipped_corners, flipped_ids, _ = self.detector.detectMarkers(cv2.flip(gray, 1))
            flipped_corner_ids = set() if flipped_ids is None else set(flipped_ids.flatten()) & BOARD_CORNER_IDS
            if len(flipped_corner_ids) > len(corner_ids):
                corners = []
                for marker_corners in flipped_corners:
                    marker_corners = marker_corners.reshape(4, 2).copy()
                    marker_corners[:, 0] = image.shape[1] - 1 - marker_corners[:, 0]
                    marker_corners = marker_corners[[1, 0, 3, 2]]
                    corners.append(marker_corners.reshape(1, 4, 2))
                ids = flipped_ids

        if ids is None or len(ids) == 0:
            raise ValueError(
                "No ArUco markers were detected."
            )

        ids = ids.flatten()

        detections = []

        for marker_id, marker_corners in zip(
            ids,
            corners
        ):

            marker_id = int(marker_id)

            # Convert each marker to four (x, y) corners.

            marker_corners = (
                marker_corners.reshape(4, 2)
            )


            # Average the corners to find the marker center.

            center = marker_corners.mean(
                axis=0
            )


            detections.append({

                "id": marker_id,

                "corners": marker_corners,

                "center": center
            })


        return detections


    # Find board boundaries

    def get_board_corners(self, detections):

        """Use the inner corner of each board marker: 200, 201, 202, and 203."""

        corner_markers = {}


        for detection in detections:

            marker_id = detection["id"]


            if marker_id not in BOARD_CORNER_IDS:
                continue


            # There must only be one copy of each
            # permanent board marker.

            if marker_id in corner_markers:

                raise ValueError(
                    f"Board marker {marker_id} "
                    f"was detected more than once."
                )


            corner_markers[marker_id] = (
                detection
            )

        # Make sure all four corner markers were detected

        missing_markers = (
            BOARD_CORNER_IDS
            - set(corner_markers.keys())
        )


        if missing_markers:

            missing_text = ", ".join(
                str(marker_id)
                for marker_id
                in sorted(missing_markers)
            )

            raise ValueError(
                "Missing board corner marker(s): "
                + missing_text
            )
        # Use the corner of each marker that faces the board.

        top_left = (
            corner_markers[
                TOP_LEFT_MARKER
            ]["corners"][2]
        )

        top_right = (
            corner_markers[
                TOP_RIGHT_MARKER
            ]["corners"][3]
        )

        bottom_right = (
            corner_markers[
                BOTTOM_RIGHT_MARKER
            ]["corners"][0]
        )

        bottom_left = (
            corner_markers[
                BOTTOM_LEFT_MARKER
            ]["corners"][1]
        )


        image_board_corners = np.float32([
            top_left,
            top_right,
            bottom_right,
            bottom_left
        ])


        return image_board_corners


    # Perspective transformation

    def calculate_homography(
        self,
        image_board_corners
    ):

        """Map image coordinates to the logical board coordinates."""

        homography = cv2.getPerspectiveTransform(

            image_board_corners,

            LOGICAL_BOARD_CORNERS
        )


        return homography


    # Transform one point

    def transform_point(
        self,
        point,
        homography
    ):

        """
        Transform one point from camera coordinates
        into logical board coordinates.
        """

        point_array = np.array(
            [[point]],
            dtype=np.float32
        )


        transformed_point = (
            cv2.perspectiveTransform(
                point_array,
                homography
            )
        )


        x, y = transformed_point[0][0]


        return float(x), float(y)


    # Find the board cell

    def point_to_cell(
        self,
        x,
        y
    ):

        """Convert board coordinates to a zero-based row and column."""


        # Point is outside the board.

        if not (
            0 <= x < BOARD_COLUMNS
            and
            0 <= y < BOARD_ROWS
        ):

            return None


        # Because every logical cell is exactly 1 unit wide and 1 unit tall:

        column = int(x)

        row = int(y)


        return row, column
    # Create ArUco matrix
    def create_aruco_matrix(
        self,
        detections,
        homography
    ):

        """Build the 8 by 6 marker matrix; empty cells contain None."""


        matrix = [

            [
                None
                for _ in range(
                    BOARD_COLUMNS
                )
            ]

            for _ in range(
                BOARD_ROWS
            )
        ]


        for detection in detections:

            marker_id = detection["id"]
            # Ignore permanent board markers
            if marker_id in BOARD_CORNER_IDS:
                continue
            # Get marker center
            center = detection["center"]
            # Convert camera location into logical
            # board coordinates
            x, y = self.transform_point(

                center,

                homography
            )
            # Determine board cell
            cell = self.point_to_cell(
                x,
                y
            )


            if cell is None:

                raise ValueError(
                    f"ArUco marker {marker_id} "
                    f"is outside the programming board."
                )


            row, column = cell
            # Do not allow two blocks in one cell
            existing_marker = (
                matrix[row][column]
            )


            if existing_marker is not None:

                raise ValueError(
                    f"Two blocks were detected in "
                    f"row {row + 1}, "
                    f"column {column + 1}: "
                    f"{existing_marker} "
                    f"and {marker_id}."
                )
            # Store marker ID
            matrix[row][column] = marker_id


        return matrix


    # Complete image processing pipeline

    def image_to_aruco_matrix(
        self,
        image
    ):

        """Detect markers, locate the board, and build the marker matrix."""


        detections = self.detect_markers(
            image
        )


        image_board_corners = (
            self.get_board_corners(
                detections
            )
        )


        homography = (
            self.calculate_homography(
                image_board_corners
            )
        )


        matrix = (
            self.create_aruco_matrix(
                detections,
                homography
            )
        )


        return matrix


# Output functions

def print_aruco_matrix(
    aruco_matrix
):

    print()
    print("=" * 60)
    print("ARUCO MATRIX")
    print("=" * 60)


    for index, row in enumerate(
        aruco_matrix
    ):

        print(
            f"Row {index + 1}: {row}"
        )


def print_primary_syntax(
    parser,
    aruco_matrix
):

    print()
    print("=" * 60)
    print("PRIMARY TRANSLATED SYNTAX")
    print("=" * 60)


    for index, row in enumerate(
        aruco_matrix
    ):

        tokens = parser.translate_row(
            row
        )


        # Ignore empty board rows.

        if not tokens:
            continue


        print(
            f"Row {index + 1}: "
            + " | ".join(tokens)
        )


# Main

def main():
    # Create the image processor
    image_processor = ImageProcessor()
    # Capture the board.

    image = image_processor.get_image()

    if image is None:
        return
    # Build the ArUco matrix
    aruco_matrix = (
        image_processor.image_to_aruco_matrix(
            image
        )
    )
    # Print the ArUco matrix
    print_aruco_matrix(
        aruco_matrix
    )
    # Create the parser
    parser = Parser()
    # Print the tokens
    print_primary_syntax(
        parser,
        aruco_matrix
    )
    # Build statements
    statements = (
        parser.create_statements(
            aruco_matrix
        )
    )
    # Generate Python
    python_code = (
        parser.convert_to_python(
            statements
        )
    )


    # Print the generated Python

    print()
    print("=" * 60)
    print("FINAL PYTHON CODE")
    print("=" * 60)

    print(python_code)
# Run application
if __name__ == "__main__":
    main()
