import bpy
from bpy.props import (StringProperty, BoolProperty, FloatProperty, 
                       IntProperty, CollectionProperty, FloatVectorProperty, 
                       EnumProperty, PointerProperty)
from bpy.types import PropertyGroup

class Pose2Robo_JointItem(PropertyGroup):
    is_expanded: BoolProperty(name="Expand Panel", default=True)
    
    joint_name: StringProperty(name="CSV Header", default="joint_name")
    
    base_bone: StringProperty(name="Base Bone", default="")
    target_bone: StringProperty(name="Target Bone", default="")
    
    axis_items = [('X', 'X', ''), ('Y', 'Y', ''), ('Z', 'Z', '')]
    axis_i: EnumProperty(name="Axis I", items=axis_items, default='X')
    axis_j: EnumProperty(name="Axis J", items=axis_items, default='X')
    axis_k: EnumProperty(name="Axis K", items=axis_items, default='Z')
    
    is_reverse: BoolProperty(name="Reverse", default=False)
    # 【新增】：初始角度（URDF零位偏移量）
    offset_angle: FloatProperty(name="Initial Angle", default=0.0)
    threshold: FloatProperty(name="Threshold", default=180.0, min=0, max=360, soft_min=0, soft_max=360)

class Pose2Robo_Settings(PropertyGroup):
    export_path: StringProperty(name="Export Path", subtype='FILE_PATH', default="//CsvOutput/export.csv", options={'PATH_SUPPORTS_BLEND_RELATIVE'})
    target_armature: PointerProperty(name="Target Armature", type=bpy.types.Object)

    target_action: PointerProperty(name="Target Action", type=bpy.types.Action, description="If empty, exports the currently playing action on the timeline by default")
    angle_unit: EnumProperty(
        name="Export Unit",
        items=[
            ('RADIAN', 'Radian', 'Export as Radian (Common for robot control)'),
            ('DEGREE', 'Degree', 'Export as Degree (For visual debugging)')
        ],
        default='RADIAN'
    )

    is_expanded_global: BoolProperty(name="Expand Global Panel", default=True)
    is_expanded_a: BoolProperty(name="Expand Panel A", default=True)

    export_root: BoolProperty(name="Export Single Bone Full Space Pose", default=True)
    root_bone: StringProperty(name="Target Bone", default="root")
    pos_x_name: StringProperty(name="pos x", default="root pos x")
    pos_y_name: StringProperty(name="pos y", default="root pos y")
    pos_z_name: StringProperty(name="pos z", default="root pos z")
    rot_x_name: StringProperty(name="rot x", default="root rot x")
    rot_y_name: StringProperty(name="rot y", default="root rot y")
    rot_z_name: StringProperty(name="rot z", default="root rot z")
    rot_w_name: StringProperty(name="rot w", default="root rot w")
    correction_euler: FloatVectorProperty(name="Euler Correction", subtype='EULER', default=(0.0, 0.0, 0.0))

    is_expanded_b: BoolProperty(name="Expand Panel B", default=True)
    export_joints: BoolProperty(name="Export Single Joint Angles", default=True)
    joints_list: CollectionProperty(type=Pose2Robo_JointItem)
    list_index: IntProperty(name="List Index", default=0)

    is_exporting: BoolProperty(name="Is Exporting", default=False)
    export_progress: FloatProperty(name="Export Progress", subtype='PERCENTAGE', default=0.0, min=0.0, max=100.0)