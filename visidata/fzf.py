# Assumptions
# - everything will be ASCII and lowercase
import collections
from enum import Enum
from visidata import VisiData, vd

DEBUG = False

Result = collections.namedtuple('Result', 'start end score positions')

scoreMatch        = 16
scoreGapStart     = -3
scoreGapExtension = -1

# We prefer matches at the beginning of a word, but the bonus should not be
# too great to prevent the longer acronym matches from always winning over
# shorter fuzzy matches. The bonus point here was specifically chosen that
# the bonus is cancelled when the gap between the acronyms grows over
# 8 characters, which is approximately the average length of the words found
# in web2 dictionary and my file system.
bonusBoundary = scoreMatch / 2

# Although bonus point for non-word characters is non-contextual, we need it
# for computing bonus points for consecutive chunks starting with a non-word
# character.
bonusNonWord = scoreMatch / 2

# Edge-triggered bonus for matches in camelCase words.
# Compared to word-boundary case, they don't accompany single-character gaps
# (e.g. FooBar vs. foo-bar), so we deduct bonus point accordingly.
bonusCamel123 = bonusBoundary + scoreGapExtension

# Minimum bonus point given to characters in consecutive chunks.
# Note that bonus points for consecutive matches shouldn't have needed if we
# used fixed match score as in the original algorithm.
bonusConsecutive = -(scoreGapStart + scoreGapExtension)

# The first character in the typed pattern usually has more significance
# than the rest so it's important that it appears at special positions where
# bonus points are given, e.g. "to-go" vs. "ongoing" on "og" or on "ogo".
# The amount of the extra bonus should be limited so that the gap penalty is
# still respected.
bonusFirstCharMultiplier = 2

# Extra bonus for word boundary after whitespace character or beginning of the string
bonusBoundaryWhite = bonusBoundary + 2

# Extra bonus for word boundary after slash, colon, semi-colon, and comma
bonusBoundaryDelimiter = bonusBoundary + 1


def try_skip(input_, char, from_):
    return input_.find(char, from_)

def ascii_fuzzy_index(input_, pattern):
    """ determines the position of the pattern
        -1, if pattern isn't a fuzzy match
        also, position is adapted one back, if possible
        (for reasons not yet clear to me -- comment says "right bonus point")
    """
    first_idx, idx = 0, 0
    for pidx in range(len(pattern)):
        idx = try_skip(input_, pattern[pidx], idx)
        if idx < 0:
            return -1
        if pidx == 0 and idx > 0:
            # Step back to find the right bonus point
            first_idx = idx - 1
        idx += 1
    return first_idx

delimiterChars = "/,:;|"

whiteChars = " \t\n\v\f\r\x85\xA0"


charWhite, charNonWord, charDelimiter, charLower, charUpper, charLetter, charNumber = range(7)
initialCharClass = charWhite

def charClassOfAscii(char):
    if char >= 'a' and char <= 'z':
        return charLower
    elif char >= 'A' and char <= 'Z':
        return charUpper
    elif char >= '0' and char <= '9':
        return charNumber
    elif char in whiteChars:
        return charWhite
    elif char in delimiterChars:
        return charDelimiter
    return charNonWord


def bonusFor(prevClass , class_):
    if class_ > charNonWord:
        if prevClass == charWhite:
            # Word boundary after whitespace
            return bonusBoundaryWhite
        elif prevClass == charDelimiter:
            # Word boundary after a delimiter character
            return bonusBoundaryDelimiter
        elif prevClass == charNonWord:
            # Word boundary
            return bonusBoundary
    if (prevClass == charLower and class_ == charUpper or
        prevClass != charNumber and class_ == charNumber):
        # camelCase letter123
        return bonusCamel123
    elif class_ == charNonWord:
        return bonusNonWord
    elif class_ == charWhite:
        return bonusBoundaryWhite
    return 0

def debugV2(T, pattern, F, lastIdx, H, C):
    width = lastIdx - F[0] + 1

    for i, f in enumerate(F):
        I = i * width
        if i == 0:
            print("  ", end='')
            for j in range(f, lastIdx+1):
                print(f" {T[j]} ", end='')
            print()
        print(pattern[i] + " ", end='')
        for idx in range(F[0], f):
            print(" 0 ", end='')
        for idx in range(f, lastIdx+1):
            print(f"{int(H[i*width+idx-int(F[0])]):2d} ", end='')
        print()

        print("  ", end='')
        for idx, p in enumerate(C[I : I+width]):
            if idx+int(F[0]) < int(F[i]):
                p = 0
            if p > 0:
                print(f"{p:2d} ", end='')
            else:
                print("   ", end='')
        print()


