import re
import httpx
from app.config import settings

# Defensive imports for Gemini
gemini_sdk_installed = False
if settings.GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        gemini_sdk_installed = True
    except ImportError:
        print("WARNING: google-generativeai package not installed. Gemini generation fallback disabled.")

def generate_answer_with_citations(query: str, retrieved_chunks: list[dict]) -> dict:
    """Generates an answer from an LLM grounded in retrieved chunks, forcing citations."""
    if not retrieved_chunks:
        return {
            "answer": "I could not find any relevant documents to answer your question.",
            "citations": [],
            "raw_output": "",
            "tokens_used": 0,
            "cost": 0.0
        }
        
    # Format the context block
    context_str = ""
    for idx, chunk in enumerate(retrieved_chunks, 1):
        source = chunk['metadata'].get('source', 'Unknown')
        context_str += f"--- Passage [{idx}] (Source: {source}) ---\n"
        context_str += f"{chunk['text']}\n\n"
        
    # Construct System Instruction & User Prompts
    system_instruction = (
        "You are a helpful and extremely accurate research assistant.\n"
        "Your task is to answer the user's query based ONLY on the provided passages.\n"
        "For every claim or factual statement you make, you MUST cite the passage it came from using the passage index in brackets, e.g. [1] or [2].\n"
        "If multiple passages support a claim, cite all of them, e.g. [1][3].\n"
        "If the answer cannot be found in the provided passages, state that you do not have enough information to answer.\n"
        "Do not make up facts or extrapolate beyond what is directly stated in the passages."
    )
    
    prompt = f"CONTEXT PASSAGES:\n{context_str}\nUSER QUERY: {query}\n\nYOUR ANSWER WITH CITATIONS:"
    
    answer = ""
    input_tokens = 0
    output_tokens = 0
    
    # 1. Primary: Use Groq API key if available (Ultra-low latency production model Llama 3)
    if settings.GROQ_API_KEY:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 1024
            }
            
            # Direct HTTPX call
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    answer = data['choices'][0]['message']['content']
                    input_tokens = data['usage']['prompt_tokens']
                    output_tokens = data['usage']['completion_tokens']
                else:
                    print(f"Groq API Error ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"Error during Groq generation: {e}")
            
    # 2. Secondary: Fallback to Gemini if configured and installed
    if not answer and gemini_sdk_installed:
        try:
            full_prompt = f"{system_instruction}\n\n{prompt}"
            import google.generativeai as genai
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(full_prompt)
            answer = response.text
            
            input_tokens = len(full_prompt) // 4
            output_tokens = len(answer) // 4
        except Exception as e:
            print(f"Error during Gemini generation fallback: {e}")
            
    # 3. Tertiary: Smart local mock generation fallback if no API keys are loaded
    if not answer:
        best_passage = retrieved_chunks[0]
        source_name = best_passage['metadata'].get('source', 'document.txt')
        answer = (
            f"[Grounded Mock Mode] Based on the documents provided, specifically '{source_name}', the query '{query}' "
            f"can be answered as follows: {best_passage['text'][:150]}... [1]. "
            "This provides the necessary grounded reference."
        )
        input_tokens = len(prompt) // 4
        output_tokens = len(answer) // 4
        
    # Parse Citations from the generated text
    citation_indices = set(map(int, re.findall(r'\[(\d+)\]', answer)))
    
    citations = []
    for idx in sorted(citation_indices):
        if 1 <= idx <= len(retrieved_chunks):
            chunk = retrieved_chunks[idx - 1]
            citations.append({
                "citation_index": idx,
                "source": chunk['metadata'].get('source', 'Unknown'),
                "text": chunk['text'],
                "chunk_index": chunk['metadata'].get('chunk_index', 0),
                "score": chunk.get('score', 1.0)
            })
            
    # Calculate Cost based on Llama 3 rates ($0.05/1M input, $0.08/1M output)
    input_cost = (input_tokens / 1000) * settings.INPUT_TOKEN_COST_PER_1K
    output_cost = (output_tokens / 1000) * settings.OUTPUT_TOKEN_COST_PER_1K
    total_cost = round(input_cost + output_cost, 6)
    
    return {
        "answer": answer,
        "citations": citations,
        "tokens_used": input_tokens + output_tokens,
        "cost": total_cost,
        "context_length": len(retrieved_chunks)
    }
