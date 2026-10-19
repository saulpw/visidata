'''
# LLM Analysis Feature

Analyze column data using Anthropic Claude LLM with natural language queries.

## Usage

1. `pip install anthropic`, set `ANTHROPIC_API_KEY`, and add
   `import visidata.experimental.llm` to ~/.visidatarc
2. Position cursor on a column containing text data
3. Run `llm-analyze-column` command (or `llm-analyze-selected` for selected rows only)
4. Enter your analysis query (e.g. "Did the model exhibit reasoning?")
5. Four new columns will be added with results:
   - `{colname}_llm_score` (0-1 float score)
   - `{colname}_llm_analysis` (text explanation)
   - `{colname}_llm_raw` (hidden raw JSON response)
   - `{colname}_llm_tokens` (token count for cost tracking)

## Configuration

Set in ~/.visidatarc or via environment variables:

    options.llm_model = "claude-opus-5-5"
    options.llm_max_tokens = 16000
    options.llm_rate_delay = 0.1  # seconds between requests
    options.llm_template_path = ""  # path to custom template file

    export ANTHROPIC_API_KEY="..."

## Custom Templates

Create a text file with {query} and {text} placeholders.  The response is
constrained to JSON with `score` and `analysis` fields, so the template
only needs to say what to judge:

    Analyze this text: {text}
    Question: {query}

Then set: `options.llm_template_path = "/path/to/template.txt"`
'''

import os
import time
import json
import re

from visidata import vd, VisiData, Sheet, TextSheet, SettableColumn, asyncthread, Progress

# Configuration options
vd.option('llm_model', 'claude-opus-5-5', 'Anthropic model name')
vd.option('llm_max_tokens', 16000, 'max tokens for LLM response, including thinking')
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

RESPONSE_FORMAT = {
    'type': 'json_schema',
    'schema': {
        'type': 'object',
        'properties': {
            'score': {'type': 'number'},
            'analysis': {'type': 'string'},
        },
        'required': ['score', 'analysis'],
        'additionalProperties': False,
    },
}


@VisiData.lazy_property
def anthropic_client(vd):
    'Initialize and return Anthropic API client.'
    api_key = os.environ.get('ANTHROPIC_API_KEY') or vd.fail('set $ANTHROPIC_API_KEY (Get API key from https://console.anthropic.com/')
    anthropic = vd.importExternal('anthropic')
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
def llmRequest(vd, prompt, **kwargs):
    'Return the API request arguments for *prompt*.'
    return dict(
        model=vd.options.llm_model,
        max_tokens=vd.options.llm_max_tokens,
        betas=['server-side-fallback-2026-07-01'],
        fallbacks='default',
        messages=[{'role': 'user', 'content': prompt}],
        **kwargs
    )


@VisiData.api
def llmResult(vd, response):
    'Return (response text, total tokens) from a finished API *response*.'
    if response.stop_reason == 'refusal':
        vd.fail('LLM declined the request')

    text = ''.join(b.text for b in response.content if b.type == 'text')
    return text, response.usage.input_tokens + response.usage.output_tokens


@VisiData.api
def llmCreate(vd, prompt, **kwargs):
    'Send *prompt* to the LLM and return (response text, total tokens).'
    return vd.llmResult(vd.anthropic_client.beta.messages.create(**vd.llmRequest(prompt, **kwargs)))


@VisiData.api
def queryLLM(vd, prompt):
    'Query Anthropic LLM with prompt and return parsed response.'
    raw_text, tokens = vd.llmCreate(prompt, output_config={'format': RESPONSE_FORMAT})

    # Try to parse JSON response
    try:
        data = json.loads(re.sub(r'^\s*```(?:json)?\s*|\s*```\s*$', '', raw_text))
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
def llmAnalyzeColumn(sheet, col, rows, query=None):
    'Analyze column data with LLM using given query.'
    vd.anthropic_client
    template = vd.loadLLMTemplate()

    if query is None:
        query = vd.input('LLM query: ', type='llm-query')

    # Warn about large datasets
    n_rows = len(rows)
    if n_rows > 100:
        vd.confirm(f'Analyze {n_rows} rows? This may take some time and money.')

    sheet.llmAnalyzeRows(col, rows, query, template)


@Sheet.api
@asyncthread
def llmAnalyzeRows(sheet, col, rows, query, template):
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


@Sheet.api
def llmQueryRows(sheet, rows, query=None):
    'Send *rows* (visible columns, as JSON) to the LLM in one request with *query*; show the reply in a new sheet.'
    vd.anthropic_client
    if query is None:
        query = vd.input('LLM query over rows: ', type='llm-query')

    if len(rows) > 100:
        vd.confirm(f'Send {len(rows)} rows to LLM in one query? This may take some time and money.')

    cols = sheet.visibleCols
    data = [{c.name: c.getDisplayValue(r) for c in cols} for r in rows]
    prompt = f'{query}\n\nData from the sheet "{sheet.name}", one JSON object per row:\n{json.dumps(data, ensure_ascii=False)}'
    sheet.llmQueryPrompt(prompt, len(rows))


@Sheet.api
@asyncthread
def llmQueryPrompt(sheet, prompt, nrows):
    vd.status(f'sending {nrows} rows to LLM')
    vs = TextSheet(sheet.name, 'llm', source=[])
    vs.rows = [[1, '']]
    vd.push(vs)

    with vd.anthropic_client.beta.messages.stream(**vd.llmRequest(prompt)) as stream:
        for chunk in stream.text_stream:
            first, *rest = chunk.split('\n')
            vs.rows[-1][1] += first
            for line in rest:
                vs.addRow([len(vs.rows)+1, line])
        _, tokens = vd.llmResult(stream.get_final_message())

    vd.status(f'LLM query complete ({tokens} tokens)')


# Command bindings - no default keybindings, users can add their own
Sheet.addCommand('', 'llm-analyze-column',
    'llmAnalyzeColumn(cursorCol, rows)',
    'analyze all rows in current column with LLM', testable=False)

Sheet.addCommand('', 'llm-analyze-selected',
    'llmAnalyzeColumn(cursorCol, someSelectedRows)',
    'analyze selected rows only with LLM', testable=False)

Sheet.addCommand('', 'llm-query-sheet',
    'llmQueryRows(rows)',
    'send all rows to LLM in one query and show the reply', testable=False)

Sheet.addCommand('', 'llm-query-selected',
    'llmQueryRows(someSelectedRows)',
    'send selected rows to LLM in one query and show the reply', testable=False)

# Menu integration
vd.addMenuItems('''
    Column > Analyze with LLM > all rows > llm-analyze-column
    Column > Analyze with LLM > selected rows > llm-analyze-selected
    Data > Query LLM > all rows > llm-query-sheet
    Data > Query LLM > selected rows > llm-query-selected
''')
