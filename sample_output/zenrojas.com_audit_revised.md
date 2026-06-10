# Zen Rojas CRO audit

## Executive summary

Zen Rojas presents a clear brand promise around organic loose leaf tea, calm rituals, family ownership, and wellness-led use cases. The crawl captured a working Shopify storefront with homepage, product pages, collections, cart, robots, sitemap, product JSON, and collection JSON all available from the selected run (`artifacts/zenrojas.com-20260609T223052Z/manifest.json`). The visible conversion constraint is not basic site availability; it is helping shoppers choose the right ritual quickly when the catalog mixes sleep, immune support, digestion, energy, samplers, teaware, and gift cards.

The highest-priority leaks are visible on high-intent surfaces. The all-products collection lists 12 products, with several teas marked Sold Out and no filters or need-based navigation (`artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-collections-all-ce5d200c.txt`; `artifacts/zenrojas.com-20260609T223052Z/screenshots/zenrojas.com-collections-all-ce5d200c-desktop.png`). PDPs include strong ingredient, use, warranty, and add-to-cart content, but the crawl found no JSON-LD product structured data and no favicon link in rendered pages (`artifacts/zenrojas.com-20260609T223052Z/raw/zenrojas.com-products-blacktea-9cc1bdcb.json`; `artifacts/zenrojas.com-20260609T223052Z/manifest.json`). This run did not include analytics, heatmaps, or order data, so the recommendations below are framed as testable hypotheses from visible storefront evidence.

The site already has useful CRO assets to build from: the homepage surfaces missions like Sleep & Relaxation, Immune Support, Daily Energy, and Digestion Support; PDPs show brewing instructions, organic/ethically sourced claims, 30-Day Warranty copy, and recommended products; the cart loads as a clean empty state with a continue-browsing link. The experiments focus on making that proof easier to act on, recovering unavailable-product intent, and improving discovery, retention capture, and technical search eligibility.

## Proposed experiments

### exp-zr-001 — Add a ritual finder above the product grid

**Pillar:** Conversion  
**Affected surface and URL:** Products collection, `https://zenrojas.com/collections/all`  
**Evidence:** The Products page lists teas, samplers, teaware, gift card, and several Sold Out items in one grid, while the raw collection signals show sorting but no filters and no need/use-case navigation (`artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-collections-all-ce5d200c.txt`; `artifacts/zenrojas.com-20260609T223052Z/raw/zenrojas.com-collections-all-ce5d200c.json`; `artifacts/zenrojas.com-20260609T223052Z/screenshots/zenrojas.com-collections-all-ce5d200c-desktop.png`).  
**Hypothesis:** Product-grid click-through improves if shoppers can choose by use case before scanning individual SKUs.  
**Primary change:** Add a compact "Choose your ritual" module above the grid with Sleep, Immune Support, Digestion, Daily Energy, Samplers, and Teaware chips that filter or anchor the collection.  
**Primary KPI:** Collection-to-PDP click-through rate  
**Decision rule:** Ship if collection-to-PDP CTR improves and PDP add-to-cart rate does not decline.  
**Expected lift range:** +6-11%  
**Confidence %:** 78%

### exp-zr-002 — Recover sold-out tea demand with back-in-stock capture

**Pillar:** Conversion  
**Affected surface and URL:** Organic Sleep Tea PDP, `https://zenrojas.com/products/organicsleeptea`; Products collection, `https://zenrojas.com/collections/all`  
**Evidence:** Organic Sleep Tea rendered with price `$12.00` and `SOLD OUT`; the product feed shows Organic Sleep Tea, Heartburn Organic Tea, Premium Sencha Organic Green Tea, and Unwind Organic Tea with 0 available variants (`artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-products-organicsleeptea-93485e52.txt`; `artifacts/zenrojas.com-20260609T223052Z/raw/zenrojas.com-products.json-products.json-a7680a87.bin`; `artifacts/zenrojas.com-20260609T223052Z/screenshots/zenrojas.com-products-organicsleeptea-93485e52-desktop.png`).  
**Hypothesis:** Sold-out PDP exits decrease if unavailable teas capture intent and route shoppers to the closest available ritual.  
**Primary change:** Replace the dead-end sold-out button area with email/SMS back-in-stock capture, estimated restock copy if available, and "Try this now" alternatives such as samplers or Bodyguard/Black Tea where relevant.  
**Primary KPI:** Back-in-stock signup rate on sold-out PDPs  
**Decision rule:** Ship if signup rate plus alternative-product clicks increases without increasing refund/support contacts.  
**Expected lift range:** +7-12%  
**Confidence %:** 74%

