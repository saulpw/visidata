'''gender(first_name): return predicted gender.  Requires gender-guesser library.

Possible values:
- "unknown" (name not found)
- "andy" (androgynous)
- "male"
- "female"
- "mostly_male"
- "mostly_female"
'''

import functools

@functools.lru_cache()
def gg_detect():
    import gender_guesser.detector
    return gender_guesser.detector.Detector()

def gender(first_name):
    return gg_detect().get_gender(first_name.capitalize())
