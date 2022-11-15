from difflib import SequenceMatcher
import re
import string


def purge_string(str):
    d = ''.join(ch for ch in str if ch.isalnum() or ch == " ")
    return d.lower()


def ratio_del_ins(a, b):
    equal_len = 0
    del_set = set()
    ins_set = set()
    s = SequenceMatcher(a=a, b=b, autojunk=False)
    max_mach = s.find_longest_match()
    print(a[max_mach[0]:(max_mach[0] + max_mach[2])], s.ratio())
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == "equal":
            equal_len += i2 - i1
        if tag == "delete":
            del_set.add(a[i1:i2])
        if tag == "insert":
            ins_set.add(b[j1:j2])
        print('{:7}   a[{}:{}] --> b[{}:{}] {!r:>8} --> {!r}'.format(
                tag, i1, i2, j1, j2, a[i1:i2], b[j1:j2]))
    print(equal_len / (len(a + b) / 2))
    del_ins_len = len("".join(item for item in del_set.intersection(ins_set)))
    print((equal_len + del_ins_len) / ((len(a + b) / 2)))


def ratio_max_mach(a, b):
    a = purge_string(a)
    b = purge_string(b)
    sum_len = len(a + b)
    equal = 0
    max_length = 6
    # i = 1
    while max_length > 5:
        s = SequenceMatcher(a=a, b=b, autojunk=False)
        # print(f"Egyezési arány az {i}-edik körben: {s.ratio()}")
        # i += 1
        max_mach = s.find_longest_match()
        equal += max_mach[2]
        # print(a[max_mach[0]:(max_mach[0] + max_mach[2])])
        a = a[:max_mach[0]] + a[(max_mach[0] + max_mach[2]):]
        b = b[:max_mach[1]] + b[(max_mach[1] + max_mach[2]):]
        max_length = max_mach[2]
    # print(equal, sum_len)
    return equal / (sum_len / 2)


def cut_a_word(string, direction):
    if " " in string:
        if direction == "right":
            string = string.rstrip().rpartition(" ")[0]
        if direction == "left":
            string = string.lstrip().partition(" ")[2]
    return string


x = " mindenki fülébe a harang szava.(isa, por) Minden csillogott-villogott, csak a por nem. Az egyenruhás alakok szájából nagy, kacskaringós, sárga csövek nőttek ki, amik azután kiszélesedtek (mintegy kihajoltak önmagukból), akár a tökvirág. – Fúvós hangszer – biccentett Fancsikó. A tanácsháza előtt "
y = " barnásodás” se! És, pardőz, az illat, az se.) Minden csillogott-villogott, csak a por nem. Az egyenruhás alakok szájából nagy, kacskaringós sárga csövek nőttek ki, amik aztán kiszélesedtek (mintegy kihajoltak önmagukból), akár a tökvirág. „Mjuzik” – mondta a mester édesapja fenyegetően. A sor "

cut_more = True
while cut_more:
    if ratio_max_mach(x, y) > ratio_max_mach(cut_a_word(x, "left"), y):
        cut_more = False
    else:
        x = cut_a_word(x, "left")
        print(x)


# x = purge_string(x)
# y = purge_string(y)

# print ("Módosított arány:", ratio_max_mach(x, y))


"""------------------------------------"""
"""for i in range(len(x_list)):
    x = str(x_list[0:-i])
    s = SequenceMatcher(a=x, b=y, autojunk=False)
    print(x, y, s.ratio())
    y = str(y_list[0:-i])
    s = SequenceMatcher(a=x, b=y, autojunk=False)
    print(x, y, s.ratio())"""

