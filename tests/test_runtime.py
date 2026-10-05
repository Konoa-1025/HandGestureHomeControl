import threading
import unittest
from contextlib import ExitStack
from unittest.mock import Mock, patch

from Core import initializer
from Core.application import Application
from Managers import echonetManager
from EchonetLite.EchonetLite import EchonetLite


class RuntimeTests(unittest.TestCase):
    def test_dry_run_does_not_start_device_network_or_sound(self):
        with ExitStack() as stack:
            mocks={}
            for name in ('action','camera','cascade','combo','system','tcp','echonet','recognition','experiment','model','feedback','appliances','pointing','position','preview'):
                mocks[name]=stack.enter_context(patch.object(getattr(initializer,name),'Initialization',return_value=True))
            stack.enter_context(patch.object(initializer.pointing,'enabled',True))
            self.assertTrue(initializer.Managers_initialize({'runtime':{'dry_run':True,'headless':True}}))
            for name in ('tcp','echonet','feedback','system','position','preview'):
                mocks[name].assert_not_called()
            mocks['pointing'].assert_called_once()

    def test_close_stops_receive_thread_without_network(self):
        device=EchonetLite.__new__(EchonetLite)
        device.debug=False
        device._stop_event=threading.Event()
        device.rsock=Mock()
        device.thread=Mock()
        device.close()
        self.assertTrue(device._stop_event.is_set())
        device.rsock.close.assert_called_once()
        device.thread.join.assert_called_once_with(timeout=1.5)

    def test_failed_action_is_reported_as_failed(self):
        with patch('Core.application.action.action_process',return_value=False):
            app=Application(False)
            app.execute('all_lights_power_off')
            self.assertEqual(app.action_status,'FAILED')
            self.assertEqual(app.last_action,'all_lights_power_off')

    def test_close_manager_is_idempotent(self):
        previous=echonetManager.el
        try:
            resource=Mock()
            echonetManager.el=resource
            echonetManager.close()
            echonetManager.close()
            resource.close.assert_called_once()
        finally:
            echonetManager.el=previous
