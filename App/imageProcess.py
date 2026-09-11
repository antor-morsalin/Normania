from pathlib import Path
import sys

import cv2
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from Parsing.parse import Parser


BOARD_ROWS = 10
BOARD_COLUMNS = 6


# All physical markers use:

# DICT_5X5_250

# These four IDs are NOT programming blocks.
# They identify the four corners of the physical board.

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


# =========================================================
# LOGICAL BOARD COORDINATE SYSTEM
# =========================================================

# This is NOT measured in pixels.
#
# The board itself becomes the coordinate system:
#
#   (0, 0) ---------------------- (6, 0)
#      |                            |
#      |       6 columns            |
#      |                            |
#      |       10 rows              |
#      |                            |
#   (0,10) ---------------------- (6,10)
#
# Every cell is therefore:
#
#       width  = 1
#       height = 1
#
# This coordinate system remains the same regardless of:
#
# - image resolution
# - camera distance
# - camera angle
# - perspective distortion
# - future camera implementation

LOGICAL_BOARD_CORNERS = np.float32([
    [0, 0],                              # top-left
    [BOARD_COLUMNS, 0],                  # top-right
    [BOARD_COLUMNS, BOARD_ROWS],         # bottom-right
    [0, BOARD_ROWS],                     # bottom-left
])

# IMAGE PROCESSOR

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

    # IMAGE ACQUISITION

    def get_image(self):

        """
        CURRENT VERSION:
        Load test.png from the App folder.

        FUTURE VERSION:
        This is the only part that needs to change.

        Instead of loading test.png, the camera can:
            1. open
            2. capture a photo
            3. optionally save it as test.png
            4. return the captured image

        Everything after this method can remain unchanged.
        """

        image_path = (
            Path(__file__).resolve().parent
            / "test.png"
        )

        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            raise ValueError(
                f"Could not load image: {image_path}"
            )

        return image


    # ARUCO DETECTION

    def detect_markers(self, image):

        """
        Detect every ArUco marker in the image.

        Each detection keeps:

            marker ID
            four corner coordinates
            center coordinate

        IMPORTANT:

        We use a list instead of a dictionary because
        multiple physical blocks may have the SAME
        ArUco ID.

        For example, there could be multiple physical
        copies of the number 5 block.
        """

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        corners, ids, rejected = (
            self.detector.detectMarkers(gray)
        )

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

            # OpenCV initially returns:
            #
            # shape = (1, 4, 2)
            #
            # Convert it to:
            #
            # shape = (4, 2)

            marker_corners = (
                marker_corners.reshape(4, 2)
            )


            # Marker corner order from OpenCV:
            #
            # 0 = top-left
            # 1 = top-right
            # 2 = bottom-right
            # 3 = bottom-left


            # Find the center of the marker.
            #
            # centerX =
            #     (x0 + x1 + x2 + x3) / 4
            #
            # centerY =
            #     (y0 + y1 + y2 + y3) / 4

            center = marker_corners.mean(
                axis=0
            )


            detections.append({

                "id": marker_id,

                "corners": marker_corners,

                "center": center
            })


        return detections


    # FIND BOARD BOUNDARIES

    def get_board_corners(self, detections):

        """
        Find the four permanent board markers.

        Instead of assuming pixel coordinates, we use
        the INNER corner of each board marker.

        Layout:

            marker 200               marker 201

                [ ]----------------------[ ]
                   \                    /
                    logical board
                   /                    \

                [ ]----------------------[ ]

            marker 203               marker 202


        Specifically:

        200 -> bottom-right corner
        201 -> bottom-left corner
        202 -> top-left corner
        203 -> top-right corner

        These four points define the programming board.
        """

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


        # -------------------------------------------------
        # Extract the INNER corner of each permanent marker
        # -------------------------------------------------
        #
        # OpenCV marker-corner indexing:
        #
        #       0 -------- 1
        #       |          |
        #       | marker   |
        #       |          |
        #       3 -------- 2
        #
        #
        # Board layout:
        #
        #  marker 200              marker 201
        #
        #        corner 2 ------ corner 3
        #             |          |
        #             |  BOARD   |
        #             |          |
        #        corner 1 ------ corner 0
        #
        #  marker 203              marker 202


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


    # PERSPECTIVE TRANSFORMATION

    def calculate_homography(
        self,
        image_board_corners
    ):

        """
        Calculate the transformation from:

            camera/image coordinates

        to:

            logical board coordinates


        Example:

        A point such as:

            (1458, 823)

        in the photograph might become:

            (2.37, 4.62)

        on the logical board.

        No image resolution is assumed.
        """

        homography = cv2.getPerspectiveTransform(

            image_board_corners,

            LOGICAL_BOARD_CORNERS
        )


        return homography


    # TRANSFORM ONE POINT

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


    # LOGICAL POINT -> BOARD CELL

    def point_to_cell(
        self,
        x,
        y
    ):

        """
        Our logical coordinate system is:

            X = 0 through 6
            Y = 0 through 10


        Example:

            x = 2.37
            y = 4.62

        means:

            column = 2
            row = 4
        """


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


    # =====================================================
    # CREATE ARUCO MATRIX
    # =====================================================

    def create_aruco_matrix(
        self,
        detections,
        homography
    ):

        """
        Produce the exact 10 x 6 matrix expected
        by Parser.

        Empty cells contain None.

        Example:

        [
            [13, 40, 5, None, None, None],
            [70, 13, None, None, None, None],
            ...
        ]
        """


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


            # ---------------------------------------------
            # Ignore permanent board markers
            # ---------------------------------------------

            if marker_id in BOARD_CORNER_IDS:
                continue


            # ---------------------------------------------
            # Get marker center
            # ---------------------------------------------

            center = detection["center"]


            # ---------------------------------------------
            # Convert camera location into logical
            # board coordinates
            # ---------------------------------------------

            x, y = self.transform_point(

                center,

                homography
            )


            # ---------------------------------------------
            # Determine board cell
            # ---------------------------------------------

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


            # ---------------------------------------------
            # Do not allow two blocks in one cell
            # ---------------------------------------------

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


            # ---------------------------------------------
            # Store marker ID
            # ---------------------------------------------

            matrix[row][column] = marker_id


        return matrix


    # COMPLETE IMAGE PROCESSING PIPELINE

    def image_to_aruco_matrix(
        self,
        image
    ):

        """
        Complete computer-vision pipeline:

        image
            ->
        ArUco detections
            ->
        board reference points
            ->
        perspective transformation
            ->
        10 x 6 ArUco matrix
        """


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


