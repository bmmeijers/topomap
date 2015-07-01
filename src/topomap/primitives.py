# cython: profile=True

import logging
log = logging.getLogger(__name__)

from math import pi, atan2
import sys

from simplegeom.geometry import Polygon, LinearRing, LineString

import cython

PI2 = 2 * pi
INIT = False
VISITED = True

def increasing(obj):
    for i, item in enumerate(obj):
        if i > 0:
            if item < obj[i - 1]:
                return False
    else:
        return True

def angle(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle = atan2(dy, dx)
    while angle < 0:
        angle += PI2
    return angle

class Face(object):
    """Face"""
    __slots__ = ('id', 'unbounded', 'attrs', 'loops', 'rings', 'linestrings', 'area')
    
    def __init__(self, face_id, attrs, unbounded):
        self.id = face_id
        self.unbounded = unbounded
        self.attrs = attrs # dict

        self.loops = []
        self.rings = []
        self.linestrings = []
        self.area = 0.

    def blank(self):
        """Sets all attributes to None
        """
        self.loops = None
        self.rings = None
        self.area = None
        self.attrs = None

    def __str__(self):
        return "<f%d>" % (self.id)

#     def __eq__(self, other):
#         return self.id == other.id
    
    def reset_loops(self):
        """Removes loops and rings info from cache
        """
        
        self.loops = []
        self.rings = []
        self.area = None

    def multigeometry(self, srid = 0):
        """Returns a list of geometries for this face
        
        This is a list, because a face can become a multi-part geometry 
        after the clipping operation
        """
        #return PolygonizeFactory.face_to_geometry(self, srid=srid)
        return PolygonizeFactory.face_to_geometry(self, srid=srid)
    
    @property
    def half_edges(self):
        """HalfEdges having a relation with this face
        """
        assert len(self.loops) > 0
        for loop in self.loops:
            for edge in loop.half_edges:
                yield edge

    @property
    def neighbours(self):
        """Returns dictionary with:
        neighbouring face -> set of edge 
        (boundary between, this edge lies on interior of *this* face)
        """
        #this doesn't work for universe
        neighbours = {}
        for loop in self.loops:
            for edge in loop.half_edges:
                if edge.twin.face not in neighbours:
                    neighbours[edge.twin.face] = set()
                neighbours[edge.twin.face].add(edge)
        return neighbours

    @property
    def neighbours_no_same_face(self):
        """Returns dictionary with:
        neighbouring face -> set of edge 
        (boundary between, this edge lies on interior of *this* face)
        eliminate empty cycles
        """
        #this doesn't work for universe
        neighbours = {}
        assert len(self.loops) > 0
        for loop in self.loops:
            for edge in loop.half_edges:
                if edge.face.id <> edge.twin.face.id:
                    if edge.twin.face not in neighbours:
                        neighbours[edge.twin.face] = set()
                    neighbours[edge.twin.face].add(edge)
        return neighbours

class Anchorage(object):
    """Container for attributes (dictionary)
    """
    
    __slots__ = ('id', 'attrs', 'geometry')
    
    def __init__(self, edge_id, geometry, attrs = None):
        self.id = edge_id
        self.geometry = geometry
        if attrs is None:
            attrs = {}
        self.attrs = attrs


class Node(object):
    """Node class
    """
    __slots__ = ('id', 'attrs', 'geometry', 'he', 'degree')
    
    def __init__(self, node_id, geometry, attrs = None):
        self.id = node_id
        if attrs is None:
            attrs = {}
        self.attrs = attrs
        self.geometry = geometry
        self.he = None # half is_edge pointer
        self.degree = 0

    def blank(self):
        """Sets attributes to None
        """
        self.he = None
        self.geometry = None
        self.degree = None

#     def __eq__(self, other):
#         return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
    
    def __str__(self):
        return str("N<{0}>".format(self.id))

    def add_halfedge(self, edge):
        """Add incident HalfEdge to this Node
        """
        self.degree += 1
        if self.he is None:
            self.he = edge
            self.he.twin.next = self.he
            self.he.prev = self.he.twin
        else:
#            print " already edges at node"
#            print "angle", degrees(edge.angle), "({0})".format(edge.angle)
#            print "first", self.edge.id, id(self.edge), degrees(self.edge.angle), self.edge
            assert self.he.origin is self
            cw_he = self.he
            ccw_he = cw_he.prev.twin # next edge outwards
            while True:
#                print "tick, cw:", cw_he.id, id(cw_he), degrees(cw_he.angle), "({0})".format(cw_he.angle), "_ ccw:", ccw_he.id, id(ccw_he), degrees(ccw_he.angle), "({0})".format(ccw_he.angle)
                assert edge.angle != None
                assert edge.angle != cw_he
                assert edge.angle != ccw_he
                if ccw_he is self.he:
                    break
                if edge.angle > cw_he.angle and edge.angle < ccw_he.angle:
                    break
                cw_he = ccw_he
                ccw_he = cw_he.prev.twin 

            try:
                assert cw_he.origin is self
                assert ccw_he.origin is self
            except:
                for edge in self.half_edges:
                    print >> sys.stderr, self, "->", edge
                raise
            assert cw_he is not None
            assert ccw_he is not None
            # adapt ccw_he, cw_he and edge
            ccw_he.twin.next = edge
            edge.prev = ccw_he.twin
            edge.twin.next = cw_he
            cw_he.prev = edge.twin
            # make this HalfEdge the HalfEdge associated with this node 
            # if angle is closer to 0 than before
            if edge.angle < self.he.angle:
                self.he = edge
#            assert increasing( [h.angle for h in self.half_edges] ), "error at N{0}, {1}".format(self.id, [(h.id, h.angle) for h in self.half_edges])

    def remove_he(self, edge):
        """Removes incident HalfEdge from this Node
        """
        assert edge.origin is self
        self.degree -= 1
        if self.degree > 0:
            cw_he = edge.twin.next #.prev
            assert cw_he.origin is self
            ccw_he = edge.prev #.next
            assert ccw_he.twin.origin is self
            cw_he.prev = ccw_he
            ccw_he.next = cw_he
            if edge is self.he:
#                raise ValueError('removing associated is_edge')
                assert ccw_he.twin.origin is self
                self.he = ccw_he.twin
        else:
            self.he = None
            assert self.degree == 0
#        assert increasing( [h.angle for h in self.half_edges] ), "error at N{0}, {1}".format(self.id, [(h.id, h.angle) for h in self.half_edges])

    @property
    def half_edges(self):
        """Iterator over incident HalfEdges
        """
        if self.he is None: 
            return
        yield self.he
        ccw_he = self.he.prev.twin # next edge outwards
        while True:
            if ccw_he is self.he:
                break
            yield ccw_he
            ccw_he = ccw_he.prev.twin

# class LoopIterator(object):
#     def __init__(self, loop):
#         self.start = self.cur = loop.start
#         self.stop = False
# 
#     def __iter__(self):
#         return self
# 
#     def next(self):
#         self.cur = self.cur.next
#         if not self.stop:
#             if self.cur is self.start:
#                 self.stop = True
#             return self.cur
#         else:
#             raise StopIteration()


class Loop(object):
    """Loop class -- A loop is a set of HalfEdges along a Face boundary
    """
    
    __slots__ = ('start', 'linear_rings', 'linestrings')
    
    def __init__(self, edge):
        self.start = edge
        self.linear_rings = None
        self.linestrings = None
    
    def __str__(self):
        try:
            return "Loop<{2} @ {1} ({0})>".format(id(self), self.start, self.face)
        except:
            return "Loop<{0}>".format(id(self))

    @property
    def face(self):
        """Face to which this Loop belongs
        """
        return self.start.face

    def blank(self):
        """Sets attributes to None
        """
        self.start = None
        self.linear_rings = None
        self.linestrings = None

    def remove_he(self, edge):
        """Removes HalfEdge from this Loop if *edge* is *self.start*
        """
        if edge is self.start:
            self.start = None
        self.linear_rings = None
        self.linestrings = None

    @property
    @cython.returns(LoopHalfEdgesIterator)
    def half_edges(self):
        """Iterator over HalfEdges that are part of this Loop
        """
        return LoopHalfEdgesIterator(self)
#         return LoopIterator(self)

#         try:
#             assert self.start is not None
# #         except:
#         if self.start is None:
#             raise ValueError("ERROR in {0} -- Orphaned loop found: no associated halfedge".format(self))
#         edge = self.start
# #         guard = 0
#         while True:
#             yield edge
# #             guard += 1
#             edge = edge.next
#             if edge is self.start:
#                 break

    def reset_geometry(self):
        """Empty cache of geometry
        """
        self.linear_rings = None
        self.linestrings = None

    @property
    def geometry(self):
        """Constructs geometry for this Loop
        """
        # caching of rings, as copying of geometry is quite heavy process
        # (could be optimised -> faster array mechanism under neath geometry?)
        #
        # MM disable caching of rings at all...
#         self.linear_rings = None
#         self.linestrings = None
        if self.linear_rings is None:
            # make linear rings out of this loop (tangency
            # can cause a loop to have multiple rings
            # Rings are tested for simplicity (no self-intersections)
            # so we have to separate rings that are self-tangent in one point
            # into more than 1 ring
            nodes = set() 
            tangent_nodes = set()
            stack = []
            visit_count = {}
            _tangent_nodes_add = tangent_nodes.add # ref to function
            _nodes_add = nodes.add                 # ref to function
            for edge in self.half_edges:
                #print edge.id, "origin", edge.origin, "face", edge.face
                if edge.origin not in nodes:
                    _nodes_add(edge.origin)
                else:
                    _tangent_nodes_add(edge.origin)
                    if edge.origin not in visit_count:
                        visit_count[edge.origin] = 1
                    visit_count[edge.origin] += 1
            ring_is_flat = edge.twin.face is edge.face
            #
            if tangent_nodes:
                rings = []
                linestrings = []
                ring = LineString()
                first = True
                start_node = None
                end_node = None
                edge_seen = set()
                #_ring_extend = ring.extend # ref to function
                for edge in self.half_edges:
                    is_flat = edge.twin.face is edge.face
                    if not edge.id in edge_seen:
                        if edge.anchor is not None:
                            geom = edge.anchor.geometry
                            step = 1
                        else:
                            geom = edge.twin.anchor.geometry
                            step = -1
                        if first:
                            s = slice(None, None, step)
                            first = False
                        else:
                            if step == -1:
                                s = slice(-2, None, step)
                            else:
                                assert step == 1
                                s = slice(1, None, step)
                        ring.extend(geom, s)

                    if is_flat:
                        edge_seen.add(edge.id)

                    if start_node is None:
                        start_node = edge.origin
                    end_node = edge.twin.origin

                    if end_node in tangent_nodes:
                        visit_count[end_node] -= 1
                        # 3 cases:
                        #  stack what was made and open new one
                        #  finish what was made and open new one
                        #  finish what was made and continue previous one
                        if start_node is end_node:
                            # finish was what made
                            if is_flat:
                                linestrings.append(ring)
                            else:
                                rings.append(LinearRing(ring))
                            loops_to_make = visit_count[end_node]
                            # FIXME: these conditions are a bit complex
                            # can they be simplified ????
                            if loops_to_make > 0:
                                # open new one
                                start_node = None
                                end_node = None
                                ring = LineString()
                                first = True
                            elif stack:
                                # continue previous one
                                ring, start_node = stack.pop()
                                first = False
                            else:
                                assert loops_to_make == 0
                                # open new one
                                start_node = None
                                end_node = None
                                ring = LineString()
                                first = True
                        else:
                            # stack what was made and open new one
                            stack.append( (ring, start_node) )
                            start_node = None
                            end_node = None
                            ring = LineString()
                            first = True
                if len(ring):
                    assert start_node is end_node
                    if is_flat:
                        linestrings.append(ring)
                    else:
                        rings.append(LinearRing(ring))
                # postcondition: stack should be empty now
                assert not stack, "stack should be empty now"
                self.linear_rings = rings
                self.linestrings = linestrings
            else:
                ring = LineString()
                first = True
                edge_seen = set()
                # No tangent node but some edge is still dead ends then whole cycle is empty. 
                #      _______
                #     /       \
                #    |  ---    |
                #     \_______/
                #
                for edge in self.half_edges:
                    if not edge.id in edge_seen:
                        if edge.anchor is not None:
                            geom = edge.anchor.geometry
                            step = 1
                        else:
                            geom = edge.twin.anchor.geometry
                            step = -1
                        if first:
                            s = slice(None, None, step)
                            first = False
                        else:
                            if step == -1:
                                s = slice(-2, None, step)
                            else:
                                assert step == 1
                                s = slice(1, None, step)
                        ring.extend(geom, s)
                        if ring_is_flat:
                            edge_seen.add(edge.id)
                if ring_is_flat:
#                    print "ring inside is flat"
                    self.linestrings = [ring]
                else:
                    self.linear_rings = [LinearRing(ring)]
    ##            Expensive checks!
    #            for ring in self.linear_rings:
    #                assert is_linearring(ring)
    #                assert is_ring_simple(ring)
        return self.linear_rings, self.linestrings


class HalfEdge(object):
    """HalfEdge class
    """
    __slots__ = ('anchor', 
                 'twin', 
                 'origin', 'angle', 
                 'prev', 'next', 
                 'loop', 'face', 'label')

    # FIXME: should we not keep only a pointer to the loop object,
    # by means of which we can access the face object? -> will not work
    # at the moment, as the face of the loop is coming from the first half edge!

    def __init__(self, anchor = None):
        self.anchor = anchor
        self.twin = None
        self.origin = None
        self.angle = -1
        self.prev = None
        self.next = None
        self.loop = None
        self.face = None
        self.label = -1

    @property
    def id(self):
        """Global identifier of this HalfEdge
        """
        if self.anchor is None:
            return self.twin.anchor.id
        else:
            return self.anchor.id

    def __str__(self):
        prev_id, next_id = None, None
        if self.prev is not None:
            prev_id = self.prev.id
        if self.next is not None:
            next_id = self.next.id
        return "HE<e{1} n{2} f{3} ({0} - next:{4} prv:{5})>".format( id(self), 
                                                  self.id, self.origin.id, self.face.id,
                                                  next_id, prev_id
                                                  )

    def set_twin(self, edge):
        """Sets twin of this HalfEdge
        """
        self.twin = edge
        edge.twin = self

    def blank(self):
        """Sets attributes to None
        """
        self.twin = None
        self.anchor = None
        self.origin = None
        self.angle = None
        self.prev = None
        self.next = None
        self.loop = None
        self.face = None
        self.label = None

    @property
    def geometry(self):
        """Returns copy of geometry that *is* 
        consistent with
        start_node, end_node, 
        left_face and right_face properties
        """
        if self.anchor:
            # Copy
            return self.anchor.geometry[:]
        else:
            # Copy
            return self.twin.anchor.geometry[:]
 
    @property
    def start_node(self):
        """Returns Node at start of this HalfEdge
        """
        if self.anchor:
            assert self.origin.geometry == self.anchor.geometry[0]
            return self.origin
        else:
            assert self.twin.origin.geometry == self.twin.anchor.geometry[0]
            return self.twin.origin
 
    @property
    def end_node(self):
        """Returns Node at end of this HalfEdge
        """
        if self.anchor:
            assert self.twin.origin.geometry == self.anchor.geometry[-1]
            return self.twin.origin
        else:
            assert self.origin.geometry == self.twin.anchor.geometry[-1]
            return self.origin
 
    @property
    def left_face(self):
        """Returns Face at left of this HalfEdge
        """
        if self.anchor:
            return self.face
        else:
            return self.twin.face
 
    @property
    def right_face(self):
        """Returns Face at right of this HalfEdge
        """
        if self.anchor:
            return self.twin.face
        else:
            return self.face

    @property
    def attrs(self):
        """Returns additional attributes that are stored with this HalfEdge
        """
        if self.anchor:
            return self.anchor.attrs
        else:
            return self.twin.anchor.attrs


class LoopHalfEdgesIterator(object):
#     __slots__ = ('start', '_next')
    def __init__(self, loop):
        self.start = loop.start
        self.cur = self.start
 
    def __iter__(self):
        return self
 
    @cython.locals(edge=HalfEdge)
    @cython.returns(HalfEdge)
    def __next__(self):
#     def next(self):
        if self.cur != None:
            edge = self.cur
            if edge.next != self.start:
                self.cur = edge.next
            else:
                self.cur = None
            return edge
        else:
            raise StopIteration()


class PolygonizeFactory(object):
    """Methods to convert Face to geometry
    """
    def __init__(self):
        pass

    @classmethod
    def face_to_geometry(cls, face, srid = 0):
        """Returns a list of geometries for this face

        This is a list, because a face can become a multi-part geometry 
        after the clipping operation or contain lose or dangling edges
        """
        face.rings = []
        face.linestrings = []
        area = 0.
        try:
            assert len(face.loops) > 0
        except AssertionError:
            log.warning('Error in face {0} -- no loops for this face'.format(face.id))
            return []
        #compute area and copy rings
        for loop in face.loops:
            loop.geometry[0]
            try:
                assert loop.linear_rings or loop.linestrings
            except AssertionError:
                log.warning('Error in loop of face {0} -- no rings nor linestrings in this loop'.format(face.id))
                return []
            if loop.linear_rings:
                for ring in loop.geometry[0]:
                    ring_area = ring.signed_area()
                    face.rings.append((ring_area, ring, loop))
                    area += ring_area 
            else:
                assert loop.linestrings  
            #copy collapsed cycles   
            #if loop.linestrings: 
                face.linestrings.extend(loop.linestrings)
        face.area = area

        # qa on ring sizes 
        # -> inner have negative area
        # -> outer have positive area
        # -> degenerate have no area

        # FIXME: is it possible that a face has only line strings ???
        # e.g. universe with only loose-lying segments
        try:
            assert len(face.rings) > 0
        except AssertionError:
            log.warning("{0} has no rings at all".format(face))
            return []
        #
        inner = 0
        outer = 0
        degenerate = 0
        for area, ring, loop, in face.rings:
            if area < 0:
                inner += 1
            elif area > 0:
                outer += 1
            else:
                degenerate += 1
        try:
#            if face.unbounded: # only holds for strictly planar partition
#                assert inner >= 1
#                assert outer == 0
#                assert degenerate == 0
#            else:
            if not face.unbounded:
                assert inner >= 0
                assert outer >= 1
                assert degenerate == 0
        except AssertionError:
            log.warning("ERROR: Face {0} has {1} inner; {2} outer; {3} degenerate".format(face.id,
                inner, outer, degenerate))
#            for area, ring, loop, in face.rings:
#                print ring
            return []
#            raise Exception('{0} does not fulfill simple SFS polygon criteria'.format(face) )
        # make polygon (should conform to SFS specs)
#        if face.unbounded:
#            log.debug('Unbounded face, setting return geometries to empty list')
#            parts = []
#        else:
        if len(face.rings) == 1:
            parts = [Polygon(shell=ring, srid=srid)]
        elif outer == 1:
            # find largest ring (this must be outer shell)
            largest = face.rings[0]
            j = 0
            for i, item in enumerate(face.rings[1:], 1):
                if item[0] > largest[0]:
                    largest = item
                    j = i
            # outer shell is largest ring found

            # remaining shells are holes
            inner = []
            for i, item in enumerate(face.rings):
                if i == j:
                    # skip outer shell
                    continue
                inner.append(face.rings[i][1])
            poly = Polygon(shell=face.rings[j][1], holes = inner, srid=srid)
            # return this poly as only part
            parts = [poly]
        else:
            # we have a multi-part geometry as result
            # therefore we first split inner and outer in different lists
            inner = []
            parts = []
            for area, ring, loop, in face.rings:
                if area < 0:
                    inner.append(ring)
                elif area > 0:
                    parts.append(Polygon(shell = ring, srid=srid))
            # then we check which inner ring is covered by which 
            # (there should be exactly one) of the outer rings
            for iring in inner:
                # FIXME:
                # this is not sufficient and can make that an island ring
                # goes outside of its exterior ring
                #
                # consider this case:

                ###   #####
                # #   # O #
                # #   #####
                # #
                # ########
                #        #
                #   O    #
                #        #
                ##########

                # The O can be in both exterior rings, just by containment
                for poly in parts:
                    if poly.envelope.covers(iring.envelope):
                        poly.append(iring)
                        break
                # if for loop did not break, we did not find suitable candidate
                else:
                    if face.unbounded is not True:
                        raise ValueError('No suitable outer ring found for inner ring {0}'.format(iring))
#                        print "No suitable outer ring found for inner ring in face", face.id

        return parts