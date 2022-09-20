import json
from pathlib import Path
from shutil import rmtree
from collections import defaultdict


# Only this function is public in this file!
def create_all_match_json(kwargs):
    """Create the output JSON to be consumed by the web client"""
    # combine all the matches in each match directory into a composite match file
    guid_to_int = defaultdict(lambda: len(guid_to_int))
    for match_directory in (kwargs['output'] / 'api' / 'matches').glob('*'):
        # buff contains the flat list of matches for a single input file
        buff = []
        for match_pair_json in match_directory.glob('*.json'):
            with open(match_pair_json) as fh:
                buff += json.load(fh)
        for i in buff:
            i['_id'] = guid_to_int[i['_id']]
        with open(f'{match_directory}.json', 'w') as out:
            json.dump(buff, out)
        rmtree(match_directory)

    # create minimal representations of all matches to be sorted by each sort heuristic below
    buff = set()
    for file_id, matches in stream_match_lists(kwargs):
        for match_idx, match in enumerate(matches):
            if int(file_id) == int(match.get('source_file_id')):
                buff.add((match_idx,
                          match.get('source_file_id'),
                          match.get('target_file_id'),
                          min(len(match.get('source_segment_ids')), len(match.get('target_segment_ids'))),
                          match.get('probability'),
                          match.get('similarity', ''),
                          match.get('source_author' ''),
                          match.get('source_title', ''),
                          match.get('source_year', ''),
                          ))

    # create and store the file_id.match_index indices for each sort heuristic
    buff = list(buff)
    for label, idx in (['length', -6],
                       ['probability', -5],
                       ['similarity', -4],
                       ['author', -3],
                       ['title', -2],
                       ['year', -1],
                       ):
        # only process the probability measures if they're present
        if label == 'probability' and not kwargs.get('compute_probabilities'):
            continue
        # reverse certain sort orders to proceed max to min
        inverse = label in {'similarity', 'length', 'probability'}
        sorted_list = sorted(buff, key=lambda x: x[idx], reverse=inverse)
        ids = [conv_to_ints(i[:6]) for i in sorted_list]
        with open(kwargs['output'] / 'api' / 'indices' / f'match-ids-by-{label}.json', 'w') as out:
            json.dump(ids, out)

    # create the scatterplot data
    write_scatterplots(kwargs)


def write_scatterplots(kwargs):
    """Write the scatterplot JSON"""
    out_dir = kwargs['output'] / 'api' / 'scatterplots'
    for i in ('source', 'target'):
        for j in ('segment_ids', 'file_id', 'author'):
            for k in ('sum', 'mean'):
                data_nest = defaultdict(list)
                for file_id, matches in stream_match_lists(kwargs):
                    for match in matches:
                        if j == 'segment_ids':
                            level = f'{i}.{match[f"{i}_file_id"]}.'
                            level += '.'.join(str(m) for m in match[f'{i}_segment_ids'])
                        else:
                            level = match[f'{i}_{j}']
                        # ensure the level (aka data key) is a string
                        if isinstance(level, list):
                            level = '.'.join(str(i) for i in level)
                        data_nest[level].append(match)
                # format the scatterplot data
                scatterplot_data = []
                for level in data_nest:
                    sims = [o['similarity'] for o in data_nest[level]]
                    sim = sum(sims) if k == 'sum' else sum(sims) / len(sims)
                    o = data_nest[level][0]
                    scatterplot_data.append({
                        'type': i,
                        'unit': j,
                        'statistic': k,
                        'key': level,
                        'similarity': sim,
                        'title': o[i + '_title'],
                        'author': o[i + '_author'],
                        'match': o[i + '_match'],
                        'source_year': o['source_year'],
                        'target_year': o['target_year'],
                    })
                # write the scatterplot data
                with open(Path(out_dir) / f'{i}-{j}-{k}.json', 'w') as out:
                    json.dump(scatterplot_data, out)


def stream_match_lists(kwargs):
    """Stream a stream of (file_id, [match, match, ...]) objects"""
    for json_file in (kwargs['output'] / 'api' / 'matches').glob('*.json'):
        file_id = json_file.stem
        with open(json_file) as f:
            match_list = json.load(f)
        yield file_id, match_list


def conv_to_ints(elems):
    ret = []
    for k in elems:
        try:
            ret.append(int(k))
        except (ValueError, TypeError):
            ret.append(k)
    return ret
