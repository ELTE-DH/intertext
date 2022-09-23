from random import randint
from multiprocessing import Pool
from itertools import islice, tee
from functools import lru_cache, partial


from bs4 import BeautifulSoup
from unidecode import unidecode


def ngrams(it, n):
    return zip(*(islice(it, i, None) for i, it in enumerate(tee(it, n))))


@lru_cache(maxsize=1024)
def get_windows(path, strip_diacritics, window_length, slide_length):
    """Given a file path return a list of strings from that file"""
    words = get_words(path, strip_diacritics, False)
    buff = []
    for idx, window in enumerate(ngrams(words, window_length)):
        if idx % slide_length == 0:
            buff.append(' '.join(window))
    return buff


@lru_cache(maxsize=1024)
def get_words(path, strip_diacritics, display):
    """Given a file path return a list of strings from that file"""
    with open(path, encoding='UTF-8') as f:
        f = f.read()
    # optionally remove diacritics
    if strip_diacritics and not display:
        f = unidecode(f)
    if not display:
        return f.split()
    # optionally format the list of words for display in the web viewer
    else:
        lines = f.replace('\n', ' __NEWLINE__ ').split()
        formatted = []
        for idx, i in enumerate(lines):
            if i == '__NEWLINE__':
                # prevent more than two consecutive brs
                if formatted and not formatted[-1].endswith('<br/><br/>'):
                    formatted[-1] += '<br/>'
            else:
                formatted.append(i)
        return formatted


@lru_cache(maxsize=1024)
def get_window_map(path, xml_page_tag, xml_page_attr, slide_length):
    """Get a mapping from window id to window metadata, including page id"""
    xml_page_tag = xml_page_tag.lower()
    xml_page_attr = xml_page_attr.lower() if xml_page_attr else None
    # read the text document
    with open(path, encoding='UTF-8') as f:
        f = f.read().lower()
    # split on page breaks using string operations
    pagebreak = f'{randint(0, 2 ** 32)}_$PB$_{randint(0, 2 ** 32)}'.lower()
    f = f.replace(f'<{xml_page_tag} ', pagebreak)
    f = f.replace(f'<{xml_page_tag}/>', pagebreak)
    pages = f.split(pagebreak)
    # populate the mapping from window index to page id d[window_index] = {page_id, ...}
    d = {}
    window_id = 0
    # skip content leading up to first page
    for page_index, page in enumerate(pages[1:]):
        # handle case of page id specified in an attribute
        if xml_page_attr:
            tag = page.split('>')[0]
            page_id = tag.split('{}='.format(xml_page_attr))[1].split(' ')[0]
            page_id = page_id.replace('"', '').replace("'", '')
            page_id = page_id.rstrip('/>')
        # hande case of page id between tags
        elif '</' + xml_page_tag in page:
            page_id = page.split('</' + xml_page_tag)[0]
            if '>' in page_id:
                page_id = page_id.split('>')[1]
        # handle case of sequential pages without identification (self-closing tags)
        else:
            page_id = page_index
        # clean the page id
        page_id = str(page_id).strip()
        # remove the lead tag
        page = '>'.join(page.split('>')[1:])
        soup = BeautifulSoup(page, 'html.parser')
        text = soup.get_text() if soup else ''
        words = text.split()
        for word_index, word in enumerate(words):
            if word_index and (word_index % slide_length == 0):
                window_id += 1
            d[window_id] = page_id
    return d


def parallel_map(fun, buff, **kwargs):
    process_pool = Pool()
    f = partial(fun, **kwargs)
    for _ in process_pool.map(f, buff):
        pass
    process_pool.close()
    process_pool.join()
