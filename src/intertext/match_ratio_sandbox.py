from difflib import SequenceMatcher


def purge_string(input_string):
    d = ''.join(ch for ch in input_string if ch.isalnum() or ch == ' ')
    return d.lower()


def ratio_del_ins(a, b):
    equal_len = 0
    del_set = set()
    ins_set = set()
    s = SequenceMatcher(a=a, b=b, autojunk=False)
    max_mach = s.find_longest_match()
    a_low = max_mach[0]
    match_size = max_mach[2]
    print(a[a_low:a_low + match_size], s.ratio())
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'equal':
            equal_len += i2 - i1
        if tag == 'delete':
            del_set.add(a[i1:i2])
        if tag == 'insert':
            ins_set.add(b[j1:j2])
        print(f'{tag:7}   a[{i1}:{i2}] --> b[{j1}:{j2}] {repr(a[i1:i2]):>8} --> {repr(b[j1:j2])}')
    avg_len = len(a) + len(b) / 2
    print(equal_len / avg_len)
    del_ins_len = len(''.join(item for item in del_set.intersection(ins_set)))
    print((equal_len + del_ins_len) / avg_len)


def ratio_max_mach_built_in(a, b):
    """Built-in ratio algorithm"""
    s = SequenceMatcher(a=a, b=b)
    sim = s.ratio() * 100
    return sim


def ratio_max_mach(a, b):
    """An improved (?) version"""
    a = purge_string(a)
    b = purge_string(b)
    avg_len = (len(a) + len(b) / 2)
    equal = 0
    match_size = 6
    # i = 1
    while match_size > 5:
        s = SequenceMatcher(a=a, b=b, autojunk=False)
        # print(f'Egyezési arány az {i}-edik körben: {s.ratio()}')
        # i += 1
        a_low, b_low, match_size = s.find_longest_match()
        equal += match_size[2]
        # print(a[a_low:(a_low + match_size)])
        # Cut the matching part
        a = a[:a_low] + a[a_low + match_size:]
        b = b[:b_low] + b[b_low + match_size:]
    # print(equal, sum_len)
    return (equal / avg_len) * 100


def cut_a_word(string, direction):
    if ' ' in string:
        if direction == 'right':
            string = string.rstrip().rpartition(' ')[0]
        if direction == 'left':
            string = string.lstrip().partition(' ')[2]
    return string


if __name__ == '__main__':

    x = ' mindenki fülébe a harang szava.(isa, por) Minden csillogott-villogott, csak a por nem. Az egyenruhás ' \
        'alakok szájából nagy, kacskaringós, sárga csövek nőttek ki, amik azután kiszélesedtek (mintegy kihajoltak ' \
        'önmagukból), akár a tökvirág. – Fúvós hangszer – biccentett Fancsikó. A tanácsháza előtt '
    y = ' barnásodás” se! És, pardőz, az illat, az se.) Minden csillogott-villogott, csak a por nem. Az egyenruhás ' \
        'alakok szájából nagy, kacskaringós sárga csövek nőttek ki, amik aztán kiszélesedtek (mintegy kihajoltak ' \
        'önmagukból), akár a tökvirág. „Mjuzik” – mondta a mester édesapja fenyegetően. A sor '

    while ratio_max_mach(x, y) <= ratio_max_mach(cut_a_word(x, 'left'), y):
        x = cut_a_word(x, 'left')
        print(x)

    # x = purge_string(x)
    # y = purge_string(y)

    # print ('Módosított arány:', ratio_max_mach(x, y))

    # -----------------------------------------------
    """for i in range(len(x_list)):
        x = str(x_list[0:-i])
        s = SequenceMatcher(a=x, b=y, autojunk=False)
        print(x, y, s.ratio())
        y = str(y_list[0:-i])
        s = SequenceMatcher(a=x, b=y, autojunk=False)
        print(x, y, s.ratio())"""
