# Hot Prices AU

A terrible fork of the excellent open source project [heissepreise](https://github.com/badlogic/heissepreise). It fetches data from the duopoly of Australian grocery chains on a daily basis and makes them available through a web interface.

This project is very basic and partly contains a copy of the original code (for the frontend) and partly a re-implementation in Python (for the backend). The aim is to provie a similar service to Australians wanting to compare grocery prices and track the history of those prices. There no website yet.

The backend consists of a command to scrape the raw data and a command to add the scraped data into the price history and normalise it. The frontend is largely copied from heissepreise, but adapted to local circumstances (translated, using `$` instead of `€`). Due to the excellent design by badlogic, the site is entirely static, so once compiled the backend can be any old webserver.

## Requirements

-   Node.js (to compile the frontend)
-   Python (to scrape/analyse)

## Running

### Development

---- TODO ----

Install NodeJS, then run this in a shell of your choice.

```bash
git clone https://github.com/badlogic/heissepreise
cd heissepreise
mkdir -p data
npm install
npm run dev
```

The first time you run this, the data needs to be fetched from the stores. You should see log out put like this.

```bash
Fetching data for date: 2023-05-23
Fetched LIDL data, took 0.77065160000324 seconds
Fetched MPREIS data, took 13.822936070203781 seconds
Fetched SPAR data, took 17.865891209602356 seconds
Fetched BILLA data, took 52.95784649944306 seconds
Fetched HOFER data, took 64.83968291568756 seconds
Fetched DM data, took 438.77065160000324 seconds
Merged price history
App listening on port 3000
```

Once the app is listening per default on port 3000, open <http://localhost:3000> in your browser.

Subsequent starts will fetch the data asynchronously, so you can start working immediately.

### Production

Install the dependencies as per above, then simply run:

```
git clone https://github.com/badlogic/heissepreise
cd heissepreise
node --dns-result-order=ipv4first /usr/bin/npm install --omit=dev
npm run start
```

Once the app is listening per default on port 3000, open <http://localhost:3000> in your browser.

## Using data from heisse-preise.io

You can also get the [raw data](https://heisse-preise.io/data/latest-canonical.json). The raw data is returned as a JSON array of items. An item has the following fields:

-   `store`: (`billa`, `spar`, `hofer`, `dm`, `lidl`, `mpreis`, ...)
-   `name`: the product name.
-   `price`: the current price in €.
-   `priceHistory`: an array of `{ date: "yyyy-mm-dd", price: number }` objects, sorted in descending order of date.
-   `unit`: unit the product is sold at. May be undefined.
-   `quantity`: quantity the product is sold at for the given price
-   `bio`: whether this product is classified as organic/"Bio"

If you run the project locally, you can use the data from the live site including the historical data as follows:

```
cd heisse-preise
rm data/latest-canonical.*
curl -o data/latest-canonical.json https://heisse-preise.io/data/latest-canonical.json
```

Restart the server with either `npm run dev` or `npm run start`.

## Historical Data Credits

The live site at [heisse-preise.io](https://heisse-preise.io) feature historical data from:

-   [Dossier](https://www.dossier.at/dossiers/supermaerkte/quellen/anatomie-eines-supermarkts-die-methodik/)
-   [@h43z](https://h.43z.one), who runs [preisinflation.online](https://inflation.43z.one), another grocery price tracker.
