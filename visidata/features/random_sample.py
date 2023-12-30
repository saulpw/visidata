from visidata import vd, Sheet

Sheet.addCommand(None, 'random-rows', 'nrows=int(input("random number to filter: ", value=nRows)); vs=copy(sheet); vs.name=name+"_sample"; vs.rows=sample(rows, nrows or nRows); vd.push(vs)', 'open duplicate sheet with a random population subset of N rows')
Sheet.addCommand(None, 'select-random', 'nrows=int(input("random number to select: ", value=nRows)); select(sample(rows, nrows or nRows))', 'select random sample of N rows')

vd.addMenuItems('Row > Select > random sample > select-random')