### exp-zr-003 — Make PDP proof scannable near add-to-cart

**Pillar:** Conversion  
**Affected surface and URL:** Organic Black Tea PDP, `https://zenrojas.com/products/blacktea`  
**Evidence:** The Black Tea PDP has price, variant, add-to-cart, "More payment options," a frequently-bought-together module, organic/ethical sourcing copy, 50-cup count, and 30-Day Warranty copy, but the guarantee and core reasons to buy sit within long text below the product story (`artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-products-blacktea-9cc1bdcb.txt`; `artifacts/zenrojas.com-20260609T223052Z/raw/zenrojas.com-products-blacktea-9cc1bdcb.json`; `artifacts/zenrojas.com-20260609T223052Z/screenshots/zenrojas.com-products-blacktea-9cc1bdcb-desktop.png`).  
**Hypothesis:** Add-to-cart rate improves when proof is visible next to the buying controls instead of requiring shoppers to read the full description first.  
**Primary change:** Add a three-point proof strip beside the price/CTA: "50 cups per bag," "100% organic + ethically sourced," and "30-Day Warranty," with the longer FDA disclaimer kept below the product details.  
**Primary KPI:** PDP add-to-cart rate  
**Decision rule:** Ship if PDP add-to-cart rate improves and product-page scroll depth does not materially decline.  
**Expected lift range:** +6-11%  
**Confidence %:** 74%

### exp-zr-004 — Turn samplers into the default discovery path

**Pillar:** AOV  
**Affected surface and URL:** Loose Leaf Samplers PDP, `https://zenrojas.com/products/looseleafsamplers`; homepage, `https://zenrojas.com/`  
**Evidence:** The homepage promotes "Your Next Favorite Sip Awaits..." with Tea Bag Samplers and Loose Leaf Samplers from `$2`; the Loose Leaf Samplers PDP offers individual blend choices plus a Loose Leaf Sampler Set (`artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-c9a96298.txt`; `artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-products-looseleafsamplers-77cadb8c.txt`; `artifacts/zenrojas.com-20260609T223052Z/screenshots/zenrojas.com-products-looseleafsamplers-77cadb8c-desktop.png`).  
**Hypothesis:** First-order AOV rises if discovery shoppers are nudged from single `$2` samples into a complete sampler set before choosing full-size teas.  
**Primary change:** Make "Start with the complete sampler set" the primary sampler CTA, show the included blends in a small comparison table, and add a full-size follow-up recommendation for each blend.  
**Primary KPI:** AOV among sampler PDP visitors  
**Decision rule:** Ship if sampler visitor AOV increases while sampler add-to-cart rate stays flat or improves.  
**Expected lift range:** +5-10%  
**Confidence %:** 72%

### exp-zr-005 — Expand frequently bought together by ritual

