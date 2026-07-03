import json
import logging
from typing import Dict, Any, List
from backend.app.agents.base import BaseAgent, AgentSession
from backend.app.agents.worker_agents import (
    RetrievalAgent, PaperAnalysisAgent, SummarizationAgent,
    ComparisonAgent, CitationAgent, LiteratureReviewAgent,
    ResearchGapAgent, CodeGenerationAgent, PresentationAgent
)

logger = logging.getLogger("researchpilot.agents.orchestrator")

class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Planner Agent",
            role="Analyzes user research goals and generates structured coordination plans.",
            system_instruction=(
                "You are the Planner Agent. Your job is to break down research requests into a logical sequence "
                "of tasks assigned to specialized worker agents. Available agents are:\n"
                "- 'Research Retrieval Agent' (for searching new papers or fetching vector database context)\n"
                "- 'Paper Analysis Agent' (for deep analysis of specific papers)\n"
                "- 'Summarization Agent' (for creating concise summaries)\n"
                "- 'Comparison Agent' (for side-by-side comparison tables)\n"
                "- 'Citation Agent' (for generating bibliography references)\n"
                "- 'Literature Review Agent' (for synthesis and writing structured reviews)\n"
                "- 'Research Gap Agent' (for listing limitations and future studies)\n"
                "- 'Code Generation Agent' (for code snippets and repositories)\n"
                "- 'Presentation Agent' (for slide structures and lecture notes)\n\n"
                "Based on the user prompt and uploaded paper contexts, generate a plan. "
                "You MUST respond ONLY with a raw JSON array of steps. Each step must contain:\n"
                "- 'step': (int) sequential index\n"
                "- 'agent': (str) exact name of the agent\n"
                "- 'action': (str) brief description of action\n"
                "- 'params': (dict) parameter values such as 'query' or 'paper_ids'\n\n"
                "Example response:\n"
                "[\n"
                "  {\"step\": 1, \"agent\": \"Research Retrieval Agent\", \"action\": \"search\", \"params\": {\"query\": \"LoRA\"}},\n"
                "  {\"step\": 2, \"agent\": \"Paper Analysis Agent\", \"action\": \"analyze\", \"params\": {}}\n"
                "]"
            )
        )

    def plan_workflow(self, session: AgentSession, user_query: str) -> List[Dict[str, Any]]:
        papers_meta = [{"id": p.get("id"), "title": p.get("title")} for p in session.papers]
        prompt = (
            f"User Research Query: '{user_query}'\n"
            f"Already Uploaded Papers in Workspace: {json.dumps(papers_meta)}\n"
            f"Generate a customized list of steps for this query."
        )
        
        raw_plan = self.execute(session, prompt)
        
        # Parse plan
        try:
            # Clean up markdown formatting if any
            clean_plan = raw_plan.strip()
            if clean_plan.startswith("```json"):
                clean_plan = clean_plan[7:]
            if clean_plan.endswith("```"):
                clean_plan = clean_plan[:-3]
            clean_plan = clean_plan.strip()
            
            plan_data = json.loads(clean_plan)
            session.log_step(self.name, "Generated workflow plan", plan_data)
            return plan_data
        except Exception as e:
            logger.error(f"Error parsing plan JSON: {e}. Raw response was: {raw_plan}")
            # Fallback default plan
            fallback = [
                {"step": 1, "agent": "Research Retrieval Agent", "action": "search", "params": {"query": user_query}},
                {"step": 2, "agent": "Paper Analysis Agent", "action": "analyze", "params": {}},
                {"step": 3, "agent": "SummarizationAgent", "action": "summarize", "params": {}}
            ]
            session.log_step(self.name, "Plan parsing failed, loaded fallback", fallback)
            return fallback


