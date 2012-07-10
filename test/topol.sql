SELECT topology.DropTopology('topo_test');
SELECT topology.CreateTopology('topo_test', 28992, 0.001);

SELECT topology.TopologySummary('topo_test');
SELECT topology.ValidateTopology('topo_test');  

INSERT INTO topo_test.edge(edge_id, geom, start_node, end_node, left_face, right_face, next_left_edge, next_right_edge)
SELECT 
    e.edge_id, 
    e.geometry, 
    e.start_node_id, 
    e.end_node_id, 
    e.left_face_id, 
    e.right_face_id,
    l.next,
    r.next
FROM
    tp_top10nl_small_edge e
JOIN 
    temp__tp_top10nl_small_edge_left l
ON 
    e.edge_id = l.edge_id
JOIN 
    temp__tp_top10nl_small_edge_right r
ON 
    e.edge_id = r.edge_id
;

INSERT INTO topo_test.face(face_id, mbr) SELECT face_id, mbr_geometry FROM tp_top10nl_small_face;
INSERT INTO topo_test.node(node_id, geom) SELECT node_id, geometry FROM tp_top10nl_small_node;
