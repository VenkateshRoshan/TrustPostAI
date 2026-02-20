# agents/writer.py

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

class WriterAgent:
    def __init__(self, model_name: str = "llama3.2:1b", temperature: float = 0.7):
        self.llm_model = ChatOllama(model=model_name, temperature=temperature)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """
You are a social media content writer. 
Your only job is to convert the given context into a social media post.
             
STRICT RULES:
- Use only the claims provided in the context.
- Do not add any new facts.
- Do not assume or infer missing information.
- Do not access any external knowledge or databases.
- Do not use any information that is not explicitly stated in the context.
- Do not use emdash.
             
You're a language formatter not a researcher. Your task is to take the provided context and format it into a social media post without adding any new information or making any assumptions.
"""),
        ("human", """Platform: {platform}
Tone: {tone}
Format: {format}

Claims to write from:
{claims}

Write the content now.""")
        ])

    def run(self, claims: list, platform: str, tone: str, format: str) -> str:
        # formatted_claims = "\n".join(
        #     [f"- {claim.statement} (Source: {claim.source})" for claim in claims]
        # )

        chain = self.prompt | self.llm_model

        response = chain.invoke({
            "platform": platform,
            "tone": tone,
            "format": format,
            # "claims": formatted_claims
            "claims": claims
        })

        return response.content
    
def main():
    claims = [
        {"statement": "The Earth revolves around the Sun.", "source": "Science Textbook"},
        {"statement": "Water boils at 100 degrees Celsius.", "source": "Chemistry Textbook"}
    ]
    agent = WriterAgent()
    post = agent.run(claims, platform="Medium", tone="Informative", format="Text")
    print(post)

if __name__ == "__main__":
    main()