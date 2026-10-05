import copy
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from Core.application import Application
from Core import application as app
from Utils.configLoader import load_setting_config


class MainPointingTests(unittest.TestCase):
    def run_frames(self, states, dry_run=False, confirmed=None):
        config = copy.deepcopy(load_setting_config())
        config['pointing'] = {'enabled': True}
        self.assertTrue(app.appliances.Initialization(config))
        self.assertTrue(app.combo.Initialization(config))
        self.assertTrue(app.pointing.Initialization(config))
        application = Application(dry_run)
        snapshots = []
        with ExitStack() as stack:
            actions = stack.enter_context(patch.object(app.action, 'action_process', return_value=True))
            stack.enter_context(patch.object(app.feedback, 'feedback'))
            compare = stack.enter_context(patch.object(app.pointing, 'compare_direction'))
            recognize = stack.enter_context(patch.object(app.recognize, 'gesture_process'))
            for index, (timestamp, candidate, gesture) in enumerate(states):
                compare.return_value = {'candidate':candidate, 'gesture':gesture, 'origin':None, 'tip':None, 'angles':{}}
                recognize.return_value = {'confirmed_gesture': confirmed[index] if confirmed else gesture, 'confirmed_direction':'UP'}
                snapshots.append(application.update({'is_hand':gesture != 'NO HAND', 'hands':[]}, (100,100,3), timestamp))
            return [call.args[0] for call in actions.call_args_list], snapshots

    def tearDown(self):
        app.combo.reset_combo()
        app.pointing.enabled = False

    def test_ceiling_off_sent_once_without_person_position(self):
        actions, statuses = self.run_frames([(i*.7,'LIGHT','POINT') for i in range(5)])
        self.assertEqual(actions,['all_lights_power_off'])
        self.assertEqual(statuses[1]['last_action'],'all_lights_power_off')
        self.assertEqual(statuses[1]['action_status'],'SENT')

    def test_selection_point_is_not_used_as_combo_input(self):
        actions, statuses = self.run_frames([(i*.7,'AIRCON','POINT') for i in range(5)])
        self.assertEqual(actions,[])
        self.assertEqual(statuses[1]['selected'],'AIRCON')
        self.assertEqual(statuses[1]['state'],'WAIT_RELEASE')

    def test_selected_appliance_uses_existing_combo_after_release(self):
        actions, statuses = self.run_frames([(0,'AIRCON','POINT'),(.7,'AIRCON','POINT'),(1.4,'AIRCON','POINT'),(2.1,None,'OPEN_HAND')])
        self.assertEqual(actions,['aircon_cooling'])
        self.assertEqual(statuses[-1]['action_status'],'SENT')
        self.assertIsNone(statuses[-1]['selected'])

    def test_stale_confirmed_point_is_not_used_after_raw_release(self):
        actions, statuses = self.run_frames([(0,'AIRCON','POINT'),(.7,'AIRCON','POINT'),(1.4,None,'OPEN_HAND'),(2.1,None,'OPEN_HAND')], confirmed=['POINT','POINT','POINT','OPEN_HAND'])
        self.assertEqual(actions,['aircon_cooling'])
        self.assertEqual(statuses[2]['state'],'WAIT_RELEASE')

    def test_simulation_never_sends(self):
        actions, statuses = self.run_frames([(0,'LIGHT','POINT'),(.7,'LIGHT','POINT')],dry_run=True)
        self.assertEqual(actions,[])
        self.assertEqual(statuses[-1]['action_status'],'SIMULATED')

    def test_combo_timeout_is_checked_while_waiting_for_release(self):
        actions, statuses = self.run_frames([(0,'AIRCON','POINT'),(.7,'AIRCON','POINT'),(10,'AIRCON','POINT')])
        self.assertEqual(actions,[])
        self.assertEqual(statuses[-1]['state'],'COMBO_TIMEOUT')
        self.assertIsNone(statuses[-1]['selected'])

    def test_video_rewind_clears_selection(self):
        actions, statuses = self.run_frames([(5,'AIRCON','POINT'),(5.7,'AIRCON','POINT'),(0,None,'NO HAND')])
        self.assertEqual(actions,[])
        self.assertIsNone(statuses[-1]['selected'])
        self.assertIn('VIDEO RESTART',statuses[-1]['history'])
