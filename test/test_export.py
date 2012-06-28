import sys
import logging
#logging.basicConfig(
#    format="%(asctime)s %(levelname)s (%(process)d) %(message)s", 
#    stream=sys.stdout, 
#    level=logging.DEBUG)
from topomap.io import TopoMapFactory
from topomap.validation import TopoMapValidator
from topomap.export import TopoMapExporter

tm = TopoMapFactory.topo_map('tp_top10nl_small', universe_id = 0, srid = 28992)

validator = TopoMapValidator(tm)
validator.validate()

TopoMapExporter.export(tm, "myexport", wings=True)

# * SELECT topology.DropTopology('topo_boston');
# * SELECT topology.CreateTopology('topo_boston', 2249, 0.25);
# * SELECT tiger.topology_load_tiger('topo_boston', 'place', '2507000'); 
# * SELECT topology.TopologySummary('topo_boston');
# * SELECT topology.ValidateTopology('topo_boston');  
#
# 'INSERT INTO ' || quote_ident(toponame) || '.edge(edge_id, geom, 
#  start_node, end_node, 
#  left_face, right_face, 
#  next_left_edge, next_right_edge)
# 'INSERT INTO ' || quote_ident(toponame) || '.face(face_id, mbr)
# 'INSERT INTO ' || quote_ident(toponame) || '.node(node_id, geom)  