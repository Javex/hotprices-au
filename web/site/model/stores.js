const allSpacesRegex = / /g;

exports.stores = {
    woolies: {
        name: "Woolworths",
        budgetBrands: [],
        color: "green",
        defaultChecked: true,
        getUrl: (item) => `https://www.woolworths.com.au/shop/productdetails/${item.id}`,
    },
    coles: {
        name: "Coles",
        budgetBrands: [],
        color: "red",
        defaultChecked: true,
        getUrl: (item) => `https://www.coles.com.au/product/${item.id}`,
    },
};

exports.STORE_KEYS = Object.keys(exports.stores);
exports.BUDGET_BRANDS = [...new Set([].concat(...Object.values(exports.stores).map((store) => store.budgetBrands)))];
