# requires gender-guesser

import functools

@functools.lru_cache()
def gg_detect():
    import gender_guesser.detector
    return gender_guesser.detector.Detector()

def gender(first_name):
    return gg_detect().get_gender(first_name.capitalize())
