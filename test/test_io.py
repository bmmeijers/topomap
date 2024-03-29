import sys
import logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s (%(process)d) %(message)s", 
    stream=sys.stdout, 
    level=logging.INFO)
from topomap.io import TopoMapFactory
import time

attribs = {"face_id": "face_id",
"feature_class": "1",
"edge_id": "edge_id",
"start_node_id" : "start_node_id", 
"end_node_id": "end_node_id",
"left_face_id": "left_face_id", 
"right_face_id": "right_face_id",
"geometry": "geometry"}


tm = TopoMapFactory.topo_map('set880k', universe_id = -1, srid = 28992, attribute_mapping = attribs)

start = time.clock()
for face in tm.faces.itervalues():
    g = face.multigeometry()
end = time.clock()

print end - start
