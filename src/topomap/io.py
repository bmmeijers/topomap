import logging

#from connection.dumb import recordset, record, irecordset, execute
#from simplegeom.postgis import register
from simplegeom.wkb import dumps

from connection import ConnectionFactory
#register()

from topomap import TopoMap
from loopfactory import find_loops
from clipper import EdgeClipper
import warnings

class TopoMapFactory(object):
    """Functions that can construct a in-memory TopoMap object from
    a set of tables in a PostGIS database
    """
    def __init__(self):
        pass

    @classmethod
    def topo_map(cls, name, 
                 universe_id = None, srid = None, 
                 attribute_mapping = None,
                 where = None):
        """Retrieves all Nodes, Edges, Faces for TopoMap ``name``
        """
        connection = ConnectionFactory.connection(True)
        universe_id = universe_id
        srid = srid
        name = name
        # TODO: get universe / srid from metadata if not given
        assert universe_id is not None
        assert srid is not None
        topo_map = TopoMap(universe_id = universe_id, srid = srid)

        if attribute_mapping is not None:
            # faces
            sql = """SELECT 
                {1[face_id]}::int,
                {1[feature_class]}::int 
            FROM
                {0}_face
            """.format(name, attribute_mapping)
        else:
            # faces
            sql = """SELECT 
                face_id::int,
                feature_class::int 
            FROM
                {0}_face
                """.format(name)
        if where is not None:
            sql += where
        for face_id, feature_class, in connection.irecordset(sql):
            assert face_id is not None
            topo_map.add_face(face_id, 
                              attrs = {'feature_class': feature_class,})
        logging.debug(sql)
        if attribute_mapping is not None:
            # faces
            sql = """SELECT 
                {1[edge_id]}::int,
                {1[start_node_id]}::int, 
                {1[end_node_id]}::int,
                
                {1[left_face_id]}::int, 
                {1[right_face_id]}::int,
                
                {1[geometry]}::geometry
            FROM 
                {0}_edge 
            """.format(name, attribute_mapping)
            
        else:
            #edges
            sql = """SELECT 
                edge_id::int,
                start_node_id::int, 
                end_node_id::int,
                
                left_face_id::int, 
                right_face_id::int,
                
                geometry::geometry
            FROM 
                {0}_edge 
            """.format(name)
        if where is not None:
            sql += where
        
        logging.debug(sql)
        
        for edge_id, \
            start_node_id, \
            end_node_id, \
            left_face_id, \
            right_face_id, \
            geometry, in connection.irecordset(sql):
            try:
                assert edge_id is not None
                assert start_node_id is not None
                assert end_node_id is not None
                assert left_face_id is not None
                assert right_face_id is not None
                assert geometry is not None
                #for item in (edge_id, start_node_id, end_node_id, left_face_id, right_face_id, geometry):
                #   assert item is not None, item
            except AssertionError:
                raise ValueError("Edge {0} not correct -- None field found".format(edge_id))
            topo_map.add_edge(edge_id,
                              start_node_id, end_node_id,
                              left_face_id, right_face_id,
                              geometry)
        find_loops(topo_map)
        return topo_map


    @classmethod
    def topo_map_not_locked(cls, name, 
                 universe_id = None, srid = None, 
                 attribute_mapping = None,
                 where = None):
        """Retrieves all Nodes, Edges, Faces for TopoMap ``name``
        """
        connection = ConnectionFactory.connection(True)
        universe_id = universe_id
        srid = srid
        name = name
        # TODO: get universe / srid from metadata if not given
        assert universe_id is not None
        assert srid is not None
        topo_map = TopoMap(universe_id = universe_id, srid = srid)
        
        if attribute_mapping is not None:
            # faces
            sql = """SELECT 
                {1[face_id]}::int,
                {1[feature_class]}::int 
            FROM
                {0}_face
            """.format(name, attribute_mapping)
        else:
            # faces
            sql = """SELECT 
                face_id::int,
                feature_class::int 
            FROM
                {0}_face
                """.format(name)
        if where is not None:
            sql += where
        for face_id, feature_class, in connection.irecordset(sql):
            assert face_id is not None
            topo_map.add_face(face_id, 
                              attrs = {'feature_class': feature_class, 'locked': False})
        
        logging.debug(sql)
        
        if attribute_mapping is not None:
            # faces
            sql = """SELECT 
                {1[edge_id]}::int,
                {1[start_node_id]}::int, 
                {1[end_node_id]}::int,
                
                {1[left_face_id]}::int, 
                {1[right_face_id]}::int,
                
                {1[geometry]}::geometry
            FROM 
                {0}_edge 
            """.format(name, attribute_mapping)
            
        else:
            #edges
            sql = """SELECT 
                edge_id::int,
                start_node_id::int, 
                end_node_id::int,
                
                left_face_id::int, 
                right_face_id::int,
                
                geometry::geometry
            FROM 
                {0}_edge 
            """.format(name)
        if where is not None:
            sql += where
        
        logging.debug(sql)
        
        for edge_id, \
            start_node_id, \
            end_node_id, \
            left_face_id, \
            right_face_id, \
            geometry, in connection.irecordset(sql):
            try:
                assert edge_id is not None
                assert start_node_id is not None
                assert end_node_id is not None
                assert left_face_id is not None
                assert right_face_id is not None
                assert geometry is not None
                #for item in (edge_id, start_node_id, end_node_id, left_face_id, right_face_id, geometry):
                #   assert item is not None, item
            except AssertionError:
                raise ValueError("Edge {0} not correct -- None field found".format(edge_id))
            topo_map.add_edge(edge_id,
                              start_node_id, end_node_id,
                              left_face_id, right_face_id,
                              geometry, attrs = {'locked': False, 'edge_class': 1})
        find_loops(topo_map)
        return topo_map



    @classmethod
    def clipped_topo_map(cls, name, bbox, universe_id = None, srid = None):
        """Retrieves all Nodes, Edges, Faces overlapping ``bbox`` for 
        TopoMap ``name``
        """
        connection = ConnectionFactory.connection(True)
        universe_id = universe_id
        bbox = bbox.envelope
        srid = srid
        name = name
        # TODO: get universe / srid from metadata if not given
        assert universe_id is not None
        assert srid is not None
        # also add border face as item
        border_face_id = -1
        topo_map = TopoMap(universe_id = universe_id, srid = srid)
        topo_map.add_face(border_face_id, 
                              attrs = {'clipped': True}).unbounded = True
        # faces
        sql = """SELECT 
            face_id::int,
            mbr_geometry,
            --feature_class::int
            0 
        FROM
            {0}_face
        WHERE
            mbr_geometry && '{1}'::geometry
            """.format(name, dumps(bbox.polygon)) # as_hexewkb(bbox, srid))
        for face_id, mbr, feature_class, in connection.irecordset(sql):
            topo_map.add_face(face_id, 
                              attrs = {'feature_class': feature_class,
                                       'clipped': False if bbox.contains_properly(mbr.envelope) else True})
        
        #edges
        sql = """SELECT 
            edge_id::int,
            start_node_id::int, end_node_id::int,
            left_face_id::int, right_face_id::int,
            geometry::geometry
        FROM 
            {0}_edge
        WHERE
            geometry && '{1}'::geometry
        """.format(name, dumps(bbox.polygon))
        
        ec = EdgeClipper(bbox=bbox, 
                         border_face_id=-1)
        for edge_id, \
            start_node_id, end_node_id, \
            left_face_id, right_face_id, \
            geometry, in connection.irecordset(sql):
            if bbox.contains_properly(geometry.envelope):
                topo_map.add_edge(edge_id,
                              start_node_id, end_node_id,
                              left_face_id, right_face_id,
                              geometry
                              )
            else:
                ec.clip_edge(edge_id,
                              start_node_id, end_node_id,
                              left_face_id, right_face_id,
                              geometry
                     )
        for item in ec.border_segments:
            topo_map.add_edge(*item)
        for item in ec.clipped:
            topo_map.add_edge(*item)
        LoopFactory.find_clipped_loops(topo_map)
        return topo_map


    @classmethod
    def clipped_topo_map_qgis(cls, name, rectangular, imp, universe_id = None, srid = None):
        """
        Create topomap for clipped viewport of QGIS
        1) Create function for retrieving correct left and right pointer of edges
        2) get proper faces and edges from db
        3) forms loops with clipped polygons         
        """
        from simplegeom.geometry import Envelope
        import loopfactory

        connection = ConnectionFactory.connection(True)
        universe_id = universe_id
        srid = srid
        name = name
        # TODO: get universe / srid from metadata if not given
        assert universe_id is not None
        assert srid is not None
        # also add border face as item
        border_face_id = -1 #FIXME: what is this border face? Is universe not sufficient?
        topo_map = TopoMap(universe_id = universe_id, srid = srid)
        topo_map.add_face(border_face_id, attrs = {'clipped': True}).unbounded = True

        # FIXME: this should not be here, but constructed by the caller!
        # then we do not have a dependency here on importing simplegeom
        bbox = Envelope(rectangular[0], rectangular[1], rectangular[2], rectangular[3])

        function = """
            CREATE OR REPLACE FUNCTION translate_face(integer, numeric)
            RETURNS integer
            LANGUAGE sql
            AS '
            with recursive walk_hierarchy(id, parentid, il, ih) as
            (
                    select face_id, parent_face_id, imp_low, imp_high from {0}_tgap_face_hierarchy where face_id = $1
                UNION ALL
                    select fh.face_id, fh.parent_face_id, fh.imp_low, fh.imp_high from {0}_tgap_face_hierarchy fh,
                    walk_hierarchy w
                    where w.parentid = fh.face_id and w.ih <= $2
            )
            select id from walk_hierarchy where il <= $2 and ih > $2;
            ' IMMUTABLE;
            """.format(name)
        connection.execute(function)
        # faces
        sql = """SELECT 
            face_id::int,
            mbr_geometry,
            feature_class::int
        FROM
            {0}_tgap_face
        WHERE
            mbr_geometry && '{1}'::geometry AND imp_low <= {2} AND imp_high > {2}
            """.format(name, dumps(bbox.polygon), imp) # as_hexewkb(bbox, srid))
