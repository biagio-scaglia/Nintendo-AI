"""
Wikipedia Agent Module
Provides structured access to Wikipedia for AI integration
"""

import re
import logging
from typing import Dict, List, Optional
import wikipediaapi

logger = logging.getLogger(__name__)


class WikiAgent:
    """
    Agent for querying Wikipedia with structured responses.
    Designed for integration with AI models like Qwen3-8B.
    """
    
    def __init__(self, lang: str = "it"):
        """
        Initialize Wikipedia API client.
        
        Args:
            lang: Language code (default: "it" for Italian)
        """
        self.lang = lang
        self.wiki = wikipediaapi.Wikipedia(
            language=lang,
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent="Nintendo-AI/1.0"
        )
        logger.info(f"WikiAgent initialized for language: {lang}")
    
    def search(self, query: str) -> List[str]:
        """
        Search Wikipedia for pages matching the query.
        
        Args:
            query: Search query string
            
        Returns:
            List of page titles (max 10 results)
        """
        try:
            search_results = self.wiki.search(query, results=10)
            titles = [page for page in search_results]
            logger.info(f"Found {len(titles)} results for query: {query}")
            return titles
        except Exception as e:
            logger.error(f"Error searching Wikipedia: {e}")
            return []
    
    def get_page(self, title: str) -> Dict:
        """
        Get full page content from Wikipedia.
        
        Args:
            title: Exact Wikipedia page title
            
        Returns:
            Dictionary with:
                - title: Page title
                - summary: First paragraph (summary)
                - full_text: Complete page text
                - sections: List of section titles
            Or error dict if page not found/empty
        """
        try:
            page = self.wiki.page(title)
            
            if not page.exists():
                logger.warning(f"Page not found: {title}")
                return {"error": "no_results"}
            
            # Extract summary (first paragraph)
            summary = ""
            full_text = page.text
            
            if full_text:
                # Get first paragraph (before first double newline or first section)
                paragraphs = full_text.split("\n\n")
                if paragraphs:
                    summary = paragraphs[0].strip()
                    # Limit summary length
                    if len(summary) > 500:
                        summary = summary[:500] + "..."
            else:
                logger.warning(f"Page has no content: {title}")
                return {"error": "empty_page"}
            
            # Extract sections
            sections = []
            if hasattr(page, 'sections') and page.sections:
                for section in page.sections:
                    if section.title:
                        sections.append(section.title)
            
            # If no sections found, try to extract from text
            if not sections:
                section_pattern = r'^==+\s*(.+?)\s*==+'
                matches = re.findall(section_pattern, full_text, re.MULTILINE)
                sections = [match.strip() for match in matches[:20]]  # Limit to 20 sections
            
            return {
                "title": page.title,
                "summary": summary,
                "full_text": full_text,
                "sections": sections
            }
            
        except Exception as e:
            logger.error(f"Error getting page '{title}': {e}")
            return {"error": "no_results"}
    
    def _extract_keywords(self, question: str) -> List[str]:
        """
        Extract keywords from a natural language question.
        Simple keyword extraction (can be enhanced with NLP).
        
        Args:
            question: Natural language question
            
        Returns:
            List of potential keywords
        """
        # Remove common question words
        stop_words = {
            "chi", "cosa", "che", "quale", "quando", "dove", "come", "perché",
            "è", "sono", "ha", "hanno", "era", "erano", "sarà", "saranno",
            "il", "la", "lo", "gli", "le", "un", "una", "uno", "di", "a", "da",
            "in", "su", "per", "con", "tra", "fra", "del", "della", "dei", "delle"
        }
        
        # Clean and split
        question_lower = question.lower()
        # Remove punctuation
        question_clean = re.sub(r'[^\w\s]', ' ', question_lower)
        words = question_clean.split()
        
        # Filter stop words and short words
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Also try to extract potential entity names (capitalized words)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', question)
        keywords.extend([w.lower() for w in capitalized if len(w) > 2])
        
        return list(set(keywords))  # Remove duplicates
    
    def _find_best_match(self, question: str, keywords: List[str]) -> Optional[str]:
        """
        Find the best matching Wikipedia page for a question.
        
        Args:
            question: Original question
            keywords: Extracted keywords
            
        Returns:
            Best matching page title or None
        """
        # Try direct search with full question
        results = self.search(question)
        if results:
            return results[0]
        
        # Try with keywords
        if keywords:
            # Try longest keyword first (likely to be the main entity)
            sorted_keywords = sorted(keywords, key=len, reverse=True)
            for keyword in sorted_keywords[:3]:  # Try top 3 keywords
                results = self.search(keyword)
                if results:
                    return results[0]
        
        return None
    
    def _find_relevant_section(self, page_text: str, keywords: List[str]) -> Optional[str]:
        """
        Find the most relevant section based on keywords.
        
        Args:
            page_text: Full page text
            keywords: Extracted keywords
            
        Returns:
            Section title or None
        """
        if not keywords:
            return None
        
        # Extract all sections
        section_pattern = r'^==+\s*(.+?)\s*==+'
        sections = re.finditer(section_pattern, page_text, re.MULTILINE)
        
        best_section = None
        best_score = 0
        
        for match in sections:
            section_title = match.group(1).strip()
            section_start = match.start()
            
            # Get section content (until next section or end)
            next_match = None
            for next_s in re.finditer(section_pattern, page_text[section_start + 1:], re.MULTILINE):
                next_match = next_s
                break
            
            if next_match:
                section_end = section_start + next_match.start()
                section_content = page_text[section_start:section_end].lower()
            else:
                section_content = page_text[section_start:].lower()
            
            # Score based on keyword matches
            score = sum(1 for keyword in keywords if keyword.lower() in section_content)
            if score > best_score:
                best_score = score
                best_section = section_title
        
        return best_section if best_score > 0 else None
    
    def answer(self, question: str) -> Dict:
        """
        Answer a natural language question using Wikipedia.
        
        Args:
            question: Natural language question
            
        Returns:
            Dictionary with:
                - matched_page: Page title
                - summary: Page summary
                - relevant_section: Most relevant section (if found)
                - full_text: Complete page text
            Or error dict if no results
        """
        try:
            # Extract keywords
            keywords = self._extract_keywords(question)
            logger.info(f"Extracted keywords from question: {keywords}")
            
            # Find best matching page
            page_title = self._find_best_match(question, keywords)
            
            if not page_title:
                logger.warning(f"No matching page found for question: {question}")
                return {"error": "no_results"}
            
            # Get page content
            page_data = self.get_page(page_title)
            
            if "error" in page_data:
                return page_data
            
            # Find relevant section
            relevant_section = self._find_relevant_section(page_data["full_text"], keywords)
            
            return {
                "matched_page": page_data["title"],
                "summary": page_data["summary"],
                "relevant_section": relevant_section,
                "full_text": page_data["full_text"],
                "language": self.lang
            }
            
        except Exception as e:
            logger.error(f"Error answering question '{question}': {e}")
            return {"error": "no_results"}
    
    def answer_multilang(self, question: str) -> Dict:
        """
        Answer a natural language question using both Italian and English Wikipedia.
        Combines results from both languages and marks which language each result is from.
        The AI will automatically translate English content to Italian.
        
        Args:
            question: Natural language question
            
        Returns:
            Dictionary with:
                - matched_page: Page title (from best result)
                - summary: Combined summary from both languages
                - relevant_section: Most relevant section (if found)
                - full_text: Combined full text from both languages
                - it_result: Italian Wikipedia result (if found)
                - en_result: English Wikipedia result (if found)
            Or error dict if no results from either language
        """
        try:
            # Try Italian first (primary language)
            it_agent = WikiAgent(lang="it")
            it_result = it_agent.answer(question)
            
            # Try English as well
            en_agent = WikiAgent(lang="en")
            en_result = en_agent.answer(question)
            
            # Combine results
            combined_result = {
                "it_result": it_result if "error" not in it_result else None,
                "en_result": en_result if "error" not in en_result else None
            }
            
            # If we have results from both languages
            if combined_result["it_result"] and combined_result["en_result"]:
                logger.info(f"Found results in both Italian and English Wikipedia")
                # Use Italian as primary, but include English as additional context
                combined_result.update({
                    "matched_page": it_result.get("matched_page", ""),
                    "summary": it_result.get("summary", ""),
                    "relevant_section": it_result.get("relevant_section"),
                    "full_text": it_result.get("full_text", ""),
                    "language": "it+en"
                })
                # Add English content as additional context
                en_summary = en_result.get("summary", "")
                en_text = en_result.get("full_text", "")
                if en_text:
                    # Limit English text to avoid overwhelming the context
                    en_text_limited = en_text[:2000] if len(en_text) > 2000 else en_text
                    combined_result["full_text"] += f"\n\n--- INFORMAZIONI AGGIUNTIVE DA WIKIPEDIA INGLESE ---\n\n{en_text_limited}"
                    if en_summary:
                        combined_result["summary"] += f"\n\n(Informazioni aggiuntive disponibili anche in inglese)"
            elif combined_result["it_result"]:
                logger.info(f"Found results only in Italian Wikipedia")
                combined_result.update(it_result)
                combined_result["language"] = "it"
            elif combined_result["en_result"]:
                logger.info(f"Found results only in English Wikipedia")
                combined_result.update(en_result)
                combined_result["language"] = "en"
            else:
                logger.warning(f"No results found in either Italian or English Wikipedia for: {question}")
                return {"error": "no_results"}
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Error in multilang answer for question '{question}': {e}")
            # Fallback to single language
            try:
                return self.answer(question)
            except:
                return {"error": "no_results"}


# Convenience function for quick access
def create_wiki_agent(lang: str = "it") -> WikiAgent:
    """
    Factory function to create a WikiAgent instance.
    
    Args:
        lang: Language code (default: "it")
        
    Returns:
        WikiAgent instance
    """
    return WikiAgent(lang=lang)

