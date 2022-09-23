import numpy as np
from vminhash import VectorizedMinHash, byte_hashes

from utils import get_windows, ngrams, parallel_map


# Only this function is public in this file!
def get_all_hashbands(infiles, cache_location, strip_diacritics, window_length, slide_length, chargram_length,
                      hashband_length, hashband_step, cache_db):
    """Generate and save hashbands for each infile"""
    hasher = VectorizedMinHash(n_perm=256)
    buff = [(idx, file_path, cache_location / 'minhashes' / (str(file_path).replace('/', '___') + '.npy'))
            for idx, file_path in enumerate(infiles)]
    parallel_map(get_file_hashbands, buff, hasher=hasher, strip_diacritics=strip_diacritics,
                 window_length=window_length, slide_length=slide_length, chargram_length=chargram_length,
                 hashband_length=hashband_length, hashband_step=hashband_step, cache_db=cache_db)


def get_file_hashbands(args, hasher, strip_diacritics, window_length, slide_length, chargram_length, hashband_length,
                       hashband_step, cache_db):
    """Minhash a file and save [[hashband, file_idx, window_idx]]"""
    file_idx, file_path, minhash_path = args
    minhashes = get_file_minhashes(file_path, minhash_path, hasher, strip_diacritics, window_length, slide_length,
                                   chargram_length)
    # get the hashbands for this minhash
    hashbands = set()
    for window_idx, minhash in enumerate(minhashes):
        for hdx, h in enumerate(ngrams(minhash, hashband_length)):
            if hdx % hashband_step == 0:
                hashbands.add(('.'.join(str(i) for i in h), file_idx, window_idx))
    if hashbands:
        cache_db.write_hashbands(hashbands)


def get_file_minhashes(file_path, minhash_path, hasher, strip_diacritics, window_length, slide_length, chargram_length):
    """Return the minhash array for a file"""
    if minhash_path.exists():
        print(' * loading', file_path, 'minhashes from cache')
        return np.load(minhash_path)
    # run minhash algorithm on file
    buff = []
    for window_idx, window in enumerate(get_windows(file_path, strip_diacritics, window_length, slide_length)):
        char_hashes = byte_hashes(window.lower().encode('UTF-8'), n=chargram_length)
        fingerprint = hasher.fingerprint(char_hashes)
        buff.append(fingerprint)
    minhashes = np.array(buff)
    np.save(minhash_path, minhashes)
    return minhashes
