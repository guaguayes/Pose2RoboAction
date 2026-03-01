import math
import mathutils

def get_bone_axis_vector(matrix, axis_char):
    """提取骨骼矩阵中对应轴向的标准化三维向量"""
    idx_map = {'X': 0, 'Y': 1, 'Z': 2}
    idx = idx_map[axis_char.upper()]
    return matrix.col[idx].to_3d().normalized()

def calculate_planar_angle_0_360(vec_k, vec_i, vec_j):
    """计算投影平面上的 0-360 度夹角"""
    basis_x = vec_i
    basis_y = vec_k.cross(vec_i) 
    x = vec_j.dot(basis_x)
    y = vec_j.dot(basis_y)
    rad = math.atan2(y, x)
    deg = math.degrees(rad)
    if deg < 0:
        deg += 360.0
    return deg