from simplegeom.geometry import Envelope
from topomap.io import TopoMapFactory
xmin = 88000
ymin = 455000
N = 3
xmax = xmin + N * 1000
ymax = ymin + N * 1000
box = Envelope(xmin, ymin, xmax, ymax)
tm = TopoMapFactory.clipped_topo_map('tp_top10nl4', bbox=box, universe_id=0, srid=28992)

def example():
    tm = TopoMapFactory.topo_map_bbox('tp_top10nl4', bbox=box.polygon, universe_id=0, srid=28992)
    import matplotlib.pyplot as plt
    
    ec = EdgeClipper(box, -1)
    for edge in tm.half_edges.itervalues():
        if box.contains_properly(edge.geometry.envelope):
            X, Y = [], []
            [(X.append(vertex[0]), Y.append(vertex[1])) for vertex in edge.geometry]    
            plt.plot(X, Y, 'go-', alpha=0.5, markersize=4)
        else:
            ec.clip_edge(edge.id, 
                     edge.start_node.id, edge.end_node.id, 
                     edge.left_face.id, edge.right_face.id, 
                     edge.geometry, 
                     edge.attrs
                     )
    
    for item in ec.border_segments:
            geom = item[5]
            X, Y = [], []
            [(X.append(vertex[0]), Y.append(vertex[1])) for vertex in geom]    
            plt.plot(X, Y, 'b-', alpha=0.5)    
    
    for item in ec.clipped:
        geom = item[5]
        X, Y = [], []
        [(X.append(vertex[0]), Y.append(vertex[1])) for vertex in geom]    
        plt.plot(X, Y, 'gH-', alpha=0.5, markersize=3)
    
    
    plt.axis([box.xmin-100, box.xmax+100, box.ymin-100, box.ymax+100 ])
    plt.show()

example()