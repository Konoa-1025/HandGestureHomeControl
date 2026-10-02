import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import cv2
import numpy as np

from Position.tatamiMap import TatamiMap, overlap_area
from Managers import cameraManager as camera, positionManager as position
from Managers.previewManager import draw_position_debug


class PositionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'map.csv'
        self.path.write_text('tatami_id,tl_x,tl_y,tr_x,tr_y,br_x,br_y,bl_x,bl_y\n'
                             'T1,0,0,50,0,50,100,0,100\n'
                             'T2,50,0,100,0,100,100,50,100\n')
        self.map = TatamiMap(self.path, (100, 100))

    def test_lower_box_winner_and_lost_person(self):
        detector = Mock()
        detector.detect.return_value = (40, 0, 90, 100)
        human = position.HumanPosition(self.map, detector)
        frame = np.zeros((100, 100, 3), np.uint8)
        self.assertEqual(human.update(frame), 'T2')
        self.assertEqual(human.position_box, (40, 70, 90, 100))
        detector.detect.return_value = None
        self.assertIsNone(human.update(frame))
        self.assertIsNone(human.bounding_box)
        self.assertIsNone(human.position_box)

    def test_scaling_and_csv_only_loaded_once(self):
        self.path.unlink()
        for width, height in ((100, 100), (1920, 1080), (2560, 1440)):
            self.assertEqual(self.map.locate((width*.6, height*.7, width*.9, height), (height, width, 3)), 'T2')
        self.assertIsNone(self.map.locate((101, 0, 120, 100), (100, 100, 3)))

    def test_overlap_geometry(self):
        polygon = [(0,0), (10,0), (10,10), (0,10)]
        self.assertEqual(overlap_area(polygon, (5,5,15,15)), 25)
        self.assertEqual(overlap_area(polygon, (10,0,20,10)), 0)
        self.assertEqual(overlap_area(polygon, (-1,-1,11,11)), 100)
        self.assertEqual(overlap_area([(0,0),(10,0),(5,10)], (0,0,10,10)), 50)

    def test_bad_csv_and_disabled(self):
        self.path.write_text('bad header\n')
        with self.assertRaises(ValueError):
            TatamiMap(self.path, (100,100))
        position.Initialization({})
        self.assertIsNone(position.update(np.zeros((10,10,3), np.uint8)))
        self.assertIsNone(position.get_debug_state())

    def test_debug_does_not_change_recognition_frame(self):
        detector = Mock()
        detector.detect.return_value = (40, 0, 90, 100)
        human = position.HumanPosition(self.map, detector)
        rgb = np.zeros((100,100,3), np.uint8)
        human.update(rgb)
        display = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        draw_position_debug(display, human)
        self.assertFalse(rgb.any())
        self.assertTrue(display.any())


    def test_detection_failure_keeps_position_optional(self):
        detector = Mock()
        detector.detect.side_effect = RuntimeError("detector unavailable")
        position.estimator = position.HumanPosition(self.map, detector)
        self.assertIsNone(position.update(np.zeros((100,100,3), np.uint8)))
        self.assertIsNone(position.estimator)
        detector.close.assert_called_once()

    def test_position_reaches_existing_direction_estimator(self):
        from Managers import recognitionManager as recognition
        hands = {"hands": []}
        with patch.object(recognition, 'get_gesture_data', return_value={"name": "POINT"}), \
             patch.object(recognition.pointing, 'get_direction', return_value={"direction": "UP"}) as direction, \
             patch.object(recognition.stabilizer, 'stabilizer_process', return_value={"confirmed_direction": "UP"}):
            self.assertEqual(recognition.gesture_process(hands, "T2"), {"confirmed_direction": "UP"})
            direction.assert_called_once_with(hands, "T2")


class CameraTests(unittest.TestCase):
    def tearDown(self):
        camera.stop_camera()

    def test_movie_loop_and_end(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / 'movie.avi')
            writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'MJPG'), 10, (64,48))
            self.assertTrue(writer.isOpened())
            for value in (20,100,200):
                writer.write(np.full((48,64,3),value,np.uint8))
            writer.release()
            for loop in (True,False):
                camera.Initialization({'camera':{'sources':[{'id':'front','type':'movie','movie':True,'loop':loop,'connection':{'path':path}}]}})
                self.assertTrue(camera.start_camera())
                frames = [camera.read_frame('front') for _ in range(4)]
                self.assertTrue(all(frame is not None for frame in frames[:3]))
                self.assertEqual(frames[3] is not None, loop)
                self.assertEqual(camera.is_finished('front'), not loop)
                if loop:
                    np.testing.assert_array_equal(frames[0],frames[3])
                camera.stop_camera()

    def test_webcam_opened_once_and_live_failure_not_eof(self):
        with patch.object(cv2, 'VideoCapture') as capture:
            capture.return_value.isOpened.return_value = True
            result = camera.try_open({'id':'front','type':'webcam','connection':{'device_id':0}})
            self.assertEqual(capture.call_count, 1)
            camera.captures['front'] = result
            result.read.return_value = (False, None)
            self.assertIsNone(camera.read_frame('front'))
            self.assertFalse(camera.is_finished('front'))


if __name__ == '__main__':
    unittest.main()
