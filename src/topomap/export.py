from sink import Field, Schema, Index, Layer, dumps
import warnings

class TopoMapExporter(object):
    def __init__(self):
        pass

    @classmethod
    def export(cls, topo_map, name, wings = False):
        if wings:
            warnings.warn("Wings have not been tested/are not fully implemented")
        # Make schema
        # NODES
        node_id = Field("node_id", "numeric")
        point = Field("geometry", "point")
        #
        schema = Schema()
        schema.add_field(node_id)
        schema.add_field(point)
        schema.add_index( Index(fields = [node_id], primary_key = True) )
        schema.add_index( Index(fields = [point], cluster = True) )
        #
        nodes = Layer(schema, '{}_node'.format(name), srid = topo_map.srid)
        
        # FACES
        face_id = Field("face_id", "numeric")
        area = Field("area", "float")
        class_ = Field("feature_class", "integer")
        pip = Field("pip_geometry", "point")
        mbr = Field("mbr_geometry", "box2d")
        #
        schema = Schema()
        schema.add_field(face_id)
        schema.add_field(area)
        schema.add_field(class_)
        schema.add_field(pip)
        schema.add_field(mbr)
        schema.add_index( Index(fields = [face_id], primary_key = True) )
        schema.add_index( Index(fields = [pip]) )
        schema.add_index( Index(fields = [mbr], cluster = True) )
        #
        faces = Layer(schema, '{}_face'.format(name), srid = topo_map.srid)
        
        # EDGES
        edge_id = Field("edge_id", "numeric")
        left = Field("left_face_id", "numeric")
        right = Field("right_face_id", "numeric")
        start = Field("start_node_id", "numeric")
        end = Field("end_node_id", "numeric")
        if wings:
            # wings
            #
            #   \     / 
            #    \   /  
            #     \e/   
            # lccw ^ rcw
            #      |  
            #(LF)  |  (RF)
            #      |  
            #  lcw o rccw
            #     /s\ 
            #    /   \ 
            #   /     \
            # at start:
            lcw = Field("lcw", "numeric")
            rccw = Field("rccw", "numeric")
            # at end:
            lccw = Field("lccw", "numeric")
            rcw = Field("rcw", "numeric")
        linestring = Field("geometry", "linestring")
        #
        schema = Schema()
        schema.add_field(edge_id)
        schema.add_field(start)
        schema.add_field(end)
        schema.add_field(left)
        schema.add_field(right)
        if wings:
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
        edges = Layer(schema, '{}_edge'.format(name), srid = topo_map.srid)
        
        # faces
        for face in topo_map.faces.itervalues():
            if not face.unbounded:
                geoms = face.multigeometry()
                assert len(geoms) == 1
                poly = geoms[0]
                faces.append(face.id, 
                    round(face.area, 3), 
                    face.attrs['feature_class'], 
                    poly.representative_point, 
                    poly.envelope)
        
        # nodes
        for node in topo_map.nodes.itervalues():
            nodes.append(node.id, node.geometry)

        # edges
        for edge in topo_map.half_edges.itervalues():
            assert edge.anchor is not None
            lft = edge
            rgt = edge.twin
            if wings:
                # TODO: signs of wings: + or -
                print "l", lft.prev.anchor is None
                print "l", lft.next.anchor is None
                print "r", rgt.prev.anchor is not None
                print "r", rgt.next.anchor is not None
                print ""
                edge = (lft.id,
                    lft.origin.id, rgt.origin.id, 
                    lft.face.id, rgt.face.id,
                    lft.prev.id, rgt.next.id, # wings at start
                    lft.next.id, rgt.prev.id, # wings at end
                    lft.geometry)
            else:
                edge = (lft.id,
                    lft.origin.id, rgt.origin.id, 
                    lft.face.id, rgt.face.id,
                    lft.geometry)
            edges.append(*edge)
        
        # TODO: make use of StringIO / file handler
#        print dumps(nodes)
#        print dumps(edges)
#        print dumps(faces)