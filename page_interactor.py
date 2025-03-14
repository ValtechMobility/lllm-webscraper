from typing import Dict, Any, List, Optional
import time

class PageInteractor:
    def __init__(self, debug=True):
        self.debug = debug
        self.tried_elements = set()

        # Common selectors for different types of elements
        self.modal_selectors = {
            'modal': '[role="dialog"], .modal, .popup',
            'close_buttons': [
                'button[aria-label="Close"]',
                'button[aria-label="Schließen"]',
                '.modal-close',
                '.close-button',
                'button:has-text("×")',
                'button:has-text("Schließen")',
                'button:has-text("Close")'
            ],
            'document_tabs': [
                'button:has-text("Dokumente")',
                'button:has-text("Details")',
                'button:has-text("Unterlagen")',
                '[role="tab"]'
            ]
        }

    def interact_with_element(self, page, action: Dict[str, Any]) -> bool:
        """Main method to handle element interaction"""
        try:
            # Reset view before interaction
            if not self._reset_view(page):
                return False

            # Find and interact with element
            element = self._find_element(page, action)
            if element:
                return self._perform_interaction(page, element)

            return False

        except Exception as e:
            if self.debug:
                print(f"Interaction error: {e}")
            return False

    def _reset_view(self, page) -> bool:
        """Reset page to initial state"""
        try:
            # Close any open modals
            if self._is_modal_open(page):
                self._close_modal(page)
                time.sleep(1)

            # Refresh page if we've tried too many elements
            if len(self.tried_elements) > 5:
                if self.debug:
                    print("Refreshing page to reset state...")
                page.reload()
                page.wait_for_load_state("networkidle")
                self.tried_elements.clear()
                time.sleep(2)

            return True

        except Exception as e:
            if self.debug:
                print(f"Error resetting view: {e}")
            return False

    def _find_element(self, page, action: Dict[str, Any]) -> Optional[Any]:
        """Find element to interact with based on action"""
        try:
            # Generate element ID to track what we've tried
            element_id = f"{action.get('element_type')}:{action.get('identifier')}"

            if element_id in self.tried_elements:
                if self.debug:
                    print(f"Already tried element: {element_id}")
                return None

            # Try different strategies to find the element
            element = self._try_element_selectors(page, action)

            if element:
                self.tried_elements.add(element_id)
                if self.debug:
                    print(f"Found element: {element_id}")

            return element

        except Exception as e:
            if self.debug:
                print(f"Error finding element: {e}")
            return None

    def _try_element_selectors(self, page, action: Dict[str, Any]) -> Optional[Any]:
        """Try different selector strategies to find element"""
        selectors = self._generate_selectors(action)

        for selector in selectors:
            try:
                if self.debug:
                    print(f"Trying selector: {selector}")

                elements = page.query_selector_all(selector)
                if elements:
                    # Return first visible element
                    for element in elements:
                        if element.is_visible():
                            return element

            except Exception as e:
                if self.debug:
                    print(f"Selector failed: {selector}, Error: {e}")
                continue

        return None

    def _generate_selectors(self, action: Dict[str, Any]) -> List[str]:
        """Generate list of possible selectors based on action"""
        identifier = action.get('identifier', '')
        element_type = action.get('element_type', '')

        selectors = []

        # Direct selector if provided
        if identifier.startswith(('.', '#', '[')):
            selectors.append(identifier)

        # Text-based selectors
        selectors.extend([
            f"{element_type}:has-text('{identifier}')",
            f"text={identifier}",
            f"[title*='{identifier}']",
            f"[aria-label*='{identifier}']"
        ])

        # Type-specific selectors
        if element_type == 'button':
            selectors.extend([
                'button, [role="button"]',
                '[class*="btn"]'
            ])
        elif element_type == 'row':
            selectors.append('tr')

        return selectors

    def _perform_interaction(self, page, element) -> bool:
        """Perform the actual interaction with the element"""
        try:
            # Ensure element is visible and scrolled into view
            if not element.is_visible():
                return False

            element.scroll_into_view_if_needed()
            time.sleep(1)

            # Click the element
            element.click()
            time.sleep(2)

            # Handle any resulting modal
            if self._is_modal_open(page):
                return self._handle_modal(page)

            return True

        except Exception as e:
            if self.debug:
                print(f"Error performing interaction: {e}")
            return False

    def _is_modal_open(self, page) -> bool:
        """Check if a modal is currently open"""
        return bool(page.query_selector(self.modal_selectors['modal']))

    def _close_modal(self, page) -> bool:
        """Close an open modal"""
        try:
            # Try close buttons
            for selector in self.modal_selectors['close_buttons']:
                close_button = page.query_selector(selector)
                if close_button and close_button.is_visible():
                    close_button.click()
                    time.sleep(1)
                    return True

            # Try escape key if no button found
            page.keyboard.press('Escape')
            time.sleep(1)
            return True

        except Exception as e:
            if self.debug:
                print(f"Error closing modal: {e}")
            return False

    def _handle_modal(self, page) -> bool:
        """Handle interaction with a modal dialog"""
        try:
            modal = page.query_selector(self.modal_selectors['modal'])
            if not modal:
                return False

            # Try to find and click document tabs
            for tab_selector in self.modal_selectors['document_tabs']:
                tab = modal.query_selector(tab_selector)
                if tab and tab.is_visible():
                    tab.click()
                    time.sleep(2)

                    # Check if click revealed any PDF links
                    pdf_links = page.query_selector_all('a[href*=".pdf"]')
                    if pdf_links:
                        if self.debug:
                            print(f"Found {len(pdf_links)} PDF links in modal")
                        return True

            # If no PDFs found, close modal
            return self._close_modal(page)

        except Exception as e:
            if self.debug:
                print(f"Error handling modal: {e}")
            return False
