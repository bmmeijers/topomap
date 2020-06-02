#from sink import use
#use('oracle')
from sink import DBColumn, Schema, Index, Layer#, dumps

import warnings

class TopoMapExporter(object):
    def __init__(self):
        pass

    @classmethod
    def export(cls, topo_map, name, stream, face_geometry = True, blnwings = False):
        if blnwings:
            warnings.warn("Wings have not been fully tested")
        # Make schema
        # NODES
        node_id = DBColumn("node_id", "numeric")
        point = DBColumn("geometry", "point")
        
        # TODO:
        # - edge_id with node table -> start node = +, end_node = - of edge
        # - face_id with node table -> contained in face <face_id>
        
        #
        schema = Schema()
        schema.add_field(node_id)
        schema.add_field(point)
        schema.add_index( Index(fields = [node_id], primary_key = True) )
        schema.add_index( Index(fields = [point], cluster = True) )
        #
        nodes = Layer(schema, '{0}_node'.format(name), srid = topo_map.srid)
        
        # FACES
        face_id = DBColumn("face_id", "numeric")
        area = DBColumn("area", "float")
        class_ = DBColumn("feature_class", "integer")
        pip = DBColumn("pip_geometry", "point")
        mbr = DBColumn("mbr_geometry", "box2d")
        if face_geometry:
            poly = DBColumn("geometry", "polygon")
        #
        schema = Schema()
        schema.add_field(face_id)
        schema.add_field(area)
        schema.add_field(class_)
        schema.add_field(pip)
        schema.add_field(mbr)
        if face_geometry:
            schema.add_field(poly)
        schema.add_index( Index(fields = [face_id], primary_key = True) )
        schema.add_index( Index(fields = [pip]) )
        schema.add_index( Index(fields = [mbr], cluster = True) )
        if face_geometry:
            schema.add_index( Index(fields = [poly], cluster = True) )
        #
        faces = Layer(schema, '{0}_face'.format(name), srid = topo_map.srid)
        
        # TODO:
        # - boundary_edge_id: signed edge on outer loop, which starts loop in
        #   correct direction
        # - island_edge_id list
        # - island_node_id list
        
        # EDGES
        edge_id = DBColumn("edge_id", "numeric")
        left = DBColumn("left_face_id", "numeric")
        right = DBColumn("right_face_id", "numeric")
        start = DBColumn("start_node_id", "numeric")
        end = DBColumn("end_node_id", "numeric")
        if blnwings:
            # wings
            #
            #   \     / 
            #    \   /  
            #     \e/   
            # lccw ^ rcw / prvr
            # nxtl |  
            #(LF)  |  (RF)
            #      |  
            #  lcw o rccw / nxtr
            # prvl/s\ 
            #    /   \ 
            #   /     \
            # at start:
            lcw = DBColumn("lcw", "numeric")
            rccw = DBColumn("rccw", "numeric")
            # at end:
            lccw = DBColumn("lccw", "numeric")
            rcw = DBColumn("rcw", "numeric")
        linestring = DBColumn("geometry", "linestring")
        #
        schema = Schema()
        schema.add_field(edge_id)
        schema.add_field(start)
        schema.add_field(end)
        schema.add_field(left)
        schema.add_field(right)
        if blnwings:
            schema.add_field(lcw)
            schema.add_field(rccw)
            schema.add_field(lccw)
            schema.add_field(rcw)
        schema.add_field(linestring)
        schema.add_index( Index(fields = [edge_id], primary_key = True) )
        schema.add_index( Index(fields = [left]) )
        schema.add_index( Index(fields = [right]) )
        schema.add_index( Index(fields = [start]) )
        schema.add_index( Index(fields = [end]) )
        schema.add_index( Index(fields = [linestring], cluster = True) )
        #
        edges = Layer(schema, '{0}_edge'.format(name), srid = topo_map.srid)
        
        # faces
        for face in topo_map.faces.itervalues():
            if not face.unbounded:
                geoms = face.multigeometry(srid = topo_map.srid)
                assert len(geoms) == 1
                poly = geoms[0]
                if face_geometry:
                    record = (face.id, 
                        round(face.area, 3), 
                        face.attrs['feature_class'], 
                        poly.representative_point(), 
                        poly.envelope,
                        poly)
                else:
                    record = (face.id, 
                        round(face.area, 3), 
                        face.attrs['feature_class'], 
                        poly.representative_point(), 
                        poly.envelope)                
                faces.append(*record)
        # nodes
        for node in topo_map.nodes.itervalues():
            nodes.append(node.id, node.geometry)

        # edges
        for edge in topo_map.half_edges.itervalues():
            assert edge.anchor is not None
            lft = edge
            rgt = edge.twin
            if blnwings:
                # TODO: signs of wings: + or -
                # - lcw / prev left
                # - rccw / next right
                # - lccw / next left
                # - rcw / prev right
                lcw, rcw, rccw, lccw = None, None, None, None
                for edge in (edge, edge.twin):
                    if edge.left_face is edge.face:
                        # lccw / next left
                        lccw = edge.next
                        if lccw.left_face is edge.face:
                            lccw_sign = +1
                        else:
                            lccw_sign = -1
                        # lcw / prev left
                        lcw = edge.prev
                        if lcw.left_face is edge.face:
                            lcw_sign = +1
                        else:
                            lcw_sign = -1
                    if edge.right_face is edge.face:
                        # rccw / next right
                        rccw = edge.next
                        if rccw.right_face is edge.face:
                            rccw_sign = -1
                        else:
                            rccw_sign = +1
                        # rcw / prev right
                        rcw = edge.prev
                        if rcw.right_face is edge.face:
                            rcw_sign = -1
                        else:
                            rcw_sign = +1
                assert lcw is not None
                assert rcw is not None
                assert lccw is not None
                assert rccw is not None
                edge = (lft.id,
                    lft.origin.id, rgt.origin.id, 
                    lft.face.id, rgt.face.id,
                    lcw_sign * lcw.id, rccw_sign * rccw.id, # wings at start
                    lccw_sign * lccw.id, rcw_sign * rcw.id, # wings at end
                    lft.geometry)
            else:
                edge = (lft.id,
                    lft.origin.id, rgt.origin.id, 
                    lft.face.id, rgt.face.id,
                    lft.geometry)
            edges.append(*edge)
        
        # TODO: make use of StringIO / file handler
        stream.write(dumps(nodes))
        stream.write(dumps(edges))
        stream.write(dumps(faces))