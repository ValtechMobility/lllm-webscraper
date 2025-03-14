from typing import Dict, Any, Optional
import requests
import json
import re

class LLMHandler:
    def __init__(self, model="deepseek-v2:latest", debug=True):
        self.model = model
        self.ollama_url = "http://localhost:11434/api/generate"
        self.debug = debug

    def analyze_page(self, page_content: str, inspection_results: Dict[str, Any], current_state: str = "initial") -> Optional[Dict[str, Any]]:
        """Analyze page using LLM with both HTML content and inspection results"""
        if not self.test_connection():
            return None

        # Create structured context from inspection results
        context = self._create_context(inspection_results)
        prompt = self._create_prompt(context, current_state)

        return self._get_llm_response(prompt)

    def _create_context(self, inspection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create structured context from inspection results"""
        context = {
            "table_rows": [],
            "buttons": [],
            "interesting_elements": [],
            "pdf_links": []
        }

        # Process table rows
        for row in inspection_results["table_rows"]:
            context["table_rows"].append({
                "text": row["text"][:100],  # Limit text length
                "has_buttons": len(row["buttons"]) > 0,
                "has_links": len(row["links"]) > 0
            })

        # Process buttons
        for button in inspection_results["buttons"]:
            context["buttons"].append({
                "text": button["text"],
                "is_visible": button.get("is_visible", False),
                "classes": button.get("attributes", {}).get("class", "")
            })

        # Process interesting elements
        for selector, elements in inspection_results["interesting_elements"].items():
            for element in elements:
                context["interesting_elements"].append({
                    "type": selector,
                    "text": element["text"],
                    "is_visible": element.get("is_visible", False)
                })

        # Process PDF links
        context["pdf_links"] = [
            {"text": link["text"], "href": link["href"]}
            for link in inspection_results["pdf_links"]
        ]

        return context

    def _create_prompt(self, context: Dict[str, Any], current_state: str) -> str:
        """Create a detailed prompt using inspection results"""
        json_format_example = '''
        {
            "actions": [
                {
                    "element_type": "button/row/link",
                    "identifier": "exact text or distinctive attribute",
                    "reason": "why this element looks promising",
                    "priority": 1-5 (5 highest)
                }
            ],
            "analysis": "your reasoning about the page structure and suggested approach"
        }
        '''

        return f"""
        Analyze this webpage for potential paths to PDF documents. You are helping to find tender/bid documents
        ("Ausschreibungsunterlagen", "Vergabeunterlagen") on a German procurement platform.

        Current state: {current_state}

        Page Structure:
        1. Table Rows Found: {len(context['table_rows'])}
        2. Interactive Buttons: {len(context['buttons'])}
        3. Interesting Elements: {len(context['interesting_elements'])}
        4. Current PDF Links: {len(context['pdf_links'])}

        Detailed Elements:

        Tables:
        {self._format_table_rows(context['table_rows'])}

        Buttons:
        {self._format_buttons(context['buttons'])}

        Interesting Elements:
        {self._format_interesting_elements(context['interesting_elements'])}

        Strategy:
        1. Look for info buttons ("i") or detail buttons near tender titles
        2. Check for elements containing words like "Unterlagen", "Dokumente", "Details"
        3. Consider table rows that might be clickable to reveal more information
        4. Examine any elements marked as information or detail indicators

        Return a JSON response in this exact format:
        {json_format_example}

        Focus on finding interactive elements that could lead to document sections.
        """

    def _format_table_rows(self, rows: list) -> str:
        return "\n".join(
            f"- Row: {row['text']} "
            f"(Has buttons: {row['has_buttons']}, Has links: {row['has_links']})"
            for row in rows
        )

    def _format_buttons(self, buttons: list) -> str:
        return "\n".join(
            f"- Button: {button['text']} "
            f"(Visible: {button['is_visible']}, Classes: {button['classes']})"
            for button in buttons
        )

    def _format_interesting_elements(self, elements: list) -> str:
        return "\n".join(
            f"- {element['type']}: {element['text']} "
            f"(Visible: {element['is_visible']})"
            for element in elements
        )

    def _get_llm_response(self, prompt: str) -> Optional[Dict[str, Any]]:
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }

            response = requests.post(self.ollama_url, json=payload)
            response_json = response.json()

            llm_text = response_json.get('response', '')
            json_match = re.search(r'\{.*\}', llm_text, re.DOTALL)

            if json_match:
                return json.loads(json_match.group(0))

            return {"actions": [], "analysis": "Failed to parse LLM response"}

        except Exception as e:
            if self.debug:
                print(f"Error in LLM response: {e}")
            return {"actions": [], "analysis": f"Error: {str(e)}"}

    def test_connection(self) -> bool:
        """Test if Ollama is responding"""
        try:
            requests.get("http://localhost:11434/api/version")
            return True
        except Exception as e:
            if self.debug:
                print(f"Failed to connect to Ollama: {e}")
            return False
