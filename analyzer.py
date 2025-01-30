import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.chains import create_extraction_chain
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Load environment variables
load_dotenv()

def find_pdf_files(directory):
    """
    Recursively find all PDF files in the given directory and its subdirectories.
    """
    pdf_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    return pdf_files

def analyze_threat_intel_pdf(pdf_path, keyword=None):
    """
    Analyze a threat intelligence PDF and extract key information.
    If keyword is provided, focus on information related to that keyword.
    """
    try:
        # Load PDF
        loader = PyPDFLoader(pdf_path)
        pages = loader.load_and_split()
        
        # Split text into manageable chunks
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        texts = text_splitter.split_documents(pages)
        
        # Define the schema for information extraction
        schema = {
            "properties": {
                "threat_actor": {"type": "string", "description": "Name of the threat actor or group"},
                "malware_name": {"type": "string", "description": "Names of any malware mentioned"},
                "attack_vector": {"type": "string", "description": "Methods used to carry out the attack"},
                "indicators": {"type": "string", "description": "IOCs like IP addresses, domains, or file hashes"},
                "targeted_sectors": {"type": "string", "description": "Industries or sectors targeted"},
                "severity": {"type": "string", "description": "Severity level of the threat"},
                "relevance": {"type": "string", "description": "Relevance to the search keyword"},
            },
            "required": ["threat_actor", "malware_name", "attack_vector"],
        }
        
        # Initialize LLM
        llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
        
        # If keyword is provided, create a specific prompt for keyword-focused analysis
        if keyword:
            prompt = PromptTemplate(
                input_variables=["text", "keyword"],
                template="""
                Analyze the following threat intelligence text, focusing specifically on information related to '{keyword}':
                
                {text}
                
                Extract and summarize any threat intelligence information related to '{keyword}', including:
                1. How it relates to any threat actors
                2. Its role in attack vectors or techniques
                3. Associated malware or tools
                4. Related indicators of compromise
                5. Targeted sectors or victims
                6. Severity or impact
                
                If there's no relevant information about '{keyword}', indicate that clearly.
                """
            )
            keyword_chain = LLMChain(llm=llm, prompt=prompt)
        
        # Create extraction chain
        extraction_chain = create_extraction_chain(schema, llm)
        
        # Process each chunk and extract information
        all_results = []
        for text in texts:
            try:
                # If keyword is provided, first check relevance
                if keyword:
                    keyword_analysis = keyword_chain.run(text=text.page_content, keyword=keyword)
                    if "no relevant information" in keyword_analysis.lower():
                        continue
                
                # Extract structured information
                result = extraction_chain.run(text.page_content)
                if result:
                    # Add keyword relevance if applicable
                    if keyword:
                        for item in result:
                            item["relevance"] = keyword_analysis
                    all_results.extend(result)
                    
            except Exception as e:
                print(f"Error processing chunk in {pdf_path}: {e}")
        
        return all_results
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {e}")
        return []

def format_results(results, pdf_path, keyword=None):
    """
    Format the analysis results into a readable summary.
    """
    summary = f"\nAnalysis Results for: {os.path.basename(pdf_path)}\n"
    summary += "=" * (len(summary) - 1) + "\n"
    
    if not results:
        if keyword:
            summary += f"No relevant threat intelligence found for keyword: {keyword}\n"
        else:
            summary += "No threat intelligence findings to report.\n"
        return summary
    
    if keyword:
        summary += f"Analysis focused on keyword: {keyword}\n"
        summary += "-" * 40 + "\n\n"
    
    for idx, result in enumerate(results, 1):
        summary += f"Finding {idx}:\n"
        summary += "-" * 10 + "\n"
        # First show relevance if it exists
        if "relevance" in result and result["relevance"]:
            summary += f"Relevance: {result['relevance']}\n\n"
        
        # Then show other fields
        for key, value in result.items():
            if value and key != "relevance":  # Skip empty values and already shown relevance
                summary += f"{key.replace('_', ' ').title()}: {value}\n"
        summary += "\n"
    
    return summary

def main():
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    # Get directory path from user
    directory = input("Enter the path to the directory containing threat intelligence PDFs: ")
    
    if not os.path.exists(directory):
        print(f"Error: Directory not found at {directory}")
        return
    
    # Get optional keyword from user
    keyword = input("Enter a keyword to focus the analysis (or press Enter to analyze everything): ").strip()
    if not keyword:
        keyword = None
    
    # Find all PDF files
    pdf_files = find_pdf_files(directory)
    
    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return
    
    print(f"\nFound {len(pdf_files)} PDF files to analyze.")
    
    # Create output directory for results
    timestamp = os.path.join("analysis_results", f"analysis_{os.path.basename(directory)}_{os.path.basename(os.path.dirname(directory))}")
    os.makedirs(timestamp, exist_ok=True)
    
    # Process each PDF
    all_summaries = []
    for i, pdf_path in enumerate(pdf_files, 1):
        try:
            print(f"\nProcessing {i}/{len(pdf_files)}: {os.path.basename(pdf_path)}")
            results = analyze_threat_intel_pdf(pdf_path, keyword)
            summary = format_results(results, pdf_path, keyword)
            all_summaries.append(summary)
            
            # Save individual results
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            individual_output = os.path.join(timestamp, f"{pdf_name}_analysis.txt")
            with open(individual_output, "w", encoding="utf-8") as f:
                f.write(summary)
            
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")
    
    # Save combined results
    combined_output = os.path.join(timestamp, "combined_analysis.txt")
    with open(combined_output, "w", encoding="utf-8") as f:
        f.write("Combined Threat Intelligence Analysis\n")
        f.write("==================================\n\n")
        f.write("\n".join(all_summaries))
    
    print(f"\nAnalysis complete! Results have been saved to:")
    print(f"- Combined results: {combined_output}")
    print(f"- Individual results: {timestamp}/*.txt")

if __name__ == "__main__":
    main()
