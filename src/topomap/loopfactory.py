'''
Created on 30 jul. 2014

@author: rsuba
'''
from primitives import Loop

INIT = 0
VISITED = 1


def find_loops_partly(tm):
    """Finds loop objects, starting on half_edges without loop"""
    # FIXME: this is not any more efficient, then just calling find_loops
    # as in find_loops the edge.loop is checked as well for starting
    raise NotImplementedError("This method is not useful, functionality similar to find_loops.")
    visit = set()
    for he in tm.half_edges.itervalues():
        for h in (he, he.twin):
            if h.loop is None:
                visit.add(h)  
    find_loops(tm, visit)

def find_loops(topomap, half_edges = None):
    """Find all Loop objects for a TopoMap 
    and adds them to the Face they belong to"""
    if half_edges is None:
        half_edges = topomap.half_edges.itervalues()

    for item in half_edges:
        for edge in (item, item.twin):
            if edge.loop != None:
                continue
            else:
                start = edge
#                 print start
#                 assert start.face.attrs['locked'] == False
                loop = Loop(start)
                start.face.loops.append(loop)
                guard = 0
                while True:
                    guard += 1
                    if guard > 500000:
                        raise Exception('Too much iteration for {0}, started at {1}'.format(start.face, start))
                    edge.label = VISITED #this guarantee that all edges after forming loop are set to VISITED
                    assert edge.loop is None, "At edge {0} already found loop".format(edge.id)
                    edge.loop = loop
                    try:
                        assert edge.face is start.face, "{0}, reconstructing: {1}".format(edge, start.face)
                    except:
#                         print edge.id
                        print "ERROR: {0}".format(edge)
                        print "... reconstructing: {0}".format(start.face)
                        print "...", edge, edge.face, start.face
                        print ""
                        raise
                    edge = edge.next
#                     print "", edge
                    if edge is start:
                        break

def find_clipped_loops(topomap, half_edges = None):
    """Find all Loop objects for a TopoMap 
    and adds them to the Face they belong to
    
    The edges of the TopoMap can be clipped and should have a field in
    their attrs-dict `clipped' that evaluates to True
    """
    #
    # Make 3 passes over the edges
    # 1. reconstruct loops fully inside
    # 2. reconstruct clipped loops, starting on a edge that is not a border segment
    # 3. reconstruct remaining loops (consisting of border segments only)
    for item in topomap.half_edges.itervalues():
        for edge in (item, item.twin):
            if edge.label == VISITED:
                continue
            elif 'clipped' in edge.attrs and edge.attrs['clipped']:
                continue
            else:
                start = edge
                loop = Loop(start)
                start.face.loops.append(loop)
                guard = 0
                while True:
                    guard += 1
                    if guard > 500000:
                        raise Exception('Too much iteration for {0}, started at {1}'.format(start.face, start))
                    edge.label = VISITED
                    edge.loop = loop
                    if 'clipped' in edge.attrs and edge.attrs['clipped']:
                        edge.face = start.face
                    try:
                        assert edge.face is start.face, "{0}, reconstructing: {1}".format(edge, start.face)
                    except:
                        print "ERROR: {0}".format(edge)
                        print "... reconstructing: {0}".format(start.face)
                        print "...", edge, edge.face, start.face
                        print ""
                        raise
                    edge = edge.next
                    if edge is start:
                        break
    for item in topomap.half_edges.itervalues():
        for edge in (item, item.twin):
            if edge.label == VISITED:
                continue
            elif edge.right_face is edge.left_face:
                continue
            else:
                start = edge
                loop = Loop(start)
                start.face.loops.append(loop)
                guard = 0
                while True:
                    guard += 1
                    if guard > 500000:
                        raise Exception('Too much iteration for {0}, started at {1}'.format(start.face, start))
                    edge.label = VISITED
                    edge.loop = loop
                    if 'clipped' in edge.attrs and edge.attrs['clipped']:
                        edge.face = start.face
                    try:
                        assert edge.face is start.face, "{0}, reconstructing: {1}".format(edge, start.face)
                    except:
                        print "ERROR: {0}".format(edge)
                        print "... reconstructing: {0}".format(start.face)
                        print "...", edge, edge.face, start.face
                        print ""
                        raise
                    edge = edge.next
                    if edge is start:
                        break
    for item in topomap.half_edges.itervalues():
        for edge in (item, item.twin):
            if edge.label == VISITED:
                continue
            else:
                start = edge
                loop = Loop(start)
                start.face.loops.append(loop)
                guard = 0
                while True:
                    guard += 1
                    if guard > 500000:
                        raise Exception('Too much iteration for {0}, started at {1}'.format(start.face, start))
                    edge.label = VISITED
                    edge.loop = loop
                    if 'clipped' in edge.attrs and edge.attrs['clipped']:
                        edge.face = start.face
                    try:
                        assert edge.face is start.face, "{0}, reconstructing: {1}".format(edge, start.face)
                    except:
                        print "ERROR: {0}".format(edge)
                        print "... reconstructing: {0}".format(start.face)
                        print "...", edge, edge.face, start.face
                        print ""
                        raise
                    edge = edge.next
                    if edge is start:
                        break
    #comment for use of qgis plugin
#     fh = open('/tmp/tm.wkt', 'w')
#     fh.write('id;wkt;clipped\n')
    to_remove = []
    for face in topomap.faces.itervalues():
        if not face.loops:
            to_remove.append(face.id)
            continue
        if face.unbounded:
            continue
        try:
            geoms = face.multigeometry()
        except Exception, err:
            print err
            pass
#         if geoms:
#             for geom in geoms:
#                 fh.write("{0};{1};{2}\n".format(face.id, geom, face.attrs['clipped']))
#     fh.close()
    for remove in to_remove:
        topomap.remove_face(remove)