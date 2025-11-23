import json
import os

DATASET_FILE = "data/dataset.json"
OUTPUT_FILE = "data/training_data.jsonl"

def main():
    if not os.path.exists(DATASET_FILE):
        print(f"Error: {DATASET_FILE} not found.")
        return

    with open(DATASET_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Converting {len(data)} items to JSONL format...")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for item in data:
            # Construct the training example
            # Input: Chinese Content
            # Output: Korean Summary (MOFA Style)
            
            # We can also include the Chinese Title in the input for context
            user_input = f"Title: {item['chinese_title']}\n\nContent:\n{item['chinese_content']}"
            
            # The model output should be the Korean summary
            model_output = item['korean_summary']
            
            # Gemini / OpenAI Chat Format
            # {"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "model", "content": "..."}]}
            
            example = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert analyst for the Korean Ministry of Foreign Affairs. Summarize the provided Chinese news article into a specific Korean report format, including the headline and bullet points."
                    },
                    {
                        "role": "user",
                        "content": user_input
                    },
                    {
                        "role": "model", # Or "assistant" for OpenAI
                        "content": model_output
                    }
                ]
            }
            
            f.write(json.dumps(example, ensure_ascii=False) + "\n")

    print(f"Done. Saved to {OUTPUT_FILE}")
    print("You can now upload this file to Google AI Studio or OpenAI Platform for fine-tuning.")

if __name__ == "__main__":
    main()
