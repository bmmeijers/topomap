"""
Created on Jun 26, 2012

@author: martijn
"""
from primitives import increasing

class TopoMapValidator(object):
    def __init__(self, topo_map):
        self.topo_map = topo_map

    def validate(self):
        self.validate_loops()
        self.validate_nodes()
        self.validate_edges_around_node()
        self.validate_angles()
        self.validate_faces()

    def validate_angles(self):
        for he in self.topo_map.half_edges.itervalues():
            assert increasing( [h.angle for h in he.origin.half_edges] ), "n{0}: {1}".format(he.origin.id, [(h.id, h.angle) for h in he.origin.half_edges])
#            assert increasing( [h.angle for h in he.twin.origin.half_edges] ), "n{0}: {1}".format(he.twin.origin.id, [(h.id, h.angle) for h in he.twin.origin.half_edges])
        
    def validate_faces(self):
        for face in self.topo_map.faces.itervalues():
            try:
                assert len(face.loops) > 0
            except:
                raise Exception('{0} has no loops'.format(face))

    def validate_loops(self):
        for he in self.topo_map.half_edges.itervalues():
            try:
                assert he.face is he.loop.face
                assert he.loop in he.face.loops
            except:
                if he.face is None or he.loop is None:
                    raise Exception("he.loop {0}, he {1}".format( he.loop, he))
                else:
                    face = None
                    if he.loop.start is not None:
                        face = he.loop.face
                    raise Exception('{0} expected {1}, found {2}'.format(he.id, he.face, face))
        
        for face in self.topo_map.faces.itervalues():
            try:
                assert face.loops
            except:
                raise ValueError('No loops for {0}'.format(face))
            for loop in face.loops:
                try:
                    assert loop.face is face
                except:
                    raise Exception('{0} expected {1}, found {2}'.format(face, loop.face, loop))
                assert loop.start is not None

    def validate_nodes(self):
        for node in self.topo_map.nodes.itervalues():
            for he in node.half_edges:
                assert he.origin is node

    def validate_edges_around_node(self):
        for node in self.topo_map.nodes.itervalues():
            for he in node.half_edges:
                assert he.origin is node
                assert he.prev.twin.origin is node
                assert he.next.origin is he.twin.origin
