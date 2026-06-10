## Executive summary

The Ginger People has strong visible proof for a retailer-routed ginger and turmeric brand: the selected crawl captured product pages with reviews, ingredient claims, use cases, and retailer-oriented copy such as "Grab a bag online or look for it in the candy aisle" on the GIN GINS Lemon PDP. The main conversion constraint is that high-intent product surfaces do not expose a clearly completed purchase handoff in the captured state: the crawler detected no visible price, add-to-cart button, or buy button on sampled PDPs, while screenshots show a Destini product-locator module loading below the product area. Evidence: `artifacts/gingerpeople.com-20260609T195304Z/manifest.json`, `artifacts/gingerpeople.com-20260609T195304Z/text/gingerpeople.com-products-gin-gins-lemon-ginger-chews-da248a63.txt`, `artifacts/gingerpeople.com-20260609T195304Z/screenshots/gingerpeople.com-products-gin-gins-lemon-ginger-chews-da248a63-desktop.png`.

The most explicit purchase-intent route needs the most immediate attention. The primary-nav Where To Buy URL returned 200, but the desktop screenshot shows a loading Destini locator followed by blog cards and footer content, and the extracted text contains no visible ZIP search, retailer list, or online retailer cards. The `/cart` URL returned a branded 404 with only a "Return to Mainland" recovery CTA. Evidence: `artifacts/gingerpeople.com-20260609T195304Z/screenshots/gingerpeople.com-where-to-buy-the-ginger-people-products-2c7d923c-desktop.png`, `artifacts/gingerpeople.com-20260609T195304Z/text/gingerpeople.com-where-to-buy-the-ginger-people-products-2c7d923c.txt`, `artifacts/gingerpeople.com-20260609T195304Z/screenshots/gingerpeople.com-cart-ad3f1cf6-desktop.png`.

The brand also has underused acquisition and retention assets. The homepage, health blog, FAQ, contact page, and product pages all point to useful themes: nausea relief, motion sickness, cooking, daily wellness, subscriber discounts, recipes, and trade inquiries. This run did not include analytics, heatmaps, mobile capture, or Lighthouse, so the recommendations below are framed as testable hypotheses from selected crawl artifacts only.

## Proposed experiments

### exp-gp-001 - Make PDP purchase handoff explicit

**Pillar:** Conversion  
**Affected surface and URL:** Product detail pages, starting with `https://gingerpeople.com/products/gin-gins-lemon-ginger-chews/`  
**Evidence:** The GIN GINS Lemon PDP contains reviews, product benefits, and "Grab a bag online or look for it in the candy aisle," while manifest product signals show `price_visible: false`, `add_to_cart_visible: false`, and `buy_button_visible: false`; screenshot shows the locator module loading below the product content. Artifacts: `artifacts/gingerpeople.com-20260609T195304Z/text/gingerpeople.com-products-gin-gins-lemon-ginger-chews-da248a63.txt`, `artifacts/gingerpeople.com-20260609T195304Z/screenshots/gingerpeople.com-products-gin-gins-lemon-ginger-chews-da248a63-desktop.png`, `artifacts/gingerpeople.com-20260609T195304Z/manifest.json`.  
**Hypothesis:** If each PDP gives shoppers a clear "Buy online" / "Find near me" choice near the product title, more product-page intent should continue into a retailer or locator action.  
**Primary change:** Add a compact purchase panel near the title with online-retailer buttons, ZIP/store-locator entry, and "also available in store" copy.  
**Primary KPI:** PDP-to-retailer/locator click-through rate.  
**Decision rule:** Ship if the click-through rate improves with no decline in product detail engagement.  
**Expected lift range:** +5-12%  
**Confidence %:** 78%

### exp-gp-002 - Stabilize the Where To Buy locator page

**Pillar:** Conversion  
**Affected surface and URL:** Where To Buy, `https://gingerpeople.com/where-to-buy-the-ginger-people-products/`  
**Evidence:** The page returned 200, but the screenshot shows a Destini Product Locators loading state followed by blog/footer content; extracted text contains blog cards and newsletter copy, not a visible locator result set or online retailer choice. Artifacts: `artifacts/gingerpeople.com-20260609T195304Z/screenshots/gingerpeople.com-where-to-buy-the-ginger-people-products-2c7d923c-desktop.png`, `artifacts/gingerpeople.com-20260609T195304Z/text/gingerpeople.com-where-to-buy-the-ginger-people-products-2c7d923c.txt`.  
**Hypothesis:** If the purchase-intent page reliably exposes store search, online retailers, and product-family filters without depending on a late-loading widget alone, more Where To Buy visitors should reach a buying destination.  
**Primary change:** Add server-rendered fallback content above the locator: ZIP search, "shop online now" cards, popular product filters, and support/contact fallback.  
**Primary KPI:** Where To Buy retailer/locator interaction rate.  
**Decision rule:** Ship if locator or retailer interactions increase without increasing support form starts for purchase-location questions.  
**Expected lift range:** +5-12%  
**Confidence %:** 79%

