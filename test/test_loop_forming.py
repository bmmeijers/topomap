from topomap.io import TopoMapFactory

attribute_mapping = {
    "face_id": "face_id",
    "feature_class": "feature_class",
    "edge_id": "edge_id",
    "start_node_id": "start_node_id",
    "end_node_id": "end_node_id",
    "left_face_id": "left_face_id_low",
    "right_face_id": "right_face_id_low",
    "geometry": "geometry",
}
tm = TopoMapFactory.topo_map('schouwen', 
                             attribute_mapping=attribute_mapping, 
                             universe_id = -1, 
                             srid = 28992)
for face in tm.faces.itervalues():
    if not face.unbounded:
        print face.id
        for loop in face.loops:
            geometries = loop.geometry
            for geom in geometries:
                print geom