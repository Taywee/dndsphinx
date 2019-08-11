#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © 2019 Taylor C. Richberger <taywee@gmx.com>
# This code is released under the license described in the LICENSE file

import re
import os
import locale
import argparse
from pathlib import Path
from functools import wraps

def absolute_rst(value):
    '''Checks that the path is an RST, and returns an absolute Path to it'''
    if not value.endswith('.rst'):
        raise 'file must be rst'

    return Path(value).resolve(strict=True)

def main():
    parser = argparse.ArgumentParser(description='Do Something')
    parser.add_argument('-c', '--chdir', help='Chdir directory (defaults to current), after selecting files.')
    parser.add_argument('-d', '--dest', help='Destination directory', required=True)
    parser.add_argument('-v', '--verbose', help='Output extra information', action='store_true')
    parser.add_argument('files', help='All files', nargs='+', type=absolute_rst)
    args = parser.parse_args()

    dest = Path(args.dest).resolve()

    dest.mkdir(parents=True, exist_ok=True)

    if args.chdir:
        os.chdir(args.chdir)

    pwd = Path().resolve()

    dest_path = '/' + str(dest.relative_to(pwd))

    verbose = args.verbose

    @wraps(print)
    def vprint(*args, **kwargs):
        if verbose:
            return print(*args, **kwargs)


    # Get all files in a (source, source_path, dest, dest_path) tuple
    files = [(source, '/' + str(source.relative_to(pwd))[:-4], dest / source.name, dest_path + '/' + source.name[:-4]) for source in args.files]

    for source_file, source_path, dest_file, dest_path in files:
        vprint(f'Moving {source_file} to {dest_file}')

        source_file.rename(dest_file)

        vprint(f'Scanning files and replacing {source_path} with {dest_path} everywhere')

        source_regex = re.compile('(?<![/a-zA-Z])' + re.escape(source_path) + '(?![/a-zA-Z])')

        for root, dirs, basenames in os.walk('.'):
            for basename in basenames:
                if basename.endswith('rst'):
                    path = (Path(root) / basename).resolve()

                    vprint(f'Replacing all instances in {path}')
                    with path.open('r') as file:
                        replacement = source_regex.sub(dest_path, file.read())
                    with path.open('w') as file:
                        file.write(replacement)

if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')
    main()