### exp-gp-003 - Replace `/cart` 404 with purchase recovery

**Pillar:** Performance  
**Affected surface and URL:** Cart route, `https://gingerpeople.com/cart`  
**Evidence:** The selected crawl recorded `/cart` as status 404, and the screenshot shows the "Oops. Captain, we're lost" page with a "Return to Mainland" button. Artifacts: `artifacts/gingerpeople.com-20260609T195304Z/manifest.json`, `artifacts/gingerpeople.com-20260609T195304Z/text/gingerpeople.com-cart-ad3f1cf6.txt`, `artifacts/gingerpeople.com-20260609T195304Z/screenshots/gingerpeople.com-cart-ad3f1cf6-desktop.png`.  
**Hypothesis:** If the cart route becomes a useful retailer-routed recovery page, visitors who land there from old links, browser history, or tracking links should have a clearer path back to products or retailers.  
**Primary change:** Replace the 404 with a branded purchase recovery page containing "Shop products," "Find near me," "Shop online retailers," and customer support links.  
**Primary KPI:** `/cart` onward click rate.  
**Decision rule:** Ship if onward clicks from `/cart` improve and no new crawl errors appear for the route.  
**Expected lift range:** +3-8%  
**Confidence %:** 76%

### exp-gp-004 - Add need-based navigation to the homepage

**Pillar:** Conversion  
**Affected surface and URL:** Homepage, `https://gingerpeople.com/`  
**Evidence:** The homepage hero leads with "Ginger Rescue Digestive Wellness Lozenges" and "SHOP NOW"; the same page includes testimonial cards tied to pregnancy, vertigo, upset stomach, travel, and period nausea, plus product CTAs. Artifact: `artifacts/gingerpeople.com-20260609T195304Z/text/gingerpeople.com-5f9a8666.txt`; visual reference: `artifacts/gingerpeople.com-20260609T195304Z/screenshots/gingerpeople.com-5f9a8666-desktop.png`.  
**Hypothesis:** If first-screen and post-hero navigation routes shoppers by job-to-be-done, more visitors should reach relevant products without decoding the full catalog.  
**Primary change:** Add four homepage mission tiles: "Settle my stomach," "Find ginger candy," "Cook with ginger," and "Buy for my business," each linked to relevant product/content paths.  
**Primary KPI:** Homepage-to-product/category click-through rate.  
**Decision rule:** Ship if mission-tile clicks lift total product/category clicks without reducing clicks on existing hero CTAs.  
**Expected lift range:** +3-7%  
**Confidence %:** 70%

### exp-gp-005 - Build a GIN GINS flavor and strength chooser

**Pillar:** AOV  
**Affected surface and URL:** GIN GINS PDP family, starting with `https://gingerpeople.com/products/gin-gins-lemon-ginger-chews/`  
**Evidence:** The crawl captured multiple GIN GINS product pages, including Lemon, Spicy Apple, Peanut, Spicy Turmeric, Double Strength, Super Strength, and Ginger Spice Drops; product signals show no bundle or upsell visible on these sampled PDPs. Artifacts: `artifacts/gingerpeople.com-20260609T195304Z/manifest.json`, `artifacts/gingerpeople.com-20260609T195304Z/text/gingerpeople.com-products-gin-gins-lemon-ginger-chews-da248a63.txt`.  
**Hypothesis:** If candy shoppers can compare flavor, ginger intensity, and format from each PDP, more of them should choose a multi-flavor or higher-value trial path.  
**Primary change:** Add a "Find your GIN GINS" chooser with flavor, heat/strength, and use-case filters, plus a sampler or retailer-search path for selected flavors.  
**Primary KPI:** Multi-product or sampler interaction rate.  
**Decision rule:** Ship if chooser interactions increase downstream retailer/locator clicks without lowering single-PDP click-through.  
**Expected lift range:** +3-7%  
**Confidence %:** 68%

### exp-gp-006 - Merchandise cooking uses into pantry bundles

