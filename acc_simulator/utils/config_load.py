def convert_str_na_to_none(d):
    """
    Since toml does not support None, we use "NA" to represent None.
    """
    if isinstance(d, dict):
        for k, v in d.items():
            d[k] = convert_str_na_to_none(v)
    elif isinstance(d, list):
        d = [convert_str_na_to_none(v) for v in d]
    elif isinstance(d, tuple):
        d = tuple(convert_str_na_to_none(v) for v in d)
    else:
        if d == "NA":
            return None
        else:
            return d
    return d
