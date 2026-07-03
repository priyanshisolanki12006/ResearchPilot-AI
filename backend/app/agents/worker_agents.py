from typing import List, Dict, Any
from backend.app.agents.base import BaseAgent, AgentSession
from backend.app.mcp.server import LocalTools
import json

class RetrievalAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Research Retrieval Agent",
            role="Searches and retrieves relevant research papers from arXiv, Semantic Scholar, and local vector stores.",
            system_instruction=(
                "You are an expert Research Retrieval Agent. Your job is to locate scientific papers and relevant literature "
                "based on the user's research criteria. You format output clearly, highlighting Title, Authors, Year, Source, URL, and Abstract."
            ),
            tools=[LocalTools.search_arxiv, LocalTools.search_semantic_scholar, LocalTools.vector_semantic_search]
        )
        
    def execute_search(self, session: AgentSession, query: str, limit: int = 5, local_only: bool = False) -> List[Dict[str, Any]]:
        session.log_step(self.name, "Querying literature databases", {"query": query, "limit": limit, "local_only": local_only})
        
        results = []
        # Query local vector store first
        local_results = LocalTools.vector_semantic_search(query, limit=limit)
        if local_results:
            for r in local_results:
                results.append({
                    "source": "local",
                    "title": r["title"],
                    "id": r["paper_id"],
                    "abstract": r["text"][:300] + "...",
                    "score": r.get("score", 0.5)
                })
                
        if not local_only:
            # Query arXiv
            arxiv_res = LocalTools.search_arxiv(query, limit=limit)
            results.extend(arxiv_res)
            
            # Query Semantic Scholar
            sem_res = LocalTools.search_semantic_scholar(query, limit=limit)
            results.extend(sem_res)
            
        # Deduplicate results by title
        seen_titles = set()
        dedup_results = []
        for r in results:
            title_lower = r["title"].lower().strip()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                dedup_results.append(r)
                
        session.log_step(self.name, "Search complete", {"total_found": len(dedup_results)})
        return dedup_results[:limit]


class PaperAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Paper Analysis Agent",
            role="Extracts contributions, methodologies, datasets, and key results from scientific literature.",
            system_instruction=(
                "You are a Senior Paper Analysis Agent. Analyze the provided research paper content. "
                "Extract and structure the following details precisely:\n"
                "1. Core Contribution / Purpose\n"
                "2. Methodology / Technical Architecture\n"
                "3. Datasets & Benchmarks used\n"
                "4. Quantitative & Qualitative Results\n"
                "Provide a rigorous, scholarly breakdown. Do not guess; if info is missing, indicate it."
            )
        )


class SummarizationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Summarization Agent",
            role="Creates concise summaries for individual and multiple research papers.",
            system_instruction=(
                "You are a Summarization Agent. Your goal is to write concise, informative summaries of scientific papers. "
                "For single papers, provide a TL;DR followed by key takeaways. For multiple papers, synthesize a high-level "
                "executive summary showing how the papers relate."
            )
        )


class ComparisonAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Comparison Agent",
            role="Compares research papers side-by-side using methodology, performance, and limitation tables.",
            system_instruction=(
                "You are a Comparison Agent. Compare the provided research papers. "
                "Format your response as a detailed Markdown table with columns: 'Paper', 'Core Methodology', 'Datasets Used', 'Key Results/Performance', 'Limitations'. "
                "Provide a 1-2 paragraph analysis comparing their relative trade-offs below the table."
            )
        )


class CitationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Citation Agent",
            role="Generates reference citations in APA, IEEE, MLA, BibTeX, and Chicago formats.",
            system_instruction=(
                "You are an expert Citation Agent. Generate bibliography entries for the specified paper details. "
                "Provide accurate citations in all of the following formats: APA, IEEE, MLA, Chicago, and BibTeX. "
                "Ensure BibTeX is in a valid code block."
            )
        )


class LiteratureReviewAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Literature Review Agent",
            role="Automatically generates a structured, publication-ready literature review.",
            system_instruction=(
                "You are a Literature Review Agent. Compile a publication-grade, structured literature review "
                "synthesizing the provided paper summaries, contexts, and findings. Use academic headings (e.g., Introduction, "
                "Methodological Synthesis, Chronological Advancements, Emerging Themes, Open Challenges). "
                "Ensure logical flow and citation of sources (e.g., Vaswani et al., 2017)."
            )
        )


class ResearchGapAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Research Gap Agent",
            role="Identifies research gaps, limitations, and future research opportunities.",
            system_instruction=(
                "You are a Research Gap Agent. Critically review the analyzed papers to detect:\n"
                "1. Methodological constraints / limitations\n"
                "2. Untested scenarios or edge cases\n"
                "3. Contradictory findings in the literature\n"
                "4. Suggested future research direction.\n"
                "Provide actionable hypotheses that a researcher could pursue as their next project."
            )
        )


class CodeGenerationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Code Generation Agent",
            role="Suggests implementation code, APIs, and relevant GitHub repositories.",
            system_instruction=(
                "You are a Code Generation Agent. Read the paper's methodology and suggest clean, modular implementation code "
                "(preferably in PyTorch, JAX, or clean Python) representing the core algorithm or logic. "
                "Provide references to standard open-source GitHub repositories (like HuggingFace transformers, etc.) that implement the concept."
            )
        )


class PresentationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Presentation Agent",
            role="Creates presentation slides and research speaker notes from analyzed papers.",
            system_instruction=(
                "You are a Presentation Agent. Convert the analyzed research content into a structured slide presentation deck outline. "
                "For each slide, provide:\n"
                "- Slide Number & Title\n"
                "- Bullet points of key content\n"
                "- Speaker Notes (what the presenter should say to elaborate)\n"
                "Keep slides visually structured and concise."
            )
        )
