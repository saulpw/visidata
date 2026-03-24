# AI Levels for Contributions

Full policy: https://visidata.org/ai

All PRs must include an **AI Level** (0-10), disclosed in the PR body. At level 4+, the model/version must be specified. If using a bot account, identify the human operator.

## Levels

- **0**: No AI. Ethically-sourced, artisanal code.
- **1**: Human asked chatbot for ideas. Every line written by hand, no copy-paste or autocomplete.
- **2**: Human wrote nearly all code; small generated segments (boilerplate, regex). LLM autocomplete acceptable.
- **3**: Human authored code with non-trivial AI-generated portions (multi-line code, algorithms with loops).
- **4**: Human produced majority of code; AI directly created/edited files (especially docs and tests). **Claude Code usage is at minimum this level.**
- **5**: AI generated most code; human reviewed every line with complete understanding.
- **6**: AI generated majority of code; human oversaw development like a team lead, relying on empirical testing rather than full logical comprehension.
- **7**: Human specified high-level requirements; AI generated functional solutions. Human focused on testing and specs, not code scrutiny.
- **8**: Human authorized AI on tasks with minimal oversight beyond basic validation.
- **9**: Human directed AI then abandoned involvement.
- **10**: Rogue bots, zero human attention.

## Principles

- A human must vouch for the PR in good faith.
- Misrepresenting AI involvement results in dismissal.
- AI contributions are welcome when transparently disclosed and verified.
