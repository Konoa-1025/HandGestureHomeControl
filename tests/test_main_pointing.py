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

    def test_held_point_toggles_once_after_selection(self):
        actions, statuses = self.run_frames([(i*.7,'AIRCON','POINT') for i in range(5)])
        self.assertEqual(actions,['aircon_toggle_power'])
        self.assertEqual(statuses[1]['selected'],'AIRCON')
        self.assertEqual(statuses[1]['state'],'COMBO')
        self.assertIsNone(statuses[1]['last_action'])
        self.assertEqual(statuses[-1]['state'],'WAIT_RELEASE')

    def test_selected_appliance_uses_existing_combo_after_release(self):
        actions, statuses = self.run_frames([(0,'AIRCON','POINT'),(.7,'AIRCON','POINT'),(1.4,None,'OPEN_HAND')])
        self.assertEqual(actions,['aircon_cooling'])
        self.assertEqual(statuses[-1]['action_status'],'SENT')
        self.assertIsNone(statuses[-1]['selected'])

    def test_stale_confirmed_point_is_not_used_after_raw_release(self):
        actions, statuses = self.run_frames([(0,'AIRCON','POINT'),(.7,'AIRCON','POINT'),(1.4,None,'OPEN_HAND'),(2.1,None,'OPEN_HAND')], confirmed=['POINT','POINT','POINT','OPEN_HAND'])
        self.assertEqual(actions,['aircon_cooling'])
        self.assertEqual(statuses[2]['state'],'COMBO')

    def test_lost_hand_does_not_execute_stale_point(self):
        actions, statuses = self.run_frames([(0,'AIRCON','POINT'),(.7,'AIRCON','POINT'),(1.4,None,'NO HAND')], confirmed=['POINT','POINT','POINT'])
        self.assertEqual(actions,[])
        self.assertIsNone(statuses[-1]['last_action'])

    def test_point_away_from_selected_device_does_not_toggle(self):
        actions, statuses = self.run_frames([(0,'AIRCON','POINT'),(.7,'AIRCON','POINT'),(1.4,'BRAIND','POINT')])
        self.assertEqual(actions,[])

    def test_release_then_point_allows_second_toggle(self):
        actions, statuses = self.run_frames([(0,'AIRCON','POINT'),(.7,'AIRCON','POINT'),(1.4,'AIRCON','POINT'),(2.1,None,'OPEN_HAND'),(2.8,'AIRCON','POINT'),(3.5,'AIRCON','POINT'),(4.2,'AIRCON','POINT'),(4.9,'AIRCON','POINT')])
        self.assertEqual(actions,['aircon_toggle_power','aircon_toggle_power'])

    def test_each_device_keeps_its_existing_point_action(self):
        for device, expected in [('AIRCON','aircon_toggle_power'),('BRAIND','braind_toggle_upper'),('AIRPURI','airpurifier_toggle_power')]:
            with self.subTest(device=device):
                actions, statuses = self.run_frames([(0,device,'POINT'),(.7,device,'POINT'),(1.4,device,'POINT')])
                self.assertEqual(actions,[expected])

    def test_toggle_in_simulation_never_sends(self):
        actions, statuses = self.run_frames([(0,'AIRCON','POINT'),(.7,'AIRCON','POINT'),(1.4,'AIRCON','POINT')], dry_run=True)
        self.assertEqual(actions,[])
        self.assertEqual(statuses[-1]['last_action'],'aircon_toggle_power')
        self.assertEqual(statuses[-1]['action_status'],'SIMULATED')

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

    def test_point_recovery_between_input_intervals_is_not_missed(self):
        actions, statuses = self.run_frames([(0,'AIRCON','POINT'),(.7,'AIRCON','POINT'),(1.4,None,'NO HAND'),(1.5,'AIRCON','POINT')])
        self.assertEqual(actions,['aircon_toggle_power'])

    def test_canceled_selection_can_retry_without_changing_hand_shape(self):
        actions, statuses = self.run_frames([(0,'AIRCON','POINT'),(.7,'AIRCON','POINT'),(1.4,None,'NO HAND'),(2,None,'NO HAND'),(2.1,'AIRCON','POINT'),(2.8,'AIRCON','POINT'),(3.5,'AIRCON','POINT')])
        self.assertEqual(statuses[3]['state'],'COMBO_CANCELED')
        self.assertEqual(actions,['aircon_toggle_power'])

    def test_timed_out_selection_can_retry_without_changing_hand_shape(self):
        actions, statuses = self.run_frames([(0,'AIRCON','POINT'),(.7,'AIRCON','POINT'),(6,'AIRCON','POINT'),(6.7,'AIRCON','POINT'),(7.4,'AIRCON','POINT')])
        self.assertEqual(actions,['aircon_toggle_power'])