@VisiData.api
def fuzzymatch(vd, input_:str, pattern:str) -> Result:
    '''
    TODO: basic usage
    '''
    M = len(pattern)
    if M == 0:
        return Result(0,0,0,[])
    N = len(input_)

    # Phase 1: Optimized search for ASCII string
    idx = ascii_fuzzy_index(input_, pattern)
    if idx < 0:
        return Result(-1, -1, 0, None)

    H0 = [0]*N
    C0 = [0]*N
    # Bonus point for each position
    B = [0]*N
    # The first occurrence of each character in the pattern
    F = [0]*M
    T = list(input_)

    # Phase 2: Calculate bonus for each point
    maxScore, maxScorePos = 0,0
    pidx, lastIdx = 0,0
    pchar0, pchar, prevH0, prevClass, inGap = pattern[0], pattern[0], 0, initialCharClass, False
    Tsub = T[idx:]
    H0sub, C0sub, Bsub = H0[idx:], C0[idx:], B[idx:]

    for off, char in enumerate(Tsub):
        class_ = charClassOfAscii(char)
        # Tsub[off] = char
        bonus = bonusFor(prevClass, class_)
        Bsub[off] = bonus
        prevClass = class_

        if char == pchar:
            if pidx < M:
                F[pidx] = idx + off
                pidx += 1
                pchar = pattern[min(pidx, M-1)]
            lastIdx = idx + off

        if char == pchar0:
            score = scoreMatch + bonus*bonusFirstCharMultiplier
            H0sub[off] = score
            C0sub[off] = 1
            if M == 1 and (score > maxScore):
                maxScore, maxScorePos = score, idx+off
                if bonus >= bonusBoundary:
                    break
            inGap = False
        else:
            if inGap:
                H0sub[off] = max(prevH0+scoreGapExtension, 0)
            else:
                H0sub[off] = max(prevH0+scoreGapStart, 0)
            C0sub[off] = 0
            inGap = True
        prevH0 = H0sub[off]

    # write back, because slices in python are a full copy (as opposed to go)
    H0[idx:], C0[idx:], B[idx:] = H0sub, C0sub, Bsub


    if pidx != M:
        return Result(-1, -1, 0, None)
    if M == 1:
        return Result(maxScorePos, maxScorePos + 1, maxScore, [maxScorePos])

    # Phase 3: Fill in score matrix (H)
    # do not allow omission.
    f0 = F[0]
    width = lastIdx - f0 + 1
    H = [0]*width*M
    H[:width] = list(H0[f0:lastIdx+1])

    # Possible length of consecutive chunk at each position.
    C = [0]*width*M
    C[:width] = C0[f0:lastIdx+1]

    Fsub = F[1:]
    Psub = pattern[1:]
    for off, f in enumerate(Fsub):
        pchar = Psub[off]
        pidx = off + 1
        row = pidx * width
        inGap = False
        Tsub = T[f : lastIdx+1]
        Bsub = B[f:][:len(Tsub)]
        H[row+f-f0-1] = 0
        for off, char in enumerate(Tsub):
            Cdiag = C[row+f-f0-1-width:][:len(Tsub)]
            Hleft = H[row+f-f0-1:][:len(Tsub)]
            Hdiag = H[row+f-f0-1-width:][:len(Tsub)]
            col = off + f
            s1, s2, consecutive = 0, 0, 0

            if inGap:
                s2 = Hleft[off] + scoreGapExtension
            else:
                s2 = Hleft[off] + scoreGapStart

            if pchar == char:
                s1 = Hdiag[off] + scoreMatch
                b = Bsub[off]
                consecutive = Cdiag[off] + 1
                if consecutive > 1:
                    fb = B[col-consecutive+1]
                    # Break consecutive chunk
                    if b >= bonusBoundary and b > fb:
                        consecutive = 1
                    else:
                        b = max(b, max(bonusConsecutive, fb))
                if s1+b < s2:
                    s1 += Bsub[off]
                    consecutive = 0
                else:
                    s1 += b
            C[row+f-f0+off] = consecutive

            inGap = s1 < s2
            score = max(max(s1, s2), 0)
            if pidx == M-1 and score > maxScore:
                maxScore, maxScorePos = score, col
            H[row+f-f0+off] = score

    if DEBUG:
        debugV2(T, pattern, F, lastIdx, H, C)

    # Phase 4. (Optional) Backtrace to find character positions
    pos = []
    i = M - 1
    j = maxScorePos
    preferMatch = True
    while(True):
        I = i * width
        j0 = j - f0
        s = H[I+j0]

        s1, s2 = 0, 0
        if i > 0 and j >= int(F[i]):
            s1 = H[I-width+j0-1]
        if j > int(F[i]):
            s2 = H[I+j0-1]

        if s > s1 and (s > s2 or s == s2 and preferMatch):
            pos.append(j)
            if i == 0:
                break
            i -= 1
        preferMatch = C[I+j0] > 1 or I+width+j0+1 < len(C) and C[I+width+j0+1] > 0
        j -= 1

    # Start offset we return here is only relevant when begin tiebreak is used.
    # However finding the accurate offset requires backtracking, and we don't
    # want to pay extra cost for the option that has lost its importance.
    return Result(j, maxScorePos + 1, int(maxScore), pos)



def test_fuzzymatch():
    assert ascii_fuzzy_index("helo", "h") == 0
    assert ascii_fuzzy_index("helo", "hlo") == 0
    assert ascii_fuzzy_index("helo", "e") == 0
    assert ascii_fuzzy_index("helo", "el") == 0
    assert ascii_fuzzy_index("helo", "eo") == 0
    assert ascii_fuzzy_index("helo", "l") == 1
    assert ascii_fuzzy_index("helo", "lo") == 1
    assert ascii_fuzzy_index("helo", "o") == 2
    assert ascii_fuzzy_index("helo", "ooh") == -1

    assert charClassOfAscii('a') == charLower
    assert charClassOfAscii('C') == charUpper
    assert charClassOfAscii('2') == charNumber
    assert charClassOfAscii(' ') == charWhite
    assert charClassOfAscii(',') == charDelimiter

    assert vd.fuzzymatch("hello", "") == Result(0,0,0,[])
    assert vd.fuzzymatch("hello", "nono") == Result(-1,-1,0, None)
    assert vd.fuzzymatch("hello", "l") == Result(2, 3, 16, [2])
    assert vd.fuzzymatch("hello world", "elo wo") == Result(1, 8, 127, [7, 6, 5, 4, 2, 1])
