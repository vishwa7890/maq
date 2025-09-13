"""
PDF Processing and Comparison Module
Handles PDF text extraction, table extraction, and similarity comparison with cost estimations.
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import pdfplumber
import fitz  # PyMuPDF
from fuzzywuzzy import fuzz, process
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re
# Removed SentenceTransformer to avoid Hugging Face dependency

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Handles PDF text and table extraction"""
    
    def __init__(self):
        """Initialize PDFProcessor without external embedding model"""
        pass
        
    def extract_text_and_tables(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract text and tables from PDF using pdfplumber
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted text and tables
        """
        try:
            extracted_data = {
                "text": "",
                "tables": [],
                "metadata": {}
            }
            
            with pdfplumber.open(pdf_path) as pdf:
                extracted_data["metadata"] = {
                    "pages": len(pdf.pages),
                    "title": pdf.metadata.get('Title', ''),
                    "author": pdf.metadata.get('Author', ''),
                    "creator": pdf.metadata.get('Creator', '')
                }
                
                full_text = []
                all_tables = []
                
                for page_num, page in enumerate(pdf.pages):
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        full_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
                    
                    # Extract tables
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        if table:
                            table_data = {
                                "page": page_num + 1,
                                "table_index": table_idx,
                                "data": table,
                                "headers": table[0] if table else [],
                                "rows": table[1:] if len(table) > 1 else []
                            }
                            all_tables.append(table_data)
                
                extracted_data["text"] = "\n\n".join(full_text)
                extracted_data["tables"] = all_tables
                
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting PDF content: {str(e)}")
            raise Exception(f"Failed to process PDF: {str(e)}")
    
    def extract_cost_information(self, text: str, tables: List[Dict]) -> Dict[str, Any]:
        """
        Extract cost-related information from text and tables
        
        Args:
            text: Extracted text from PDF
            tables: Extracted tables from PDF
            
        Returns:
            Dictionary containing cost information
        """
        cost_info = {
            "amounts": [],
            "services": [],
            "timeline": [],
            "terms": []
        }
        
        # Extract monetary amounts using regex
        amount_patterns = [
            r'₹\s*[\d,]+(?:\.\d{2})?',  # Indian Rupee
            r'Rs\.?\s*[\d,]+(?:\.\d{2})?',  # Rupees
            r'\$\s*[\d,]+(?:\.\d{2})?',  # Dollar
            r'INR\s*[\d,]+(?:\.\d{2})?',  # INR
            r'[\d,]+\s*(?:rupees?|dollars?)',  # Written currency
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            cost_info["amounts"].extend(matches)
        
        # Extract service-related keywords
        service_keywords = [
            'development', 'design', 'testing', 'deployment', 'maintenance',
            'frontend', 'backend', 'database', 'api', 'integration',
            'ui/ux', 'mobile', 'web', 'application', 'software'
        ]
        
        for keyword in service_keywords:
            if keyword.lower() in text.lower():
                # Extract context around the keyword
                pattern = rf'.{{0,50}}{re.escape(keyword)}.{{0,50}}'
                matches = re.findall(pattern, text, re.IGNORECASE)
                cost_info["services"].extend(matches)
        
        # Extract timeline information
        timeline_patterns = [
            r'\d+\s*(?:days?|weeks?|months?|years?)',
            r'(?:within|in|by)\s+\d+\s*(?:days?|weeks?|months?)',
            r'deadline:?\s*[^\n]+',
            r'timeline:?\s*[^\n]+',
            r'delivery:?\s*[^\n]+'
        ]
        
        for pattern in timeline_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            cost_info["timeline"].extend(matches)
        
        # Extract terms and conditions
        terms_patterns = [
            r'payment:?\s*[^\n]+',
            r'terms:?\s*[^\n]+',
            r'conditions:?\s*[^\n]+',
            r'advance:?\s*[^\n]+',
            r'gst:?\s*[^\n]+',
            r'tax:?\s*[^\n]+'
        ]
        
        for pattern in terms_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            cost_info["terms"].extend(matches)
        
        # Process tables for cost information
        for table in tables:
            table_data = table.get("data", [])
            for row in table_data:
                if row:
                    row_text = " ".join([str(cell) for cell in row if cell])
                    # Check if row contains cost information
                    for pattern in amount_patterns:
                        if re.search(pattern, row_text, re.IGNORECASE):
                            cost_info["amounts"].append(row_text)
        
        return cost_info

class CostEstimationComparator:
    """Compares PDF content with AI-generated cost estimations"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
    
    def compare_with_estimation(self, pdf_content: Dict[str, Any], estimation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare PDF content with cost estimation
        
        Args:
            pdf_content: Extracted PDF content
            estimation_data: AI-generated cost estimation
            
        Returns:
            Comparison results with similarity score and mismatches
        """
        try:
            # Extract cost information from PDF
            processor = PDFProcessor()
            pdf_cost_info = processor.extract_cost_information(
                pdf_content.get("text", ""), 
                pdf_content.get("tables", [])
            )
            
            # Prepare estimation text for comparison
            estimation_text = self._prepare_estimation_text(estimation_data)
            pdf_text = pdf_content.get("text", "")
            
            # Calculate similarity scores
            similarity_scores = self._calculate_similarity_scores(pdf_text, estimation_text)
            
            # Find closest matches
            closest_matches = self._find_closest_matches(pdf_cost_info, estimation_data)
            
            # Identify mismatches
            mismatches = self._identify_mismatches(pdf_cost_info, estimation_data)
            
            # Generate suggestions
            suggestions = self._generate_suggestions(mismatches, closest_matches)
            
            # Calculate overall match score
            overall_score = self._calculate_overall_score(similarity_scores, closest_matches, mismatches)
            
            return {
                "match_score": round(overall_score, 2),
                "similarity_scores": similarity_scores,
                "closest_matches": closest_matches,
                "mismatches": mismatches,
                "suggestions": suggestions,
                "pdf_cost_info": pdf_cost_info
            }
            
        except Exception as e:
            logger.error(f"Error comparing PDF with estimation: {str(e)}")
            raise Exception(f"Comparison failed: {str(e)}")
    
    def _prepare_estimation_text(self, estimation_data: Dict[str, Any]) -> str:
        """Convert estimation data to text for comparison"""
        text_parts = []
        
        if "scope_of_work" in estimation_data:
            for phase, activities in estimation_data["scope_of_work"].items():
                text_parts.append(f"{phase}: {' '.join(activities)}")
        
        if "pricing" in estimation_data:
            for item, price in estimation_data["pricing"].items():
                text_parts.append(f"{item}: {price}")
        
        if "timeline" in estimation_data:
            text_parts.append(f"Timeline: {estimation_data['timeline']}")
        
        if "notes" in estimation_data:
            text_parts.append(f"Notes: {estimation_data['notes']}")
        
        return " ".join(text_parts)
    
    def _calculate_similarity_scores(self, pdf_text: str, estimation_text: str) -> Dict[str, float]:
        """Calculate various similarity scores"""
        scores = {}
        
        # TF-IDF Cosine Similarity
        try:
            tfidf_matrix = self.vectorizer.fit_transform([pdf_text, estimation_text])
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            scores["cosine_similarity"] = float(cosine_sim)
        except:
            scores["cosine_similarity"] = 0.0
        
        # Fuzzy string matching
        scores["fuzzy_ratio"] = fuzz.ratio(pdf_text[:1000], estimation_text[:1000]) / 100.0
        scores["fuzzy_partial_ratio"] = fuzz.partial_ratio(pdf_text[:1000], estimation_text[:1000]) / 100.0
        
        # Semantic similarity (approximate): reuse TF-IDF cosine as a semantic proxy
        scores["semantic_similarity"] = scores.get("cosine_similarity", 0.0)
        
        return scores
    
    def _find_closest_matches(self, pdf_cost_info: Dict[str, Any], estimation_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Find closest matches between PDF and estimation"""
        matches = []
        
        # Compare amounts
        pdf_amounts = pdf_cost_info.get("amounts", [])
        est_pricing = estimation_data.get("pricing", {})
        
        for pdf_amount in pdf_amounts[:5]:  # Limit to top 5
            best_match = None
            best_score = 0
            
            for item, price in est_pricing.items():
                score = fuzz.partial_ratio(str(pdf_amount), f"{item}: {price}")
                if score > best_score and score > 60:  # Threshold
                    best_score = score
                    best_match = {
                        "pdf_content": str(pdf_amount),
                        "estimation_content": f"{item}: {price}",
                        "similarity": score
                    }
            
            if best_match:
                matches.append(best_match)
        
        return matches
    
    def _identify_mismatches(self, pdf_cost_info: Dict[str, Any], estimation_data: Dict[str, Any]) -> List[str]:
        """Identify potential mismatches"""
        mismatches = []
        
        # Check for GST/Tax mentions
        pdf_text_lower = " ".join(pdf_cost_info.get("terms", [])).lower()
        if "gst" not in pdf_text_lower and "tax" not in pdf_text_lower:
            if estimation_data.get("total", 0) > 0:
                mismatches.append("GST/Tax not mentioned in client document")
        
        # Check timeline mismatches
        pdf_timeline = pdf_cost_info.get("timeline", [])
        est_timeline = estimation_data.get("timeline", "")
        
        if pdf_timeline and est_timeline:
            timeline_text = " ".join(pdf_timeline).lower()
            if fuzz.partial_ratio(timeline_text, est_timeline.lower()) < 50:
                mismatches.append("Timeline mismatch between documents")
        elif not pdf_timeline and est_timeline:
            mismatches.append("Delivery timeline not mentioned in client document")
        
        # Check for missing payment terms
        if not pdf_cost_info.get("terms"):
            mismatches.append("Payment terms not clearly specified in client document")
        
        return mismatches
    
    def _generate_suggestions(self, mismatches: List[str], closest_matches: List[Dict[str, str]]) -> List[str]:
        """Generate suggestions based on comparison results"""
        suggestions = []
        
        if "GST" in " ".join(mismatches):
            suggestions.append("Consider clarifying GST/tax implications in the final quote")
        
        if "timeline" in " ".join(mismatches).lower():
            suggestions.append("Align project timeline expectations between both documents")
        
        if "payment" in " ".join(mismatches).lower():
            suggestions.append("Specify clear payment terms and schedule")
        
        # Suggestions based on close matches
        for match in closest_matches[:3]:
            if match["similarity"] > 80:
                suggestions.append(f"Strong alignment found: {match['pdf_content']} matches {match['estimation_content']}")
        
        return suggestions
    
    def _calculate_overall_score(self, similarity_scores: Dict[str, float], closest_matches: List[Dict], mismatches: List[str]) -> float:
        """Calculate overall match score"""
        # Weight different similarity measures
        weights = {
            "cosine_similarity": 0.3,
            "fuzzy_ratio": 0.2,
            "fuzzy_partial_ratio": 0.2,
            "semantic_similarity": 0.3
        }
        
        weighted_score = sum(
            similarity_scores.get(metric, 0) * weight 
            for metric, weight in weights.items()
        )
        
        # Boost score based on close matches
        match_boost = min(len(closest_matches) * 0.1, 0.3)
        
        # Penalize for mismatches
        mismatch_penalty = min(len(mismatches) * 0.05, 0.2)
        
        final_score = (weighted_score + match_boost - mismatch_penalty) * 100
        
        return max(0, min(100, final_score))  # Clamp between 0-100
