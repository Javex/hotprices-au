const misc = require("../js/misc");
const { Model } = require("./model");

class Carts extends Model {
    constructor() {
        super();
        this._carts = [];
    }

    get carts() {
        return this._carts;
    }

    async load(itemsLookup) {
        const val = localStorage.getItem("carts");
        let carts = (this._carts = val ? JSON.parse(val) : []);

        // Update items in cart to their latest version.
        for (const cart of carts) {
            const items = [];
            for (const cartItem of cart.items) {
                const item = itemsLookup[cartItem.store + cartItem.id];
                if (item) items.push(item);
            }
            cart.items = items;
        }
        this.save();
    }

    save() {
        const carts = [];
        for (const cart of this._carts) {
            carts.push({
                name: cart.name,
                items: cart.items.map((item) => {
                    return { store: item.store, id: item.id };
                }),
            });
        }
        localStorage.setItem("carts", JSON.stringify(carts, null, 2));
        this.notify();
    }

    add(name) {
        this._carts.push({ name: name, items: [] });
        this.save();
    }

    remove(name) {
        this._carts = this._carts.filter((cart) => cart.name !== name);
        this.save();
    }
}

exports.Carts = Carts;
