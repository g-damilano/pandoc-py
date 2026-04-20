from __future__ import annotations

import argparse
from dataclasses import dataclass

from pandoc_py import __version__
from pandoc_py.app import SUPPORTED_INPUT_FORMATS, SUPPORTED_OUTPUT_FORMATS


class OptionError(ValueError):
    """Raised when CLI options fall outside the current supported slice."""


_FORMAT_ALIASES = {
    'markdown': 'markdown',
    'json': 'json',
    'pandoc-json': 'json',
    'html': 'html',
    'html5': 'html',
    'xhtml': 'html',
    'native': 'native',
    'commonmark': 'commonmark',
    'commonmark_x': 'commonmark_x',
    'commonmark-x': 'commonmark_x',
}


@dataclass(frozen=True)
class CliOptions:
    input_path: str = '-'
    from_format: str = 'markdown'
    to_format: str = 'markdown'
    output_path: str | None = None
    standalone: bool = False
    version: bool = False


def normalize_format(value: str, *, role: str) -> str:
    canonical = _FORMAT_ALIASES.get(value.casefold())
    if canonical is None:
        supported = SUPPORTED_INPUT_FORMATS if role == 'input' else SUPPORTED_OUTPUT_FORMATS
        raise OptionError(f'Unsupported {role} format: {value}. Supported: {", ".join(sorted(supported))}.')
    supported = SUPPORTED_INPUT_FORMATS if role == 'input' else SUPPORTED_OUTPUT_FORMATS
    if canonical not in supported:
        raise OptionError(f'Unsupported {role} format: {value}. Supported: {", ".join(sorted(supported))}.')
    return canonical


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='pandoc_py')
    parser.add_argument('input_path', nargs='?', default='-')
    parser.add_argument('-f', '--from', dest='from_format', required=False, default='markdown')
    parser.add_argument('-t', '--to', dest='to_format', required=False, default='markdown')
    parser.add_argument('-o', '--output', dest='output_path', required=False)
    parser.add_argument('-s', '--standalone', action='store_true')
    parser.add_argument('--version', action='store_true')
    return parser


def parse_cli_options(argv: list[str] | None = None) -> CliOptions:
    args = build_parser().parse_args(argv)
    if args.version:
        return CliOptions(
            input_path=args.input_path,
            from_format=args.from_format,
            to_format=args.to_format,
            output_path=args.output_path,
            standalone=args.standalone,
            version=True,
        )
    return CliOptions(
        input_path=args.input_path,
        from_format=normalize_format(args.from_format, role='input'),
        to_format=normalize_format(args.to_format, role='output'),
        output_path=args.output_path,
        standalone=args.standalone,
        version=False,
    )


def format_version_banner() -> str:
    return f'pandoc_py {__version__}\n'
