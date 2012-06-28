from math import pi, atan2
import sys

from brep.util import signed_area, extend_slice
from brep.geometry import Polygon, LineString, Point

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
    __slots__ = ('id', 'unbounded', 'attrs', 'loops', 'rings', 'area')
    
    def __init__(self, face_id, attrs, unbounded):
        self.id = face_id
        self.unbounded = unbounded
        self.attrs = attrs # dict

        self.loops = []
        self.rings = []
        self.area = 0.

    def blank(self):
        self.loops = None
        self.rings = None
        self.area = None
        self.attrs = None

    def __str__(self):
        return "<f%d>" % (self.id)

    def __eq__(self, other):
        return self.id == other.id
    
    def reset_loops(self):
        self.loops = []
        self.rings = []
        self.area = None

    def multigeometry(self):
        """Returns a list of geometries for this face
        
        This is a list, because a face can become a multi-part geometry 
        after the clipping operation
        """
        self.rings = []
        area = 0.
        try:
            assert len(self.loops) > 0
        except:
            raise ValueError('Error in face {0} -- no loops for this face'.format(self.id))
        for loop in self.loops:
            for ring in loop.geometry:
                ring_area = signed_area(ring)
                self.rings.append((ring_area, ring, loop))
                area += ring_area
        self.area = area

        # qa on ring sizes 
        # -> inner have negative area
        # -> outer have positive area
        # -> degenerate have no area
        try:
            assert len(self.rings) > 0
        except:
            print "ERROR: Face", self.id, "has no rings at all"
            raise Exception("{0} has no rings at all".format(self))
        #
        inner = 0
        outer = 0
        degenerate = 0
        for area, ring, loop, in self.rings:
            if area < 0:
                inner += 1
            elif area > 0:
                outer += 1
            else:
                degenerate += 1
        try:
#            if self.unbounded: # only holds for strictly planar partition
#                assert inner >= 1
#                assert outer == 0
#                assert degenerate == 0
#            else:
            if not self.unbounded:
                assert inner >= 0
                assert outer >= 1
                assert degenerate == 0
        except AssertionError:
            print "ERROR: Face", self.id, "has", inner, "inner;", outer, "outer;", degenerate, "degenerate"
            raise Exception('{0} does not fulfill simple SFS polygon criteria'.format(self) )
        # make polygon (should conform to SFS specs)
        if self.unbounded:
            parts = []
        else:
            if len(self.rings) == 1:
                parts = [Polygon(shell=ring)]
            elif outer == 1:
                # find largest ring (this must be outer shell)
                largest = self.rings[0]
                j = 0
                for i, item in enumerate(self.rings[1:], 1):
                    if item[0] > largest[0]:
                        largest = item
                        j = i
                # outer shell is largest ring found
                poly = Polygon(shell=self.rings[j][1])
                # remaining shells are holes
                for i, item in enumerate(self.rings):
                    if i == j:
                        # skip outer shell
                        continue
                    poly.append(self.rings[i][1])
                # return this poly as only part
                parts = [poly]
            else:
                # we have a multi-part geometry as result
                # therefore we first split inner and outer in different lists
                inner = []
                parts = []
                for area, ring, loop, in self.rings:
                    if area < 0:
                        inner.append(ring)
                    elif area > 0:
                        parts.append(Polygon(shell = ring))
                # then we check which inner ring is covered by which 
                # (there should be exactly one) of the outer rings
                for iring in inner:
                    for poly in parts:
                        if poly.envelope.covers(iring.envelope):
                            poly.append(iring)
                            break
                    # if for loop did not break, we did not find suitable candidate
                    else: 
                        raise ValueError('No suitable outer ring found for inner ring {0}'.format(iring))
#                        print "No suitable outer ring found for inner ring in face", self.id
        return parts

    @property
    def half_edges(self):
        for loop in self.loops:
            for he in loop.half_edges:
                yield he

    @property
    def neighbours(self):
        """Returns dictionary with:
        neighbouring face -> set of he 
        (boundary between, this he lies on interior of *this* face)
        """
        neighbours = {}
        for loop in self.loops:
            for he in loop.half_edges:
                if he.twin.face not in neighbours:
                    neighbours[he.twin.face] = set()
                neighbours[he.twin.face].add(he)
        return neighbours


