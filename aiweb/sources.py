"""
The published figures this page stands on, one source per figure.

None of these numbers can be recomputed from a public dataset: each is copied from the report, filing or
survey named beside it, as read on 2026-11-14 (the lane's research notes, 03 RESEARCH/nov-2026-batch3/ai-web/
research/w1-01..05, give the URL and the method for every row). The build reads these tables and never types a
number of its own. Map positions are this page's judgement and are marked so.
"""

# key: (value, unit, period, source key). Values are as published; rounding happens in update_page.py.
FIG = {
    # --- the forecast that opens the page
    "gartner_drop":     (25, "percent fall in traditional search engine volume", "by 2026", "gartner2024"),
    "goog_rev":         (63.35, "USD billion, Google Search & other revenue", "Q3 2026", "alphabet_q3_2026"),
    "goog_rev_prev":    (56.57, "USD billion, same", "Q3 2025", "alphabet_q3_2026"),
    # --- hollowed web
    "pew_n":            (900, "US adults whose browsing was tracked", "March 2025", "pew2025_clicks"),
    "pew_searches":     (68879, "Google searches in the sample", "March 2025", "pew2025_clicks"),
    "pew_click_ai":     (8, "percent of searches with an AI summary that led to a click on a result", "March 2025", "pew2025_clicks"),
    "pew_click_no":     (15, "percent of searches without one", "March 2025", "pew2025_clicks"),
    "pew_click_in":     (1, "percent of searches with a summary that led to a click inside it", "March 2025", "pew2025_clicks"),
    "zero_2026":        (68.01, "percent of US Google searches ending without a click", "Jan-Apr 2026", "sparktoro2026"),
    "zero_2024":        (60.45, "same", "2024", "sparktoro2026"),
    "zero_datos":       (27.2, "percent of US desktop Google searches ending without a click (Datos panel)", "March 2025", "datos_2025"),
    "chartbeat_sites":  (2500, "news sites in the Chartbeat sample (more than)", "2025", "reuters_trends_2026"),
    "chartbeat_drop":   (33, "percent fall in Google search traffic to publishers, worldwide", "Nov 2024 to Nov 2025", "reuters_trends_2026"),
    "chartbeat_us":     (38, "same, United States", "Nov 2024 to Nov 2025", "reuters_trends_2026"),
    "chartbeat_small":  (60, "percent fall in search pageviews, small sites", "Dec 2024 to Dec 2025", "chartbeat_q1_2026"),
    "chartbeat_large":  (22, "percent fall, large sites", "Dec 2024 to Dec 2025", "chartbeat_q1_2026"),
    "ai_ref_share":     (1, "percent of publisher pageviews from AI platforms (under)", "Jan 2024 to Feb 2026", "chartbeat_q1_2026"),
    "crawl_google":     (5.4, "HTML crawls per referred visit, Google", "July 2025", "cloudflare_crawl_2025"),
    "crawl_openai":     (1091, "same, OpenAI", "July 2025", "cloudflare_crawl_2025"),
    "crawl_anthropic":  (38066, "same, Anthropic", "July 2025", "cloudflare_crawl_2025"),
    "graphite_sites":   (40000, "US sites in the sample (more than)", "2025", "graphite_seo_2026"),
    "graphite_traffic": (2.5, "percent fall in organic Google traffic", "2025 vs 2024", "graphite_seo_2026"),
    "graphite_top10":   (1.6, "percent average rise in organic Google traffic, ten largest sites", "2025 vs 2024", "graphite_seo_2026"),
    "wiki_drop":        (8, "percent fall in human page views (about)", "recent months of 2025 vs the same months of 2024", "wikimedia2025"),
    # --- agentic web
    "bot_share":        (53, "percent of traffic from automated software", "2025", "imperva2026"),
    "bot_share_prev":   (51, "same", "2024", "imperva2026"),
    "cf_human_html":    (47, "percent of HTML requests made by humans", "snapshot, 2 Dec 2025", "cloudflare_yir_2025"),
    "cf_ai_bots":       (4.2, "percent of HTML requests from declared AI bots (average)", "Jan-Dec 2025", "cloudflare_yir_2025"),
    "cf_googlebot":     (4.5, "percent of HTML requests from Googlebot (average)", "Jan-Dec 2025", "cloudflare_yir_2025"),
    "mcp_servers":      (10000, "active public MCP servers (more than)", "Dec 2025", "anthropic_mcp_2025"),
    "mck_lo":           (3, "USD trillion of commerce orchestrated by agents, low", "by 2030", "mckinsey2025"),
    "mck_hi":           (5, "same, high", "by 2030", "mckinsey2025"),
    "agent_browse":     (85.2, "percent of agent requests to product or search pages", "Oct 2026", "human_oct_2026"),
    "agent_checkout":   (1.9, "percent of agent requests to checkout or payment", "Oct 2026", "human_oct_2026"),
    "forrester_trust":  (24, "percent of US online adults who trust agents with routine purchases", "2025", "forrester2025"),
    # --- closing web
    "dpi_before":       (1, "percent of tokens restricted by robots.txt (about)", "mid-2023", "longpre2024"),
    "dpi_after_lo":     (5, "same, low", "April 2024", "longpre2024"),
    "dpi_after_hi":     (7, "same, high", "April 2024", "longpre2024"),
    "dpi_head_lo":      (20, "percent of tokens from the most important domains, low", "April 2024", "longpre2024"),
    "dpi_head_hi":      (33, "same, high", "April 2024", "longpre2024"),
    "news_block":       (79, "percent of top US and UK news sites blocking at least one AI training bot (about)", "late 2025", "buzzstream2025"),
    "top1m_block":      (10.6, "percent of the top one million websites that fully block GPTBot", "Sept 2025", "bouchaud2025"),
    "deals":            (91, "publicly announced AI content-licensing deals", "Jan 2023 to June 2026", "kelly2026"),
    "newscorp":         (250, "USD million over five years, News Corp and OpenAI (reported)", "May 2024", "newscorp_openai"),
    "nyt_lo":           (20, "USD million a year, Amazon and The New York Times, low (reported)", "July 2025", "nyt_amazon"),
    "nyt_hi":           (25, "same, high", "July 2025", "nyt_amazon"),
    "nyt_share":        (1, "percent of the paper's 2024 revenue (about)", "2024", "nyt_amazon"),
    "tollbit":          (30, "percent of AI bot scrapes that bypassed robots.txt permissions (about)", "Q4 2025", "tollbit2026"),
    "lawsuits":         (157, "US copyright suits against AI companies", "29 Oct 2026", "suits2026"),
    "bartz":            (1.5, "USD billion, Anthropic settlement with authors", "final approval July 2026", "bartz2026"),
    # --- synthetic flood
    "europol":          (90, "percent of online content 'may be synthetically generated' (as much as)", "by 2026", "europol2022"),
    "graphite_articles":(49.9, "percent of new English articles mostly AI-written", "Q1 2026", "graphite_ai_2026"),
    "graphite_flat":    (5, "quarters the share has stayed near half", "to Q1 2026", "graphite_ai_2026"),
    "graphite_serp":    (14, "percent of Google results AI-generated", "June 2025", "graphite_serp_2025"),
    "graphite_top":     (7, "percent of first results AI-generated", "June 2025", "graphite_serp_2025"),
    "ng_2023":          (49, "AI content-farm news sites identified", "early May 2023", "newsguard_2023"),
    "ng_2026":          (3749, "same", "June 2026", "newsguard"),
    # --- adaptation
    "g_visits":         (88.4, "billion visits a month, google.com", "Oct 2026", "similarweb2026"),
    "c_visits":         (6.0, "billion visits a month, chatgpt.com", "Oct 2026", "similarweb2026"),
    "ri_ai_2025":       (34, "percent of online adults using standalone generative AI weekly (six-country average)", "2025", "reuters_genai_2026"),
    "ri_ai_2026":       (51, "same", "2026", "reuters_genai_2026"),
    "ri_saw":           (57, "percent who saw AI answers in a search engine in the last week (nine-country figure)", "2026", "reuters_genai_2026"),
    # --- forecasters
    "elon_n":           (301, "experts canvassed", "Dec 2024 to Feb 2025", "elon2025"),
    "elon_better":      (16, "percent: mostly better", "by 2035", "elon2025"),
    "elon_worse":       (23, "percent: mostly worse", "by 2035", "elon2025"),
    "elon_mixed":       (50, "percent: equal measure", "by 2035", "elon2025"),
    "pew_exp":          (56, "percent of AI experts expecting a positive impact on the US over 20 years", "2024", "pew2025_experts"),
    "pew_pub":          (17, "percent of the US public", "2024", "pew2025_experts"),
    "ri_pub_drop":      (43, "percent fall in search traffic expected by news executives within three years", "Jan 2026", "reuters_trends_2026"),
    "ri_pub_n":         (280, "news executives surveyed", "late 2025", "reuters_trends_2026"),
    "ri_pub_answered":  (268, "of them answering the search-traffic question", "late 2025", "reuters_trends_2026"),
}

