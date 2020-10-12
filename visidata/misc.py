import random

from visidata import Sheet

Sheet.addCommand(None, 'random-rows', 'nrows=int(input("random number to select: ", value=nRows)); vs=copy(sheet); vs.name=name+"_sample"; vs.rows=random.sample(rows, nrows or nRows); vd.push(vs)', 'open duplicate sheet with a random population subset of N rows')
