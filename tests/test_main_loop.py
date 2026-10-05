import copy
import unittest
from contextlib import ExitStack
from unittest.mock import Mock, patch
import numpy as np
import main


class MainLoopTests(unittest.TestCase):
    def test_preview_drawn_once_per_processed_frame_after_controller_update(self):
        frame=np.zeros((10,10,3),np.uint8)
        states=[{'state':'NO_HAND'},{'state':'SELECTING'},{'state':'WAIT_RELEASE'}]
        config={'camera':{'sources':[{'id':'front','type':'movie','enabled':True}]}}
        capture=Mock()
        capture.get.return_value=1
        controller=Mock()
        controller.update.side_effect=states
        with ExitStack() as stack:
            def mock(obj,name,**kwargs):
                return stack.enter_context(patch.object(obj,name,**kwargs))
            mock(main.figload,'load_setting_config',return_value=copy.deepcopy(config))
            init=mock(main.initializer,'Managers_initialize',return_value=True)
            mock(main,'Application',return_value=controller)
            mock(main.camera,'start_camera',return_value=True)
            mock(main.camera,'get_capture',return_value=capture)
            mock(main.camera,'read_frame',side_effect=[frame,frame,frame,None])
            mock(main.camera,'get_timestamp',side_effect=[0,.1,.2])
            mock(main.camera,'stop_camera')
            mock(main.system,'get_mem',return_value=0)
            mock(main.system,'get_cpu',return_value=0)
            mock(main.cascade,'cascade_process',return_value={'cased_frame':frame,'is_motion':False})
            mock(main.model,'model_process',return_value={'is_hand':False,'hands':[]})
            mock(main.model,'close')
            mock(main.pointing,'enabled',new=True)
            show=mock(main.preview,'show_frame_pointing',return_value=True)
            mock(main.preview,'close_window')
            mock(main.preview,'last_key',new=-1)
            self.assertTrue(main.main())
            self.assertEqual(controller.update.call_count,3)
            self.assertEqual(show.call_count,3)
            self.assertEqual([call.args[2]['state'] for call in show.call_args_list],['NO_HAND','SELECTING','WAIT_RELEASE'])
            self.assertTrue(init.call_args.args[0]['runtime']['dry_run'])

    def test_headless_requires_bounded_frames(self):
        with self.assertRaises(SystemExit):
            main.make_options(['--headless'])
