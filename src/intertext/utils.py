from random import randint
from typing import Hashable
from multiprocessing import Pool
from itertools import islice, tee, chain
from functools import lru_cache, partial


from bs4 import BeautifulSoup
from unidecode import unidecode


@lru_cache(maxsize=1024)
def get_words(path, encoding, xml_base_tag, xml_remove_tags, strip_diacritics, display):
    """Given a file path return a list of strings from that file"""

    with open(path, encoding=encoding) as f:
        if xml_base_tag:
            f = get_soup_text(f, xml_base_tag, xml_remove_tags)
        else:
            f = f.read()
    # optionally remove diacritics
    if strip_diacritics and not display:
        f = unidecode(f)
    # optionally format the list of words for display in the web viewer
    if display:
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
    else:
        return f.split()


def get_soup_text(f, xml_base_tag, xml_remove_tags):
    """Return a soup object given a _io.TextIOWrapper object"""
    soup = BeautifulSoup(f, 'html.parser').find(xml_base_tag.lower())
    if not soup:
        print('WARNING: No XML content was found at tag', xml_base_tag.lower(), f.name)
        return ''
    # remove any specified xml tags
    for i in xml_remove_tags:
        for t in soup.find_all(i.lower()):
            t.extract()

    return soup.get_text() if soup else ''


def ngrams(it, n):
    return zip(*(islice(it, i, None) for i, it in enumerate(tee(it, n))))


def chunked_iterator(iterable, n):
    # Original source:
    # https://stackoverflow.com/questions/8991506/iterate-an-iterator-by-chunks-of-n-in-python/29524877#29524877
    it = iter(iterable)
    try:
        while True:
            yield chain((next(it),), islice(it, n-1))
    except StopIteration:
        return


@lru_cache(maxsize=1024)
def get_windows(path, encoding, xml_base_tag, xml_remove_tags, strip_diacritics, display, window_length, slide_length):
    """Given a file path return a list of strings from that file"""
    words = get_words(path, encoding, xml_base_tag, xml_remove_tags, strip_diacritics, display, )
    buff = []
    for idx, window in enumerate(ngrams(words, window_length)):
        if idx % slide_length == 0:
            buff.append(' '.join(window))
    return buff


@lru_cache(maxsize=1024)
def get_window_map(path, xml_page_tag, xml_page_attr, encoding, slide_length):
    """Get a mapping from window id to window metadata, including page id"""
    if not xml_page_tag:
        return
    xml_page_tag = xml_page_tag.lower()
    xml_page_attr = xml_page_attr.lower() if xml_page_attr else None
    # read the text document
    with open(path, encoding=encoding) as f:
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
