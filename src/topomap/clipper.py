import sys
from simplegeom.geometry import Point, LineString, Envelope
from primitives import angle

class EdgeClipper(object):
    def __init__(self, bbox, border_face_id = None):
        self.bbox = bbox
        self.vertices = []
        self.vertex_ids = {}
        self._add_vertex( Point(bbox.xmin, bbox.ymin) )
        self._add_vertex( Point(bbox.xmin, bbox.ymax) )
        self._add_vertex( Point(bbox.xmax, bbox.ymin) )
        self._add_vertex( Point(bbox.xmax, bbox.ymax) )
        self.clipped = []
        self.new_edge_id = -1
        self.border_face_id = border_face_id
        self.original_edges = []
    
    def clip_edge(self, edge_id,
                       start_node_id, end_node_id,
                       left_face_id, right_face_id,
                       geometry, attrs = {}):
        
        # PRECONDITION:
        # bounding box of segment overlaps clipping window
        #
        # caller should do something like this
        #
        # """
        #if clip_window.intersects(geometry.envelope) and \
        #    not clip_window.contains(geometry.envelope):
        # """
        self.original_edges.append(geometry)
        
        left, bottom, right, top = self.bbox.xmin, self.bbox.ymin, \
                                 self.bbox.xmax, self.bbox.ymax
        segment_ct = len(geometry) - 1
        start_node = None
        end_node = None
        clipped_geometry = LineString(srid = geometry.srid)
        new_sn_id = None
        new_en_id = None
        for s in xrange(segment_ct):
            first_segment = False
            last_segment = False
            t = s + 1
            if s == 0: # first segment
                first_segment = True
            if t == segment_ct: # last segment
                last_segment = True
            x1, y1 = geometry[s] # start point of segment 
            x2, y2 = geometry[t] # end point

            # simple tests to reject segment, completely outside
            if ((max(x1, x2) < left) or
                (max(y1, y2) < bottom) or
                (min(x1, x2) > right) or
                (min(y1, y2) > top)):
                continue
            # simple tests to accept segment
            # completely inside
            elif (left <= x1 <= right and
                left <= x2 <= right and
                bottom <= y1 <= top and
                bottom <= y2 <= top):
                # find if segment is fully on border
                # we ignore it, but we add nodes on the border
                if ((x1 == left or x1 == right) and x1 == x2) or \
                    ((y1 == bottom or y1 == top) and y1 == y2):
                    node = Point(x1, y1)
                    self._add_vertex(node)
                    node = Point(x2, y2)
                    self._add_vertex(node)
                # segment is inside, 
                # but can still have one or two points
                # on the border of clipping window
                else:
                    pt = Point(x1, y1)
                    clipped_geometry.append( pt )
                    if first_segment == True:
                        start_node = pt
                    if last_segment == True:
                        end_node = Point(x2, y2)
                        clipped_geometry.append( end_node )
                    # start of segment is on border of clipping window
                    if (x1 == left or x1 == right) or \
                        (y1 == top or y1 == bottom):
                        start_node = Point(x1, y1)
                        new_sn_id = self._add_vertex(start_node)
                    # end of segment is on border of clipping window
                    if (x2 == left or x2 == right) or \
                        (y2 == top or y2 == bottom):
                        end_node = Point(x2, y2)
                        new_en_id = self._add_vertex(end_node)
                        # we only add the point if there will be more parts
                        if not last_segment:
                            clipped_geometry.append( end_node )
            # segment not fully inside, 
            # nor fully outside                    
            # -> clip
            else:
                clipped_segment = self._clip_segment(x1, y1, x2, y2)
                if clipped_segment is None:
                    # segment is fully outside clipping window
                    # but bbox of segment overlaps clipping window
                    continue
                # collapsed to one point, rejecting -- but adding to border
                if clipped_segment[0] == clipped_segment[1]:
                    node = Point(clipped_segment[0][0], 
                                 clipped_segment[0][1])
                    self._add_vertex(node)
                # segment is still a segment
                else:
                    # different start node after clip
                    if clipped_segment[0][0] != x1 or \
                        clipped_segment[0][1] != y1: 
                        start_node = Point(clipped_segment[0][0], 
                                           clipped_segment[0][1])
                        clipped_geometry.append( start_node )
                        new_sn_id = self._add_vertex(start_node)
                    else: 
                        clipped_geometry.append(Point(x1, y1))

                    # different end node after clip                    
                    if clipped_segment[1][0] != x2 or \
                        clipped_segment[1][1] != y2:
                        end_node = Point(clipped_segment[1][0], 
                                         clipped_segment[1][1])
                        new_en_id = self._add_vertex(end_node)
                        clipped_geometry.append( end_node )
                        # if this is the first segment and we do not have
                        # a start_node yet, we should set it as such
                        if first_segment == True and start_node is None:
                            start_node = Point(x1, y1)
                    # if this is the last segment of the polyline
                    # and we do not have a end node yet, take
                    # the end of the segment as the end node
                    elif last_segment == True and end_node is None:
                        end_node = Point(x2, y2)
                        clipped_geometry.append( end_node )

            if start_node is not None and end_node is not None:
                # found a clipped piece
                # add it to the `clipped' list
                sn_id = start_node_id
                en_id = end_node_id
                if new_sn_id is not None:
                    sn_id = new_sn_id
                if new_en_id is not None:
                    en_id = new_en_id
                attrs['locked'] = True
                attrs['clipped'] = True
                new_edge = (self.new_edge_id, 
                        sn_id, en_id,
                        left_face_id, right_face_id,
                        clipped_geometry, 
                        attrs)
                self.clipped.append(new_edge)
                # reset for a next part that eventually is inside
                clipped_geometry = LineString(srid = geometry.srid)
                start_node = None
                end_node = None
                new_sn_id = None
                new_en_id = None
                self.new_edge_id -= 1
    
    def _add_vertex(self, vertex):
        """Adds a vertex that is on the rim of the clipping window
        and returns a unique numeric identifier (negative) for this vertex
        """
        if vertex not in self.vertex_ids:
            self.vertices.append(vertex)
            vid = -1 * len(self.vertices) - 1
            self.vertex_ids[vertex] = vid
        else:
            vid = self.vertex_ids[vertex]
        return vid

    def _clip_segment(self, x1, y1, x2, y2):
        """Clips a segment
        
        The Liang-Barsky Algorithm is used for clipping
        """
        coords = None
        left, bottom, right, top = self.bbox.xmin, self.bbox.ymin, \
                                    self.bbox.xmax, self.bbox.ymax
        # the Segment can be parameterized as
        #
        # x = u * (x2 - x1) + x1
        # y = u * (y2 - y1) + y1
        #
        # for u = 0, x => x1, y => y1
        # for u = 1, x => x2, y => y2
        #
        # The following is the Liang-Barsky Algorithm
        # for segment clipping
        x1, y1, x2, y2 = map(float, [x1, y1, x2, y2])
        dx = x2 - x1
        dy = y2 - y1
        P = [-dx, dx, -dy, dy]
        q = [(x1 - left), (right - x1), (y1 - bottom), (top - y1)]
        u1 = 0.0
        u2 = 1.0
        # valid means inside OR partially inside, i.e. clipped
        valid = True 
        for i in xrange(4): 
            # 0 left, 1 right, 2 bottom, 3 top
            pi = P[i]
            qi = q[i]
            if pi == 0.: 
                # -> parallel line
                # was "< 1e-10" pi smaller than tolerance
                if qi < 0.0:
                    valid = False
                    break
            else:
                r = qi / pi
                if pi < 0.0: 
                    if r > u2:
                        valid = False
                        break
                    # update u1
                    if r > u1: 
                        u1 = r
                else:
                    if r < u1:
                        valid = False
                        break
                    # update u2
                    if r < u2: 
                        u2 = r
        # end for
        if valid:
            if u2 < 1:
                x2 = x1 + u2 * dx
                y2 = y1 + u2 * dy
            else:
                assert u2 == 1.
            if u1 > 0: 
                x1 += u1 * dx
                y1 += u1 * dy
            else:
                assert u1 == 0.
            coords = [(x1, y1), (x2, y2)]
        return coords

    @property
    def border_segments(self):
        """After clipping all edges, this property gives all
        edges that together form the rim of the clipping window
        """
        segments = []
        cx = (self.bbox.xmax + self.bbox.xmin) * .5
        cy = (self.bbox.ymax + self.bbox.ymin) * .5
        centre = (cx, cy)
        #radial sort around viewport
        clipped_coords = self.vertices[:]
        clipped_coords.sort(lambda x, y: cmp(-angle(centre, x), 
                                             -angle(centre, y)))
        for i in range(-1, len(clipped_coords) - 1):
            self.new_edge_id -= 1
            border_edge = (self.new_edge_id, 
                    self.vertex_ids[clipped_coords[i]],
                    self.vertex_ids[clipped_coords[i+1]],
                    self.border_face_id,
                    self.border_face_id,
                    LineString( (clipped_coords[i], clipped_coords[i + 1])),
                    {'locked': True, 'border': True, 'clipped': True}
                    )
            segments.append(border_edge)
        return segments
        # TODO:
        # - how to get left / right face info on this segment?
        # - if TopoMap is making loops, probably don't care about missing info?