# OUTPUT FUNCTIONS

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


# MAIN

def main():

    # -----------------------------------------------------
    # 1. Create image processor
    # -----------------------------------------------------

    image_processor = ImageProcessor()


    # -----------------------------------------------------
    # 2. GET IMAGE
    #
    # CURRENT:
    #     test.png
    #
    # FUTURE:
    #     camera capture
    #
    # Nothing after this point needs to care where
    # the image came from.
    # -----------------------------------------------------

    image = image_processor.get_image()


    # -----------------------------------------------------
    # 3. IMAGE -> ARUCO MATRIX
    # -----------------------------------------------------

    aruco_matrix = (
        image_processor.image_to_aruco_matrix(
            image
        )
    )


    # -----------------------------------------------------
    # 4. PRINT ARUCO MATRIX
    # -----------------------------------------------------

    print_aruco_matrix(
        aruco_matrix
    )


    # -----------------------------------------------------
    # 5. CREATE PARSER
    # -----------------------------------------------------

    parser = Parser()


    # -----------------------------------------------------
    # 6. PRINT PRIMARY TOKEN TRANSLATION
    # -----------------------------------------------------

    print_primary_syntax(
        parser,
        aruco_matrix
    )


    # -----------------------------------------------------
    # 7. ARUCO MATRIX -> STATEMENT OBJECTS
    # -----------------------------------------------------

    statements = (
        parser.create_statements(
            aruco_matrix
        )
    )


    # -----------------------------------------------------
    # 8. STATEMENTS -> PYTHON
    # -----------------------------------------------------

    python_code = (
        parser.convert_to_python(
            statements
        )
    )


    # 9. PRINT FINAL PYTHON

    print()
    print("=" * 60)
    print("FINAL PYTHON CODE")
    print("=" * 60)

    print(python_code)


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    main()