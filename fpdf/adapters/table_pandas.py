from pandas import MultiIndex
from fpdf import FPDF


class FPDF_pandas(FPDF):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def dataframe(self, df, **kwargs):
        with self.table(
            num_index_columns=df.index.nlevels,
            num_heading_rows=df.columns.nlevels,
            **kwargs
        ) as table:
            TABLE_DATA = format_df(df)
            for data_row in TABLE_DATA:
                row = table.row()
                for datum in data_row:
                    row.cell(datum)


def format_df(df, char: str = " ", convert_to_string: bool = True) -> list:
    data = df.map(str).values.tolist()
    if isinstance(df.columns, MultiIndex):
        heading = [list(c) for c in zip(*df.columns)]
    else:
        heading = df.columns.values.reshape(1, len(df.columns)).tolist()

    if isinstance(df.index, MultiIndex):
        index = [list(c) for c in df.index]
    else:
        index = df.index.values.reshape(len(df), 1).tolist()
    padding = [list(char) * df.index.nlevels] * df.columns.nlevels

    output = [i + j for i, j in zip(padding + index, heading + data)]
    if convert_to_string:
        output = [[str(d) for d in row] for row in output]
    return output