#         print sql
        for face_id, mbr, feature_class, in connection.irecordset(sql):
            topo_map.add_face(face_id, 
                              attrs = {'feature_class': feature_class,
                                       'clipped': False if bbox.contains_properly(mbr.envelope) else True})
        
        #edges
        sql = """SELECT 
            edge_id::int,
            start_node_id::int, end_node_id::int,
            left_face_id_low::int,
            translate_face(left_face_id_low, {2})::int, 
            right_face_id_low::int,
            translate_face(right_face_id_low, {2})::int,
            geometry::geometry
        FROM 
            {0}_tgap_edge
        WHERE
            geometry && '{1}'::geometry AND imp_low <= {2} AND imp_high > {2}
        """.format(name, dumps(bbox.polygon), imp)
        ec = EdgeClipper(bbox=bbox, 
                         border_face_id=-1)
        for edge_id, \
            start_node_id, end_node_id, \
            old_left_face, left_face_id, \
            old_right_face, right_face_id, \
            geometry, in connection.irecordset(sql):
            
            if old_left_face == universe_id:
                left_face_id = universe_id
            if old_right_face == universe_id:
                right_face_id = universe_id
#             print "edge", edge_id, old_left_face, left_face_id,old_right_face, right_face_id
            if bbox.contains_properly(geometry.envelope):
                topo_map.add_edge(edge_id,
                              start_node_id, end_node_id,
                              left_face_id, right_face_id,
                              geometry
                              )
            else:
                ec.clip_edge(edge_id,
                              start_node_id, end_node_id,
                              left_face_id, right_face_id,
                              geometry
                     )
        for item in ec.border_segments:
            topo_map.add_edge(*item)
        for item in ec.clipped:
            topo_map.add_edge(*item)
        loopfactory.find_clipped_loops(topo_map)
        return topo_map


    @classmethod
    def topo_map_bbox(cls, name, bbox, universe_id = None, srid = None):
        """Retrieves all Nodes, Edges, Faces overlapping ``bbox`` for 
        TopoMap ``name``
        """
        connection = ConnectionFactory.connection(True)
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
            --feature_class::int
            0 
        FROM
            {0}_face
        WHERE
            mbr_geometry && '{1}'::geometry
            """.format(name, dumps(bbox)) # as_hexewkb(bbox, srid))
        for face_id, feature_class, in connection.irecordset(sql):
            topo_map.add_face(face_id, 
                              attrs = {'feature_class': feature_class,})
#                              attrs = {'imp_low': 0.0,
#                                            'imp_high': 0.0,
#                                            'imp_own': 0.0,
#                                            'min_step': 0,
#                                            'max_step': 0,
#                                            'feature_class': feature_class,
#                                            }
        
        #edges
        sql = """SELECT 
            edge_id::int,
            start_node_id::int, end_node_id::int,
            left_face_id::int, right_face_id::int,
            geometry::geometry
        FROM 
            {0}_edge
        WHERE
            geometry && '{1}'
        """.format(name, bbox)
        for edge_id, \
            start_node_id, end_node_id, \
            left_face_id, right_face_id, \
            geometry, in connection.irecordset(sql):
            topo_map.add_edge(edge_id,
                              start_node_id, end_node_id,
                              left_face_id, right_face_id,
                              geometry
                              #,
                              #attrs = {'imp_low': 0.0, 'imp_high': 0.0,
                              #         'lf_lo': left_face_id, 
                              #         'rf_lo': right_face_id,}
                              )
#        LoopFactory.find_loops()
        return topo_map

    @classmethod
    def topo_map_wazaa(cls, name, bbox, universe_id = None, srid = None, skip = None):
        """
        Retrieves all Nodes, Edges, Faces properly inside ``bbox`` and 
        not properly inside ``skip`` for TopoMap ``name``
        """
        connection = ConnectionFactory.connection(True)
        universe_id = universe_id
        srid = srid
        name = name
        # TODO: get universe / srid from metadata if not given
        assert universe_id is not None
        assert srid is not None
        topo_map = TopoMap(
            universe_id = universe_id, 
            srid = srid)
        # TODO: ugly that we have duplicate code (because different geometry name)
        if skip:
            exclude = []
            for item in skip:
                exclude.append("""AND NOT ST_ContainsProperly('{0}', mbr_geometry)""".format(dumps(item)))
            exclusion = " ".join(exclude)
        else:
            exclusion = ""
        # faces
        sql = """SELECT 
            face_id::int,
            --feature_class::int 
            feature_class::int 
        FROM
            {0}_face
        WHERE
            mbr_geometry && '{1}'
            AND
            ST_ContainsProperly('{1}', mbr_geometry)
            {2}
            """.format(name, dumps(bbox), exclusion)
        face_ids = set()
        for face_id, feature_class, in connection.irecordset(sql):
            face_ids.add(face_id)
            topo_map.add_face(face_id, 
                              attrs = {'imp_low': 0.0,
                                        'imp_high': 0.0,
                                        'imp_own': 0.0,
                                        'min_step': 0,
                                        'max_step': 0,
                                       'feature_class': feature_class,
                                       })
        
        # We could skip 'dangling' edges
        # By looking at which edges we really need
#         if face_ids:
#             inclusion = "AND (left_face_id IN ({0}) or right_face_id IN ({0}))".format(", ".join(map(str, face_ids)))
#         else:
        inclusion = ""
        
        # faces
        faces_sql = """SELECT 
            face_id::int
        FROM
            {0}_face
        WHERE
            mbr_geometry && '{1}'
            AND
            ST_ContainsProperly('{1}', mbr_geometry)
            {2}
            """.format(name, dumps(bbox), exclusion)
        print faces_sql
        #edges
        sql = """SELECT 
            edge_id::int,
            start_node_id::int, end_node_id::int,
            left_face_id::int, right_face_id::int,
            geometry::geometry
        FROM 
            {0}_edge
        WHERE
            geometry && '{1}'
            AND
            --ST_ContainsProperly('{1}', geometry)
            --AND 
            (left_face_id IN ({3}) or right_face_id IN ({3}))
            {2}
        """.format(name, dumps(bbox), inclusion, faces_sql)
        print sql
        for edge_id, \
            start_node_id, end_node_id, \
            left_face_id, right_face_id, \
            geometry, in connection.irecordset(sql):
            orig_left_face_id = left_face_id
            orig_right_face_id = right_face_id
            if left_face_id not in face_ids:
                orig_left_face_id = left_face_id
                left_face_id = universe_id
            if right_face_id not in face_ids:
                orig_right_face_id = right_face_id
                right_face_id = universe_id
            topo_map.add_edge(edge_id,
                              start_node_id, end_node_id,
                              left_face_id, right_face_id,
                              geometry,
                              attrs = {'original_left_face_id': orig_left_face_id,
                                       'original_right_face_id': orig_right_face_id,
                                       'imp_low': 0.0, 'imp_high': 0.0,
                                       'lf_lo': orig_left_face_id, 
                                       'rf_lo': orig_right_face_id,
                                       
                                       }
                              #,
                              #attrs = {'imp_low': 0.0, 'imp_high': 0.0,
                              #         'lf_lo': left_face_id, 
                              #         'rf_lo': right_face_id,}
                              )
#        topo_map.find_loops()
        LoopFactory.find_loops(topo_map)
        return topo_map

class PolygonFactory():
    """Class that encapsulates methods for reconstructing Polygon geometries
    from a TopoMap
    
    """
    def __init__(self):
        #self.connection = ConnectionFactory.connection(True)
        pass
    
    def polygon(self, name, face_id, universe_id = None, srid = None, 
                connection = None):
        """Construct a Polygon for given ``face_id`` in TopoMap ``name``
        """
        
        # TODO: get universe / srid from metadata if not given
        assert universe_id is not None
        assert srid is not None
        topo_map = TopoMap(universe_id = universe_id, srid = srid)
        # faces
        sql = """SELECT 
            face_id::int,
            mbr_geometry::geometry,
            -1 -- feature_class::int 
        FROM
            {0}_face
        WHERE face_id = {1}
            """.format(name, face_id)
        face_id, mbr_geometry, feature_class, = connection.record(sql)
        logging.debug(face_id)
        topo_map.add_face(face_id, 
            attrs = {'feature_class': feature_class,
                     'mbr': mbr_geometry.envelope,
                     'fixed': False, })
        assert len(topo_map.faces) == 2
        
        fixed = topo_map.add_face(-99, attrs = {'fixed': True,})
        logging.debug(fixed)
        #edges
        sql = """SELECT 
                edge_id::int, 
                start_node_id::int,
                end_node_id::int,
                left_face_id::int,
                right_face_id::int,
                geometry::geometry
            FROM
                {0}_edge
            WHERE 
                (left_face_id = %s or right_face_id = %s) 
            AND
                geometry && %s""".format(name)
        params = (face_id, face_id, mbr_geometry)
        for edge_id, \
            start_node_id, end_node_id, \
            left_face_id, right_face_id, \
            geometry, in connection.recordset(sql, params):
            # we set the face ptr to universe
            if left_face_id != face_id: 
                left_face_id = fixed.id
            if right_face_id != face_id: 
                right_face_id = fixed.id
            topo_map.add_edge(edge_id,
                              start_node_id, end_node_id,
                              left_face_id, right_face_id,
                              geometry)
        LoopFactory.find_loops(topo_map)
        lst = topo_map.faces[face_id].multigeometry()
        if len(lst) == 1:
            return lst[0]
        else:
            raise ValueError('multi geometry found')

    @classmethod
    def wings(cls, name, face_id, universe_id = None, srid = None):
        warnings.warn("Wings have not been fully tested")
#        logging.debug("starting wings")
        # TODO: get universe / srid from metadata if not given
        connection = ConnectionFactory.connection(True)
        assert universe_id is not None
        assert srid is not None
        topo_map = TopoMap(universe_id = universe_id, srid = srid)
        fixed = topo_map.add_face(-99, attrs = {'fixed': True,})
        if face_id != universe_id:
            sql = """SELECT 
                face_id::int,
                mbr_geometry::geometry
            FROM
                {0}_face
            WHERE face_id = {1}
                    """.format(name, face_id)
            face_id, mbr_geometry, = connection.record(sql)
#            mbr_geometry = geom_from_binary(mbr_wkb)
            topo_map.add_face(face_id, attrs = {'fixed': False, })
        
            #edges
            sql = """SELECT 
                    edge_id::int, 
                    start_node_id::int,
                    end_node_id::int,
                    left_face_id::int,
                    right_face_id::int,
                    geometry::geometry
                FROM
                    {0}_edge
                WHERE 
                    (left_face_id = %s or right_face_id = %s) 
                AND
                    geometry && %s""".format(name)
            params = (face_id, face_id, mbr_geometry)
        else:
            sql = """SELECT 
                    edge_id::int, 
                    start_node_id::int,
                    end_node_id::int,
                    left_face_id::int,
                    right_face_id::int,
                    geometry::geometry
                FROM
                    {0}_edge
                WHERE 
                    (left_face_id = %s or right_face_id = %s) 
                """.format(name)
            params = (face_id, face_id,)    
        for edge_id, \
            start_node_id, end_node_id, \
            left_face_id, right_face_id, \
            geometry, in connection.recordset(sql, params):
            # we set the face ptr to universe
            if left_face_id != face_id: 
                left_face_id = fixed.id
            if right_face_id != face_id: 
                right_face_id = fixed.id
            topo_map.add_edge(edge_id,
                              start_node_id, end_node_id,
                              left_face_id, right_face_id,
                              geometry)
#            logging.debug("edge: {0} {1}".format(edge_id, geometry))
        LoopFactory.find_loops(topo_map)
        current_face = topo_map.faces[face_id]
#        for edge in topo_map.half_edges.itervalues():
#            if edge.face is current_face:
#                print "...",  
#                print edge, edge.anchor is None, edge.next.id, edge.prev.id
        logging.info(current_face)
        for loop in current_face.loops:
#            print loop
            if loop.start.left_face is current_face:
                loop_sign = 1
            else:
                loop_sign = -1
#            print ""
#            print "loop", 
            loop_id = loop_sign * loop.start.id 
            #sql = 'UPDATE temp__{0}_edge SET {1} = %s WHERE edge_id = %s'
            sqll = 'INSERT INTO {0}_edge_left (edge_id, next, prev) VALUES (%s, %s, %s)'
            sqlr = 'INSERT INTO {0}_edge_right (edge_id, next, prev) VALUES (%s, %s, %s)'
            # TODO: next/prev and ccw/cw are mixed up here
            for edge in loop.half_edges:
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
                    connection.execute(sqll.format(name), parameters = ( edge.id, lcw_sign * lcw.id, lccw_sign * lccw.id,))
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
                    connection.execute(sqlr.format(name), parameters = (edge.id, rcw_sign * rcw.id, rccw_sign * rccw.id,))

##                print ""
##                print "e", edge.id
#                if edge.left_face is current_face:
#                    # next left / lcw
#                    lcw = edge.next
#                    if edge.next.left_face is current_face:
#                        lcw_sign = +1
#                    else:
#                        lcw_sign = -1
#                    # prev left / lccw
#                    lccw = edge.prev
#                    if edge.prev.left_face is current_face:
#                        lccw_sign = +1
#                    else:
#                        lccw_sign = -1

#                if edge.right_face is current_face:
#                    # prev right / rccw
#                    rccw = edge.prev
#                    if edge.prev.right_face is current_face:
#                        rccw_sign = -1
#                    else:
#                        rccw_sign = +1
#                    # next right / rcw
#                    rcw = edge.next
#                    if edge.next.right_face is current_face:
#                        rcw_sign = +1
#                    else:
#                        rcw_sign = -1
if __name__ == "__main__":
    we = TopoMapFactory.topo_map('delft10nl', 0, 28992)
