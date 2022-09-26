import json
from pathlib import Path
from shutil import rmtree
from collections import defaultdict


# Only this function is public in this file!
def create_all_match_json(output, compute_probabilities):
    """Create the output JSON to be consumed by the web client"""
    # combine all the matches in each match directory into a composite match file
    guid_to_int = defaultdict(lambda: len(guid_to_int))  # 0, 1, 2, 3, etc. in access order
    for match_directory in (output / 'api' / 'matches').glob('*'):
        # buff contains the flat list of matches for a single input file
        match_pairs = []
        for match_pair_json in match_directory.glob('*.json'):
            with open(match_pair_json, encoding='UTF-8') as fh:
                json_match_pairs = json.load(fh)
            for match in json_match_pairs:
                match['_id'] = guid_to_int[match['_id']]
                match_pairs.append(match)
        with open(f'{match_directory}.json', 'w', encoding='UTF-8') as out:
            json.dump(match_pairs, out, ensure_ascii=False)
        rmtree(match_directory)

    # create minimal representations of all matches to be sorted by each sort heuristic below
    buff = set()
    for file_id, matches in stream_match_lists(output):
        for match_idx, match in enumerate(matches):
            if file_id == match.get('source_file_id'):
                buff.add((match_idx,
                          match['source_file_id'],
                          match['target_file_id'],
                          min(len(match['source_segment_ids']), len(match['target_segment_ids'])),
                          match['probability'],
                          match['similarity'],
                          match['source_author'],
                          match['source_title'],
                          # only year can by empty
                          match.get('source_year', ''),
                          ))

    # create and store the file_id.match_index indices for each sort heuristic
    # 3: length, 4: probability, 5: similarity, 6: author, 7: title, 8: year,
    # 1: source_file_id, 2: target_file_id, 0: match idx
    sort_heuristic = [('length', True, lambda x: (x[3], x[4], x[5], x[6], x[7], x[8], x[1], x[2], x[0])),
                      ('probability', True, lambda x: (x[4], x[3], x[5], x[6], x[7], x[8], x[1], x[2], x[0])),
                      ('similarity', True, lambda x: (x[5], x[3], x[4], x[6], x[7], x[8], x[1], x[2], x[0])),
                      ('author', False, lambda x: (x[6], x[3], x[4], x[5], x[7], x[8], x[1], x[2], x[0])),
                      ('title', False, lambda x: (x[7], x[3], x[4], x[5], x[6], x[8], x[1], x[2], x[0])),
                      ('year', False, lambda x: (x[8], x[3], x[4], x[5], x[6], x[7], x[1], x[2], x[0])),
                      ]
    if not compute_probabilities:
        sort_heuristic.pop(1)  # only process the probability measures if they're present
    for label, inverse, key in sort_heuristic:
        # reverse certain sort orders to proceed max to min
        sorted_list = sorted(buff, key=key, reverse=inverse)
        ids = [i[:6] for i in sorted_list]
        with open(output / 'api' / 'indices' / f'match-ids-by-{label}.json', 'w', encoding='UTF-8') as out:
            json.dump(ids, out, ensure_ascii=False)

    # create the scatterplot data
    write_scatterplots(output)


def write_scatterplots(output):
    """Write the scatterplot JSON"""
    out_dir = output / 'api' / 'scatterplots'
    for i in ('source', 'target'):
        for j in ('segment_ids', 'file_id', 'author'):
            for k in ('sum', 'mean'):
                data_nest = defaultdict(list)
                for file_id, matches in stream_match_lists(output):
                    for match in matches:
                        if j == 'segment_ids':
                            level = f'{i}.{match[f"{i}_file_id"]}.{".".join(str(m) for m in match[f"{i}_segment_ids"])}'
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
                    if k == 'sum':
                        sim = sum(sims)
                    else:
                        sim = sum(sims) / len(sims)
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
                with open(Path(out_dir) / f'{i}-{j}-{k}.json', 'w', encoding='UTF-8') as out:
                    json.dump(scatterplot_data, out, ensure_ascii=False)


def stream_match_lists(output):
    """Stream a stream of (file_id, [match, match, ...]) objects"""
    for json_file in (output / 'api' / 'matches').glob('*.json'):
        with open(json_file, encoding='UTF-8') as f:
            match_list = json.load(f)
        yield int(json_file.stem), match_list