# Where each source lives. Cited on the page through add_citations.PAGES["aiweb.html"]; listed here so the
# build can check that every figure names a known source.
REFS = {
    "gartner2024": "https://www.gartner.com/en/newsroom/press-releases/2024-02-19-gartner-predicts-search-engine-volume-will-drop-25-percent-by-2026-due-to-ai-chatbots-and-other-virtual-agents",
    "alphabet_q3_2026": "https://www.sec.gov/Archives/edgar/data/0001652044/000165204426000080/googexhibit991q32026.htm",
    "pew2025_clicks": "https://www.pewresearch.org/short-reads/2025/07/22/google-users-are-less-likely-to-click-on-links-when-an-ai-summary-appears-in-the-results/",
    "sparktoro2026": "https://sparktoro.com/blog/in-2026-less-than-one-third-of-google-searches-still-send-a-click/",
    "reuters_trends_2026": "https://reutersinstitute.politics.ox.ac.uk/journalism-media-and-technology-trends-and-predictions-2026",
    "chartbeat_q1_2026": "https://lp.chartbeat.com/hubfs/Chartbeat-Report-2026Q1.pdf",
    "cloudflare_crawl_2025": "https://blog.cloudflare.com/crawlers-click-ai-bots-training/",
    "graphite_seo_2026": "https://graphite.io/five-percent/debunking-the-myth-that-seo-traffic-has-dramatically-declined",
    "datos_2025": "https://searchengineland.com/zero-click-searches-up-organic-clicks-down-456660",
    "wikimedia2025": "https://diff.wikimedia.org/2025/10/17/new-user-trends-on-wikipedia/",
    "imperva2026": "https://www.imperva.com/blog/bad-bot-report-2026-bots-agentic-age/",
    "cloudflare_yir_2025": "https://blog.cloudflare.com/radar-2025-year-in-review",
    "anthropic_mcp_2025": "https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation",
    "mckinsey2025": "https://www.mckinsey.com/capabilities/quantumblack/our-insights/europes-agentic-commerce-moment-decision-influence-is-here-execution-is-coming",
    "human_oct_2026": "https://www.humansecurity.com/learn/blog/october-2026-agentic-traffic/",
    "forrester2025": "https://www.forrester.com/report/many-us-consumers-believe-in-agentic-commerce-but-few-trust-it-to-make-purchases/RES188737",
    "openai_checkout": "https://openai.com/index/buy-it-in-chatgpt/",
    "ms_build_2025": "https://blogs.microsoft.com/blog/2025/05/19/microsoft-build-2025-the-age-of-ai-agents-and-building-the-open-agentic-web/",
    "google_ap2": "https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol",
    "longpre2024": "https://arxiv.org/abs/2407.14933",
    "buzzstream2025": "https://www.buzzstream.com/blog/publishers-block-ai-study/",
    "bouchaud2025": "https://arxiv.org/html/2510.09031v1",
    "kelly2026": "https://mediaandthemachine.substack.com/p/ai-content-licensing-deals-june-2026",
    "newscorp_openai": "https://www.engadget.com/openai-will-reportedly-pay-250-million-to-put-news-corps-journalism-in-chatgpt-214615249.html",
    "nyt_amazon": "https://www.engadget.com/ai/the-new-york-times-and-amazons-ai-licensing-deal-is-reportedly-worth-up-to-25-million-per-year-135523853/",
    "tollbit2026": "https://digiday.com/media/in-graphic-detail-ai-licensing-deals-protection-measures-arent-slowing-web-scraping/",
    "suits2026": "https://chatgptiseatingtheworld.com/2026/10/29/latest-map-of-u-s-copyright-suits-v-ai-companies-total-157/",
    "bartz2026": "https://news.bloomberglaw.com/ip-law/anthropic-authors-1-5-billion-deal-receives-final-approval",
    "europol2022": "https://www.europol.europa.eu/publications-events/publications/facing-reality-law-enforcement-and-challenge-of-deepfakes",
    "graphite_ai_2026": "https://graphite.io/five-percent/research/ai-now-writes-as-many-online-articles-as-humans-do",
    "graphite_serp_2025": "https://graphite.io/five-percent/ai-content-in-search-and-llms",
    "newsguard": "https://www.newsguardtech.com/special-reports/ai-tracking-center/",
    "newsguard_2023": "https://www.newsguardtech.com/press/newsguard-now-identifies-125-news-and-information-websites-generated-by-ai-develops-framework-for-defining-unreliable-ai-generated-news-and-information-sources/",
    "shumailov2024": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11269175/",
    "similarweb2026": "https://www.similarweb.com/blog/research/market-research/most-visited-websites/",
    "reuters_genai_2026": "https://reutersinstitute.politics.ox.ac.uk/generative-ai-and-news-report-2026-standalone-tools-information-infrastructure",
    "elon2025": "https://imaginingthedigitalfuture.org/reports-and-publications/being-human-in-2035/being-human-in-2035-research-methodologies-and-topline-findings/",
    "pew2025_experts": "https://www.pewresearch.org/internet/2025/04/03/how-the-us-public-and-ai-experts-view-artificial-intelligence/",
    "google_clicks_2025": "https://blog.google/products-and-platforms/products/search/ai-search-driving-more-queries-higher-quality-clicks/",
}

