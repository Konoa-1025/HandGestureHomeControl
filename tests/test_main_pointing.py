import copy
import unittest
from contextlib import ExitStack
from unittest.mock import patch
import numpy as np

import main as app
from Utils.configLoader import load_setting_config


class MainPointingTests(unittest.TestCase):
    def run_frames(self, states):
        config = copy.deepcopy(load_setting_config())
        config['pointing'] = {'enabled': True}
        frame = np.zeros((100,100,3),np.uint8)
        index = -1
        def read(camera_id):
            nonlocal index
            if camera_id != 'front':
                return None
            index += 1
            return frame if index < len(states) else None
        def initialize(settings):
            return (app.appliances.Initialization(settings) and app.combo.Initialization(settings)
                    and app.pointing.Initialization(settings))
        def result(*args):
            candidate, gesture = states[index]
            return {'candidate':candidate, 'gesture':gesture, 'origin':None, 'tip':None, 'angles':{}}
        with ExitStack() as stack:
            def replace(obj,name,**kwargs):
                return stack.enter_context(patch.object(obj,name,**kwargs))
            replace(app.figload,'load_setting_config',return_value=config)
            replace(app.initializer,'Managers_initialize',side_effect=initialize)
            replace(app.camera,'start_camera',return_value=True)
            replace(app.camera,'read_frame',side_effect=read)
            replace(app.camera,'get_timestamp',side_effect=lambda _: index * .7)
            replace(app.camera,'is_finished',return_value=True)
            replace(app.camera,'stop_camera')
            replace(app.system,'get_mem',return_value=10)
            replace(app.system,'get_cpu',return_value=10)
            replace(app.cascade,'cascade_process',return_value={'is_motion':False,'cased_frame':frame})
            replace(app.model,'model_process',return_value={'is_hand':True,'hands':[]})
            replace(app.pointing,'compare_direction',side_effect=result)
            replace(app.preview,'show_frame_pointing',return_value=True)
            replace(app.preview,'close_window')
            replace(app.recognize,'gesture_process',side_effect=lambda *args: {'confirmed_gesture':states[index][1],'confirmed_direction':'UP'})
            replace(app.combo.time,'monotonic',side_effect=lambda: index*.7)
            replace(app.feedback,'feedback')
            actions = replace(app.action,'action_process',return_value=True)
            app.main()
            return [call.args[0] for call in actions.call_args_list]

    def tearDown(self):
        app.combo.reset_combo()
        app.pointing.enabled = False

    def test_ceiling_off_sent_once_without_person_position(self):
        self.assertEqual(self.run_frames([('LIGHT','POINT')]*5), ['all_lights_power_off'])

    def test_selection_point_is_not_used_as_combo_input(self):
        self.assertEqual(self.run_frames([('AIRCON','POINT')]*5), [])

    def test_selected_appliance_uses_existing_combo_after_release(self):
        states = [('AIRCON','POINT'),('AIRCON','POINT'),('AIRCON','POINT'),(None,'OPEN_HAND')]
        self.assertEqual(self.run_frames(states), ['aircon_cooling'])
