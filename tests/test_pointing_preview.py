import unittest
from unittest.mock import patch
import numpy as np
from pointing_preview import compare_direction, draw_preview


class PointingPreviewTests(unittest.TestCase):
    def hand(self, origin=(.2,.5), tip=(.3,.5)):
        landmarks = [{'x':0., 'y':0.} for _ in range(21)]
        for index, point in ((5,origin),(8,tip)):
            landmarks[index] = dict(zip(('x','y'),point))
        return {'hands':[{'landmarks':landmarks}]}

    @patch('pointing_preview.gesture.run', return_value={'name':'POINT'})
    def test_nearest_forward_target_and_angle_limit(self, _):
        result = compare_direction(self.hand(), (720,1280,3), {'ahead':(.8,.5),'behind':(.1,.5),'above':(.2,.1)})
        self.assertEqual(result['candidate'],'ahead')
        self.assertAlmostEqual(result['angles']['behind'],180)
        self.assertIsNone(compare_direction(self.hand(),(720,1280,3),{'above':(.2,.1)})['candidate'])

    @patch('pointing_preview.gesture.run', return_value={'name':'POINT'})
    def test_pixel_aspect_and_resolution_changes(self, _):
        hand = self.hand((.2,.5),(.3,.4))
        for shape in ((720,1280,3),(1080,1920,3),(1440,2560,3)):
            result=compare_direction(hand,shape,{'target':(.6,.1)})
            self.assertEqual(result['candidate'],'target')
            self.assertAlmostEqual(result['angles']['target'],0,places=5)

    def test_missing_hand_and_non_point_have_no_candidate(self):
        self.assertIsNone(compare_direction({'hands':[]},(720,1280,3),{})['candidate'])
        with patch('pointing_preview.gesture.run',return_value={'name':'OPEN_HAND'}):
            self.assertIsNone(compare_direction(self.hand(),(720,1280,3),{'ahead':(.8,.5)})['candidate'])
        with patch('pointing_preview.gesture.run',return_value={'name':'POINT'}):
            self.assertIsNone(compare_direction(self.hand(tip=(.2,.5)),(720,1280,3),{'ahead':(.8,.5)})['candidate'])

    @patch('pointing_preview.gesture.run', return_value={'name':'POINT'})
    def test_short_finger_accepted_with_lower_threshold(self, _):
        hand = self.hand(tip=(.21,.5))
        targets = {'ahead':(.8,.5)}
        self.assertIsNone(compare_direction(hand,(1440,2560,3),targets,min_finger_length_ratio=.02)['candidate'])
        self.assertEqual(compare_direction(hand,(1440,2560,3),targets,min_finger_length_ratio=.005)['candidate'],'ahead')
        self.assertIsNone(compare_direction(self.hand(tip=(.201,.5)),(1440,2560,3),targets)['candidate'])
        self.assertIsNone(compare_direction(self.hand(tip=(.2,.5)),(1440,2560,3),targets,min_finger_length_ratio=0)['candidate'])

    def test_display_does_not_modify_recognition_image(self):
        rgb=np.zeros((720,1280,3),np.uint8)
        result=compare_direction({'hands':[]},rgb.shape,{})
        display=draw_preview(rgb,{'AIRPURI':(.6,.3)},result,'AIRPURI',False)
        self.assertFalse(rgb.any())
        self.assertTrue(display.any())
