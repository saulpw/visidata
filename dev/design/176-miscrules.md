# Miscellanous rules discovered during implementation

- Don't put an @asynccache on calcValue, unless you know the rowdef to be simple.  asynccache will expand the entire row every time it is called, which can be more expensive than the actual calcValue.