**Pillar:** AOV  
**Affected surface and URL:** Tea Bags PDP, `https://zenrojas.com/products/tea-bags`; Organic Black Tea PDP, `https://zenrojas.com/products/blacktea`  
**Evidence:** The Tea Bags and Black Tea PDPs both show frequently-bought-together modules with accessories and samplers; Tea Bags pairs with Tea Bag Samplers and Tea Infuser for a displayed total of `$12.00`, while Black Tea pairs with Tea Bags and Tea Infuser for `$18.00` (`artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-products-tea-bags-6ae5d454.txt`; `artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-products-blacktea-9cc1bdcb.txt`).  
**Hypothesis:** Bundle attachment improves if the upsell is named as a beginner or daily ritual kit rather than a generic frequently-bought-together group.  
**Primary change:** Rename and reframe bundles as "Loose Leaf Starter Kit" and "Daily Brew Kit," with tea, Tea Bags or Infuser, and sampler add-ons selected by default where inventory permits.  
**Primary KPI:** Bundle attach rate  
**Decision rule:** Ship if bundle attach rate rises and single-item add-to-cart rate does not fall.  
**Expected lift range:** +6-12%  
**Confidence %:** 70%

### exp-zr-006 — Make newsletter capture use-case specific

**Pillar:** Retention  
**Affected surface and URL:** Homepage and footer newsletter forms, `https://zenrojas.com/`  
**Evidence:** The homepage includes two newsletter forms using "Promotions, new products and sales. Directly to your inbox." and an email placeholder, while the same page also has strong use-case sections for Sleep & Relaxation, Immune Support, Daily Energy, and Digestion Support (`artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-c9a96298.txt`; `artifacts/zenrojas.com-20260609T223052Z/raw/zenrojas.com-c9a96298.json`).  
**Hypothesis:** Email signup rate improves if the opt-in promises ritual guidance tied to the shopper's goal, not only promotions.  
**Primary change:** Add selectable interests to the newsletter block, such as Sleep, Energy, Digestion, Immune Support, and Tea Education, then tailor the welcome flow to the chosen ritual.  
**Primary KPI:** Homepage email signup rate  
**Decision rule:** Ship if signup rate improves and unsubscribe rate from the welcome sequence remains acceptable.  
**Expected lift range:** +5-10%  
**Confidence %:** 68%

### exp-zr-007 — Build a replenishment reminder from cup counts

**Pillar:** Retention  
**Affected surface and URL:** Organic Black Tea PDP, `https://zenrojas.com/products/blacktea`; Bodyguard Organic Tea PDP, `https://zenrojas.com/products/bodyguardtea`  
**Evidence:** Black Tea states 50 cups per 100g bag; Bodyguard states 25 cups per 50g bag; both provide daily-use instructions and add-to-cart controls (`artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-products-blacktea-9cc1bdcb.txt`; `artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-products-bodyguardtea-723917e1.txt`).  
**Hypothesis:** Repeat purchase improves if daily tea buyers are prompted to reorder around expected depletion timing.  
**Primary change:** Add a post-purchase email/SMS replenishment reminder based on the visible cup count, with copy such as "Your 25-cup Bodyguard ritual may be running low."  
**Primary KPI:** 45-day repeat purchase rate for tea buyers  
**Decision rule:** Ship if repeat purchase rate improves without increasing unsubscribe rate materially.  
**Expected lift range:** +5-10%  
**Confidence %:** 64%

### exp-zr-008 — Create SEO landing pages for high-intent tea needs

**Pillar:** Acquisition  
**Affected surface and URL:** New pages linked from Products and homepage, e.g. `https://zenrojas.com/pages/sleep-tea-ritual` and `https://zenrojas.com/pages/digestion-tea-ritual`  
**Evidence:** The homepage already groups products by Sleep & Relaxation, Immune Support, Daily Energy, and Digestion Support; product tags in the saved product JSON include high-intent phrases such as "best tea for insomnia," "acid reflux relief tea organic," and "Clean Energy Tea" (`artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-c9a96298.txt`; `artifacts/zenrojas.com-20260609T223052Z/raw/zenrojas.com-products.json-products.json-a7680a87.bin`).  
**Hypothesis:** Organic landing-page conversion improves if search-intent visitors land on educational ritual pages with product modules instead of only generic product grids.  
**Primary change:** Create need-specific pages for sleep, digestion, immune support, and daily energy. Each page should include compliant education, relevant products, sampler path, warranty copy, and links to FAQs/refund policy.  
**Primary KPI:** Organic landing-page conversion rate  
**Decision rule:** Ship if indexed landing pages generate engaged organic sessions and outperform the all-products page on add-to-cart rate.  
**Expected lift range:** +6-12%  
**Confidence %:** 66%

