
from sys import argv


def combos(l):
    result = []

    def inner(first, letter_list):
        # print(result)
        result.append(first)

        if len(letter_list) == 0:
            return

        for i, letter in enumerate(letter_list):
            inner(first+letter, letter_list[i+1:])

    for j,k in enumerate(l):
        inner(k, l[j+1:])

    return result



x = 'abc'

l = list(x)

print(combos(argv[1]))
