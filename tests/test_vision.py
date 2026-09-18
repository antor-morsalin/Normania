import cv2
import numpy as np
import pytest
from App.imageProcess import ImageProcessor

MATRIX = [[2,18,12,None,None], [32,2,21,None,None], [35,41,None,None,None],
          [34,None,None,None,None], [35,42,None,None,None], [None]*5]


def synthetic_board(matrix=MATRIX, rotate_markers=False):
    cell, origin, size = 130, 140, 78
    height, width = 6*cell + 2*origin, 5*cell + 2*origin
    image = np.full((height, width), 255, dtype=np.uint8)
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_250)
    def paste(marker_id, x, y, rotation=0):
        marker = cv2.aruco.generateImageMarker(dictionary, marker_id, size)
        marker = np.rot90(marker, rotation)
        image[y:y+size, x:x+size] = marker
    # Inward vertices coincide with the outer grid corners.
    for marker_id, x, y in [(200,origin-size,origin-size), (201,origin+5*cell,origin-size),
                            (202,origin+5*cell,origin+6*cell), (203,origin-size,origin+6*cell)]:
        paste(marker_id, x, y, (marker_id % 4) if rotate_markers else 0)
    for row, values in enumerate(matrix):
        for col, marker_id in enumerate(values):
            if marker_id is not None:
                paste(marker_id, origin+col*cell+(cell-size)//2, origin+row*cell+(cell-size)//2,
                      ((row+col) % 4) if rotate_markers else 0)
    # Light board grid lines reflect printed cells without touching markers.
    for row in range(7):
        cv2.line(image, (origin,origin+row*cell), (origin+5*cell,origin+row*cell), 170, 1)
    for col in range(6):
        cv2.line(image, (origin+col*cell,origin), (origin+col*cell,origin+6*cell), 170, 1)
    return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)


@pytest.fixture(scope='module')
def processor():
    return ImageProcessor()


@pytest.mark.parametrize('mode', ['plain','mirrored','rotated','rotated_markers','perspective','dim','blur','small','gray','bgra'])
def test_image_to_matrix(processor, mode):
    image = synthetic_board(rotate_markers=mode == 'rotated_markers')
    if mode == 'mirrored':
        image = cv2.flip(image, 1)
    elif mode == 'rotated':
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    elif mode == 'perspective':
        height, width = image.shape[:2]
        src = np.float32([[0,0], [width-1,0], [width-1,height-1], [0,height-1]])
        dst = np.float32([[90,30], [width-90,70], [width-10,height-20], [25,height-100]])
        image = cv2.warpPerspective(image, cv2.getPerspectiveTransform(src,dst),(width,height),borderValue=(255,255,255))
    elif mode == 'dim':
        gradient = np.linspace(0.25, 0.60, image.shape[1])[None,:,None]
        image = np.clip(image*gradient+35,0,255).astype(np.uint8)
    elif mode == 'blur':
        image = cv2.GaussianBlur(image,(5,5),1.0)
    elif mode == 'small':
        image = cv2.resize(image, None, fx=0.45, fy=0.45, interpolation=cv2.INTER_AREA)
    elif mode == 'gray':
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif mode == 'bgra':
        image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    assert processor.image_to_aruco_matrix(image) == MATRIX


def test_repeated_ids_are_not_collapsed(processor):
    scan = processor.scan_image(synthetic_board())
    assert sum(d['id'] == 2 for d in scan.detections) == 2
    assert sum(d['id'] == 35 for d in scan.detections) == 2


def test_occluded_block_not_invented(processor):
    image = synthetic_board()
    origin, cell, size = 140, 130, 78
    x,y = origin+cell+(cell-size)//2, origin+2*cell+(cell-size)//2
    image[y-5:y+size+5,x-5:x+size+5] = 255
    expected = [row.copy() for row in MATRIX]
    expected[2][1] = None
    assert processor.image_to_aruco_matrix(image) == expected


def detection(marker_id, x, y):
    return {'id':marker_id, 'center':np.array([x,y],dtype=float)}


def test_collisions_rejected_even_same_id(processor):
    with pytest.raises(ValueError, match='Two blocks occupy row 1, column 1'):
        processor.create_aruco_matrix([detection(2,.4,.4),detection(2,.6,.6)],np.eye(3))


@pytest.mark.parametrize('x,y', [(-.01,.5),(5,.5),(.5,6),(.5,-.01),(float('nan'),.5),(float('inf'),.5)])
def test_outside_coordinates_never_index_matrix(processor,x,y):
    assert processor.point_to_cell(x,y) is None
    with pytest.raises(ValueError):
        processor.create_aruco_matrix([detection(2,x,y)],np.eye(3))


def test_near_row_boundary_requests_reposition(processor):
    with pytest.raises(ValueError, match='cell boundary'):
        processor.create_aruco_matrix([detection(34,.5,2.999)],np.eye(3))


@pytest.mark.parametrize('image', [None,np.empty((0,0),dtype=np.uint8),np.ones((100,100),dtype=float),np.ones((100,100,2),dtype=np.uint8)])
def test_invalid_image_is_clear_error(processor,image):
    with pytest.raises(ValueError):
        processor.detect_markers(image)


def test_missing_and_duplicate_corners(processor):
    detections=processor.detect_markers(synthetic_board())
    with pytest.raises(ValueError, match='Missing: 200'):
        processor.get_board_corners([d for d in detections if d['id'] != 200])
    corner=next(d for d in detections if d['id']==200)
    with pytest.raises(ValueError, match='appears more than once'):
        processor.get_board_corners(detections+[corner])


def test_bad_corner_geometry_rejected(processor):
    with pytest.raises(ValueError):
        processor.calculate_homography(np.zeros((4,2),dtype=np.float32))
    with pytest.raises(ValueError):
        processor.calculate_homography(np.float32([[0,0],[100,100],[100,0],[0,100]]))

