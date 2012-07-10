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

# ORACLE:
# SELECT sdo_topo.Drop_Topology('test_tp');
# SELECT sdo_topo.Create_Topology('test_tp', 0.0001, 28992);

#test_tp_edge$
# Name                                      Null?    Type
# ----------------------------------------- -------- ----------------------------
# EDGE_ID                                   NOT NULL NUMBER
# START_NODE_ID                                      NUMBER
# END_NODE_ID                                        NUMBER
# NEXT_LEFT_EDGE_ID                                  NUMBER
# PREV_LEFT_EDGE_ID                                  NUMBER
# NEXT_RIGHT_EDGE_ID                                 NUMBER
# PREV_RIGHT_EDGE_ID                                 NUMBER
# LEFT_FACE_ID                                       NUMBER
# RIGHT_FACE_ID                                      NUMBER
# GEOMETRY                                           PUBLIC.SDO_GEOMETRY


#SQL> desc test_tp_node$
# Name                                      Null?    Type
# ----------------------------------------- -------- ----------------------------
# NODE_ID                                   NOT NULL NUMBER
# EDGE_ID                                            NUMBER
# FACE_ID                                            NUMBER
# GEOMETRY                                           PUBLIC.SDO_GEOMETRY
#Geometry object (point) representing this node
#For each node, the EDGE_ID or FACE_ID value (but not both) must be null:
#    If the EDGE_ID value is null, the node is an isolated node (that is, isolated in a face).
#    If the FACE_ID value is null, the node is not an isolated node, but rather the start node or end node of an edge.

#SQL> desc test_tp_face$
# Name                                      Null?    Type
# ----------------------------------------- -------- ----------------------------
# FACE_ID                                   NOT NULL NUMBER
# BOUNDARY_EDGE_ID                                   NUMBER
# ISLAND_EDGE_ID_LIST                                PUBLIC.SDO_LIST_TYPE
# ISLAND_NODE_ID_LIST                                PUBLIC.SDO_LIST_TYPE
# MBR_GEOMETRY                                       PUBLIC.SDO_GEOMETRY

#FACE_ID
#Unique ID number for this face
#
#BOUNDARY_EDGE_ID
#ID number of the boundary edge for this face. The sign of this number (which is ignored for use as a key) indicates which orientation is being used for this boundary component (positive numbers indicate the left of the edge, and negative numbers indicate the right of the edge).
#
#ISLAND_EDGE_ID_LIST
#Island edges (if any) in this face. (The SDO_LIST_TYPE type is described in Section 1.6.6.)
#
#ISLAND_NODE_ID_LIST
#Island nodes (if any) in this face. (The SDO_LIST_TYPE type is described in Section 1.6.6.)
#
#MBR_GEOMETRY
#Minimum bounding rectangle (MBR) that encloses this face. (This is required, except for the universe face.) The MBR must be stored as an optimized rectangle (a rectangle in which only the lower-left and the upper-right corners are specified). The SDO_TOPO.INITIALIZE_METADATA procedure creates a spatial index on this column.


# insert into test_tp_edge$ (select edge_id, start_node_id, end_node_id, lccw, lcw, rccw, rcw, left_face_id, right_face_id, geometry from myexport_edge);