class Anchorage(object):
    
    __slots__ = ('id', 'attrs', 'geometry')
    
    def __init__(self, edge_id, geometry, attrs = {}):
        self.id = edge_id
        self.geometry = geometry
        self.attrs = attrs


class Node(object):
    
    __slots__ = ('id', 'attrs', 'geometry', 'he', 'degree')
    
    def __init__(self, node_id, geometry, attrs = {}):
        self.id = node_id
        self.attrs = attrs
        self.geometry = geometry
        self.he = None # half is_edge pointer
        self.degree = 0

    def blank(self):
        self.he = None
        self.geometry = None
        self.degree = None

    def __eq__(self, other):
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
    
    def __str__(self):
        return str("N<{0}>".format(self.id))

    def add_halfedge(self, he):
        self.degree += 1
        if self.he is None:
            self.he = he
            self.he.twin.next = self.he
            self.he.prev = self.he.twin
        else:
#            print " already edges at node"
#            print "angle", degrees(he.angle), "({0})".format(he.angle)
#            print "first", self.he.id, id(self.he), degrees(self.he.angle), self.he
            assert self.he.origin is self
            cw_he = self.he
            ccw_he = cw_he.prev.twin # next he outwards
            while True:
#                print "tick, cw:", cw_he.id, id(cw_he), degrees(cw_he.angle), "({0})".format(cw_he.angle), "_ ccw:", ccw_he.id, id(ccw_he), degrees(ccw_he.angle), "({0})".format(ccw_he.angle)
                assert he.angle != None
                assert he.angle != cw_he
                assert he.angle != ccw_he
                if ccw_he is self.he:
                    break
                if he.angle > cw_he.angle and he.angle < ccw_he.angle:
                    break
                cw_he = ccw_he
                ccw_he = cw_he.prev.twin 

            try:
                assert cw_he.origin is self
                assert ccw_he.origin is self
            except:
                for he in self.half_edges:
                    print >> sys.stderr, self, "->", he
                raise
            assert cw_he is not None
            assert ccw_he is not None
            # adapt ccw_he, cw_he and he
            ccw_he.twin.next = he
            he.prev = ccw_he.twin
            he.twin.next = cw_he
            cw_he.prev = he.twin
            # make this HalfEdge the HalfEdge associated with this node 
            # if angle is closer to 0 than before
            if he.angle < self.he.angle:
                self.he = he
#            assert increasing( [h.angle for h in self.half_edges] ), "error at N{0}, {1}".format(self.id, [(h.id, h.angle) for h in self.half_edges])

    def remove_he(self, he):
        assert he.origin is self
        self.degree -= 1
        if self.degree > 0:
            cw_he = he.twin.next #.prev
            assert cw_he.origin is self
            ccw_he = he.prev #.next
            assert ccw_he.twin.origin is self
            cw_he.prev = ccw_he
            ccw_he.next = cw_he
            if he is self.he:
#                raise ValueError('removing associated is_edge')
                assert ccw_he.twin.origin is self
                self.he = ccw_he.twin
        else:
            self.he = None
            assert self.degree == 0
#        assert increasing( [h.angle for h in self.half_edges] ), "error at N{0}, {1}".format(self.id, [(h.id, h.angle) for h in self.half_edges])

    @property
    def half_edges(self):
        if self.he is None: return
        yield self.he
        ccw_he = self.he.prev.twin # next he outwards
        while True:
            if ccw_he is self.he:
                break
            yield ccw_he
            ccw_he = ccw_he.prev.twin

