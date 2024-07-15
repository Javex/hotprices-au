// These are a match of the Billa categories, which are organized in a 2-level hierarchy.
// Each category in the top level gets a code from 1-Z, each sub category also gets a code.
// Together the two codes from a unique id for the category, which we store in the item.category
// field. E.g. "Obst & Gemüse > Salate" has the code "13", "Kühlwaren > Tofu" has the code "4C"
exports.categories = [
    {
        name: "🍌🥑 Fruit & Veg",
        subcategories: [
            /*00*/ "Fruit",
            /*01*/ "Veg",
            /*02*/ "Salad & Herbs",
            /*03*/ "Nuts & Dried Fruit",
        ],
    },
    {
        name: "🍞🥐 Bread & Pastries",
        subcategories: [
            /*10*/ "Rolls & Toast",
            /*11*/ "Bread & Pastries",
            /*12*/ "Crispbread & Zwieback",
            /*13*/ "Cakes & Co.",
            /*14*/ "Breadcrumbs & Crumbs",
        ],
    },
    {
        name: "🥤🍺 Beverages",
        subcategories: [
            /*20*/ "Non-Alcoholic Beverages",
            /*21*/ "Beer & Shandy",
            /*22*/ "Coffee, Tea & Co.",
            /*23*/ "Sparkling Wine & Champagne",
            /*24*/ "Spirits",
            /*25*/ "Wine",
            /*26*/ "Mineral Water",
        ],
    },
    {
        name: "🥩🦐 Meat & Seafood",
        subcategories: [
            /*30*/ "Poultry",
            /*31*/ "Meat",
            /*32*/ "Seafood",
            /*33*/ "BBQ",
        ],
    },
    {
        name: "🧊🍦 Frozen",
        subcategories: [
            /*40*/ "Ice Cream",
            /*41*/ "Unknown", // Not available in Billa hierarchy, left blank
            /*42*/ "Ready Meals",
            /*43*/ "Fish & Shrimp",
            /*44*/ "Vegetables & Herbs",
            /*45*/ "French Fries & Co.",
            /*46*/ "Pizza & Baguette",
            /*47*/ "Desserts & Fruits",
        ],
    },
    {
        name: "🌾 Basic Food",
        subcategories: [
            /*50*/ "Asian & Mexican Products",
            /*51*/ "Baby",
            /*52*/ "Baking",
            /*53*/ "Vinegar & Oil",
            /*54*/ "Ready Meals",
            /*55*/ "Spices & Seasonings",
            /*56*/ "Honey, Jam & Co.",
            /*57*/ "Canned & Pickled Foods",
            /*58*/ "Cakes & Co.",
            /*59*/ "Flour & Grain Products",
            /*5A*/ "Muesli & Cereals",
            /*5B*/ "Rice, Pasta & Sauces",
            /*5C*/ "Sauces & Dressings",
            /*5D*/ "Special Diet",
            /*5E*/ "Sugar & Sweeteners",
            /*5F*/ "Convenience Products",
        ],
    },
    {
        name: "🍫🍿 Sweets & Savory Snacks",
        subcategories: [
            /*60*/ "Ladyfingers & Ice Cream Cones",
            /*61*/ "Smart Treats",
            /*62*/ "Muesli Bars",
            /*63*/ "Chips & Co.",
            /*64*/ "Sweets",
        ],
    },
    {
        name: "👄👶 Personal Care",
        subcategories: [
            /*70*/ "Baby",
            /*71*/ "Feminine Hygiene",
            /*72*/ "Deodorants",
            /*73*/ "Hair Care & Hair Colors",
            /*74*/ "Plasters & Bandages",
            /*75*/ "Skin & Lip Care",
            /*76*/ "Oral Hygiene",
            /*77*/ "Shaving Needs",
            /*78*/ "Soap & Shower Gels",
            /*79*/ "Sun & Gel Protection",
            /*7A*/ "Contraceptives",
            /*7B*/ "Foot Care",
            /*7C*/ "Tights & Socks",
        ],
    },
    {
        name: "🧹🧺 Household",
        subcategories: [
            /*80*/ "Office & School Supplies",
            /*81*/ "Garden",
            /*82*/ "Adhesives & Fasteners",
            /*83*/ "Kitchen Items",
            /*84*/ "Kitchen Rolls & Toilet Paper",
            /*85*/ "Lamps & Batteries",
            /*86*/ "Garbage Bags, Freezer Bags & Co.",
            /*87*/ "Room Sprays & Candles",
            /*88*/ "Cleaning & Care",
            /*89*/ "Tissues & Napkins",
            /*8A*/ "Laundry Detergent & Fabric Softener",
            /*8B*/ "Shoe Care",
            /*8C*/ "Plastic Containers",
            /*8D*/ "Insect Repellent",
            /*8E*/ "Toys",
            /*8F*/ "Hygiene Protection Items",
        ],
    },
    {
        name: "🐶🐱 Pet",
        subcategories: [
            /*90*/ "Dogs",
            /*91*/ "Cats",
            /*92*/ "Rodents",
            /*93*/ "Birds",
        ],
    },
    {
        name: "Unknown",
        subcategories: [/*A0*/ "Unknown"],
    },
];

exports.categories.forEach((category, index) => (category.index = index));

exports.toCategoryCode = (i, j) => {
    return (
        (i < 10 ? "" + i : String.fromCharCode("A".charCodeAt(0) + (i - 10))) + (j < 10 ? "" + j : String.fromCharCode("A".charCodeAt(0) + (j - 10)))
    );
};

exports.fromCategoryCode = (code) => {
    if (!code || code.length != 2) return [exports.categories.length - 1, 0];
    const codeI = code.charCodeAt(0);
    const codeJ = code.charCodeAt(1);
    return [
        codeI - (codeI < "A".charCodeAt(0) ? "0".charCodeAt(0) : "A".charCodeAt(0) - 10),
        codeJ - (codeJ < "A".charCodeAt(0) ? "0".charCodeAt(0) : "A".charCodeAt(0) - 10),
    ];
};

exports.isValidCode = (code) => {
    const [i, j] = exports.fromCategoryCode(code);
    if (i < 0 || i >= exports.categories.length) return false;
    const category = exports.categories[i];
    if (j < 0 || j >= exports.categories.subcategories) return false;
    return true;
};

exports.getCategory = (code) => {
    const [i, j] = exports.fromCategoryCode(code);
    return [exports.categories[i], exports.categories[i].subcategories[j]];
};

exports.UNKNOWN_CATEGORY = exports.toCategoryCode(exports.categories.length - 1, 0);

if (require.main === module) {
    const code = exports.toCategoryCode(10, 1);
    console.log(code);
    const [i, j] = exports.fromCategoryCode("A1");
    console.log(i + ", " + j);
    console.log(exports.isValidCode("F1"));
    console.log(exports.isValidCode("11"));
    console.log(exports.getCategory("A1"));
}
