import sys

from typing import Iterable, Optional, TextIO, Tuple


def draw_table(
        titles: Iterable[str],
        data: Tuple[Tuple[str, ...], ...],
        out_stream: Optional[TextIO] = None,
        err_stream: Optional[TextIO] = None
):
    if out_stream is None:
        out_stream = sys.stdout
    if err_stream is None:
        err_stream = sys.stderr

    colwidths = tuple(max(len(row[col]) for row in (titles,) + data) for col in range(len(titles)))
    err_stream.write('|'.join(title.ljust(colwidths[col]) for col, title in enumerate(titles)))
    err_stream.write('\n')
    err_stream.write('+'.join('-' * width for width in colwidths))
    err_stream.write('\n')
    err_stream.flush()
    for row in data:
        for col, coldata in enumerate(row):
            assert len(coldata) <= colwidths[col]
            not_last = col < len(colwidths) - 1
            out_stream.write(coldata)
            if not_last:
                out_stream.write(', ')
            out_stream.flush()
            if not_last:
                err_stream.write('\b\b')
                err_stream.write(' ' * (colwidths[col] - len(coldata)))
                err_stream.write('|')
                err_stream.flush()
        out_stream.write('\n')
        out_stream.flush()
