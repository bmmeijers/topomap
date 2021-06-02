"""Non-recursive version of obtaining QuadTree tile scheme

"""

__date_created__ = '2012-07-02'
__author__ = 'Martijn Meijers'

import sys
import logging
logging.basicConfig(
    format="%(asctime)s %(levelname)s (%(process)d) %(message)s", 
    stream=sys.stderr, 
    level=logging.DEBUG)
#from brep.io import geom_from_binary
from connection.connect import ConnectionFactory
from connection.stateful import record
from topomap.io import TopoMapFactory

from simplegeo.postgis import register
register()
#from brep.geometry import Envelope
from simplegeo.geometry import Envelope
from collections import deque

from math import ceil, floor

factory = ConnectionFactory()
connection = factory.connection()

NAME = "tp_top10nl"

class QuadTree(object):
    count = 150000 # default value
    def __init__(self, dataset, srid, geometry_column):
        cursor = connection.cursor()
        cmd = "SELECT st_extent({1})::geometry FROM {0}".format(dataset, geometry_column)
        cursor.execute(cmd)
        wkb ,= cursor.fetchone()
        area_extent = wkb.envelope
        cursor.close()
        xmin, ymin = floor(area_extent.xmin), floor(area_extent.ymin)
        w, h = ceil(area_extent.width), ceil(area_extent.height)
        xmin = int(xmin)
        ymin = int(ymin)
        w = int(ceil(w))
        h = int(ceil(h))
        dw = int(ceil(w / 2.))
        dh = int(ceil(h / 2.))
        centerx = xmin + dw
        centery = ymin + dh
        # enlarge box by 10%, so that everything fits
        dw = int(dw + 0.1 * dw)
        dh = int(dh + 0.1 * dh)
        if w > h:
            square = Envelope(xmin=centerx - dw, 
                              ymin=centery - dw, 
                              xmax=centerx + dw, 
                              ymax=centery + dw, 
                              srid = srid)
        else:
            square = Envelope(xmin=centerx - dh, 
                              ymin=centery - dh, 
                              xmax=centerx + dh, 
                              ymax=centery + dh,
                              srid = srid)     
        self.root = Quad(square, "0", dataset, srid, geometry_column)

    def accept(self, visitor):
        visitor.visit(self.root)

class Quad(object):
    def __init__(self, envelope, label, dataset, srid, geometry_column, parent = None):
        self.envelope = envelope
        self.label = label
        self.dataset = dataset
        self.srid = srid
        self.count = None
        self.parent = parent
        self.children = None # [None, None, None, None]
    
    def get_count(self, geometry_column):
        cursor = connection.cursor()
        cmd = """SELECT 
                    count(*)
                 FROM 
                     {1}
                 WHERE
                     {3} &&
                     st_envelope(st_setsrid('{0}'::geometry, {2}))
                                 AND
                     ST_ContainsProperly( 
                     st_envelope(st_setsrid('{0}'::geometry, 
                                 {2})), {3})""".format(self.envelope,
                                                   self.dataset,
                                                   self.srid,
                                                   geometry_column)
        cursor.execute(cmd)
        count,  = cursor.fetchone()
        if count is None:
            self.count = 0
        else:
            self.count = int(count)
        cursor.close()


class Visitor(object):
    """General visitor"""
    def visit(self, node):
        """Visit a node"""
        # Method dispatch, based on type of node
        # Find a specific visit method, default to "default"
        methname = "visit_%s" % node.__class__.__name__
        method = getattr(self, methname, self.default)
        # Call visit method on node
        method(node)

    def default(self, node):
        '''Visit node children'''
        for child in node.children:
            self.visit(child)


class NodeVisitor(Visitor):
    def __init__(self):
        super(NodeVisitor, self).__init__()
        self.output = []
    
    def default(self, node):
        if node.children is not None:
            self.output.append(node)
            for child in node.children:
                self.visit(child)
        else:
            self.output.append(node)

def reconstruct():
    count = 25000
    geometry_column = "mbr_geometry"
    name = '{}_face'.format(NAME)
    srid = 28992
    QuadTree.count = count
    tree = QuadTree(dataset=name, srid=srid, geometry_column=geometry_column)
    quads = [tree.root]
    while quads:
        q = quads.pop()
        print q.envelope, q.srid
        q.get_count(geometry_column)
        if q.count > QuadTree.count:
            xmin, ymin, = int(q.envelope.xmin), int(q.envelope.ymin)
            xmax, ymax, = q.envelope.xmax, q.envelope.ymax
            hw, hh, = q.envelope.width / 2, q.envelope.height / 2
            cx, cy, = int(xmin + hw), int(ymin + hh)
            nw = Envelope(xmin=xmin, ymin=cy,  xmax=cx, ymax=ymax, srid = q.srid) # 0
            ne = Envelope(xmin=cx,   ymin=cy,  xmax=xmax, ymax=ymax, srid = q.srid) # 1
            sw = Envelope(xmin=xmin, ymin=ymin, xmax=cx, ymax=cy, srid = q.srid) # 2
            se = Envelope(xmin=cx,   ymin=ymin, xmax=xmax, ymax=cy, srid = q.srid) # 3
            labels = []
            for i in range(4):
                labels.append("{0}{1}".format(q.label, i))
            nwq, neq, swq, seq, = Quad(nw, labels[0], name, srid, geometry_column, parent = q), \
                                  Quad(ne, labels[1], name, srid, geometry_column, parent = q), \
                                  Quad(sw, labels[2], name, srid, geometry_column, parent = q), \
                                  Quad(se, labels[3], name, srid, geometry_column, parent = q)
            q.children = [nwq, neq, swq, seq]
            for item in (nwq, neq, swq, seq):
                quads.append(item)
    visitor = NodeVisitor()
    tree.accept(visitor)
    return visitor.output


def do(quad):
    poly, skip, = quad
    srid = 28992
    topo_map = TopoMapFactory.topo_map(name=NAME, 
                                        bbox=poly,
                                        skip=skip,
                                        universe_id=0, 
                                        srid=srid)
    logging.debug("Reconstructed: {}".format(len(topo_map.faces) - 1))
    return len(topo_map.faces) - 1


if __name__ == "__main__":
    logging.debug('Starting')
#    from multiprocessing import Pool
    logging.debug('Retrieving quads')
    quads = reconstruct()
    process = []
    for quad in quads:
        if quad.children:
            process.append(
                (quad.envelope.polygon, 
                 [q.envelope.polygon for q in quad.children],))
        else:
            process.append((quad.envelope.polygon, [],))
    logging.debug('Start reconstruction')
#    pool = Pool() 
    total = sum(map(do, process))
    
    logging.info("Reconstructed {}".format(total))
    