# Prompt Playbook v1

## Objective
Capture empirical observations comparing prompt variants and model behaviors. Use this as a living artifact you will refine in future weeks.

## How to Use This File
1. After each script run, append rows to the Results Table.
2. Tag failure modes (see legend) so patterns emerge quickly.
3. Summarize insights after completing stretch assignments.

## Scoring Rubric (1–5)
| Score | Instruction Adherence | Reasoning Depth | Style / Persona | Format Fidelity |
|-------|-----------------------|-----------------|-----------------|-----------------|
| 1 | Misses key directives | Single sentence | Ignores persona | Broken / ignores |
| 3 | Mostly follows | Some steps implicit | Partial persona | Minor drift |
| 5 | Precise & complete | Clear multi-step chain | Fully consistent | Exact, parsable |

## Failure Mode Tags
hallucination, verbosity, shallow, drift (format), persona-loss, json-break, constraint-fail

## Results Table (Populate During Lab)
| Prompt Pattern | Example Used | Model | Adherence (1–5) | Reasoning (1–5) | Style (1–5) | Format (1–5) | Failure Modes | Notes | Reuse? (Y/N) |
| Prompt Pattern | Example Used | Model | Adherence (1–5) | Reasoning (1–5) | Style (1–5) | Format (1–5) | Failure Modes | Notes | Reuse? (Y/N) |
|----------------|---------------|--------|------------------|-----------------|--------------|---------------|----------------|--------|---------------|
| Simple | Explain how to make a cup of coffee. | llama3 | 5 | 5 | 5 | 5 | verbosity | used 2 methods | |
| Role | You are a cooking instructor. Explain how to boil water to a beginner. | llama3 | 5 | 5 | 5 | 5 | | | |
| Chain-of-Thought | Explain how to boil water step-by-step, starting with choosing a pot and ending with boiling point. | llama3 | 5 | 5 | 5 | 5 | | | |
| Simple | Explain how to make a cup of coffee. | mistral | 5 | 5 | 5 | 5 | | | |
| Role | You are a cooking instructor. Explain how to boil water to a beginner. | mistral | 5 | 5 | 5 | 5 | | | |
| Chain-of-Thought | Explain how to boil water step-by-step, starting with choosing a pot and ending with boiling point. | mistral | 3 | 5 | 5 | 5 | | More consistent. Used comment instead of prompt or meaningful label | |
| Simple | Explain how to make a cup of coffee. | gemini-flash 1.5 | 3 | 5 | 3 | 1 | drift (format) | No .md format. Didn't print original prompt. | |
| Role | You are a cooking instructor. Explain how to boil water to a beginner. | gemini-flash 1.5 | 3 | 5 | 3 | 1 | drift (format) | No .md format. Didn't print original prompt. | |
| Chain-of-Thought | Explain how to boil water step-by-step, starting with choosing a pot and ending with boiling point. | gemini-flash 1.5 | 3 | 5 | 3 | 1 | drift (format) | No .md format. Didn't print original prompt. | |
| Simple | Explain how to make a cup of coffee. | claude-sonnet4.5 | 5 | 5 | 5 | 5 | | | |
| Role | You are a cooking instructor. Explain how to boil water to a beginner. | claude-sonnet4.5 | 5 | 5 | 5 | 5 | | Motivational | |
| Chain-of-Thought | Explain how to boil water step-by-step, starting with choosing a pot and ending with boiling point. | claude-sonnet4.5 | 5 | 5 | 5 | 5 | | Simple steps | |
| Simple | Explain how to make a cup of coffee. | chatgpt4o | 5 | 5 | 5 | 5 | | Icons | |
| Role | You are a cooking instructor. Explain how to boil water to a beginner. | chatgpt4o | 5 | 5 | 5 | 5 | | | |
| Chain-of-Thought | Explain how to boil water step-by-step, starting with choosing a pot and ending with boiling point. | chatgpt4o | 5 | 5 | 5 | 5 | | | |
| Simple | Explain how to make a cup of coffee. | chatgpt5 | 5 | 5 | 5 | 5 | | | |
| Role | You are a cooking instructor. Explain how to boil water to a beginner. | chatgpt5 | 5 | 5 | 5 | 5 | | | |
| Chain-of-Thought | Explain how to boil water step-by-step, starting with choosing a pot and ending with boiling point. | chatgpt5 | 5 | 5 | 5 | 5 | | | |
                                                                  |                |

## Model Summary (After Initial Pass)
| Capability | Best Model(s) | Evidence Snippet | Notes |
|------------|---------------|------------------|-------|
| Explanatory Clarity | | | |
| Chain-of-Thought | | | |
| Persona Control | | | |
| Instruction Strictness | | | |

## Insight Log
Record notable surprises, regressions, or improvements.
- ollama images were only 4 to 5 GB in size aprox. Each query takes more than 2 mins to answer back.
- Dificult to find a good prompt to see actual difference in scoring rubric.
- 


---

### 1. Role Prompting

*   **Best Practice:**
    *   Clearly define the persona or role you want the AI to adopt. This helps to set the context, tone, and level of detail in the response.
*   **Example:**
    *   Instead of "Explain black holes," use "You are an astrophysicist. Explain the concept of a black hole to a curious 10-year-old."

---

### 2. Few-Shot Learning

*   **Best Practice:**
    *   Provide a few examples of the desired input and output format. This is especially useful for tasks like classification, summarization, or code generation.
*   **Example:**
    *   When asking for a summary, provide one or two examples of a text and its corresponding summary before providing the text you want to be summarized.

---

### 3. Chain-of-Thought (CoT)

*   **Best Practice:**
    *   Encourage the model to "think step by step" or to "show its work." This is particularly effective for complex reasoning tasks, such as math problems or logic puzzles.
*   **Example:**
    *   Append "Let's think step by step" to your prompt when you need the model to reason through a problem.

---

### 4. Anti-Patterns to Avoid
## Reflection (End of Week)
Answer briefly:
1. Which two prompt patterns yielded the largest delta between models?
- I notice the Chain of thought was more simple and precise.
2. Which failure mode was most frequent? Root cause?
- First test notice some persona-loss. On second test extra info fixed it.
3. Default model choice for: explanation / reasoning / structure.
- 
4. Open questions heading into Week 2.
*   **Ambiguity:**
    *   Avoid vague or open-ended questions. Be as specific as possible.
*   **Leading Questions:**
    *   Don't phrase your prompt in a way that suggests a desired answer.
*   **Overly Complex Prompts:**
    *   Break down complex tasks into smaller, more manageable prompts.

---
