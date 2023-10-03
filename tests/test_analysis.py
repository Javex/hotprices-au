from hotprices_au import analysis

def get_item(price=1, id='1'):
    item = {
        'store': 'foo',
        'id': id,
        'price': price,
        'priceHistory': [{
            'price': price,
        }],
    }
    return item

def test_merge_price_history():
    # Price changed
    old_items = [get_item()]
    new_items = [get_item(price=2)]
    items = analysis.merge_price_history(old_items, new_items)
    assert len(items) == 1
    item = items[0]
    assert item['price'] == 2
    assert len(item['priceHistory']) == 2
    assert item['priceHistory'][0]['price'] == 2
    assert item['priceHistory'][1]['price'] == 1

    # Price didn't change
    old_items = [get_item()]
    new_items = [get_item()]
    items = analysis.merge_price_history(old_items, new_items)
    assert len(items) == 1
    item = items[0]
    assert item['price'] == 1
    assert len(item['priceHistory']) == 1
    assert item['priceHistory'][0]['price'] == 1

    # No past history
    new_items = [get_item(price=2)]
    items = analysis.merge_price_history(None, new_items)
    assert len(items) == 1
    item = items[0]
    assert item['price'] == 2
    assert len(item['priceHistory']) == 1
    assert item['priceHistory'][0]['price'] == 2

    # Multiple products
    old_items = [get_item(price=3), get_item(id='2')]
    new_items = [get_item(price=2), get_item(id='2')]
    items = analysis.merge_price_history(old_items, new_items)
    assert len(items) == 2
    item = items[0]
    assert item['price'] == 2
    assert len(item['priceHistory']) == 2
    assert item['priceHistory'][0]['price'] == 2
    assert item['priceHistory'][1]['price'] == 3

    # Repeat run of history on same day
    old_items = [get_item()]
    new_items = [old_items[0]]
    items = analysis.merge_price_history(old_items, new_items)
    assert len(items) == 1
    item = items[0]
    assert len(item['priceHistory']) == 1

    # Prices with history don't get overwritten
    oldest_items = [get_item()]
    middle_items = [get_item(price=2)]
    newest_items = [get_item(price=2)]
    items = analysis.merge_price_history(oldest_items, middle_items)
    items = analysis.merge_price_history(items, newest_items)
    assert len(items) == 1
    item = items[0]
    assert len(item['priceHistory']) == 2
