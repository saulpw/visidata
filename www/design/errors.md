#  Exceptions

## EscapeException

All try blocks with catch-all `except:` clauses must also have a separate `except EscapeException:` that re-raises, so that user can early-out slow operations.

## error(msg)

Raises an Exception with the given msg.  Useful for Command execstrs, lambdas, and all around conciseness.
A common pattern is e.g. `rows or error("no rows")`, which disallows an empty rowset in a minimum of code.

## exceptionCaught()

## ^E
   ^E previous [global] error traceback (g^E all prev error tracebacks; z^E for this cell caught during calcValue/typeConversion/formatValue)
## ^Q

