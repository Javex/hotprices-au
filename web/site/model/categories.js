// These are a match of the Billa categories, which are organized in a 2-level hierarchy.
// Each category in the top level gets a code from 1-Z, each sub category also gets a code.
// Together the two codes from a unique id for the category, which we store in the item.category
// field. E.g. "Obst & Gemüse > Salate" has the code "13", "Kühlwaren > Tofu" has the code "4C"
exports.categories = [
    {
        name: "🍌🥑 Fruit & Veg",
        subcategories: [
            /*00*/ "Fresh Fruit",
            /*01*/ "Fresh Vegetables",
            /*02*/ "Fresh Salad & Herbs",
            /*03*/ "Organic Fruit & Vegetables",
            /*04*/ "Prepared Fresh Produce",
            /*05*/ "Frozen Fruit & Vegetables"
        ]
    },
    {
        name: "🥩🦐 Meat & Seafood",
        subcategories: [
            /*06*/ "Meat & Seafood",
            /*07*/ "Beef & Veal",
            /*08*/ "Lamb",
            /*09*/ "Pork",
            /*10*/ "Poultry",
            /*11*/ "Seafood",
            /*12*/ "Sausages, Burgers & Meatballs",
            /*13*/ "Marinated & Prepped Meats",
            /*14*/ "Frozen Meat & Seafood"
        ]
    },
    {
        name: "🥚🧀 Dairy, Eggs & Fridge",
        subcategories: [
            /*15*/ "Dairy, Eggs & Fridge",
            /*16*/ "Milk",
            /*17*/ "Eggs",
            /*18*/ "Yogurt",
            /*19*/ "Cheese",
            /*20*/ "Butter & Margarine",
            /*21*/ "Cream & Desserts",
            /*22*/ "Dips & Cold Packaged Meats",
            /*23*/ "Tofu, Tempeh & Meat Alternatives",
            /*24*/ "Fresh Pasta & Sauces",
            /*25*/ "Chilled Juice",
            /*26*/ "Salads & Salad Kits",
            /*27*/ "Ready Meals & Snacks"
        ]
    },
    {
        name: "🛒🍫 Pantry",
        subcategories: [
            /*28*/ "Pantry",
            /*29*/ "Biscuits & Crackers",
            /*30*/ "Breakfast & Spreads",
            /*31*/ "Canned Goods",
            /*32*/ "Pasta & Noodles",
            /*33*/ "Rice & Grains",
            /*34*/ "Cooking & Baking Needs",
            /*35*/ "Condiments & Dressings",
            /*36*/ "Healthy Snacks & Foods",
            /*37*/ "Soup",
            /*38*/ "Packaged Meals",
            /*39*/ "Savoury Snacks",
            /*40*/ "Confectionery",
            /*41*/ "International Foods"
        ]
    },
    {
        name: "🍞🥐 Bakery",
        subcategories: [
            /*42*/ "Bakery",
            /*43*/ "Bread Rolls & Wraps",
            /*44*/ "Cakes, Muffins & Pastries",
            /*45*/ "Bakery Snacks",
            /*46*/ "Bakery Bread",
            /*47*/ "Flatbread"
        ]
    },
    {
        name: "🧊🍦 Frozen",
        subcategories: [
            /*48*/ "Frozen",
            /*49*/ "Frozen Meals",
            /*50*/ "Frozen Meat & Poultry",
            /*51*/ "Frozen Seafood",
            /*52*/ "Frozen Vegetables & Fruit",
            /*53*/ "Frozen Chips, Wedges & Potatoes",
            /*54*/ "Ice Cream & Frozen Desserts",
            /*55*/ "Frozen Party Food"
        ]
    },
    {
        name: "🥤🍺 Drinks",
        subcategories: [
            /*56*/ "Drinks",
            /*57*/ "Juice",
            /*58*/ "Soft Drinks",
            /*59*/ "Mineral Water",
            /*60*/ "Energy Drinks",
            /*61*/ "Iced Tea",
            /*62*/ "Cordials",
            /*63*/ "Syrups",
            /*64*/ "Sports Drinks"
        ]
    },
    {
        name: "👄💅 Beauty & Personal Care",
        subcategories: [
            /*65*/ "Beauty & Personal Care",
            /*66*/ "Feminine Hygiene",
            /*67*/ "Hair Care",
            /*68*/ "Men's Grooming",
            /*69*/ "Oral Care",
            /*70*/ "Shaving & Hair Removal",
            /*71*/ "Skin Care",
            /*72*/ "Cosmetics",
            /*73*/ "Period Care",
            /*74*/ "Continence Care",
            /*75*/ "Personal Care & Hygiene",
            /*76*/ "First Aid & Medicinal",
            /*77*/ "Women's Hair Removal",
            /*78*/ "Hampers & Gifting",
            /*79*/ "Everyday Market"
        ]
    },
    {
        name: "🍷🍻 Liquor",
        subcategories: [
            /*80*/ "Liquor",
            /*81*/ "Liquor Specials",
            /*82*/ "Beer",
            /*83*/ "Cider",
            /*84*/ "White Wine",
            /*85*/ "Red Wine",
            /*86*/ "Champagne & Sparkling",
            /*87*/ "Fortified & Cask Wine",
            /*88*/ "Spirits",
            /*89*/ "Premixed Drinks"
        ]
    },
    {
        name: "💊🩺 HealthyLife Pharmacy",
        subcategories: [
            /*90*/ "HealthyLife Pharmacy",
            /*91*/ "HealthyLife Pharmacy Specials",
            /*92*/ "Prescription Medicine",
            /*93*/ "Pharmacist Only Medicine",
            /*94*/ "Pharmacy Medicine"
        ]
    },
    {
        name: "👶🍼 Baby",
        subcategories: [
            /*95*/ "Baby",
            /*96*/ "Baby Specials",
            /*97*/ "Pregnancy Tests",
            /*98*/ "Nappies & Wipes",
            /*99*/ "Baby Food",
            /*100*/ "Baby Accessories",
            /*101*/ "Baby Formula & Toddler Milk",
            /*102*/ "Baby Furniture",
            /*103*/ "Baby Travel & Accessories",
            /*104*/ "Hampers & Gifting",
            /*105*/ "Everyday Market"
        ]
    },
    {
        name: "🐶🐱 Pet",
        subcategories: [
            /*106*/ "Pet",
            /*107*/ "Pet Specials",
            /*108*/ "Cat & Kitten",
            /*109*/ "Dog & Puppy",
            /*110*/ "Birds, Fish & Small Pets",
            /*111*/ "Everyday Market"
        ]
    },
    {
        name: "🧼🧽 Cleaning",
        subcategories: [
            /*112*/ "Cleaning",
            /*113*/ "Cleaning Specials",
            /*114*/ "Laundry",
            /*115*/ "Kitchen",
            /*116*/ "Toilet Paper, Tissues & Paper Towels",
            /*117*/ "Cleaning Goods",
            /*118*/ "Pest Control",
            /*119*/ "Garden & Outdoors",
            /*120*/ "Hardware",
            /*121*/ "Bathroom",
            /*122*/ "Homewares",
            /*123*/ "Electronics",
            /*124*/ "Sport & Fitness"
        ]
    },
    {
        name: "🏠🛋️ Home & Lifestyle",
        subcategories: [
            /*125*/ "Home & Lifestyle",
            /*126*/ "Home & Lifestyle Specials",
            /*127*/ "Dining & Entertaining",
            /*128*/ "Party Supplies",
            /*129*/ "Kitchenware & Storage",
            /*130*/ "Kitchen Appliances",
            /*131*/ "Home Appliances",
            /*132*/ "Home Decor & Furniture",
            /*133*/ "Manchester & Bedding",
            /*134*/ "Bathroom Towels & Accessories",
            /*135*/ "Clothing & Accessories",
            /*136*/ "Electronics",
            /*137*/ "Stationery & Office Supplies",
            /*138*/ "Toys & Games",
            /*139*/ "Books & Magazines",
            /*140*/ "Outdoor Living",
            /*141*/ "Luggage & Travel",
            /*142*/ "Sport, Fitness & Outdoor Activities",
            /*143*/ "Everyday Market"
        ]
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
