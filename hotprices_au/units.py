import re


global_units = {
    "ea": {'unit': 'ea', 'factor': 1},
    "each": {'unit': 'ea', 'factor': 1},
    "pack": {'unit': 'ea', 'factor': 1},
    "pk": {'unit': 'ea', 'factor': 1},
    "bunch": {'unit': 'ea', 'factor': 1},
    "sheets": {'unit': 'ea', 'factor': 1},
    "sachets": {'unit': 'ea', 'factor': 1},
    "capsules": {'unit': 'ea', 'factor': 1},
    "ss": {'unit': 'ea', 'factor': 1},  # No idea what this is, related to face masks?
    "set": {'unit': 'ea', 'factor': 1},
    "pair": {'unit': 'ea', 'factor': 1},  # Yes I know it should be 2, but for pairs 1 makes more sense
    "pairs": {'unit': 'ea', 'factor': 1},  # Yes I know it should be 2, but for pairs 1 makes more sense
    "piece": {'unit': 'ea', 'factor': 1},
    "tablets": {'unit': 'ea', 'factor': 1},
    "rolls": {'unit': 'ea', 'factor': 1},
    "dozen": {'unit': 'ea', 'factor': 12},
    'mg': {'unit': 'g', 'factor': 0.001},
    'g': {'unit': 'g', 'factor': 1},
    'kg': {'unit': 'g', 'factor': 1000},
    'ml': {'unit': 'ml', 'factor': 1},
    'l': {'unit': 'ml', 'factor': 1000},
    'm': {'unit': 'cm', 'factor': 100},
    'metre': {'unit': 'cm', 'factor': 100},
    'cm': {'unit': 'cm', 'factor': 1},
}

def parse_str_unit(unit_str):
    unit_str = unit_str.lower()
    match unit_str:
        case "whole each": return 1, "ea"
        case "half each": return 0.5, "ea"
        case "each": return 1, "ea"
        # Handle this stupid case separately
        case "355ml xcase": return 8520, "ml"

    if unit_str.startswith("per "):
        unit_str = unit_str[4:]

    # Regex for 30 x 375ml
    # And the stupid 4x4x375mL ...
    re_multiple_first = r'^(?P<count>[0-9x]+)? ?x ?(?P<quantity>[0-9]+) ?(?P<unit>[a-z]+) ?(case|carton|pack)?$'

    # Regex for 375ml x 30
    re_multiple_later = r'^(?P<quantity>[0-9]+)(?P<unit>[a-z]+) ?x ?(?P<count>[0-9]+)? ?(case|carton|pack)?$'

    # Regex for 100g Pack
    re_regular_pack = r'^(?P<quantity>[0-9\.]+)? ?(?P<unit>[a-z]+) ?(punnet|pack|each|set)?$'

    # Try each regex and pick first match
    all_regex = [
        re_multiple_first,
        re_multiple_later,
        re_regular_pack,
    ]
    for regex in all_regex:
        matched = re.match(regex, unit_str)
        if matched:
            try:
                count_group = matched.group('count')
                # We might match on 4x4 and not just 4, so we split by x, type case each and then multiply them
                if 'x' in count_group:
                    counts = count_group.split('x')
                else:
                    counts = [count_group]
                counts = [float(c) for c in counts]
                count = 1
                for count_elem in counts:
                    count *= count_elem
            except IndexError:
                count = 1

            try:
                quantity = float(matched.group('quantity'))
            except TypeError:
                quantity = 1

            unit = matched.group('unit')
            if unit not in global_units:
                # If it's not a valid unit we can't parse it
                continue

            quantity *= count
            return quantity, unit
    else:
        # No match
        raise RuntimeError("Can't parse")


def convert_unit(item):
    # Parse unit if necessary
    unit = item['unit'].lower()


    # Handle quantity if it's a string
    quantity = item['quantity']


    conv = global_units[unit]
    item['quantity'] = conv['factor'] * quantity
    item['unit'] = conv['unit']

    return item