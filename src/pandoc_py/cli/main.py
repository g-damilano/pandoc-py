from __future__ import annotations

import sys
from pathlib import Path

from pandoc_py.app import CONVERSION_EXCEPTIONS, convert_text
from pandoc_py.cli.options import OptionError, format_version_banner, parse_cli_options


class CliError(RuntimeError):
    """Raised for CLI usage or conversion errors."""


def _read_input(path: str) -> str:
    if path == '-':
        return sys.stdin.read()
    return Path(path).read_text(encoding='utf-8')


def _write_output(text: str, output_path: str | None = None) -> None:
    if output_path is None:
        sys.stdout.write(text)
        return
    Path(output_path).write_text(text, encoding='utf-8')


def main(argv: list[str] | None = None) -> int:
    try:
        options = parse_cli_options(argv)
    except OptionError as exc:
        sys.stderr.write(f'{type(exc).__name__}: {exc}\n')
        return 2

    if options.version:
        sys.stdout.write(format_version_banner())
        return 0

    try:
        source = _read_input(options.input_path)
        output = convert_text(source, options.from_format, options.to_format, standalone=options.standalone)
        _write_output(output, options.output_path)
        return 0
    except CONVERSION_EXCEPTIONS as exc:
        sys.stderr.write(f'{type(exc).__name__}: {exc}\n')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