**Pillar:** AOV  
**Affected surface and URL:** Crystallized Ginger Chips PDP, `https://gingerpeople.com/products/crystallized-ginger-chips/`  
**Evidence:** The PDP positions the product for cookies, quick breads, carrot cake, fruit cobblers, oatmeal, granola, pancakes, salads, roasted vegetables, tea, and ginger snaps, but manifest product signals show no visible bundle or upsell module. Artifact: `artifacts/gingerpeople.com-20260609T195304Z/text/gingerpeople.com-products-crystallized-ginger-chips-6676f252.txt`; manifest: `artifacts/gingerpeople.com-20260609T195304Z/manifest.json`.  
**Hypothesis:** If cooking-oriented PDPs present recipe-led companion products, shoppers who came for one pantry ingredient should be more likely to continue to a higher-value basket or retailer list.  
**Primary change:** Add "Bake with ginger" and "Pantry starter" modules that pair Crystallized Ginger Chips with relevant recipes and complementary pantry products.  
**Primary KPI:** Companion-product click-through rate.  
**Decision rule:** Ship if companion-product clicks increase and PDP retailer/locator clicks remain stable.  
**Expected lift range:** +3-7%  
**Confidence %:** 67%

### exp-gp-007 - Turn health blog topics into product-guided landing paths

**Pillar:** Acquisition  
**Affected surface and URL:** Health blog, `https://gingerpeople.com/health-blog/`  
**Evidence:** The health blog lists articles such as "Boost Your GLP-1 Naturally," "The Power Of Ginger In Easing Cancer Treatment Side Effects," and "What's The Easiest & Healthiest Way To Consume Ginger Juice?", while the manifest marks the page as content, not a product surface. Artifact: `artifacts/gingerpeople.com-20260609T195304Z/text/gingerpeople.com-health-blog-ea16ba2d.txt`; screenshot: `artifacts/gingerpeople.com-20260609T195304Z/screenshots/gingerpeople.com-health-blog-ea16ba2d-desktop.png`.  
**Hypothesis:** If high-intent health articles connect to compliant product choice modules, organic content visitors should have a clearer path from education to relevant formats.  
**Primary change:** Add article-end modules that route to "Ginger Rescue," "GIN GINS," and "Ginger/Turmeric Juice" choices with careful "support" language and retailer handoff.  
**Primary KPI:** Blog-to-product click-through rate.  
**Decision rule:** Ship if blog-to-product clicks increase without increasing exits from article pages.  
**Expected lift range:** +3-8%  
**Confidence %:** 64%

### exp-gp-008 - Create a FAQ buying assistant

**Pillar:** Acquisition  
**Affected surface and URL:** FAQ, `https://gingerpeople.com/faqs/`  
**Evidence:** The FAQ includes purchase-intent questions: "Where can I find your products?", "Can I buy your products directly?", "Do you have samples available?", and "Do you have coupons?". Artifact: `artifacts/gingerpeople.com-20260609T195304Z/text/gingerpeople.com-faqs-b5a2390d.txt`; screenshot: `artifacts/gingerpeople.com-20260609T195304Z/screenshots/gingerpeople.com-faqs-b5a2390d-desktop.png`.  
**Hypothesis:** If the FAQ answers buying questions with direct product/retailer actions, shoppers using support content should be less likely to dead-end after getting an answer.  
**Primary change:** Add a top-of-FAQ "I want to buy" assistant with retailer search, online retailer cards, coupon/newsletter entry, and links to product families.  
**Primary KPI:** FAQ-to-retailer/product click-through rate.  
**Decision rule:** Ship if FAQ onward clicks increase while contact-form starts for basic purchase questions decline or stay flat.  
**Expected lift range:** +3-7%  
**Confidence %:** 66%

### exp-gp-009 - Make the Ginger Lovers Club a routine builder

**Pillar:** Retention  
**Affected surface and URL:** Homepage/newsletter footer, `https://gingerpeople.com/`  
**Evidence:** The homepage footer invites users to "Join the Ginger Lovers Club" for subscriber-only discounts, early access to new flavors, and recipes; product and content pages repeat the newsletter module. Artifacts: `artifacts/gingerpeople.com-20260609T195304Z/text/gingerpeople.com-5f9a8666.txt`, `artifacts/gingerpeople.com-20260609T195304Z/screenshots/gingerpeople.com-5f9a8666-desktop.png`.  
**Hypothesis:** If the newsletter capture is tied to specific routines or interests, more subscribers should receive relevant follow-up paths that support repeat consideration.  
**Primary change:** Add preference choices at signup: nausea/travel, candy flavors, cooking/recipes, turmeric wellness, and wholesale. Use those choices to trigger tailored welcome flows.  
**Primary KPI:** Newsletter signup rate by preference segment.  
**Decision rule:** Ship if segmented signup rate improves or holds steady while downstream email click-through improves in the test group.  
**Expected lift range:** +2-6%  
**Confidence %:** 63%

### exp-gp-010 - Improve crawl-visible image accessibility and discovery

