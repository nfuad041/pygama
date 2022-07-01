"""
pygama's command line interface utilities.
"""
import argparse
import logging
import os
import sys

import numpy as np

import pygama
from pygama.dsp import build_dsp
from pygama.raw import build_raw


def pygama_cli():
    """pygama's command line interface.

    Defines the command line interface (CLI) of the package, which exposes some
    of the most used functions to the console.  This function is added to the
    ``entry_points.console_scripts`` list and defines the ``pygama`` executable
    (see ``setuptools``' documentation). To learn more about the CLI, have a
    look at the help section:

    .. code-block:: console

      $ pygama --help
      $ pygama build-raw --help  # help section for a specific sub-command
    """

    parser = argparse.ArgumentParser(
        prog='pygama',
        description="pygama's command-line interface")

    # global options
    parser.add_argument('--version', action='store_true',
                        help="""Print pygama version and exit""")
    parser.add_argument('--verbose', '-v', action='store_true',
                        help="""Increase the program verbosity""")

    subparsers = parser.add_subparsers()

    add_build_raw_parser(subparsers)
    add_build_dsp_parser(subparsers)

    if len(sys.argv) < 2:
        parser.print_usage(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG,
                            format="%(name)s [%(levelname)s] %(message)s")
    else:
        logging.basicConfig(level=logging.INFO,
                            format="%(name)s [%(levelname)s] %(message)s")

    if args.version:
        print(pygama.__version__)
        sys.exit()

    args.func(args)


def add_build_raw_parser(subparsers):
    """Configure :func:`.raw.build_raw.build_raw` command line interface"""

    parser_d2r = subparsers.add_parser(
        'build-raw', description="""Convert data into LEGEND HDF5 (LH5) raw format""")
    parser_d2r.add_argument('in_stream', nargs='+',
                            help="""Input stream. Can be a single file, a list
                            of files or any other input type supported by the
                            selected streamer""")
    parser_d2r.add_argument('--stream-type', '-t',
                            help="""Input stream type name. Use this if the
                            stream type cannot be automatically deduced by
                            pygama""")
    parser_d2r.add_argument('--out-spec', '-o',
                            help="""Specification for the output stream. HDF5
                            or JSON file name""")
    parser_d2r.add_argument('--buffer_size', '-b', type=int, default=8192,
                            help="""Set buffer size""")
    parser_d2r.add_argument('--max-rows', '-n', type=int, default=np.inf,
                            help="""Maximum number of rows of data to process
                            from the input file""")
    parser_d2r.add_argument('--overwrite', '-w', action='store_true',
                            help="""Overwrite output files""")

    parser_d2r.set_defaults(func=build_raw_cli)


def build_raw_cli(args):
    """Passes command line arguments to :func:`.raw.build_raw.build_raw`."""

    for stream in args.in_stream:
        basename = os.path.splitext(os.path.basename(stream))[0]
        build_raw(stream, in_stream_type=args.stream_type,
                  out_spec=args.out_spec, buffer_size=args.buffer_size,
                  n_max=args.max_rows, overwrite=args.overwrite,
                  orig_basename=basename)


def add_build_dsp_parser(subparsers):
    """Configure :func:`.dsp.build_dsp.build_dsp` command line interface"""

    parser_r2d = subparsers.add_parser(
        'build-dsp', description="""Process LH5 raw files and produce a
        dsp file using a JSON configuration""")
    parser_r2d.add_argument('raw_lh5_file', nargs='+',
                            help="""Input raw LH5 file. Can be a single file or
                            a list of them""")
    parser_r2d.add_argument('--config', '-c', required=True,
                            help=""""JSON file holding configuration of signal
                            processing routines""")
    parser_r2d.add_argument('--hdf5-groups', '-g', nargs='*', default=None,
                            help="""Name of group in the LH5 file. By default
                            process all base groups. Supports wildcards""")
    parser_r2d.add_argument('--output', '-o', default=None,
                            help="""Name of output file, if only one is
                            supplied. By default, output to
                            <input-filename>_dsp.lh5""")
    parser_r2d.add_argument('--database', '-d', default=None,
                            help="""JSON file to read database parameters from.
                            Should be nested dict with channel at the top
                            level, and parameters below that""")
    parser_r2d.add_argument('--output-pars', '-p', nargs='*', default=None,
                            help="""List of additional output DSP parameters
                            written to file. By default use the "outputs" list
                            defined in in the JSON configuration file""")
    parser_r2d.add_argument('--max-rows', '-n', default=None, type=int,
                            help="""Number of rows to process. By default
                            do the whole file""")
    parser_r2d.add_argument('--block', '-b', default=16, type=int,
                            help="""Number of waveforms to process
                            simultaneously. Default is 16""")
    parser_r2d.add_argument('--chunk', '-k', default=3200, type=int,
                            help="""Number of waveforms to read from disk at a
                            time. Default is 3200""")

    group = parser_r2d.add_mutually_exclusive_group()
    group.add_argument('--overwrite', '-w', action='store_const',
                       const='r', dest='writemode', default='r',
                       help="""Overwrite file if it already exists. Default
                       option""")
    group.add_argument('--update', '-u', action='store_const', const='u',
                       dest='writemode', help="""Update existing file with new
                       values. Useful with the --outpar option""")
    group.add_argument('--append', '-a', action='store_const', const='a',
                       dest='writemode', help="""Append values to existing
                       file""")

    parser_r2d.set_defaults(func=build_dsp_cli)


def build_dsp_cli(args):
    """Passes command line arguments to :func:`.dsp.build_dsp.build_dsp`."""

    if len(args.raw_lh5_file) > 1 and args.output is not None:
        raise NotImplementedError('not possible to set multiple output file names yet')

    out_files = []
    if len(args.raw_lh5_file) == 1:
        if args.output is None:
            basename = os.path.splitext(os.path.basename(args.raw_lh5_file[0]))[0]
            basename = basename.removesuffix('_raw')
            out_files.append(f'{basename}_dsp.lh5')
        else:
            out_files.append(args.output)
    else:
        for file in args.raw_lh5_file:
            basename = os.path.splitext(os.path.basename(file))[0]
            basename = basename.removesuffix('_raw')
            out_files.append(f'{basename}_dsp.lh5')

    for i in range(len(args.raw_lh5_file)):
        build_dsp(args.raw_lh5_file[i], out_files[i], args.config,
                  lh5_tables=args.hdf5_groups,
                  database=args.database, verbose=args.verbose,
                  outputs=args.output_pars, n_max=args.max_rows,
                  write_mode=args.writemode, buffer_len=args.chunk,
                  block_width=args.block)
