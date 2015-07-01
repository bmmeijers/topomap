from topomap.primitives import LoopHalfEdgesIterator
class Mock:
    start = None

l = LoopHalfEdgesIterator(Mock())
for item in l:
    print item
