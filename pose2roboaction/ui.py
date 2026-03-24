import bpy
from bpy.types import Panel
from bpy.app.translations import pgettext_iface as iface_

class VIEW3D_PT_Pose2Robo_Main(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Pose2Robo'
    bl_label = "Robot Action Exporter"

    def draw(self, context):
        layout = self.layout
        props = context.scene.pose2robo_settings
        arm = props.target_armature

        # --- 1. 全局配置 ---
        box = layout.box()
        
        header_global = box.row(align=True)
        icon_state_global = 'TRIA_DOWN' if props.is_expanded_global else 'TRIA_RIGHT'
        header_global.prop(props, "is_expanded_global", text="", icon=icon_state_global, emboss=False)
        header_global.label(text=iface_("Global Settings"), icon='WORLD')
        
        if props.is_expanded_global:
            col = box.column(align=True)
            col.prop(props, "export_path", text=iface_("Export Path"))
            col.separator()
            col.prop(props, "target_armature", text=iface_("Target Armature"))
            col.prop(props, "target_action", text=iface_("Target Action"))
            col.separator()
            row_unit = col.row()
            row_unit.prop(props, "angle_unit", expand=True) 

        # --- 2. Config A ---
        box_a = layout.box()
        
        header_a = box_a.row(align=True)
        icon_state_a = 'TRIA_DOWN' if props.is_expanded_a else 'TRIA_RIGHT'
        header_a.prop(props, "is_expanded_a", text="", icon=icon_state_a, emboss=False)
        header_a.prop(props, "export_root", text=iface_("Export Single Bone Full Space Pose"))
        
        if props.is_expanded_a and props.export_root:
            col = box_a.column(align=True)
            if arm and arm.type == 'ARMATURE':
                col.prop_search(props, "root_bone", arm.data, "bones", text=iface_("Target Bone"))
            else:
                col.prop(props, "root_bone", text=iface_("Target Bone"))
            
            col.separator()
            
            sub = col.box()
            sub.label(text=iface_("CSV Header Mapping:"), icon='LINENUMBERS_ON')
            
            col_pos = sub.column(align=True)
            col_pos.prop(props, "pos_x_name", text="pos x ->")
            col_pos.prop(props, "pos_y_name", text="pos y ->")
            col_pos.prop(props, "pos_z_name", text="pos z ->")
            
            col_rot = sub.column(align=True)
            col_rot.prop(props, "rot_x_name", text="rot x ->")
            col_rot.prop(props, "rot_y_name", text="rot y ->")
            col_rot.prop(props, "rot_z_name", text="rot z ->")
            col_rot.prop(props, "rot_w_name", text="rot w ->")
            
            col.separator()
            col.prop(props, "correction_euler", text=iface_("Euler Correction"))

        # --- 3. Config B ---
        box_b = layout.box()
        
        header_b = box_b.row(align=True)
        icon_state_b = 'TRIA_DOWN' if props.is_expanded_b else 'TRIA_RIGHT'
        header_b.prop(props, "is_expanded_b", text="", icon=icon_state_b, emboss=False)
        header_b.prop(props, "export_joints", text=iface_("Export Single Joint Angles"))
        
        if props.is_expanded_b and props.export_joints:
            box_b.operator("pose2robo.list_add", icon='ADD', text=iface_("Add New Joint Config"))
            
            for i, item in enumerate(props.joints_list):
                card = box_b.box()
                
                header = card.row(align=True)
                icon_state = 'TRIA_DOWN' if item.is_expanded else 'TRIA_RIGHT'
                header.prop(item, "is_expanded", text="", icon=icon_state, emboss=False)
                
                display_name = item.joint_name if item.joint_name else iface_("New Joint")
                header.label(text=f"{iface_('Config:')} {display_name}", icon='BONE_DATA')
                
                remove_op = header.operator("pose2robo.list_remove_item", icon='X', text="")
                remove_op.index = i 
                
                if item.is_expanded:
                    col = card.column(align=True)
                    col.prop(item, "joint_name", text=iface_("CSV Header"))
                    col.separator()
                    
                    if arm and arm.type == 'ARMATURE':
                        col.prop_search(item, "base_bone", arm.data, "bones", text=iface_("Base Bone"))
                        col.prop_search(item, "target_bone", arm.data, "bones", text=iface_("Target Bone"))
                    else:
                        col.prop(item, "base_bone", text=iface_("Base Bone"))
                        col.prop(item, "target_bone", text=iface_("Target Bone"))
                    col.separator()
                    
                    row_axes = col.row(align=True)
                    row_axes.prop(item, "axis_i", text=iface_("Reference i"))
                    row_axes.prop(item, "axis_j", text=iface_("Active j"))
                    row_axes.prop(item, "axis_k", text=iface_("Normal k"))
                    col.separator()
                    
                    # 【核心修改】：将“初始角度”插入到布局中
                    # 使用 split 手动划分宽度比例：前 20% 给复选框，后 75% 给数值框
                    split = col.split(factor=0.2, align=True)
                    split.prop(item, "is_reverse", text=iface_("Reverse"))

                    # 在右侧的 75% 区域内创建一个紧凑的行
                    row_floats = split.row(align=True)
                    row_floats.prop(item, "offset_angle", text=iface_("Initial Angle"))
                    row_floats.prop(item, "threshold", text=iface_("Threshold"))

        # --- 4. 动态显示 ---
        layout.separator()
        if props.is_exporting:
            row = layout.row()
            row.enabled = False  
            row.prop(props, "export_progress", text=iface_("Exporting..."), slider=True)
        else:
            layout.operator("pose2robo.export_csv", icon='EXPORT', text=iface_("Start Exporting CSV Sequence"))