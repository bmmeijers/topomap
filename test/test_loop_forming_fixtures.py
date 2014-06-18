from topomap.topomap import TopoMap, LoopFactory
from collections import namedtuple
from simplegeom.geometry import LineString, Point

Edge = namedtuple("Edge", "edge_id start_node_id end_node_id left_face_id right_face_id geometry")
Face = namedtuple("Face", "face_id feature_class")

edges = [ 
#     [Edge(1, 1, 2, 1, 1, LineString([(1,1), (2,1)])),
#      Edge(2, 3, 3, 1, 0, LineString([(0, 0), (3, 0), (3, 2), (0, 2), (0, 0)])),
#      Edge(3, 4, 1, 1, 1, LineString([(0.5, 1), (1,1)])),
#      ],
#     [Edge(1, 1, 2, 1, 1, LineString([(1,1), (2,1)])),
#      Edge(2, 3, 3, 1, 0, LineString([(0, 0), (3, 0), (3, 2), (0, 2), (0, 0)])),
#      ],
#     [Edge(1, 1, 2, 1, 1, LineString([(1,1), (2,1)])),
#      Edge(2, 3, 3, 1, 0, LineString([(0, 0), (3, 0), (3, 2), (0, 2), (0, 0)])),
#      Edge(3, 4, 1, 1, 1, LineString([(0.5, 1), (1,1)])),
#      Edge(4, 3, 1, 1, 1, LineString([(0, 0), (1,1)])),
#      ],
#     [Edge(2, 3, 3, 1, 0, LineString([(0, 0), (3, 0), (3, 2), (0, 2), (0, 0)])),
#      Edge(4, 3, 1, 1, 1, LineString([(0, 0), (1,1)])),
#      Edge(1, 1, 1, 2, 1, LineString([(1,1), (2,1), (2, 1.5), (1,1)]))
#      ],
#     [Edge(2, 3, 3, 1, 0, LineString([(0, 0), (3, 0), (3, 2), (0, 2), (0, 0)])),
#      Edge(4, 3, 1, 1, 1, LineString([(0, 0), (1,1)])),
#      Edge(1, 1, 1, 2, 1, LineString([(1,1), (2,1), (2, 1.5), (1,1)])),
#      Edge(3, 1, 1, 1, 3, LineString([(1,1), (0.5,1), (0.5, 1.5), (1,1)]))
#      ],
#      [
#       # loop
#       Edge(1, 1, 2, 1, 0, LineString([(0, 0), (3, 0)])),
#       Edge(2, 2, 3, 1, 0, LineString([(3, 0), (3, 2)])),
#       Edge(3, 3, 4, 1, 0, LineString([(3, 2), (0, 2)])),
#       Edge(4, 4, 1, 1, 0, LineString([(0, 2), (0, 0)])),
#       # dangle
#       Edge(5, 1, 5, 1, 1, LineString([(0, 0), (1,1)])),
#       Edge(6, 3, 6, 1, 1, LineString([(3, 2), (2,1)])),           
#       ],
#      [
#       # loop
#       Edge(1, 1, 2, 1, 0, LineString([(0, 0), (3, 0)])),
#       Edge(2, 2, 3, 1, 0, LineString([(3, 0), (3, 2)])),
#       Edge(3, 3, 4, 1, 0, LineString([(3, 2), (0, 2)])),
#       Edge(4, 4, 1, 1, 0, LineString([(0, 2), (0, 0)])),
#       # dangle
#       Edge(5, 1, 5, 1, 1, LineString([(0, 0), (1,1)])),
#       Edge(6, 5, 6, 1, 1, LineString([(1,1), (1, 1.5)])),
#       Edge(7, 5, 7, 1, 1, LineString([(1,1), (1.5, 1)]))
#       #Edge(6, 3, 6, 1, 1, LineString([(3, 2), (2,1)])),           
#       ],
     [
      # loop
      Edge( 1, 1, 2, 1, 0, LineString([(0, 0), (3, 0)])),
      Edge( 2, 2, 3, 1, 0, LineString([(3, 0), (3, 2)])),
      Edge( 3, 3, 4, 1, 0, LineString([(3, 2), (0, 2)])),
      Edge( 4, 4, 1, 1, 0, LineString([(0, 2), (0, 0)])),
      
      Edge( 5, 1, 5, 1, 2, LineString([(0,0), (1,1.5), (1.5, 1.5)]) ),
      Edge( 6, 5, 1, 1, 2, LineString([(1.5, 1.5), (0,0)]) ),
      
      Edge( 7, 5, 6, 1, 3, LineString([(1.5, 1.5), (1.25, 1.8), (1.5, 1.8)]) ),
      Edge( 8, 6, 5, 1, 3, LineString([(1.5, 1.8), (1.5, 1.5)]) ),
      Edge( 9, 5, 7, 1, 4, LineString([(1.5, 1.5), (2, 1.5), (2, 0.5)]) ),
      Edge(10, 7, 5, 1, 4, LineString([(2, 0.5), (1.5, 1.5)]) )
      ]  
]
faces = [
#     [Face(1, 1)]
#     ,
#     [Face(1, 1)]
#     ,
#     [Face(1, 1)]
#     ,
#     [Face(1, 1),
#      Face(2, 1)],
#     [Face(1, 1),
#      Face(2, 1),
#      Face(3, 1),
#      ]
#     ,
#     [Face(1, 1)]
# ,
#     [Face(1, 1)]
#     ,
    [Face(1, 1),
     Face(2, 1),
     ]
]

def topomap(edges, faces):
    universe_id = 0
    srid = 28992
    assert universe_id is not None
    assert srid is not None
    topo_map = TopoMap(universe_id = universe_id, srid = srid)
    
    for face_id, feature_class, in faces:
        assert face_id is not None
        topo_map.add_face(face_id, 
                          attrs = {'feature_class': feature_class,})
    
    for edge_id, \
        start_node_id, \
        end_node_id, \
        left_face_id, \
        right_face_id, \
        geometry, in edges:
        try:
            assert edge_id is not None
            assert start_node_id is not None
            assert end_node_id is not None
            assert left_face_id is not None
            assert right_face_id is not None
            assert geometry is not None
            #for item in (edge_id, start_node_id, end_node_id, left_face_id, right_face_id, geometry):
            #   assert item is not None, item
        except AssertionError:
            raise ValueError("Edge {0} not correct -- None field found".format(edge_id))
        topo_map.add_edge(edge_id,
                          start_node_id, end_node_id,
                          left_face_id, right_face_id,
                          geometry)
    LoopFactory.find_loops(topo_map)
    return topo_map

fixtures = []
for e, f in zip(edges, faces):
    for edge in e:
        print edge.geometry
    
    tm = topomap(e, f)
    fixtures.append(tm)

for fixture in fixtures:
    print "--"
    for face_id in [1]:
        geometries = []
        for loop in fixture.faces[face_id].loops:
            geometries.extend( [geom for geom in loop.geometry] )
        for geom in geometries:
#             print type(geom), 
            print geom
#         nrs = [len(geom) for geom in geometries]
#         nrs.sort()
#         assert nrs == [2, 2, 5]
#         found = False
#         for geom in geometries:
#             print len(geom)
#             if len(geom) == 5:
#                 found = True
#         assert found == True
#         found = False
#         for geom in geometries:
#             print len(geom)
#             if len(geom) == 2:
#                 found = True
#         assert found == True