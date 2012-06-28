from primitives import Face, Anchorage, Loop, HalfEdge, Node
from primitives import angle

INIT = False
VISITED = True

class TopoMap(object):
    def __init__(self, universe_id = 0, srid = -1):
        self.srid = srid
        self.universe_id = universe_id
        self.faces = {}
        self.half_edges = {}
        self.nodes = {}
        self.add_face(universe_id, unbounded = True)

    def add_face(self, face_id, attrs = {}, unbounded = False):
        """Adds a Face to the TopoMap"""
        if face_id not in self.faces:
            face = Face(face_id, attrs, unbounded)
            self.faces[face_id] = face
        else:
            face = self.faces[face_id]
        return face

    def remove_face(self, face_id):
        """Deleting a face from the map.
        """
        face = self.faces[face_id]
        face.blank()
        del self.faces[face_id]

    def change_face_id(self, face, new_id):
        del self.faces[face.id]
        face.id = new_id
        self.faces[new_id] = face

    def add_edge(self, edge_id,
        start_node_id, end_node_id,
        left_face_id, right_face_id,
        geometry, attrs = {}):
        """Adds an Edge to the TopoMap
        
        Also creates Node objects if not yet there (start/end)
        Assumes that Face objects are already created (left/right)
        
        Calls add_edge method on Node objects to set wing pointers for created
        Edge object.
        """
        if edge_id not in self.half_edges:
            attribute = Anchorage(edge_id, geometry, attrs)
            # half edges
            he0 = HalfEdge(attribute)
            he1 = HalfEdge(None) 
            # store id and geometry in left part
            # link he - he
            he0.set_twin(he1)
            #
            assert geometry[0] != geometry[1], "{0} {1}; {2} ".format(geometry[0], geometry[1], geometry, edge_id)
            assert geometry[-1] != geometry[-2], "{0} {1}; {2}".format(geometry[-1], geometry[-2], geometry, edge_id)
            #
            he0.angle = angle(geometry[0], geometry[1])
            he1.angle = angle(geometry[-1], geometry[-2])
            
            # left face
            he0.face = self.add_face(left_face_id)
            # right face
            he1.face = self.add_face(right_face_id)
            # start node
            start_node = self.add_node(start_node_id, geometry[0])
            he0.origin = start_node
            start_node.add_halfedge(he0)
            # end node
            end_node = self.add_node(end_node_id, geometry[-1])
            he1.origin = end_node
            end_node.add_halfedge(he1)
            assert geometry[0] == start_node.geometry, "e{2} {0} vs. {1} :: {3} {4} @ {5} (startnode)".format(geometry[0], start_node.geometry, edge_id, geometry, he0, start_node.id)
            assert geometry[-1] == end_node.geometry, "e{2} {0} vs. {1} @ {4} (endnode) :: {3}".format(geometry[-1], end_node.geometry, edge_id, geometry, end_node.id)
            # add is_edge to dictionary of edges
            self.half_edges[edge_id] = he0
        else:
            he0 = self.half_edges[edge_id]
        return he0

    def remove_edge(self, edge_id, remove_nodes = False):
        """Removing a HalfEdge from the TopoMap.
        
        If a node is left with degree == 0, 
        it is also deleted if ``remove_nodes`` = True.
        """
        he0 = self.half_edges[edge_id]
        he1 = he0.twin
        # set pointers to this HalfEdge to zero, if they exist
        he0.loop.remove_he(he0)
        he1.loop.remove_he(he1)

        start_node = he0.origin
        end_node = he1.origin
        
        start_node.remove_he(he0)
        end_node.remove_he(he1)
        
        if remove_nodes:
            if start_node.degree == 0:
                self.remove_node(start_node.id)
            if start_node is not end_node and end_node.degree == 0:
                self.remove_node(end_node.id)
        he0.next = None
        he0.prev = None
        he1.next = None
        he1.prev = None
        # blank references, this breaks cyclic references so GC can do its work
        he0.blank()
        he1.blank()
        del self.half_edges[edge_id]
        
    def add_node(self, node_id, geometry, attrs = {}):
        """Adds a Node to the TopoMap"""
        if node_id not in self.nodes:
            node = Node(node_id, geometry, attrs)
            self.nodes[node_id] = node
        else:
            node = self.nodes[node_id]
        return node

    def remove_node(self, node_id):
        """Deleting a node from the map. The node should not be connected
        any more (i.e. degree == 0).
        """
        node = self.nodes[node_id]
        assert node.degree == 0
        node.blank()
        del self.nodes[node_id]

    def remove_loops(self):
        """Removes all loops for all faces
        """
        for face in self.faces.itervalues():
            face.reset_loops()

    def find_loops(self):
        """Find all Loop objects and adds them to the Face they belong to"""
        self.label_half_edges(INIT)
        self._find_loops(self.half_edges.itervalues())
        for face in self.faces.itervalues():
            try:
                face.multigeometry()
            except:
                print face
                raise

    def _find_loops(self, half_edges):
        for item in half_edges:
            for he in (item, item.twin):
                if he.label == VISITED:
                    continue
                else:
                    start = he
                    loop = Loop(start)
                    start.face.loops.append(loop)
                    guard = 0
                    while True:
                        guard += 1
                        if guard > 500000:
                            raise Exception('Too much iteration for {0}, started at {1}'.format(start.face, start))
                        he.label = VISITED
                        he.loop = loop
                        try:
                            assert he.face is start.face, "{0}, reconstructing: {1}".format(he, start.face)
                        except:
                            print "ERROR: {0}".format(he)
                            print "... reconstructing: {0}".format(start.face)
                            print "...", he, he.face, start.face
                            print ""
                            raise
                        he = he.next
                        if he is start:
                            break

    def label_half_edges(self, value):
        """Set ``value'' to all label properties on all HalfEdges"""
        for he in self.half_edges.itervalues():
            he.label = value
            he.twin.label = value

    def clear(self):
        for edge_id in self.half_edges.keys():
            self.remove_edge(edge_id, True)
        for face_id in self.faces.keys():
            self.remove_face(face_id)
        self.nodes.clear()
        self.half_edges.clear()
        self.faces.clear()
