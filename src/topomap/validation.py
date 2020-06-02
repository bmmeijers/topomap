"""
Created on Jun 26, 2012

@author: author1_givenname
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
        self.validate_face_geometries()

    def validate_angles(self):
        for edge in self.topo_map.half_edges.itervalues():
            assert increasing( [h.angle for h in edge.origin.half_edges] ), "n{0}: {1}".format(edge.origin.id, [(h.id, h.angle) for h in edge.origin.half_edges])
#            assert increasing( [h.angle for h in edge.twin.origin.half_edges] ), "n{0}: {1}".format(edge.twin.origin.id, [(h.id, h.angle) for h in edge.twin.origin.half_edges])
        
    def validate_faces(self):
        for face in self.topo_map.faces.itervalues():
            try:
                assert len(face.loops) > 0
            except:
                raise Exception('{0} has no loops'.format(face))

    def validate_face_geometries(self):
        for face in self.topo_map.faces.itervalues():
            face.multigeometry()

    def validate_loops(self):
        for edge in self.topo_map.half_edges.itervalues():
            try:
                assert edge.face is edge.loop.face
                assert edge.loop in edge.face.loops
            except:
                if edge.face is None or edge.loop is None:
                    raise Exception("edge.loop {0}, edge {1}".format( edge.loop, edge))
                else:
                    face = None
                    if edge.loop.start is not None:
                        face = edge.loop.face
                    raise Exception('{0} expected {1}, found {2}'.format(edge.id, edge.face, face))
        
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
            for edge in node.half_edges:
                assert edge.origin is node

    def validate_edges_around_node(self):
        for node in self.topo_map.nodes.itervalues():
            for edge in node.half_edges:
                assert edge.origin is node
                assert edge.prev.twin.origin is node
                assert edge.next.origin is edge.twin.origin
