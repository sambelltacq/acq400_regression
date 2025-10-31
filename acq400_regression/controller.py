"""
"""

import logging
import os
import importlib
import argparse
from pathlib import Path
from pprint import pprint
import copy

from acq400_regression.harness import UUTCollection #rename from harness?
from acq400_regression.data_handler import Dataset

class Controller:
    tests_root = "tests/"
    
    def __init__(self, args):
        self.test = None
        self.args = args[0]
        self.unmatched_args = args[1]
        self.tests_available = self.discover_tests()
        #TODO add a test merge method here
        self.uuts = UUTCollection(self.args.uuts)

    @classmethod
    def discover_tests(cls):
        """return test that are available"""
        tests_available = {}
        package_dir = Path(__file__).parent
        tests_dir = Path(os.path.join(package_dir, cls.tests_root))

        for suite_dir in tests_dir.iterdir():
            if suite_dir.is_dir() and not suite_dir.name.startswith('__'):
                suite_name = suite_dir.name

                for test_file in suite_dir.glob("*.py"):
                    if not test_file.name.startswith('__'):
                        test_name = test_file.stem
                        relative_path = test_file.relative_to(tests_dir.parent)
                        
                        module_path = str(relative_path).replace('\\', '/').replace('/', '.').replace('.py', '')
                        
                        tests_available[test_name] = {
                            'suite': suite_name,
                            'path': str(relative_path).replace('\\', '/'),
                            'module_path': f"acq400_regression.{module_path}"
                        }
                        
                        logging.debug(f"Discovered test: {test_name} at {relative_path}")
        return tests_available


    def read_data(self):
        """Initialize and return a Dataset instance with the UUTs"""
        return Dataset(self.uuts)

    def run_test(self, test_name):
        """Run the test"""

        self.test = self.init_test(test_name)
        self.test.start_test()
        #TODO after every test save results to disk in case of test fail 
        logging.info(f"Test {test_name} complete")
    
    def init_test(self, test_name):
        """Init test with args"""
        test_class = self.import_test(self.tests_available[test_name]['module_path'])
        parser = argparse.ArgumentParser(add_help=False)
        parser = test_class.get_args(parser)
        test_args = parser.parse_known_args(self.unmatched_args, copy.copy(self.args))[0]
        logging.debug(f"Initing test class: {test_class}")
        return test_class(test_args, self.uuts, self)

    @classmethod
    def import_test(cls, module_path):
        """Import test class"""
        logging.debug(f"Importing test {module_path}")
        try:
            test_module = importlib.import_module(module_path)
            test_name = module_path.split('.')[-1]
            
            for test_class in dir(test_module):
                if test_class.upper() == test_name.upper():
                    break
            return getattr(test_module, test_class)
        except Exception as e:
            logging.error(f"Error importing test '{module_path}'")
            raise