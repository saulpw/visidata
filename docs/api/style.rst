Guide Style Guide
=================

General Notes
-------------

- Review first sentences `with this in mind <https://jamesg.blog/2023/12/03/first-sentences/>`_.
- In general, do not use second person (you/your) outside of tutorials.

Referenced from `Simplified Technical English <https://en.wikipedia.org/wiki/Simplified_Technical_English>`_:

- Make instructions as clear and specific as possible.
- Use the approved forms of the verb:
    - The infinitive
    - The imperative
    - The simple present tense
    - The simple past tense
    - The past participle (only as an adjective)
    - The future tense
- Do not use helping verbs to make `complex verb structures <https://www.utsa.edu/twc/documents/Complex%20Verb%20Phrases.pdf>`_.
- Use the "-ing" form of a verb only as a technical name or as a modifier in a technical name.
- Do not use passive voice in procedures.
- Use the active voice as much as possible in descriptive texts.
- Prefer short sentences and simpler word choices.
- Do not omit parts of the sentence (e.g. verb, subject, article) to make your text shorter.
- Use vertical lists for complex text.
- Write one instruction per sentence.
- Write only one topic per paragraph.

Color/Markup Standards
-----------------------

- VisiData documentation uses `basic markdown <https://www.markdownguide.org/basic-syntax/>`_ like # Headings, \*\*bold\*\*, \*italics\*, \`code snippets\`, and \_underscore\_.

- Internally, VisiData has its `own display attribute syntax </docs/colors#attrs>`_. Some example usage:
    - ``[:onclick <url>]<text>[/]`` formats ``<text>`` into a clickable url that will open in ``$BROWSER``.
    - ``[:red on black]<sentence>[/]`` changes the color of ``<sentence>`` to be red text on black background.
      Any VisiData color option name can be used after ``:``, like ``[:warning]``, ``[:error]``, ``[:menu]``.
      Preference is for using ``[:option_name]`` instead of hard-coded colors when possible.
    - e.g. Use ``[:keys]`` for keystrokes and longnames, and ``[:code]`` for Python and other actual code.

- List relevant commands with the general pattern: ``- [:keys]<keystroke>[/] ([:code]<longname>[/]) to <command helpstring>``.
    - Use ``{help.commands.<longname>}`` to get the **GuideSheet** to replace it with the properly formatted string above. You can write it out manually if that would result in more detail or clarity, but it's much more preferred to adjust the docstring so that this pattern would work. 

- List relevant options with ``[:onclick options-sheet <option name>][:code]option name>[/] to <option helpstring> (default: <option default value>)``.
  - Similarly, use ``{help.options.<option-name>}`` to expand into the above, and prefer to modify the helpstring instead of writing it out manually.
