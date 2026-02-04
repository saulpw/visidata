'''
# LLM Analysis Feature

Analyze column data using Anthropic Claude LLM with natural language queries.

## Usage

1. Position cursor on a column containing text data
2. Run `llm-analyze-column` command (or `llm-analyze-selected` for selected rows only)
3. Enter your analysis query (e.g. "Did the model exhibit reasoning?")
4. Four new columns will be added with results:
   - `{colname}_llm_score` (0-1 float score)
   - `{colname}_llm_analysis` (text explanation)
   - `{colname}_llm_raw` (hidden raw JSON response)
   - `{colname}_llm_tokens` (token count for cost tracking)

## Configuration

Set in ~/.visidatarc or via environment variables:

    options.llm_model = "claude-haiku-4-5"
    options.llm_max_tokens = 1024
    options.llm_temperature = 1.0
    options.llm_rate_delay = 0.5  # seconds between requests
    options.llm_template_path = ""  # path to custom template file

    export ANTHROPIC_API_KEY="..."
## Custom Templates

Create a text file with {query} and {text} placeholders:

    Analyze this text: {text}
    Question: {query}
    Return JSON: {{"score": 0-1, "analysis": "explanation"}}

Then set: `options.llm_template_path = "/path/to/template.txt"`
'''

import os
import time
import json
import re

from visidata import vd, VisiData, Sheet, SettableColumn, asyncthread, Progress

# Configuration options
vd.option('llm_model', 'claude-haiku-4-5', 'Anthropic model name')
vd.option('llm_max_tokens', 1024, 'max tokens for LLM response')
vd.option('llm_temperature', 1.0, 'temperature for LLM sampling (0-1)')
vd.option('llm_rate_delay', 0.1, 'delay in seconds between API requests')
vd.option('llm_template_path', '', 'path to custom template file (empty = use default)')

# Default template with structured JSON output
DEFAULT_TEMPLATE = '''Analyze the following text and respond in JSON format.

Query: {query}
Text: {text}

Provide:
1. A score from 0 to 1 indicating how well the text matches or satisfies the query
2. A brief analysis explaining your reasoning

Response format: {{"score": <float 0-1>, "analysis": "<text>"}}'''


@VisiData.lazy_property
def anthropic_client(vd):
    'Initialize and return Anthropic API client.'
    anthropic = vd.importExternal('anthropic')
    api_key = os.environ.get('ANTHROPIC_API_KEY') or vd.fail('set $ANTHROPIC_API_KEY (Get API key from https://console.anthropic.com/')
    return anthropic.Anthropic(api_key=api_key)


@VisiData.api
def loadLLMTemplate(vd):
    'Load LLM template from file or return default template.'
    template_path = vd.options.llm_template_path
    if template_path:
        try:
            with open(template_path) as f:
                return f.read()
        except Exception as e:
            vd.exceptionCaught(e)
            vd.fail(f'Could not load template from {template_path}')

    return DEFAULT_TEMPLATE


@VisiData.api
def queryLLM(vd, prompt):
    'Query Anthropic LLM with prompt and return parsed response.'
    response = vd.anthropic_client.messages.create(
        model=vd.options.llm_model,
        max_tokens=vd.options.llm_max_tokens,
        temperature=vd.options.llm_temperature,
        messages=[{'role': 'user', 'content': prompt}]
    )

    raw_text = response.content[0].text
    tokens = response.usage.input_tokens + response.usage.output_tokens

    # Try to parse JSON response
    try:
        data = json.loads(raw_text)
        score = float(data.get('score', 0))
        analysis = str(data.get('analysis', ''))
    except (json.JSONDecodeError, ValueError, KeyError):
        # Fallback: try to extract score with regex
        score_match = re.search(r'"?score"?\s*:\s*(\d+\.?\d*)', raw_text)
        score = float(score_match.group(1)) if score_match else None
        analysis = raw_text  # use raw response as analysis

    return {
        'score': score,
        'analysis': analysis,
        'raw': raw_text,
        'tokens': tokens
    }


@Sheet.api
@asyncthread
def llmAnalyzeColumn(sheet, col, rows, query):
    'Analyze column data with LLM using given query.'
    # Load template
    template = vd.loadLLMTemplate()

    # Warn about large datasets
    n_rows = len(rows)
    if n_rows > 100:
        if not vd.confirm(f'Analyze {n_rows} rows? This may take some time and money.'):
            return

    # Create result columns
    score_col = SettableColumn(f'{col.name}_llm_score', type=float)
    analysis_col = SettableColumn(f'{col.name}_llm_analysis', type=str, width=40)
    raw_col = SettableColumn(f'{col.name}_llm_raw', type=str, width=0)  # hidden
    tokens_col = SettableColumn(f'{col.name}_llm_tokens', type=int, width=8)

    sheet.addColumnAtCursor(score_col, analysis_col, raw_col, tokens_col)

    # Track statistics
    processed = 0
    skipped = 0
    errors = 0
    total_tokens = 0

    # Process rows sequentially
    for row in Progress(rows, gerund='analyzing with LLM'):
        cell_text = col.format(col.getTypedValue(row))

        # Skip empty cells
        if not cell_text or str(cell_text).strip() == '':
            skipped += 1
            continue

        # Truncate if too long (rough estimate: 4 chars ≈ 1 token)
        max_chars = vd.options.llm_max_tokens * 3
        if len(cell_text) > max_chars:
            cell_text = cell_text[:max_chars] + '...'
            vd.warning(f'Cell content truncated (exceeded {max_chars} chars)')

        # Build prompt
        prompt = template.format(query=query, text=cell_text)

        # Call API with error handling
        try:
            result = vd.queryLLM(prompt)

            score_col.setValue(row, result['score'])
            analysis_col.setValue(row, result['analysis'])
            raw_col.setValue(row, result['raw'])
            tokens_col.setValue(row, result['tokens'])

            total_tokens += result['tokens']
            processed += 1

        except Exception as e:
            vd.exceptionCaught(e)
            analysis_col.setValue(row, f'Error: {e}')
            errors += 1

        # Rate limiting
        time.sleep(vd.options.llm_rate_delay)

    # Report results
    msg = f'LLM analysis complete: {processed} rows processed'
    if skipped > 0:
        msg += f', {skipped} skipped (empty)'
    if errors > 0:
        msg += f', {errors} errors'
    if total_tokens > 0:
        msg += f' ({total_tokens} tokens)'

    vd.status(msg)


# Command bindings - no default keybindings, users can add their own
Sheet.addCommand('', 'llm-analyze-column',
    'llmAnalyzeColumn(cursorCol, rows, vd.input("LLM query: ", type="llm-query"))',
    'analyze all rows in current column with LLM')

Sheet.addCommand('', 'llm-analyze-selected',
    'llmAnalyzeColumn(cursorCol, someSelectedRows, vd.input("LLM query: ", type="llm-query"))',
    'analyze selected rows only with LLM')

# Menu integration
vd.addMenuItems('''
    Column > Analyze with LLM > all rows > llm-analyze-column
    Column > Analyze with LLM > selected rows > llm-analyze-selected
''')
