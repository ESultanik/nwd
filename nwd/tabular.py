import sys

def draw_table(titles, data, out_stream=None, err_stream=None):
    if out_stream is None:
        out_stream = sys.stdout
    if err_stream is None:
        err_stream = sys.stderr
    
    colwidths = tuple(max(len(row[col]) for row in (titles,) + data) for col in range(len(titles)))
    rowwidth = sum(colwidths) + len(colwidths) - 1
    sys.stderr.write('|'.join(title.ljust(colwidths[col]) for col, title in enumerate(titles)))
    sys.stderr.write('\n')
    sys.stderr.write('+'.join('-' * width for width in colwidths))
    sys.stderr.write('\n')
    sys.stderr.flush()
    for row in data:
        for col, coldata in enumerate(row):
            assert len(coldata) <= colwidths[col]
            not_last = col < len(colwidths) - 1
            sys.stdout.write(coldata)
            if not_last:
                sys.stdout.write(', ')
            sys.stdout.flush()
            if not_last:
                sys.stderr.write('\b\b')
                sys.stderr.write(' ' * (colwidths[col] - len(coldata)))
                sys.stderr.write('|')
                sys.stderr.flush()
        sys.stdout.write('\n')
        sys.stdout.flush()