class PartialProxy:
    def __init__(self, partial):
        self.partial = partial
    
    @property
    def faces(self):
        d = {}
        for key, value in zip(self.partial.faces.iterkeys(), self.partial.faces.itervalues()):
            if not value.attrs['locked']:
                d[key] = value
        return d

    @property
    def half_edges(self):
        return self.partial.half_edges
    @property
    def nodes(self):
        return self.partial.nodes
    @property
    def srid(self):
        return self.partial.srid


def test():
    import matplotlib.pyplot as plt

    ec = EdgeClipper(bbox=Envelope(0, 0, 10, 10), border_face_id=None)
    
    ec.clip_edge(1, 
        1, 2, 3, 4, 
        geometry = LineString([(-5, 5), (2.5, 12.5)], srid=28992), 
        attrs = {})

    ec.clip_edge(5, 
        6, 7, 8, 9, 
        geometry = LineString([(-5, 5), (5, 5)], srid=28992), 
        attrs = {})
    
    ec.clip_edge(10, 
        11, 12, 13, 14, 
        geometry = LineString([(7.5, 5), (10, 5)], srid=28992), 
        attrs = {})

    ec.clip_edge(15, 
        16, 17, 18, 19, 
        geometry = LineString([(10, 6), (7.5, 6)], srid=28992), 
        attrs = {})

    ec.clip_edge(20, 
        21, 22, 23, 24, 
        geometry = LineString([(10, 7), (7.5, 7), (6.5, 7)], srid=28992), 
        attrs = {})

    ec.clip_edge(25, 
        26, 27, 28, 29, 
        geometry = LineString([(2.5, 12.5), (2.5, 10), (7.5, 10), (7.5, 12.5)], srid=28992), 
        attrs = {})

    ec.clip_edge(30, 
        31, 32, 33, 34, 
        geometry = LineString([(1,7), (0,7), (-1, 7)], srid=28992), 
        attrs = {})
    
    ec.clip_edge(35, 
        36, 37, 38, 39, 
        geometry = LineString([(-1,8), (0,8), (1, 8)], srid=28992), 
        attrs = {})
    
    ec.clip_edge(40, 
        41, 42, 43, 44, 
        geometry = LineString([(1, -1), (1,1), (2,1), (2,-1), (3,-1), (3,1), (4,1), (4,-1), (5,-1), (5,1), (6,1)], srid=28992), 
        attrs = {})
    
    ec.clip_edge(45, 
        46, 47, 48, 49, 
        geometry = LineString([(0, 11), (2, 9)], srid=28992), 
        attrs = {})
    ec.clip_edge(50, 
        51, 52, 53, 54, 
        geometry = LineString([(-1, 11), (1, 9)], srid=28992), 
        attrs = {})    
    
    ec.clip_edge(55, 
        56, 57, 58, 59, 
        geometry = LineString([(9, 2), (12, 2)], srid=28992), 
        attrs = {})
    
    ec.clip_edge(55, 
        56, 57, 58, 59, 
        geometry = LineString([(-1,3), (0,3), (5,4), (10,3)], srid=28992), 
        attrs = {})

    ec.clip_edge(60, 
        61, 62, 63, 64, 
        geometry = LineString([(7,2), (8,0), (9,1)], srid=28992), 
        attrs = {})

    # - print clipped edges --------------------------------    
    for item in ec.clipped:
        print item

    # - plot --------------------------------
    for item in ec.border_segments:
        geom = item[5]
        X, Y = [], []
        [(X.append(vertex[0]), Y.append(vertex[1])) for vertex in geom]    
        plt.plot(X, Y, 'b-', alpha=0.5)    
    
    for item in ec.clipped:
        geom = item[5]
        X, Y = [], []
        [(X.append(vertex[0]), Y.append(vertex[1])) for vertex in geom]    
        plt.plot(X, Y, 'gH-', alpha=0.5, markersize=20)
    
    X, Y = [], []
    [(X.append(vertex[0]), Y.append(vertex[1])) for vertex in ec.vertices]
    plt.plot(X, Y, 'ro')
    
    plt.axis([-1, 11, -1, 11])
    plt.show()

