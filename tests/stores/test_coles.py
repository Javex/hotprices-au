from hotprices_au.sites import coles

def get_item(ofMeasureUnits=None, quantity=None, isWeighted=True, pricing=True, size=None, **kwargs):
    defaults = {
        '_type': 'PRODUCT',
        'id': '1',
        'name': 'test',
        'description': 'test desc',
        'pricing': {
            'now': 10,
            'unit': {
                'isWeighted': isWeighted,
            },
        },
    }
    if isWeighted is None:
        del defaults['pricing']['unit']['isWeighted']
    else:
        defaults['pricing']['unit']['isWeighted'] = isWeighted

    if ofMeasureUnits is not None:
        defaults['pricing']['unit']['ofMeasureUnits'] = ofMeasureUnits

    if quantity is not None:
        defaults['pricing']['unit']['quantity'] = quantity

    if size is not None:
        defaults['size'] = size

    if pricing is None:
        defaults['pricing'] = None
    defaults.update(kwargs)
    item = defaults
    return item


def test_get_canonical():
    today = '2023-09-29'
    item = get_item(_type='SINGLE_TILE', adId='foo')
    can_item = coles.get_canonical(item, today)
    assert can_item is None

    item = get_item(pricing=None)
    can_item = coles.get_canonical(item, today)
    assert can_item is None

    item = get_item(ofMeasureUnits='kg', quantity=1.4)
    can_item = coles.get_canonical(item, today)
    assert can_item['unit'] == 'g'
    assert can_item['quantity'] == 1400
    assert can_item['isWeighted']

    item = get_item(ofMeasureUnits='ea', quantity=1.4, isWeighted=None)
    can_item = coles.get_canonical(item, today)
    assert can_item['unit'] == 'ea'
    assert can_item['quantity'] == 1.4
    assert not can_item['isWeighted']

    item = get_item(quantity=1, isWeighted=False, size='38g')
    can_item = coles.get_canonical(item, today)
    assert can_item['unit'] == 'g'
    assert can_item['quantity'] == 38
    assert not can_item['isWeighted']

    item = get_item(quantity=1, isWeighted=False, size='1 set')
    can_item = coles.get_canonical(item, today)
    assert can_item['unit'] == 'ea'
    assert can_item['quantity'] == 1
    assert not can_item['isWeighted']

    item = get_item(quantity=1, isWeighted=False, size='1 pair')
    can_item = coles.get_canonical(item, today)
    assert can_item['unit'] == 'ea'
    assert can_item['quantity'] == 1
    assert not can_item['isWeighted']

    item = get_item(quantity=1, isWeighted=False, size='16 piece')
    can_item = coles.get_canonical(item, today)
    assert can_item['unit'] == 'ea'
    assert can_item['quantity'] == 16
    assert not can_item['isWeighted']

    item = get_item(description='BEER CAN 375ML:PACK6', quantity=0, isWeighted=False, size='')
    can_item = coles.get_canonical(item, today)
    assert can_item['unit'] == 'ml'
    assert can_item['quantity'] == 2250
    assert not can_item['isWeighted']


if __name__ == '__main__':
    test_get_canonical()