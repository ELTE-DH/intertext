import functools
import multiprocessing

import numpy as np
from vectorizedMinHash import fastNGramHashes

from config import CUDA_AVAILABLE, cache_location, hasher
from utils import get_windows, get_cacheable, ngrams
from db import write_hashbands


def get_all_hashbands(kwargs):
    """Generate and save hashbands for each infile"""
    pool = multiprocessing.Pool()
    buff = [[idx, i] for idx, i in enumerate(kwargs['infiles'])]
    f = functools.partial(get_file_hashbands, **kwargs)
    for _ in pool.map(f, buff):
        pass
    pool.close()
    pool.join()


def get_file_hashbands(args, **kwargs):
    """Minhash a file and save [[hashband, file_idx, window_idx]]"""
    file_idx, file_path = args
    minhashes = get_file_minhashes(file_path, **kwargs)
    # get the hashbands for this minhash
    hashbands = set()
    for window_idx, minhash in enumerate(minhashes):
        for hdx, h in enumerate(ngrams(minhash, kwargs['hashband_length'])):
            if hdx % kwargs['hashband_step'] == 0:
                hashbands.add(tuple(['.'.join([str(i) for i in h]), file_idx, window_idx]))
    write_hashbands(hashbands, **kwargs)


def get_file_minhashes(file_path, **kwargs):
    """Return the minhash array for a file"""
    minhash_path = cache_location / 'minhashes' / (str(file_path).replace('/', '___') + '.npy')
    if minhash_path.exists():
        print(' * loading', file_path, 'minhashes from cache')
        return np.load(minhash_path)
    # run minhash algorithm on file
    buff = []
    for window_idx, window in enumerate(get_windows(file_path, **get_cacheable(kwargs))):
        char_hashes = fastNGramHashes(window.lower().encode(kwargs['encoding']), n=kwargs['chargram_length'])
        fingerprint = hasher.fingerprint(char_hashes, cuda=CUDA_AVAILABLE)
        buff.append(fingerprint)
    minhashes = np.array(buff)
    np.save(minhash_path, minhashes)
    return minhashes