# The map. Positions are this page's judgement (0-100 on each axis), not measurements. Across: the share of requests
# made by software, which today's 53 percent measures. Up: the share of what readers are shown that machines wrote,
# which Graphite's 14 percent of Google results measures. Each future is placed against today, so none sits to the
# left of or below it: no forecast has machine traffic or machine-written results falling.
SCENARIOS = [
    {"key": "adapt",  "name": "Adaptation",      "x": 60, "y": 22, "section": "adapt",
     "line": "the web absorbs AI as it absorbed search and phones"},
    {"key": "hollow", "name": "Hollowed web",    "x": 72, "y": 40, "section": "hollow",
     "line": "AI answers replace the visit"},
    {"key": "agent",  "name": "Agentic web",     "x": 88, "y": 55, "section": "agents",
     "line": "agents browse and buy for people"},
    {"key": "flood",  "name": "Synthetic flood", "x": 62, "y": 85, "section": "flood",
     "line": "machines write most of what is published and shown"},
]
# Today, measured: x from the automated share of traffic; y from the AI share of what Google shows (the axis) and,
# as a second marker, of what is published. Keys into FIG.
TODAY = {"x": "bot_share", "y_published": "graphite_articles", "y_shown": "graphite_serp"}
# The closing-web strip: two measured points on a 0-100 scale. Two different measures (one crawler fully blocked
# across all top sites; at least one crawler blocked by news sites), so the gap is partly definitional.
STRIP = [("top1m_block", "the million most-visited sites, fully blocking OpenAI's crawler"),
         ("news_block", "top US and UK news sites, blocking at least one AI training crawler")]

# Forecasts set against what has been measured since (the scorecard table).
SCORECARD = [
    {"forecast": "Traditional search volume falls {gartner_drop} percent by 2026",
     "by": "Gartner, February 2024",
     "measured": "Google's query growth the fastest in five years; search revenue up {goog_growth} percent (Q3 2026)",
     "verdict": "Not met"},
    {"forecast": "As much as {europol} percent of online content synthetic by 2026",
     "by": "Europol report, 2022, citing one author",
     "measured": "{graphite_articles} percent of new English articles (early 2026); {graphite_serp} percent of Google results (mid-2025)",
     "verdict": "Not met, and no data behind it"},
    {"forecast": "Search traffic to news sites falls {ri_pub_drop} percent within three years",
     "by": "News executives, January 2026 ({ri_pub_answered} of {ri_pub_n} answering)",
     "measured": "Already down {chartbeat_drop} percent in the year to November 2025, before the forecast was made (Chartbeat)",
     "verdict": "Too early to judge"},
]
