import unittest

import mock

from pulp.server.async import worker_watcher


class TestParseAndLogEvent(unittest.TestCase):
    @mock.patch('pulp.server.async.worker_watcher.datetime')
    @mock.patch('pulp.server.async.worker_watcher._log_event')
    def test__parse_and_log_event(self, mock__log_event, mock_datetime):
        event = {'timestamp': mock.Mock(), 'type': mock.Mock(), 'hostname': mock.Mock()}

        result = worker_watcher._parse_and_log_event(event)

        # assert that the timestamp got converted using utcfromtimestamp()
        mock_datetime.utcfromtimestamp.assert_called_once_with(event['timestamp'])

        # assert that the resul dictionary has the right keys
        self.assertTrue('timestamp' in result)
        self.assertTrue('type' in result)
        self.assertTrue('worker_name' in result)

        # assert that the values in the resul dictionary are right
        self.assertTrue(result['timestamp'] is mock_datetime.utcfromtimestamp.return_value)
        self.assertTrue(result['type'] is event['type'])
        self.assertTrue(result['worker_name'] is event['hostname'])

        # assert that the event info is passed to _log_event
        mock__log_event.assert_called_once_with(result)


class TestLogEvent(unittest.TestCase):
    @mock.patch('pulp.server.async.worker_watcher._logger')
    @mock.patch('pulp.server.async.worker_watcher._')
    def test__log_event(self, mock_gettext, mock__logger):
        event_info = {'timestamp': mock.Mock(), 'type': mock.Mock(), 'worker_name': mock.Mock()}

        worker_watcher._log_event(event_info)

        log_string = "received '%(type)s' from %(worker_name)s at time: %(timestamp)s"
        mock_gettext.assert_called_with(log_string)
        mock__logger.assert_called_once()


class TestHandleWorkerHeartbeat(unittest.TestCase):
    @mock.patch('__builtin__.list', return_value=False)
    @mock.patch('pulp.server.async.worker_watcher._parse_and_log_event')
    @mock.patch('pulp.server.async.worker_watcher.Criteria')
    @mock.patch('pulp.server.async.worker_watcher.resources')
    @mock.patch('pulp.server.async.worker_watcher.Worker')
    @mock.patch('pulp.server.async.worker_watcher._')
    @mock.patch('pulp.server.async.worker_watcher._logger')
    def test_handle_worker_heartbeat_new(self, mock__logger, mock_gettext, mock_worker,
                                         mock_resources, mock_criteria,
                                         mock__parse_and_log_event, mock_list):
        mock_event = mock.Mock()

        worker_watcher.handle_worker_heartbeat(mock_event)

        event_info = mock__parse_and_log_event.return_value
        mock__parse_and_log_event.assert_called_with(mock_event)
        mock_criteria.assert_called_once_with(filters={'_id': event_info['worker_name']},
                                              fields=('_id', 'last_heartbeat'))
        mock_resources.filter_workers.assert_called_once(mock_criteria.return_value)
        mock_worker.assert_called_once_with(event_info['worker_name'], event_info['timestamp'])
        mock_gettext.assert_called_once_with("New worker '%(worker_name)s' discovered")
        mock__logger.assert_called_once()
        mock_worker.return_value.save.assert_called_once_with()

    @mock.patch('__builtin__.list', return_value=True)
    @mock.patch('pulp.server.async.worker_watcher._parse_and_log_event')
    @mock.patch('pulp.server.async.worker_watcher.Criteria')
    @mock.patch('pulp.server.async.worker_watcher.resources')
    @mock.patch('pulp.server.async.worker_watcher.Worker')
    @mock.patch('pulp.server.async.worker_watcher._', new=mock.Mock())
    @mock.patch('pulp.server.async.worker_watcher._logger', new=mock.Mock())
    def test_handle_worker_heartbeat_update(self, mock_worker, mock_resources,
                                            mock_criteria,
                                            mock__parse_and_log_event, mock_list):
        mock_event = mock.Mock()

        worker_watcher.handle_worker_heartbeat(mock_event)

        event_info = mock__parse_and_log_event.return_value
        mock__parse_and_log_event.assert_called_with(mock_event)
        mock_criteria.assert_called_once_with(filters={'_id': event_info['worker_name']},
                                              fields=('_id', 'last_heartbeat'))
        mock_resources.filter_workers.assert_called_once(mock_criteria.return_value)
        mock_worker.get_collection.assert_called_once_with()
        find_and_modify = mock_worker.get_collection.return_value.find_and_modify
        find_and_modify.assert_called_once_with(
            query={'_id': event_info['worker_name']},
            update={'$set': {'last_heartbeat': event_info['timestamp']}}
        )


class TestHandleWorkerOffline(unittest.TestCase):
    @mock.patch('pulp.server.async.worker_watcher._parse_and_log_event')
    @mock.patch('pulp.server.async.worker_watcher._delete_worker')
    @mock.patch('pulp.server.async.worker_watcher._')
    @mock.patch('pulp.server.async.worker_watcher._logger')
    def test_handle_worker_offline(self, mock__logger, mock_gettext, mock__delete_worker,
                                   mock__parse_and_log_event):
        mock_event = mock.Mock()

        worker_watcher.handle_worker_offline(mock_event)

        event_info = mock__parse_and_log_event.return_value
        mock__parse_and_log_event.assert_called_once_with(mock_event)
        mock_gettext.assert_called_once_with("Worker '%(worker_name)s' shutdown")
        mock__logger.info.assert_called_once()
        mock__delete_worker.assert_called_once_with(event_info['worker_name'], normal_shutdown=True)