class Loop(object):
    
    __slots__ = ('start', 'linear_rings')
    
    def __init__(self, he):
        self.start = he
        self.linear_rings = None
    
    def __str__(self):
        try:
            return "Loop<{2} @ {1} ({0})>".format(id(self), self.start, self.face)
        except:
            return "Loop<{0}>".format(id(self))

    @property
    def face(self):
        return self.start.face

    def blank(self):
        self.start = None
        self.linear_rings = None

    def remove_he(self, he):
        if he is self.start:
            self.start = None
        self.linear_rings = None

    @property
    def half_edges(self):
        try:
            assert self.start is not None
        except:
            raise Exception("ERROR in {0} -- Orphaned loop found: no associated half is_edge".format(self))
        he = self.start
        guard = 0
        while True:
            yield he
            guard += 1
            he = he.next
            if he is self.start:
                break
            if guard > 500000:
                raise Exception('Too much iteration in loop.half_edges')
    
    def reset_geometry(self):
        self.linear_rings = None
    
    @property
    def geometry(self):
        # caching of rings, as copying of geometry is quite heavy process
        # (could be optimised -> faster array mechanism under neath geometry?)
        if self.linear_rings is None:
            # make linear rings out of this loop (tangency
            # can cause a loop to have multiple rings
            # Rings are tested for simplicity (no self-intersections)
            # so we have to separate rings that are self-tangent in one point
            # into more than 1 ring
            nodes = set() 
            tangent_nodes = set()
            stack = []
            for he in self.half_edges:
                if he.origin not in nodes:
                    nodes.add(he.origin)
                else:
                    tangent_nodes.add(he.origin)
            if tangent_nodes:
                rings = []
                ring = LineString()
                first = True
                start_node = None
                end_node = None
                for he in self.half_edges:
                    if he.anchor is not None:
                        geom = he.anchor.geometry
                        step = 1
                    else:
                        geom = he.twin.anchor.geometry
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
                    extend_slice(ring, geom, s)
                    if start_node is None:
                        start_node = he.origin
                    end_node = he.twin.origin
                    if he.twin.origin in tangent_nodes:
                        if start_node is not end_node:
                            stack.append( (ring, start_node) )
                            start_node = None
                            end_node = None
                            ring = LineString()
                            first = True
                        else: 
                            rings.append(ring)
                            if stack:
                                ring, start_node = stack.pop()
                                first = False
                            else:
                                ring = LineString()
                                first = True
                if len(ring):
                    try:
                        assert start_node is end_node
                        rings.append(ring)
                    except AssertionError:
                        pass
                    
                self.linear_rings = rings
            else:
                ring = LineString()
                first = True
                for he in self.half_edges:
                    if he.anchor is not None:
                        geom = he.anchor.geometry
                        step = 1
                    else:
                        geom = he.twin.anchor.geometry
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
                    extend_slice(ring, geom, s)
                self.linear_rings = [ring]
                
##            Expensive checks!
#            for ring in self.linear_rings:
#                assert is_linearring(ring)
#                assert is_ring_simple(ring)
                
        return self.linear_rings

class HalfEdge(object):
    
    __slots__ = ('anchor', 
                 'twin', 
                 'origin', 'angle', 
                 'prev', 'next', 
                 'loop', 'face', 'label')
    
    def __init__(self, anchor = None):
        self.anchor = anchor
        self.twin = None
        
        self.origin = None
        self.angle = None
        
        self.prev = None
        self.next = None
        
        self.loop = None
        self.face = None
        
        self.label = None
        
    @property
    def id(self):
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
        return "HE<e{1} n{2} f{3} ({0} - nxt:{4} prv:{5})>".format( id(self), 
                                                  self.id, self.origin.id, self.face.id,
                                                  next_id, prev_id
                                                  )

    def set_twin(self, he):
        self.twin = he
        he.twin = self
    
    def blank(self):
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
        if self.anchor:
            return self.anchor.geometry[:]
        else:
            geom = self.twin.anchor.geometry[:]
            return geom

    @property
    def start_node(self):
        if self.anchor:
            return self.origin
        else:
            return self.twin.origin

    @property
    def end_node(self):
        if self.anchor:
            return self.twin.origin
        else:
            return self.origin

    @property
    def left_face(self):
        if self.anchor:
            return self.face
        else:
            return self.twin.face

    @property
    def right_face(self):
        if self.anchor:
            return self.twin.face
        else:
            return self.face

    @property
    def attrs(self):
        if self.anchor:
            return self.anchor.attrs
        else:
            return self.twin.anchor.attrs
