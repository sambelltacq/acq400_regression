import argparse
from acq400_regression.controller import Controller
from acq400_regression.utilities import Tri

class CustomArgumentParser(argparse.ArgumentParser):

    add_help = False
    
    def print_help(self, file=None):
        """Override print_help"""
        if 'test' in self.prog:
            self.print_all_test_args()
        else:
            super().print_help(file)

    def print_all_test_args(self):
        """Print help from every test"""
        import logging
        logging.disable(logging.CRITICAL)
        
        try:
            tests_available = Controller.discover_tests()

            for test_name, test_conf in sorted(tests_available.items()):
                print(f"Test - {test_name.title()}")
                print(f"{'-'*70}")
                
                try:
                    test_class = Controller.import_test(test_conf['module_path'])
                    test_parser = argparse.ArgumentParser(
                        prog=f"acq400_regression test {test_name}",
                        add_help=False,
                        formatter_class=argparse.RawDescriptionHelpFormatter,
                        parents=[self]
                    )
                    test_parser = test_class.get_args(test_parser)
                    remove_arg(test_parser, 'tests')
                    test_parser.print_help()
                    print("\n")
                except Exception as e:
                    print(f"Error loading help for {test_name}: {e}\n")
        finally:
            logging.disable(logging.NOTSET)


class ArgTypes:
    """Custom argument type converters"""
    
    @staticmethod
    def list_of_ints(arg):
        return list(map(int, arg.split(',')))

    @staticmethod
    def list_of_strings_comma(arg):
        return arg.split(',')

    @staticmethod
    def list_of_strings_slash(arg):
        return arg.split('/')

    @staticmethod
    def list_of_trinarys(trinarys):
        def _type(arg):
            if arg.lower() == 'all': return [Tri(trinary) for trinary in trinarys]
            return [Tri(trinary) for trinary in arg.split('/')]
        return _type

    @staticmethod
    def list_of_channels(arg):
        if arg.lower() == 'all':
            return 'all'

        channels = []
        for chan in arg.split(','):
            if '-' in chan:
                start, end = map(int, chan.split('-'))
                channels.extend(list(range(start, end + 1)))
            else:
                channels.append(int(chan))
        return channels


def remove_arg(parser, arg_name):
    for action in parser._actions[:]:
        if action.dest == arg_name:
            # Remove from _actions list
            parser._actions.remove(action)
            # Also remove from the action group
            for group in parser._action_groups:
                if action in group._group_actions:
                    group._group_actions.remove(action)
            return action
    return None

def get_parser():
    parser = CustomArgumentParser(
        prog='acq400_regression',
        description='ACQ400 Regression Testing Framework',
        epilog='For more information, visit: https://github.com/acq400/acq400_regression',
        add_help=False
    )

    parser.add_argument('-h', '--help', action='help', help=argparse.SUPPRESS)
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)

    # exec_parser command
    parser.exec_parser = subparsers.add_parser('exec', help='execute test definition file')
    parser.exec_parser.add_argument('uut', nargs='+', help="uut hostnames")
    parser.exec_parser.add_argument('file', help="test definition filepath")
    
    # test_parser command
    parser.test_parser = subparsers.add_parser('test', help='run regression test', add_help=False)
    parser.test_parser.add_argument('-h', '--help', action='help', help=argparse.SUPPRESS)
    parser.test_parser.add_argument('--channels', default=[1], type=ArgTypes.list_of_channels, help="Channels to test (e.g., 1,2,3,4 or all)")
    parser.test_parser.add_argument('--shots', default=1, type=int, help="Total shots per run")
    #parser.test_parser.add_argument('--master', default=None, type=str, help='Master UUT override') #TODO fix this
    parser.test_parser.add_argument('--wavelength', default=20000, type=int, help="target samples in waveform")
    parser.test_parser.add_argument('--cycles', default=1, type=int, help='waveform cycles')
    parser.test_parser.add_argument('--demux', default=0, type=int, help="Demux (disabled: 0) or (enabled: 1)")
    parser.test_parser.add_argument('--spad', default='1,2,0', help="spad value")
    parser.test_parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')


    #TODO --plot=-1/0/1/add plot arg -1 plot on shot error 0 no plot and 1 plot every shot
    #TODO --plot_1
    #TODO --plot_2
    #TODO uuts if multple uut then plot all on one plot to compare channels have a split plot option


    parser.test_parser.add_argument('tests', default=['post'], type=ArgTypes.list_of_strings_comma, help=f"Tests to run")
    parser.test_parser.add_argument('uuts', nargs='+', help="uut hostnames")

    # upload_parser command
    parser.upload_parser = subparsers.add_parser('upload', help='upload results')
    parser.upload_parser.add_argument('url', default="shuna/regression", help="upload url")
    parser.upload_parser.add_argument('--mark', action='store_true', help='Mark uploaded results')
    return parser


def get_test_parser():
    """Get the test subparser for printing help"""
    parser = get_parser()
    return parser.test_parser


def get_args():
    parser = get_parser()
    args, unmatched = parser.parse_known_args()
    args.unmatched = unmatched
    return args



def merge_args(parent, child):
    global_dict = vars(parent)
    test_dict = vars(child)
    
    merged_dict = {**global_dict, **test_dict}
    
    return argparse.Namespace(**merged_dict)
