# AI Summary Assistant Training Guide

## 1. Data Assessment
*   **Dataset Size**: ~120 pairs (Korean Summary + Chinese Original).
*   **Nature**: Cross-lingual summarization with specific stylistic requirements (MOFA style).
*   **Quality**: High (Verified matches, specific format).

## 2. Recommended Strategy

Given the dataset size (120 examples), you have two main approaches. I recommend starting with **Option A** as it requires no technical training setup and yields immediate results.

### Option A: In-Context Learning (Many-Shot Prompting) [Recommended Start]
Instead of "training" (modifying the model's weights), you feed a large number of examples (e.g., 20-50) into the model's *context window* as part of the prompt.

*   **Why**:
    *   **Zero Setup**: No training pipeline needed.
    *   **Flexible**: You can change the style instantly by changing the examples in the prompt.
    *   **Gemini 1.5 Advantage**: Gemini 1.5 Pro has a huge context window (1-2 Million tokens). You can fit *your entire dataset* into the prompt if you want, allowing the model to learn the style perfectly on the fly.
*   **How**:
    *   Construct a prompt:
        ```text
        System: You are an expert analyst for the Korean Ministry of Foreign Affairs. Summarize the Chinese news article into the specific Korean report format.
        
        Example 1:
        [Chinese Content]
        ...
        [Korean Summary]
        ...
        
        Example 2:
        ...
        
        (Repeat for 20+ examples)
        
        Current Article:
        [New Chinese Content]
        ```

### Option B: Fine-Tuning (PEFT/LoRA)
If you want to reduce costs (shorter prompts) or ensure strict adherence to format without providing examples every time, you can "fine-tune" a model.

*   **Why**:
    *   **Efficiency**: Shorter prompts (save money/time on input tokens).
    *   **Consistency**: The model "memorizes" the style.
*   **Suitable Models**:
    *   **Gemini 1.5 Flash**: Fast, cheap, excellent for fine-tuning on specific tasks.
    *   **GPT-4o-mini**: Also a good option for cost-effective fine-tuning.
*   **How**:
    1.  Convert `dataset.json` to JSONL format (Input: Chinese, Output: Korean).
    2.  Upload to Google AI Studio or OpenAI Platform.
    3.  Run a fine-tuning job (takes ~10-20 mins for 120 examples).

## 3. Model Recommendation

| Feature | **Gemini 1.5 Pro** | **Gemini 1.5 Flash** | **GPT-4o** |
| :--- | :--- | :--- | :--- |
| **Role** | **Best Quality (In-Context)** | **Best Efficiency (Fine-Tuned)** | Strong Alternative |
| **Reason** | Huge context window allows "reading" all your examples at once. Best reasoning. | Very fast and cheap. Fine-tuning it makes it a specialist. | Good reasoning, but context window management is trickier for many-shot. |
| **Verdict** | **Use for Prototyping/High Quality** | **Use for Production/Batch Processing** | |

## 4. Next Steps (Action Plan)

1.  **Data Preparation**: Convert `dataset.json` to JSONL format.
2.  **Test Option A**: Use a script to send a request to Gemini 1.5 Pro with 10 examples.
3.  **Decide**: If Option A works, stick with it. If you need faster/cheaper inference, proceed to Option B.
