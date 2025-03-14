from llm_handler import LLMHandler
from page_inspector import PageInspector
from page_interactor import PageInteractor
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin

class PDFScraper:
    def __init__(self, debug=True):
        self.debug = debug
        self.llm = LLMHandler(debug=debug)
        self.inspector = PageInspector(debug=debug)
        self.interactor = PageInteractor(debug=debug)

    def scrape_website(self, url, max_iterations=20):
        pdf_links = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_context().new_page()

            try:
                page.goto(url, wait_until="networkidle", timeout=60000)

                for iteration in range(max_iterations):
                    # Inspect page
                    inspection_results = self.inspector.inspect_page(page)

                    # Get LLM analysis with inspection results
                    analysis = self.llm.analyze_page(
                        page.content(),
                        inspection_results,
                        f"Iteration {iteration + 1}"
                    )

                    if not analysis:
                        break

                    # Collect PDF links
                    pdf_links.extend(self._collect_pdf_links(page, url))

                    # Try interactions
                    if not self._try_suggested_actions(page, analysis):
                        break

            finally:
                browser.close()

        return list(set(pdf_links))

    def _collect_pdf_links(self, page, base_url):
        """Collect PDF links from the page"""
        links = []
        for link in page.query_selector_all('a[href*=".pdf"]'):
            href = link.get_attribute('href')
            if href:
                links.append(urljoin(base_url, href))
        return links

    def _try_suggested_actions(self, page, analysis):
        """Try actions suggested by LLM"""
        actions = sorted(
            analysis['actions'],
            key=lambda x: x['priority'],
            reverse=True
        )

        for action in actions:
            if self.interactor.interact_with_element(page, action):
                return True
        return False
