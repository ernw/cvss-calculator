import argparse
from cvsscalc import wxgui, cvsscalc

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
                description='Calculates the CVSS 2 Score')
    parser.add_argument(
            'INFILE', type=argparse.FileType('r'), nargs='?')
    parser.add_argument(
            '--gui', default='wx', help='show gui', nargs='?', choices=['wx'])
    parser.add_argument(
            '--console', help='only console', action='store_true')


    args = parser.parse_args()

    if args.console:
        cvsscalc.main(args.INFILE)
    elif args.gui == 'wx':
        wxgui.main(args.INFILE)