**Pillar:** Performance  
**Affected surface and URL:** Sitewide rendered pages, starting with `https://gingerpeople.com/`  
**Evidence:** The manifest reports 200 rendered-sample images missing alt text, including 20 missing-alt images on the homepage and 41 on the health blog. Artifact: `artifacts/gingerpeople.com-20260609T195304Z/manifest.json`.  
**Hypothesis:** If key product, blog, and navigation images receive descriptive alt text and redundant image variants are reviewed, accessibility and image-search discoverability should improve without changing the storefront layout.  
**Primary change:** Add descriptive alt text for product packaging, blog thumbnails, locator/recovery illustrations, and recipe imagery; prioritize homepage, PDPs, and health blog.  
**Primary KPI:** Missing-alt count in the crawl and organic image-entry clicks.  
**Decision rule:** Ship if the next crawl reduces missing-alt count by at least 80% on sampled pages with no layout regressions.  
**Expected lift range:** +2-6%  
**Confidence %:** 62%

## Competitor analysis

Competitor sites were not crawled in this run, so this is category-pattern benchmarking, not artifact-backed competitor inspection. The adaptation patterns below are tied back to Ginger People evidence from the selected crawl: retailer-routed PDPs, health/content assets, GIN GINS variety, FAQ buying questions, and the captured Where To Buy route.

| Competitor | Positioning | What the competitor makes easier | Pattern the audited store could adapt |
|---|---|---|---|
| Dramamine | Motion-sickness and nausea relief | Symptom-first entry points for travel and nausea shoppers | Use the homepage testimonials and health-content evidence to create clearer "nausea/travel" routes into Ginger Rescue and GIN GINS products. Evidence: `artifacts/gingerpeople.com-20260609T195304Z/text/gingerpeople.com-5f9a8666.txt`. |
| Tummydrops | Digestive comfort drops and lozenges | Condition-led product selection and format comparison | Add a guided chooser that compares chews, lozenges, tablets, juices, and hard candies by use case. Evidence: multiple sampled PDPs in `artifacts/gingerpeople.com-20260609T195304Z/manifest.json`. |
| Reed's | Ginger beverages and ginger candy | Familiar retailer-led buying paths across ginger products | Make each PDP's online/store handoff more explicit and improve the Where To Buy fallback. Evidence: `artifacts/gingerpeople.com-20260609T195304Z/screenshots/gingerpeople.com-where-to-buy-the-ginger-people-products-2c7d923c-desktop.png`. |
| Chimes Gourmet | Ginger chew flavor variety | Simple flavor-led candy choice | Turn the captured GIN GINS flavor spread into a flavor/strength chooser or sampler path. Evidence: sampled GIN GINS pages in `artifacts/gingerpeople.com-20260609T195304Z/manifest.json`. |

## Technical checks

| Check | Status | Detail |
|---|---|---|
| SSL | Pass | The normalized URL uses HTTPS, and the homepage rendered at `https://gingerpeople.com/`; evidence: `artifacts/gingerpeople.com-20260609T195304Z/manifest.json`. |
| HTTPS redirect | Warn | The selected run loaded the HTTPS final URL, but it did not explicitly prove an HTTP-to-HTTPS redirect chain. |
| Sitemap | Warn | `/sitemap.xml` and `/sitemap_index.xml` returned 403 to the crawler; evidence in manifest technical endpoints. |
| Robots.txt | Warn | `/robots.txt` returned 403 to the crawler; evidence in manifest technical endpoints. |
| Critical pages loading | Warn | Homepage, FAQ, contact, Where To Buy, health blog, and PDPs rendered with 200 statuses, but `/cart` returned 404. |
| Meta tags | Pass | Rendered pages exposed titles and at least one meta description in the selected manifest. |
| Structured data | Pass | JSON-LD structured data was detected on rendered pages in the selected manifest. |
| Favicon | Pass | Favicon links were found on rendered pages in the selected manifest. |
| Mobile friendliness | Warn | Mobile capture was disabled by the required `--no-mobile` crawl, so no mobile layout artifact was collected. |
| Mobile page speed | Warn | No mobile Lighthouse or Core Web Vitals run was collected. |
| Desktop page speed | Warn | Rough Playwright timing was captured, but no Lighthouse performance audit was collected. |
| Broken links | Warn | The manifest lists sampled broken/blocked internal checks and failed malformed FAQ-derived URLs; browser-rendered critical pages still loaded, so this needs follow-up validation. |
| Image optimization | Warn | The manifest reports 200 missing-alt images in rendered samples; byte-size, format, and compression were not measured. |
| Cookie/privacy | Warn | A Privacy Policy link was detected, but consent behavior was not audited. |
| Checkout reachable | Fail | `/cart` returned 404 in the selected crawl, and no checkout route was reached. |
