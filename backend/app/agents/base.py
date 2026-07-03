import os
import json
import logging
from typing import List, Dict, Any, Callable, Optional
from backend.app.config import settings

logger = logging.getLogger("researchpilot.agents.base")

class AgentSession:
    """
    State shared across agents during a specific task execution.
    """
    def __init__(self, session_id: str, db_session = None):
        self.session_id = session_id
        self.db = db_session
        self.papers: List[Dict[str, Any]] = [] # Uploaded papers
        self.messages: List[Dict[str, Any]] = [] # Session history
        self.variables: Dict[str, Any] = {} # Arbitrary state
        self.logs: List[Dict[str, Any]] = [] # Step execution logs

    def log_step(self, agent_name: str, action: str, details: Any):
        log_entry = {
            "agent": agent_name,
            "action": action,
            "details": details
        }
        self.logs.append(log_entry)
        logger.info(f"[{agent_name}] {action}: {str(details)[:150]}")

class BaseAgent:
    """
    Base Agent representing a specialized AI agent.
    """
    def __init__(
        self,
        name: str,
        role: str,
        system_instruction: str,
        tools: List[Callable] = None
    ):
        self.name = name
        self.role = role
        self.system_instruction = system_instruction
        self.tools = tools or []
        self.tools_map = {t.__name__: t for t in self.tools}

    def _call_gemini(self, prompt: str, history: List[Dict[str, Any]] = None) -> str:
        """
        Calls Gemini using standard generativeai SDK.
        Falls back to a mock response generator if GEMINI_API_KEY is missing.
        """
        if not settings.GEMINI_API_KEY:
            logger.warning(f"GEMINI_API_KEY is not configured. Mocking output for {self.name}.")
            return self._generate_mock_response(prompt)
            
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Format history for Gemini chat if present
            # Otherwise use simple generate_content with system instructions
            contents = []
            if history:
                for msg in history:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append({"role": role, "parts": [msg["content"]]})
            
            contents.append({"role": "user", "parts": [prompt]})
            
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                system_instruction=self.system_instruction
            )
            
            # Simple config
            config = genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=4000
            )
            
            response = model.generate_content(contents, generation_config=config)
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini in agent {self.name}: {e}. Generating mock fallback.")
            return self._generate_mock_response(prompt)

    def _generate_mock_response(self, prompt: str) -> str:
        """
        Generates clean mock responses based on agent role for testing without API keys.
        """
        prompt_lower = prompt.lower()
        
        if self.name == "Planner Agent":
            return json.dumps({
                "plan": [
                    {"step": 1, "agent": "Research Retrieval Agent", "action": "Gather papers about the topic"},
                    {"step": 2, "agent": "Paper Analysis Agent", "action": "Analyze main findings and methodology"},
                    {"step": 3, "agent": "Summarization Agent", "action": "Produce structured summaries"},
                    {"step": 4, "agent": "Literature Review Agent", "action": "Synthesize a literature review paper"}
                ],
                "explanation": "I have created a 4-step research workflow to address your query."
            })
            
        elif self.name == "Research Retrieval Agent":
            return "Here are research papers matching your query:\n1. 'Attention Is All You Need' (Vaswani et al., 2017) - Introducing the Transformer architecture.\n2. 'BERT: Pre-training of Deep Bidirectional Transformers' (Devlin et al., 2018) - Pre-training language representations."
            
        elif self.name == "Paper Analysis Agent":
            return "### Paper Analysis\n- **Methodology**: Multi-head self-attention mechanisms replacing recurrence/convolutions.\n- **Contributions**: Transformer translation model achieving SOTA.\n- **Datasets**: WMT 2014 English-to-German and English-to-French.\n- **Key Results**: BLEU score of 28.4 on English-to-German."
            
        elif self.name == "Summarization Agent":
            return "### Executive Summary\nThe papers describe the shift from sequential RNN architectures to self-attention-based models. By allowing parallelized training across entire sequences, Transformers achieved state-of-the-art results in language translation tasks, drastically reducing training time."
            
        elif self.name == "Comparison Agent":
            return "### Methodology Comparison\n| Paper | Architecture | Strengths | Limitations |\n|---|---|---|---|\n| Attention Is All You Need | Pure Self-Attention | High Parallelization, SOTA BLEU | Quadratic memory scaling |\n| BERT | Masked LM Transformer | Bidirectional context, versatile | High training cost |"
            
        elif self.name == "Citation Agent":
            return "### Citations\n- **APA**: Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... & Polosukhin, I. (2017). Attention is all you need. *Advances in Neural Information Processing Systems*, 30.\n- **BibTeX**:\n```bibtex\n@inproceedings{vaswani2017attention,\n  title={Attention is all you need},\n  author={Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N and Kaiser, Lukasz and Polosukhin, Illia},\n  booktitle={Advances in Neural Information Processing Systems},\n  pages={5998--6008},\n  year={2017}\n}\n```"
            
        elif self.name == "Literature Review Agent":
            return "## Literature Review: Advanced Self-Attention Architectures\n\n### Introduction\nThe field of NLP has been revolutionized by self-attention mechanisms. This review synthesizes key advancements from core publications.\n\n### Methodological Synthesis\nVaswani et al. (2017) replaced recurrence entirely, establishing the Transformer. Devlin et al. (2018) built on this with BERT, showing bidirectional pre-training is crucial for understanding context.\n\n### Open Challenges\nQuadratic space complexity remains a bottleneck for long document analysis."
            
        elif self.name == "Research Gap Agent":
            return "### Research Gaps & Open Challenges\n1. **Long-context Efficiency**: Standard self-attention scales quadratically ($O(N^2)$) with sequence length. Efficient sparse-attention models are needed.\n2. **Hardware Constraints**: Large-scale language model pre-training is resource-heavy, creating a barrier for smaller research labs."
            
        elif self.name == "Code Generation Agent":
            return "### Implementation Code\nHere is a simple PyTorch self-attention module:\n```python\nimport torch\nimport torch.nn as nn\n\nclass SelfAttention(nn.Module):\n    def __init__(self, embed_size, heads):\n        super(SelfAttention, self).__init__()\n        self.embed_size = embed_size\n        self.heads = heads\n        self.head_dim = embed_size // heads\n        \n        self.values = nn.Linear(self.head_dim, self.head_dim, bias=False)\n        self.keys = nn.Linear(self.head_dim, self.head_dim, bias=False)\n        self.queries = nn.Linear(self.head_dim, self.head_dim, bias=False)\n        self.fc_out = nn.Linear(heads * self.head_dim, embed_size)\n```"
            
        elif self.name == "Presentation Agent":
            return "### Presentation Outline: Transformers & Attention\n\n#### Slide 1: Title\n- **Title**: Attention Mechanisms in Modern AI\n- **Presenter**: ResearchPilot AI\n\n#### Slide 2: The Core Problem\n- Traditional RNNs are slow due to sequential computations.\n- Context is lost over long distances."
            
        return f"Synthesized analysis from {self.name} regarding your request."

    def execute(self, session: AgentSession, prompt: str) -> str:
        """Executes the agent logic, logging the process to the session."""
        session.log_step(self.name, "Starting execution", {"prompt": prompt})
        
        # In a fully agentic flow, we might extract tool calls.
        # For simplicity, we feed context into the LLM system instruction and request a final output.
        result = self._call_gemini(prompt, history=session.messages)
        
        session.log_step(self.name, "Completed execution", {"result_length": len(result)})
        return result
