from typing import Dict, List, Any

class PageInspector:
    def __init__(self, debug=True):
        self.debug = debug
        self.interesting_selectors = [
            '[class*="info"]',
            '[class*="detail"]',
            '[class*="dokument"]',
            '[title*="info"]',
            '[title*="detail"]',
            '[aria-label*="info"]',
            '[aria-label*="detail"]',
            'i.fa-info',
            '.info-icon'
        ]

    def inspect_page(self, page) -> Dict[str, Any]:
        """Main inspection method that returns all page information"""
        inspection_results = {
            "table_rows": self._inspect_table_rows(page),
            "buttons": self._inspect_buttons(page),
            "interesting_elements": self._inspect_interesting_elements(page),
            "pdf_links": self._find_pdf_links(page)
        }

        if self.debug:
            self._print_inspection_results(inspection_results)

        return inspection_results

    def _get_element_attributes(self, page, element) -> Dict[str, str]:
            """Get all attributes of an element"""
            try:
                return page.evaluate("""
                    (element) => {
                        const attrs = {};
                        for (const attr of element.attributes) {
                            attrs[attr.name] = attr.value;
                        }
                        return attrs;
                    }
                """, element)
            except Exception:
                return {}

    def _get_element_info(self, page, element) -> Dict[str, Any]:
        """Get comprehensive information about an element"""
        try:
            return {
                "text": element.text_content().strip(),
                "attributes": self._get_element_attributes(page, element),
                "position": element.bounding_box(),
                "is_visible": element.is_visible(),
                "tag_name": page.evaluate("el => el.tagName.toLowerCase()", element)
            }
        except Exception as e:
            if self.debug:
                print(f"Error getting element info: {e}")
            return {}

    def _inspect_table_rows(self, page) -> List[Dict[str, Any]]:
        """Inspect all table rows and their contents"""
        rows_info = []
        rows = page.query_selector_all('tr')

        for row in rows:
            try:
                buttons = row.query_selector_all('button, [role="button"]')
                links = row.query_selector_all('a')

                row_info = {
                    **self._get_element_info(page, row),
                    "buttons": [self._get_element_info(page, btn) for btn in buttons],
                    "links": [self._get_element_info(page, link) for link in links]
                }
                rows_info.append(row_info)

            except Exception as e:
                if self.debug:
                    print(f"Error inspecting row: {e}")
                continue

        return rows_info

    def _inspect_buttons(self, page) -> List[Dict[str, Any]]:
        """Inspect all buttons on the page"""
        buttons_info = []
        buttons = page.query_selector_all('button, [role="button"]')

        for button in buttons:
            try:
                button_info = self._get_element_info(page, button)
                buttons_info.append(button_info)
            except Exception as e:
                if self.debug:
                    print(f"Error inspecting button: {e}")
                continue

        return buttons_info

    def _inspect_interesting_elements(self, page) -> Dict[str, List[Dict[str, Any]]]:
        """Inspect elements matching interesting selectors"""
        interesting_elements = {}

        for selector in self.interesting_selectors:
            try:
                elements = page.query_selector_all(selector)
                interesting_elements[selector] = [
                    self._get_element_info(page, el) for el in elements
                ]
            except Exception as e:
                if self.debug:
                    print(f"Error inspecting elements for selector {selector}: {e}")
                interesting_elements[selector] = []

        return interesting_elements

    def _find_pdf_links(self, page) -> List[Dict[str, Any]]:
        """Find all PDF links on the page"""
        pdf_links = []
        links = page.query_selector_all('a[href*=".pdf"]')

        for link in links:
            try:
                link_info = self._get_element_info(page, link)
                link_info['href'] = link.get_attribute('href')
                pdf_links.append(link_info)
            except Exception as e:
                if self.debug:
                    print(f"Error inspecting PDF link: {e}")
                continue

        return pdf_links

    def _print_inspection_results(self, results: Dict[str, Any]) -> None:
        """Print inspection results in a readable format"""
        print("\n=== PAGE INSPECTION RESULTS ===")

        print("\nTABLE ROWS:")
        for idx, row in enumerate(results['table_rows']):
            print(f"\nRow {idx}:")
            print(f"  Text: {row['text'][:100]}...")
            print(f"  Buttons: {len(row['buttons'])}")
            print(f"  Links: {len(row['links'])}")

        print("\nBUTTONS:")
        for idx, button in enumerate(results['buttons']):
            print(f"\nButton {idx}:")
            print(f"  Text: {button['text']}")
            print(f"  Attributes: {button['attributes']}")

        print("\nINTERESTING ELEMENTS:")
        for selector, elements in results['interesting_elements'].items():
            print(f"\nSelector '{selector}': {len(elements)} elements")
            for idx, element in enumerate(elements):
                print(f"  Element {idx}:")
                print(f"    Text: {element['text']}")
                print(f"    Attributes: {element['attributes']}")

        print("\nPDF LINKS:")
        for idx, link in enumerate(results['pdf_links']):
            print(f"\nPDF Link {idx}:")
            print(f"  Text: {link['text']}")
            print(f"  href: {link['href']}")

        print("\n=== END OF INSPECTION ===\n")
