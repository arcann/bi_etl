import time
import unittest

from bi_etl.timer import Timer


class TestTimer(unittest.TestCase):
    _multiprocess_can_split_ = True

    def test_context_block(self):
        with Timer('tenth') as s:
            time.sleep(0.1)
        time.sleep(0.1)
        self.assertAlmostEqual(s.seconds_elapsed, 0.1, 1)
        secs, time_interval = s.seconds_elapsed_formatted.split(' ')
        secs = float(secs)
        self.assertAlmostEqual(secs, 0.1, 1)
        self.assertEqual(time_interval, 'seconds')

    def test_format_long(self):
        s = Timer()
        s.stored_time = 3660
        s.start()
        time.sleep(0.1)
        s.stop()
        sec_num, seconds, hrs_mins_secs = s.seconds_elapsed_formatted.split(' ')
        secs = float(sec_num)
        self.assertAlmostEqual(secs, 3660.1, 1)
        self.assertEqual(seconds, 'seconds')
        hrs_mins_secs = hrs_mins_secs.lstrip('(')
        hrs_mins_secs = hrs_mins_secs.rstrip(')')
        hrs, mins, secs = hrs_mins_secs.split(':')
        self.assertEqual('1h', hrs)
        self.assertEqual('01m', mins)
        self.assertEqual('0.1s', secs)

    def test_extra_start(self):
        s = Timer()
        s.start()
        time.sleep(0.1)
        s.start()
        time.sleep(0.1)
        s.stop()
        self.assertAlmostEqual(s.seconds_elapsed, 0.2, 1)

    def test_seconds_while_running(self):
        s = Timer()
        s.start()
        time.sleep(0.1)
        self.assertAlmostEqual(s.seconds_elapsed, 0.1, 1)
        time.sleep(0.1)
        s.stop()
        self.assertAlmostEqual(s.seconds_elapsed, 0.2, 1)

    def test_with_reset(self):
        s = Timer()
        s.start()
        time.sleep(0.1)
        s.reset()
        time.sleep(0.1)
        s.stop()
        self.assertAlmostEqual(s.seconds_elapsed, 0.1, 1)

    def test_no_start(self):
        s = Timer(start_running=False)
        # We need to force this to get an error.
        s.running = True
        self.assertRaises(ValueError, s.stop)

    def test_quick_steps(self):
        s = Timer()
        i = 0
        for _ in range(100):
            s.start()
            i += 1
            s.stop()
            time.sleep(0.01)
        # print(s.seconds_elapsed)
        # Actual time will depend on CPU type and load
        # However, it tests at 0.0003 seconds total
        # Whereas the 1st start vs final stop should be around 1 second apart.
        self.assertLess(s.seconds_elapsed, 0.01)
