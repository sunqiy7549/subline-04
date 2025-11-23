# Functional Specification: News Summary Assistant

## 1. Goal
Create an AI-powered assistant capable of generating high-quality weekly news summaries based on collected Chinese political news data. The assistant should mimic a specific writing style and provide insightful, concise reports.

## 2. User Stories
*   **As a** content creator,
*   **I want to** feed a week's worth of collected news articles into the system,
*   **So that** I can automatically generate a draft of a weekly summary report.

*   **As a** user,
*   **I want** the system to learn/adhere to a specific "News Summary" writing style,
*   **So that** the output feels professional and consistent with my previous work.

## 3. Core Features
*   **Data Ingestion**: Ability to read news data (likely from the existing News Aggregator database/files).
*   **Summarization Engine**:
    *   Input: Multiple news articles (text).
    *   Process: Analyze, cluster, and summarize.
    *   Output: A structured weekly report.
*   **Style Customization**: The ability to "train" or "prompt" the AI with examples of the desired style.

## 4. Constraints & Questions (To Be Clarified)
*   **Input Data Source**: Will this read directly from the `news_aggregator` SQLite DB? Or text files?
*   **Training Method**: Shall we use "Few-Shot Prompting" (providing examples in the prompt) or "Fine-Tuning" (training a custom model)? *Recommendation: Start with Few-Shot Prompting using a high-end model (Gemini Pro/GPT-4) for agility.*
*   **Output Format**: Markdown? PDF? HTML?

## 5. Success Metrics
*   The generated summary requires minimal human editing (< 5 minutes of edits per report).
*   The style matches the provided examples.
