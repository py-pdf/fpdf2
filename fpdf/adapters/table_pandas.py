def format_dataframe(df, include_index: bool = True):
    """Fully formats a Pandas dataframe for conversion into pdf"""
    data = df.map(str).values
    columns = df.columns
    indexes = df.index
    table_data = add_labels_to_data(data, indexes, columns, include_index=include_index)
    return table_data


def add_labels_to_data(data, indexes, columns, include_index: bool = True, char=" "):
    """Combines index and column labels with data for table output"""
    if include_index:
        index_header_padding = [tuple(char) * len(indexes[0])] * len(columns[0])
        formatted_indexes = format_label_tuples(indexes)
        new_values = []
        for i, v in zip(formatted_indexes, data):
            new_values.append(list(i) + list(v))
        formatted_columns = [
            list(c)
            for c in zip(*format_label_tuples(index_header_padding + list(columns)))
        ]
        new_data = formatted_columns + new_values

    else:
        formatted_columns = [list(c) for c in zip(*format_label_tuples(list(columns)))]
        new_data = formatted_columns + data.tolist()

    return new_data


def format_label_tuples(lbl, char=" "):
    """
    Formats columns and indexes to match DataFrame formatting.
    """
    indexes = [lbl[0]]
    for i, j in zip(lbl, lbl[1:]):
        next_label = []
        for i_, j_ in zip(i, j):
            if j_ == i_:
                next_label.append(char)
            else:
                next_label.append(j_)
        indexes.append(tuple(next_label))
    return indexes