def plot(ec):
    import matplotlib.pyplot as plt

    # - plot --------------------------------
    for item in ec.border_segments:
        geom = item[5]
        X, Y = [], []
        [(X.append(vertex[0]), Y.append(vertex[1])) for vertex in geom]    
        plt.plot(X, Y, 'b-', alpha=0.5)    
    
    for item in ec.clipped:
        geom = item[5]
        X, Y = [], []
        [(X.append(vertex[0]), Y.append(vertex[1])) for vertex in geom]    
        plt.plot(X, Y, 'gH-', alpha=0.5, markersize=20)

    for geom in ec.original_edges:
        X, Y = [], []
        [(X.append(vertex[0]), Y.append(vertex[1])) for vertex in geom]    
        plt.plot(X, Y, 'rH-', markersize=5)
    
    X, Y = [], []
    [(X.append(vertex[0]), Y.append(vertex[1])) for vertex in ec.vertices]
    plt.plot(X, Y, 'ro')
    
    # plt.axis([-1, 11, -1, 11])
    plt.show()


def test2():
#    81996.029 454995.4185 82010.37 455005.837
#    LINESTRING(81979.573 454987.807, 81981.688 454985.0, 81996.029 454995.4185, 82010.37 455005.837, 82009.463 455007.209)
#    POLYGON((81000.0 455000.0, 81000.0 456000.0, 82000.0 456000.0, 82000.0 455000.0, 81000.0 455000.0))
    ec = EdgeClipper(bbox=Envelope(81000.0, 455000.0, 82000.0, 456000.0), border_face_id=None)
    
    ec.clip_edge(1, 
        1, 2, 3, 4, 
        geometry = LineString([[81979.573, 454987.807], 
[81981.688, 454985.0], 
[81996.029, 454995.4185], 
[82010.37, 455005.837], 
[82009.463, 455007.209]], srid=28992), 
        attrs = {})
    
#    plot(ec)

        
if __name__ == "__main__":
    test()