import logging
log = logging.getLogger(__name__)

from connection.stateful import recordset, record, irecordset
from brep.io import geom_from_binary, as_hexewkb

from topomap import TopoMap


class TopoMapFactory(object):
    def __init__(self):
        pass

    @classmethod
    def topo_map(cls, name, universe_id = None, srid = None):
        universe_id = universe_id
        srid = srid
        name = name
        # TODO: get universe / srid from metadata if not given
        assert universe_id is not None
        assert srid is not None
        topo_map = TopoMap(universe_id = universe_id, srid = srid)
        
        # faces
        sql = """SELECT 
            face_id::int,
            -1 -- feature_class::int 
        FROM
            {0}_face
            """.format(name)
        for face_id, feature_class, in irecordset(sql):
            topo_map.add_face(face_id, 
                              attrs = {'feature_class': feature_class,})
        
        #edges
        sql = """SELECT 
            edge_id::int,
            start_node_id::int, end_node_id::int,
            left_face_id::int, right_face_id::int,
            ST_AsBinary(geometry) 
        FROM 
            %s_edge 
        """ % (name)
        for edge_id, \
            start_node_id, end_node_id, \
            left_face_id, right_face_id, \
            wkb, in irecordset(sql):
            geometry = geom_from_binary(wkb)
            topo_map.add_edge(edge_id,
                              start_node_id, end_node_id,
                              left_face_id, right_face_id,
                              geometry
                              #,
                              #attrs = {'imp_low': 0.0, 'imp_high': 0.0,
                              #         'lf_lo': left_face_id, 
                              #         'rf_lo': right_face_id,}
                              )
        topo_map.find_loops()
        return topo_map


    @classmethod
    def topo_map_bbox(cls, name, bbox, universe_id = None, srid = None):
        universe_id = universe_id
        srid = srid
        name = name
        # TODO: get universe / srid from metadata if not given
        assert universe_id is not None
        assert srid is not None
        topo_map = TopoMap(universe_id = universe_id, srid = srid)
        
        # faces
        sql = """SELECT 
            face_id::int,
            -1 -- feature_class::int 
        FROM
            {0}_face
        WHERE
            mbr_geometry && {1}
            """.format(name,  as_hexewkb(bbox, srid))
        for face_id, feature_class, in irecordset(sql):
            topo_map.add_face(face_id, 
                              attrs = {'feature_class': feature_class,})
        
        #edges
        sql = """SELECT 
            edge_id::int,
            start_node_id::int, end_node_id::int,
            left_face_id::int, right_face_id::int,
            ST_AsBinary(geometry) 
        FROM 
            {0}_edge
        WHERE
            mbr_geometry && {1}
        """ % (name,  as_hexewkb(bbox, srid))
        for edge_id, \
            start_node_id, end_node_id, \
            left_face_id, right_face_id, \
            wkb, in irecordset(sql):
            geometry = geom_from_binary(wkb)
            topo_map.add_edge(edge_id,
                              start_node_id, end_node_id,
                              left_face_id, right_face_id,
                              geometry
                              #,
                              #attrs = {'imp_low': 0.0, 'imp_high': 0.0,
                              #         'lf_lo': left_face_id, 
                              #         'rf_lo': right_face_id,}
                              )
        topo_map.find_loops()
        return topo_map

class PolygonFactory():
    def __init__(self):
        pass

    @classmethod
    def polygon(cls, name, face_id, universe_id = None, srid = None):
        # TODO: get universe / srid from metadata if not given
        assert universe_id is not None
        assert srid is not None
        topo_map = TopoMap(universe_id = universe_id, srid = srid)
        # faces
        sql = """SELECT 
            face_id::int,
            ST_AsBinary(mbr_geometry),
            -1 -- feature_class::int 
        FROM
            {0}_face
        WHERE face_id = {1}
            """.format(name, face_id)
        face_id, mbr_wkb, feature_class, = record(sql)
        mbr_geometry = geom_from_binary(mbr_wkb)
        topo_map.add_face(face_id, 
            attrs = {'feature_class': feature_class,
                     'mbr': mbr_geometry.envelope,})
        assert len(topo_map.faces) == 2
        #edges
        sql = """SELECT 
                edge_id::int, 
                start_node_id::int,
                end_node_id::int,
                left_face_id::int,
                right_face_id::int,
                ST_AsBinary(geometry)
            FROM
                {}_edge
            WHERE 
                (left_face_id = %s or right_face_id = %s) 
            AND
                geometry && %s""".format(name)
        params = (face_id, face_id, as_hexewkb(mbr_geometry, srid))
        for edge_id, \
            start_node_id, end_node_id, \
            left_face_id, right_face_id, \
            wkb, in recordset(sql, params):
            geometry = geom_from_binary(wkb)
            # we set the face ptr to universe
            if left_face_id != face_id: 
                left_face_id = universe_id
            if right_face_id != face_id: 
                right_face_id = universe_id
            topo_map.add_edge(edge_id,
                              start_node_id, end_node_id,
                              left_face_id, right_face_id,
                              geometry)
        topo_map.find_loops()
        lst = topo_map.faces[face_id].multigeometry()
        if len(lst) == 1:
            return lst[0]
        else:
            raise ValueError('multi geometry found')