### exp-zr-009 — Add product and breadcrumb structured data

**Pillar:** Acquisition  
**Affected surface and URL:** Product pages, including `https://zenrojas.com/products/blacktea` and `https://zenrojas.com/products/bodyguardtea`  
**Evidence:** Rendered raw artifacts show `structured_data_count: 0`, empty `structured_data_types`, and `json_ld_product: false` on the homepage and sampled PDPs, despite visible product titles, prices, descriptions, images, and availability data (`artifacts/zenrojas.com-20260609T223052Z/raw/zenrojas.com-products-blacktea-9cc1bdcb.json`; `artifacts/zenrojas.com-20260609T223052Z/raw/zenrojas.com-products-bodyguardtea-723917e1.json`; `artifacts/zenrojas.com-20260609T223052Z/manifest.json`).  
**Hypothesis:** Search result eligibility improves if product pages expose machine-readable product, offer, image, availability, and breadcrumb data.  
**Primary change:** Add JSON-LD Product and BreadcrumbList schema to PDP templates using Shopify product fields, including availability for sold-out teas and current variant prices.  
**Primary KPI:** Valid product rich-result coverage  
**Decision rule:** Ship if Google Rich Results/Test and Search Console validation pass with no structured-data errors.  
**Expected lift range:** +3-8%  
**Confidence %:** 73%

### exp-zr-010 — Improve crawl-time image and brand signals

**Pillar:** Performance  
**Affected surface and URL:** Homepage, `https://zenrojas.com/`; product/collection templates  
**Evidence:** The selected manifest reports 31 images without alt text in rendered samples and no favicon link found. Homepage raw details show 13 images with 7 missing alt attributes; Products collection raw details show 13 images with 5 missing alt attributes (`artifacts/zenrojas.com-20260609T223052Z/manifest.json`; `artifacts/zenrojas.com-20260609T223052Z/raw/zenrojas.com-c9a96298.json`; `artifacts/zenrojas.com-20260609T223052Z/raw/zenrojas.com-collections-all-ce5d200c.json`).  
**Hypothesis:** Accessibility, search understanding, and perceived brand polish improve if product imagery and browser chrome expose complete descriptive signals.  
**Primary change:** Add descriptive alt text for product, lifestyle, and blog images; add favicon links in the theme head; review large HEIC/JPG product media for optimized web formats while keeping visual quality.  
**Primary KPI:** Image-alt coverage and Lighthouse accessibility score  
**Decision rule:** Ship if missing-alt count drops near zero and Lighthouse accessibility improves without worsening desktop load timing.  
**Expected lift range:** +2-6%  
**Confidence %:** 69%

## Competitor analysis

Competitor sites were not crawled in this run; this is category-pattern benchmarking only. The adaptation ideas below are grounded in Zen Rojas artifacts from the selected crawl, especially the mission-led homepage, mixed product grid, sampler PDP, and wellness PDP copy.

| Competitor | Positioning | What the competitor makes easier | Pattern the audited store could adapt |
|---|---|---|---|
| Art of Tea | Premium loose leaf tea and wellness blends | Shopping by tea type, mood, and gift use case | Turn Zen Rojas' homepage missions into persistent collection filters and need pages, supported by the existing Sleep, Immune, Energy, and Digestion sections (`artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-c9a96298.txt`). |
| Rishi Tea | Organic loose leaf tea with ingredient and origin depth | Product education and flavor discovery | Move key proof like cup count, ingredients, caffeine, and organic sourcing into scannable PDP modules beside add-to-cart (`artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-products-blacktea-9cc1bdcb.txt`). |
| Traditional Medicinals | Herbal wellness teas organized by benefit | Benefit-led navigation for sleep, digestion, throat, and daily wellness | Build compliant ritual landing pages that route Zen Rojas' wellness claims to products and samplers without making unsupported medical promises (`artifacts/zenrojas.com-20260609T223052Z/raw/zenrojas.com-products.json-products.json-a7680a87.bin`). |
| DAVIDsTEA | Flavored tea discovery, accessories, gifts, and samplers | Starter kits, sampler paths, and giftable entry points | Package Tea Bags, Tea Infuser, Mug, and Samplers into named starter/gifting paths using the current accessory and sampler catalog (`artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-products-tea-bags-6ae5d454.txt`; `artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-products-looseleafsamplers-77cadb8c.txt`). |

