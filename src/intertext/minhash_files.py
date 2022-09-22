import numpy as np
from vminhash import byte_hashes

from utils import get_windows, ngrams, parallel_map_new


# Only this function is public in this file!
def get_all_hashbands(infiles, cache_location, hasher, encoding, xml_base_tag, xml_remove_tags, strip_diacritics,
                      display, window_length, slide_length, chargram_length, hashband_length, hashband_step,
                      write_hashbands_fun):
    """Generate and save hashbands for each infile"""
    buff = [(idx, i) for idx, i in enumerate(infiles)]
    parallel_map_new(get_file_hashbands, buff, cache_location=cache_location,
                     hasher=hasher, encoding=encoding, xml_base_tag=xml_base_tag, xml_remove_tags=xml_remove_tags,
                     strip_diacritics=strip_diacritics, display=display, window_length=window_length,
                     slide_length=slide_length, chargram_length=chargram_length, hashband_length=hashband_length,
                     hashband_step=hashband_step, write_hashbands_fun=write_hashbands_fun)


def get_file_hashbands(args, cache_location, hasher, encoding, xml_base_tag, xml_remove_tags, strip_diacritics,
                       display, window_length, slide_length, chargram_length, hashband_length, hashband_step,
                       write_hashbands_fun):
    """Minhash a file and save [[hashband, file_idx, window_idx]]"""
    file_idx, file_path = args
    minhashes = get_file_minhashes(file_path, cache_location, hasher, encoding, xml_base_tag, xml_remove_tags,
                                   strip_diacritics, display, window_length, slide_length, chargram_length)
    # get the hashbands for this minhash
    hashbands = set()
    for window_idx, minhash in enumerate(minhashes):
        for hdx, h in enumerate(ngrams(minhash, hashband_length)):
            if hdx % hashband_step == 0:
                hashbands.add(('.'.join(str(i) for i in h), file_idx, window_idx))
    write_hashbands_fun(hashbands)


def get_file_minhashes(file_path, cache_location, hasher, encoding, xml_base_tag, xml_remove_tags, strip_diacritics,
                       display, window_length, slide_length, chargram_length):
    """Return the minhash array for a file"""
    minhash_path = cache_location / 'minhashes' / (str(file_path).replace('/', '___') + '.npy')
    if minhash_path.exists():
        print(' * loading', file_path, 'minhashes from cache')
        return np.load(minhash_path)
    # run minhash algorithm on file
    buff = []
    for window_idx, window in enumerate(get_windows(file_path, encoding, xml_base_tag, xml_remove_tags,
                                                    strip_diacritics, display, window_length, slide_length)):
        char_hashes = byte_hashes(window.lower().encode(encoding), n=chargram_length)
        fingerprint = hasher.fingerprint(char_hashes)
        buff.append(fingerprint)
    minhashes = np.array(buff)
    np.save(minhash_path, minhashes)
    return minhashes
