"""Run the real capture callback with a simulated camera and Tk event loop."""
from types import SimpleNamespace

import numpy as np
import pytest

from App import imageProcess as capture
from Data.arucoMap import ARUCO_TO_TOKEN
from Parsing.parse import Parser
from main import execute_python


@pytest.mark.parametrize('invalid_first', [False, True])
def test_capture_accepts_first_valid_frame_without_elapsed_time(monkeypatch, invalid_first):
    ids = {token: marker for marker, token in ARUCO_TO_TOKEN.items()}
    rows = [['IF', '1', 'IS', '2', 'THEN'], ['SHOW', 'GREAT JOB'], ['END'],
            ['OTHERWISE'], ['SHOW', 'KEEP TRYING'], ['END']]
    valid = [[ids[token] for token in row] + [None] * (5 - len(row)) for row in rows]
    incomplete = [row.copy() for row in valid]
    incomplete[4][1] = None
    readings = ([None, ValueError('Show all four corner markers.'),
                 [[None] * 5 for _ in range(6)], incomplete] if invalid_first else []) + [valid]
    frames = [None if value is None else np.full((12, 12, 3), i, np.uint8)
              for i, value in enumerate(readings)]

    class Camera:
        reads = 0
        released = False

        def isOpened(self):
            return True

        def set(self, *args):
            pass

        def read(self):
            assert self.reads < len(frames), 'Capture requested a frame after the first valid reading'
            frame = frames[self.reads]
            self.reads += 1
            return frame is not None, frame

        def release(self):
            self.released = True

    class Widget:
        def __init__(self, *args, **kwargs):
            pass

        def pack(self, **kwargs):
            pass

        def configure(self, **kwargs):
            pass

    class Window:
        def __init__(self):
            self.callbacks = {}
            self.closed = False
            self.next_id = 0

        def after(self, delay, callback):
            self.next_id += 1
            self.callbacks[self.next_id] = callback
            return self.next_id

        def after_cancel(self, key):
            self.callbacks.pop(key, None)

        def destroy(self):
            self.closed = True

        def winfo_exists(self):
            return not self.closed

        def winfo_screenwidth(self):
            return 1280

        def winfo_screenheight(self):
            return 900

        def noop(self, *args):
            pass

        title = transient = protocol = bind = wait_visibility = grab_set = focus_set = noop

    def wait_window(window):
        while not window.closed:
            assert window.callbacks, 'Capture stopped scheduling camera reads'
            key = next(iter(window.callbacks))
            window.callbacks.pop(key)()

    camera, window = Camera(), Window()
    monkeypatch.setattr(capture.cv2, 'VideoCapture', lambda *args: camera)
    monkeypatch.setattr(capture.tk, 'Toplevel', lambda parent: window)
    monkeypatch.setattr(capture.tk, 'Label', Widget)
    monkeypatch.setattr(capture.tk, 'Button', Widget)
    monkeypatch.setattr(capture.ImageTk, 'PhotoImage', lambda *args, **kwargs: object())
    monkeypatch.setattr(capture, 'time', SimpleNamespace(monotonic=lambda: 10.0))
    monkeypatch.setattr(capture.cv2, 'imwrite', lambda *args: True)
    processor = capture.ImageProcessor()

    def scan_image(frame):
        processor.last_scan = None
        index = int(frame[0, 0, 0])
        value = readings[index]
        if isinstance(value, Exception):
            raise value
        # The board moves between readings, as with a shaking hand.
        corners = np.float32([[0, 0], [500, 0], [500, 600], [0, 600]]) + index * 20
        processor.last_scan = capture.BoardScan(value, [], corners, np.eye(3))
        return processor.last_scan

    saved = []
    monkeypatch.setattr(processor, 'scan_image', scan_image)
    monkeypatch.setattr(processor, 'draw_scan', lambda frame, scan: frame)
    monkeypatch.setattr(processor, 'save_debug', lambda image, scan, path: saved.append(scan))
    image = processor.get_image(parent=SimpleNamespace(wait_window=wait_window))
    assert camera.reads == len(readings)
    assert camera.released and window.closed
    assert np.array_equal(image, frames[-1])
    assert processor.last_capture.matrix == valid
    assert saved == [processor.last_capture]
    parser = Parser()
    code = parser.convert_to_python(parser.create_statements(processor.last_capture.matrix))
    assert execute_python(code, parser.line_map) == 'KEEP TRYING\n'