class Orchestrator:
    def __init__(self):
        self.planner = PlannerAgent()
        self.workers = {
            "Research Retrieval Agent": RetrievalAgent(),
            "Paper Analysis Agent": PaperAnalysisAgent(),
            "Summarization Agent": SummarizationAgent(),
            "Comparison Agent": ComparisonAgent(),
            "Citation Agent": CitationAgent(),
            "Literature Review Agent": LiteratureReviewAgent(),
            "Research Gap Agent": ResearchGapAgent(),
            "Code Generation Agent": CodeGenerationAgent(),
            "Presentation Agent": PresentationAgent()
        }

    def execute_workflow(self, session: AgentSession, user_query: str) -> Dict[str, Any]:
        """
        Coordinates the planner and workers to resolve the research task.
        """
        session.log_step("Orchestrator", "Initiating workflow for user query", user_query)
        
        # Step 1: Get plan
        plan = self.planner.plan_workflow(session, user_query)
        
        # Keep track of intermediate results to feed to next steps
        context_data = {
            "query": user_query,
            "retrieved_papers": [],
            "analyses": [],
            "summaries": [],
            "citations": [],
            "reviews": [],
            "gaps": [],
            "code": [],
            "slides": []
        }
        
        # Execute each step of the plan
        for step in plan:
            agent_name = step.get("agent")
            action = step.get("action")
            params = step.get("params", {})
            
            worker = self.workers.get(agent_name)
            if not worker:
                session.log_step("Orchestrator", f"Warning: Unknown agent '{agent_name}' requested in plan.", None)
                continue
                
            session.log_step("Orchestrator", f"Running step {step.get('step')}: {agent_name}", step)
            
            # Specialized agent execution
            if agent_name == "Research Retrieval Agent":
                retrieval_query = params.get("query", user_query)
                limit = params.get("limit", 3)
                # Pass local papers context too
                found = worker.execute_search(session, retrieval_query, limit=limit)
                context_data["retrieved_papers"].extend(found)
                
            elif agent_name == "Paper Analysis Agent":
                # Analyze local papers in workspace
                papers_to_analyze = session.papers if session.papers else context_data["retrieved_papers"]
                analyses = []
                for paper in papers_to_analyze[:3]: # Limit to first 3 papers to avoid token overflow
                    paper_content = paper.get("full_text", paper.get("abstract", ""))[:6000] # Cap text size
                    prompt = f"Analyze this paper:\nTitle: {paper.get('title')}\nAbstract: {paper.get('abstract')}\nContent Snippet: {paper_content}"
                    analysis_out = worker.execute(session, prompt)
                    analyses.append({"paper_id": paper.get("id"), "title": paper.get("title"), "analysis": analysis_out})
                context_data["analyses"] = analyses
                
            elif agent_name == "Summarization Agent":
                papers_to_summarize = session.papers if session.papers else context_data["retrieved_papers"]
                summary_prompt = "Summarize the following papers:\n"
                for p in papers_to_summarize[:3]:
                    summary_prompt += f"- Title: {p.get('title')}\nAbstract: {p.get('abstract')}\n"
                summary_out = worker.execute(session, summary_prompt)
                context_data["summaries"].append(summary_out)
                
            elif agent_name == "Comparison Agent":
                papers_to_compare = session.papers if session.papers else context_data["retrieved_papers"]
                comp_prompt = "Compare the following papers:\n"
                for p in papers_to_compare[:3]:
                    comp_prompt += f"- Title: {p.get('title')}\nAbstract: {p.get('abstract')}\n"
                comp_out = worker.execute(session, comp_prompt)
                context_data["comparisons"] = comp_out
                
            elif agent_name == "Citation Agent":
                papers_to_cite = session.papers if session.papers else context_data["retrieved_papers"]
                cite_prompt = "Generate citations for these papers:\n"
                for p in papers_to_cite[:3]:
                    cite_prompt += f"- Title: {p.get('title')}\nAuthors: {p.get('authors')}\nYear: {p.get('year')}\nDOI: {p.get('doi')}\n"
                cite_out = worker.execute(session, cite_prompt)
                context_data["citations"].append(cite_out)
                
            elif agent_name == "Literature Review Agent":
                papers_to_review = session.papers if session.papers else context_data["retrieved_papers"]
                lit_prompt = f"Write a structured literature review on '{user_query}' based on these papers:\n"
                for p in papers_to_review[:3]:
                    lit_prompt += f"- Title: {p.get('title')}\nAbstract: {p.get('abstract')}\n"
                if context_data["analyses"]:
                    lit_prompt += f"\nHere are the detailed analyses:\n" + json.dumps(context_data["analyses"][:2])
                review_out = worker.execute(session, lit_prompt)
                context_data["reviews"].append(review_out)
                
            elif agent_name == "Research Gap Agent":
                papers_to_gap = session.papers if session.papers else context_data["retrieved_papers"]
                gap_prompt = "Identify research gaps in these papers:\n"
                for p in papers_to_gap[:3]:
                    gap_prompt += f"- Title: {p.get('title')}\nAbstract: {p.get('abstract')}\n"
                gap_out = worker.execute(session, gap_prompt)
                context_data["gaps"].append(gap_out)
                
            elif agent_name == "Code Generation Agent":
                papers_to_code = session.papers if session.papers else context_data["retrieved_papers"]
                code_prompt = f"Generate code related to the methodology of these papers for the goal '{user_query}':\n"
                for p in papers_to_code[:2]:
                    code_prompt += f"- Title: {p.get('title')}\nAbstract: {p.get('abstract')}\n"
                code_out = worker.execute(session, code_prompt)
                context_data["code"].append(code_out)
                
            elif agent_name == "Presentation Agent":
                papers_to_slides = session.papers if session.papers else context_data["retrieved_papers"]
                slide_prompt = f"Create a slide deck outline based on these research papers for topic '{user_query}':\n"
                for p in papers_to_slides[:2]:
                    slide_prompt += f"- Title: {p.get('title')}\nAbstract: {p.get('abstract')}\n"
                slide_out = worker.execute(session, slide_prompt)
                context_data["slides"].append(slide_out)

        # Synthesize final response combining results
        session.log_step("Orchestrator", "Compiling and synthesizing final result", None)
        
        synthesis_prompt = (
            f"User Research Query: '{user_query}'\n\n"
            f"Here is the context of what the multi-agent workflow accomplished:\n"
        )
        if context_data["retrieved_papers"]:
            synthesis_prompt += f"- Retrieval: Found {len(context_data['retrieved_papers'])} papers.\n"
        if context_data["analyses"]:
            synthesis_prompt += f"- Analysis: Conducted deep analysis of {len(context_data['analyses'])} papers.\n"
        if context_data["summaries"]:
            synthesis_prompt += "- Summarization: Created general syntheses.\n"
        if context_data["reviews"]:
            synthesis_prompt += "- Lit Review: Structured review generated.\n"
        if context_data["comparisons"]:
            synthesis_prompt += "- Comparison: Side-by-side comparison table generated.\n"
            
        synthesis_prompt += "\nSynthesize a highly polished summary response to the user. Guide them through what research files were analyzed and what insights were uncovered. Highlight the next logical steps."
        
        # We can use the Summarization Agent to compile the final synthesis
        final_summary = self.workers["Summarization Agent"].execute(session, synthesis_prompt)
        
        # Gather all generated artifacts
        artifacts = {
            "summary": final_summary,
            "papers": context_data["retrieved_papers"],
            "comparisons": context_data.get("comparisons", ""),
            "literature_review": context_data["reviews"][0] if context_data["reviews"] else "",
            "citations": context_data["citations"][0] if context_data["citations"] else "",
            "research_gaps": context_data["gaps"][0] if context_data["gaps"] else "",
            "code_suggestions": context_data["code"][0] if context_data["code"] else "",
            "presentation": context_data["slides"][0] if context_data["slides"] else ""
        }
        
        return {
            "answer": final_summary,
            "artifacts": artifacts,
            "plan": plan,
            "logs": session.logs
        }
