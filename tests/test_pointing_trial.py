import unittest
from unittest.mock import patch
from Recognizers.pointingTrial import PointingTrial
from pointing_preview import click_to_center, preview_geometry, compare_direction


class TrialTests(unittest.TestCase):
    def result(self, candidate='LIGHT', gesture='POINT'):
        return {'candidate': candidate, 'gesture': gesture}

    def test_lights_off_once_and_release_to_repeat(self):
        trial = PointingTrial(.5)
        self.assertIsNone(trial.update(self.result(), 0))
        self.assertIsNone(trial.update(self.result(), .49))
        self.assertEqual(trial.update(self.result(), .5), 'all_lights_power_off')
        self.assertIsNone(trial.update(self.result(), 2))
        trial.update(self.result(None, 'NO HAND'), 3)
        self.assertIsNone(trial.update(self.result(), 4))
        trial.update(self.result(None, 'OPEN_HAND'), 5)
        trial.update(self.result(), 6)
        self.assertEqual(trial.update(self.result(), 6.5), 'all_lights_power_off')

    def test_event_needs_no_person_position(self):
        trial = PointingTrial(.5)
        self.assertIsNone(trial.update(self.result('AIRPURI'), 0))
        self.assertEqual(trial.update(self.result('AIRPURI'), .5), 'SELECT AIRPURI')

    def test_lost_detection_resets_pending_hold(self):
        trial = PointingTrial(.5)
        trial.update(self.result(), 0)
        trial.update(self.result(None, 'NO HAND'), .4)
        self.assertIsNone(trial.update(self.result(), .5))
        self.assertEqual(trial.update(self.result(), 1), 'all_lights_power_off')

    def test_paused_frame_cannot_accumulate_hold(self):
        trial = PointingTrial(.5)
        for _ in range(20):
            self.assertIsNone(trial.update(self.result(), 1))

    def test_other_device_and_video_rewind(self):
        trial = PointingTrial(.5)
        trial.update(self.result('AIRCON'), 10)
        self.assertEqual(trial.update(self.result('AIRCON'), 11), 'SELECT AIRCON')
        self.assertIsNone(trial.update(self.result(), 0))
        self.assertEqual(trial.update(self.result(), .5), 'all_lights_power_off')

    def test_margin_click_coordinate_roundtrip(self):
        for shape in ((1080,1920,3),(1440,2560,3)):
            w,h=preview_geometry(shape)
            self.assertEqual(click_to_center(140,230,shape),(0,0))
            self.assertAlmostEqual(click_to_center(140+w*.5,230-h*.18,shape)[1],-.18)
            self.assertLess(click_to_center(50,300,shape)[0],0)
            self.assertIsNone(click_to_center(50,30,shape))

    @patch('pointing_preview.gesture.run',return_value={'name':'POINT'})
    def test_outside_target(self, _):
        points=[{'x':.5,'y':.5} for _ in range(21)]
        points[8]={'x':.5,'y':.4}
        result=compare_direction({'hands':[{'landmarks':points}]},(1080,1920,3),{'LIGHT':(.5,-.18),'AIRCON':(-.08,.1)})
        self.assertEqual(result['candidate'],'LIGHT')


if __name__ == '__main__':
    unittest.main()
