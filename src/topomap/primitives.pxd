# cython: profile=True

cpdef increasing(object obj)
cpdef double angle(object, object)

# cdef class A:
#     cdef public int a,b
#     cpdef foo(self, double x)

cdef class Face:
    cdef public int id
    cdef public bint unbounded
    cdef public dict attrs
    cdef public list loops
    cdef public list rings
    cdef public list linestrings
    cdef public double area

cdef class Anchorage:
    cdef public int id
    cdef public dict attrs
    cdef public object geometry

cdef class HalfEdge

cdef class Node:
    cdef public int id
    cdef public dict attrs
    cdef public object geometry
    cdef public HalfEdge he
    cdef public unsigned int degree

cdef class LoopHalfEdgesIterator:
    cdef public HalfEdge start
    cdef public HalfEdge cur
#     cpdef HalfEdge next

cdef class Loop:
    cdef public HalfEdge start 
    cdef public list linear_rings
    cdef public list linestrings

cdef class HalfEdge:
    cdef public Anchorage anchor
    cdef public HalfEdge twin
    cdef public Node origin
    cdef public double angle
    cdef public HalfEdge prev
    cdef public HalfEdge next
    cdef public Loop loop
    cdef public Face face
    cdef public int label
#         __slots__ = ('anchor', 
#                  'twin', 
#                  'origin', 'angle', 
#                  'prev', 'next', 
#                  'loop', 'face', 'label')
