from difflib import SequenceMatcher


def purge_string(input_string):
    d = ''.join(ch for ch in input_string if ch.isalnum() or ch == ' ')
    return d.lower()


def ratio_max_mach_built_in(a, b, min_len):
    """Built-in ratio algorithm"""
    s = SequenceMatcher(a=a, b=b)
    sim = s.ratio() * 100
    return sim


def ratio_max_mach(a, b, min_len):
    """An improved (?) version"""
    a = purge_string(a)
    b = purge_string(b)
    avg_len = (len(a) + len(b) / 2)
    equal = 0
    match_len = 100
    # i = 1
    while match_len > min_len:
        s = SequenceMatcher(a=a, b=b, autojunk=False)
        # print(f'Egyezési arány az {i}-edik körben: {s.ratio()}')
        # i += 1
        a_low, b_low, match_len = s.find_longest_match()
        equal += match_len
        # print(a[a_low:(a_low + match_len)])
        # Cut the matching part
        a = a[:a_low] + a[a_low + match_len:]
        b = b[:b_low] + b[b_low + match_len:]
    # print(equal, sum_len)
    return (equal / avg_len) * 100


def cut_a_word(string, direction):
    if ' ' in string:
        if direction == 'right':
            string = string.rstrip().rpartition(' ')[0]
        if direction == 'left':
            string = string.lstrip().partition(' ')[2]
    return string


def cut_edges(a, b, minlength):
    change = False
    a_rstrip = cut_a_word(a, "right")
    b_rstrip = cut_a_word(b, "right")
    a_lstrip = cut_a_word(a, "left")
    b_lstrip = cut_a_word(b, "left")

    if ratio_max_mach(a, b, minlength) < ratio_max_mach(a_rstrip, b, minlength):
        a = a_rstrip
        change = True
    if ratio_max_mach(a, b, minlength) < ratio_max_mach(b_rstrip, a, minlength):
        b = b_rstrip
        change = True
    if ratio_max_mach(a, b, minlength) < ratio_max_mach(a_lstrip, b, minlength):
        a = a_lstrip
        change = True
    if ratio_max_mach(a, b, minlength) < ratio_max_mach(b_lstrip, a, minlength):
        b = b_lstrip
        change = True

    return a, b, change


if __name__ == '__main__':

    x = ' ajtón átverekedtük magunkat. A fürdőszobáét meglengettem, ahogy egy könyvet lapoznék. Lábujjhegyen ' \
        '(tipegve) becserkésztük apámat, akinek fehér teste, mint színehagyott moszat lebegett a kádban. A test ' \
        'körvonalai meglazultak: gyanús átmenetek képződtek egyik-másik vízhullámmal; igaz, az a néhány kemény ' \
        'kontúr a fej környékén sem volt biztatóbb. Azt természetesen azért nem gondolhattuk, hogy egyszerre csak ' \
        'föloldódik az édesapám a fürdővízben. A nyakával egy szinten, a dereka vonalában deszkahíd ívelt a kád ' \
        'fölé. Valahonnét, sok ütközés után, egy marék napfény került ide, s tette láthatóvá – a porszemek által – a ' \
        'levegőt. Fancsikó ripacskodott a porszemeken ugrálva. '
    y = 'De aztán Marci úr meglengeti a fürdőszoba ajtót, ahogy egy könyvet lapozna (kettőt!), lábujjhegyen – ' \
        'tipegve – becserkészi a mesterrel közös apját, akinek fehér teste, mint színehagyott moszat lebeg a kádban. ' \
        'A test körvonalai meglazultak: gyanús átmenetek képződtek egyik-másik vízhullámmal; igaz, az a néhány kemény ' \
        'kontúr a fej környékén sem biztatóbb. Azt azért nem gondolhatják, hogy egyszerre csak feloldódik az apjuk a ' \
        'fürdővízben. A nyakával egy szinten, a derék vonalában deszkahíd ível a kád fölé. Valahonnét, sok ütközés ' \
        'után, marék napfény kerül ide; s teszi láthatóvá – a porszemek által – a levegőt. A porszemeken senki. ' \
        '(„Kell? nem kell!”) Jobb kézről, két'

    changed = True
    while changed:
        (x, y, changed) = cut_edges(x, y, 5)

    print(x, y, sep='\n')

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
