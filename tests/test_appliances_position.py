import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np

from Managers import appliancesManager as appliances
from Managers import previewManager as preview


class AppliancePositionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'position.csv'
        self.settings = {'home_appliances': {'files': {
            'appliancesmap': str(Path(__file__).resolve().parent.parent / 'Data/homeAppliances/appliancesMap.csv'),
            'positionmap': str(self.path),
        }}}

    def write_map(self, rows):
        with self.path.open('w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['tatami_id', 'direction', 'device'])
            writer.writerows(rows)

    def tearDown(self):
        appliances.position_appliances = {}
        appliances.use_position_map = False
        appliances.appliances = []

    def test_same_direction_changes_device_by_tatami(self):
        self.write_map([['T1','RIGHT','AIRCON'], ['T2','RIGHT','AIRPURI']])
        self.assertTrue(appliances.Initialization(self.settings))
        self.assertEqual(appliances.select_appliance_abstract('RIGHT','T1')['device'], 'AIRCON')
        self.assertEqual(appliances.select_appliance_abstract('RIGHT','T2')['device'], 'AIRPURI')
        self.assertIs(appliances.select_appliance_abstract('RIGHT','T1'), appliances.appliances[0])
        self.assertEqual(preview.select_appliance_abstract('RIGHT','T1'), 'エアコン')
        self.assertEqual(preview.select_appliance_abstract('RIGHT','T2'), '空気清浄機')

    def test_preview_uses_position_with_debug_disabled(self):
        self.write_map([['T2','RIGHT','AIRPURI']])
        self.assertTrue(appliances.Initialization(self.settings))
        with patch.object(preview, 'window_created', True), \
             patch.object(preview, 'draw_text') as draw, \
             patch.object(preview.cv2, 'imshow'), \
             patch.object(preview.cv2, 'waitKey', return_value=-1), \
             patch.object(preview.cv2, 'getWindowProperty', return_value=1):
            self.assertTrue(preview.show_frame_detail(np.zeros((100,100,3),np.uint8), None, 'T2'))
            labels = {call.args[2]: call.args[1] for call in draw.call_args_list}
            self.assertEqual(labels['right'], '空気清浄機')
            self.assertEqual(labels['top_left'], 'None')

    def test_unknown_position_or_empty_direction_does_not_fall_back(self):
        self.write_map([['T1','UP_LEFT',''], ['T2','RIGHT','AIRCON']])
        self.assertTrue(appliances.Initialization(self.settings))
        for direction, position in [('UP_LEFT','T1'), ('UP_LEFT',None), ('RIGHT',None), ('RIGHT','T9'), ('UNKNOWN','T2')]:
            self.assertIsNone(appliances.select_appliance_abstract(direction,position))
            self.assertEqual(preview.select_appliance_abstract(direction,position), 'None')

    def test_existing_fixed_mapping_without_setting(self):
        del self.settings['home_appliances']['files']['positionmap']
        self.assertTrue(appliances.Initialization(self.settings))
        self.assertEqual(appliances.select_appliance_abstract('UP_LEFT')['device'], 'AIRCON')
        self.assertEqual(appliances.select_appliance_abstract('UP_LEFT','T7')['device'], 'AIRCON')

    def test_csv_is_loaded_once_and_reload_replaces_mapping(self):
        self.write_map([['T1','RIGHT','AIRCON']])
        self.assertTrue(appliances.Initialization(self.settings))
        self.path.unlink()
        self.assertEqual(appliances.select_appliance_abstract('RIGHT','T1')['device'], 'AIRCON')
        self.write_map([['T2','RIGHT','AIRPURI']])
        self.assertTrue(appliances.Initialization(self.settings))
        self.assertIsNone(appliances.select_appliance_abstract('RIGHT','T1'))

    def test_invalid_map_never_leaves_old_selection_active(self):
        for invalid in ([['T1','RIGHT','MISSING']], [['T1','BAD','AIRCON']],
                        [['T1','RIGHT','AIRCON'],['T1','RIGHT','AIRPURI']]):
            self.write_map([['T1','RIGHT','AIRCON']])
            self.assertTrue(appliances.Initialization(self.settings))
            self.write_map(invalid)
            self.assertFalse(appliances.Initialization(self.settings))
            self.assertIsNone(appliances.select_appliance_abstract('RIGHT','T1'))
            self.assertIsNone(appliances.select_appliance_abstract('UP_LEFT','T1'))

    def test_blank_template_selects_nothing(self):
        self.settings['home_appliances']['files']['positionmap'] = 'Data/homeAppliances/positionMap.csv'
        self.assertTrue(appliances.Initialization(self.settings))
        self.assertIsNone(appliances.select_appliance_abstract('UP_LEFT','T1'))


if __name__ == '__main__':
    unittest.main()