## Technical checks

| Check | Status | Detail |
|---|---|---|
| SSL | Pass | Manifest technical checks report normalized URL scheme as `https` (`artifacts/zenrojas.com-20260609T223052Z/manifest.json`). |
| HTTPS redirect | Pass | Homepage final URL resolved to `https://zenrojas.com/` (`artifacts/zenrojas.com-20260609T223052Z/manifest.json`). |
| Sitemap | Pass | `/sitemap.xml` returned 200 and listed product, page, collection, blog, and agentic discovery sitemaps (`artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-sitemap.xml-sitemap.xml-d8357f0c.txt`). |
| Robots.txt | Pass | `/robots.txt` returned 200 and includes a sitemap directive (`artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-robots.txt-robots.txt-2a17c71d.txt`). |
| Critical pages loading | Pass | Homepage, sampled PDPs, collection pages, and cart returned status 200 with no failed pages in the selected manifest (`artifacts/zenrojas.com-20260609T223052Z/manifest.json`). |
| Meta tags | Pass | Homepage and sampled PDPs exposed titles and meta descriptions, including Black Tea's product-specific meta description (`artifacts/zenrojas.com-20260609T223052Z/raw/zenrojas.com-products-blacktea-9cc1bdcb.json`). |
| Structured data | Warn | No JSON-LD found in rendered pages; sampled PDPs show `structured_data_count: 0` and `json_ld_product: false` (`artifacts/zenrojas.com-20260609T223052Z/raw/zenrojas.com-products-blacktea-9cc1bdcb.json`). |
| Favicon | Warn | Rendered raw artifacts and manifest technical checks found no favicon link (`artifacts/zenrojas.com-20260609T223052Z/manifest.json`). |
| Mobile friendliness | Warn | Mobile capture was disabled for this required `--no-mobile` run, so mobile layout was not evidenced (`artifacts/zenrojas.com-20260609T223052Z/manifest.json`). |
| Mobile page speed | Warn | No mobile Lighthouse or mobile navigation timing was captured because mobile capture was disabled (`artifacts/zenrojas.com-20260609T223052Z/manifest.json`). |
| Desktop page speed | Pass | Rendered desktop timing was captured; homepage load event was 1478 ms and sampled PDP load events were around 1132-1513 ms in raw artifacts (`artifacts/zenrojas.com-20260609T223052Z/raw/zenrojas.com-c9a96298.json`). |
| Broken links | Pass | Manifest reports 0 sampled broken internal links and no failed pages (`artifacts/zenrojas.com-20260609T223052Z/manifest.json`). |
| Image optimization | Warn | Manifest reports 31 images without alt text in rendered samples; several direct product image URLs were captured as JPG/HEIC assets (`artifacts/zenrojas.com-20260609T223052Z/manifest.json`). |
| Cookie/privacy | Warn | Privacy Policy links were detected on rendered pages, but cookie consent behavior was not verified in this crawl (`artifacts/zenrojas.com-20260609T223052Z/raw/zenrojas.com-c9a96298.json`). |
| Checkout reachable | Warn | Cart page returned 200 and the cart drawer includes a CHECKOUT button, but this audit did not proceed into checkout or payment flows (`artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-cart-1742a2f2.txt`; `artifacts/zenrojas.com-20260609T223052Z/text/zenrojas.com-c9a96298.txt`). |
