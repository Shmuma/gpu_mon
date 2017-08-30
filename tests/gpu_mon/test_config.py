import unittest
from gpu_mon import config
import configparser


class TestConfigs(unittest.TestCase):
    def test_minimal(self):
        parser = configparser.ConfigParser()
        parser.read_string("""
        [defaults]
        interval_seconds=123
        
        [tty]
        enabled=False
        """)
        c = config.Configuration.config_from_parser(parser)
        self.assertIsNotNone(c)
        self.assertIsInstance(c, config.Configuration)
        self.assertEqual(c.interval_seconds, 123)
        self.assertEqual(len(c.gpus_conf), 0)
        self.assertEqual(len(c.processes_conf), 0)


if __name__ == '__main__':
    unittest.main()
