illegal = {
        ord(' '): '20',
        ord('"'): '22',
        ord('%'): '25',
        ord('&'): '26',
        ord('\''): '27',
        ord('*'): '2A',
        ord('+'): '2B',
        ord(','): '2C',
        ord('-'): '2D',
        ord('/'): '2F',
        ord(';'): '3B',
        ord('<'): '3C',
        ord('='): '3D',
        ord('>'): '3E',
        ord('ˆ'): '5E',
        ord('|'): '7C'
    }

# Generate translate table to convert illegal chars to corresponding HTML encoding
illegal_trans = str.maketrans(
        {c: '&#x' + illegal[c] + ';' for c in illegal}
    )


# Encode strings returned in a query (list of dicts)
def encode_qry(query):
    for q in query:
        q.update((k, encode(v)) for k, v in q.items())
    return query


# HTML encode dangerous chars in a string
def encode(string):
    if isinstance(string, str):
        return string.translate(illegal_trans)
    else:
        return string;


# TODO: Tests