
// =========================================
// BLACKROCK INVESTMENT
// MARKETS PAGE JAVASCRIPT
// SIMULATED MARKET ENGINE
// =========================================

document.addEventListener("DOMContentLoaded", () => {

    // =========================================
    // MARKET DATA
    // =========================================

    const marketAssets = {

        // -----------------------------------------
        // CRYPTO
        // -----------------------------------------

        BTC: {
            price: 67842.31,
            change: 3.42,
            decimals: 2,
            volatility: 0.0012,
            marketCap: 1340000000000,
            volume: 38400000000
        },

        ETH: {
            price: 3482.76,
            change: 2.87,
            decimals: 2,
            volatility: 0.0015,
            marketCap: 419100000000,
            volume: 19700000000
        },

        USDT: {
            price: 1.00,
            change: 0.01,
            decimals: 2,
            volatility: 0.00008,
            marketCap: 112500000000,
            volume: 54200000000
        },

        BNB: {
            price: 612.48,
            change: 1.94,
            decimals: 2,
            volatility: 0.0013,
            marketCap: 89700000000,
            volume: 1800000000
        },

        SOL: {
            price: 186.42,
            change: -0.86,
            decimals: 2,
            volatility: 0.0018,
            marketCap: 86200000000,
            volume: 3100000000
        },

        XRP: {
            price: 0.58,
            change: -1.23,
            decimals: 2,
            volatility: 0.0017,
            marketCap: 32400000000,
            volume: 1400000000
        },


        // -----------------------------------------
        // OIL & GAS
        // -----------------------------------------

        BRENT: {
            price: 82.46,
            change: 1.28,
            decimals: 2,
            volatility: 0.0010
        },

        WTI: {
            price: 78.31,
            change: -0.64,
            decimals: 2,
            volatility: 0.0011
        },

        NATGAS: {
            price: 2.84,
            change: 0.92,
            decimals: 2,
            volatility: 0.0020
        },


        // -----------------------------------------
        // ENERGY STOCKS
        // -----------------------------------------

        XOM: {
            price: 118.42,
            change: 0.84,
            decimals: 2,
            volatility: 0.0008,
            marketCap: 510200000000,
            volume: 2100000000
        },

        CVX: {
            price: 164.31,
            change: -0.27,
            decimals: 2,
            volatility: 0.0008,
            marketCap: 305400000000,
            volume: 1600000000
        },

        COP: {
            price: 103.75,
            change: 1.12,
            decimals: 2,
            volatility: 0.0010,
            marketCap: 121800000000,
            volume: 1700000000
        },

        SHEL: {
            price: 72.18,
            change: 0.46,
            decimals: 2,
            volatility: 0.0008,
            marketCap: 225100000000,
            volume: 1200000000
        },

        BP: {
            price: 37.64,
            change: -0.38,
            decimals: 2,
            volatility: 0.0009,
            marketCap: 98500000000,
            volume: 800000000
        },

        TTE: {
            price: 67.92,
            change: 0.61,
            decimals: 2,
            volatility: 0.0008,
            marketCap: 160400000000,
            volume: 900000000
        }

    };


    // =========================================
    // HELPER FUNCTIONS
    // =========================================

    function formatPrice(value, decimals = 2) {

        return value.toLocaleString(
            "en-US",
            {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            }
        );

    }


    function formatCompact(value) {

        if (value >= 1e12) {

            return "$" + (value / 1e12).toFixed(2) + "T";

        }

        if (value >= 1e9) {

            return "$" + (value / 1e9).toFixed(1) + "B";

        }

        if (value >= 1e6) {

            return "$" + (value / 1e6).toFixed(1) + "M";

        }

        return "$" + value.toLocaleString("en-US");

    }


    function randomMovement(asset) {

        const randomDirection =
            Math.random() > 0.5 ? 1 : -1;

        const movement =
            Math.random() * asset.volatility;

        return randomDirection * movement;

    }


    // =========================================
    // UPDATE PRICE
    // =========================================

    function updateAsset(symbol) {

        const asset =
            marketAssets[symbol];

        if (!asset) {
            return;
        }


        const oldPrice =
            asset.price;


        // Generate a small simulated movement

        const movement =
            randomMovement(asset);


        asset.price =
            asset.price * (1 + movement);


        // Prevent unrealistic movement

        if (asset.price <= 0) {

            asset.price = oldPrice;

        }


        // Update simulated daily change

        const priceDifference =
            asset.price - oldPrice;

        const percentageMovement =
            (priceDifference / oldPrice) * 100;


        asset.change =
            asset.change + percentageMovement;


        // Keep percentage within a reasonable demo range

        asset.change =
            Math.max(
                -15,
                Math.min(
                    15,
                    asset.change
                )
            );


        updatePopularCard(
            symbol,
            asset
        );


        updateTable(
            symbol,
            asset
        );


        updateEnergyCard(
            symbol,
            asset
        );


        updateStockCard(
            symbol,
            asset
        );

    }


    // =========================================
    // POPULAR CRYPTO CARDS
    // =========================================

    function updatePopularCard(symbol, asset) {

        const priceElement =
            document.querySelector(
                `[data-price="${symbol}"]`
            );


        const changeElement =
            document.querySelector(
                `[data-change="${symbol}"]`
            );


        if (!priceElement) {
            return;
        }


        priceElement.textContent =
            "$" +
            formatPrice(
                asset.price,
                asset.decimals
            );


        if (changeElement) {

            updateChangeElement(
                changeElement,
                asset.change
            );

        }


        flashPrice(
            priceElement,
            asset.change
        );

    }


    // =========================================
    // OIL & GAS CARDS
    // =========================================

    function updateEnergyCard(symbol, asset) {

        const priceElement =
            document.querySelector(
                `[data-energy-price="${symbol}"]`
            );


        const changeElement =
            document.querySelector(
                `[data-energy-change="${symbol}"]`
            );


        if (!priceElement) {
            return;
        }


        priceElement.textContent =
            "$" +
            formatPrice(
                asset.price,
                asset.decimals
            );


        if (changeElement) {

            updateChangeElement(
                changeElement,
                asset.change
            );

        }


        flashPrice(
            priceElement,
            asset.change
        );

    }


    // =========================================
    // STOCK CARDS
    // =========================================

    function updateStockCard(symbol, asset) {

        const priceElement =
            document.querySelector(
                `[data-stock-price="${symbol}"]`
            );


        const changeElement =
            document.querySelector(
                `[data-stock-change="${symbol}"]`
            );


        if (!priceElement) {
            return;
        }


        priceElement.textContent =
            "$" +
            formatPrice(
                asset.price,
                asset.decimals
            );


        if (changeElement) {

            updateChangeElement(
                changeElement,
                asset.change
            );

        }


        flashPrice(
            priceElement,
            asset.change
        );

    }


    // =========================================
    // UPDATE TABLE
    // =========================================

    function updateTable(symbol, asset) {

        const priceElement =
            document.querySelector(
                `[data-table-price="${symbol}"]`
            );


        const changeElement =
            document.querySelector(
                `[data-table-change="${symbol}"]`
            );


        const marketCapElement =
            document.querySelector(
                `[data-market-cap="${symbol}"]`
            );


        const volumeElement =
            document.querySelector(
                `[data-volume="${symbol}"]`
            );


        if (priceElement) {

            priceElement.textContent =
                "$" +
                formatPrice(
                    asset.price,
                    asset.decimals
                );


            flashPrice(
                priceElement,
                asset.change
            );

        }


        if (changeElement) {

            updateChangeElement(
                changeElement,
                asset.change
            );

        }


        if (
            marketCapElement &&
            asset.marketCap
        ) {

            // Small simulated market-cap movement

            const capMovement =
                1 +
                (
                    Math.random() - 0.5
                ) * 0.001;


            asset.marketCap =
                asset.marketCap *
                capMovement;


            marketCapElement.textContent =
                formatCompact(
                    asset.marketCap
                );

        }


        if (
            volumeElement &&
            asset.volume
        ) {

            // Small simulated volume movement

            const volumeMovement =
                1 +
                (
                    Math.random() - 0.5
                ) * 0.003;


            asset.volume =
                asset.volume *
                volumeMovement;


            volumeElement.textContent =
                formatCompact(
                    asset.volume
                );

        }

    }


    // =========================================
    // CHANGE DISPLAY
    // =========================================

    function updateChangeElement(
        element,
        change
    ) {

        const arrow =
            change > 0
                ? "fa-arrow-up"
                : change < 0
                    ? "fa-arrow-down"
                    : "fa-minus";


        const sign =
            change > 0
                ? "+"
                : change < 0
                    ? ""
                    : "";


        element.classList.remove(
            "positive",
            "negative",
            "neutral"
        );


        if (change > 0) {

            element.classList.add(
                "positive"
            );

        } else if (change < 0) {

            element.classList.add(
                "negative"
            );

        } else {

            element.classList.add(
                "neutral"
            );

        }


        const icon =
            element.querySelector("i");


        if (icon) {

            icon.className =
                `fa-solid ${arrow}`;

        }


        const text =
            document.createTextNode(
                ` ${sign}${change.toFixed(2)}%`
            );


        // Remove previous text nodes

        Array.from(
            element.childNodes
        ).forEach(node => {

            if (
                node.nodeType ===
                Node.TEXT_NODE
            ) {

                node.remove();

            }

        });


        element.appendChild(
            text
        );

    }


    // =========================================
    // PRICE FLASH
    // =========================================

    function flashPrice(
        element,
        change
    ) {

        element.classList.remove(
            "price-up",
            "price-down"
        );


        // Force browser reflow

        void element.offsetWidth;


        if (change >= 0) {

            element.classList.add(
                "price-up"
            );

        } else {

            element.classList.add(
                "price-down"
            );

        }


        setTimeout(() => {

            element.classList.remove(
                "price-up",
                "price-down"
            );

        }, 650);

    }


    // =========================================
    // UPDATE MARKET SUMMARY
    // =========================================

    function updateMarketSummary() {

        let totalMarketCap = 0;

        let totalVolume = 0;

        let totalChange = 0;

        let assetCount = 0;


        Object.values(
            marketAssets
        ).forEach(asset => {

            if (asset.marketCap) {

                totalMarketCap +=
                    asset.marketCap;

            }


            if (asset.volume) {

                totalVolume +=
                    asset.volume;

            }


            totalChange +=
                asset.change;


            assetCount++;

        });


        const averageChange =
            totalChange /
            assetCount;


        const marketCapElement =
            document.getElementById(
                "totalMarketCap"
            );


        const volumeElement =
            document.getElementById(
                "totalVolume"
            );


        const changeElement =
            document.getElementById(
                "overallMarketChange"
            );


        const sentimentElement =
            document.getElementById(
                "marketSentiment"
            );


        const sentimentDescription =
            document.getElementById(
                "sentimentDescription"
            );


        if (marketCapElement) {

            marketCapElement.textContent =
                formatCompact(
                    totalMarketCap
                );

        }


        if (volumeElement) {

            volumeElement.textContent =
                formatCompact(
                    totalVolume
                );

        }


        if (changeElement) {

            const sign =
                averageChange >= 0
                    ? "+"
                    : "";


            changeElement.textContent =
                sign +
                averageChange.toFixed(2) +
                "%";


            changeElement.classList.toggle(
                "positive",
                averageChange >= 0
            );

        }


        if (sentimentElement) {

            if (averageChange > 1) {

                sentimentElement.textContent =
                    "Positive";

            } else if (
                averageChange < -1
            ) {

                sentimentElement.textContent =
                    "Negative";

            } else {

                sentimentElement.textContent =
                    "Neutral";

            }

        }


        if (sentimentDescription) {

            if (averageChange > 1) {

                sentimentDescription.innerHTML =
                    `<i class="fa-solid fa-circle"></i>
                     Bullish activity`;

            } else if (
                averageChange < -1
            ) {

                sentimentDescription.innerHTML =
                    `<i class="fa-solid fa-circle"></i>
                     Bearish activity`;

            } else {

                sentimentDescription.innerHTML =
                    `<i class="fa-solid fa-circle"></i>
                     Mixed activity`;

            }

        }

    }


    // =========================================
    // SIMULATED MARKET CLOCK
    // =========================================

    function updateMarketStatus() {

        const statusText =
            document.getElementById(
                "marketStatusText"
            );


        if (!statusText) {
            return;
        }


        // Demo market is always presented
        // as active.

        statusText.textContent =
            "Market Open";

    }


    // =========================================
    // RUN MARKET ENGINE
    // =========================================

    function updateMarkets() {

        Object.keys(
            marketAssets
        ).forEach(symbol => {

            updateAsset(symbol);

        });


        updateMarketSummary();

        updateMarketStatus();

    }


    // =========================================
    // INITIAL UPDATE
    // =========================================

    updateMarkets();


    // =========================================
    // CONTINUOUS SIMULATION
    // =========================================
    //
    // Prices update every 3 seconds.
    //
    // This is simulated demo data and does
    // NOT represent live financial prices.
    // =========================================

    setInterval(
        updateMarkets,
        3000
    );


    // =========================================
    // MARKET SEARCH
    // =========================================

    const marketSearch =
        document.getElementById(
            "marketSearch"
        );


    const marketRows =
        document.querySelectorAll(
            "#marketTableBody tr"
        );


    const marketEmpty =
        document.getElementById(
            "marketEmpty"
        );


    if (marketSearch) {

        marketSearch.addEventListener(
            "input",
            function () {

                const searchValue =
                    this.value
                        .toLowerCase()
                        .trim();


                let visibleRows = 0;


                marketRows.forEach(row => {

                    const assetName =
                        (
                            row.dataset.name ||
                            ""
                        ).toLowerCase();


                    const symbol =
                        (
                            row.dataset.symbol ||
                            ""
                        ).toLowerCase();


                    const matches =
                        assetName.includes(
                            searchValue
                        ) ||
                        symbol.includes(
                            searchValue
                        );


                    if (matches) {

                        row.style.display =
                            "";

                        visibleRows++;

                    } else {

                        row.style.display =
                            "none";

                    }

                });


                if (marketEmpty) {

                    marketEmpty.style.display =
                        visibleRows === 0
                            ? "block"
                            : "none";

                }

            }
        );

    }

});

