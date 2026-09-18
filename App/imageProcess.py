"""Location-preserving ArUco detection and immediate validated board capture."""
from dataclasses import dataclass
from pathlib import Path
import json
import sys
import time
import tkinter as tk

import cv2
import numpy as np
from PIL import Image, ImageTk

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
from Data.arucoMap import ARUCO_TO_TOKEN
from Parsing.parse import Parser, BOARD_ROWS, BOARD_COLUMNS

TOP_LEFT_MARKER, TOP_RIGHT_MARKER = 200, 201
BOTTOM_RIGHT_MARKER, BOTTOM_LEFT_MARKER = 202, 203
CORNER_ORDER = (200, 201, 202, 203)
BOARD_CORNER_IDS = set(CORNER_ORDER)
LOGICAL_BOARD_CORNERS = np.float32([[0, 0], [BOARD_COLUMNS, 0],
                                  [BOARD_COLUMNS, BOARD_ROWS], [0, BOARD_ROWS]])


@dataclass
class BoardScan:
    matrix: list
    detections: list
    board_corners: np.ndarray
    homography: np.ndarray


class ImageProcessor:
    def __init__(self, boundary_margin=0.05):
        if not hasattr(cv2, "aruco"):
            raise RuntimeError("OpenCV ArUco is missing. Install the project's requirements.txt.")
        self.aruco_dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_250)
        parameters = cv2.aruco.DetectorParameters()
        parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        parameters.cornerRefinementWinSize = 3
        parameters.adaptiveThreshWinSizeMin = 3
        parameters.adaptiveThreshWinSizeMax = 53
        parameters.adaptiveThreshWinSizeStep = 10
        parameters.minMarkerPerimeterRate = 0.02
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dictionary, parameters)
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        self.boundary_margin = boundary_margin
        self.last_scan = None
        self.last_capture = None

    @staticmethod
    def _gray(image):
        if not isinstance(image, np.ndarray) or image.size == 0:
            raise ValueError("The camera image is empty. Capture again.")
        if image.dtype != np.uint8:
            raise ValueError("Use an 8-bit camera image (PNG or JPEG).")
        if image.ndim == 2:
            return np.ascontiguousarray(image)
        if image.ndim == 3 and image.shape[2] in (3, 4):
            mode = cv2.COLOR_BGR2GRAY if image.shape[2] == 3 else cv2.COLOR_BGRA2GRAY
            return cv2.cvtColor(image, mode)
        raise ValueError("Use a grayscale, BGR, or BGRA image.")

    def _decode(self, gray):
        corners, ids, _ = self.detector.detectMarkers(gray)
        if ids is None:
            return []
        if len(ids) != len(corners):
            raise ValueError("The marker reading was incomplete. Capture again.")
        detections = []
        for marker_id, quad in zip(ids.flatten(), corners):
            quad = np.asarray(quad, dtype=np.float32).reshape(4, 2)
            if not np.all(np.isfinite(quad)):
                raise ValueError("A marker location could not be read. Capture again.")
            detections.append({"id": int(marker_id), "corners": quad,
                               "center": quad.mean(axis=0)})
        return detections

    @staticmethod
    def _merge(base, extra):
        """Deduplicate by physical location, not by ID (IDs can repeat)."""
        merged = list(base)
        for new in extra:
            duplicate = False
            new_side = np.mean(np.linalg.norm(np.roll(new["corners"], 1, axis=0) - new["corners"], axis=1))
            for old in merged:
                old_side = np.mean(np.linalg.norm(np.roll(old["corners"], 1, axis=0) - old["corners"], axis=1))
                if np.linalg.norm(new["center"] - old["center"]) < 0.30 * min(new_side, old_side):
                    if old["id"] != new["id"]:
                        raise ValueError("One block was read as two different markers. Improve the light and recapture.")
                    duplicate = True
                    break
            if not duplicate:
                merged.append(new)
        return merged

    def detect_markers(self, image):
        gray = self._gray(image)
        detections = self._merge(self._decode(gray), self._decode(self.clahe.apply(gray)))
        ids = {d["id"] for d in detections} & BOARD_CORNER_IDS
        mirrored = False
        if ids != BOARD_CORNER_IDS:
            reverse = cv2.flip(gray, 1)
            reverse_detections = self._merge(self._decode(reverse), self._decode(self.clahe.apply(reverse)))
            reverse_ids = {d["id"] for d in reverse_detections} & BOARD_CORNER_IDS
            if len(reverse_ids) > len(ids):
                gray, detections, mirrored = reverse, reverse_detections, True
        if not detections:
            raise ValueError("No ArUco markers were detected. Move closer and improve the light.")
        if mirrored:
            for detection in detections:
                detection["corners"][:, 0] = gray.shape[1] - 1 - detection["corners"][:, 0]
                detection["center"] = detection["corners"].mean(axis=0)
        return detections

    def get_board_corners(self, detections):
        markers = {}
        for detection in detections:
            marker_id = detection["id"]
            if marker_id in BOARD_CORNER_IDS:
                if marker_id in markers:
                    raise ValueError(f"Board marker {marker_id} appears more than once. Show only one board.")
                markers[marker_id] = detection
        missing = BOARD_CORNER_IDS - markers.keys()
        if missing:
            raise ValueError("Show all four corner markers. Missing: " + ", ".join(map(str, sorted(missing))))
        middle = np.mean([markers[i]["center"] for i in CORNER_ORDER], axis=0)
        corners = []
        for marker_id in CORNER_ORDER:
            quad = np.asarray(markers[marker_id]["corners"], dtype=np.float32)
            if quad.shape != (4, 2) or not np.all(np.isfinite(quad)):
                raise ValueError(f"Board marker {marker_id} has an invalid outline. Capture again.")
            # ArUco vertex indices rotate with the printed marker. Geometry selects
            # the inward vertex regardless of marker rotation or camera mirroring.
            corners.append(quad[np.argmin(np.linalg.norm(quad - middle, axis=1))])
        corners = np.asarray(corners, dtype=np.float32)
        self._validate_quad(corners)
        return corners

    @staticmethod
    def _validate_quad(corners):
        if corners.shape != (4, 2) or not np.all(np.isfinite(corners)):
            raise ValueError("The board corners could not be located. Capture again.")
        if not cv2.isContourConvex(corners) or abs(cv2.contourArea(corners)) < 25:
            raise ValueError("Check the corner layout: 200, 201, 202, 203 around the board. Keep the board flat.")

    def calculate_homography(self, image_board_corners):
        corners = np.asarray(image_board_corners, dtype=np.float32)
        self._validate_quad(corners)
        homography = cv2.getPerspectiveTransform(corners, LOGICAL_BOARD_CORNERS)
        if not np.all(np.isfinite(homography)) or abs(np.linalg.det(homography)) < 1e-14:
            raise ValueError("The board is too tilted to read. Face it toward the camera.")
        return homography

    def transform_point(self, point, homography):
        point = np.asarray(point, dtype=float)
        matrix = np.asarray(homography, dtype=float)
        if (point.shape != (2,) or not np.all(np.isfinite(point))
                or matrix.shape != (3, 3) or not np.all(np.isfinite(matrix))):
            raise ValueError("A block position could not be mapped to the board.")
        projected = matrix @ np.array([point[0], point[1], 1.0])
        if not np.all(np.isfinite(projected)) or abs(projected[2]) < 1e-12:
            raise ValueError("A block position could not be mapped to the board.")
        return tuple(projected[:2] / projected[2])

    def point_to_cell(self, x, y):
        if not np.isfinite(x) or not np.isfinite(y) or not (0 <= x < BOARD_COLUMNS and 0 <= y < BOARD_ROWS):
            return None
        return int(y), int(x)

    def create_aruco_matrix(self, detections, homography):
        matrix = [[None] * BOARD_COLUMNS for _ in range(BOARD_ROWS)]
        for detection in detections:
            marker_id = detection["id"]
            if marker_id in BOARD_CORNER_IDS:
                continue
            # Average AFTER rectification to avoid perspective-biased centers.
            if "corners" in detection:
                points = [self.transform_point(point, homography) for point in detection["corners"]]
                x, y = np.mean(points, axis=0)
            else:
                x, y = self.transform_point(detection["center"], homography)
            cell = self.point_to_cell(x, y)
            if cell is None:
                raise ValueError(f"Block {marker_id} is outside the grid. Place it inside the board.")
            row, column = cell
            for coordinate, limit in ((x, BOARD_COLUMNS), (y, BOARD_ROWS)):
                nearest = round(float(coordinate))
                if 0 < nearest < limit and abs(coordinate - nearest) < self.boundary_margin:
                    raise ValueError(f"Block {marker_id} is too close to a cell boundary near row {row + 1}, "
                                     f"column {column + 1}. Move it toward the center of its cell.")
            if matrix[row][column] is not None:
                raise ValueError(f"Two blocks occupy row {row + 1}, column {column + 1}: "
                                 f"{matrix[row][column]} and {marker_id}. Separate them.")
            matrix[row][column] = marker_id
        return matrix

    def _recover_rectified(self, image, homography):
        # Re-read the same frame at a consistent cell size. No cross-frame filling.
        scale, margin = 120, 24
        to_pixels = np.array([[scale, 0, margin], [0, scale, margin], [0, 0, 1]], dtype=float)
        transform = to_pixels @ homography
        gray = self._gray(image)
        board = cv2.warpPerspective(gray, transform,
                                    (BOARD_COLUMNS * scale + margin * 2, BOARD_ROWS * scale + margin * 2),
                                    borderValue=255)
        recovered = self._merge(self._decode(board), self._decode(self.clahe.apply(board)))
        inverse = np.linalg.inv(transform)
        results = []
        for detection in recovered:
            if detection["id"] in BOARD_CORNER_IDS:
                continue
            quad = np.asarray([self.transform_point(point, inverse) for point in detection["corners"]],
                              dtype=np.float32)
            results.append({"id": detection["id"], "corners": quad, "center": quad.mean(axis=0)})
        return results

    def scan_image(self, image):
        self.last_scan = None
        detections = self.detect_markers(image)
        corners = self.get_board_corners(detections)
        homography = self.calculate_homography(corners)
        detections = self._merge(detections, self._recover_rectified(image, homography))
        matrix = self.create_aruco_matrix(detections, homography)
        self.last_scan = BoardScan(matrix, detections, corners, homography)
        return self.last_scan

    def image_to_aruco_matrix(self, image):
        return self.scan_image(image).matrix

    def orient_captured_image(self, image):
        # Corner identities define logical orientation; keep image/scan coordinates aligned.
        self.get_board_corners(self.detect_markers(image))
        return image

    def draw_scan(self, image, scan):
        gray = self._gray(image)
        overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        inverse = np.linalg.inv(scan.homography)
        for col in range(BOARD_COLUMNS + 1):
            a, b = [tuple(np.rint(self.transform_point(p, inverse)).astype(int))
                    for p in ((col, 0), (col, BOARD_ROWS))]
            cv2.line(overlay, a, b, (80, 175, 80), 1)
        for row in range(BOARD_ROWS + 1):
            a, b = [tuple(np.rint(self.transform_point(p, inverse)).astype(int))
                    for p in ((0, row), (BOARD_COLUMNS, row))]
            cv2.line(overlay, a, b, (80, 175, 80), 1)
        for d in scan.detections:
            quad = np.rint(d["corners"]).astype(np.int32)
            cv2.polylines(overlay, [quad], True, (0, 200, 255), 2)
            label = ARUCO_TO_TOKEN.get(d["id"], str(d["id"]))
            x, y = np.min(quad, axis=0)
            cv2.putText(overlay, label, (int(x), max(15, int(y) - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 80, 220), 1, cv2.LINE_AA)
        return overlay

    def save_debug(self, image, scan, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        payload = {"board_rows": BOARD_ROWS, "board_columns": BOARD_COLUMNS,
                   "matrix": scan.matrix,
                   "tokens": [[ARUCO_TO_TOKEN.get(i, f"UNKNOWN {i}") for i in row if i is not None]
                              for row in scan.matrix],
                   "board_corners": scan.board_corners.tolist()}
        (directory / "last_capture.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        if not cv2.imwrite(str(directory / "detected_board.png"), self.draw_scan(image, scan)):
            raise OSError("Could not save the detected board image.")

    def get_image(self, parent=None, camera_index=0):
        """Capture the first nonempty, valid whole-board reading without a countdown."""
        self.last_capture = None
        backend = cv2.CAP_AVFOUNDATION if sys.platform == "darwin" else cv2.CAP_ANY
        camera = cv2.VideoCapture(camera_index, backend)
        window = owned_root = after_id = None
        captured_image = capture_error = None
        parser = Parser()
        last_frame_time = time.monotonic()
        try:
            if not camera.isOpened():
                raise RuntimeError("Could not open the camera. Close other camera apps and allow camera "
                                   "access for Python or your terminal/IDE in your system settings.")
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            if parent is None:
                owned_root = tk.Tk()
                owned_root.withdraw()
                parent = owned_root
            window = tk.Toplevel(parent)
            window.title("Capture board")
            if owned_root is None:
                window.transient(parent)
            tk.Label(window, text="Show all four corners and the complete program.\n"
                                  "The board is captured as soon as a valid program is detected.",
                     padx=16, pady=10).pack()
            preview = tk.Label(window)
            preview.pack(padx=12)
            status = tk.Label(window, text="Starting camera...", wraplength=760, pady=8)
            status.pack()
            rows_label = tk.Label(window, text="", justify="left", anchor="w", font=("Courier", 10))
            rows_label.pack(fill="x", padx=16)
            def close_camera(event=None):
                nonlocal after_id
                if after_id is not None:
                    window.after_cancel(after_id)
                    after_id = None
                window.destroy()
            tk.Button(window, text="Cancel", command=close_camera).pack(pady=10)
            window.protocol("WM_DELETE_WINDOW", close_camera)
            window.bind("<Escape>", close_camera)
            preview_size = (min(960, max(320, window.winfo_screenwidth() - 80)),
                            min(480, max(180, window.winfo_screenheight() - 370)))
            def update_frame():
                nonlocal after_id, captured_image, capture_error, last_frame_time
                after_id = None
                try:
                    ok, frame = camera.read()
                    if not ok or frame is None or frame.size == 0:
                        rows_label.configure(text="")
                        if time.monotonic() - last_frame_time >= 5:
                            raise RuntimeError("The camera stopped sending images. Try capturing again.")
                        status.configure(text="Waiting for the camera...")
                        after_id = window.after(100, update_frame)
                        return
                    last_frame_time = time.monotonic()
                    display = frame
                    try:
                        scan = self.scan_image(frame)
                        display = self.draw_scan(frame, scan)
                        rows_label.configure(text=format_rows(scan.matrix))
                        statements = parser.create_statements(scan.matrix)
                        if not statements:
                            raise ValueError("No programming blocks were read. Place your program on the grid.")
                        parser.convert_to_python(statements)
                        # Keep this exact frame and matrix; no stability delay or
                        # second camera reading may replace the validated program.
                        captured_image, self.last_capture = frame.copy(), scan
                        close_camera()
                        return
                    except ValueError as error:
                        if self.last_scan is None:
                            rows_label.configure(text="")
                        status.configure(text=str(error))
                    preview_image = Image.fromarray(cv2.cvtColor(display, cv2.COLOR_BGR2RGB))
                    preview_image.thumbnail(preview_size)
                    photo = ImageTk.PhotoImage(preview_image, master=window)
                    preview.configure(image=photo)
                    preview.image = photo
                    after_id = window.after(50, update_frame)
                except Exception as error:
                    capture_error = error
                    close_camera()
            window.wait_visibility()
            window.grab_set()
            window.focus_set()
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
        if captured_image is None:
            return None
        directory = Path(__file__).resolve().parent
        if not cv2.imwrite(str(directory / "test.png"), captured_image):
            raise OSError("Could not save the captured image.")
        self.save_debug(captured_image, self.last_capture, directory)
        return captured_image


def format_rows(matrix):
    return "\n".join(f"Row {i}: " + (" | ".join(ARUCO_TO_TOKEN.get(v, f"UNKNOWN {v}")
                       for v in row if v is not None) or "(empty)")
                     for i, row in enumerate(matrix, 1))


def print_aruco_matrix(matrix):
    print("ARUCO MATRIX")
    for index, row in enumerate(matrix, 1):
        print(f"Row {index}: {row}")


def print_primary_syntax(parser, matrix):
    print("PRIMARY TRANSLATED SYNTAX")
    print(format_rows(matrix))


if __name__ == "__main__":
    processor = ImageProcessor()
    photo = processor.get_image()
    if photo is not None:
        matrix = processor.last_capture.matrix
        print_aruco_matrix(matrix)
        print_primary_syntax(Parser(), matrix)
        print(Parser().convert_to_python(Parser().create_statements(matrix)))
