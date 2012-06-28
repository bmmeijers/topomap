from brep.geometry import Point, LineString
from primitives import angle

class EdgeClipper(object):
    def __init__(self, bbox, border_face_id):
        self.bbox = bbox
        self.vertices = []
        self.vertex_ids = {}
        self._add_vertex( Point(bbox.xmin, bbox.ymin) )
        self._add_vertex( Point(bbox.xmin, bbox.ymax) )
        self._add_vertex( Point(bbox.xmax, bbox.ymin) )
        self._add_vertex( Point(bbox.xmax, bbox.ymax) )
        self.clipped = []
        self.segment_ct = -1
        self.border_face_id = border_face_id
        self.original_edges = []
    
    def clip_edge(self, edge_id,
                       start_node_id, end_node_id,
                       left_face_id, right_face_id,
                       geometry, attrs = {}):
        
        self.original_edges.append( (edge_id,
                       start_node_id, end_node_id,
                       left_face_id, right_face_id,
                       geometry, attrs) )

#        print "isect?", self.bbox.intersects(geometry.envelope) 
        if self.bbox.intersects(geometry.envelope) and \
            not self.bbox.contains(geometry.envelope):
#            print "have to clip, #", edge_id
            ll_x, ll_y, ul_x, ul_y = self.bbox.xmin, self.bbox.ymin, \
                                     self.bbox.xmax, self.bbox.ymax
            segment_ct = len(geometry) - 1
            start_node = None
            end_node = None
            clipped_ln = LineString()
            new_sn_id = None
            new_en_id = None
            for s in xrange(segment_ct):
                first_segment = False
                last_segment = False
                t = s + 1
                if s == 0: #first segment
                    first_segment = True
                if t == segment_ct: # last segment
                    last_segment = True
                x1, y1 = geometry[s] # start point of segment 
                x2, y2 = geometry[t] # end point
                #
                # TODO: find if those simple tests are needed
                # My understanding is that these are incorporated in 
                # loop of Liang-Barsky already!!!
                #
                # simple tests to reject segment, completely outside
                if ((max(x1, x2) < ll_x) or
                    (max(y1, y2) < ll_y) or
                    (min(x1, x2) > ul_x) or
                    (min(y1, y2) > ul_y)):
                    pass
                # simple tests to accept segment, completely inside
                elif (ll_x < x1 < ul_x and
                    ll_x < x2 < ul_x and
                    ll_y < y1 < ul_y and
                    ll_y < y2 < ul_y):
                    pt = Point(x1, y1)
                    clipped_ln.append( pt )
                    if first_segment == True:
                        start_node = pt
                    if last_segment == True:
                        end_node = Point(x2, y2)
                        clipped_ln.append( end_node )
                # figure out where to clip
                else:
                    coords = None
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
                    dx = x2 - x1
                    dy = y2 - y1
                    P = [-dx, dx, -dy, dy]
                    q = [(x1 - ll_x), (ul_x - x1), (y1 - ll_y), (ul_y - y1)]
                    u1 = 0.0
                    u2 = 1.0
                    valid = True # valid means inside OR partially inside, i.e. clipped
                    for i in xrange(4): # 0 left 1 right 2 bottom 3 top
                        pi = P[i]
                        qi = q[i]
                        if abs(pi) < 1e-10:
#                           print "NOTICE: pi smaller than tolerance -> parallel line"
                            if qi < 0.0:
                                valid = False
                                break
                        else:
                            r = qi / pi
                            if pi < 0.0: 
                                if r > u2:
                                    valid = False
                                    break
                                if r > u1: # update u1
                                    u1 = r
                            else:
                                if r < u1:
                                    valid = False
                                    break
                                if r < u2: # update u2
                                    u2 = r
                    if valid:
                        coords =  [(((u1 * dx) + x1), ((u1 * dy) + y1)),
                                   (((u2 * dx) + x1), ((u2 * dy) + y1))]
                        if (coords[0][0] == coords[1][0]) and \
                           (coords[0][1] == coords[1][1]):
                            # touching is_edge in one point -> clipped to one node actually
                            raise NotImplementedError, """Clip collapsed line to point, 
                                                        i.e. same coords of clipped element!"""
                        else:
                            if coords[0][0] != x1 or coords[0][1] != y1: # Different start node after clip"
                                start_node = Point(coords[0][0], coords[0][1])
                                clipped_ln.append( start_node )
                                new_sn_id = self._add_vertex(start_node)
                            else: 
                                clipped_ln.append( Point(coords[0][0], coords[0][1]))
                            if coords[1][0] != x2 or coords[1][1] != y2:
                                end_node = Point(coords[1][0], coords[1][1])
                                new_en_id = self._add_vertex(end_node)
                                clipped_ln.append( end_node )
                                if first_segment == True and start_node is None:
                                    start_node = Point(x1, y1)
                            elif last_segment == True and end_node is None:
                                end_node = Point(x2, y2)
                                clipped_ln.append( end_node )
                if start_node is not None and end_node is not None:
#                    print "found piece inside >>", clipped_ln
                    # TODO:
                    # - segment is_edge ids, get them correct: done
                    # - node ids, get them correct: done
                    sn_id = start_node_id
                    en_id = end_node_id
                    if new_sn_id is not None:
                        sn_id = new_sn_id
                    if new_en_id is not None:
                        en_id = new_en_id
                    attrs['locked'] = True
                    attrs['clipped'] = True
                    is_edge = (self.segment_ct, 
                            sn_id, en_id,
                            left_face_id, right_face_id,
                            clipped_ln, 
                            attrs)
                    self.clipped.append(is_edge)
                    clipped_ln = LineString()
                    start_node = None
                    end_node = None
                    new_sn_id = None
                    new_en_id = None
                    self.segment_ct -= 1
#        else:
#            print "discard #", edge_id, " outside"
    
    def _add_vertex(self, vertex):
        if vertex not in self.vertex_ids:
            self.vertices.append(vertex)
            vid = -1 * len(self.vertices) - 1
            self.vertex_ids[vertex] = vid
        else:
            vid = self.vertex_ids[vertex]
        return vid
    
    @property
    def border_segments(self):
        segments = []
        cx = (self.bbox.xmax + self.bbox.xmin) * .5
        cy = (self.bbox.ymax + self.bbox.ymin) * .5
        centre = (cx, cy)
        #radial sort around viewport
        clipped_coords = self.vertices[:]
        clipped_coords.sort(lambda x, y: cmp(-angle(centre, x), 
                                             -angle(centre, y)))
#        print clipped_coords
        for i in range(-1, len(clipped_coords) - 1):
            self.segment_ct -= 1
#            print self.segment_ct, #segment id
#            print self.vertex_ids[clipped_coords[i]], # sn
#            print self.vertex_ids[clipped_coords[i+1]], # en
#            print "? ?", # lf rf
#            print LineString( (clipped_coords[i], clipped_coords[i + 1]))
            is_edge = (self.segment_ct, 
                    self.vertex_ids[clipped_coords[i]],
                    self.vertex_ids[clipped_coords[i+1]],
                    self.border_face_id, # TODO: make border is_edge explicit!
                    self.border_face_id,
                    LineString( (clipped_coords[i], clipped_coords[i + 1])),
                    {'locked': True, 'border': True}
                    )
            segments.append(is_edge)
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
