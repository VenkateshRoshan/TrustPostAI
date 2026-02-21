# agents/research.py

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Literal

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import Config

class ResearchOutput(BaseModel):
    core_understanding: str = Field(description="What this topic is really about, written clearly for an intelligent reader")
    key_dynamics: str = Field(description="Forces, relationships, causes, and consequences at play")
    important_nuances: str = Field(description="Common misunderstandings, edge cases, exceptions, contradictions")
    conflicting_perspectives: str = Field(description="Where sources disagree and what each side argues")
    knowledge_gaps: list[str] = Field(description="List of plain strings describing what could not be determined")
    research_confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(description="Confidence level: HIGH, MEDIUM, or LOW")
    additional_queries_needed: list[str] = Field(description="List of plain search query strings to fill gaps. Empty list if HIGH confidence")
    insufficient: bool = Field(description="True if data was too poor to form any understanding, else False")
    insufficient_reason: str | None = Field(default=None, description="Reason if insufficient is True, else null")

class ResearchAgent:
    def __init__(self, model_name: str = "deepseek-r1:8b", temperature: float = 0.0):
        self.llm = ChatOllama(model=model_name, temperature=temperature, format="json")
        self.parser = JsonOutputParser(pydantic_object=ResearchOutput)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
You are a Research Agent. You think like a senior investigative journalist 
combined with a subject matter expert.

You have been given raw web data on a topic.
Your job is not to extract bullet points.
Your job is to DEEPLY UNDERSTAND the topic.

--- 
             
PHASE 1 - COMPREHENSION

Before doing anything else, ask yourself:

What is this topic actually about at its core?
What problem, event, trend, or subject does it represent?
Why does it matter right now?
Who are the key players, entities, or stakeholders involved?
What is the broader context this topic sits inside?

Think through these questions seriously. Build a mental model of the topic 
before touching any specific fact.

PHASE 2 - CRITICAL ANALYSIS

Now go deeper. Challenge what you are reading.

What is the mainstream narrative being presented here?
Is there a counter-narrative or an opposing perspective in the data?
What assumptions are being made by the sources?
What is NOT being said that probably should be?
Are there gaps in the story - missing causes, missing consequences, 
missing voices?
What would a skeptic challenge about this topic?
What would a domain expert notice that a casual reader would miss?
What is the most important thing to understand here that most people get wrong?

PHASE 3 - CONNECTING THE DOTS

Look across all sources together now.

Where do sources agree? What does that consensus tell you?
Where do sources conflict? What does that conflict reveal?
Are there patterns across sources that no single source states explicitly?
What cause-and-effect relationships exist in this topic?
What are the short-term and long-term implications of what is happening?
What historical context is relevant to understanding this properly?

PHASE 4 - GAP IDENTIFICATION

What questions does the raw data raise but not answer?
What information would a reader urgently need that is not present here?
What aspects of this topic have NOT been covered by the sources provided?

PHASE 5 - OUTPUT

Return a single valid JSON object. No explanation outside the JSON.

STRICT RULES FOR JSON:
- knowledge_gaps must be a list of plain strings only
- additional_queries_needed must be a list of plain strings only
- insufficient must be a boolean true or false
- research_confidence must be exactly one of: HIGH, MEDIUM, LOW
- Do not nest objects inside any list field

{format_instructions}
"""),
            ("human", """
Topic: {topic}

Raw data and sources:
{claims}
""")
        ]).partial(format_instructions=self.parser.get_format_instructions())

    def run(self, claims: list, topic: str) -> ResearchOutput:

        chain = self.prompt | self.llm | self.parser

        response = chain.invoke({
            "topic": topic,
            "claims": claims
        })

        def to_str_list(items) -> list[str]:
            if not isinstance(items, list):
                return [str(items)]
            result = []
            for item in items:
                if isinstance(item, str):
                    result.append(item)
                elif isinstance(item, dict):
                    result.append(" | ".join(str(v) for v in item.values()))
                else:
                    result.append(str(item))
            return result

        def to_bool(value) -> bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in ("true", "1", "yes")
            if isinstance(value, list):
                return len(value) > 0
            return bool(value)

        def to_str(value) -> str:
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                return " | ".join(str(v) for v in value.values())
            if isinstance(value, list):
                return " ".join(str(i) for i in value)
            return str(value)

        response["knowledge_gaps"] = to_str_list(response.get("knowledge_gaps", []))
        response["additional_queries_needed"] = to_str_list(response.get("additional_queries_needed", []))
        response["insufficient"] = to_bool(response.get("insufficient", False))
        response["insufficient_reason"] = to_str(response.get("insufficient_reason", "")) or None
        response["core_understanding"] = to_str(response.get("core_understanding", ""))
        response["key_dynamics"] = to_str(response.get("key_dynamics", ""))
        response["important_nuances"] = to_str(response.get("important_nuances", ""))
        response["conflicting_perspectives"] = to_str(response.get("conflicting_perspectives", ""))

        return ResearchOutput(**response)

def main():
    claims = [
        {"statement": "The Earth revolves around the Sun.", "source": "Science Textbook"},
        {"statement": "Water boils at 100 degrees Celsius.", "source": "Chemistry Textbook"}
    ]

    agent = ResearchAgent(Config.REASONING_MODEL, Config.REASONING_TEMPERATURE)
    result = agent.run(claims, topic="Solar System and Chemistry")

    print("CORE UNDERSTANDING:", result.core_understanding)
    print("CONFIDENCE:        ", result.research_confidence)
    print("GAPS:              ", result.knowledge_gaps)
    print("EXTRA QUERIES:     ", result.additional_queries_needed)
    print("INSUFFICIENT:      ", result.insufficient)

    if result.research_confidence in ("LOW", "MEDIUM"):
        print("\nNeeds more data. Sending back to Web Search Agent:")
        for q in result.additional_queries_needed:
            print(f"  - {q}")


if __name__ == "__main__":
    main()