#!/usr/bin/env python2

from cvsscalc import wxgui, cvsscalc
import logging
import sys

try:
    import argparse
except ImportError:
    argparse = None

def wx(infile):
   try:
       wxgui.main(infile)
   except:
       logging.basicConfig(level=logging.DEBUG, filename='cvsscalc.log')
       logging.exception('Autsch')


def main():
    parser = argparse.ArgumentParser(
                description='Calculates the CVSS 2 Score')
    main_group = parser.add_mutually_exclusive_group()
    parser.add_argument(
            'INFILE', type=argparse.FileType('r'), nargs='?')
    gui_group = main_group.add_argument_group()
    main_group.add_argument(
            '--gui', default='wx', help='show gui', nargs='?', choices=['wx'])
    console_group = main_group.add_argument_group()
    main_group.add_argument(
            '--console', help='only console', action='store_true')
    console_group.add_argument(
            '--cr', help='print with crlf', action='store_true')
    
    args = parser.parse_args()

    if args.console:
        cvsscalc.main(args.INFILE, crlf=args.cr)
    elif args.gui == 'wx':
        wx(args.INFILE)

if __name__ == '__main__':
    if argparse:
        main()
    else:
        wx(sys.argv[1] if len(sys.argv) > 1 else None)
