from random import randint
from typing import Hashable
from functools import lru_cache
from itertools import islice, tee

from bs4 import BeautifulSoup
from unidecode import unidecode

NEWLINE = '__NEWLINE__'


@lru_cache(maxsize=1024)
def get_words(path, **kwargs):
    """Given a file path return a list of strings from that file"""
    with get_file_handler(path, **kwargs) as f:
        if kwargs['xml_base_tag']:
            soup = get_soup(f, **kwargs)
            f = soup.get_text() if soup else ''
        else:
            f = f.read()
    # optionally remove diacritics
    if kwargs['strip_diacritics'] and not kwargs.get('display', False):
        f = unidecode(f)
    # optionally format the list of words for display in the web viewer
    if kwargs.get('display', False):
        lines = f.replace('\n', ' ' + NEWLINE + ' ').split()
        formatted = []
        for idx, i in enumerate(lines):
            if i == NEWLINE:
                # prevent more than two consecutive brs
                if formatted and not formatted[-1].endswith('<br/><br/>'):
                    formatted[-1] += '<br/>'
            else:
                formatted.append(i)
        return formatted
    else:
        return f.split()


def get_file_handler(path, **kwargs):
    """Given the path to a file return a _io.TextIOWrapper object in 'r' mode"""
    return open(path, encoding=kwargs['encoding'])


def get_soup(f, **kwargs):
    """Return a soup object given a _io.TextIOWrapper object"""
    soup = BeautifulSoup(f, 'html.parser').find(kwargs['xml_base_tag'].lower())
    if not soup:
        print('WARNING: No XML content was found at tag', kwargs['xml_base_tag'].lower(), f.name)
        return ''
    # remove any specified xml tags
    if kwargs.get('xml_remove_tags'):
        for i in kwargs['xml_remove_tags']:
            for t in soup.find_all(i.lower()):
                t.extract()
    return soup


def ngrams(it, n):
    return zip(*(islice(it, i, None) for i, it in enumerate(tee(it, n))))


@lru_cache(maxsize=1024)
def get_windows(path, **kwargs):
    """Given a file path return a list of strings from that file"""
    words = get_words(path, **kwargs)
    buff = []
    for idx, window in enumerate(ngrams(words, kwargs['window_length'])):
        if idx % kwargs['slide_length'] != 0:
            continue
        buff.append(' '.join(window))
    return buff


@lru_cache(maxsize=1024)
def get_window_map(path, **kwargs):
    """Get a mapping from window id to window metadata, including page id"""
    xml_page_tag = kwargs.get('xml_page_tag')
    xml_page_attr = kwargs.get('xml_page_attr')
    if not xml_page_tag:
        return
    xml_page_tag = xml_page_tag.lower()
    xml_page_attr = xml_page_attr.lower() if xml_page_attr else None
    # read the text document
    with get_file_handler(path, **kwargs) as f:
        f = f.read().lower()
    # split on page breaks using string operations
    pagebreak = '{}_$PB$_{}'.format(randint(0, 2 ** 32), randint(0, 2 ** 32)).lower()
    f = f.replace('<{} '.format(xml_page_tag), pagebreak)
    f = f.replace('<{}/>'.format(xml_page_tag), pagebreak)
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
            if word_index and (word_index % kwargs['slide_length'] == 0):
                window_id += 1
            d[window_id] = page_id
    return d


def get_cacheable(*args):
    """Given a dictionary of kwargs return a dictionary with cacheable values retained"""
    kwargs = args[0]
    if len(args) > 1:
        for i in args[1:]:
            kwargs.update(i)
    return {k: kwargs[k] for k in kwargs if isinstance(kwargs[k], Hashable)}
